from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path, PurePosixPath

import pytest

from core.deployment.pilot_evidence import (
    ACTIVATION_STEPS, ROLLBACK_STEPS, InMemoryPilotRollbackUseRegistry,
    PilotEvidenceError, PilotEvidenceManifest, PilotEvidenceService,
    PilotRollbackPlanningService, PilotRollbackRequest, PilotRollbackStatus,
    PilotRollbackValidationService, canonical_json, digest,
)
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/deployment"
D = lambda char: "sha256:" + char * 64
ZERO = {
    "production_writes": 0, "repository_runtime_writes": 0,
    "ubuntu_changes": 0, "network_accesses": 0,
    "runtime_commands": 0, "service_restarts": 0,
}


def bundle(**changes):
    values = {
        "permit_id": "permit-01", "permit_digest": D("a"),
        "execution_authorization_id": "auth-01",
        "readiness_report_id": "ready-01", "readiness_report_digest": D("b"),
        "activation_id": "activation-01", "activation_receipt_id": "receipt-01",
        "activation_receipt_digest": D("c"), "package_digest": D("d"),
        "plan_digest": D("e"), "target_identity": "mac-mini-m4",
        "environment": "staging", "sandbox_root_identity_digest": D("f"),
        "requester_identity": "requester-01", "operator_identity": "operator-01",
        "approver_identity": "approver-01",
        "ordered_activation_steps": ACTIVATION_STEPS,
        "ordered_executor_result_ids": ("result-1", "result-2", "result-3"),
        "ordered_executor_result_digests": (D("1"), D("2"), D("3")),
        "manifest": PilotEvidenceManifest(
            D("0"), D("9"),
            ("artifacts/result-2/manifest.json", "artifacts/result-3/evidence.json"),
            (D("7"), D("8")),
        ),
        "safety_counters": ZERO, "recorded_at": "2026-07-29T16:20:00Z",
    }
    values.update(changes)
    return PilotEvidenceService().create(**values)


def expected(value):
    return {
        key: getattr(value, key) for key in (
            "permit_id", "permit_digest", "execution_authorization_id",
            "readiness_report_id", "readiness_report_digest", "activation_id",
            "activation_receipt_digest", "package_digest", "plan_digest",
            "target_identity", "environment", "sandbox_root_identity_digest",
        )
    }


def request(value, **changes):
    values = {
        "evidence_bundle_id": value.bundle_id, "evidence_digest": value.evidence_digest,
        "operator_identity": "rollback-operator",
        "rollback_approver_identity": "rollback-approver",
        "rollback_approver_role": "rollback-approver",
        "reason_category": "CONTROLLED_TEST_CLOSEOUT",
        "requested_at": "2026-07-29T16:25:00Z",
        "expires_at": "2026-07-29T16:35:00Z",
    }
    values.update(changes)
    return PilotRollbackRequest(**values)


def plan(value):
    report = PilotEvidenceService().validate(value, expected=expected(value), validated_at="2026-07-29T16:21:00Z")
    decision = PilotRollbackPlanningService().plan(request=request(value), bundle=value, report=report)
    assert decision.plan is not None
    return decision.plan


class TempRollbackAdapter:
    def __init__(self, root: Path, root_digest: str, before_digest: str, mutate=None):
        self.root = root.resolve()
        self.root_digest = root_digest
        self.before_digest = before_digest
        self.mutate = mutate
        self.calls = 0

    def rollback(self, *, plan):
        self.calls += 1
        for relative_text in plan.artifact_paths:
            relative = PurePosixPath(relative_text)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe path")
            target = self.root.joinpath(*relative.parts)
            if target.is_symlink() or self.root not in target.resolve().parents:
                raise ValueError("escaped path")
            if target.exists():
                target.unlink()
            parent = target.parent
            while parent != self.root and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        result = {
            "plan_id": plan.plan_id,
            "sandbox_root_identity_digest": self.root_digest,
            "after_rollback_manifest_digest": self.before_digest,
            "evidence_digests": (D("6"),), **ZERO,
        }
        if self.mutate:
            self.mutate(result)
        return result


def test_immutable_deterministic_evidence_and_exact_activation_order():
    first = bundle()
    second = bundle()
    assert first == second
    assert first.bundle_id == second.bundle_id
    assert first.evidence_digest == second.evidence_digest
    assert canonical_json(first) == canonical_json(second)
    with pytest.raises(FrozenInstanceError):
        first.environment = "test"
    report = PilotEvidenceService().validate(first, expected=expected(first), validated_at="2026-07-29T16:21:00Z")
    assert report.status is PilotRollbackStatus.EVIDENCE_VALID


