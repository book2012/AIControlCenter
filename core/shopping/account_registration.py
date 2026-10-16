"""Side-effect-free account-registration input contract.

This module validates a candidate only. It does not verify contact ownership,
persist data, call providers, create WooCommerce customers, or enable signup.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re


_USERNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{3,19}\Z", re.ASCII)
_EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+\Z", re.ASCII)
_PHONE = re.compile(r"\+8210[0-9]{8}\Z", re.ASCII)


class SignupInputError(ValueError):
    """Stable, value-free validation error suitable for a public boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class SignupCandidate:
    login_id: str = field(repr=False)
    email: str = field(repr=False)
    password: str = field(repr=False)
    password_confirmation: str = field(repr=False)
    phone: str = field(repr=False)
    terms_accepted: bool
    privacy_accepted: bool
    terms_version: str = field(repr=False)
    privacy_notice_version: str = field(repr=False)

    def __repr__(self) -> str:
        return "SignupCandidate(private_fields=<redacted>, terms_accepted=<redacted>, privacy_accepted=<redacted>)"


@dataclass(frozen=True)
class ValidatedSignupCandidate:
    """Validated values; still unverified and not safe to persist."""

    login_id: str = field(repr=False)
    email: str = field(repr=False)
    password: str = field(repr=False)
    phone: str = field(repr=False)
    terms_version: str = field(repr=False)
    privacy_notice_version: str = field(repr=False)
    privacy_accepted: bool

    def __repr__(self) -> str:
        return "ValidatedSignupCandidate(private_fields=<redacted>)"


def validate_signup_candidate(candidate: SignupCandidate) -> ValidatedSignupCandidate:
    """Validate the first-step field contract without external or persistent effects.

    Contact verification tickets and uniqueness claims are intentionally handled
    by later service stages. This function must not be treated as authorization
    to create a WooCommerce account.
    """
    if type(candidate) is not SignupCandidate:
        raise SignupInputError("SIGNUP_INPUT_INVALID")

    if type(candidate.login_id) is not str or not _USERNAME.fullmatch(candidate.login_id):
        raise SignupInputError("SIGNUP_LOGIN_ID_INVALID")
    if type(candidate.email) is not str or len(candidate.email) > 254 or not _EMAIL.fullmatch(candidate.email):
        raise SignupInputError("SIGNUP_EMAIL_INVALID")
    if (type(candidate.password) is not str or not 8 <= len(candidate.password) <= 128
            or candidate.password != candidate.password_confirmation):
        raise SignupInputError("SIGNUP_PASSWORD_INVALID")
    if type(candidate.phone) is not str or not _PHONE.fullmatch(candidate.phone):
        raise SignupInputError("SIGNUP_PHONE_INVALID")
    if candidate.terms_accepted is not True:
        raise SignupInputError("SIGNUP_TERMS_REQUIRED")
    if candidate.privacy_accepted is not True:
        raise SignupInputError("SIGNUP_PRIVACY_CONSENT_REQUIRED")
    if (type(candidate.terms_version) is not str or not 1 <= len(candidate.terms_version) <= 64
            or candidate.terms_version != candidate.terms_version.strip()):
        raise SignupInputError("SIGNUP_TERMS_VERSION_INVALID")
    if (type(candidate.privacy_notice_version) is not str
            or not 1 <= len(candidate.privacy_notice_version) <= 64
            or candidate.privacy_notice_version != candidate.privacy_notice_version.strip()):
        raise SignupInputError("SIGNUP_PRIVACY_NOTICE_VERSION_INVALID")

    return ValidatedSignupCandidate(
        login_id=candidate.login_id,
        email=candidate.email,
        password=candidate.password,
        phone=candidate.phone,
        terms_version=candidate.terms_version,
        privacy_notice_version=candidate.privacy_notice_version,
        privacy_accepted=True,
    )


__all__ = [
    "SignupCandidate", "SignupInputError", "ValidatedSignupCandidate",
    "validate_signup_candidate",
]
