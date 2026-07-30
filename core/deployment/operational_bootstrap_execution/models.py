"""Immutable contracts for authorized Mac bootstrap execution."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class OperationalBootstrapExecutionError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class OperationalBootstrapExecutionStage(StrEnum):
    AUTHORIZED_MAC_BOOTSTRAP_EXECUTION = "AUTHORIZED_MAC_BOOTSTRAP_EXECUTION"


class OperationalBootstrapRuntimeMode(StrEnum):
    TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION = "TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION"
    CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP = "CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP"


class OperationalBootstrapRuntimeStatus(StrEnum):
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


RUNTIME_STEP_CODES = (
    "VALIDATE_RUNTIME_CONFIGURATION", "VALIDATE_EXACT_BRANCH_AND_COMMIT",
    "VALIDATE_GIT_CLEAN_AND_UPSTREAM_PARITY", "VALIDATE_MAC_HOST_AND_NON_ROOT_OPERATOR",
    "VALIDATE_LIVE_PERMIT_AND_ISSUANCE_EVIDENCE", "VALIDATE_PERMIT_WINDOW_AND_SCOPE",
    "REVALIDATE_OPERATIONAL_TARGET_ABSENCE", "REVALIDATE_FILESYSTEM_AND_CAPACITY",
    "ATOMICALLY_CLAIM_PERMIT", "REVALIDATE_TARGET_ABSENCE_AFTER_CLAIM",
    "CREATE_MAC_OPERATIONAL_DIRECTORY_LAYOUT", "APPLY_AND_VERIFY_RESTRICTIVE_PERMISSIONS",
    "BOOTSTRAP_AUDIT_SQLITE_DATABASE", "READ_ONLY_INSPECT_AUDIT_DATABASE",
    "BOOTSTRAP_REPLAY_SQLITE_DATABASE", "READ_ONLY_INSPECT_REPLAY_DATABASE",
    "CREATE_AND_VALIDATE_BASELINE_AUDIT_BACKUP",
    "CREATE_AND_VALIDATE_BASELINE_REPLAY_BACKUP",
    "CREATE_NON_PERSISTED_PRE_ACTIVATION_MONITORING_SNAPSHOT",
    "VERIFY_WRITERS_REMAIN_DISABLED", "VERIFY_MONITORING_REMAINS_INACTIVE",
    "VERIFY_EXTERNAL_DISPATCH_REMAINS_INACTIVE", "GENERATE_RUNTIME_RECEIPT_AND_EVIDENCE",
)

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|https?://", re.I)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _FORBIDDEN.search(str(key)):
                raise OperationalBootstrapExecutionError("UNSAFE_FIELD_REJECTED")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, str) and _FORBIDDEN.search(value):
        raise OperationalBootstrapExecutionError("UNSAFE_VALUE_REJECTED")
    elif not isinstance(value, (str, int, bool, type(None), StrEnum, Path)):
        raise OperationalBootstrapExecutionError("UNSUPPORTED_VALUE_REJECTED")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapExecutionConfig:
    mode: OperationalBootstrapRuntimeMode
    repository_root: Path
    approved_branch: str = "feature/deployment-package"
    minimum_free_bytes: int = 16 * 1024 * 1024
    production_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository_root", Path(self.repository_root).resolve())
        if not isinstance(self.mode, OperationalBootstrapRuntimeMode):
            raise OperationalBootstrapExecutionError("RUNTIME_MODE_REJECTED")
        if self.approved_branch != "feature/deployment-package" or self.production_authorized:
            raise OperationalBootstrapExecutionError("RUNTIME_CONFIGURATION_REJECTED")
        if self.minimum_free_bytes < 1:
            raise OperationalBootstrapExecutionError("CAPACITY_POLICY_INVALID")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeRequest:
    request_id: str
    mode: OperationalBootstrapRuntimeMode
    branch: str
    commit: str
    operator_identity: str
    requested_at: str
    claim_at: str
    permit_path: Path
    issuance_evidence_path: Path
    evidence_directory: Path
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.request_id or not _COMMIT.fullmatch(self.commit):
            raise OperationalBootstrapExecutionError("REQUEST_BINDING_INVALID")
        if not self.operator_identity or self.operator_identity in {"root", "operator", "unknown"}:
            raise OperationalBootstrapExecutionError("OPERATOR_IDENTITY_INVALID")
        for name in ("permit_path", "issuance_evidence_path", "evidence_directory"):
            value = Path(getattr(self, name))
            if not value.is_absolute() or ".." in value.parts:
                raise OperationalBootstrapExecutionError("ABSOLUTE_PATH_REQUIRED")
            object.__setattr__(self, name, value)
        validate_safe(self.metadata)
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapLivePermitEvidence:
    permit: Mapping[str, Any]
    canonical_payload: str
    permit_digest: str

    def __post_init__(self) -> None:
        validate_safe(self.permit)
        if not _DIGEST.fullmatch(self.permit_digest):
            raise OperationalBootstrapExecutionError("PERMIT_DIGEST_INVALID")
        object.__setattr__(self, "permit", dict(sorted(self.permit.items())))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapIssuanceEvidence:
    evidence: Mapping[str, Any]
    canonical_payload: str

    def __post_init__(self) -> None:
        validate_safe(self.evidence)
        object.__setattr__(self, "evidence", dict(sorted(self.evidence.items())))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapHostRevalidationEvidence:
    system: str
    uid: int
    trusted_home: Path
    repository_root: Path
    git_clean: bool
    upstream_ahead: int
    upstream_behind: int
    available_bytes: int


@dataclass(frozen=True, slots=True)
class OperationalBootstrapTargetRevalidationEvidence:
    operational_root: Path
    targets_absent: bool
    symlink_free: bool
    local_fixed_volume: bool
    matching_prior_receipt: bool = False


@dataclass(frozen=True, slots=True)
class OperationalBootstrapSharedParentEvidence:
    application_state_parent_preexisting: bool
    application_state_parent_owned_by_bootstrap: bool
    application_state_parent_mode: int | None
    application_state_parent_owner_uid: int | None
    application_state_parent_symlink: bool
    application_state_parent_group_world_write: bool
    existing_unmanaged_sibling_count: int
    existing_unmanaged_sibling_identity_digests: tuple[str, ...]
    managed_targets_absent: bool
    shared_parent_restrictions: tuple[str, ...]
    existing_parent_modified: bool = False


@dataclass(frozen=True, slots=True)
class OperationalBootstrapClaimRequest:
    permit_id: str
    permit_digest: str
    branch: str
    commit: str
    operator_identity: str
    claimed_at: str
    execution_request_id: str

    def __post_init__(self) -> None:
        if not self.permit_id or not _DIGEST.fullmatch(self.permit_digest):
            raise OperationalBootstrapExecutionError("CLAIM_BINDING_INVALID")
        if not _COMMIT.fullmatch(self.commit):
            raise OperationalBootstrapExecutionError("CLAIM_GIT_BINDING_INVALID")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapClaimReceipt:
    claim_id: str
    claim_path: Path
    claim_digest: str
    request: OperationalBootstrapClaimRequest


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeStep:
    sequence: int
    code: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimePlan:
    steps: tuple[OperationalBootstrapRuntimeStep, ...]
    plan_digest: str

    @classmethod
    def build(cls) -> "OperationalBootstrapRuntimePlan":
        steps = tuple(OperationalBootstrapRuntimeStep(i, code)
                      for i, code in enumerate(RUNTIME_STEP_CODES, 1))
        return cls(steps, canonical_digest([asdict(step) for step in steps]))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeStepReceipt:
    sequence: int
    code: str
    complete: bool
    evidence_digest: str


@dataclass(frozen=True, slots=True, order=True)
class OperationalBootstrapRuntimeFinding:
    code: str
    severity: str = "ERROR"


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeReceipt:
    receipt_id: str
    request_id: str
    permit_id: str
    claim_id: str
    mode: OperationalBootstrapRuntimeMode
    status: OperationalBootstrapRuntimeStatus
    branch: str
    commit: str
    completed_at: str
    step_receipts: tuple[OperationalBootstrapRuntimeStepReceipt, ...]
    findings: tuple[OperationalBootstrapRuntimeFinding, ...]
    artifact_references: tuple[str, ...]
    writers_activated: bool = False
    monitoring_activated: bool = False
    external_dispatch_activated: bool = False
    production_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeEvidenceBundle:
    bundle_id: str
    receipt: OperationalBootstrapRuntimeReceipt
    receipt_digest: str
    claim_digest: str
    plan_digest: str
    evidence_digest: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRuntimeValidationReport:
    report_id: str
    status: OperationalBootstrapRuntimeStatus
    findings: tuple[OperationalBootstrapRuntimeFinding, ...]
    report_digest: str
