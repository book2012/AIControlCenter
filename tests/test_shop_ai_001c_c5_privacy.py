from __future__ import annotations

from datetime import datetime, timezone
import pytest

from core.shopping.ports.provider_activation import (
    ProviderActivationState, ProviderEvidenceLogProjection, ProviderOperation,
    ProviderRequestIdentity,
)
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult, ProviderReadStatus,
)


NOW = datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc)


def test_repr_and_logging_projection_are_secret_and_destination_free() -> None:
    raw_phone = "+821012345678"
    raw_otp = "123456"
    raw_secret = "provider-secret-value"
    result = ProviderReadResult(
        provider_source="future.provider", operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(request_id="request-1", correlation_id="correlation-1"),
        status=ProviderReadStatus.HEALTHY, observed_at=NOW,
    )
    projection = ProviderEvidenceLogProjection(
        activation_state=ProviderActivationState.AUTHENTICATED_READ_ONLY,
        operation=ProviderOperation.READ_HEALTH,
        provider_source="future.provider", request_id="request-1",
        correlation_id="correlation-1", outcome="HEALTHY", observed_at=NOW,
    ).to_dict()
    rendered = repr(result) + repr(projection)
    for forbidden in (raw_phone, raw_otp, raw_secret, "otp", "hmac", "payload"):
        assert forbidden.lower() not in rendered.lower()
    assert set(projection) <= {
        "activation_state", "operation", "provider_source", "request_id",
        "correlation_id", "outcome", "observed_at",
    }


def test_evidence_log_projection_rejects_arbitrary_outcomes_and_timestamps() -> None:
    values = dict(
        activation_state=ProviderActivationState.AUTHENTICATED_READ_ONLY,
        operation=ProviderOperation.READ_HEALTH,
        provider_source="future.provider", request_id="request-1",
        correlation_id="correlation-1", observed_at=NOW,
    )
    with pytest.raises(ValueError):
        ProviderEvidenceLogProjection(**dict(values, outcome="provider said anything"))
    with pytest.raises(ValueError):
        ProviderEvidenceLogProjection(**dict(values, outcome="HEALTHY", observed_at=object()))
    with pytest.raises(ValueError):
        ProviderEvidenceLogProjection(**dict(
            values, outcome="HEALTHY", observed_at=datetime(2026, 9, 29, 1, 0),
        ))
