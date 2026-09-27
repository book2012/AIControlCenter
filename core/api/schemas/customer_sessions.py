"""Closed, secret-free customer session HTTP outcomes."""
from enum import Enum
from typing import Literal

from core.api.schemas.customer_auth import PublicAuthContract


class SessionAPIError(str, Enum):
    INVALID_REQUEST = "customer_session_invalid_request"
    DENIED = "customer_session_denied"
    ORIGIN_DENIED = "customer_session_origin_denied"
    CSRF_DENIED = "customer_session_csrf_denied"
    UNAVAILABLE = "customer_session_unavailable"
    INTERNAL = "customer_session_internal_error"
    METHOD_DENIED = "customer_session_method_denied"


class LogoutResponse(PublicAuthContract):
    outcome: Literal["REVOKED"] = "REVOKED"
