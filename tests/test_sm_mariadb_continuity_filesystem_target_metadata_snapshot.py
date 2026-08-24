from dataclasses import FrozenInstanceError, fields
import inspect

import pytest

from core.secrets import (
    mariadb_continuity_filesystem_target_metadata_snapshot as module,
)
from core.secrets.mariadb_continuity_concrete_protected_evidence_path import (
    ConcreteProtectedEvidencePath,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    TrustedOwnershipExpectation,
)


def nested_values(path="/exact/../unchanged", uid=501, gid=20):
    concrete = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(concrete, "concrete_path", path)
    ownership = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(ownership, "expected_uid", uid)
    object.__setattr__(ownership, "expected_gid", gid)
    return concrete, ownership


def request(path="/exact/../unchanged", uid=501, gid=20):
    return module.create_filesystem_target_metadata_snapshot_request(
        *nested_values(path, uid, gid)
    )


def test_exact_request_shape_direct_construction_and_immutability():
    value = request()
    assert tuple(item.name for item in fields(value)) == (
        "concrete_path", "ownership_expectation"
    )
    assert module.FilesystemTargetMetadataSnapshotRequest.__slots__ == (
        "concrete_path", "ownership_expectation"
    )
    assert not hasattr(value, "__dict__")
    with pytest.raises(FrozenInstanceError):
        value.concrete_path = object()
    with pytest.raises(TypeError):
        module.FilesystemTargetMetadataSnapshotRequest()


class IntSubclass(int):
    pass


@pytest.mark.parametrize("uid,gid", [(True, 20), (501, False), (IntSubclass(501), 20), (501, IntSubclass(20)), (-1, 20), (501, -1)])
def test_factory_rejects_malformed_expected_ids_without_coercion(uid, gid):
    with pytest.raises(TypeError):
        request(uid=uid, gid=gid)


def test_factory_rejects_malformed_nested_types_and_path():
    concrete, ownership = nested_values()
    with pytest.raises(TypeError):
        module.create_filesystem_target_metadata_snapshot_request(object(), ownership)
    with pytest.raises(TypeError):
        module.create_filesystem_target_metadata_snapshot_request(concrete, object())
    malformed, ownership = nested_values(path=object())
    with pytest.raises(TypeError):
        module.create_filesystem_target_metadata_snapshot_request(malformed, ownership)


def test_exact_enum_vocabularies_have_no_safe_bound_claim():
    assert tuple(item.name for item in module.FilesystemTargetMetadataSnapshotOutcome) == (
        "DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE", "ABSENT", "UNSAFE", "UNAVAILABLE", "UNCERTAIN"
    )
    assert tuple(item.name for item in module.FilesystemTargetMetadataSnapshotReason) == (
        "DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE", "SOURCE_ABSENT", "SYMLINK_REJECTED",
        "WRONG_FILE_TYPE", "TARGET_MODE_MISMATCH", "TARGET_UID_MISMATCH",
        "TARGET_GID_MISMATCH", "METADATA_ACCESS_FAILURE", "AMBIGUOUS_METADATA_RESULT"
    )
    assert tuple(item.name for item in module.FilesystemTargetClassification) == (
        "UNOBSERVED", "DIRECTORY", "SYMLINK", "OTHER", "AMBIGUOUS"
    )
    vocabulary = {item.name for enum in (
        module.FilesystemTargetMetadataSnapshotOutcome,
        module.FilesystemTargetMetadataSnapshotReason,
        module.FilesystemTargetClassification,
    ) for item in enum}
    assert "SAFE_BOUND" not in vocabulary
    assert "METADATA_SAFE_AND_STABLY_BOUND" not in vocabulary


def test_exact_snapshot_shape_is_private_frozen_slotted_and_zero_authority():
    value = module._create_filesystem_target_metadata_snapshot(
        module.FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT,
        None, None, None,
    )
    assert tuple(item.name for item in fields(value)) == (
        "outcome", "reason", "target_classification", "observed_mode",
        "observed_uid", "observed_gid", "stable_handle_bound", "toctou_closed",
        "fd_inode_device_bound",
    )
    assert not hasattr(value, "__dict__")
    assert (value.stable_handle_bound, value.toctou_closed, value.fd_inode_device_bound) == (False, False, False)
    assert not hasattr(value, "expected_uid")
    assert not hasattr(value, "expected_gid")
    with pytest.raises(FrozenInstanceError):
        value.outcome = None
    with pytest.raises(TypeError):
        module.FilesystemTargetMetadataSnapshot()


