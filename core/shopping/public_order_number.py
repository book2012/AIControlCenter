"""Stable customer-facing order numbers; provider IDs remain internal."""
from datetime import datetime, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo
import re


def _phone_digits(phone: str) -> str:
    value = re.sub(r"\D", "", str(phone or ""))
    if value.startswith("82"):
        value = "0" + value[2:]
    return value


def public_order_number(*, requested_at, phone: str, entropy: str) -> str:
    """Return YYMMDD + last two phone digits + stable two-digit suffix."""
    try:
        date = datetime.fromisoformat(str(requested_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        date = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    date = date.astimezone(ZoneInfo("Asia/Seoul"))
    digits = _phone_digits(phone)
    phone_part = (digits[-2:] if len(digits) >= 2 else "00")
    suffix = int(sha256(str(entropy).encode("utf-8")).hexdigest()[:8], 16) % 100
    return f"{date:%y%m%d}{phone_part}{suffix:02d}"


def is_public_order_number(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", str(value or "").strip().removeprefix("#")))
