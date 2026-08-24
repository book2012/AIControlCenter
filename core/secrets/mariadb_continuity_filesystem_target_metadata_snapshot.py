"""Zero-authority filesystem target metadata snapshot values.

These values record one point-in-time metadata observation.  They are not
authorization, capabilities, stable path bindings, content evidence, or a
security boundary.  Possession and Python object identity grant zero authority.
"""

from dataclasses import dataclass, field
from enum import Enum

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import (
    ConcreteProtectedEvidencePath,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    TrustedOwnershipExpectation,
)


class FilesystemTargetMetadataSnapshotOutcome(Enum):
    DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE = "DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE"
    ABSENT = "ABSENT"
    UNSAFE = "UNSAFE"
    UNAVAILABLE = "UNAVAILABLE"
    UNCERTAIN = "UNCERTAIN"


class FilesystemTargetMetadataSnapshotReason(Enum):
    DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE = "DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE"
    SOURCE_ABSENT = "SOURCE_ABSENT"
    SYMLINK_REJECTED = "SYMLINK_REJECTED"
    WRONG_FILE_TYPE = "WRONG_FILE_TYPE"
    TARGET_MODE_MISMATCH = "TARGET_MODE_MISMATCH"
    TARGET_UID_MISMATCH = "TARGET_UID_MISMATCH"
    TARGET_GID_MISMATCH = "TARGET_GID_MISMATCH"
    METADATA_ACCESS_FAILURE = "METADATA_ACCESS_FAILURE"
    AMBIGUOUS_METADATA_RESULT = "AMBIGUOUS_METADATA_RESULT"


class FilesystemTargetClassification(Enum):
    UNOBSERVED = "UNOBSERVED"
    DIRECTORY = "DIRECTORY"
    SYMLINK = "SYMLINK"
    OTHER = "OTHER"
    AMBIGUOUS = "AMBIGUOUS"


_OUTCOME_BY_REASON = {
    FilesystemTargetMetadataSnapshotReason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE:
        FilesystemTargetMetadataSnapshotOutcome.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE,
    FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT:
        FilesystemTargetMetadataSnapshotOutcome.ABSENT,
    FilesystemTargetMetadataSnapshotReason.SYMLINK_REJECTED:
        FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
    FilesystemTargetMetadataSnapshotReason.WRONG_FILE_TYPE:
        FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
    FilesystemTargetMetadataSnapshotReason.TARGET_MODE_MISMATCH:
        FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
    FilesystemTargetMetadataSnapshotReason.TARGET_UID_MISMATCH:
        FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
    FilesystemTargetMetadataSnapshotReason.TARGET_GID_MISMATCH:
        FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
    FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE:
        FilesystemTargetMetadataSnapshotOutcome.UNAVAILABLE,
    FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT:
        FilesystemTargetMetadataSnapshotOutcome.UNCERTAIN,
}

_CLASSIFICATION_BY_REASON = {
    FilesystemTargetMetadataSnapshotReason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE:
        FilesystemTargetClassification.DIRECTORY,
    FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT:
        FilesystemTargetClassification.UNOBSERVED,
    FilesystemTargetMetadataSnapshotReason.SYMLINK_REJECTED:
        FilesystemTargetClassification.SYMLINK,
    FilesystemTargetMetadataSnapshotReason.WRONG_FILE_TYPE:
        FilesystemTargetClassification.OTHER,
    FilesystemTargetMetadataSnapshotReason.TARGET_MODE_MISMATCH:
        FilesystemTargetClassification.DIRECTORY,
    FilesystemTargetMetadataSnapshotReason.TARGET_UID_MISMATCH:
        FilesystemTargetClassification.DIRECTORY,
    FilesystemTargetMetadataSnapshotReason.TARGET_GID_MISMATCH:
        FilesystemTargetClassification.DIRECTORY,
    FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE:
        FilesystemTargetClassification.UNOBSERVED,
    FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT:
        FilesystemTargetClassification.AMBIGUOUS,
}

_REASONS_WITHOUT_OBSERVED_METADATA = frozenset(
    {
        FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT,
        FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE,
        FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT,
    }
)


@dataclass(frozen=True, slots=True, init=False)
class FilesystemTargetMetadataSnapshotRequest:
    concrete_path: ConcreteProtectedEvidencePath
    ownership_expectation: TrustedOwnershipExpectation

    def __new__(cls):
        raise TypeError(
            "FilesystemTargetMetadataSnapshotRequest is constructed only by the "
            "repository factory"
        )