@pytest.mark.parametrize("reason,outcome,classification", [
    (module.FilesystemTargetMetadataSnapshotReason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE, module.FilesystemTargetMetadataSnapshotOutcome.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE, module.FilesystemTargetClassification.DIRECTORY),
    (module.FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT, module.FilesystemTargetMetadataSnapshotOutcome.ABSENT, module.FilesystemTargetClassification.UNOBSERVED),
    (module.FilesystemTargetMetadataSnapshotReason.SYMLINK_REJECTED, module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE, module.FilesystemTargetClassification.SYMLINK),
    (module.FilesystemTargetMetadataSnapshotReason.WRONG_FILE_TYPE, module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE, module.FilesystemTargetClassification.OTHER),
    (module.FilesystemTargetMetadataSnapshotReason.TARGET_MODE_MISMATCH, module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE, module.FilesystemTargetClassification.DIRECTORY),
    (module.FilesystemTargetMetadataSnapshotReason.TARGET_UID_MISMATCH, module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE, module.FilesystemTargetClassification.DIRECTORY),
    (module.FilesystemTargetMetadataSnapshotReason.TARGET_GID_MISMATCH, module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE, module.FilesystemTargetClassification.DIRECTORY),
    (module.FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE, module.FilesystemTargetMetadataSnapshotOutcome.UNAVAILABLE, module.FilesystemTargetClassification.UNOBSERVED),
    (module.FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT, module.FilesystemTargetMetadataSnapshotOutcome.UNCERTAIN, module.FilesystemTargetClassification.AMBIGUOUS),
])
def test_all_canonical_reason_mappings(reason, outcome, classification):
    observed = (None, None, None) if reason in {
        module.FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT,
        module.FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE,
        module.FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT,
    } else (0, 0, 0)
    value = module._create_filesystem_target_metadata_snapshot(reason, *observed)
    assert value.outcome is outcome
    assert value.target_classification is classification


def test_classifier_does_not_accept_caller_outcome_or_classification():
    parameters = inspect.signature(
        module._create_filesystem_target_metadata_snapshot
    ).parameters
    assert "outcome" not in parameters
    assert "target_classification" not in parameters
    with pytest.raises(TypeError):
        module._create_filesystem_target_metadata_snapshot(
            reason=module.FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT,
            observed_mode=None,
            observed_uid=None,
            observed_gid=None,
            outcome=module.FilesystemTargetMetadataSnapshotOutcome.UNSAFE,
        )


@pytest.mark.parametrize("reason", [
    module.FilesystemTargetMetadataSnapshotReason.SOURCE_ABSENT,
    module.FilesystemTargetMetadataSnapshotReason.METADATA_ACCESS_FAILURE,
    module.FilesystemTargetMetadataSnapshotReason.AMBIGUOUS_METADATA_RESULT,
])
def test_unobserved_reasons_require_all_metadata_none(reason):
    value = module._create_filesystem_target_metadata_snapshot(reason, None, None, None)
    assert (value.observed_mode, value.observed_uid, value.observed_gid) == (None, None, None)
    with pytest.raises(TypeError):
        module._create_filesystem_target_metadata_snapshot(reason, 0, None, None)


@pytest.mark.parametrize("reason", [
    module.FilesystemTargetMetadataSnapshotReason.SYMLINK_REJECTED,
    module.FilesystemTargetMetadataSnapshotReason.WRONG_FILE_TYPE,
    module.FilesystemTargetMetadataSnapshotReason.TARGET_MODE_MISMATCH,
    module.FilesystemTargetMetadataSnapshotReason.TARGET_UID_MISMATCH,
    module.FilesystemTargetMetadataSnapshotReason.TARGET_GID_MISMATCH,
    module.FilesystemTargetMetadataSnapshotReason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE,
])
@pytest.mark.parametrize("observed", [
    (True, 0, 0), (IntSubclass(0), 0, 0), (-1, 0, 0), ("0", 0, 0),
    (0, False, 0), (0, IntSubclass(0), 0), (0, -1, 0), (0, 0.0, 0),
    (0, 0, True), (0, 0, IntSubclass(0)), (0, 0, -1), (0, 0, None),
])
def test_observed_metadata_reasons_require_exact_non_negative_ints(reason, observed):
    with pytest.raises(TypeError):
        module._create_filesystem_target_metadata_snapshot(reason, *observed)


@pytest.mark.parametrize("reason", [object(), "SOURCE_ABSENT", 1])
def test_classifier_requires_exact_reason_type(reason):
    with pytest.raises(TypeError):
        module._create_filesystem_target_metadata_snapshot(reason, None, None, None)
