"""Crash-safe evidence journal for the one pre-bootstrap remediation attempt.

This is deliberately separate from ordinary SEC-02 authorization consumption.
It stores no authorization capability and exposes no Production constructor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
from typing import Callable, Protocol

from .governance_remediation_authorization import RemediationAuthorizationPurpose


JOURNAL_SCHEMA_VERSION = 1
JOURNAL_PURPOSE_VERSION = "GOVERNANCE_DIRECTORY_MODE_0755_TO_0700/V1"
FUTURE_PRODUCTION_JOURNAL_PATH = Path(
    "/Library/Application Support/AIControlCenter/Security/"
    "PreBootstrapRemediation/attempt-journal.sqlite3"
)
_REPLAY_DOMAIN = b"AIControlCenter/SEC02/pre-bootstrap-remediation/replay/v1\x00"
_REPLAY_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class DurableAttemptState(Enum):
    DURABLY_CLAIMED = "DURABLY_CLAIMED"
    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"
    TERMINAL_UNCERTAIN = "TERMINAL_UNCERTAIN"


class DurableJournalError(RuntimeError):
    """The durable boundary failed closed."""


class ReplayDenied(DurableJournalError):
    """The replay identity already has a claim or terminal record."""


@dataclass(frozen=True, slots=True, init=False)
class AuthorizationReplayKey:
    """Non-authoritative, immutable fingerprint of an ephemeral capability.

    SHA-256 and domain separation are fixed here. This does not assert that the
    opaque native input has entropy or uniqueness, and the key grants no right.
    """

    value: str

    def __init__(self, value: object) -> None:
        raise TypeError("replay keys cannot be constructed from caller text")

    @classmethod
    def derive_from_ephemeral_capability(cls, capability: bytes) -> "AuthorizationReplayKey":
        if type(capability) is not bytes or not capability:
            raise ValueError("ephemeral capability must be non-empty exact bytes")
        instance = object.__new__(cls)
        object.__setattr__(instance, "value", hashlib.sha256(_REPLAY_DOMAIN + capability).hexdigest())
        return instance

    @classmethod
    def _from_stored_value(cls, value: object) -> "AuthorizationReplayKey":
        if type(value) is not str or _REPLAY_PATTERN.fullmatch(value) is None:
            raise DurableJournalError("stored replay identity is invalid")
        instance = object.__new__(cls)
        object.__setattr__(instance, "value", value)
        return instance


@dataclass(frozen=True, slots=True)
class DurableAttemptRecord:
    replay_key: AuthorizationReplayKey
    purpose: RemediationAuthorizationPurpose
    purpose_version: str
    state: DurableAttemptState
    claimed_at: str
    terminal_at: str | None = None


class PreBootstrapRemediationAttemptJournal(Protocol):
    def claim_once(self, replay_key: AuthorizationReplayKey) -> DurableAttemptRecord: ...
    def record_terminal(
        self, replay_key: AuthorizationReplayKey, state: DurableAttemptState
    ) -> DurableAttemptRecord: ...
    def read(self, replay_key: AuthorizationReplayKey) -> DurableAttemptRecord | None: ...


class SQLitePreBootstrapRemediationAttemptJournal:
    """Purpose-fixed SQLite journal available only at explicitly isolated paths."""

    def __init__(
        self,
        database_path: Path,
        *,
        clock: Callable[[], datetime] | None = None,
        fault: Callable[[str, sqlite3.Connection], None] | None = None,
    ) -> None:
        if not isinstance(database_path, Path) or not database_path.is_absolute():
            raise ValueError("journal test path must be an absolute pathlib.Path")
        if database_path == FUTURE_PRODUCTION_JOURNAL_PATH:
            raise ValueError("Production journal provisioning is not authorized")
        resolved_parent = database_path.parent.resolve()
        temporary_root = Path(tempfile.gettempdir()).resolve()
        if resolved_parent != temporary_root and temporary_root not in resolved_parent.parents:
            raise ValueError("journal repository adapter is restricted to temporary paths")
        self._path = database_path
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._fault = fault
        try:
            database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if not database_path.exists():
                descriptor = os.open(database_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
            parent_metadata = database_path.parent.lstat()
            database_metadata = database_path.lstat()
            if (
                not stat.S_ISDIR(parent_metadata.st_mode)
                or stat.S_IMODE(parent_metadata.st_mode) != 0o700
                or not stat.S_ISREG(database_metadata.st_mode)
                or stat.S_IMODE(database_metadata.st_mode) != 0o600
            ):
                raise DurableJournalError("journal path permissions or object kind are unsafe")
            with self._connect() as connection:
                self._initialize_or_validate(connection)
        except (OSError, sqlite3.DatabaseError, DurableJournalError) as exc:
            if isinstance(exc, DurableJournalError):
                raise
            raise DurableJournalError("cannot initialize durable attempt journal") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, isolation_level=None, timeout=1.0)
        connection.execute("PRAGMA busy_timeout=1000")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @staticmethod
    def _initialize_or_validate(connection: sqlite3.Connection) -> None:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        objects = connection.execute(
            "SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        if version == 0 and not objects:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """CREATE TABLE remediation_attempts (
                    replay_key TEXT PRIMARY KEY NOT NULL CHECK(length(replay_key)=64),
                    purpose TEXT NOT NULL CHECK(purpose='GOVERNANCE_DIRECTORY_MODE_0755_TO_0700'),
                    purpose_version TEXT NOT NULL CHECK(purpose_version='GOVERNANCE_DIRECTORY_MODE_0755_TO_0700/V1'),
                    state TEXT NOT NULL CHECK(state IN ('DURABLY_CLAIMED','TERMINAL_SUCCESS','TERMINAL_FAILURE','TERMINAL_UNCERTAIN')),
                    claimed_at TEXT NOT NULL,
                    terminal_at TEXT
                ) WITHOUT ROWID"""
            )
            connection.execute(f"PRAGMA user_version={JOURNAL_SCHEMA_VERSION}")
            connection.commit()
            return
        if version != JOURNAL_SCHEMA_VERSION or objects != [("remediation_attempts", "table")]:
            raise DurableJournalError("journal schema mismatch")

    def _inject(self, stage: str, connection: sqlite3.Connection) -> None:
        if self._fault is not None:
            self._fault(stage, connection)

    def _timestamp(self) -> str:
        try:
            value = self._clock()
        except Exception as exc:
            raise DurableJournalError("journal clock failed closed") from exc
        if type(value) is not datetime or value.tzinfo is None:
            raise DurableJournalError("journal clock must return an aware datetime")
        return value.isoformat()

    @staticmethod
    def _require_key(replay_key: object) -> AuthorizationReplayKey:
        if type(replay_key) is not AuthorizationReplayKey:
            raise ValueError("replay_key must be exactly AuthorizationReplayKey")
        return AuthorizationReplayKey._from_stored_value(replay_key.value)

    def _read_connection(
        self, connection: sqlite3.Connection, replay_key: AuthorizationReplayKey
    ) -> DurableAttemptRecord | None:
        row = connection.execute(
            "SELECT replay_key,purpose,purpose_version,state,claimed_at,terminal_at "
            "FROM remediation_attempts WHERE replay_key=?",
            (replay_key.value,),
        ).fetchone()
        if row is None:
            return None
        try:
            key = AuthorizationReplayKey._from_stored_value(row[0])
            purpose = RemediationAuthorizationPurpose(row[1])
            state = DurableAttemptState(row[3])
        except (ValueError, DurableJournalError) as exc:
            raise DurableJournalError("journal row is corrupt") from exc
        if row[2] != JOURNAL_PURPOSE_VERSION or type(row[4]) is not str:
            raise DurableJournalError("journal row is corrupt")
        terminal_at = row[5]
        if (state is DurableAttemptState.DURABLY_CLAIMED) != (terminal_at is None):
            raise DurableJournalError("journal row is corrupt")
        return DurableAttemptRecord(key, purpose, row[2], state, row[4], terminal_at)

    def read(self, replay_key: AuthorizationReplayKey) -> DurableAttemptRecord | None:
        key = self._require_key(replay_key)
        try:
            with self._connect() as connection:
                self._initialize_or_validate(connection)
                return self._read_connection(connection, key)
        except sqlite3.DatabaseError as exc:
            raise DurableJournalError("journal read failed closed") from exc

    def claim_once(self, replay_key: AuthorizationReplayKey) -> DurableAttemptRecord:
        key = self._require_key(replay_key)
        claimed_at = self._timestamp()
        attempted_commit = False
        try:
            with self._connect() as connection:
                self._initialize_or_validate(connection)
                connection.execute("BEGIN IMMEDIATE")
                if self._read_connection(connection, key) is not None:
                    connection.rollback()
                    raise ReplayDenied("replay identity was already claimed")
                connection.execute(
                    "INSERT INTO remediation_attempts VALUES (?,?,?,?,?,NULL)",
                    (key.value, RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700.value,
                     JOURNAL_PURPOSE_VERSION, DurableAttemptState.DURABLY_CLAIMED.value, claimed_at),
                )
                self._inject("before_claim_commit", connection)
                attempted_commit = True
                connection.commit()
                self._inject("after_claim_commit", connection)
        except ReplayDenied:
            raise
        except (sqlite3.DatabaseError, DurableJournalError) as exc:
            if attempted_commit:
                record = self.read(key)
                if record is not None and record.state is DurableAttemptState.DURABLY_CLAIMED:
                    return record
            raise DurableJournalError("durable claim failed closed") from exc
        record = self.read(key)
        if record is None or record.state is not DurableAttemptState.DURABLY_CLAIMED:
            raise DurableJournalError("durable claim acknowledgement is inconsistent")
        return record

    def record_terminal(
        self, replay_key: AuthorizationReplayKey, state: DurableAttemptState
    ) -> DurableAttemptRecord:
        key = self._require_key(replay_key)
        if type(state) is not DurableAttemptState or state is DurableAttemptState.DURABLY_CLAIMED:
            raise ValueError("state must be an exact terminal state")
        terminal_at = self._timestamp()
        attempted_commit = False
        try:
            with self._connect() as connection:
                self._initialize_or_validate(connection)
                connection.execute("BEGIN IMMEDIATE")
                current = self._read_connection(connection, key)
                if current is None or current.state is not DurableAttemptState.DURABLY_CLAIMED:
                    connection.rollback()
                    raise DurableJournalError("exact durable claim is required")
                changed = connection.execute(
                    "UPDATE remediation_attempts SET state=?,terminal_at=? "
                    "WHERE replay_key=? AND state='DURABLY_CLAIMED'",
                    (state.value, terminal_at, key.value),
                ).rowcount
                if changed != 1:
                    connection.rollback()
                    raise DurableJournalError("terminal transition was not exact")
                self._inject("before_terminal_commit", connection)
                attempted_commit = True
                connection.commit()
                self._inject("after_terminal_commit", connection)
        except (sqlite3.DatabaseError, DurableJournalError) as exc:
            if attempted_commit:
                record = self.read(key)
                if record is not None and record.state is state:
                    return record
            raise DurableJournalError("terminal recording failed closed") from exc
        record = self.read(key)
        if record is None or record.state is not state:
            raise DurableJournalError("terminal acknowledgement is inconsistent")
        return record


__all__ = (
    "AuthorizationReplayKey", "DurableAttemptRecord", "DurableAttemptState",
    "DurableJournalError", "FUTURE_PRODUCTION_JOURNAL_PATH", "JOURNAL_PURPOSE_VERSION",
    "PreBootstrapRemediationAttemptJournal", "ReplayDenied",
    "SQLitePreBootstrapRemediationAttemptJournal",
)
