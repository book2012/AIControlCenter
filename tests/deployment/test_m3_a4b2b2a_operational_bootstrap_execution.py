from __future__ import annotations

import dataclasses
import json
import os
import stat
from pathlib import Path

import pytest

from core.deployment.operational_bootstrap_execution import *
from core.deployment.policy.dependency_boundaries import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
COMMIT = "1" * 40
NOW = "2026-07-30T12:00:00+09:00"
DIGEST = "sha256:" + "a" * 64


class Home:
    def __init__(self, path):
        self.path = path

    def resolve(self):
        return self.path


def canonical_file(path, value):
    path.write_text(canonical_json(value), encoding="utf-8")
    return path


def permit():
    content = {
        "permit_id": "permit-test-1", "branch": "feature/deployment-package",
        "commit": COMMIT, "issued_at": "2026-07-30T11:00:00+09:00",
        "not_before": "2026-07-30T11:30:00+09:00",
        "expires_at": "2026-07-30T13:00:00+09:00",
        "bootstrap_execution_deadline": "2026-07-30T12:30:00+09:00",
        "maximum_uses": 1, "claimed": False,
        "environment": "CONTROLLED_NON_PRODUCTION",
        "operator_identity": "mac-operator-01",
        "approver_identity": "security-approver-02",
        "warning_acknowledgements": ["warning-427", "production-disabled"],
        "readiness_report_digest": DIGEST, "preflight_report_digest": DIGEST,
        "schema_binding_digest": DIGEST, "target_binding_digest": DIGEST,
        "plan_binding_digest": DIGEST, "bootstrap_authorized": True,
        "writers_authorized": False, "monitoring_authorized": False,
        "external_dispatch_authorized": False, "production_authorized": False,
    }
    content["permit_digest"] = canonical_digest(content)
    return content


@pytest.fixture
def roots(tmp_path):
    execution = Path(os.environ["AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT"])
    home_base = Path(os.environ["AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_HOME"])
    root = execution / tmp_path.parent.name / tmp_path.name
    home = home_base / tmp_path.parent.name / tmp_path.name
    root.mkdir(parents=True)
    home.mkdir(parents=True)
    return root, home


def setup_execution(roots, *, adapter=None, change=None):
    execution, home = roots
    value = permit()
    if change:
        value.update(change)
        if "permit_digest" not in change:
            unsigned = dict(value)
            unsigned.pop("permit_digest", None)
            value["permit_digest"] = canonical_digest(unsigned)
    permit_path = canonical_file(execution / "permit.json", value)
    issuance = {"permit_id": value["permit_id"], "permit_digest": value["permit_digest"]}
    issuance_path = canonical_file(execution / "issuance.json", issuance)
    request = OperationalBootstrapRuntimeRequest(
        "request-1", OperationalBootstrapRuntimeMode.TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION,
        "feature/deployment-package", COMMIT, "mac-operator-01", NOW, NOW,
        permit_path, issuance_path, execution / "evidence", {})
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=Home(home), repository_root=ROOT, test_home=home)
    paths = policy.resolve(test_only=True)
    host = OperationalBootstrapHostRevalidationEvidence(
        "Darwin", 501, home, ROOT, True, 0, 0, 10**9)
    target = OperationalBootstrapTargetRevalidationEvidence(
        paths.root, True, True, True)
    coordinator = OperationalMacBootstrapExecutionCoordinator(
        config=OperationalBootstrapExecutionConfig(request.mode, ROOT),
        artifact_reader=StrictJsonArtifactReader(),
        claim_registry=AtomicPermitClaimFileRegistry(), path_policy=policy,
        runtime_adapter=adapter or TestOnlyOperationalBootstrapRuntimeAdapter())
    return coordinator, request, host, target, paths


def test_immutable_contracts_modes_and_deterministic_plan(roots):
    plan = OperationalBootstrapRuntimePlan.build()
    assert plan == OperationalBootstrapRuntimePlan.build()
    assert tuple(x.code for x in plan.steps) == RUNTIME_STEP_CODES
    assert OperationalBootstrapRuntimeMode.CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.plan_digest = DIGEST
    for mode in ("GENERAL_OPERATIONAL", "ACTIVE", "LIVE_CUSTOMER", "PRODUCTION",
                 "CUSTOMER_PRODUCTION", "UBUNTU", "WORKER"):
        with pytest.raises(OperationalBootstrapExecutionError):
            OperationalBootstrapExecutionConfig(mode, ROOT)


def test_exact_paths_trusted_home_and_caller_root_rejected(roots):
    _, home = roots
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=Home(home), repository_root=ROOT, test_home=home)
    paths = policy.resolve(test_only=True)
    expected = home / "Library" / "Application Support" / "AIControlCenter"
    assert paths.root == expected
    assert paths.audit_database == expected / "audit/audit-ledger.sqlite3"
    assert paths.audit_backups == expected / "audit/backups"
    assert paths.replay_database == expected / "security/permit-replay.sqlite3"
    assert paths.replay_backups == expected / "security/backups"
    assert paths.monitoring == expected / "monitoring"
    with pytest.raises(OperationalBootstrapExecutionError):
        policy.resolve(caller_root=home / "chosen", test_only=True)


def test_live_permit_validation_window_scope_and_bindings(roots):
    coordinator, request, host, target, _ = setup_execution(roots)
    bundle = coordinator.execute(request=request, host=host, target=target)
    assert bundle.receipt.status is OperationalBootstrapRuntimeStatus.COMPLETE
    assert tuple(step.code for step in bundle.receipt.step_receipts) == RUNTIME_STEP_CODES
    assert OperationalBootstrapRuntimeEvidenceValidator().validate(
        bundle).status is OperationalBootstrapRuntimeStatus.COMPLETE


