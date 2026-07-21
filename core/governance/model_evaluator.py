"""Read-only model governance evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .model_registry import ApprovedModel, ModelRegistry


COMPLIANT = "COMPLIANT"
UNAPPROVED = "UNAPPROVED"
MISSING = "MISSING"
DIGEST_MISMATCH = "DIGEST_MISMATCH"
RESOURCE_POLICY_VIOLATION = "RESOURCE_POLICY_VIOLATION"


@dataclass(frozen=True)
class ObservedModel:
    runtime_name: str
    digest: str | None
    size_bytes: int | None
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class ModelEvaluation:
    model_id: str | None
    runtime_name: str
    approval_status: str
    observed: bool
    available: bool
    compliance_status: str
    reasons: tuple[str, ...]
    expected_digest: str | None
    observed_digest: str | None
    maximum_disk_bytes: int | None
    observed_size_bytes: int | None

    def to_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "model_id": self.model_id,
                "runtime_name": self.runtime_name,
                "approval_status": self.approval_status,
                "observed": self.observed,
                "available": self.available,
                "compliance_status": self.compliance_status,
                "reasons": list(self.reasons),
                "expected_digest": self.expected_digest,
                "observed_digest": self.observed_digest,
                "maximum_disk_bytes": self.maximum_disk_bytes,
                "observed_size_bytes": self.observed_size_bytes,
            }
        )


@dataclass(frozen=True)
class GovernanceEvaluation:
    mode: str
    default_policy: str
    approved_count: int
    observed_count: int
    compliant_count: int
    violation_count: int
    models: tuple[ModelEvaluation, ...]

    def to_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "service": "model-governance",
                "mode": self.mode,
                "default_policy": self.default_policy,
                "approved_count": self.approved_count,
                "observed_count": self.observed_count,
                "compliant_count": self.compliant_count,
                "violation_count": self.violation_count,
                "models": [
                    dict(model.to_dict())
                    for model in self.models
                ],
            }
        )


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _optional_non_negative_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def normalize_observed_model(
    payload: Mapping[str, Any],
) -> ObservedModel:
    runtime_name = (
        _optional_string(payload.get("name"))
        or _optional_string(payload.get("model"))
    )

    if runtime_name is None:
        raise ValueError(
            "observed model requires a non-empty name or model field"
        )

    return ObservedModel(
        runtime_name=runtime_name,
        digest=_optional_string(payload.get("digest")),
        size_bytes=_optional_non_negative_integer(
            payload.get("size")
        ),
        raw=MappingProxyType(dict(payload)),
    )


def _evaluate_approved_model(
    approved: ApprovedModel,
    observed: ObservedModel | None,
) -> ModelEvaluation:
    if observed is None:
        return ModelEvaluation(
            model_id=approved.model_id,
            runtime_name=approved.runtime_name,
            approval_status=approved.approval_status,
            observed=False,
            available=False,
            compliance_status=MISSING,
            reasons=("approved model is not present in Ollama",),
            expected_digest=approved.expected_digest,
            observed_digest=None,
            maximum_disk_bytes=(
                approved.resource_policy.maximum_disk_bytes
            ),
            observed_size_bytes=None,
        )

    reasons: list[str] = []

    if (
        approved.expected_digest is not None
        and observed.digest != approved.expected_digest
    ):
        reasons.append(
            "observed digest does not match approved digest"
        )

    if (
        observed.size_bytes is not None
        and observed.size_bytes
        > approved.resource_policy.maximum_disk_bytes
    ):
        reasons.append(
            "observed model exceeds maximum disk budget"
        )

    if reasons:
        status = DIGEST_MISMATCH
        if len(reasons) > 1 or not reasons[0].startswith(
            "observed digest"
        ):
            status = RESOURCE_POLICY_VIOLATION

        return ModelEvaluation(
            model_id=approved.model_id,
            runtime_name=approved.runtime_name,
            approval_status=approved.approval_status,
            observed=True,
            available=False,
            compliance_status=status,
            reasons=tuple(reasons),
            expected_digest=approved.expected_digest,
            observed_digest=observed.digest,
            maximum_disk_bytes=(
                approved.resource_policy.maximum_disk_bytes
            ),
            observed_size_bytes=observed.size_bytes,
        )

    return ModelEvaluation(
        model_id=approved.model_id,
        runtime_name=approved.runtime_name,
        approval_status=approved.approval_status,
        observed=True,
        available=approved.approval_status == "APPROVED",
        compliance_status=COMPLIANT,
        reasons=(),
        expected_digest=approved.expected_digest,
        observed_digest=observed.digest,
        maximum_disk_bytes=(
            approved.resource_policy.maximum_disk_bytes
        ),
        observed_size_bytes=observed.size_bytes,
    )


def evaluate_model_governance(
    registry: ModelRegistry,
    observed_models: Iterable[Mapping[str, Any]],
) -> GovernanceEvaluation:
    normalized = tuple(
        normalize_observed_model(model)
        for model in observed_models
    )

    observed_by_name: dict[str, ObservedModel] = {}

    for model in normalized:
        if model.runtime_name in observed_by_name:
            raise ValueError(
                "duplicate observed runtime name: "
                + model.runtime_name
            )
        observed_by_name[model.runtime_name] = model

    evaluations: list[ModelEvaluation] = []

    for approved in registry.models:
        observed = observed_by_name.pop(
            approved.runtime_name,
            None,
        )
        evaluations.append(
            _evaluate_approved_model(approved, observed)
        )

    for observed in observed_by_name.values():
        evaluations.append(
            ModelEvaluation(
                model_id=None,
                runtime_name=observed.runtime_name,
                approval_status="UNAPPROVED",
                observed=True,
                available=False,
                compliance_status=UNAPPROVED,
                reasons=(
                    "observed model is not registered in "
                    "AIControlCenter",
                ),
                expected_digest=None,
                observed_digest=observed.digest,
                maximum_disk_bytes=None,
                observed_size_bytes=observed.size_bytes,
            )
        )

    evaluations.sort(
        key=lambda item: (item.runtime_name, item.model_id or "")
    )

    compliant_count = sum(
        item.compliance_status == COMPLIANT
        for item in evaluations
    )

    return GovernanceEvaluation(
        mode="read-only",
        default_policy=registry.default_policy,
        approved_count=len(registry.approved_models),
        observed_count=len(normalized),
        compliant_count=compliant_count,
        violation_count=len(evaluations) - compliant_count,
        models=tuple(evaluations),
    )
