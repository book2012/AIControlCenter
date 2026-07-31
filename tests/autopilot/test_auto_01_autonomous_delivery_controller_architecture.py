from __future__ import annotations

from dataclasses import replace
import ast
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from core.autopilot.lifecycle import validate_transition
from core.autopilot.manifest import build_manifest, validate_manifest
from core.autopilot.models import (
    ApprovalGatePolicy,
    ApprovalRequirement,
    ApprovalState,
    AutonomyLevel,
    AutopilotPolicyError,
    DocumentationGatePolicy,
    DeliveryRunState,
    DeliveryTransition,
    EvidencePolicy,
    GitGatePolicy,
    RetryClassification,
    RetryPolicy,
    SprintBaseline,
    SprintDependency,
    SprintManifest,
    SprintScopePolicy,
    SprintTaskId,
    TestGatePolicy as GateTestPolicy,
)
from core.autopilot.planning import compile_roadmap
from core.autopilot.policy import AutonomousDeliveryPolicy
from core.autopilot.retry import classify_retry

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "873ad5cc8fcbf2cb48bd3205ce1ee6451c5338ec"


def manifest(
    task_id: str = "AUTO-01",
    level: AutonomyLevel = AutonomyLevel.L0_OBSERVE,
    dependencies: tuple[str, ...] = (),
) -> SprintManifest:
    approval = ApprovalGatePolicy()
    if level is AutonomyLevel.L4_CONTROLLED_OPERATIONAL_WRITE:
        approval = ApprovalGatePolicy(
            ApprovalRequirement.OPERATIONAL_WRITE, ApprovalState.REQUIRED, True
        )
    if level is AutonomyLevel.L5_PRODUCTION_ACTIVATION:
        approval = ApprovalGatePolicy(
            ApprovalRequirement.PRODUCTION, ApprovalState.REQUIRED, True
        )
    return SprintManifest(
        schema_version="1.0",
        task_id=SprintTaskId(task_id),
        title=task_id,
        milestone="AUTO",
        baseline=SprintBaseline("feature/deployment-package", BASELINE),
        dependencies=tuple(SprintDependency(SprintTaskId(item)) for item in dependencies),
        autonomy_level=level,
        maximum_autonomy_level=level,
        test_only=level is AutonomyLevel.L2_TEST_ONLY_IMPLEMENT,
        operational_write_allowed=False,
        production=level is AutonomyLevel.L5_PRODUCTION_ACTIVATION,
        ubuntu_participation="NONE",
        scope=SprintScopePolicy(
            ("core/autopilot/**",),
            (".env", "core/worker/**"),
            ("autopilot", "deployment_contracts"),
            ("workers", "api_write", "production"),
        ),
        git_gates=GitGatePolicy(),
        test_gates=GateTestPolicy((".venv/bin/python -m pytest tests/autopilot",)),
        documentation_gates=DocumentationGatePolicy(("README.md",)),
        approval=approval,
        retry=RetryPolicy(),
        evidence=EvidencePolicy(("git_status", "test_report", "remote_commit")),
        commit_policy="one validated task commit",
        next_task_policy="explicit roadmap scheduling only",
        forbidden_operations=(
            "subprocess", "network", "shell", "runtime activation", "automatic post-claim retry"
        ),
    )


@pytest.mark.parametrize("level", list(AutonomyLevel)[:4])
def test_valid_lower_level_manifests(level: AutonomyLevel) -> None:
    assert validate_manifest(build_manifest(manifest(level=level))).valid


def test_default_is_least_privilege() -> None:
    assert manifest().autonomy_level is AutonomyLevel.L0_OBSERVE


def test_l4_requires_human_approval() -> None:
    value = replace(manifest(level=AutonomyLevel.L4_CONTROLLED_OPERATIONAL_WRITE), approval=ApprovalGatePolicy())
    assert "L4_REQUIRES_HUMAN_APPROVAL" in validate_manifest(value).errors


def test_l5_requires_production_approval() -> None:
    value = replace(manifest(level=AutonomyLevel.L5_PRODUCTION_ACTIVATION), approval=ApprovalGatePolicy())
    assert "L5_REQUIRES_PRODUCTION_APPROVAL" in validate_manifest(value).errors


def test_no_autonomy_self_escalation_and_production_below_l5() -> None:
    value = replace(
        manifest(level=AutonomyLevel.L3_GIT_CLOSEOUT),
        maximum_autonomy_level=AutonomyLevel.L1_PLAN,
        production=True,
    )
    assert {"AUTONOMY_SELF_ESCALATION", "PRODUCTION_PROHIBITED_BELOW_L5"} <= set(validate_manifest(value).errors)


def test_manifest_json_digest_and_round_trip_are_deterministic() -> None:
    first = build_manifest(manifest())
    second = build_manifest(manifest())
    assert first.canonical_json() == second.canonical_json()
    assert first.canonical_manifest_digest == second.canonical_manifest_digest
    assert json.loads(first.canonical_json())["task_id"] == "AUTO-01"


def test_deterministic_dag_ordering() -> None:
    values = (
        build_manifest(manifest("C", dependencies=("A",))),
        build_manifest(manifest("B")),
        build_manifest(manifest("A")),
    )
    first = compile_roadmap(values)
    second = compile_roadmap(tuple(reversed(values)))
    assert [step.task_id for step in first.steps] == ["A", "B", "C"]
    assert first.canonical_json() == second.canonical_json()


