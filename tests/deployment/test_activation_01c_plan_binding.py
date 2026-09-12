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
    ProductionRuntimeActivationError,
    ProductionRuntimeActivationRequest,
)
from core.deployment.production_runtime_activation.plan import (
    PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE,
    ProductionRuntimeActivationPlan,
)


SOURCE_DIGEST = (
    "sha256:"
    "a2b40bf8efb889e2a1e4b0185b175859716809be9bcbe45d73b4bfb991fe0792"
)


def activation_plan():
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
        primitive_identity=PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE,
    )


def activation_request():
    return ProductionRuntimeActivationRequest(
        request_id="activation-01c-plan-binding-red",
        candidate_runtime_id="28869898a28f",
        candidate_source_commit=(
            "28869898a28fbc0f0d0fd6c995104defa645ada3"
        ),
        governance_commit="a" * 40,
        expected_current_runtime_id="d8f9f550093d",
        canonical_service_label="com.aicontrolcenter.api",
        canonical_runtime_target="ops.macos.runtime.application:app",
        human_authorization_id="production-human-authorization-test",
        human_authorization_digest="sha256:" + ("1" * 64),
        # Intentionally valid syntax but NOT derived from activation_plan().
        plan_digest="sha256:" + ("2" * 64),
    )


def activation_permit(request):
    return ProductionRuntimeActivationAuthorizationPermit(
        authorization_id="activation-01c-plan-binding-authorization",
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
    def __init__(self):
        self.calls = []

    def activate(self, request):
        self.calls.append(request)


def test_coordinator_rejects_request_not_bound_to_actual_plan_before_mutation(
    tmp_path,
):
    plan = activation_plan()
    request = activation_request()
    permit = activation_permit(request)

    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    lane_root = tmp_path / "activation-lane"
    lane_root.mkdir(mode=0o700)

    primitive = RecordingPrimitive()
    verifier = AcceptingArtifactVerifier()

    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=ProductionRuntimeActivationExecutionLaneRegistry(
            lane_root
        ),
        artifact_verifier=verifier,
        primitive=primitive,
    )

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_PLAN_BINDING_MISMATCH",
    ):
        coordinator.execute(
            request=request,
            plan=plan,
            permit=permit,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    assert list(claim_root.iterdir()) == []
    assert list(lane_root.iterdir()) == []
    assert verifier.calls == []
    assert primitive.calls == []
