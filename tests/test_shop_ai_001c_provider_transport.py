from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.shopping.adapters.phone_verification_transport import (
    InertProviderPhoneVerificationTransport,
)
from core.shopping.ports.phone_verification import (
    ProviderSourceIdentifier, ProviderVerificationIdentifier,
)
from core.shopping.ports.phone_verification_transport import (
    ProviderTransportError, ProviderTransportFailureCode,
    ProviderTransportStartRequest, ProviderTransportVerifyRequest,
)
from core.shopping.phone_normalization import OpaquePhoneBinding
from core.shopping.customer_auth import VerificationPurpose


SOURCE = ProviderSourceIdentifier(value="synthetic.mock")
BINDING = OpaquePhoneBinding(value="phb_" + "b" * 64)
VERIFICATION = ProviderVerificationIdentifier(value="provider-verification-1")


def test_transport_requests_are_closed_and_timeout_is_bounded() -> None:
    request = ProviderTransportStartRequest(
        provider_source=SOURCE,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        phone_binding=BINDING,
        timeout_seconds=30,
    )
    assert request.timeout_seconds == 30.0
    with pytest.raises((ValidationError, ValueError, TypeError)):
        ProviderTransportStartRequest(
            provider_source=SOURCE,
            purpose=VerificationPurpose.SESSION_ISSUANCE,
            phone_binding=BINDING,
            timeout_seconds=30.1,
        )
    with pytest.raises((ValidationError, ValueError, TypeError)):
        ProviderTransportStartRequest(
            provider_source=SOURCE,
            purpose=VerificationPurpose.SESSION_ISSUANCE,
            phone_binding=BINDING,
            timeout_seconds=0,
        )
    with pytest.raises((ValidationError, ValueError, TypeError)):
        ProviderTransportStartRequest(
            provider_source=SOURCE,
            purpose=VerificationPurpose.SESSION_ISSUANCE,
            phone_binding=BINDING,
            extra="forbidden",
        )


def test_otp_is_verify_only_and_never_exposed_by_request_rendering() -> None:
    request = ProviderTransportVerifyRequest(
        provider_source=SOURCE,
        provider_verification_id=VERIFICATION,
        otp="654321",
    )
    assert "654321" not in repr(request)
    assert "654321" not in str(request.model_dump())
    assert "654321" not in request.model_dump_json()
    with pytest.raises((ValidationError, ValueError, TypeError)):
        ProviderTransportStartRequest(
            provider_source=SOURCE,
            purpose=VerificationPurpose.SESSION_ISSUANCE,
            phone_binding=BINDING,
            otp="654321",
        )


def test_inert_transport_is_network_free_unavailable_and_non_retrying() -> None:
    transport = InertProviderPhoneVerificationTransport()
    start = ProviderTransportStartRequest(
        provider_source=SOURCE,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        phone_binding=BINDING,
    )
    verify = ProviderTransportVerifyRequest(
        provider_source=SOURCE,
        provider_verification_id=VERIFICATION,
        otp="654321",
    )
    assert transport.retry_count == 0
    assert "654321" not in repr(transport)
    with pytest.raises(ProviderTransportError) as start_error:
        transport.start(start)
    assert start_error.value.code is ProviderTransportFailureCode.PROVIDER_UNAVAILABLE
    with pytest.raises(ProviderTransportError) as verify_error:
        transport.verify(verify)
    assert verify_error.value.code is ProviderTransportFailureCode.PROVIDER_UNAVAILABLE
    assert verify_error.value.code is start_error.value.code


def test_transport_failure_repr_is_secret_safe() -> None:
    failure = ProviderTransportError(
        ProviderTransportFailureCode.TIMEOUT,
        operation="VERIFY",
    )
    assert "TIMEOUT" in repr(failure)
    assert "otp" not in repr(failure).lower()
    assert "secret" not in repr(failure).lower()
