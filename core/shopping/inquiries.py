"""AIControlCenter-owned, read-only inquiry state and trusted handoff config."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
import hashlib
import secrets
import os
from threading import Lock
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from core.shopping.models import Product, ProductVariant

from core.shopping.customer_persistence import (
    AuthorizationConflict, IdempotencyConflict, InquiryVersionConflict,
    OwnershipConflict, StorageUnavailable, open_connection,
    initialize_schema, persisted_session_status,
)
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
                                  now: datetime) -> InquiryMessage:
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
            connection.execute("INSERT INTO inquiries (id, payload, token_hash) VALUES (?, ?, ?)", (result.id, result.model_dump_json(), self._tokens[result.id]))
        return result
    def get(self, inquiry_id: str) -> InquiryResponse | None:
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute("SELECT payload FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return _load_inquiry_payload(row[0]) if row else None

    def authorize(self, inquiry_id: str, token: str) -> bool:
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute("SELECT token_hash FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return bool(row and row[0] and secrets.compare_digest(row[0], hashlib.sha256(token.encode()).hexdigest()))

    def append_message(self, inquiry_id: str, body: str, sender_type: str) -> InquiryMessage | None:
        item = self.get(inquiry_id)
        if item is None:
            return None
        result = InquiryMessage(id=secrets.token_urlsafe(18), inquiry_id=inquiry_id, sender_type=sender_type,
                                body=sanitize_message(body), created_at=datetime.now(timezone.utc).isoformat())
        item.messages.append(result)
        if result:
            with sqlite3.connect(self._db_path) as connection:
                connection.execute("UPDATE inquiries SET payload = ? WHERE id = ?", (item.model_dump_json(), inquiry_id))
        return result
    def list(self) -> list[InquiryResponse]:
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute("SELECT payload FROM inquiries ORDER BY id DESC").fetchall()
        return [_load_inquiry_payload(row[0]) for row in rows]
