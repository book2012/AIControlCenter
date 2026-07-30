from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path

import pytest

from core.deployment.audit_sqlite import (
    SQLiteAuditReadOnlyInspector, SQLiteAuditSchemaExpectation,
    SQLiteAuditStatus, SQLiteAuditStorageConfig,
)
from core.deployment.contracts import sha256_digest
from core.deployment.operational_monitoring import (
    MonitoringEvidence, OperationalMonitoringConfig,
    OperationalMonitoringService, OperationalStage,
)
from core.deployment.permit_replay_sqlite import (
    PermitReplayReadOnlyInspector, PermitReplaySchemaExpectation,
    PermitReplayStatus, PermitReplayStorageConfig,
)
from core.deployment.operational_bootstrap_execution import (
    AtomicPermitClaimFileRegistry,
    MacOperationalBootstrapRuntimeAdapter,
    MacOperationalBootstrapPathPolicy,
    OperationalBootstrapExecutionConfig,
    OperationalBootstrapHostRevalidationEvidence,
    OperationalBootstrapRuntimeMode,
    OperationalBootstrapRuntimeRequest,
    OperationalBootstrapRuntimeStatus,
    OperationalBootstrapTargetRevalidationEvidence,
    OperationalMacBootstrapExecutionCoordinator,
    StrictJsonArtifactReader,
    TestOnlyOperationalBootstrapRuntimeAdapter,
)
from core.deployment.operational_activation_authorization import *
from core.deployment.operational_bootstrap_live import *
from core.deployment.operational_bootstrap_live.runner import main
from core.deployment.policy.dependency_boundaries import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
COMMIT = "d3155c0d7cc255b521bfb5b9451cadbe6367e0f6"
DIGEST = "sha256:" + "a" * 64


def payload(tmp_path: Path) -> dict:
    artifact_root = tmp_path / "evidence"
    permit = artifact_root / "permit.json"
    return {
        "request_id": "m3-a4b2b2b-r3-test-request",
        "branch": "feature/deployment-package",
        "commit": COMMIT,
        "trusted_operational_root": str(
            tmp_path / "home/Library/Application Support/AIControlCenter"),
        "requester_identity": "test:requester:r3",
        "operator_identity": "test:operator:r3",
        "independent_approver_identity": "test:approver:r3",
        "artifacts": {
            "approval_input": str(artifact_root / "approval.json"),
            "shared_parent_preflight_evidence": str(artifact_root / "preflight.json"),
            "activation_authorization_request_output": str(artifact_root / "activation-request.json"),
            "activation_authorization_output": str(artifact_root / "activation.json"),
            "activation_authorization_evidence_output": str(artifact_root / "activation-evidence.json"),
            "operational_permit_output": str(permit),
            "permit_issuance_evidence_output": str(artifact_root / "issuance.json"),
            "permit_claim_output": str(permit.with_name("permit.json.claim.json")),
            "bootstrap_receipt_output": str(artifact_root / "receipt.json"),
            "bootstrap_evidence_output": str(artifact_root / "bootstrap-evidence.json"),
            "post_bootstrap_validation_output": str(artifact_root / "validation.json"),
        },
        "time_policy": {
            "requested_at": "2026-07-30T12:00:00+09:00",
            "approval_maximum_age_seconds": 3600,
            "activation_not_before": "2026-07-30T12:00:00+09:00",
            "activation_expires_at": "2026-07-30T13:00:00+09:00",
            "permit_not_before": "2026-07-30T12:01:00+09:00",
            "permit_expires_at": "2026-07-30T12:59:00+09:00",
            "bootstrap_execution_deadline": "2026-07-30T12:30:00+09:00",
            "maximum_uses": 1,
        },
        "restriction_acknowledgement_digests": [DIGEST, "sha256:" + "b" * 64],
        "active_restriction_digests": [DIGEST],
        "restriction_acknowledgements": [
            {
                "restriction_identifier": "warnings-427",
                "acknowledging_identity": identity,
                "acknowledgement_digest": digest,
                "restriction_digest": DIGEST,
                "branch": "feature/deployment-package",
                "commit": COMMIT,
                "request_id": "m3-a4b2b2b-r3-test-request",
                "synthetic": False,
                "placeholder": False,
            }
            for identity, digest in (
                ("test:operator:r3", DIGEST),
                ("test:approver:r3", "sha256:" + "b" * 64))
        ],
        "scope": "CONTROLLED_NON_PRODUCTION",
        "maximum_uses": 1,
        "production_authorized": False,
        "writers_authorized": False,
        "monitoring_authorized": False,
        "external_dispatch_authorized": False,
    }


