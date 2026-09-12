from pathlib import Path

import pytest

from core.deployment.production_runtime_activation.authorization import (
    ProductionRuntimeActivationAuthorizationPermit,
    request_digest,
)
from core.deployment.production_runtime_activation.claim import (
    ProductionRuntimeActivationClaimRegistry,
    ProductionRuntimeActivationExecutionLaneRegistry,
)
from core.deployment.production_runtime_activation.coordinator import (
    ProductionRuntimeActivationCoordinator,
)
from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationRequest,
)
from core.deployment.production_runtime_activation.plan import (
    ProductionRuntimeActivationPlan,
    activation_plan_digest,
)


def execution_lane(
    tmp_path: Path,
) -> ProductionRuntimeActivationExecutionLaneRegistry:
    root = tmp_path / "coordinator-activation-lane"
    root.mkdir(mode=0o700)
    return ProductionRuntimeActivationExecutionLaneRegistry(root)


SOURCE_DIGEST = (
    "sha256:"
    "a2b40bf8efb889e2a1e4b0185b175859716809be9bcbe45d73b4bfb991fe0792"
)

def activation_plan() -> ProductionRuntimeActivationPlan:
    return ProductionRuntimeActivationPlan(
        candidate_runtime_id="28869898a28f",
        candidate_source_commit=(
            "28869898a28fbc0f0d0fd6c995104defa645ada3"
        ),
        source_artifact_content_digest=SOURCE_DIGEST,
        governance_commit="a" * 40,
        expected_current_runtime_id="d8f9f550093d",
        canonical_service_label="com.aicontrolcenter.api",
        canonical_runtime_target="ops.macos.runtime.application:app",
    )

def activation_request() -> ProductionRuntimeActivationRequest:
    return ProductionRuntimeActivationRequest(
        request_id="activation-01c-coordinator-test",
        candidate_runtime_id="28869898a28f",
        candidate_source_commit="28869898a28fbc0f0d0fd6c995104defa645ada3",
        governance_commit="a" * 40,
        expected_current_runtime_id="d8f9f550093d",
        canonical_service_label="com.aicontrolcenter.api",
        canonical_runtime_target="ops.macos.runtime.application:app",
        human_authorization_id="production-human-authorization-test",
        human_authorization_digest="sha256:" + ("1" * 64),
        plan_digest=activation_plan_digest(activation_plan()),
    )


def activation_permit(
    request: ProductionRuntimeActivationRequest,
) -> ProductionRuntimeActivationAuthorizationPermit:
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




class AcceptingArtifactVerifier:
    def __init__(self) -> None:
        self.calls = []

    def verify(self, plan) -> None:
        self.calls.append(plan)


class RecordingPrimitive:
    def __init__(self) -> None:
        self.calls = []

    def activate(self, request: ProductionRuntimeActivationRequest) -> None:
        self.calls.append(request)


def test_coordinator_claims_before_exactly_one_primitive_invocation(
    tmp_path: Path,
) -> None:
    request = activation_request()
    permit = activation_permit(request)

    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    primitive = RecordingPrimitive()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=execution_lane(tmp_path),
        artifact_verifier=AcceptingArtifactVerifier(),
        primitive=primitive,
    )

    receipt = coordinator.execute(
        request=request,
        plan=activation_plan(),
        permit=permit,
        validated_at="2026-09-11T10:05:00+09:00",
        operator_identity="mac-operator-01",
    )

    assert len(primitive.calls) == 1
    assert primitive.calls[0] == request
    assert receipt.claim_receipt.claim_path.exists()

import pytest

from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationError,
)


def test_coordinator_rejects_missing_authorization_before_claim_and_primitive(
    tmp_path,
) -> None:
    request = activation_request()
    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    primitive = RecordingPrimitive()
    verifier = AcceptingArtifactVerifier()
    lane = execution_lane(tmp_path)
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=lane,
        artifact_verifier=verifier,
        primitive=primitive,
    )

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="PRODUCTION_RUNTIME_ACTIVATION_AUTHORIZATION_REQUIRED",
    ):
        coordinator.execute(
            request=request,
            plan=activation_plan(),
            permit=None,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    assert primitive.calls == []
    assert list(claim_root.iterdir()) == []
    assert list(lane.root.iterdir()) == []
    assert verifier.calls == []


def test_coordinator_duplicate_claim_prevents_second_primitive_invocation(
    tmp_path,
) -> None:
    request = activation_request()
    permit = activation_permit(request)
    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    primitive = RecordingPrimitive()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=execution_lane(tmp_path),
        artifact_verifier=AcceptingArtifactVerifier(),
        primitive=primitive,
    )

    coordinator.execute(
        request=request,
        plan=activation_plan(),
        permit=permit,
        validated_at="2026-09-11T10:05:00+09:00",
        operator_identity="mac-operator-01",
    )

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_ALREADY_CLAIMED",
    ):
        coordinator.execute(
            request=request,
            plan=activation_plan(),
            permit=permit,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    assert len(primitive.calls) == 1


class FailingPrimitive:
    def __init__(self) -> None:
        self.calls = []

    def activate(self, request: ProductionRuntimeActivationRequest) -> None:
        self.calls.append(request)
        raise RuntimeError("synthetic primitive failure")


def test_coordinator_preserves_claim_after_primitive_failure_and_never_retries(
    tmp_path,
) -> None:
    request = activation_request()
    permit = activation_permit(request)
    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    primitive = FailingPrimitive()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=execution_lane(tmp_path),
        artifact_verifier=AcceptingArtifactVerifier(),
        primitive=primitive,
    )

    with pytest.raises(RuntimeError, match="synthetic primitive failure"):
        coordinator.execute(
            request=request,
            plan=activation_plan(),
            permit=permit,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    claims = list(claim_root.glob("*.claim.json"))
    assert len(claims) == 1
    assert claims[0].exists()
    assert len(primitive.calls) == 1

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_ALREADY_CLAIMED",
    ):
        coordinator.execute(
            request=request,
            plan=activation_plan(),
            permit=permit,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    assert len(primitive.calls) == 1

def test_coordinator_requires_execution_lane_before_verification_claim_and_primitive(
    tmp_path,
) -> None:
    request = activation_request()
    permit = activation_permit(request)

    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    lane_root = tmp_path / "activation-lane"
    lane_root.mkdir(mode=0o700)

    lane = ProductionRuntimeActivationExecutionLaneRegistry(lane_root)
    primitive = RecordingPrimitive()
    verifier = AcceptingArtifactVerifier()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=lane,
        artifact_verifier=verifier,
        primitive=primitive,
    )

    with lane.acquire():
        with pytest.raises(
            ProductionRuntimeActivationError,
            match="ACTIVATION_EXECUTION_LANE_BUSY",
        ):
            coordinator.execute(
                request=request,
                plan=activation_plan(),
                permit=permit,
                validated_at="2026-09-11T10:05:00+09:00",
                operator_identity="mac-operator-01",
            )

    assert verifier.calls == []
    assert list(claim_root.iterdir()) == []
    assert primitive.calls == []
