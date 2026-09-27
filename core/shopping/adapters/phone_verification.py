"""Provider-neutral phone-verification adapter over a typed transport."""
from __future__ import annotations

from typing import Any

from core.secrets.ports import SecretReference
from core.shopping.ports.phone_verification import (
    ChallengeStartRequest, ChallengeStartResult, ChallengeStatus,
    ChallengeVerificationRequest, ChallengeVerificationResult,
    PhoneVerificationPort, ProviderSourceIdentifier,
    VerificationStatus,
)
from core.shopping.ports.phone_verification_transport import (
    DEFAULT_PROVIDER_TIMEOUT_SECONDS, MAX_PROVIDER_TIMEOUT_SECONDS,
    ProviderTransportError, ProviderTransportFailureCode, ProviderTransportPort,
    ProviderTransportStartRequest, ProviderTransportStartResult,
    ProviderTransportStartStatus, ProviderTransportVerificationStatus,
    ProviderTransportVerifyRequest, ProviderTransportVerifyResult,
)


class ProviderPhoneVerificationError(RuntimeError):
    """Sanitized adapter failure; transport exception text never crosses out."""

    def __init__(self, code: ProviderTransportFailureCode) -> None:
        try:
            normalized = ProviderTransportFailureCode(code)
        except (TypeError, ValueError):
            normalized = ProviderTransportFailureCode.UNKNOWN_OUTCOME
        self.code = normalized
        self.failure_code = normalized
        self.reason_code = normalized
        super().__init__(normalized.value)

    def __str__(self) -> str:
        return self.code.value

    def __repr__(self) -> str:
        return f"ProviderPhoneVerificationError(code={self.code.value!r})"


ProviderAdapterFailureCode = ProviderTransportFailureCode
ProviderAdapterErrorCode = ProviderTransportFailureCode
ProviderAdapterError = ProviderPhoneVerificationError