def test_duplicate_cycle_and_missing_dependency_are_rejected() -> None:
    one = build_manifest(manifest("A"))
    with pytest.raises(AutopilotPolicyError, match="DUPLICATE"):
        compile_roadmap((one, one))
    with pytest.raises(AutopilotPolicyError, match="UNKNOWN"):
        compile_roadmap((build_manifest(manifest("A", dependencies=("X",))),))
    cycle = (
        build_manifest(manifest("A", dependencies=("B",))),
        build_manifest(manifest("B", dependencies=("A",))),
    )
    with pytest.raises(AutopilotPolicyError, match="CYCLE"):
        compile_roadmap(cycle)


def test_incomplete_dependency_blocks_scheduling() -> None:
    plan = compile_roadmap(
        (
            build_manifest(manifest("AUTO-01")),
            build_manifest(manifest("AUTO-02", dependencies=("AUTO-01",))),
        ),
        completed_task_ids=frozenset(),
    )
    assert plan.steps[1].blocked and plan.steps[1].blockers == ("AUTO-01",)


def test_readiness_and_approval_do_not_imply_authorization_or_activation() -> None:
    plan = compile_roadmap((build_manifest(manifest()),))
    assert plan.operational_actions_authorized == 0
    assert plan.production_authorized is False
    assert all(not item.approval_is_authorization and not item.activation_authorized for item in plan.steps)


def transition(source: DeliveryRunState, target: DeliveryRunState, **values: bool) -> DeliveryTransition:
    return DeliveryTransition(source, target, ("immutable-evidence",), **values)


def test_no_skipped_lifecycle_state() -> None:
    assert not validate_transition(transition(DeliveryRunState.PLANNED, DeliveryRunState.RUNNING)).allowed


def test_running_requires_exact_baseline() -> None:
    assert not validate_transition(transition(DeliveryRunState.PREFLIGHT, DeliveryRunState.RUNNING)).allowed
    assert validate_transition(transition(DeliveryRunState.PREFLIGHT, DeliveryRunState.RUNNING, exact_baseline_verified=True)).allowed


def test_commit_requires_tests_and_documentation() -> None:
    assert not validate_transition(transition(DeliveryRunState.DOCUMENTING, DeliveryRunState.COMMITTING, tests_passed=True)).allowed
    assert validate_transition(transition(DeliveryRunState.DOCUMENTING, DeliveryRunState.COMMITTING, tests_passed=True, documentation_passed=True)).allowed


def test_push_requires_commit_and_close_requires_remote_verification() -> None:
    assert not validate_transition(transition(DeliveryRunState.COMMITTING, DeliveryRunState.PUSHING)).allowed
    assert validate_transition(transition(DeliveryRunState.COMMITTING, DeliveryRunState.PUSHING, commit_evidence_present=True)).allowed
    assert not validate_transition(transition(DeliveryRunState.PUSHING, DeliveryRunState.CLOSED)).allowed
    assert validate_transition(transition(DeliveryRunState.PUSHING, DeliveryRunState.CLOSED, remote_commit_verified=True)).allowed


def test_no_automatic_transition_through_approval() -> None:
    value = transition(DeliveryRunState.PREFLIGHT, DeliveryRunState.AWAITING_APPROVAL)
    assert not validate_transition(value).allowed


def test_retry_classification_is_default_deny() -> None:
    assert classify_retry(repository_edited=False, authorization_created=False, permit_issued=False, claim_created=False, operational_write=False) is RetryClassification.SAFE_PREFLIGHT_RETRY
    assert classify_retry(repository_edited=True, authorization_created=False, permit_issued=False, claim_created=False, operational_write=False) is RetryClassification.SAFE_PRE_CLAIM_RECOVERY
    assert classify_retry(repository_edited=False, authorization_created=True, permit_issued=True, claim_created=True, operational_write=False) is RetryClassification.MANUAL_POST_CLAIM_RECOVERY
    assert classify_retry(repository_edited=False, authorization_created=False, permit_issued=False, claim_created=False, operational_write=False, evidence_complete=False) is RetryClassification.NO_RETRY


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("control_plane_owner", "Codex"),
        ("governance_authority", "Codex"),
        ("approval_authority", "Codex"),
        ("retry_authority", "Codex"),
        ("ubuntu_participation", "ORCHESTRATION_OWNER"),
    ],
)
def test_external_authorities_and_ubuntu_ownership_rejected(field: str, value: str) -> None:
    assert not validate_manifest(replace(manifest(), **{field: value})).valid


def test_environment_authorization_env_dependency_and_unsafe_defaults_rejected() -> None:
    value = replace(
        manifest(),
        approval=replace(manifest().approval, environment_authorization_allowed=True),
        secret_dependencies=(".env",),
        forbidden_operations=(),
    )
    errors = set(validate_manifest(value).errors)
    assert {"ENVIRONMENT_ONLY_AUTHORIZATION", "SECRET_DEPENDENCY", "EMPTY_FORBIDDEN_OPERATIONS"} <= errors


def test_schemas_accept_safe_contracts() -> None:
    sprint_schema = json.loads((ROOT / "config/autopilot/sprint-manifest.schema.json").read_text())
    plan_schema = json.loads((ROOT / "config/autopilot/roadmap-plan.schema.json").read_text())
    value = build_manifest(manifest())
    assert not list(Draft202012Validator(sprint_schema).iter_errors(json.loads(value.canonical_json())))
    plan = compile_roadmap((value,))
    assert not list(Draft202012Validator(plan_schema).iter_errors(json.loads(plan.canonical_json())))


def test_no_subprocess_or_network_boundary_and_no_operational_side_effects() -> None:
    forbidden_imports = {"subprocess", "socket", "requests", "httpx", "urllib", "paramiko", "docker"}
    imports: set[str] = set()
    for path in (ROOT / "core/autopilot").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(forbidden_imports)
    policy = AutonomousDeliveryPolicy()
    assert policy.persistent_runner_created is False
    assert policy.production_authorized is False
    assert policy.decision.value == "READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE"
