"""Strict RFC 8785 profile used only by the SEC-02 trust boundary."""

from __future__ import annotations

import json
from typing import Any

import rfc8785

SAFE_INTEGER = 9_007_199_254_740_991


class CanonicalizationError(ValueError):
    """Input is outside the AIControlCenter strict canonical JSON profile."""


def _reject_float(_: str) -> None:
    raise CanonicalizationError("floating-point JSON values are prohibited")


def _integer(value: str) -> int:
    parsed = int(value)
    if not -SAFE_INTEGER <= parsed <= SAFE_INTEGER:
        raise CanonicalizationError("integer is outside the JavaScript safe range")
    return parsed


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalizationError("duplicate object key")
        result[key] = value
    return result


def _validate_strict_value(value: Any) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, float):
        raise CanonicalizationError("floating-point values are prohibited")
    if isinstance(value, int):
        if not -SAFE_INTEGER <= value <= SAFE_INTEGER:
            raise CanonicalizationError("integer is outside the JavaScript safe range")
        return
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise CanonicalizationError("surrogate code points are prohibited")
        return
    elif isinstance(value, list):
        for item in value:
            _validate_strict_value(item)
        return
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("object keys must be strings")
            _validate_strict_value(key)
            _validate_strict_value(item)
        return
    raise CanonicalizationError("value is not JSON-compatible")


def parse_json_bytes(raw: bytes) -> Any:
    """Parse bytes without discarding duplicate-key or numeric evidence."""
    if not isinstance(raw, bytes):
        raise CanonicalizationError("raw input must be bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CanonicalizationError("UTF-8 BOM is prohibited")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_object,
            parse_float=_reject_float,
            parse_int=_integer,
            parse_constant=_reject_float,
        )
    except CanonicalizationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise CanonicalizationError("invalid strict JSON input") from error
    _validate_strict_value(value)
    return value


def canonicalize(value: Any) -> bytes:
    """Encode with RFC 8785 after enforcing the stricter local profile."""
    _validate_strict_value(value)
    try:
        return rfc8785.dumps(value)
    except (rfc8785.CanonicalizationError, TypeError, ValueError) as error:
        raise CanonicalizationError("value cannot be canonically encoded") from error


def parse_canonical_json(raw: bytes) -> Any:
    value = parse_json_bytes(raw)
    if canonicalize(value) != raw:
        raise CanonicalizationError("raw JSON is not its RFC 8785 encoding")
    return value