class ProviderPhoneVerificationAdapter(PhoneVerificationPort):
    """Translate C1 application contracts to bounded transport evidence.

    The adapter has no clock or durable state.  Request bindings are copied
    from the trusted request, while the transport contributes only bounded
    provider identifier, status, and UTC timestamp evidence.
    """

    def __init__(
        self,
        transport: ProviderTransportPort,
        provider_source: ProviderSourceIdentifier | str = "synthetic.mock",
        *,
        secret_reference: SecretReference | None = None,
        timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    ) -> None:
        start_method = getattr(transport, "start", None) or getattr(
            transport, "start_challenge", None,
        )
        verify_method = getattr(transport, "verify", None) or getattr(
            transport, "verify_challenge", None,
        )
        if not callable(start_method) or not callable(verify_method):
            raise TypeError("a provider transport is required")
        try:
            self._provider_source = (
                provider_source
                if isinstance(provider_source, ProviderSourceIdentifier)
                else ProviderSourceIdentifier(value=provider_source)
            )
            if type(timeout_seconds) not in (int, float):
                raise ValueError
            if not 0 < timeout_seconds <= MAX_PROVIDER_TIMEOUT_SECONDS:
                raise ValueError
            if secret_reference is not None and type(secret_reference) is not SecretReference:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("provider adapter configuration is invalid") from None
        self._transport = transport
        self._transport_start = start_method
        self._transport_verify = verify_method
        self._secret_reference = secret_reference
        self.timeout_seconds = float(timeout_seconds)

    @property
    def provider_source(self) -> ProviderSourceIdentifier:
        return self._provider_source

    @property
    def secret_reference(self) -> SecretReference | None:
        """Return metadata only; this property never resolves credentials."""

        return self._secret_reference

    def __repr__(self) -> str:
        return (
            "ProviderPhoneVerificationAdapter("
            f"provider_source={str(self._provider_source)!r}, "
            f"transport={type(self._transport).__name__!r}, "
            f"secret_reference={self._secret_reference!r})"
        )

    def start_challenge(self, request: ChallengeStartRequest) -> ChallengeStartResult:
        if type(request) is not ChallengeStartRequest:
            self._raise(ProviderTransportFailureCode.REJECTED)
        self._validate_source(request.provider_source)
        transport_request = ProviderTransportStartRequest(
            provider_source=request.provider_source,
            purpose=request.purpose,
            phone_binding=request.subject.phone_binding,
            destination_handle=request.destination_handle,
            timeout_seconds=self.timeout_seconds,
        )
        result = self._invoke("START", self._transport_start, transport_request)
        if type(result) is not ProviderTransportStartResult:
            self._raise(ProviderTransportFailureCode.MALFORMED_RESPONSE)
        try:
            status = {
                ProviderTransportStartStatus.STARTED: ChallengeStatus.STARTED,
                ProviderTransportStartStatus.PENDING: ChallengeStatus.PENDING,
            }[result.status]
            return ChallengeStartResult(
                provider_source=request.provider_source,
                provider_verification_id=result.provider_verification_id,
                purpose=request.purpose,
                challenge_reference=request.challenge_reference,
                replay_reference=request.replay_reference,
                phone_binding=request.subject.phone_binding,
                status=status,
                started_at=result.started_at,
                provider_expires_at=result.provider_expires_at,
            )
        except (KeyError, TypeError, ValueError):
            self._raise(ProviderTransportFailureCode.MALFORMED_RESPONSE)
        raise AssertionError("unreachable")

    def verify_challenge(
        self, request: ChallengeVerificationRequest,
    ) -> ChallengeVerificationResult:
        if type(request) is not ChallengeVerificationRequest:
            self._raise(ProviderTransportFailureCode.REJECTED)
        self._validate_source(request.provider_source)
        transport_request = ProviderTransportVerifyRequest(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            otp=request.otp,
            timeout_seconds=self.timeout_seconds,
        )
        result = self._invoke("VERIFY", self._transport_verify, transport_request)
        if type(result) is not ProviderTransportVerifyResult:
            self._raise(ProviderTransportFailureCode.MALFORMED_RESPONSE)
        if result.provider_verification_id != request.provider_verification_id:
            self._raise(ProviderTransportFailureCode.AMBIGUOUS_PROVIDER_IDENTIFIER)
        try:
            status = {
                ProviderTransportVerificationStatus.SUCCESS: VerificationStatus.SUCCESS,
                ProviderTransportVerificationStatus.REJECTED: VerificationStatus.REJECTED,
                ProviderTransportVerificationStatus.EXPIRED: VerificationStatus.EXPIRED,
                ProviderTransportVerificationStatus.FAILED: VerificationStatus.FAILED,
            }[result.status]
        except (KeyError, TypeError, ValueError):
            self._raise(
                ProviderTransportFailureCode.UNKNOWN_OUTCOME
                if result.status is ProviderTransportVerificationStatus.UNKNOWN
                else ProviderTransportFailureCode.MALFORMED_RESPONSE,
            )
        try:
            return ChallengeVerificationResult(
                provider_source=request.provider_source,
                provider_verification_id=request.provider_verification_id,
                purpose=request.purpose,
                challenge_reference=request.challenge_reference,
                replay_reference=request.replay_reference,
                phone_binding=request.phone_binding,
                status=status,
                verified_at=result.verified_at,
                provider_expires_at=result.provider_expires_at,
            )
        except (TypeError, ValueError):
            self._raise(ProviderTransportFailureCode.MALFORMED_RESPONSE)
        raise AssertionError("unreachable")

    def _validate_source(self, source: ProviderSourceIdentifier) -> None:
        if source != self._provider_source:
            self._raise(ProviderTransportFailureCode.REJECTED)

    @staticmethod
    def _invoke(operation: str, method: Any, request: Any) -> Any:
        try:
            return method(request)
        except ProviderTransportError as error:
            raise ProviderPhoneVerificationError(error.code) from None
        except TimeoutError:
            raise ProviderPhoneVerificationError(
                ProviderTransportFailureCode.TIMEOUT,
            ) from None
        except Exception:
            raise ProviderPhoneVerificationError(
                ProviderTransportFailureCode.PROVIDER_UNAVAILABLE,
            ) from None

    @staticmethod
    def _raise(code: ProviderTransportFailureCode) -> None:
        raise ProviderPhoneVerificationError(code)


__all__ = [
    "ProviderAdapterError",
    "ProviderAdapterErrorCode",
    "ProviderAdapterFailureCode",
    "ProviderPhoneVerificationAdapter",
    "ProviderPhoneVerificationError",
]