def write_request(tmp_path: Path, change=None) -> Path:
    value = payload(tmp_path)
    if change:
        change(value)
    path = tmp_path / "request.json"
    path.write_text(canonical_json(value))
    return path


def test_immutable_deterministic_strict_request(tmp_path):
    path = write_request(tmp_path)
    first = ControlledOperationalBootstrapRequestValidator().parse(path)
    second = ControlledOperationalBootstrapRequestValidator().parse(path)
    assert first == second
    assert canonical_digest(first.as_dict()) == canonical_digest(second.as_dict())
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.commit = "0" * 40


@pytest.mark.parametrize("field,value", [
    ("maximum_uses", 2), ("production_authorized", True),
    ("writers_authorized", True), ("monitoring_authorized", True),
    ("external_dispatch_authorized", True), ("scope", "PRODUCTION"),
])
def test_default_deny_scope_and_capabilities(tmp_path, field, value):
    path = write_request(tmp_path, lambda item: item.__setitem__(field, value))
    with pytest.raises((ControlledOperationalBootstrapError, ValueError)):
        ControlledOperationalBootstrapRequestValidator().parse(path)


def test_unknown_json_and_cli_arguments_rejected(tmp_path, capsys):
    path = write_request(tmp_path, lambda item: item.__setitem__("argv", []))
    assert main(["--request", str(path)]) == 2
    assert "UNSAFE_FIELD_REJECTED" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["--request", str(path), "--adapter", "test"])


