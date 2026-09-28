"""C4 reconciliation capability and authority-boundary tests."""
from datetime import datetime, timezone

import pytest

from core.shopping import customer_persistence as persistence
from core.shopping.ports.phone_verification_reconciliation import (
    StartReconciliationCommand, VerificationReconciliationCapability,
    VerifyReconciliationCommand,
)
from core.shopping.verification_reconciliation_service import (
    ReconciliationAuthorizationError, VerificationReconciliationService,
)


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def test_capability_is_opaque_and_not_directly_constructible():
    with pytest.raises(TypeError):
        VerificationReconciliationCapability()
    with pytest.raises(TypeError):
        VerificationReconciliationCapability("shopping-verification-reconciliation/v1")
    capability = VerificationReconciliationCapability.issue()
    assert type(capability) is VerificationReconciliationCapability


def test_reconciliation_service_requires_the_dedicated_capability(tmp_path):
    path = tmp_path / "authority.sqlite3"
    persistence.initialize_schema(path)
    with pytest.raises(ReconciliationAuthorizationError):
        VerificationReconciliationService(database_path=path, utc_clock=lambda: NOW)
    with pytest.raises(ReconciliationAuthorizationError):
        VerificationReconciliationService(
            database_path=path, utc_clock=lambda: NOW, capability=object(),
        )


def test_wrong_invocation_capability_is_denied_even_for_a_valid_service(tmp_path):
    path = tmp_path / "wrong-capability.sqlite3"
    persistence.initialize_schema(path)
    capability = VerificationReconciliationCapability.issue()
    service = VerificationReconciliationService(
        database_path=path, utc_clock=lambda: NOW, capability=capability,
    )
    command = StartReconciliationCommand(
        command_id="command-1", challenge_reference="challenge-1",
        replay_reference="replay-1", expected_challenge_version=1,
        expected_quarantine_version=1, provider_source="synthetic.mock",
        status="FAILED", actor_ref="operator", correlation_id="correlation",
    )
    with pytest.raises(ReconciliationAuthorizationError):
        service.reconcile_start(command, capability=object())
    with pytest.raises(ReconciliationAuthorizationError):
        service.reconcile_start(command)
    with pytest.raises(ReconciliationAuthorizationError):
        service.reconcile_start(command, capability=None)
    with pytest.raises(ReconciliationAuthorizationError):
        service.reconcile_start(
            command, capability=VerificationReconciliationCapability.issue(),
        )
    verify_command = VerifyReconciliationCommand(
        command_id="verify-1", challenge_reference="challenge-1",
        replay_reference="replay-1", expected_challenge_version=1,
        expected_quarantine_version=1, provider_source="synthetic.mock",
        provider_verification_id="provider-1", status="UNKNOWN",
        actor_ref="operator", correlation_id="correlation",
    )
    with pytest.raises(ReconciliationAuthorizationError):
        service.reconcile_verify(verify_command)
