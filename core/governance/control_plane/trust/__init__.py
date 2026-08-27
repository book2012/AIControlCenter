"""Generic verify-only trusted-human authorization boundary."""

from .intake import intake_trusted_authorization
from .verification import parse_authorization_envelope, parse_registry, verify_authorization_envelope

__all__ = (
    "parse_authorization_envelope",
    "parse_registry",
    "verify_authorization_envelope",
    "intake_trusted_authorization",
)
