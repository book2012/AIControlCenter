from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shopping.ports.phone_verification import (
    ProviderSourceIdentifier, ProviderVerificationIdentifier,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation, ProviderRequestIdentity,
)
from core.shopping.ports.provider_authenticated_read import (
    NormalizedProviderEvidence, ProviderEvidenceNormalizationError, ProviderReadError,
    ProviderEvidenceReconciliationAdapter, ProviderReadRequest, ProviderReadResult,
    ProviderReadStatus,
)


NOW = datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc)


def identity() -> ProviderRequestIdentity:
    return ProviderRequestIdentity(request_id="request-1", correlation_id="correlation-1")


def test_authenticated_read_request_is_read_only_and_payload_free() -> None:
    request = ProviderReadRequest(
        provider_source="future.provider", operation=ProviderOperation.READ_HEALTH,
        identity=identity(),
    )
    assert request.operation is ProviderOperation.READ_HEALTH
    assert "secret" not in repr(request).lower()
    with pytest.raises(ValueError):
        ProviderReadRequest(
            provider_source="future.provider",
            operation=ProviderOperation.START_CHALLENGE,
            identity=identity(),
        )


def test_evidence_code_and_observed_at_are_strict_allowlisted_contracts() -> None:
    values = dict(
        provider_source="future.provider", operation=ProviderOperation.READ_EVIDENCE,
        identity=identity(), status=ProviderReadStatus.AVAILABLE, observed_at=NOW,
    )
    with pytest.raises(ValueError):
        ProviderReadResult(**dict(values, evidence_code="arbitrary-provider-text"))
    with pytest.raises(ValueError):
        ProviderReadResult(**dict(values, observed_at="2026-09-29T01:00:00+00:00"))
    with pytest.raises(ValueError):
        ProviderReadResult(**dict(values, observed_at=datetime(2026, 9, 29, 1, 0)))

    result = ProviderReadResult(**dict(values, evidence_code="VERIFICATION_FOUND"))
    assert result.to_log_dict()["evidence_code"] == "VERIFICATION_FOUND"


def test_read_result_is_normalized_and_logging_projection_is_bounded() -> None:
    result = ProviderReadResult(
        provider_source="future.provider", operation=ProviderOperation.READ_EVIDENCE,
        identity=identity(), status=ProviderReadStatus.AVAILABLE, observed_at=NOW,
        provider_verification_id=ProviderVerificationIdentifier(value="provider-id-1"),
        evidence_code="VERIFICATION_FOUND",
    )
    projection = result.to_log_dict()
    assert projection["status"] == "AVAILABLE"
    assert "raw_response" not in projection
    assert "provider_verification_id" not in projection
    assert set(projection) <= {
        "provider_source", "operation", "request_id", "correlation_id",
        "status", "observed_at", "evidence_code",
    }
    assert "otp" not in repr(result).lower()
    normalized = ProviderEvidenceReconciliationAdapter.normalize(result)
    assert isinstance(normalized, NormalizedProviderEvidence)
    assert normalized.provider_verification_id.value == "provider-id-1"


def test_normalization_rejects_unbounded_or_wrong_objects() -> None:
    with pytest.raises(ProviderEvidenceNormalizationError):
        ProviderEvidenceReconciliationAdapter.normalize({"raw": "payload"})


@pytest.mark.parametrize("invalid_id", ["provider-id-1", object()])
def test_normalized_evidence_requires_exact_provider_identifier_type(invalid_id) -> None:
    with pytest.raises((TypeError, ValueError)):
        NormalizedProviderEvidence(
            provider_source=ProviderSourceIdentifier(value="future.provider"),
            operation=ProviderOperation.READ_EVIDENCE,
            status=ProviderReadStatus.AVAILABLE,
            observed_at=NOW,
            provider_verification_id=invalid_id,
        )


def test_normalized_evidence_rejects_provider_identifier_subclasses() -> None:
    class DerivedProviderVerificationIdentifier(ProviderVerificationIdentifier):
        pass

    with pytest.raises(TypeError):
        NormalizedProviderEvidence(
            provider_source=ProviderSourceIdentifier(value="future.provider"),
            operation=ProviderOperation.READ_EVIDENCE,
            status=ProviderReadStatus.AVAILABLE,
            observed_at=NOW,
            provider_verification_id=DerivedProviderVerificationIdentifier(value="provider-id-1"),
        )


def test_errors_expose_only_bounded_reason_codes() -> None:
    assert ProviderReadError("raw provider exception").reason_code == "UNKNOWN_OUTCOME"
    assert ProviderEvidenceNormalizationError("raw provider exception").reason_code == "EVIDENCE_REJECTED"