def create_filesystem_target_metadata_snapshot_request(
    concrete_path: ConcreteProtectedEvidencePath,
    ownership_expectation: TrustedOwnershipExpectation,
) -> FilesystemTargetMetadataSnapshotRequest:
    """Construct a request after exact, non-coercing nested validation."""

    _validate_nested_request_facts(concrete_path, ownership_expectation)
    request = object.__new__(FilesystemTargetMetadataSnapshotRequest)
    object.__setattr__(request, "concrete_path", concrete_path)
    object.__setattr__(request, "ownership_expectation", ownership_expectation)
    return request


def validate_filesystem_target_metadata_snapshot_request(
    request: FilesystemTargetMetadataSnapshotRequest,
) -> None:
    """Fail closed on any malformed request before an adapter performs I/O."""

    if type(request) is not FilesystemTargetMetadataSnapshotRequest:
        raise TypeError("request must be FilesystemTargetMetadataSnapshotRequest")
    try:
        concrete_path = request.concrete_path
        ownership_expectation = request.ownership_expectation
    except (AttributeError, TypeError) as exc:
        raise TypeError("request does not supply its exact nested facts") from exc
    _validate_nested_request_facts(concrete_path, ownership_expectation)


def _validate_nested_request_facts(
    concrete_path: ConcreteProtectedEvidencePath,
    ownership_expectation: TrustedOwnershipExpectation,
) -> None:
    if type(concrete_path) is not ConcreteProtectedEvidencePath:
        raise TypeError("concrete_path must be ConcreteProtectedEvidencePath")
    if type(ownership_expectation) is not TrustedOwnershipExpectation:
        raise TypeError(
            "ownership_expectation must be TrustedOwnershipExpectation"
        )
    try:
        path_value = concrete_path.concrete_path
        expected_uid = ownership_expectation.expected_uid
        expected_gid = ownership_expectation.expected_gid
    except (AttributeError, TypeError) as exc:
        raise TypeError("nested request facts are missing") from exc
    if type(path_value) is not str:
        raise TypeError("concrete_path.concrete_path must be an exact str")
    if type(expected_uid) is not int or expected_uid < 0:
        raise TypeError("expected_uid must be a non-negative exact int")
    if type(expected_gid) is not int or expected_gid < 0:
        raise TypeError("expected_gid must be a non-negative exact int")


@dataclass(frozen=True, slots=True, init=False)
class FilesystemTargetMetadataSnapshot:
    outcome: FilesystemTargetMetadataSnapshotOutcome
    reason: FilesystemTargetMetadataSnapshotReason
    target_classification: FilesystemTargetClassification
    observed_mode: int | None
    observed_uid: int | None
    observed_gid: int | None
    stable_handle_bound: bool = field(default=False, init=False)
    toctou_closed: bool = field(default=False, init=False)
    fd_inode_device_bound: bool = field(default=False, init=False)

    def __new__(cls):
        raise TypeError(
            "FilesystemTargetMetadataSnapshot is constructed only by repository "
            "classification"
        )


def _create_filesystem_target_metadata_snapshot(
    reason: FilesystemTargetMetadataSnapshotReason,
    observed_mode: int | None,
    observed_uid: int | None,
    observed_gid: int | None,
) -> FilesystemTargetMetadataSnapshot:
    if type(reason) is not FilesystemTargetMetadataSnapshotReason:
        raise TypeError("reason must be an exact FilesystemTargetMetadataSnapshotReason")
    observed_values = (observed_mode, observed_uid, observed_gid)
    if reason in _REASONS_WITHOUT_OBSERVED_METADATA:
        if observed_values != (None, None, None):
            raise TypeError("reason requires all observed metadata to be None")
    elif not all(type(value) is int and value >= 0 for value in observed_values):
        raise TypeError("observed metadata must be non-negative exact ints")

    snapshot = object.__new__(FilesystemTargetMetadataSnapshot)
    object.__setattr__(snapshot, "outcome", _OUTCOME_BY_REASON[reason])
    object.__setattr__(snapshot, "reason", reason)
    object.__setattr__(
        snapshot, "target_classification", _CLASSIFICATION_BY_REASON[reason]
    )
    object.__setattr__(snapshot, "observed_mode", observed_mode)
    object.__setattr__(snapshot, "observed_uid", observed_uid)
    object.__setattr__(snapshot, "observed_gid", observed_gid)
    object.__setattr__(snapshot, "stable_handle_bound", False)
    object.__setattr__(snapshot, "toctou_closed", False)
    object.__setattr__(snapshot, "fd_inode_device_bound", False)
    return snapshot