def test_cli_is_fail_closed_without_reviewed_composition(tmp_path, capsys):
    path = write_request(tmp_path)
    assert main(["--request", str(path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "TARGET_BINDING_INVALID"


def test_live_orchestrator_rejects_test_adapter():
    with pytest.raises(ControlledOperationalBootstrapError, match="TEST_ADAPTER_REJECTED"):
        ControlledOperationalBootstrapOrchestrator(
            approval_reader=None, preflight_reader=None, artifact_writer=None,
            git_evidence=None, host_evidence=None, clock=None,
            activation_service=None, permit_service=None, execution_coordinator=None,
            runtime_adapter=TestOnlyOperationalBootstrapRuntimeAdapter())


def test_validation_runner_unchanged_and_direct_coordinator_dependency():
    validation_runner = (
        ROOT / "core/deployment/operational_bootstrap_execution/runner.py").read_text()
    live = (ROOT / "core/deployment/operational_bootstrap_live/coordinator.py").read_text()
    assert "CONTROLLED_EXECUTION_REQUIRES_COORDINATOR" in validation_runner
    assert "OperationalMacBootstrapExecutionCoordinator" not in validation_runner
    assert "execution_coordinator.execute" in live
    assert "operational_bootstrap_execution.runner" not in live
    assert "MacOperationalBootstrapRuntimeAdapter" in live


def test_dependency_policy_and_forbidden_dependencies():
    paths = [str(path.relative_to(ROOT)) for path in
             (ROOT / "core/deployment/operational_bootstrap_live").glob("*.py")]
    assert validate_dependency_boundaries(
        repository_root=ROOT, paths=paths)["overall_result"] == "PASS"
    source = "\n".join((ROOT / path).read_text() for path in paths)
    for forbidden in ("subprocess", "socket", "requests", "core.api", "core.worker",
                      "UbuntuWorkerClient", "paramiko", "launchctl"):
        assert forbidden not in source


class FakeHome:
    def __init__(self, path):
        self.path = path

    def resolve(self):
        return self.path


def tree_digest(path: Path) -> str:
    if not path.exists():
        return "ABSENT"
    digest = hashlib.sha256()
    for child in sorted(path.rglob("*")):
        digest.update(str(child.relative_to(path)).encode())
        if child.is_file():
            digest.update(child.read_bytes())
    return digest.hexdigest()


class ConfinedInspectorPathPolicy:
    def __init__(self, root: Path):
        self.root = root

    def identity_digest(self, path: Path) -> str:
        return sha256_digest({"path": str(path)})

    def validate(self, path: Path) -> tuple[str, ...]:
        try:
            path.resolve().relative_to(self.root.resolve())
            return ()
        except ValueError:
            return ("OUTSIDE_TEST_ROOT",)


def independently_inspect(paths, now):
    policy = ConfinedInspectorPathPolicy(paths.root)
    audit = SQLiteAuditReadOnlyInspector(
        config=SQLiteAuditStorageConfig(paths.audit_database),
        path_policy=policy, schema=SQLiteAuditSchemaExpectation()).inspect(
            inspected_at=now)
    replay = PermitReplayReadOnlyInspector(
        config=PermitReplayStorageConfig(paths.replay_database),
        path_policy=policy, schema=PermitReplaySchemaExpectation()).inspect(
            inspected_at=now)
    return audit, replay


def preactivation_snapshot(audit, replay, now):
    evidence = MonitoringEvidence(
        observed_at=now,
        audit_inspection_status=audit.status.value,
        audit_inspection_report_id=audit.report_id,
        audit_inspection_report_digest=audit.report_digest,
        audit_evidence_generated_at=now,
        audit_schema_valid=not audit.schema_findings,
        audit_hash_chain_valid=audit.chain_result == "VALID",
        audit_production_privacy_violations=audit.production_authorization_violations,
        audit_recovery_status="RECOVERY_VALID",
        audit_recovery_report_id="test-audit-recovery",
        audit_recovery_report_digest=DIGEST,
        audit_recovery_evidence_generated_at=now,
        audit_backup_age_seconds=0, audit_recovery_drill_age_seconds=0,
        replay_inspection_status=replay.status.value,
        replay_inspection_report_id=replay.report_id,
        replay_inspection_report_digest=replay.report_digest,
        replay_evidence_generated_at=now,
        replay_schema_valid=not replay.schema_findings,
        replay_hash_chain_valid=replay.chain_result == "VALID",
        replay_state_machine_valid=replay.invalid_count == 0,
        replay_violation_count=replay.replay_violations,
        replay_recovery_status="RECOVERY_VALID",
        replay_recovery_report_id="test-replay-recovery",
        replay_recovery_report_digest=DIGEST,
        replay_recovery_evidence_generated_at=now,
        replay_backup_age_seconds=0, replay_recovery_drill_age_seconds=0,
        permit_states_restored=True, replay_protection_restored=True,
        post_recovery_concurrency_valid=True,
        m2_readiness_status="READY", m2_readiness_report_id="test-m2",
        m2_readiness_report_digest=DIGEST, m2_evidence_generated_at=now,
        controlled_pilot_closeout_status="CLOSED",
        pilot_report_id="test-pilot", pilot_report_digest=DIGEST,
        pilot_evidence_generated_at=now, regression_passed=1,
        regression_failed=0, regression_deselected=0, regression_warnings=0,
        git_clean=True, git_ahead=0, git_behind=0, documentation_complete=True,
        control_plane_owner="AIControlCenter/Mac",
        operational_audit_database_created=False,
        operational_replay_database_created=False,
        operational_writer_activated=False,
        operational_backup_schedule_activated=False,
        safety_counters={
            "operational_database_files_created": 0,
            "monitoring_database_writes": 0, "operational_audit_writes": 0,
            "operational_replay_writes": 0, "alerts_dispatched": 0,
            "notifications_sent": 0, "n8n_invocations": 0,
            "network_requests": 0, "ubuntu_changes": 0,
            "runtime_infrastructure_commands": 0, "service_restarts": 0,
            "api_write_routes": 0, "production_activations": 0},
        production_authorized=False)
    config = OperationalMonitoringConfig(
        3600, 3600, 7200, 86400, 172800, 3600, 7200, 86400, 172800)
    return OperationalMonitoringService(config).evaluate(
        evidence, stage=OperationalStage.PRE_ACTIVATION)


def activation(root: Path, now: str):
    request = OperationalActivationAuthorizationRequest(
        "approval-r3", DIGEST, "review-r3", DIGEST,
        OperationalActivationAuthorizationIdentityBinding(
            "test:requester:r3", "test:operator:r3", "test:approver:r3"),
        OperationalActivationAuthorizationRestrictionBinding(
            (DIGEST, "sha256:" + "b" * 64), (DIGEST,)),
        OperationalActivationAuthorizationCommitBinding(
            "feature/deployment-package", COMMIT, True, 0, 0),
        OperationalActivationAuthorizationWindow(
            "2026-07-30T11:00:00+09:00", "2026-07-30T11:30:00+09:00",
            "2026-07-30T13:00:00+09:00"),
        OperationalActivationAuthorizationSafetyBinding({
            "operational_permits_issued": 0, "live_claims": 0,
            "bootstrap_executions": 0, "production_activations": 0}),
        DIGEST, root, DIGEST, DIGEST, {"audit": DIGEST, "replay": DIGEST}, DIGEST)
    config = OperationalActivationAuthorizationConfig(
        "feature/deployment-package", COMMIT, root)
    _, permit = OperationalActivationAuthorizationCoordinator().build(
        config=config, request=request, decided_at=now, issued_at=now)
    assert OperationalActivationAuthorizationValidator().validate(
        config=config, permit=permit, validated_at=now,
        operator_identity="test:operator:r3").status.value == "AUTHORIZED"
    return permit


def live_execution(tmp_path: Path, *, failure_step=None):
    live_root = Path(os.environ["AICONTROLCENTER_OPERATIONAL_LIVE_TEST_ROOT"])
    case = live_root / tmp_path.parent.name / tmp_path.name
    home = case / "home"
    shared = home / "Library/Application Support/AIControlCenter"
    shared.mkdir(parents=True, mode=0o700)
    sibling = shared / "unrelated-existing-sibling.txt"
    sibling.write_text("preserve-me", encoding="utf-8")
    sibling_before = tree_digest(shared)
    actual = Path.home() / "Library/Application Support/AIControlCenter"
    actual_before = tree_digest(actual)
    evidence = case / "evidence"
    evidence.mkdir(parents=True)
    now = "2026-07-30T12:00:00+09:00"
    auth = activation(shared, now)
    permit = {
        "permit_id": "permit-r3-test", "branch": "feature/deployment-package",
        "commit": COMMIT, "issued_at": "2026-07-30T11:45:00+09:00",
        "not_before": "2026-07-30T11:50:00+09:00",
        "expires_at": "2026-07-30T13:00:00+09:00",
        "bootstrap_execution_deadline": "2026-07-30T12:30:00+09:00",
        "maximum_uses": 1, "claimed": False,
        "environment": "CONTROLLED_NON_PRODUCTION",
        "operator_identity": "test:operator:r3",
        "approver_identity": "test:approver:r3",
        "warning_acknowledgements": ["warning-427", "production-disabled"],
        "readiness_report_digest": DIGEST, "preflight_report_digest": DIGEST,
        "schema_binding_digest": DIGEST, "target_binding_digest": DIGEST,
        "plan_binding_digest": DIGEST, "bootstrap_authorized": True,
        "writers_authorized": False, "monitoring_authorized": False,
        "external_dispatch_authorized": False, "production_authorized": False,
    }
    from core.deployment.operational_bootstrap_execution import canonical_digest as runtime_digest
    permit["permit_digest"] = runtime_digest(permit)
    permit_path = evidence / "permit.json"
    permit_path.write_text(
        json.dumps(permit, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    issuance_path = evidence / "issuance.json"
    issuance_path.write_text(json.dumps({
        "permit_id": permit["permit_id"], "permit_digest": permit["permit_digest"]},
        sort_keys=True, separators=(",", ":")), encoding="utf-8")
    runtime_request = OperationalBootstrapRuntimeRequest(
        "request-r3", OperationalBootstrapRuntimeMode.CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP,
        "feature/deployment-package", COMMIT, "test:operator:r3", now, now,
        permit_path, issuance_path, evidence, {},
        activation_authorization_digest=auth.authorization_digest)
    policy = MacOperationalBootstrapPathPolicy(
        home_resolver=FakeHome(home), repository_root=ROOT)
    paths = policy.resolve()
    host = OperationalBootstrapHostRevalidationEvidence(
        "Darwin", 501, home, ROOT, True, 0, 0, 10**9)
    target = OperationalBootstrapTargetRevalidationEvidence(
        paths.root, True, True, True)
    coordinator = OperationalMacBootstrapExecutionCoordinator(
        config=OperationalBootstrapExecutionConfig(runtime_request.mode, ROOT),
        artifact_reader=StrictJsonArtifactReader(),
        claim_registry=AtomicPermitClaimFileRegistry(), path_policy=policy,
        runtime_adapter=MacOperationalBootstrapRuntimeAdapter(
            failure_step=failure_step))
    return (coordinator, runtime_request, host, target, auth, paths, sibling,
            sibling_before, actual, actual_before)


def test_pytest_owned_end_to_end_mac_bootstrap_and_atomic_claim(tmp_path):
    values = live_execution(tmp_path)
    coordinator, request, host, target, auth, paths, sibling, _, actual, actual_before = values
    bundle = coordinator.execute(
        request=request, host=host, target=target, activation_authorization=auth)
    assert bundle.receipt.status is OperationalBootstrapRuntimeStatus.COMPLETE
    assert paths.audit_database.is_file() and paths.replay_database.is_file()
    assert (paths.audit_backups / "baseline.sqlite3").is_file()
    assert (paths.replay_backups / "baseline.sqlite3").is_file()
    assert sibling.read_text(encoding="utf-8") == "preserve-me"
    assert not bundle.receipt.writers_activated
    assert not bundle.receipt.monitoring_activated
    assert not bundle.receipt.external_dispatch_activated
    assert tree_digest(actual) == actual_before
    audit, replay = independently_inspect(paths, request.requested_at)
    assert audit.status is SQLiteAuditStatus.HEALTHY
    assert not audit.schema_findings
    assert audit.integrity_result == "OK"
    assert audit.chain_result == "VALID"
    assert audit.event_count == 0
    assert replay.status is PermitReplayStatus.HEALTHY
    assert not replay.schema_findings
    assert replay.invalid_count == 0 and replay.replay_violations == 0
    assert replay.chain_result == "VALID"
    assert replay.event_count == 0
    first = preactivation_snapshot(audit, replay, request.requested_at)
    second = preactivation_snapshot(audit, replay, request.requested_at)
    assert first.operational_stage is OperationalStage.PRE_ACTIVATION
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_digest == second.snapshot_digest
    assert first.alerts_dispatched == 0 and first.notifications_sent == 0
    assert not first.production_authorized
    claim = request.permit_path.with_name("permit.json.claim.json")
    assert claim.is_file()
    from core.deployment.operational_bootstrap_execution import OperationalBootstrapClaimRequest
    with pytest.raises(Exception, match="PERMIT_ALREADY_CLAIMED"):
        AtomicPermitClaimFileRegistry().claim(
            request.permit_path, OperationalBootstrapClaimRequest(
                "conflicting-permit", DIGEST, request.branch, request.commit,
                request.operator_identity, request.claim_at, "conflicting-request"))


def test_post_claim_failure_consumes_claim_and_cleans_managed_artifacts(tmp_path):
    values = live_execution(
        tmp_path, failure_step="BOOTSTRAP_REPLAY_SQLITE_DATABASE")
    coordinator, request, host, target, auth, paths, sibling, _, actual, actual_before = values
    with pytest.raises(Exception, match="INJECTED_POST_CLAIM_FAILURE"):
        coordinator.execute(
            request=request, host=host, target=target,
            activation_authorization=auth)
    assert request.permit_path.with_name("permit.json.claim.json").is_file()
    assert sibling.read_text(encoding="utf-8") == "preserve-me"
    assert not any(item.exists() for item in paths.managed_targets)
    assert tree_digest(actual) == actual_before
    failure_path = request.evidence_directory / "failure-evidence.json"
    assert failure_path.is_file()
    assert failure_path.stat().st_mode & 0o777 == 0o600
    raw = failure_path.read_text(encoding="utf-8")
    failure = json.loads(raw)
    assert raw == json.dumps(failure, sort_keys=True, separators=(",", ":"))
    evidence_digest = failure.pop("failure_evidence_digest")
    from core.deployment.operational_bootstrap_execution import canonical_digest as runtime_digest
    assert evidence_digest == runtime_digest(failure)
    claim = json.loads(request.permit_path.with_name(
        "permit.json.claim.json").read_text())
    assert failure["status"] != "COMPLETE"
    assert failure["request_id"] == request.request_id
    claim_digest = runtime_digest(claim)
    claim_id = "m3-a4b2b2a-claim-" + claim_digest[7:39]
    assert failure["permit_id"] == claim["permit_id"]
    assert failure["permit_digest"] == claim["permit_digest"]
    assert failure["claim_id"] == claim_id
    assert failure["claim_digest"] == claim_digest
    assert failure["claim_consumed"] and failure["failed_after_claim"]
    assert failure["cleanup_result"] == "INCOMPLETE_MANAGED_ARTIFACTS_REMOVED"
    assert failure["shared_parent_preserved"]
    assert failure["sibling_preservation_recorded"]
    assert not failure["writers_active"]
    assert not failure["monitoring_active"]
    assert not failure["dispatch_active"]
    assert not failure["production_authorized"]
    with pytest.raises(Exception, match="PERMIT_ALREADY_CLAIMED"):
        coordinator.execute(
            request=request, host=host, target=target,
            activation_authorization=auth)