@pytest.mark.parametrize("steps", [
    ACTIVATION_STEPS[:-1],
    (ACTIVATION_STEPS[0], ACTIVATION_STEPS[0], ACTIVATION_STEPS[2]),
    tuple(reversed(ACTIVATION_STEPS)),
    (*ACTIVATION_STEPS[:-1], "UNKNOWN"),
])
def test_missing_duplicate_reordered_or_unknown_activation_step_denied(steps):
    value = bundle(ordered_activation_steps=steps)
    report = PilotEvidenceService().validate(value, expected=expected(value), validated_at="2026-07-29T16:21:00Z")
    assert report.status is PilotRollbackStatus.EVIDENCE_INVALID
    assert report.findings[0].code == "ACTIVATION_STEP_ORDER_INVALID"


@pytest.mark.parametrize("field", [
    "permit_digest", "activation_receipt_digest", "readiness_report_digest",
    "package_digest", "plan_digest", "target_identity", "environment",
    "sandbox_root_identity_digest",
])
def test_binding_mismatches_are_deterministically_detected(field):
    value = bundle()
    bindings = expected(value)
    bindings[field] = "changed"
    report = PilotEvidenceService().validate(value, expected=bindings, validated_at="2026-07-29T16:21:00Z")
    assert report.status is PilotRollbackStatus.EVIDENCE_INVALID
    assert any(finding.field == field for finding in report.findings)


def test_altered_digest_duplicate_evidence_and_nonzero_safety_denied():
    value = bundle()
    altered = replace(value, evidence_digest=D("x"))
    assert PilotEvidenceService().validate(altered, expected=expected(value), validated_at="x").status is PilotRollbackStatus.EVIDENCE_INVALID
    with pytest.raises(PilotEvidenceError, match="duplicate evidence"):
        PilotEvidenceManifest(D("0"), D("9"), ("a",), (D("7"), D("7")))
    unsafe = bundle(safety_counters={**ZERO, "network_accesses": 1})
    assert any(f.field == "network_accesses" for f in PilotEvidenceService().validate(unsafe, expected=expected(unsafe), validated_at="x").findings)


@pytest.mark.parametrize("field", [
    "password", "api_key", "access_token", "private_key", "cookie",
    "authorization_header", "raw_environment", "shell", "command", "argv", "script",
])
def test_secret_and_arbitrary_operation_fields_rejected(field):
    with pytest.raises(PilotEvidenceError):
        bundle(safety_counters={**ZERO, field: 0})


def test_deterministic_evidence_derived_plan_and_separation_of_duties():
    value = bundle()
    first = plan(value)
    second = plan(value)
    assert first == second
    assert first.plan_id == second.plan_id
    assert tuple(step.operation for step in first.steps) == ROLLBACK_STEPS
    assert first.artifact_paths == value.manifest.artifact_paths
    report = PilotEvidenceService().validate(value, expected=expected(value), validated_at="x")
    denied = PilotRollbackPlanningService().plan(
        request=request(value, operator_identity="same", rollback_approver_identity="same"),
        bundle=value, report=report,
    )
    assert denied.status is PilotRollbackStatus.DENIED


def test_exactly_one_successful_controlled_pytest_rollback(tmp_path):
    value = bundle()
    rollback_plan = plan(value)
    for relative in rollback_plan.artifact_paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("controlled activation artifact")
    registry = InMemoryPilotRollbackUseRegistry()
    adapter = TempRollbackAdapter(tmp_path, value.sandbox_root_identity_digest, value.manifest.before_state_manifest_digest)
    service = PilotRollbackValidationService(adapter=adapter, registry=registry)
    first = service.rollback(plan=rollback_plan, bundle=value)
    assert first.status is PilotRollbackStatus.ROLLED_BACK
    assert adapter.calls == 1
    assert first.receipt.after_rollback_manifest_digest == value.manifest.before_state_manifest_digest
    assert first.receipt.ordered_rollback_steps == ROLLBACK_STEPS
    assert not any((tmp_path / relative).exists() for relative in rollback_plan.artifact_paths)
    assert first.receipt.persistent_host_rollback is False
    assert first.receipt.production_authorized is False


