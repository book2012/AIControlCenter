"""Mac-owned single-lstat filesystem target metadata observation boundary."""

import os
import stat

from core.secrets import (
    mariadb_continuity_filesystem_target_metadata_snapshot as snapshot_contract,
)


Reason = snapshot_contract.FilesystemTargetMetadataSnapshotReason


class MacFilesystemTargetMetadataSnapshotAdapter:
    """Observe only target metadata once and grant no authority."""

    def observe_once(
        self, request: snapshot_contract.FilesystemTargetMetadataSnapshotRequest
    ) -> snapshot_contract.FilesystemTargetMetadataSnapshot:
        snapshot_contract.validate_filesystem_target_metadata_snapshot_request(request)

        try:
            observed = os.lstat(request.concrete_path.concrete_path)
        except FileNotFoundError:
            return _snapshot(Reason.SOURCE_ABSENT)
        except OSError:
            return _snapshot(Reason.METADATA_ACCESS_FAILURE)

        try:
            observed_mode = observed.st_mode
            observed_uid = observed.st_uid
            observed_gid = observed.st_gid
        except (AttributeError, TypeError):
            return _ambiguous()
        if not all(
            type(value) is int and value >= 0
            for value in (observed_mode, observed_uid, observed_gid)
        ):
            return _ambiguous()

        if stat.S_ISLNK(observed_mode):
            reason = Reason.SYMLINK_REJECTED
        elif not stat.S_ISDIR(observed_mode):
            reason = Reason.WRONG_FILE_TYPE
        elif stat.S_IMODE(observed_mode) != 0o700:
            reason = Reason.TARGET_MODE_MISMATCH
        elif observed_uid != request.ownership_expectation.expected_uid:
            reason = Reason.TARGET_UID_MISMATCH
        elif observed_gid != request.ownership_expectation.expected_gid:
            reason = Reason.TARGET_GID_MISMATCH
        else:
            reason = Reason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE
        return _snapshot(
            reason,
            observed_mode,
            observed_uid,
            observed_gid,
        )


def _ambiguous() -> snapshot_contract.FilesystemTargetMetadataSnapshot:
    return _snapshot(Reason.AMBIGUOUS_METADATA_RESULT)


def _snapshot(
    reason: Reason,
    observed_mode: int | None = None,
    observed_uid: int | None = None,
    observed_gid: int | None = None,
) -> snapshot_contract.FilesystemTargetMetadataSnapshot:
    return snapshot_contract._create_filesystem_target_metadata_snapshot(
        reason,
        observed_mode,
        observed_uid,
        observed_gid,
    )
