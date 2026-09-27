"""AIControlCenter-owned, read-only inquiry state and trusted handoff config."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import sqlite3
import hashlib
import secrets
import os
from threading import Lock
from pathlib import Path
from typing import Callable, Protocol
import uuid

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from core.shopping.models import Product, ProductVariant
from core.shopping.customer_persistence import (
    AuthorizationConflict, IdempotencyConflict, InquiryVersionConflict,
    OwnershipConflict, StorageUnavailable, open_connection,
    initialize_schema, persisted_session_status,
    SCHEMA_VERSION, PersistenceError,
)
from core.shopping.customer_identity import require_utc
from core.shopping.customer_session_service import CustomerSessionService, SessionValidationCode
from core.shopping.customer_sessions import SafeSessionProjection
from core.shopping.migration_contract import EXPLICIT_UNOWNED_MARKER

MAX_MESSAGE_LENGTH = 1000
CONTACT_CHANNELS = ({"type": "kakao_openchat", "label": "카카오 오픈채팅",
                     "url": "https://open.kakao.com/o/sV26tFNi", "enabled": True},)


def configured_contact_channels() -> list[dict]:
    channels = [dict(channel) for channel in CONTACT_CHANNELS if channel["enabled"]]
    instagram_url = os.getenv("AICC_INSTAGRAM_CONTACT_URL", "").strip()
    if instagram_url.startswith("https://www.instagram.com/"):
        channels.append({"type": "instagram", "label": "인스타그램", "url": instagram_url, "enabled": True})
    return channels


class InquiryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    variant_id: str | None = Field(default=None, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    inquiry_type: str = Field(default="purchase", pattern=r"^purchase$")
    message: str = Field(default="", max_length=MAX_MESSAGE_LENGTH)


class InquiryMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


class OwnedInquiryMessageRequest(InquiryMessageRequest):
    expected_version: int = Field(strict=True, ge=0)
    idempotency_key: str = Field(strict=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class InquirySessionAuthority:
    """Server-held references plus credential, never accepted as browser JSON.

    This object is not proof by itself. Each operation verifies its credential
    through B3-B under the inquiry database's writer lock, then checks current
    eligibility in that same transaction. A different database is denied.
    """

    service: CustomerSessionService = field(repr=False)
    session_secret: SecretStr = field(repr=False)
    customer_id: str
    session_id: str
    clock: Callable[[], datetime] = field(repr=False)

    def revalidate(self, connection: sqlite3.Connection, database_path: str) -> datetime:
        if Path(self.service.database_path).resolve() != Path(database_path).resolve():
            raise AuthorizationConflict("session authority denied")
        now = require_utc(self.clock())
        result = self.service.validate_session(
            self.session_id, self.session_secret.get_secret_value(), self.customer_id, now=now,
        )
        if result.code == SessionValidationCode.STORAGE_UNAVAILABLE:
            raise StorageUnavailable("session authority unavailable")
        if result.code != SessionValidationCode.VALID or type(result.projection) is not SafeSessionProjection:
            raise AuthorizationConflict("session authority denied")
        projection = SafeSessionProjection.model_validate(result.projection)
        if (projection.id != self.session_id or projection.customer_id != self.customer_id
                or persisted_session_status(connection, self.customer_id, self.session_id, now=now).value != "ELIGIBLE"):
            raise AuthorizationConflict("session authority denied")
        return now


class InquiryProduct(BaseModel):
    id: str
    name: str


class InquiryVariant(BaseModel):
    id: str
    label: str


class InquiryMessage(BaseModel):
    id: str
    inquiry_id: str
    sender_type: str
    body: str
    created_at: str


class InquiryResponse(BaseModel):
    id: str
    status: str
    product: InquiryProduct
    variant: InquiryVariant | None = None
    formatted_message: str
    contact_channels: list[dict]
    messages: list[InquiryMessage] = Field(default_factory=list)
    public_access_token: str | None = None


class InquiryRepository(Protocol):
    def create(self, product: Product, variant: ProductVariant | None, message: str) -> InquiryResponse: ...
    def get(self, inquiry_id: str) -> InquiryResponse | None: ...
    def append_message(self, inquiry_id: str, body: str, sender_type: str) -> InquiryMessage | None: ...
    def authorize(self, inquiry_id: str, token: str) -> bool: ...
    def list(self) -> list[InquiryResponse]: ...
    def get_legacy_authorized(self, inquiry_id: str, token: str) -> InquiryResponse | None: ...
    def append_legacy_authorized(self, inquiry_id: str, token: str, body: str) -> InquiryMessage | None: ...


def sanitize_message(message: str) -> str:
    # Keep plain text and line breaks; discard control characters and normalize whitespace.
    cleaned = "".join(char for char in message.replace("\r\n", "\n").replace("\r", "\n")
                      if char in "\n\t" or not ord(char) < 32)
    return cleaned.replace("<", "［").replace(">", "］").strip()[:MAX_MESSAGE_LENGTH]


def format_message(inquiry_id: str, product: Product, variant: ProductVariant | None, message: str) -> str:
    lines = ["[agachichi 상품문의]", "", f"문의번호: {inquiry_id}", f"상품: {product.name}", f"상품코드: {product.id}"]
    if variant:
        lines.append(f"선택 사이즈: {variant.label}")
    lines.extend(["문의유형: 구매문의", "", "문의내용:", message])
    return "\n".join(lines)


class InMemoryInquiryRepository:
    """Ephemeral Preview/test repository, never durable ownership evidence."""
    def __init__(self):
        self._items: dict[str, InquiryResponse] = {}
        self._next = 1
        self._lock = Lock()
        self._tokens: dict[str, str] = {}

    def create(self, product: Product, variant: ProductVariant | None, message: str) -> InquiryResponse:
        with self._lock:
            inquiry_id = f"AG-INQ-{self._next:06d}"
            self._next += 1
            token = secrets.token_urlsafe(32)
            result = InquiryResponse(id=inquiry_id, status="created",
                product=InquiryProduct(id=product.id, name=product.name),
                variant=InquiryVariant(id=variant.id, label=variant.label) if variant else None,
                formatted_message=format_message(inquiry_id, product, variant, message),
                contact_channels=configured_contact_channels(),
                public_access_token=token)
            self._items[inquiry_id] = result.model_copy(update={"public_access_token": None}, deep=True)
            self._tokens[inquiry_id] = hashlib.sha256(token.encode()).hexdigest()
            return result

    def get(self, inquiry_id: str) -> InquiryResponse | None:
        item = self._items.get(inquiry_id)
        return item.model_copy(update={"public_access_token": None}, deep=True) if item else None

    def authorize(self, inquiry_id: str, token: str) -> bool:
        return secrets.compare_digest(self._tokens.get(inquiry_id, ""), hashlib.sha256(token.encode()).hexdigest())

    def get_legacy_authorized(self, inquiry_id: str, token: str) -> InquiryResponse | None:
        # In-process-only token behavior; this is not durable classification
        # or migration evidence.
        return self.get(inquiry_id) if self.authorize(inquiry_id, token) else None

    def append_legacy_authorized(self, inquiry_id: str, token: str, body: str) -> InquiryMessage | None:
        return self.append_message(inquiry_id, body, "customer") if self.authorize(inquiry_id, token) else None

    def append_message(self, inquiry_id: str, body: str, sender_type: str) -> InquiryMessage | None:
        item = self._items.get(inquiry_id)
        if not item: return None
        message = InquiryMessage(id=secrets.token_urlsafe(18), inquiry_id=inquiry_id, sender_type=sender_type,
                                 body=sanitize_message(body), created_at=datetime.now(timezone.utc).isoformat())
        item.messages.append(message)
        return message

    def list(self) -> list[InquiryResponse]:
        return [item.model_copy(update={"public_access_token": None}, deep=True)
                for item in self._items.values()]


def _load_inquiry_payload(raw: str) -> InquiryResponse:
    payload = json.loads(raw)
    # Legacy payloads may contain a creation token; never project or reuse it.
    payload.pop("public_access_token", None)
    return InquiryResponse.model_validate(payload)


class SQLiteInquiryRepository(InMemoryInquiryRepository):
    """Durable AIControlCenter application state using the existing SQLite pattern."""
    def __init__(self, db_path: str):
        super().__init__()
        self._db_path = db_path
        with sqlite3.connect(self._db_path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS inquiries (id TEXT PRIMARY KEY, payload TEXT NOT NULL, token_hash TEXT NOT NULL)")
            columns = {row[1] for row in connection.execute("PRAGMA table_info(inquiries)")}
            if "token_hash" not in columns:
                connection.execute("ALTER TABLE inquiries ADD COLUMN token_hash TEXT NOT NULL DEFAULT ''")
            row = connection.execute("SELECT id FROM inquiries ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            self._next = int(row[0].rsplit("-", 1)[-1]) + 1

    @classmethod
    def initialize_persistence_schema(cls, db_path: str) -> None:
        """Explicitly provision the B2 persistence tables; never auto-migrate."""
        initialize_schema(db_path)

    def bind_customer_ownership(self, inquiry_id: str, customer_id: str, session_id: str) -> None:
        """Bind an inquiry from a trusted server-side adapter only.

        This low-level foundation never treats a caller's IDs as authentication
        evidence. The future trusted adapter must establish that authority.
        """
        try:
            connection = open_connection(self._db_path)
            try:
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute("SELECT 1 FROM inquiries WHERE id=?", (inquiry_id,)).fetchone() is None:
                    raise KeyError(inquiry_id)
                existing = connection.execute(
                    "SELECT customer_id,session_id,version FROM shopping_inquiry_ownership WHERE inquiry_id=?",
                    (inquiry_id,),
                ).fetchone()
                if existing is not None:
                    if (existing["customer_id"], existing["session_id"]) != (customer_id, session_id):
                        raise OwnershipConflict("inquiry ownership is immutable")
                    connection.commit()
                    return
                connection.execute(
                    "INSERT INTO shopping_inquiry_ownership(inquiry_id,customer_id,session_id,version) VALUES(?,?,?,0)",
                    (inquiry_id, customer_id, session_id),
                )
                # Historical bearer credentials and unowned provenance cannot
                # survive a trusted ownership transition, even after schema loss.
                row = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
                payload = json.loads(row["payload"])
                payload.pop("_ownership", None)
                payload.pop("public_access_token", None)
                connection.execute("UPDATE inquiries SET payload=?,token_hash='' WHERE id=?",
                                   (json.dumps(payload), inquiry_id))
                connection.commit()
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise
            finally:
                connection.close()
        except sqlite3.OperationalError:
            raise StorageUnavailable("storage unavailable") from None

    def append_message_authorized(self, inquiry_id: str, body: str, sender_type: str, *,
                                  customer_id: str, session_id: str, expected_version: int,
                                  idempotency_key: str, actor_ref: str, correlation_id: str,
                                  now: datetime, authority: InquirySessionAuthority | None = None) -> InquiryMessage:
        """Atomically apply a trusted, versioned inquiry mutation.

        Existing token-authorized API methods intentionally remain unchanged;
        this method is an opt-in foundation for a future trusted cutover.
        """
        if sender_type not in ("customer", "operator"):
            raise AuthorizationConflict("unsupported sender")
        if type(expected_version) is not int or expected_version < 0:
            raise InquiryVersionConflict("invalid inquiry version")
        if not all(type(value) is str and 1 <= len(value) <= 160
                   for value in (idempotency_key, actor_ref, correlation_id)):
            raise ValueError("bounded mutation references are required")
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise ValueError("timestamp must be timezone-aware UTC")
        cleaned = sanitize_message(body)
        request_digest = hashlib.sha256(json.dumps(
            {"inquiry_id": inquiry_id, "body": cleaned, "sender_type": sender_type,
             "customer_id": customer_id, "session_id": session_id, "version": expected_version},
            sort_keys=True, separators=(",", ":"),
        ).encode()).hexdigest()
        occurred = now.isoformat(timespec="microseconds").replace("+00:00", "Z")
        connection = None
        try:
            connection = open_connection(self._db_path)
            connection.execute("BEGIN IMMEDIATE")
            if authority is not None:
                if (authority.customer_id, authority.session_id, actor_ref, sender_type) != (
                        customer_id, session_id, customer_id, "customer"):
                    raise AuthorizationConflict("session authority denied")
                now = authority.revalidate(connection, self._db_path)
                occurred = now.isoformat(timespec="microseconds").replace("+00:00", "Z")
            ownership = connection.execute(
                "SELECT customer_id,session_id,version FROM shopping_inquiry_ownership WHERE inquiry_id=?",
                (inquiry_id,),
            ).fetchone()
            if ownership is None or (ownership["customer_id"], ownership["session_id"]) != (customer_id, session_id):
                raise AuthorizationConflict("inquiry ownership denied")
            if persisted_session_status(connection, customer_id, session_id, now=now).value != "ELIGIBLE":
                raise AuthorizationConflict("session is not eligible")
            existing = connection.execute(
                "SELECT request_digest,message_id,result_version FROM shopping_inquiry_idempotency WHERE inquiry_id=? AND idempotency_key=?",
                (inquiry_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["request_digest"] != request_digest:
                    raise IdempotencyConflict("idempotency key conflicts with another request")
                row = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
                if row is None:
                    raise StorageUnavailable("inquiry state unavailable")
                replay = _load_inquiry_payload(row["payload"])
                message = next((item for item in replay.messages if item.id == existing["message_id"]), None)
                if message is None:
                    raise StorageUnavailable("idempotency result is incomplete")
                connection.commit()
                return message
            if ownership["version"] != expected_version:
                raise InquiryVersionConflict("inquiry version conflict")
            row = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
            if row is None:
                raise KeyError(inquiry_id)
            item = _load_inquiry_payload(row["payload"])
            message = InquiryMessage(
                id=secrets.token_urlsafe(18), inquiry_id=inquiry_id,
                sender_type=sender_type, body=cleaned, created_at=occurred,
            )
            item.messages.append(message)
            next_version = expected_version + 1
            connection.execute(
                "UPDATE inquiries SET payload=? WHERE id=?",
                (item.model_dump_json(exclude={"public_access_token"}), inquiry_id),
            )
            connection.execute(
                "UPDATE shopping_inquiry_ownership SET version=? WHERE inquiry_id=? AND version=?",
                (next_version, inquiry_id, expected_version),
            )
            if connection.execute("SELECT changes()").fetchone()[0] != 1:
                raise InquiryVersionConflict("inquiry version conflict")
            connection.execute(
                "INSERT INTO shopping_inquiry_idempotency(inquiry_id,idempotency_key,request_digest,message_id,result_version) VALUES(?,?,?,?,?)",
                (inquiry_id, idempotency_key, request_digest, message.id, next_version),
            )
            event_id = hashlib.sha256(f"{inquiry_id}:{idempotency_key}:{next_version}".encode()).hexdigest()
            connection.execute(
                "INSERT INTO shopping_inquiry_audit(event_id,actor_ref,resource_ref,action,outcome,correlation_id,occurred_at) VALUES(?,?,?,?,?,?,?)",
                (event_id, actor_ref, inquiry_id, "INQUIRY_MESSAGE_APPEND", "APPLIED", correlation_id, occurred),
            )
            connection.commit()
            return message
        except sqlite3.DatabaseError:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise StorageUnavailable("storage unavailable") from None
        except Exception:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()

    def create(self, product: Product, variant: ProductVariant | None, message: str) -> InquiryResponse:
        result = super().create(product, variant, message)
        with sqlite3.connect(self._db_path) as connection:
            payload = result.model_dump(exclude={"public_access_token"})
            # Only fresh, explicitly unowned creation gains this provenance.
            # Never retrofit it onto historical records or infer it from a token.
            payload["_ownership"] = "unowned/v1"
            connection.execute("INSERT INTO inquiries (id, payload, token_hash) VALUES (?, ?, ?)",
                               (result.id, json.dumps(payload), self._tokens[result.id]))
        return result

    def get(self, inquiry_id: str) -> InquiryResponse | None:
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute("SELECT payload FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return _load_inquiry_payload(row[0]) if row else None

    def authorize(self, inquiry_id: str, token: str) -> bool:
        with self._transaction(require_owned_schema=False) as connection:
            return self._legacy_row(connection, inquiry_id, token) is not None

    def append_message(self, inquiry_id: str, body: str, sender_type: str) -> InquiryMessage | None:
        with self._transaction(require_owned_schema=False) as connection:
            row = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
            if row is None:
                return None
            # Unversioned legacy writes, including the legacy operator endpoint,
            # must never bypass owned mutation version/idempotency/audit checks.
            if not self._positively_unowned(connection, inquiry_id, row["payload"]):
                raise AuthorizationConflict("versioned owned mutation required")
            return self._append_legacy(connection, inquiry_id, row["payload"], body, sender_type)

    def list(self) -> list[InquiryResponse]:
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute("SELECT payload FROM inquiries ORDER BY id DESC").fetchall()
        return [_load_inquiry_payload(row[0]) for row in rows]

    @contextmanager
    def _transaction(self, *, require_owned_schema: bool = True):
        connection = None
        try:
            connection = (open_connection(self._db_path) if require_owned_schema else
                          sqlite3.connect(self._db_path, timeout=0.75, isolation_level=None))
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except sqlite3.Error:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise StorageUnavailable("inquiry storage unavailable") from None
        except Exception:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _positively_unowned(connection, inquiry_id: str, payload: str) -> bool:
        def trusted_marker() -> bool:
            try:
                value = json.loads(payload)
            except (TypeError, ValueError):
                return False
            return isinstance(value, dict) and value.get("_ownership") == EXPLICIT_UNOWNED_MARKER

        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        tables = {"shopping_customer_persistence_meta", "shopping_inquiry_ownership"}
        if not names & tables:
            # Schema absence cannot establish the persistence contract.  A
            # marker alone is not positive unowned evidence for durable
            # SQLite authorization.
            return False
        if not tables <= names:
            return False
        version = connection.execute(
            "SELECT version FROM shopping_customer_persistence_meta WHERE name='schema'"
        ).fetchone()
        columns = {row[1]: (row[2], row[3], row[5]) for row in connection.execute(
            "PRAGMA table_info(shopping_inquiry_ownership)")}
        if (version is None or version[0] != SCHEMA_VERSION or columns != {
                "inquiry_id": ("TEXT", 0, 1), "customer_id": ("TEXT", 1, 0),
                "session_id": ("TEXT", 1, 0), "version": ("INTEGER", 1, 0)}):
            return False
        if connection.execute("SELECT 1 FROM shopping_inquiry_ownership WHERE inquiry_id=?",
                              (inquiry_id,)).fetchone() is not None:
            return False
        # Row absence is not provenance. Use only the existing server-written
        # fresh-unowned marker, also required by the pre-B2 compatibility path.
        return trusted_marker()

    def _legacy_row(self, connection, inquiry_id: str, token: str):
        row = connection.execute("SELECT payload,token_hash FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
        if (row is None or not row["token_hash"]
                or not secrets.compare_digest(row["token_hash"], hashlib.sha256(token.encode()).hexdigest())
                or not self._positively_unowned(connection, inquiry_id, row["payload"])):
            return None
        return row

    def get_legacy_authorized(self, inquiry_id: str, token: str) -> InquiryResponse | None:
        with self._transaction(require_owned_schema=False) as connection:
            row = self._legacy_row(connection, inquiry_id, token)
            return _load_inquiry_payload(row["payload"]) if row is not None else None

    def append_legacy_authorized(self, inquiry_id: str, token: str, body: str) -> InquiryMessage | None:
        with self._transaction(require_owned_schema=False) as connection:
            row = self._legacy_row(connection, inquiry_id, token)
            if row is None:
                return None
            return self._append_legacy(connection, inquiry_id, row["payload"], body, "customer")

    @staticmethod
    def _append_legacy(connection, inquiry_id, raw, body, sender_type):
        item = _load_inquiry_payload(raw)
        result = InquiryMessage(id=secrets.token_urlsafe(18), inquiry_id=inquiry_id, sender_type=sender_type,
                                body=sanitize_message(body), created_at=datetime.now(timezone.utc).isoformat())
        item.messages.append(result)
        payload = item.model_dump(exclude={"public_access_token"})
        if json.loads(raw).get("_ownership") == "unowned/v1":
            payload["_ownership"] = "unowned/v1"
        connection.execute("UPDATE inquiries SET payload=? WHERE id=?", (json.dumps(payload), inquiry_id))
        return result

    def create_owned(self, request: InquiryCreateRequest, *, authority: InquirySessionAuthority,
                     product_loader: Callable[[str], dict]) -> tuple[InquiryResponse, int]:
        """One transaction for current authority, input, inquiry, ownership and audit."""
        with self._transaction() as connection:
            now = authority.revalidate(connection, self._db_path)
            request = InquiryCreateRequest.model_validate(request.model_dump())
            product = product_loader(request.product_id)
            if product["id"] != request.product_id:
                raise ValueError("invalid product")
            variants = product.get("variants", []) or []
            variant = next((item for item in variants if item["id"] == request.variant_id), None)
            if ((variants and request.variant_id is None) or (request.variant_id and variant is None)
                    or (variant is not None and variant["available"] is not True)):
                raise ValueError("invalid variant")
            canonical_product = Product(**{key: product[key] for key in Product.__dataclass_fields__})
            canonical_variant = ProductVariant(**variant) if variant else None
            # Allocate under the writer lock, independently of per-instance counters.
            number = connection.execute("SELECT COALESCE(MAX(CAST(substr(id,8) AS INTEGER)),0)+1 FROM inquiries").fetchone()[0]
            if not 1 <= number < 10**18:
                raise StorageUnavailable("inquiry identifiers unavailable")
            inquiry_id = f"AG-INQ-{number:06d}"
            item = InquiryResponse(id=inquiry_id, status="created",
                product=InquiryProduct(id=canonical_product.id, name=canonical_product.name),
                variant=InquiryVariant(id=canonical_variant.id, label=canonical_variant.label) if canonical_variant else None,
                formatted_message=format_message(inquiry_id, canonical_product, canonical_variant, sanitize_message(request.message)),
                contact_channels=configured_contact_channels())
            connection.execute("INSERT INTO inquiries(id,payload,token_hash) VALUES(?,?,'')",
                               (inquiry_id, item.model_dump_json(exclude={"public_access_token"})))
            connection.execute(
                "INSERT INTO shopping_inquiry_ownership(inquiry_id,customer_id,session_id,version) VALUES(?,?,?,0)",
                (inquiry_id, authority.customer_id, authority.session_id))
            connection.execute(
                "INSERT INTO shopping_inquiry_audit(event_id,actor_ref,resource_ref,action,outcome,correlation_id,occurred_at) VALUES(?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, authority.customer_id, inquiry_id, "INQUIRY_CREATE_OWNED", "APPLIED",
                 uuid.uuid4().hex, now.isoformat(timespec="microseconds").replace("+00:00", "Z")))
        with self._lock:
            self._next = max(self._next, number + 1)
        return item, 0

    def get_owned(self, inquiry_id: str, *, authority: InquirySessionAuthority) -> tuple[InquiryResponse, int]:
        with self._transaction() as connection:
            authority.revalidate(connection, self._db_path)
            owner = connection.execute(
                "SELECT customer_id,session_id,version FROM shopping_inquiry_ownership WHERE inquiry_id=?",
                (inquiry_id,)).fetchone()
            if owner is None or (owner["customer_id"], owner["session_id"]) != (authority.customer_id, authority.session_id):
                raise AuthorizationConflict("owned inquiry access denied")
            row = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()
            if row is None:
                raise AuthorizationConflict("owned inquiry access denied")
            return _load_inquiry_payload(row["payload"]), owner["version"]

    def append_owned_message(self, inquiry_id: str, request: OwnedInquiryMessageRequest, *,
                             authority: InquirySessionAuthority) -> InquiryMessage:
        return self.append_message_authorized(
            inquiry_id, request.body, "customer", customer_id=authority.customer_id,
            session_id=authority.session_id, expected_version=request.expected_version,
            idempotency_key=request.idempotency_key, actor_ref=authority.customer_id,
            correlation_id=uuid.uuid4().hex, now=authority.clock(), authority=authority,
        )
