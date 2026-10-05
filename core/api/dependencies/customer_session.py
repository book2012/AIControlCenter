"""Explicit isolated API composition; no database, issuer, or runtime defaults.

B3-B validates (session_id, secret, customer_id), not a cookie alone. This
bounded process-local index retains only a digest and server-issued references.
It is populated exclusively after trusted issuance and service validation.
Restart, eviction, or a different boundary instance denies access; it never
reconstructs authority from client claims. Durable validity/revocation remains
in B3-B. This is not a multi-worker or production composition.

CSRF uses a domain-separated HMAC over that binding and an explicitly injected
server key. No raw cookie or CSRF token is retained, and no schema changes are
needed. Trusted receipt resolution has no implementation or default here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import re
from threading import RLock
from typing import Callable
from urllib.parse import urlsplit
import uuid

from fastapi import Request
from pydantic import SecretBytes

from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
from core.api.schemas.customer_sessions import SessionAPIError
from core.shopping.customer_auth import TrustedVerificationContext, TrustedVerificationReceipt
from core.shopping.customer_identity import require_utc
from core.shopping.customer_session_service import (
    CustomerSessionService, IssuedSession, SessionValidationCode,
)
from core.shopping.customer_sessions import SafeSessionProjection


COOKIE_NAME = "__Host-aicc_customer"
CSRF_HEADER = "X-CSRF-Token"
_SECRET = re.compile(r"[A-Za-z0-9_-]{43}\Z")


class SessionAPIDenied(Exception):
    def __init__(self, code: SessionAPIError, *, clear_cookie: bool = False):
        super().__init__(code.value)
        self.code = code
        self.clear_cookie = clear_cookie


@dataclass(frozen=True, repr=False)
class TrustedSessionEvidence:
    """Server-only resolver result; parsing browser JSON cannot supply this."""

    receipt: TrustedVerificationReceipt
    context: TrustedVerificationContext
    expected_challenge: str


@dataclass(frozen=True)
class _Binding:
    session_id: str
    customer_id: str
    expires_at: datetime


def _digest(secret: str) -> str:
    return hashlib.sha256(b"aicc/browser-session/v1\0" + secret.encode("ascii")).hexdigest()


class CustomerSessionBoundary:
    def __init__(
        self, *, service: CustomerSessionService, trusted_origin: str,
        csrf_key: SecretBytes, clock: Callable[[], datetime],
        resolve_evidence: Callable[[VerificationReceiptConsumeRequest], TrustedSessionEvidence] | None = None,
        max_bindings: int = 1024,
        recover_durable_bindings: bool = False,
    ):
        # Exact canonical HTTPS origin only; never infer it from Host/Forwarded.
        parsed = urlsplit(trusted_origin)
        if (not re.fullmatch(r"https://[a-z0-9]+(?:[.-][a-z0-9]+)*(?::[1-9][0-9]{0,4})?", trusted_origin)
                or parsed.port is not None and not 1 <= parsed.port <= 65535):
            raise ValueError("an explicit canonical HTTPS origin is required")
        if not isinstance(csrf_key, SecretBytes) or len(csrf_key.get_secret_value()) < 32:
            raise ValueError("an explicit server CSRF key is required")
        if type(max_bindings) is not int or not 1 <= max_bindings <= 10000:
            raise ValueError("a bounded session index is required")
        if type(recover_durable_bindings) is not bool:
            raise ValueError("explicit durable recovery mode required")
        self._recover_durable_bindings = recover_durable_bindings
        self.service = service
        self.trusted_origin = trusted_origin
        self._csrf_key = csrf_key
        self.clock = clock
        self.resolve_evidence = resolve_evidence
        self._max_bindings = max_bindings
        self._bindings: dict[str, _Binding] = {}
        self._lock = RLock()

    def now(self) -> datetime:
        return require_utc(self.clock())

    def check_origin(self, request: Request, *, required: bool) -> None:
        origins = request.headers.getlist("origin")
        provenance = request.headers.getlist("sec-fetch-site")
        if ((required and not origins)
                or (origins and origins != [self.trusted_origin])
                or (provenance and provenance != ["same-origin"])):
            raise SessionAPIDenied(SessionAPIError.ORIGIN_DENIED)

    def cookie_secret(self, request: Request) -> str:
        # Reject ambiguous duplicate cookies instead of relying on parser order.
        values = [part.strip().partition("=")[2]
                  for header in request.headers.getlist("cookie")
                  for part in header.split(";")
                  if part.strip().partition("=")[0] == COOKIE_NAME]
        if len(values) != 1 or not _SECRET.fullmatch(values[0]):
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        return values[0]

    @staticmethod
    def has_cookie(request: Request) -> bool:
        return any(part.strip().partition("=")[0] == COOKIE_NAME
                   for header in request.headers.getlist("cookie") for part in header.split(";"))

    @staticmethod
    def _projection(value: object, now: datetime) -> SafeSessionProjection:
        if type(value) is not SafeSessionProjection:
            raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
        projection = SafeSessionProjection.model_validate(value)
        if (projection.revoked_at is not None or projection.last_activity_at > now
                or now >= min(projection.idle_expires_at, projection.absolute_expires_at)):
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        return projection

    def _validate(self, secret: str, binding: _Binding, now: datetime) -> SafeSessionProjection:
        checked = self.service.validate_session(
            binding.session_id, secret, binding.customer_id, now=now,
        )
        if checked.code == SessionValidationCode.STORAGE_UNAVAILABLE:
            raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
        if checked.code != SessionValidationCode.VALID:
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        projection = self._projection(checked.projection, now)
        if (projection.id != binding.session_id or projection.customer_id != binding.customer_id):
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        return projection

    def authenticate(self, secret: str, *, now: datetime) -> SafeSessionProjection:
        with self._lock:
            binding = self._bindings.get(_digest(secret))
        if binding is None and self._recover_durable_bindings:
            checked=self.service.validate_credential_session(secret,now=now)
            if checked.code==SessionValidationCode.STORAGE_UNAVAILABLE:
                raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
            if checked.code!=SessionValidationCode.VALID:
                raise SessionAPIDenied(SessionAPIError.DENIED,clear_cookie=True)
            projection=self._projection(checked.projection,now)
            binding=_Binding(projection.id,projection.customer_id,min(projection.idle_expires_at,projection.absolute_expires_at))
            with self._lock:
                self._bindings={key:value for key,value in self._bindings.items() if now<value.expires_at}
                if len(self._bindings)>=self._max_bindings:
                    raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
                self._bindings[_digest(secret)]=binding
        if binding is None:
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        # Always ask B3-B about current customer state, credential and revocation.
        projection = self._validate(secret, binding, now)
        if now >= binding.expires_at:
            raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
        return projection

    def csrf_token(self, secret: str, projection: SafeSessionProjection) -> str:
        message = "\0".join(("aicc/customer-csrf/v1", self.trusted_origin,
                             _digest(secret), projection.id, projection.customer_id))
        return hmac.new(self._csrf_key.get_secret_value(), message.encode("ascii"), hashlib.sha256).hexdigest()

    def check_csrf(self, request: Request, secret: str, projection: SafeSessionProjection) -> None:
        tokens = request.headers.getlist(CSRF_HEADER)
        if (len(tokens) != 1 or not re.fullmatch(r"[0-9a-f]{64}", tokens[0])
                or not hmac.compare_digest(tokens[0], self.csrf_token(secret, projection))):
            raise SessionAPIDenied(SessionAPIError.CSRF_DENIED)

    def issue(self, payload: VerificationReceiptConsumeRequest, *, now: datetime) -> IssuedSession:
        if self.resolve_evidence is None:
            raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
        evidence = self.resolve_evidence(payload)
        if type(evidence) is not TrustedSessionEvidence:
            raise SessionAPIDenied(SessionAPIError.DENIED)
        with self._lock:
            self._bindings = {key: value for key, value in self._bindings.items() if now < value.expires_at}
            if len(self._bindings) >= self._max_bindings:
                raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
            issued = self.service.consume_receipt_and_create_session(
                evidence.receipt, expected_challenge=evidence.expected_challenge,
                trusted_context=evidence.context, now=now, correlation_id=uuid.uuid4().hex,
            )
            projection = self._projection(issued.projection, now)
            secret = issued.session_secret.get_secret_value()
            if (not _SECRET.fullmatch(secret) or issued.session_id != projection.id
                    or _digest(secret) in self._bindings):
                raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
            binding = _Binding(projection.id, projection.customer_id,
                               min(projection.idle_expires_at, projection.absolute_expires_at))
            checked = self._validate(secret, binding, now)
            if checked != projection:
                raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
            self._bindings[_digest(secret)] = binding
            return issued

    def revoke(self, secret: str, projection: SafeSessionProjection, *, now: datetime) -> None:
        result = self.service.revoke_session(
            projection.id, now=now, actor_ref=projection.customer_id, correlation_id=uuid.uuid4().hex,
        )
        if result.code not in {"REVOKED", "ALREADY_REVOKED"}:
            raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
        with self._lock:
            self._bindings.pop(_digest(secret), None)


def get_customer_session_boundary() -> CustomerSessionBoundary:
    """Must be explicitly overridden; importing/registering routes creates no authority."""
    raise SessionAPIDenied(SessionAPIError.UNAVAILABLE)
