"""Governed coordinator for Production Runtime activation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from .authorization import (
    ProductionRuntimeActivationAuthorizationPermit,
    canonical_digest,
    request_digest,
    validate_activation_authorization,
)
from .claim import (
    ProductionRuntimeActivationClaimReceipt,
    ProductionRuntimeActivationClaimRegistry,
    ProductionRuntimeActivationClaimRequest,
    ProductionRuntimeActivationExecutionLaneRegistry,
)
from .models import ProductionRuntimeActivationRequest
from .plan import (
    ProductionRuntimeActivationPlan,
    validate_activation_plan_binding,
)


class ProductionRuntimeActivationArtifactVerifier(Protocol):
    """Fail-closed verifier for the exact source artifact bound by the plan."""

    def verify(
        self,
        plan: ProductionRuntimeActivationPlan,
    ) -> None: ...


class ProductionRuntimeActivationPrimitive(Protocol):
    """Structured activation port. No raw shell, argv, or environment surface."""

    def activate(
        self,
        request: ProductionRuntimeActivationRequest,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationExecutionReceipt:
    receipt_id: str
    activation_request_digest: str
    claim_receipt: ProductionRuntimeActivationClaimReceipt
    primitive_invocations: int


class ProductionRuntimeActivationCoordinator:
    """Authorize, serialize, claim once, invoke exactly once, then emit evidence."""

    def __init__(
        self,
        *,
        claim_registry: ProductionRuntimeActivationClaimRegistry,
        execution_lane: ProductionRuntimeActivationExecutionLaneRegistry,
        artifact_verifier: ProductionRuntimeActivationArtifactVerifier,
        primitive: ProductionRuntimeActivationPrimitive,
    ) -> None:
        self.claim_registry = claim_registry
        self.execution_lane = execution_lane
        self.artifact_verifier = artifact_verifier
        self.primitive = primitive

    def execute(
        self,
        *,
        request: ProductionRuntimeActivationRequest,
        plan: ProductionRuntimeActivationPlan,
        permit: ProductionRuntimeActivationAuthorizationPermit,
        validated_at: str,
        operator_identity: str,
    ) -> ProductionRuntimeActivationExecutionReceipt:
        validate_activation_plan_binding(
            request=request,
            plan=plan,
        )
        validate_activation_authorization(
            request=request,
            permit=permit,
            validated_at=validated_at,
            operator_identity=operator_identity,
        )

        activation_request_digest = request_digest(request)
        authorization_digest = canonical_digest(asdict(permit))

        with self.execution_lane.acquire():
            self.artifact_verifier.verify(plan)
            claim_receipt = self.claim_registry.claim(
                ProductionRuntimeActivationClaimRequest(
                    authorization_id=permit.authorization_id,
                    authorization_digest=authorization_digest,
                    activation_request_digest=activation_request_digest,
                    candidate_runtime_id=request.candidate_runtime_id,
                    candidate_source_commit=request.candidate_source_commit,
                    governance_commit=request.governance_commit,
                    expected_current_runtime_id=request.expected_current_runtime_id,
                    operator_identity=operator_identity,
                    claimed_at=validated_at,
                )
            )

            self.primitive.activate(request)

            receipt_digest = canonical_digest(
                {
                    "activation_request_digest": activation_request_digest,
                    "claim_digest": claim_receipt.claim_digest,
                    "primitive_invocations": 1,
                }
            )

            return ProductionRuntimeActivationExecutionReceipt(
                receipt_id="activation-01c-execution-" + receipt_digest[7:39],
                activation_request_digest=activation_request_digest,
                claim_receipt=claim_receipt,
                primitive_invocations=1,
            )
