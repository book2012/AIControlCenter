"""Default-safe, network-free phone-verification transport."""
from __future__ import annotations

from core.shopping.ports.phone_verification_transport import (
    ProviderTransportError, ProviderTransportFailureCode,
    ProviderTransportStartRequest, ProviderTransportStartResult,
    ProviderTransportVerifyRequest, ProviderTransportVerifyResult,
)


class InertProviderPhoneVerificationTransport:
    """An unavailable transport with no credential or network capability."""

    retry_count = 0

    def __repr__(self) -> str:
        return "InertProviderPhoneVerificationTransport(status='unavailable')"

    def start(
        self, request: ProviderTransportStartRequest,
    ) -> ProviderTransportStartResult:
        _ = request
        raise ProviderTransportError(
            ProviderTransportFailureCode.PROVIDER_UNAVAILABLE,
            operation="START",
        )

    def verify(
        self, request: ProviderTransportVerifyRequest,
    ) -> ProviderTransportVerifyResult:
        _ = request
        raise ProviderTransportError(
            ProviderTransportFailureCode.PROVIDER_UNAVAILABLE,
            operation="VERIFY",
        )

    # Explicit operation aliases keep the inert implementation convenient for
    # callers that use the application vocabulary at this boundary.
    start_challenge = start
    verify_challenge = verify


UnavailableProviderPhoneVerificationTransport = InertProviderPhoneVerificationTransport
InertPhoneVerificationTransport = InertProviderPhoneVerificationTransport
FakeProviderPhoneVerificationTransport = InertProviderPhoneVerificationTransport


__all__ = [
    "InertPhoneVerificationTransport",
    "InertProviderPhoneVerificationTransport",
    "FakeProviderPhoneVerificationTransport",
    "UnavailableProviderPhoneVerificationTransport",
]
