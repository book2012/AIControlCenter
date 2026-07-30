"""Fail-closed validation of bootstrap evidence and isolated baseline recovery."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.deployment.audit_sqlite import (
    SQLiteAuditReadOnlyInspector,
    SQLiteAuditStatus,
    SQLiteAuditStorageConfig,
)
from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.operational_bootstrap_execution.models import (
    RUNTIME_STEP_CODES,
    canonical_digest,
)
from core.deployment.operational_bootstrap_live.models import (
    ControlledRestrictionAcknowledgement,
)
from core.deployment.permit_replay_sqlite import (
    PermitReplayReadOnlyInspector,
    PermitReplayStatus,
    PermitReplayStorageConfig,
)

TASK = "M3-A4B3"
BRANCH = "feature/deployment-package"
COMMIT = "f7a81b73b86c170300bb6b80f437dbb753362f7e"
AUTHORIZATION_ID = "m3-a4b2b2b-r2-60cc9ee1f8cf6c9a55a97cea3224786d"
PERMIT_ID = "m3-a4b2b2b-r4-permit-a72d2e43cc42cf05150884e95919d4b7"
CLAIM_ID = "m3-a4b2b2a-claim-ef74c0c861feb6868e45999396e6f6db"
INSPECTED_AT = "2026-07-30T14:11:03.162569+00:00"


class BootstrapEvidenceRecoveryError(RuntimeError):
    """A stable fail-closed validation failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class BootstrapEvidenceRecoveryConfig:
    operational_snapshot: Path
    evidence_snapshot: Path
    recovery_work: Path
    expected_uid: int = os.getuid()
    branch: str = BRANCH
    commit: str = COMMIT

    def __post_init__(self) -> None:
        for name in ("operational_snapshot", "evidence_snapshot", "recovery_work"):
            path = Path(getattr(self, name))
            if not path.is_absolute() or ".." in path.parts:
                raise BootstrapEvidenceRecoveryError("ABSOLUTE_PATH_REQUIRED")
            object.__setattr__(self, name, path)
        if self.branch != BRANCH or self.commit != COMMIT:
            raise BootstrapEvidenceRecoveryError("GIT_BINDING_MISMATCH")
        if self.recovery_work.is_symlink() or not self.recovery_work.is_dir():
            raise BootstrapEvidenceRecoveryError("RECOVERY_ROOT_UNAVAILABLE")
        for source in (self.operational_snapshot, self.evidence_snapshot):
            if source.is_symlink() or not source.is_dir():
                raise BootstrapEvidenceRecoveryError("SOURCE_SNAPSHOT_UNAVAILABLE")
            try:
                source.relative_to(self.recovery_work)
            except ValueError:
                pass
            else:
                raise BootstrapEvidenceRecoveryError("SOURCE_RECOVERY_OVERLAP")


