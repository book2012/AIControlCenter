from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import pytest

from core.deployment.bootstrap_evidence_recovery import (
    BootstrapEvidenceRecoveryConfig,
    BootstrapEvidenceRecoveryError,
    BootstrapEvidenceRecoveryValidator,
)
from core.deployment.contracts import canonical_json_bytes


@pytest.fixture
def source_paths(sqlite_snapshot_workspace):
    return sqlite_snapshot_workspace.source_paths


def _work(source_paths, label: str) -> Path:
    root = source_paths[2] / f"pytest-{label}-{uuid.uuid4().hex}"
    root.mkdir(mode=0o700)
    return root


def _validator(source_paths, label="valid"):
    recovery = _work(source_paths, label)
    return BootstrapEvidenceRecoveryValidator(BootstrapEvidenceRecoveryConfig(
        source_paths[0], source_paths[1], recovery, source_paths[3])), recovery


def _copy_sources(source_paths, label: str):
    root = _work(source_paths, label)
    operational, evidence, recovery = root / "operational", root / "evidence", root / "recovery"
    shutil.copytree(source_paths[0], operational)
    shutil.copytree(source_paths[1], evidence)
    recovery.mkdir(mode=0o700)
    os.chmod(operational, 0o700)
    os.chmod(evidence, 0o700)
    for path in operational.rglob("*"):
        os.chmod(path, 0o700 if path.is_dir() else 0o600)
    for path in evidence.rglob("*"):
        os.chmod(path, 0o600)
    return operational, evidence, recovery


def _rewrite(path: Path, mutate):
    value = json.loads(path.read_bytes())
    mutate(value)
    path.write_bytes(canonical_json_bytes(value))
    os.chmod(path, 0o600)


def test_complete_evidence_chain_and_isolated_recovery(source_paths):
    validator, recovery = _validator(source_paths)
    report = validator.validate()
    assert report["evidence_chain_status"] == "VALID"
    assert report["branch"] == "feature/deployment-package"
    assert report["commit"] == "f7a81b73b86c170300bb6b80f437dbb753362f7e"
    assert report["authorization_id"] == source_paths[3].authorization_id
    assert report["permit_id"] == source_paths[3].permit_id
    assert report["claim_id"] == source_paths[3].claim_id
    assert report["audit_inspection"]["status"] == "HEALTHY"
    assert report["audit_inspection"]["event_count"] == 0
    assert report["replay_inspection"]["status"] == "HEALTHY"
    assert report["replay_inspection"]["event_count"] == 0
    assert report["audit_recovery"]["status"] == "HEALTHY"
    assert report["replay_recovery"]["status"] == "HEALTHY"
    assert report["source_immutability"] is True
    assert all(report[key] is False for key in (
        "writers_active", "monitoring_active", "dispatch_active",
        "ubuntu_participation", "production_authorization"))
    assert all(path.is_relative_to(recovery) for path in recovery.rglob("*"))


def test_report_is_deterministic(source_paths):
    first, _ = _validator(source_paths, "deterministic-a")
    second, _ = _validator(source_paths, "deterministic-b")
    a, b = first.validate(), second.validate()
    # Destination paths are deliberately represented only by stable basenames.
    assert first.canonical_json(a) == second.canonical_json(b)


@pytest.mark.parametrize(("artifact", "mutation", "code"), [
    ("approval-input.json", lambda value: value.update(commit="0" * 40), "GIT_BINDING_MISMATCH"),
    ("live-bootstrap-request.json", lambda value: value["restriction_acknowledgements"].pop(),
     "ACKNOWLEDGEMENT_EVIDENCE_INCOMPLETE"),
    ("activation-authorization.json", lambda value: value.update(authorization_id="tampered"),
     "AUTHORIZATION_DIGEST_INVALID"),
    ("operational-permit.json", lambda value: value.update(maximum_uses=2),
     "PERMIT_DIGEST_INVALID"),
    ("operational-permit.json.claim.json", lambda value: value.update(permit_id="tampered"),
     "CLAIM_BINDING_INVALID"),
    ("bootstrap-receipt.json", lambda value: value.update(status="FAILED"),
     "RECEIPT_FAILED"),
    ("bootstrap-evidence.json", lambda value: value.update(receipt_digest="sha256:" + "0" * 64),
     "BOOTSTRAP_EVIDENCE_INVALID"),
    ("post-bootstrap-validation.json", lambda value: value.update(status="FAILED"),
     "POST_BOOTSTRAP_VALIDATION_INVALID"),
])
def test_tampered_evidence_is_rejected(source_paths, artifact, mutation, code):
    operational, evidence, recovery = _copy_sources(source_paths, artifact)
    _rewrite(evidence / artifact, mutation)
    validator = BootstrapEvidenceRecoveryValidator(
        BootstrapEvidenceRecoveryConfig(operational, evidence, recovery, source_paths[3]))
    with pytest.raises(BootstrapEvidenceRecoveryError, match=code):
        validator.validate()


