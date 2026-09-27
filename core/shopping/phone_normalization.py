"""Pure, provider-neutral phone normalization and opaque binding values."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import re


_DIGITS = re.compile(r"^[0-9]+$")
_CANONICAL = re.compile(r"^\+[1-9][0-9]{7,14}$")
_SEPARATORS = re.compile(r"[\s().-]")
_CALLING_CODE = re.compile(r"^\+[1-9][0-9]{0,2}$")
_BINDING = re.compile(r"^phb_[0-9a-f]{64}$")


class PhoneNormalizationError(ValueError):
    """The supplied number is not an unambiguous canonical phone value."""


@dataclass(frozen=True)
class CanonicalPhone:
    """An immutable canonical E.164-like phone representation."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or _CANONICAL.fullmatch(self.value) is None:
            raise PhoneNormalizationError("phone is not canonical E.164-like data")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        """Keep accidental diagnostics from rendering contact data."""

        return "CanonicalPhone(<redacted>)"


@dataclass(frozen=True)
class OpaquePhoneBinding:
    """A keyed, non-reversible phone binding safe for contract boundaries."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or _BINDING.fullmatch(self.value) is None:
            raise ValueError("phone binding is not a valid opaque binding")

    def __str__(self) -> str:
        return self.value


# Short alias for callers that describe the value as a phone binding.
PhoneBinding = OpaquePhoneBinding


def _clean(value: str) -> str:
    if type(value) is not str:
        raise PhoneNormalizationError("phone must be a string")
    value = value.strip()
    if not value:
        raise PhoneNormalizationError("phone is empty")
    return _SEPARATORS.sub("", value)


def _validate_canonical(value: str) -> CanonicalPhone:
    if _CANONICAL.fullmatch(value) is None:
        raise PhoneNormalizationError("phone is not a strict E.164-like number")
    return CanonicalPhone(value)


def normalize_phone(
    value: str,
    *,
    country_calling_code: str | None = None,
    country_code: str | None = None,
    national_trunk_prefix: str | None = None,
) -> CanonicalPhone:
    """Normalize only unambiguous input; national input requires explicit code.

    Country context is a calling code such as ``+82``.  It is never inferred
    from locale, environment, provider defaults, or the shape of the number.
    National input also requires its explicit trunk prefix, such as ``0``.
    International input must already carry ``+`` and cannot be combined with
    either form of national context.
    """

    if country_calling_code is not None and country_code is not None:
        raise PhoneNormalizationError("country context was supplied twice")
    if country_code is not None:
        if type(country_code) is not str:
            raise PhoneNormalizationError("country code is invalid")
        country_calling_code = country_code

    cleaned = _clean(value)
    if country_calling_code is not None:
        if type(country_calling_code) is not str:
            raise PhoneNormalizationError("country calling code is invalid")
        context = country_calling_code.strip()
        if _CALLING_CODE.fullmatch(context) is None:
            raise PhoneNormalizationError("country calling code is invalid")
    else:
        context = None

    if national_trunk_prefix is not None:
        if (type(national_trunk_prefix) is not str
                or _DIGITS.fullmatch(national_trunk_prefix) is None):
            raise PhoneNormalizationError("national trunk prefix is invalid")
        trunk_prefix = national_trunk_prefix
    else:
        trunk_prefix = None

    if cleaned.startswith("+"):
        if context is not None or trunk_prefix is not None:
            raise PhoneNormalizationError("national context is only for national input")
        return _validate_canonical(cleaned)

    # A leading 00 or a bare international-looking digit string is ambiguous.
    # National input must have both an explicit trunk prefix and calling code.
    if (context is None or trunk_prefix is None
            or cleaned.startswith("00") or not _DIGITS.fullmatch(cleaned)):
        raise PhoneNormalizationError(
            "national phone requires explicit country and trunk context",
        )
    if not cleaned.startswith(trunk_prefix) or len(cleaned) <= len(trunk_prefix):
        raise PhoneNormalizationError("national phone format is ambiguous")
    return _validate_canonical(context + cleaned[len(trunk_prefix):])


def derive_phone_binding(
    phone: CanonicalPhone | str,
    binding_key: bytes,
) -> OpaquePhoneBinding:
    """Derive a deterministic opaque binding using an injected server key."""

    if isinstance(phone, CanonicalPhone):
        canonical = phone
    elif type(phone) is str:
        canonical = normalize_phone(phone)
    else:
        raise TypeError("phone must be canonical phone data")
    if type(binding_key) is not bytes or not binding_key:
        raise ValueError("phone binding key must be non-empty injected bytes")
    digest = hmac.new(binding_key, canonical.value.encode("ascii"), hashlib.sha256).hexdigest()
    return OpaquePhoneBinding("phb_" + digest)


# Explicitly named alias for callers that want the security property in code.
derive_opaque_phone_binding = derive_phone_binding


__all__ = [
    "CanonicalPhone",
    "OpaquePhoneBinding",
    "PhoneBinding",
    "PhoneNormalizationError",
    "derive_opaque_phone_binding",
    "derive_phone_binding",
    "normalize_phone",
]
