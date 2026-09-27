"""In-memory Control Plane seam for provider-neutral phone verification.

This module is intentionally not production phone verification.  It has no
network or provider dependency.  Durable replay prevention and concurrency
control are deferred to a future explicitly authorized persistence boundary;
this phase keeps those indexes in memory only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re
from typing import Callable
import uuid

from pydantic import TypeAdapter

from core.shopping.customer_auth import (
    RECEIPT_MAX_LIFETIME, TrustedReceiptBinding, TrustedVerificationContext,
    TrustedVerificationReceipt, TrustedVerificationSeam, VerificationPurpose,
)
from core.shopping.customer_identity import CustomerId, require_utc
from core.shopping.phone_normalization import (
    CanonicalPhone, OpaquePhoneBinding, derive_phone_binding, normalize_phone,
)
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartRequest, ChallengeStartResult,
    ChallengeStatus, ChallengeSubject, ChallengeVerificationRequest,
    ChallengeVerificationResult, PhoneVerificationPort,
    ProviderSourceIdentifier, ProviderVerificationIdentifier, ReplayReference,
    VerificationStatus,
)


_OPAQUE = re.compile(r"^AG-[A-Z]{3}-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")
_CUSTOMER_ID = TypeAdapter(CustomerId)


class PhoneVerificationError(RuntimeError):
    """Sanitized fail-closed error; provider details never cross the seam."""


class PhoneVerificationRejected(PhoneVerificationError):
    pass


@dataclass(frozen=True)
class PhoneChallenge:
    """Validated start evidence plus local policy state, never raw phone data."""

    start_evidence: ChallengeStartResult
    customer_id: str
    browser_challenge: str
    local_expires_at: datetime

    def __repr__(self) -> str:
        return (
            "PhoneChallenge(start_evidence=<validated>, "
            f"customer_id={self.customer_id!r}, "
            f"browser_challenge={self.browser_challenge!r}, "
            f"local_expires_at={self.local_expires_at!r})"
        )


@dataclass(frozen=True)
class TrustedPhoneVerification:
    """Accepted provider evidence projected into the existing B3-A seam."""

    seam: TrustedVerificationSeam
    verification_evidence: ChallengeVerificationResult

    @property
    def receipt(self) -> TrustedVerificationReceipt:
        return self.seam.receipt

    @property
    def context(self) -> TrustedVerificationContext:
        return self.seam.context

    @property
    def trusted_receipt(self) -> TrustedVerificationReceipt:
        return self.seam.receipt

    @property
    def trusted_context(self) -> TrustedVerificationContext:
        return self.seam.context

    def __repr__(self) -> str:
        return (
            "TrustedPhoneVerification(seam=<trusted receipt/context>, "
            "verification_evidence=<validated>)"
        )


PhoneVerificationOutcome = TrustedPhoneVerification


@dataclass(frozen=True)
class _ChallengeState:
    challenge: PhoneChallenge
    replay_reference: ReplayReference
    provider_verification_id: ProviderVerificationIdentifier
    phone_binding: OpaquePhoneBinding
    purpose: VerificationPurpose
    request_fingerprint: str


@dataclass(frozen=True)
class _ReplayState:
    challenge_reference: ChallengeReference
    phone_binding: OpaquePhoneBinding
    purpose: VerificationPurpose
    otp_digest: str
    outcome: TrustedPhoneVerification | None = None


def _uuid4_shaped(prefix: str, seed: str) -> str:
    """Make a deterministic opaque ID with the repository's UUID4-shaped form."""

    raw = bytearray(hashlib.sha256(seed.encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return prefix + uuid.UUID(bytes=bytes(raw)).hex


def _as_identifier(value: object, kind: type) -> object:
    if isinstance(value, kind):
        return value
    if type(value) is str:
        try:
            return kind(value=value)
        except (TypeError, ValueError):
            pass
    raise PhoneVerificationRejected("phone verification evidence rejected")


def _opaque_ref(prefix: str, value: object) -> str:
    if type(value) is str and _OPAQUE.fullmatch(value):
        return value
    return _uuid4_shaped(prefix, str(value))


class PhoneVerificationService:
    """Control Plane policy seam over one injected provider-neutral port."""

    def __init__(
        self,
        port: PhoneVerificationPort,
        utc_clock: Callable[[], datetime] | None = None,
        phone_binding_key: bytes | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        binding_key: bytes | None = None,
        provider_source: ProviderSourceIdentifier | str = "synthetic.mock",
        issuer_ref: str | None = None,
        challenge_lifetime: timedelta = timedelta(minutes=5),
        evidence_max_age: timedelta = timedelta(minutes=5),
    ) -> None:
        if not hasattr(port, "start_challenge") or not hasattr(port, "verify_challenge"):
            raise TypeError("a phone verification port is required")
        if utc_clock is None:
            utc_clock = clock
        if phone_binding_key is None:
            phone_binding_key = binding_key
        if not callable(utc_clock):
            raise TypeError("an injected UTC clock is required")
        if type(phone_binding_key) is not bytes or not phone_binding_key:
            raise ValueError("phone binding key must be non-empty injected bytes")
        self._port = port
        self._clock = utc_clock
        self._binding_key = phone_binding_key
        self._provider_source = _as_identifier(provider_source, ProviderSourceIdentifier)
        if issuer_ref is None:
            issuer_ref = _uuid4_shaped("AG-ISS-", "issuer:" + str(self._provider_source))
        if type(issuer_ref) is not str or _OPAQUE.fullmatch(issuer_ref) is None or not issuer_ref.startswith("AG-ISS-"):
            raise ValueError("issuer reference is invalid")
        if (type(challenge_lifetime) is not timedelta or challenge_lifetime <= timedelta(0)
                or challenge_lifetime > RECEIPT_MAX_LIFETIME):
            raise ValueError("challenge lifetime is outside the local policy")
        if (type(evidence_max_age) is not timedelta or evidence_max_age <= timedelta(0)
                or evidence_max_age > RECEIPT_MAX_LIFETIME):
            raise ValueError("evidence age is outside the local policy")
        self._issuer_ref = issuer_ref
        self._challenge_lifetime = challenge_lifetime
        self._evidence_max_age = evidence_max_age
        self._challenges: dict[str, _ChallengeState] = {}
        self._start_replays: dict[str, str] = {}
        self._replays: dict[str, _ReplayState] = {}
        self._provider_ids: dict[tuple[str, str], str] = {}

    def _now(self) -> datetime:
        try:
            value = self._clock()
            return require_utc(value)
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise PhoneVerificationRejected("phone verification policy rejected") from None

    def _reference(
        self, value: object | None, kind: type, *, prefix: str, seed: str,
    ) -> object:
        if value is None:
            return kind(value=_uuid4_shaped(prefix, seed + ":" + uuid.uuid4().hex))
        return _as_identifier(value, kind)

    def start_challenge(
        self,
        phone: CanonicalPhone | str,
        *,
        customer_id: str,
        browser_challenge: str | None = None,
        country_calling_code: str | None = None,
        country_code: str | None = None,
        national_trunk_prefix: str | None = None,
        purpose: VerificationPurpose = VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference: ChallengeReference | str | None = None,
        replay_reference: ReplayReference | str | None = None,
    ) -> ChallengeStartResult:
        """Normalize locally, then accept only a strictly bound start result."""

        try:
            if type(purpose) is not VerificationPurpose:
                raise ValueError
            customer = _CUSTOMER_ID.validate_python(customer_id)
            canonical = phone if isinstance(phone, CanonicalPhone) else normalize_phone(
                phone, country_calling_code=country_calling_code,
                country_code=country_code,
                national_trunk_prefix=national_trunk_prefix,
            )
            if browser_challenge is None:
                browser = _opaque_ref(
                    "AG-CHL-", "browser:" + str(customer) + ":" + canonical.value,
                )
            elif type(browser_challenge) is str and _OPAQUE.fullmatch(browser_challenge):
                browser = browser_challenge
            else:
                raise ValueError
            challenge = self._reference(
                challenge_reference, ChallengeReference, prefix="AG-CHL-",
                seed="challenge:" + browser,
            )
            replay = self._reference(
                replay_reference, ReplayReference, prefix="AG-RPL-",
                seed="replay:" + str(challenge),
            )
            now = self._now()
            binding = derive_phone_binding(canonical, self._binding_key)
        except (TypeError, ValueError, PhoneVerificationRejected):
            raise PhoneVerificationRejected("phone verification request rejected") from None

        request = ChallengeStartRequest(
            provider_source=self._provider_source,
            purpose=purpose,
            challenge_reference=challenge,
            replay_reference=replay,
            subject=ChallengeSubject(phone_binding=binding),
        )
        existing = self._challenges.get(str(challenge))
        if existing is not None:
            if (
                existing.replay_reference != replay
                or existing.phone_binding != binding
                or existing.purpose is not purpose
                or existing.challenge.browser_challenge != browser
            ):
                raise PhoneVerificationRejected("challenge reference conflict")
            return existing.challenge.start_evidence
        prior_start = self._start_replays.get(str(replay))
        if prior_start is not None and prior_start != str(challenge):
            raise PhoneVerificationRejected("replay reference conflict")
        try:
            result = self._port.start_challenge(request)
        except Exception:
            raise PhoneVerificationRejected("phone verification provider failed") from None
        if type(result) is not ChallengeStartResult:
            raise PhoneVerificationRejected("phone verification evidence rejected")
        self._validate_start(result, request=request, now=now)

        local_expires = min(now + self._challenge_lifetime, now + RECEIPT_MAX_LIFETIME)
        state = _ChallengeState(
            challenge=PhoneChallenge(result, customer, browser, local_expires),
            replay_reference=replay,
            provider_verification_id=result.provider_verification_id,
            phone_binding=binding,
            purpose=purpose,
            request_fingerprint=self._fingerprint(result),
        )
        key = (str(result.provider_source), str(result.provider_verification_id))
        prior = self._provider_ids.get(key)
        if prior is not None and prior != self._fingerprint(result):
            raise PhoneVerificationRejected("ambiguous provider verification identifier")
        self._provider_ids[key] = state.request_fingerprint
        self._challenges[str(challenge)] = state
        self._start_replays[str(replay)] = str(challenge)
        return result

    def _validate_start(
        self, result: ChallengeStartResult, *, request: ChallengeStartRequest, now: datetime,
    ) -> None:
        if result.provider_source != request.provider_source:
            raise PhoneVerificationRejected("wrong provider source")
        if result.purpose is not request.purpose:
            raise PhoneVerificationRejected("wrong verification purpose")
        if result.challenge_reference != request.challenge_reference:
            raise PhoneVerificationRejected("wrong challenge reference")
        if result.replay_reference != request.replay_reference:
            raise PhoneVerificationRejected("wrong replay reference")
        if result.phone_binding != request.subject.phone_binding:
            raise PhoneVerificationRejected("wrong phone binding")
        if result.status not in {ChallengeStatus.STARTED, ChallengeStatus.PENDING}:
            raise PhoneVerificationRejected("challenge did not start")
        if result.started_at > now or now - result.started_at > self._evidence_max_age:
            raise PhoneVerificationRejected("invalid challenge timestamp")
        if result.provider_expires_at is not None and result.provider_expires_at <= now:
            raise PhoneVerificationRejected("challenge evidence expired")

    @staticmethod
    def _fingerprint(result: ChallengeStartResult) -> str:
        data = "|".join((
            str(result.provider_source), str(result.provider_verification_id),
            str(result.purpose), str(result.challenge_reference),
            str(result.replay_reference), str(result.phone_binding),
        ))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def verification_request(
        self,
        start: ChallengeStartResult,
        *,
        otp: str,
    ) -> ChallengeVerificationRequest:
        """Build a transport request from validated start evidence only."""

        if type(start) is not ChallengeStartResult:
            raise PhoneVerificationRejected("validated challenge start is required")
        state = self._challenges.get(str(start.challenge_reference))
        if state is None or state.challenge.start_evidence != start:
            raise PhoneVerificationRejected("unknown challenge")
        return ChallengeVerificationRequest(
            provider_source=start.provider_source,
            provider_verification_id=start.provider_verification_id,
            purpose=start.purpose,
            challenge_reference=start.challenge_reference,
            replay_reference=start.replay_reference,
            phone_binding=start.phone_binding,
            otp=otp,
        )

    def verify_challenge(
        self,
        request: ChallengeVerificationRequest | ChallengeStartResult | None = None,
        *,
        challenge_reference: ChallengeReference | str | None = None,
        replay_reference: ReplayReference | str | None = None,
        otp: str | None = None,
    ) -> TrustedPhoneVerification:
        """Verify one local challenge and project accepted evidence to B3-A."""

        if type(request) is ChallengeStartResult:
            if otp is None:
                raise PhoneVerificationRejected("verification OTP is required")
            request = self.verification_request(request, otp=otp)
        if request is None:
            if challenge_reference is None or replay_reference is None or otp is None:
                raise PhoneVerificationRejected("verification request is incomplete")
            challenge = _as_identifier(challenge_reference, ChallengeReference)
            replay = _as_identifier(replay_reference, ReplayReference)
            state = self._challenges.get(str(challenge))
            if state is None:
                raise PhoneVerificationRejected("unknown challenge")
            request = self.verification_request(state.challenge.start_evidence, otp=otp)
            if request.replay_reference != replay:
                raise PhoneVerificationRejected("replay reference conflict")
        elif type(request) is not ChallengeVerificationRequest:
            raise PhoneVerificationRejected("verification request is malformed")

        state = self._challenges.get(str(request.challenge_reference))
        if state is None:
            raise PhoneVerificationRejected("unknown challenge")
        if (
            request.provider_source != self._provider_source
            or request.provider_verification_id != state.provider_verification_id
            or request.purpose is not state.purpose
            or request.replay_reference != state.replay_reference
            or request.phone_binding != state.phone_binding
        ):
            raise PhoneVerificationRejected("verification binding rejected")

        now = self._now()
        if now >= state.challenge.local_expires_at:
            raise PhoneVerificationRejected("local challenge expired")
        replay_key = str(request.replay_reference)
        otp_digest = hashlib.sha256(request.otp.encode("utf-8")).hexdigest()
        prior_replay = self._replays.get(replay_key)
        if prior_replay is not None:
            if (
                prior_replay.challenge_reference != request.challenge_reference
                or prior_replay.phone_binding != request.phone_binding
                or prior_replay.purpose is not request.purpose
                or prior_replay.otp_digest != otp_digest
                or prior_replay.outcome is None
            ):
                raise PhoneVerificationRejected("replay conflict")
            return prior_replay.outcome

        try:
            result = self._port.verify_challenge(request)
        except Exception:
            raise PhoneVerificationRejected("phone verification provider failed") from None
        if type(result) is not ChallengeVerificationResult:
            raise PhoneVerificationRejected("phone verification evidence rejected")
        self._validate_verification(result, request=request, state=state, now=now)

        provider_key = (str(result.provider_source), str(result.provider_verification_id))
        known_provider = self._provider_ids.get(provider_key)
        if known_provider != state.request_fingerprint:
            raise PhoneVerificationRejected("ambiguous provider verification identifier")

        receipt = TrustedVerificationReceipt(
            receipt_id=_uuid4_shaped("AG-VRF-", "receipt:" + replay_key),
            purpose=VerificationPurpose.SESSION_ISSUANCE,
            browser_challenge=state.challenge.browser_challenge,
            issuer_ref=self._issuer_ref,
            customer_id=state.challenge.customer_id,
            issued_at=now,
            expires_at=min(state.challenge.local_expires_at, now + RECEIPT_MAX_LIFETIME),
        )
        context = TrustedVerificationContext(accepted_bindings=frozenset({
            TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, receipt.customer_id),
        }))
        outcome = TrustedPhoneVerification(
            seam=TrustedVerificationSeam(receipt=receipt, context=context),
            verification_evidence=result,
        )
        self._replays[replay_key] = _ReplayState(
            request.challenge_reference, request.phone_binding, request.purpose,
            otp_digest, outcome,
        )
        return outcome

    def _validate_verification(
        self,
        result: ChallengeVerificationResult,
        *,
        request: ChallengeVerificationRequest,
        state: _ChallengeState,
        now: datetime,
    ) -> None:
        if result.provider_source != request.provider_source:
            raise PhoneVerificationRejected("wrong provider source")
        if result.provider_verification_id != request.provider_verification_id:
            raise PhoneVerificationRejected("wrong provider verification identifier")
        if result.purpose is not request.purpose:
            raise PhoneVerificationRejected("wrong verification purpose")
        if result.challenge_reference != request.challenge_reference:
            raise PhoneVerificationRejected("wrong challenge reference")
        if result.replay_reference != request.replay_reference:
            raise PhoneVerificationRejected("wrong replay reference")
        if result.phone_binding != request.phone_binding:
            raise PhoneVerificationRejected("wrong phone binding")
        if result.status is not VerificationStatus.SUCCESS:
            raise PhoneVerificationRejected("verification did not succeed")
        if result.verified_at > now or now - result.verified_at > self._evidence_max_age:
            raise PhoneVerificationRejected("invalid verification timestamp")
        if result.provider_expires_at is not None and result.provider_expires_at <= now:
            raise PhoneVerificationRejected("verification evidence expired")
        if result.verified_at >= state.challenge.local_expires_at:
            raise PhoneVerificationRejected("verification exceeds local expiry")


__all__ = [
    "PhoneChallenge",
    "PhoneVerificationError",
    "PhoneVerificationOutcome",
    "PhoneVerificationRejected",
    "PhoneVerificationService",
    "TrustedPhoneVerification",
]
