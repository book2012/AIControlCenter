from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shopping.ports.phone_verification_reconciliation import (
    StartReconciliationCommand, VerificationReconciliationCapability,
)
from core.shopping.ports.provider_activation import ProviderOperation
from core.shopping.ports.provider_authenticated_read import (
    ProviderEvidenceNormalizationError, ProviderEvidenceReconciliationAdapter,
    ProviderReadResult, ProviderReadStatus,
)


NOW = datetime(2026, 9, 29, 1, 0, tzinfo=timezone.utc)


class RecordingReconciliationPort:
    def __init__(self):
        self.calls = []

    def reconcile_start(self, command, *, capability):
        self.calls.append(("START", command, capability))
        return "c4-result"

    def reconcile_verify(self, command, *, capability):
        self.calls.append(("VERIFY", command, capability))
        return "c4-result"


def command(provider_verification_id="provider-id-1") -> StartReconciliationCommand:
    values = dict(
        command_id="command-1", challenge_reference="challenge-1",
        replay_reference="replay-1", expected_challenge_version=1,
        expected_quarantine_version=1, provider_source="future.provider", status="STARTED",
        started_at=NOW,
        actor_ref="actor-1", correlation_id="correlation-1",
    )
    if provider_verification_id is not None:
        values["provider_verification_id"] = provider_verification_id
    return StartReconciliationCommand(**values)


def evidence(provider_verification_id=None) -> ProviderReadResult:
    return ProviderReadResult(
        provider_source="future.provider", operation=ProviderOperation.READ_EVIDENCE,
        identity={"request_id": "request-1", "correlation_id": "correlation-1"},
        status=ProviderReadStatus.AVAILABLE, observed_at=NOW,
        provider_verification_id=provider_verification_id,
    )


def test_provider_evidence_is_normalized_before_c4_admission() -> None:
    port = RecordingReconciliationPort()
    adapter = ProviderEvidenceReconciliationAdapter(port)
    result = evidence("provider-id-1")
    normalized_evidence = adapter.normalize(result)
    assert normalized_evidence.status is ProviderReadStatus.AVAILABLE
    capability = VerificationReconciliationCapability.issue()
    assert adapter.admit(normalized_evidence, command(), capability=capability) == "c4-result"
    assert port.calls[0][0] == "START"
    assert port.calls[0][2] is capability


def test_provider_evidence_and_command_may_both_omit_provider_id() -> None:
    port = RecordingReconciliationPort()
    adapter = ProviderEvidenceReconciliationAdapter(port)
    capability = VerificationReconciliationCapability.issue()
    assert adapter.admit(
        adapter.normalize(evidence()), command(None), capability=capability,
    ) == "c4-result"
    assert len(port.calls) == 1


def test_unknown_outcome_is_rejected_before_c4_reconciliation() -> None:
    port = RecordingReconciliationPort()
    adapter = ProviderEvidenceReconciliationAdapter(port)
    unresolved = adapter.normalize(
        ProviderReadResult(
            provider_source="future.provider", operation=ProviderOperation.READ_EVIDENCE,
            identity={"request_id": "request-1", "correlation_id": "correlation-1"},
            status=ProviderReadStatus.UNKNOWN_OUTCOME, observed_at=NOW,
        ),
    )
    with pytest.raises(ProviderEvidenceNormalizationError) as error:
        adapter.admit(
            unresolved, command(None),
            capability=VerificationReconciliationCapability.issue(),
        )
    assert error.value.reason_code == "EVIDENCE_REJECTED"
    assert port.calls == []


def test_bounded_unknown_evidence_code_is_rejected_before_c4() -> None:
    port = RecordingReconciliationPort()
    adapter = ProviderEvidenceReconciliationAdapter(port)
    unresolved = adapter.normalize(
        ProviderReadResult(
            provider_source="future.provider", operation=ProviderOperation.READ_EVIDENCE,
            identity={"request_id": "request-1", "correlation_id": "correlation-1"},
            status=ProviderReadStatus.AVAILABLE, observed_at=NOW,
            evidence_code="PROVIDER_UNKNOWN_OUTCOME",
        ),
    )
    with pytest.raises(ProviderEvidenceNormalizationError):
        adapter.admit(
            unresolved, command(None),
            capability=VerificationReconciliationCapability.issue(),
        )
    assert port.calls == []


@pytest.mark.parametrize(
    ("evidence_id", "command_id"),
    ((None, "provider-id-1"), ("provider-id-1", None), ("provider-id-a", "provider-id-b")),
)
def test_provider_evidence_id_binding_is_exact_and_fail_closed(evidence_id, command_id) -> None:
    port = RecordingReconciliationPort()
    adapter = ProviderEvidenceReconciliationAdapter(port)
    capability = VerificationReconciliationCapability.issue()
    with pytest.raises(ProviderEvidenceNormalizationError) as error:
        adapter.admit(
            adapter.normalize(evidence(evidence_id)), command(command_id), capability=capability,
        )
    assert error.value.reason_code == "EVIDENCE_BINDING_REJECTED"
    assert port.calls == []


def test_adapter_has_no_sqlite_authority_and_unknown_remains_evidence() -> None:
    path = (  # keep the assertion tied to the implementation boundary
        __import__("pathlib").Path(__file__).parents[1]
        / "core/shopping/ports/provider_authenticated_read.py"
    )
    assert "sqlite3" not in path.read_text()
    assert ProviderReadStatus.UNKNOWN_OUTCOME.value == "UNKNOWN_OUTCOME"