@pytest.mark.parametrize(("change", "code"), [
    ({"not_before": "2026-07-30T12:01:00+09:00"}, "PERMIT_NOT_YET_VALID"),
    ({"expires_at": NOW}, "PERMIT_EXPIRED"),
    ({"bootstrap_execution_deadline": NOW}, "BOOTSTRAP_DEADLINE_EXPIRED"),
    ({"maximum_uses": 2}, "PERMIT_USE_STATE_INVALID"),
    ({"environment": "PRODUCTION"}, "PERMIT_ENVIRONMENT_INVALID"),
    ({"writers_authorized": True}, "PERMIT_SCOPE_INVALID"),
    ({"monitoring_authorized": True}, "PERMIT_SCOPE_INVALID"),
    ({"external_dispatch_authorized": True}, "PERMIT_SCOPE_INVALID"),
    ({"production_authorized": True}, "PERMIT_SCOPE_INVALID"),
])
def test_invalid_permits_fail_before_claim_and_target_write(roots, change, code):
    coordinator, request, host, target, paths = setup_execution(roots, change=change)
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        coordinator.execute(request=request, host=host, target=target)
    assert caught.value.code == code
    assert not request.permit_path.with_name("permit.json.claim.json").exists()
    assert not paths.root.exists()


def test_atomic_claim_modes_second_claim_and_full_test_bootstrap(roots):
    coordinator, request, host, target, paths = setup_execution(roots)
    bundle = coordinator.execute(request=request, host=host, target=target)
    claim = request.permit_path.with_name("permit.json.claim.json")
    assert stat.S_IMODE(claim.stat().st_mode) == 0o600
    assert stat.S_IMODE(claim.parent.stat().st_mode) == 0o700
    assert paths.audit_database.exists() and paths.replay_database.exists()
    assert (paths.audit_backups / "baseline.sqlite3").exists()
    assert (paths.replay_backups / "baseline.sqlite3").exists()
    assert paths.monitoring.exists() and not tuple(paths.monitoring.iterdir())
    assert not bundle.receipt.writers_activated
    assert not bundle.receipt.monitoring_activated
    assert not bundle.receipt.external_dispatch_activated
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        AtomicPermitClaimFileRegistry().claim(claim.with_name("permit.json"),
                                              bundle.receipt and bundle.receipt
                                              and OperationalBootstrapClaimRequest(
                                                  "permit-test-1", permit()["permit_digest"],
                                                  "feature/deployment-package", COMMIT,
                                                  "other-operator", NOW, "request-2"))
    assert caught.value.code == "PERMIT_ALREADY_CLAIMED"


def test_post_claim_failure_preserves_claim_and_cleans_created_artifacts(roots):
    adapter = TestOnlyOperationalBootstrapRuntimeAdapter(
        failure_step="BOOTSTRAP_REPLAY_SQLITE_DATABASE")
    coordinator, request, host, target, paths = setup_execution(roots, adapter=adapter)
    with pytest.raises(OperationalBootstrapExecutionError):
        coordinator.execute(request=request, host=host, target=target)
    assert request.permit_path.with_name("permit.json.claim.json").exists()
    assert not paths.root.exists()


def test_runtime_host_target_capacity_and_existing_target_gates(roots):
    coordinator, request, host, target, paths = setup_execution(roots)
    for changed in (
        dataclasses.replace(host, system="Linux"),
        dataclasses.replace(host, uid=0),
        dataclasses.replace(host, git_clean=False),
        dataclasses.replace(host, upstream_behind=1),
        dataclasses.replace(host, available_bytes=0),
    ):
        with pytest.raises(OperationalBootstrapExecutionError):
            coordinator.execute(request=request, host=changed, target=target)
    paths.root.mkdir(parents=True)
    paths.monitoring.mkdir()
    with pytest.raises(OperationalBootstrapExecutionError):
        coordinator.execute(request=request, host=host, target=target)


def test_symlink_repository_and_untrusted_volume_rejected(roots):
    execution, home = roots
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=Home(ROOT), repository_root=ROOT, test_home=ROOT)
    with pytest.raises(OperationalBootstrapExecutionError):
        policy.resolve(test_only=True)
    link = home / "Library"
    link.symlink_to(execution, target_is_directory=True)
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=Home(home), repository_root=ROOT, test_home=home)
    with pytest.raises(OperationalBootstrapExecutionError):
        policy.resolve(test_only=True)


def test_json_runner_validation_without_execution(roots, capsys):
    execution, _ = roots
    request = {
        "request_id": "runner-1",
        "mode": "TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION",
        "branch": "feature/deployment-package", "commit": COMMIT,
        "operator_identity": "mac-operator-01", "requested_at": NOW, "claim_at": NOW,
        "permit_path": str(execution / "permit.json"),
        "issuance_evidence_path": str(execution / "issuance.json"),
        "evidence_directory": str(execution / "evidence"), "metadata": {},
    }
    path = canonical_file(execution / "request.json", request)
    from core.deployment.operational_bootstrap_execution.runner import main
    assert main(["--request", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "VALIDATED"
    request["mode"] = "CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP"
    canonical_file(path, request)
    assert main(["--request", str(path)]) != 0


def test_dependency_policy_and_forbidden_imports():
    package = ROOT / "core/deployment/operational_bootstrap_execution"
    paths = [str(path.relative_to(ROOT)) for path in package.glob("*.py")]
    assert validate_dependency_boundaries(
        repository_root=ROOT, paths=paths)["overall_result"] == "PASS"
    source = "\n".join((ROOT / path).read_text() for path in paths)
    for forbidden in ("subprocess", "socket", "requests", "core.api", "core.worker",
                      "UbuntuWorkerClient", "paramiko", "launchctl"):
        assert forbidden not in source
