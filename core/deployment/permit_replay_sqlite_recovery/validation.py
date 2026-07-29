"""Exact recovery and post-recovery concurrency validation."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from core.deployment.contracts import sha256_digest
from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplayReadOnlyInspector,
    PermitReplayStatus,
    PermitReplayStorageConfig,
)
from core.deployment.permit_replay_sqlite_writer import (
    PermitReplayWriteStatus,
    PermitReplayWriterConfig,
    PermitReservationRequest,
    PermitTerminalRequest,
    PermitTerminalState,
    SQLitePermitReplayRegistry,
)

from core.deployment.permit_replay_sqlite_recovery.models import (
    PermitReplayConcurrencyValidationReport,
    PermitReplayRecoveryFinding,
    PermitReplayRecoveryStatus,
    PermitReplayRecoveryValidationReport,
)
from core.deployment.permit_replay_sqlite_recovery.services import _FIELDS, _bytes_digest, _identity, _open_read_only, _snapshot


class PermitReplayRecoveryValidator:
    def __init__(self, *, path_policy: PermitReplayPathPolicy) -> None:
        self._policy = path_policy

    def validate(self, source: Path, recovered: Path, *, validated_at: str,
                 expected_source_digest: str | None = None
                 ) -> PermitReplayRecoveryValidationReport:
        source_rows, source_logical, source_states = _snapshot(source)
        recovered_rows, recovered_logical, recovered_states = _snapshot(recovered)
        source_digest = _bytes_digest(source)
        source_unchanged = expected_source_digest in (None, source_digest)
        inspection = PermitReplayReadOnlyInspector(
            config=PermitReplayStorageConfig(recovered), path_policy=self._policy
        ).inspect(inspected_at=validated_at)
        events_equal = source_rows == recovered_rows and source_logical == recovered_logical
        states_equal = source_states == recovered_states
        findings = []
        if not events_equal:
            findings.append(PermitReplayRecoveryFinding("EVENT_MISMATCH"))
        if not states_equal:
            findings.append(PermitReplayRecoveryFinding("STATE_MISMATCH"))
        if not source_unchanged:
            findings.append(PermitReplayRecoveryFinding("SOURCE_CHANGED"))
        healthy = inspection.status is PermitReplayStatus.HEALTHY
        if not healthy:
            findings.append(PermitReplayRecoveryFinding("RECOVERED_NOT_HEALTHY"))
        semantic = {
            "status": (PermitReplayRecoveryStatus.VALID if not findings
                       else PermitReplayRecoveryStatus.INVALID),
            "findings": tuple(findings),
            "source_path_identity_digest": _identity(source),
            "recovered_path_identity_digest": _identity(recovered),
            "exact_event_equality": events_equal,
            "exact_permit_state_equality": states_equal,
            "source_unchanged": source_unchanged,
            "recovered_healthy": healthy,
            "replay_violations": inspection.replay_violations,
            "production_authorized": False,
        }
        digestable = {key: ([asdict(item) for item in value] if key == "findings"
                            else value.value if hasattr(value, "value") else value)
                      for key, value in semantic.items()}
        return PermitReplayRecoveryValidationReport(
            **semantic, report_digest=sha256_digest(digestable)
        )


class PermitReplayPostRecoveryConcurrencyValidator:
    def __init__(self, *, database_path: Path,
                 path_policy: PermitReplayPathPolicy) -> None:
        self._path = database_path
        self._policy = path_policy

    def validate(self, *, reservation: PermitReservationRequest,
                 consumed: PermitTerminalRequest,
                 failed_closed: PermitTerminalRequest,
                 validated_at: str) -> PermitReplayConcurrencyValidationReport:
        registry = SQLitePermitReplayRegistry(
            config=PermitReplayWriterConfig(self._path), path_policy=self._policy
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            reservations = list(pool.map(registry.reserve, (reservation, reservation)))
        reservation_commits = sum(
            report.status is PermitReplayWriteStatus.COMMITTED for report, _ in reservations
        )
        reservation_idempotent = sum(
            report.status is PermitReplayWriteStatus.IDEMPOTENT for report, _ in reservations
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            terminals = list(pool.map(
                registry.transition_terminal, (consumed, failed_closed)
            ))
        terminal_commits = sum(
            report.status is PermitReplayWriteStatus.COMMITTED for report, _ in terminals
        )
        terminal_denials = sum(
            report.status is PermitReplayWriteStatus.DENIED for report, _ in terminals
        )
        with _open_read_only(self._path) as connection:
            sequences = [row[0] for row in connection.execute(
                "SELECT ledger_sequence FROM permit_use_events"
            )]
            event_ids = [row[0] for row in connection.execute(
                "SELECT event_id FROM permit_use_events"
            )]
        inspection = PermitReplayReadOnlyInspector(
            config=PermitReplayStorageConfig(self._path), path_policy=self._policy
        ).inspect(inspected_at=validated_at)
        healthy = inspection.status is PermitReplayStatus.HEALTHY
        valid = (
            reservation_commits == 1 and reservation_idempotent == 1 and
            terminal_commits == 1 and terminal_denials == 1 and
            len(sequences) == len(set(sequences)) and
            len(event_ids) == len(set(event_ids)) and healthy and
            inspection.replay_violations == 0
        )
        semantic = {
            "status": PermitReplayRecoveryStatus.VALID if valid
            else PermitReplayRecoveryStatus.INVALID,
            "reservation_commits": reservation_commits,
            "reservation_idempotent": reservation_idempotent,
            "terminal_commits": terminal_commits,
            "terminal_denials": terminal_denials,
            "duplicate_sequences": len(sequences) - len(set(sequences)),
            "duplicate_event_ids": len(event_ids) - len(set(event_ids)),
            "final_healthy": healthy,
            "replay_violations": inspection.replay_violations,
            "production_authorized": False,
        }
        digestable = {key: value.value if hasattr(value, "value") else value
                      for key, value in semantic.items()}
        return PermitReplayConcurrencyValidationReport(
            **semantic, report_digest=sha256_digest(digestable)
        )
