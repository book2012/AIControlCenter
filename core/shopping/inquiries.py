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
    """Application-state repository for preview/tests; replaceable by durable storage."""
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
            self._items[inquiry_id] = result
            self._tokens[inquiry_id] = hashlib.sha256(token.encode()).hexdigest()
            return result

    def get(self, inquiry_id: str) -> InquiryResponse | None:
        return self._items.get(inquiry_id)

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
        return list(self._items.values())


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

    def create(self, product: Product, variant: ProductVariant | None, message: str) -> InquiryResponse:
        result = super().create(product, variant, message)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute("INSERT INTO inquiries (id, payload, token_hash) VALUES (?, ?, ?)", (result.id, result.model_dump_json(), self._tokens[result.id]))
        return result

    def get(self, inquiry_id: str) -> InquiryResponse | None:
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute("SELECT payload FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return InquiryResponse.model_validate(json.loads(row[0])) if row else None

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
        return [InquiryResponse.model_validate(json.loads(row[0])) for row in rows]