def test_receipt_determinism_replay_and_failure_consumption(tmp_path):
    value = bundle()
    rollback_plan = plan(value)
    service = PilotRollbackValidationService(
        adapter=TempRollbackAdapter(tmp_path, value.sandbox_root_identity_digest, value.manifest.before_state_manifest_digest),
        registry=InMemoryPilotRollbackUseRegistry(),
    )
    first = service.rollback(plan=rollback_plan, bundle=value)
    semantic = first.receipt.to_dict()
    receipt_digest = semantic.pop("receipt_digest")
    assert receipt_digest == digest(semantic)
    assert service.rollback(plan=rollback_plan, bundle=value).status is PilotRollbackStatus.REPLAYED
    failing = PilotRollbackValidationService(
        adapter=TempRollbackAdapter(tmp_path, value.sandbox_root_identity_digest, value.manifest.before_state_manifest_digest, lambda result: result.update(network_accesses=1)),
        registry=InMemoryPilotRollbackUseRegistry(),
    )
    assert failing.rollback(plan=rollback_plan, bundle=value).status is PilotRollbackStatus.FAILED
    assert failing.rollback(plan=rollback_plan, bundle=value).status is PilotRollbackStatus.REPLAYED


@pytest.mark.parametrize(("mutate", "reason"), [
    (lambda result: result.pop("plan_id"), "MALFORMED_ROLLBACK_RESULT"),
    (lambda result: result.update(plan_id="wrong"), "ROLLBACK_ADAPTER_BINDING_MISMATCH"),
    (lambda result: result.update(after_rollback_manifest_digest=D("x")), "PRE_ACTIVATION_STATE_NOT_RESTORED"),
])
def test_malformed_binding_and_prestate_fail_closed(tmp_path, mutate, reason):
    value = bundle()
    decision = PilotRollbackValidationService(
        adapter=TempRollbackAdapter(tmp_path, value.sandbox_root_identity_digest, value.manifest.before_state_manifest_digest, mutate),
        registry=InMemoryPilotRollbackUseRegistry(),
    ).rollback(plan=plan(value), bundle=value)
    assert decision.status is PilotRollbackStatus.FAILED
    assert reason in decision.reason_codes


def test_missing_adapter_registry_and_malformed_request_default_deny():
    value = bundle()
    rollback_plan = plan(value)
    assert PilotRollbackValidationService(adapter=None, registry=InMemoryPilotRollbackUseRegistry()).rollback(plan=rollback_plan, bundle=value).status is PilotRollbackStatus.BLOCKED
    assert PilotRollbackValidationService(adapter=TempRollbackAdapter(Path("/tmp"), D("f"), D("0")), registry=None).rollback(plan=rollback_plan, bundle=value).status is PilotRollbackStatus.BLOCKED
    report = PilotEvidenceService().validate(value, expected=expected(value), validated_at="x")
    expired = PilotRollbackPlanningService().plan(request=request(value, expires_at="2026-07-29T16:00:00Z"), bundle=value, report=report)
    assert expired.status is PilotRollbackStatus.DENIED


@pytest.mark.parametrize("unsafe", ["../escape", "/tmp/escape"])
def test_out_of_root_and_parent_traversal_rejected(tmp_path, unsafe):
    value = bundle(manifest=PilotEvidenceManifest(D("0"), D("9"), (unsafe,), (D("7"),)))
    with pytest.raises(ValueError):
        TempRollbackAdapter(tmp_path, D("f"), D("0")).rollback(plan=plan(value))


def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path.parent / "outside-m2p3"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "artifacts"
    link.symlink_to(outside, target_is_directory=True)
    value = bundle(manifest=PilotEvidenceManifest(D("0"), D("9"), ("artifacts/file",), (D("7"),)))
    with pytest.raises(ValueError):
        TempRollbackAdapter(tmp_path, D("f"), D("0")).rollback(plan=plan(value))


def test_fixtures_dependency_boundary_and_no_forbidden_capability():
    names = {
        "m2-p3-valid-evidence.json", "m2-p3-altered-evidence.json",
        "m2-p3-missing-activation-step.json", "m2-p3-controlled-rollback.json",
        "m2-p3-rollback-replay.json", "m2-p3-rollback-adapter-failure.json",
        "m2-p3-rollback-root-mismatch.json",
    }
    for name in names:
        value = json.loads((FIXTURES / name).read_text())
        assert value["schema_version"] == "dpl/m2-p3-fixture/v1"
        assert value["production_authorized"] is False
    forbidden = {"subprocess", "socket", "requests", "paramiko", "sqlite3", "core.api", "core.worker"}
    for source in (ROOT / "core/deployment/pilot_evidence").glob("*.py"):
        tree = ast.parse(source.read_text())
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(item == prefix or item.startswith(prefix + ".") for item in imports for prefix in forbidden)
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
