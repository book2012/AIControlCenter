import copy
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

from core.governance.control_plane.application.api_projection import (
    GovernanceApiReference,
    GovernanceReadModel,
    project_governance_api_envelope,
)
from core.governance.control_plane.domain import (
    AuthorizationState,
    ExecutionStatus,
    MutationBudgetStatus,
    PostconditionDecision,
    PreconditionComparisonStatus,
)


def reference(contract_name: str, suffix: str) -> GovernanceApiReference:
    return GovernanceApiReference(contract_name, f"resource-{suffix}", f"sha256:{suffix}")


def read_model() -> GovernanceReadModel:
    return GovernanceReadModel(
        lifecycle_id="lifecycle-a9",
        authorization_state=AuthorizationState.CONSUMED,
        precondition_status=PreconditionComparisonStatus.MATCH,
        mutation_budget_status=MutationBudgetStatus.CONSUMED,
        allowed_invocation_count=3,
        actual_invocation_count=2,
        completed_count=1,
        uncertain_count=1,
        execution_status=ExecutionStatus.UNCERTAIN,
        postcondition_decision=PostconditionDecision.FAIL,
        failure_present=True,
        manual_action_required=True,
        data_reference=reference("GovernanceApiEnvelope", "projection"),
        evidence_manifest_reference=reference("GovernanceEvidenceManifest", "manifest"),
        evidence_bundle_reference=reference("GovernanceEvidenceBundle", "bundle"),
        git_documentation_gate_status="PENDING",
        git_documentation_gate_reference=reference(
            "GovernanceGitDocumentationGateReport", "git-gate"
        ),
        projected_at=datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
    )


def test_read_model_is_immutable() -> None:
    model = read_model()
    with pytest.raises(FrozenInstanceError):
        model.lifecycle_id = "changed"  # type: ignore[misc]


def test_read_model_preserves_typed_governance_state() -> None:
    projected = read_model().to_dict()
    assert projected["authorization_state"] == "CONSUMED"
    assert projected["precondition_status"] == "MATCH"
    assert projected["mutation_budget_status"] == "CONSUMED"
    assert projected["allowed_invocation_count"] == 3
    assert projected["actual_invocation_count"] == 2
    assert projected["completed_count"] == 1
    assert projected["uncertain_count"] == 1
    assert projected["execution_status"] == "UNCERTAIN"
    assert projected["postcondition_decision"] == "FAIL"
    assert projected["failure_present"] is True
    assert projected["manual_action_required"] is True
    assert projected["git_documentation_gate_status"] == "PENDING"


def test_projection_is_deterministic_json_safe_and_preserves_references() -> None:
    model = read_model()
    first = project_governance_api_envelope(model)
    second = project_governance_api_envelope(model)
    assert first == second
    assert json.loads(json.dumps(first)) == first
    assert first["generated_at"] == "2026-08-10T15:00:00+00:00"
    assert first["data_reference"] == model.data_reference.to_dict()
    assert {item["contract_name"] for item in first["evidence_references"]} == {
        "GovernanceEvidenceManifest",
        "GovernanceEvidenceBundle",
        "GovernanceGitDocumentationGateReport",
    }


def test_projection_validates_against_existing_envelope_schema() -> None:
    schema_path = Path(
        "core/governance/control_plane/contracts/schemas/v1/governance-api-envelope.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(
        project_governance_api_envelope(read_model())
    )


def test_projection_uses_no_internal_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    model = read_model()

    class ForbiddenDateTime:
        @classmethod
        def now(cls, *args: object, **kwargs: object) -> None:
            raise AssertionError("internal clock access is forbidden")

    monkeypatch.setattr(
        "core.governance.control_plane.application.api_projection.datetime", ForbiddenDateTime
    )
    assert project_governance_api_envelope(model)["generated_at"] == (
        "2026-08-10T15:00:00+00:00"
    )


def test_projection_does_not_mutate_input() -> None:
    model = read_model()
    before = copy.deepcopy(model)
    project_governance_api_envelope(model)
    assert model == before
