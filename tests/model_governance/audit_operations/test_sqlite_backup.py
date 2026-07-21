import hashlib
import sqlite3

import pytest

from core.governance.operations.adapters.sqlite import (
    BackupVerificationError,
    REQUIRED_OBJECTS,
    SQLiteOnlineBackupVerifier,
    SQLiteOperationsEventRepository,
)
from core.governance.operations.domain.events import (
    Operation,
    scheduled_event,
)

from .test_sqlite_repository import utc


def populated_database(tmp_path):
    source = tmp_path / "source.sqlite3"
    repository = SQLiteOperationsEventRepository(
        source
    )
    repository.initialize_schema()
    repository.append(
        scheduled_event(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT,
            utc(1),
        )
    )
    return source


def test_online_backup_is_verified_and_finalized(
    tmp_path,
):
    source = populated_database(tmp_path)
    destination = tmp_path / "verified.sqlite3"

    result = SQLiteOnlineBackupVerifier(
        source
    ).verify_to(destination)

    assert destination.is_file()
    assert not (
        tmp_path / "verified.sqlite3.partial"
    ).exists()
    assert result.quick_check == ("ok",)
    assert result.source_row_count == 1
    assert result.backup_row_count == 1
    assert set(result.required_objects) == REQUIRED_OBJECTS
    assert result.sha256 == hashlib.sha256(
        destination.read_bytes()
    ).hexdigest()

    backup_repository = (
        SQLiteOperationsEventRepository(
            destination
        )
    )
    assert backup_repository.count() == 1


def test_backup_refuses_existing_destination(
    tmp_path,
):
    source = populated_database(tmp_path)
    destination = tmp_path / "existing.sqlite3"
    destination.write_bytes(b"preserve")

    with pytest.raises(BackupVerificationError):
        SQLiteOnlineBackupVerifier(
            source
        ).verify_to(destination)

    assert destination.read_bytes() == b"preserve"


def test_backup_rejects_source_as_destination(
    tmp_path,
):
    source = populated_database(tmp_path)

    with pytest.raises(BackupVerificationError):
        SQLiteOnlineBackupVerifier(
            source
        ).verify_to(source)


def test_failed_verification_removes_partial_file(
    tmp_path,
):
    source = tmp_path / "invalid.sqlite3"
    connection = sqlite3.connect(source)
    connection.close()

    destination = tmp_path / "failed.sqlite3"
    partial = tmp_path / "failed.sqlite3.partial"

    with pytest.raises(sqlite3.OperationalError):
        SQLiteOnlineBackupVerifier(
            source
        ).verify_to(destination)

    assert not destination.exists()
    assert not partial.exists()