def test_failure_evidence_and_second_claim_are_rejected(source_paths):
    operational, evidence, recovery = _copy_sources(source_paths, "extra-evidence")
    (evidence / "failure-evidence.json").write_bytes(canonical_json_bytes({"status": "FAILED"}))
    validator = BootstrapEvidenceRecoveryValidator(
        BootstrapEvidenceRecoveryConfig(operational, evidence, recovery, source_paths[3]))
    with pytest.raises(BootstrapEvidenceRecoveryError, match="FAILURE_EVIDENCE_PRESENT"):
        validator.validate()
    (evidence / "failure-evidence.json").unlink()
    shutil.copyfile(evidence / "operational-permit.json.claim.json",
                    evidence / "second.claim.json")
    with pytest.raises(BootstrapEvidenceRecoveryError, match="EVIDENCE_ARTIFACT_SET_INVALID"):
        validator.validate()


@pytest.mark.parametrize(("kind", "code"), [
    ("missing", "UNMANAGED_PATH"),
    ("empty", "BACKUP_DIGEST_MISMATCH"),
    ("truncated", "BACKUP_DIGEST_MISMATCH"),
    ("modified", "BACKUP_DIGEST_MISMATCH"),
    ("checksum", "BACKUP_DIGEST_MISMATCH"),
    ("wrong-service", "REPLAY_INSPECTION_INVALID"),
    ("schema", "UNMANAGED_PATH"),
    ("unsupported-version", "UNMANAGED_PATH"),
])
def test_corrupt_and_cross_service_backups_fail_closed(source_paths, kind, code):
    operational, evidence, recovery = _copy_sources(source_paths, "backup-" + kind)
    audit_backup = operational / "audit/backups/baseline.sqlite3"
    audit_manifest = operational / "audit/backups/baseline.manifest.json"
    validator = BootstrapEvidenceRecoveryValidator(
        BootstrapEvidenceRecoveryConfig(operational, evidence, recovery, source_paths[3]))
    if kind == "missing":
        audit_manifest.unlink()
    elif kind == "empty":
        audit_backup.write_bytes(b"")
    elif kind == "truncated":
        audit_backup.write_bytes(audit_backup.read_bytes()[:128])
    elif kind == "modified":
        data = bytearray(audit_backup.read_bytes())
        data[-1] ^= 1
        audit_backup.write_bytes(data)
    elif kind == "checksum":
        _rewrite(audit_manifest, lambda value: value.update(
            database_byte_digest="sha256:" + "0" * 64))
    elif kind == "wrong-service":
        replay = operational / "security/backups/baseline.sqlite3"
        replay_manifest = operational / "security/backups/baseline.manifest.json"
        shutil.copyfile(audit_backup, replay)
        _rewrite(replay_manifest, lambda value: value.update(
            database_byte_digest=BootstrapEvidenceRecoveryValidator(
                BootstrapEvidenceRecoveryConfig(operational, evidence, recovery, source_paths[3])
            )._restore.__self__ and __import__("hashlib").sha256(replay.read_bytes()).hexdigest()))
        _rewrite(replay_manifest, lambda value: value.update(
            database_byte_digest="sha256:" + value["database_byte_digest"]))
    else:
        import sqlite3
        connection = sqlite3.connect(audit_backup)
        connection.execute("UPDATE audit_ledger_meta SET schema_version=?",
                           ("unsupported" if kind == "unsupported-version" else "mismatch",))
        connection.commit()
        connection.close()
        _rewrite(audit_manifest, lambda value: value.update(
            database_byte_digest="sha256:" + __import__("hashlib").sha256(
                audit_backup.read_bytes()).hexdigest()))
    with pytest.raises((BootstrapEvidenceRecoveryError, FileNotFoundError), match=code):
        validator.validate()


def test_permissions_symlinks_and_unsafe_destinations_rejected(source_paths):
    operational, evidence, recovery = _copy_sources(source_paths, "unsafe")
    database = operational / "audit/audit-ledger.sqlite3"
    os.chmod(database, 0o644)
    validator = BootstrapEvidenceRecoveryValidator(
        BootstrapEvidenceRecoveryConfig(operational, evidence, recovery, source_paths[3]))
    with pytest.raises(BootstrapEvidenceRecoveryError, match="FILE_MODE_INVALID"):
        validator.validate()
    os.chmod(database, 0o600)
    destination = operational / "monitoring/link"
    destination.symlink_to(database)
    with pytest.raises(BootstrapEvidenceRecoveryError, match="UNMANAGED_PATH"):
        validator.validate()
    destination.unlink()
    (recovery / "audit-recovery").mkdir()
    with pytest.raises(BootstrapEvidenceRecoveryError, match="RECOVERY_DESTINATION_EXISTS"):
        validator.validate()


def test_source_metadata_hash_size_and_mtime_are_unchanged(
    source_paths, sqlite_snapshot_workspace,
):
    retained = sqlite_snapshot_workspace.retained
    before = (retained.operational_state, retained.evidence_state)
    validator, _ = _validator(source_paths, "immutability")
    validator.validate()
    retained.assert_unchanged()
    assert before == (
        retained.operational_state,
        retained.evidence_state,
    )
    assert all(
        path.is_relative_to(sqlite_snapshot_workspace.root)
        for path in sqlite_snapshot_workspace.sqlite_sidecars()
    )