class _ConfinedReadOnlyPolicy:
    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def identity_digest(path: Path) -> str:
        return "sha256:" + hashlib.sha256(os.fsencode(path)).hexdigest()

    def validate(self, path: Path) -> tuple[str, ...]:
        path = Path(path)
        if not path.is_absolute() or ".." in path.parts:
            return ("UNSAFE_PATH",)
        try:
            path.relative_to(self.root)
        except ValueError:
            return ("PATH_OUTSIDE_VALIDATION_ROOT",)
        current = Path(path.anchor)
        for component in path.parts[1:]:
            current /= component
            if current.is_symlink():
                return ("SYMLINK_PATH_COMPONENT",)
        return ()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _snapshot(root: Path) -> dict[str, tuple[int, int, int, str]]:
    result: dict[str, tuple[int, int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        relative = str(path.relative_to(root))
        digest = _file_digest(path) if stat.S_ISREG(info.st_mode) else ""
        result[relative] = (info.st_mode, info.st_size, info.st_mtime_ns, digest)
    return result


def _read_canonical(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise BootstrapEvidenceRecoveryError("ARTIFACT_UNAVAILABLE")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BootstrapEvidenceRecoveryError("ARTIFACT_JSON_INVALID") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise BootstrapEvidenceRecoveryError("STRICT_CANONICAL_JSON_REQUIRED")
    return value


def _time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise BootstrapEvidenceRecoveryError("TIMESTAMP_INVALID") from exc
    if result.tzinfo is None:
        raise BootstrapEvidenceRecoveryError("TIMESTAMP_TIMEZONE_REQUIRED")
    return result


class BootstrapEvidenceRecoveryValidator:
    """No issuance, claim, runner, writer, activation, dispatch, or remote ports."""

    _ARTIFACTS = (
        "approval-input.json",
        "shared-parent-preflight.json",
        "live-bootstrap-request.json",
        "activation-authorization-request.json",
        "activation-authorization-evidence.json",
        "activation-authorization.json",
        "operational-permit.json",
        "permit-issuance-evidence.json",
        "operational-permit.json.claim.json",
        "bootstrap-receipt.json",
        "bootstrap-evidence.json",
        "post-bootstrap-validation.json",
    )
    _MANAGED_DIRS = ("audit", "audit/backups", "security", "security/backups", "monitoring")
    _MANAGED_FILES = {
        "audit/audit-ledger.sqlite3", "audit/audit-ledger.sqlite3-shm",
        "audit/audit-ledger.sqlite3-wal", "audit/backups/baseline.manifest.json",
        "audit/backups/baseline.sqlite3", "audit/backups/baseline.sqlite3-shm",
        "audit/backups/baseline.sqlite3-wal", "security/permit-replay.sqlite3",
        "security/permit-replay.sqlite3-shm", "security/permit-replay.sqlite3-wal",
        "security/backups/baseline.manifest.json", "security/backups/baseline.sqlite3",
        "security/backups/baseline.sqlite3-shm", "security/backups/baseline.sqlite3-wal",
    }

    def __init__(self, config: BootstrapEvidenceRecoveryConfig) -> None:
        self.config = config

    def _evidence(self) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        root = self.config.evidence_snapshot
        if (root / "failure-evidence.json").exists():
            raise BootstrapEvidenceRecoveryError("FAILURE_EVIDENCE_PRESENT")
        allowed = set(self._ARTIFACTS) | {
            "source-human-attestation.json", "source-shared-parent-observation.json"}
        present = {path.name for path in root.iterdir() if path.is_file()}
        if present != allowed:
            raise BootstrapEvidenceRecoveryError("EVIDENCE_ARTIFACT_SET_INVALID")
        if len(tuple(root.glob("*.claim.json"))) != 1:
            raise BootstrapEvidenceRecoveryError("EXACTLY_ONE_CLAIM_REQUIRED")
        values = {name: _read_canonical(root / name) for name in self._ARTIFACTS}
        digests = {name: sha256_digest(value) for name, value in values.items()}
        approval, preflight = values["approval-input.json"], values["shared-parent-preflight.json"]
        request, auth_request = values["live-bootstrap-request.json"], values["activation-authorization-request.json"]
        authorization = values["activation-authorization.json"]
        authorization_evidence = values["activation-authorization-evidence.json"]
        permit, issuance = values["operational-permit.json"], values["permit-issuance-evidence.json"]
        claim, receipt = values["operational-permit.json.claim.json"], values["bootstrap-receipt.json"]
        bundle, post = values["bootstrap-evidence.json"], values["post-bootstrap-validation.json"]
        for item in (approval, preflight, request, permit, claim, receipt):
            if item.get("branch") != self.config.branch or item.get("commit") != self.config.commit:
                raise BootstrapEvidenceRecoveryError("GIT_BINDING_MISMATCH")
        if approval.get("status") != "APPROVED":
            raise BootstrapEvidenceRecoveryError("APPROVAL_INVALID")
        if (approval.get("requester_identity"), approval.get("operator_identity"),
                approval.get("independent_approver_identity")) != (
                "mac-account:kyouhan", "mac-account:kyouhan", "brightbok"):
            raise BootstrapEvidenceRecoveryError("IDENTITY_BINDING_INVALID")
        if preflight.get("status") != "READY_WITH_RESTRICTIONS" or preflight.get("ubuntu_participation") is not False:
            raise BootstrapEvidenceRecoveryError("PREFLIGHT_INVALID")
        if request.get("maximum_uses") != 1 or request.get("trusted_operational_root") != preflight.get("trusted_operational_root"):
            raise BootstrapEvidenceRecoveryError("REQUEST_BINDING_INVALID")
        acknowledgements = request.get("restriction_acknowledgements")
        if not isinstance(acknowledgements, list) or len(acknowledgements) != 24:
            raise BootstrapEvidenceRecoveryError("ACKNOWLEDGEMENT_EVIDENCE_INCOMPLETE")
        acknowledgement_digests = tuple(sorted(item["acknowledgement_digest"] for item in acknowledgements))
        if acknowledgement_digests != tuple(sorted(request["restriction_acknowledgement_digests"])):
            raise BootstrapEvidenceRecoveryError("ACKNOWLEDGEMENT_DIGEST_MISMATCH")
        warning = tuple(sorted(item["acknowledgement_digest"] for item in acknowledgements
                               if item["restriction_identifier"] == "warnings-427"))
        if tuple(permit.get("warning_acknowledgements", ())) != warning or len(warning) != 2:
            raise BootstrapEvidenceRecoveryError("WARNING_PAIR_INVALID")
        typed_acknowledgements = tuple(
            ControlledRestrictionAcknowledgement(**item) for item in acknowledgements)
        expected_full = canonical_digest(
            [item.as_dict() for item in sorted(typed_acknowledgements)])
        if permit.get("full_restriction_acknowledgement_digest") != expected_full:
            raise BootstrapEvidenceRecoveryError("FULL_RESTRICTION_BINDING_INVALID")
        auth_content = dict(authorization)
        auth_digest = auth_content.pop("authorization_digest", None)
        if auth_digest != canonical_digest(auth_content) or authorization.get("authorization_id") != AUTHORIZATION_ID:
            raise BootstrapEvidenceRecoveryError("AUTHORIZATION_DIGEST_INVALID")
        if authorization.get("request") != auth_request:
            raise BootstrapEvidenceRecoveryError("AUTHORIZATION_REQUEST_BINDING_INVALID")
        if authorization_evidence != {
            "decision_id": authorization_evidence.get("decision_id"),
            "request_digest": canonical_digest(auth_request),
            "status": "AUTHORIZED",
        }:
            raise BootstrapEvidenceRecoveryError("AUTHORIZATION_EVIDENCE_INVALID")
        permit_content = dict(permit)
        permit_digest = permit_content.pop("permit_digest", None)
        if permit_digest != canonical_digest(permit_content) or permit.get("permit_id") != PERMIT_ID:
            raise BootstrapEvidenceRecoveryError("PERMIT_DIGEST_INVALID")
        if issuance != {"permit_digest": permit_digest, "permit_id": PERMIT_ID}:
            raise BootstrapEvidenceRecoveryError("PERMIT_ISSUANCE_BINDING_INVALID")
        if claim.get("permit_id") != PERMIT_ID or claim.get("permit_digest") != permit_digest:
            raise BootstrapEvidenceRecoveryError("CLAIM_BINDING_INVALID")
        claim_digest = canonical_digest(claim)
        if CLAIM_ID != "m3-a4b2b2a-claim-" + claim_digest[7:39]:
            raise BootstrapEvidenceRecoveryError("CLAIM_DIGEST_INVALID")
        if receipt.get("permit_id") != PERMIT_ID or receipt.get("claim_id") != CLAIM_ID:
            raise BootstrapEvidenceRecoveryError("RECEIPT_BINDING_INVALID")
        if receipt.get("status") != "COMPLETE" or receipt.get("findings") != []:
            raise BootstrapEvidenceRecoveryError("RECEIPT_FAILED")
        steps = receipt.get("step_receipts")
        if not isinstance(steps, list) or tuple(item.get("code") for item in steps) != RUNTIME_STEP_CODES:
            raise BootstrapEvidenceRecoveryError("RECEIPT_STEPS_INVALID")
        if any(item.get("sequence") != index or item.get("complete") is not True
               for index, item in enumerate(steps, 1)):
            raise BootstrapEvidenceRecoveryError("RECEIPT_STEPS_INVALID")
        receipt_digest = canonical_digest(receipt)
        bundle_content = {
            "receipt_digest": receipt_digest,
            "claim_digest": claim_digest,
            "plan_digest": bundle.get("plan_digest"),
        }
        supplied_evidence_digest = bundle.get("evidence_digest")
        if (bundle.get("claim_digest") != claim_digest or bundle.get("receipt_digest") != receipt_digest
                or supplied_evidence_digest != canonical_digest(bundle_content)
                or bundle.get("bundle_id") != "m3-a4b2b2a-evidence-" + supplied_evidence_digest[7:39]):
            raise BootstrapEvidenceRecoveryError("BOOTSTRAP_EVIDENCE_INVALID")
        if (post.get("status") != "COMPLETE" or post.get("findings") != []
                or not all(item.get("passed") is True for item in post.get("checks", ()))):
            raise BootstrapEvidenceRecoveryError("POST_BOOTSTRAP_VALIDATION_INVALID")
        if (post.get("activation_authorization_id"), post.get("permit_id"), post.get("claim_id")) != (
                AUTHORIZATION_ID, PERMIT_ID, CLAIM_ID):
            raise BootstrapEvidenceRecoveryError("CROSS_BINDING_INVALID")
        issued, claimed, completed = map(_time, (
            permit["issued_at"], claim["claimed_at"], receipt["completed_at"]))
        not_before, deadline, expires = map(_time, (
            permit["not_before"], permit["bootstrap_execution_deadline"], permit["expires_at"]))
        if not (not_before <= issued <= claimed <= completed < deadline <= expires):
            raise BootstrapEvidenceRecoveryError("WINDOW_BINDING_INVALID")
        false_fields = (
            approval["production_authorized"], request["production_authorized"],
            request["writers_authorized"], request["monitoring_authorized"],
            request["external_dispatch_authorized"], permit["production_authorized"],
            permit["writers_authorized"], permit["monitoring_authorized"],
            permit["external_dispatch_authorized"], receipt["production_authorized"],
            receipt["writers_activated"], receipt["monitoring_activated"],
            receipt["external_dispatch_activated"], post["production_authorized"],
        )
        if any(value is not False for value in false_fields):
            raise BootstrapEvidenceRecoveryError("ACTIVATION_STATE_INVALID")
        return values, digests

    def _filesystem(self) -> None:
        root = self.config.operational_snapshot
        actual = {str(path.relative_to(root)) for path in root.rglob("*")}
        if actual != set(self._MANAGED_DIRS) | self._MANAGED_FILES:
            raise BootstrapEvidenceRecoveryError("UNMANAGED_PATH")
        for relative in self._MANAGED_DIRS:
            path, info = root / relative, (root / relative).lstat()
            if path.is_symlink() or not path.is_dir() or info.st_uid != self.config.expected_uid:
                raise BootstrapEvidenceRecoveryError("MANAGED_DIRECTORY_INVALID")
            if stat.S_IMODE(info.st_mode) not in (0o700, 0o500):
                raise BootstrapEvidenceRecoveryError("DIRECTORY_MODE_INVALID")
        for relative in self._MANAGED_FILES:
            path, info = root / relative, (root / relative).lstat()
            if path.is_symlink() or not path.is_file() or info.st_uid != self.config.expected_uid:
                raise BootstrapEvidenceRecoveryError("MANAGED_FILE_INVALID")
            if stat.S_IMODE(info.st_mode) not in (0o600, 0o400):
                raise BootstrapEvidenceRecoveryError("FILE_MODE_INVALID")

    def _inspect(self, path: Path, service: str, root: Path) -> dict[str, Any]:
        before = (path.stat().st_size, path.stat().st_mtime_ns, _file_digest(path))
        policy = _ConfinedReadOnlyPolicy(root)
        if service == "audit":
            report = SQLiteAuditReadOnlyInspector(
                config=SQLiteAuditStorageConfig(path), path_policy=policy
            ).inspect(inspected_at=INSPECTED_AT)
            healthy = report.status is SQLiteAuditStatus.HEALTHY
        else:
            report = PermitReplayReadOnlyInspector(
                config=PermitReplayStorageConfig(path), path_policy=policy
            ).inspect(inspected_at=INSPECTED_AT)
            healthy = report.status is PermitReplayStatus.HEALTHY
        after = (path.stat().st_size, path.stat().st_mtime_ns, _file_digest(path))
        if not healthy or report.event_count != 0 or report.writes_performed != 0 or before != after:
            raise BootstrapEvidenceRecoveryError(f"{service.upper()}_INSPECTION_INVALID")
        return {
            "status": report.status.value,
            "event_count": report.event_count,
            "schema_version": report.schema_version,
            "query_only": report.query_only,
            "source_unchanged": True,
        }

    def _restore(self, service: str, source: Path, manifest_path: Path) -> dict[str, Any]:
        if source.is_symlink() or manifest_path.is_symlink():
            raise BootstrapEvidenceRecoveryError("SYMLINK_SOURCE")
        manifest = _read_canonical(manifest_path)
        if manifest.get("production_authorized") is not False:
            raise BootstrapEvidenceRecoveryError("PRODUCTION_AUTHORIZATION_INVALID")
        if manifest.get("database_byte_digest") != _file_digest(source):
            raise BootstrapEvidenceRecoveryError("BACKUP_DIGEST_MISMATCH")
        root = self.config.recovery_work / f"{service}-recovery"
        if root.exists() or root.is_symlink():
            raise BootstrapEvidenceRecoveryError("RECOVERY_DESTINATION_EXISTS")
        root.mkdir(mode=0o700)
        destination = root / f"{service}-restored.sqlite3"
        try:
            source.relative_to(self.config.recovery_work)
        except ValueError:
            pass
        else:
            raise BootstrapEvidenceRecoveryError("BACKUP_SOURCE_POLICY_INVALID")
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, 0o600)
        result = self._inspect(destination, service, root)
        evidence = {
            "backup_digest": manifest["database_byte_digest"],
            "destination": destination.name,
            "event_count": result["event_count"],
            "production_authorized": False,
            "schema_version": result["schema_version"],
            "service": service,
            "status": "RESTORE_VALIDATED",
        }
        return {**result, "recovery_evidence_digest": sha256_digest(evidence)}

    def validate(self) -> dict[str, Any]:
        before = {
            "operational": _snapshot(self.config.operational_snapshot),
            "evidence": _snapshot(self.config.evidence_snapshot),
        }
        values, artifact_digests = self._evidence()
        self._filesystem()
        operational = self.config.operational_snapshot
        audit = self._inspect(operational / "audit/audit-ledger.sqlite3", "audit", operational)
        replay = self._inspect(operational / "security/permit-replay.sqlite3", "replay", operational)
        audit_recovery = self._restore(
            "audit", operational / "audit/backups/baseline.sqlite3",
            operational / "audit/backups/baseline.manifest.json")
        replay_recovery = self._restore(
            "replay", operational / "security/backups/baseline.sqlite3",
            operational / "security/backups/baseline.manifest.json")
        unchanged = before == {
            "operational": _snapshot(self.config.operational_snapshot),
            "evidence": _snapshot(self.config.evidence_snapshot),
        }
        if not unchanged:
            raise BootstrapEvidenceRecoveryError("SOURCE_SNAPSHOT_CHANGED")
        root = values["live-bootstrap-request.json"]["trusted_operational_root"]
        content = {
            "artifact_digests": artifact_digests,
            "audit_inspection": audit,
            "audit_recovery": audit_recovery,
            "authorization_id": AUTHORIZATION_ID,
            "blockers": [],
            "branch": self.config.branch,
            "claim_id": CLAIM_ID,
            "commit": self.config.commit,
            "dispatch_active": False,
            "evidence_chain_status": "VALID",
            "monitoring_active": False,
            "operational_root_binding": sha256_digest(root),
            "permit_id": PERMIT_ID,
            "production_authorization": False,
            "readiness_decision": "READY_FOR_CONTROLLED_ACTIVATION_VALIDATION",
            "replay_inspection": replay,
            "replay_recovery": replay_recovery,
            "risks": [],
            "source_immutability": unchanged,
            "task": TASK,
            "ubuntu_participation": False,
            "writers_active": False,
        }
        return {**content, "report_digest": sha256_digest(content)}

    @staticmethod
    def canonical_json(report: dict[str, Any]) -> str:
        return canonical_json_bytes(report).decode("utf-8")
