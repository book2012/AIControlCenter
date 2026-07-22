from __future__ import annotations

from datetime import datetime, timezone

from core.governance.operations.adapters.sqlite import (
    SQLiteOperationsEventRepository,
)
from core.governance.operations.application.models import (
    BackupExecutionResult,
    SnapshotExecutionResult,
)


def utc(
    hour: int,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(
        2026,
        7,
        21,
        hour,
        minute,
        second,
        tzinfo=timezone.utc,
    )


class SequenceClock:
    def __init__(self, *values: datetime) -> None:
        self.values = list(values)
        self.index = 0

    def now(self) -> datetime:
        if self.index >= len(self.values):
            raise RuntimeError(
                "clock sequence exhausted"
            )

        value = self.values[self.index]
        self.index += 1
        return value


class FakeSnapshotExecutor:
    def __init__(
        self,
        *,
        result=None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or SnapshotExecutionResult(
            snapshot_id="snapshot-001",
            snapshot_timestamp=utc(9),
            record_count=3,
            evidence={"read_only": True},
        )
        self.error = error
        self.calls = []

    def execute(
        self,
        *,
        scheduled_for,
    ):
        self.calls.append(
            {
                "scheduled_for": scheduled_for,
            }
        )

        if self.error is not None:
            raise self.error

        return self.result


class FakeBackupVerifier:
    def __init__(
        self,
        *,
        result=None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or BackupExecutionResult(
            backup_path="/tmp/verified.sqlite3",
            backup_sha256="a" * 64,
            quick_check=("ok",),
            row_counts_match=True,
        )
        self.error = error
        self.calls = []

    def verify(
        self,
        *,
        scheduled_for,
    ):
        self.calls.append(
            {
                "scheduled_for": scheduled_for,
            }
        )

        if self.error is not None:
            raise self.error

        return self.result


class FailingAppendRepository:
    def __init__(
        self,
        delegate,
        *,
        fail_on_append: int,
    ) -> None:
        self.delegate = delegate
        self.fail_on_append = fail_on_append
        self.append_calls = 0

    def append(self, event):
        self.append_calls += 1

        if (
            self.append_calls
            == self.fail_on_append
        ):
            raise RuntimeError(
                "simulated persistence failure"
            )

        return self.delegate.append(event)

    def events_for_run(self, run_id):
        return self.delegate.events_for_run(run_id)

    def iter_events(self, operation=None):
        return self.delegate.iter_events(operation)


def temporary_repository(tmp_path):
    instance = SQLiteOperationsEventRepository(
        tmp_path / "operations.sqlite3"
    )
    instance.initialize_schema()
    return instance
