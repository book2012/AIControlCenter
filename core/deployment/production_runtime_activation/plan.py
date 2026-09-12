"""Immutable execution plan for governed Production Runtime activation."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .authorization import canonical_digest
from .models import (
    ProductionRuntimeActivationError,
    ProductionRuntimeActivationRequest,
)

PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE = (
    "BOOTSTRAP_PRODUCTION_RUNTIME_ACTIVATE_V1"
)


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationPlan:
    candidate_runtime_id: str
    candidate_source_commit: str
    source_artifact_content_digest: str
    governance_commit: str
    expected_current_runtime_id: str
    canonical_service_label: str
    canonical_runtime_target: str
    primitive_identity: str = PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE

    def __post_init__(self) -> None:
        probe = ProductionRuntimeActivationRequest(
            request_id="activation-plan-validation",
            candidate_runtime_id=self.candidate_runtime_id,
            candidate_source_commit=self.candidate_source_commit,
            governance_commit=self.governance_commit,
            expected_current_runtime_id=self.expected_current_runtime_id,
            canonical_service_label=self.canonical_service_label,
            canonical_runtime_target=self.canonical_runtime_target,
            human_authorization_id="activation-plan-validation",
            human_authorization_digest="sha256:" + ("0" * 64),
            plan_digest="sha256:" + ("0" * 64),
        )
        del probe

        digest = self.source_artifact_content_digest
        if (
            not isinstance(digest, str)
            or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(ch not in "0123456789abcdef" for ch in digest[7:])
        ):
            raise ProductionRuntimeActivationError(
                "SOURCE_ARTIFACT_CONTENT_DIGEST_INVALID"
            )

        if self.primitive_identity != PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_PRIMITIVE_IDENTITY_INVALID"
            )


def activation_plan_digest(plan: ProductionRuntimeActivationPlan) -> str:
    return canonical_digest(asdict(plan))


def validate_activation_plan_binding(
    *,
    request: ProductionRuntimeActivationRequest,
    plan: ProductionRuntimeActivationPlan,
) -> None:
    """Bind the execution request to the exact immutable activation plan."""
    if not isinstance(plan, ProductionRuntimeActivationPlan):
        raise ProductionRuntimeActivationError(
            "PRODUCTION_RUNTIME_ACTIVATION_PLAN_REQUIRED"
        )

    if activation_plan_digest(plan) != request.plan_digest:
        raise ProductionRuntimeActivationError(
            "ACTIVATION_PLAN_BINDING_MISMATCH"
        )

    bindings = (
        (plan.candidate_runtime_id, request.candidate_runtime_id),
        (plan.candidate_source_commit, request.candidate_source_commit),
        (plan.governance_commit, request.governance_commit),
        (
            plan.expected_current_runtime_id,
            request.expected_current_runtime_id,
        ),
        (
            plan.canonical_service_label,
            request.canonical_service_label,
        ),
        (
            plan.canonical_runtime_target,
            request.canonical_runtime_target,
        ),
    )

    if any(actual != expected for actual, expected in bindings):
        raise ProductionRuntimeActivationError(
            "ACTIVATION_PLAN_BINDING_MISMATCH"
        )
