"""Pure canonical JSON and digest helpers for DPL contracts."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any


class CanonicalJSONError(ValueError):
    """Raised when a value cannot be represented as canonical JSON."""


def _check_json(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise CanonicalJSONError(f"{path}: non-finite number")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise CanonicalJSONError(f"{path}: object key is not a string")
            _check_json(child, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value):
            _check_json(child, f"{path}[{index}]")
        return
    raise CanonicalJSONError(f"{path}: value is not JSON-compatible")


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON without mutating *value*."""
    _check_json(value)
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise CanonicalJSONError("Unable to serialize canonical JSON") from error
    return text.encode("utf-8")


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def verify_digest(value: Any, expected_digest: str) -> bool:
    if not isinstance(expected_digest, str):
        return False
    return hmac.compare_digest(sha256_digest(value), expected_digest)


__all__ = (
    "CanonicalJSONError",
    "canonical_json_bytes",
    "sha256_digest",
    "verify_digest",
)
