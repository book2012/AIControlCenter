from dataclasses import FrozenInstanceError, replace

import pytest

from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationError,
    ProductionRuntimeActivationRequest,
)


CANDIDATE_RUNTIME = "28869898a28f"
CANDIDATE_SOURCE = "28869898a28fbc0f0d0fd6c995104defa645ada3"
EXPECTED_CURRENT = "d8f9f550093d"
GOVERNANCE_COMMIT = "a" * 40
AUTHORIZATION_DIGEST = "sha256:" + ("1" * 64)
PLAN_DIGEST = "sha256:" + ("2" * 64)


def activation_request() -> ProductionRuntimeActivationRequest:
    return ProductionRuntimeActivationRequest(
        request_id="activation-01c-test-request",
        candidate_runtime_id=CANDIDATE_RUNTIME,
        candidate_source_commit=CANDIDATE_SOURCE,
        governance_commit=GOVERNANCE_COMMIT,
        expected_current_runtime_id=EXPECTED_CURRENT,
        canonical_service_label="com.aicontrolcenter.api",
        canonical_runtime_target="ops.macos.runtime.application:app",
        human_authorization_id="production-human-authorization-test",
        human_authorization_digest=AUTHORIZATION_DIGEST,
        plan_digest=PLAN_DIGEST,
    )


def test_production_runtime_activation_request_is_immutable_and_exactly_bound() -> None:
    request = activation_request()

    assert request.candidate_runtime_id == CANDIDATE_SOURCE[:12]
    assert request.expected_current_runtime_id == EXPECTED_CURRENT
    assert request.canonical_service_label == "com.aicontrolcenter.api"
    assert request.canonical_runtime_target == "ops.macos.runtime.application:app"

    with pytest.raises(FrozenInstanceError):
        request.candidate_runtime_id = "b" * 12


def test_candidate_runtime_must_match_source_commit_identity() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="CANDIDATE_SOURCE_BINDING_INVALID",
    ):
        replace(activation_request(), candidate_runtime_id="b" * 12)


def test_canonical_serving_target_is_fail_closed() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="CANONICAL_TARGET_BINDING_INVALID",
    ):
        replace(
            activation_request(),
            canonical_runtime_target="core.api.app:app",
        )

from core.deployment.production_runtime_activation.authorization import (
    ProductionRuntimeActivationAuthorizationPermit,
    request_digest,
    validate_activation_authorization,
)


def activation_permit() -> ProductionRuntimeActivationAuthorizationPermit:
    request = activation_request()
    return ProductionRuntimeActivationAuthorizationPermit(
        authorization_id="activation-01c-human-authorization",
        activation_request_digest=request_digest(request),
        candidate_runtime_id=request.candidate_runtime_id,
        candidate_source_commit=request.candidate_source_commit,
        governance_commit=request.governance_commit,
        expected_current_runtime_id=request.expected_current_runtime_id,
        plan_digest=request.plan_digest,
        operator_identity="mac-operator-01",
        independent_approver_identity="production-approver-01",
        authorized_at="2026-09-11T10:00:00+09:00",
        not_before="2026-09-11T10:00:00+09:00",
        expires_at="2026-09-11T10:10:00+09:00",
    )


def test_production_authorization_is_exactly_bound_and_valid() -> None:
    validate_activation_authorization(
        request=activation_request(),
        permit=activation_permit(),
        validated_at="2026-09-11T10:05:00+09:00",
        operator_identity="mac-operator-01",
    )


def test_production_authorization_requires_independent_approver() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="INDEPENDENT_APPROVER_REQUIRED",
    ):
        replace(
            activation_permit(),
            independent_approver_identity="mac-operator-01",
        )


def test_production_authorization_rejects_request_binding_mismatch() -> None:
    changed = replace(
        activation_request(),
        expected_current_runtime_id="b" * 12,
    )
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_AUTHORIZATION_BINDING_MISMATCH",
    ):
        validate_activation_authorization(
            request=changed,
            permit=activation_permit(),
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )


def test_production_authorization_expires_fail_closed() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_AUTHORIZATION_EXPIRED",
    ):
        validate_activation_authorization(
            request=activation_request(),
            permit=activation_permit(),
            validated_at="2026-09-11T10:10:00+09:00",
            operator_identity="mac-operator-01",
        )

from core.deployment.production_runtime_activation.authorization import (
    ProductionRuntimeActivationAuthorizationPermit,
    request_digest,
    validate_activation_authorization,
)


def activation_permit() -> ProductionRuntimeActivationAuthorizationPermit:
    request = activation_request()
    return ProductionRuntimeActivationAuthorizationPermit(
        authorization_id="activation-01c-human-authorization",
        activation_request_digest=request_digest(request),
        candidate_runtime_id=request.candidate_runtime_id,
        candidate_source_commit=request.candidate_source_commit,
        governance_commit=request.governance_commit,
        expected_current_runtime_id=request.expected_current_runtime_id,
        plan_digest=request.plan_digest,
        operator_identity="mac-operator-01",
        independent_approver_identity="production-approver-01",
        authorized_at="2026-09-11T10:00:00+09:00",
        not_before="2026-09-11T10:00:00+09:00",
        expires_at="2026-09-11T10:10:00+09:00",
    )


def test_production_authorization_is_exactly_bound_and_valid() -> None:
    validate_activation_authorization(
        request=activation_request(),
        permit=activation_permit(),
        validated_at="2026-09-11T10:05:00+09:00",
        operator_identity="mac-operator-01",
    )


def test_production_authorization_requires_independent_approver() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="INDEPENDENT_APPROVER_REQUIRED",
    ):
        replace(
            activation_permit(),
            independent_approver_identity="mac-operator-01",
        )


def test_production_authorization_rejects_request_binding_mismatch() -> None:
    changed = replace(
        activation_request(),
        expected_current_runtime_id="b" * 12,
    )
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_AUTHORIZATION_BINDING_MISMATCH",
    ):
        validate_activation_authorization(
            request=changed,
            permit=activation_permit(),
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )


def test_production_authorization_expires_fail_closed() -> None:
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_AUTHORIZATION_EXPIRED",
    ):
        validate_activation_authorization(
            request=activation_request(),
            permit=activation_permit(),
            validated_at="2026-09-11T10:10:00+09:00",
            operator_identity="mac-operator-01",
        )

import stat

from core.deployment.production_runtime_activation.claim import (
    ProductionRuntimeActivationClaimRegistry,
    ProductionRuntimeActivationClaimRequest,
)


def claim_request() -> ProductionRuntimeActivationClaimRequest:
    permit = activation_permit()
    return ProductionRuntimeActivationClaimRequest(
        authorization_id=permit.authorization_id,
        authorization_digest=request_digest(permit),
        activation_request_digest=permit.activation_request_digest,
        candidate_runtime_id=permit.candidate_runtime_id,
        candidate_source_commit=permit.candidate_source_commit,
        governance_commit=permit.governance_commit,
        expected_current_runtime_id=permit.expected_current_runtime_id,
        operator_identity=permit.operator_identity,
        claimed_at="2026-09-11T10:05:00+09:00",
    )


def test_production_activation_claim_is_durable_single_use(tmp_path) -> None:
    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    registry = ProductionRuntimeActivationClaimRegistry(claim_root)
    receipt = registry.claim(claim_request())

    assert receipt.claim_path.exists()
    assert stat.S_IMODE(receipt.claim_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(claim_root.stat().st_mode) == 0o700

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_ALREADY_CLAIMED",
    ):
        registry.claim(claim_request())

    assert receipt.claim_path.exists()


def test_production_activation_claim_rejects_insecure_root(tmp_path) -> None:
    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)
    claim_root.chmod(0o755)

    registry = ProductionRuntimeActivationClaimRegistry(claim_root)

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_CLAIM_ROOT_MODE_INVALID",
    ):
        registry.claim(claim_request())

    assert not tuple(claim_root.iterdir())
