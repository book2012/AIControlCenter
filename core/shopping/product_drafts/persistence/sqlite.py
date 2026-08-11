"""SQLite ProductDraft repository and read source."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import sqlite3

from ..errors import DuplicateRevisionError, RevisionChainError, RevisionSequenceError
from ..lifecycle import TransitionCommand, TransitionOutcome, TransitionResult, evaluate_transition, replay_result
from ..models import ProductDraftRevision
from ..serialization import canonical_json, product_draft_from_json, sha256_digest
from .schema import BUSY_TIMEOUT_MS, connect_database, validate_database
from .path_policy import DatabasePathPolicy, DEFAULT_DURABLE_PATH_POLICY


def _transition_from_json(payload: str) -> TransitionResult:
    item = json.loads(payload)
    return TransitionResult(
        item["draft_id"], item["revision_id"], item["previous_state"], item["state"], item["outcome"],
        item["idempotency_key"], item["command_digest"], item["result_digest"], item["audit_reference"],
        datetime.fromisoformat(item["completed_at"].replace("Z", "+00:00")),
        item.get("kind", "RESULT"), item.get("schema_version", "1.0.0"),
    )


class SQLiteProductDraftStore:
    """One-database ProductDraft source of truth with SQLite writer locking."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS,
                 path_policy: DatabasePathPolicy = DEFAULT_DURABLE_PATH_POLICY) -> None:
        self._path_policy = path_policy
        self.database_path = path_policy.validate(database_path)
        self.busy_timeout_ms = busy_timeout_ms

    def _reader(self) -> sqlite3.Connection:
        connection = connect_database(self.database_path, read_only=True,
                                      busy_timeout_ms=self.busy_timeout_ms)
        validate_database(connection)
        return connection

    def _writer(self) -> sqlite3.Connection:
        connection = connect_database(self.database_path, busy_timeout_ms=self.busy_timeout_ms,
                                      path_policy=self._path_policy)
        validate_database(connection)
        return connection

    def is_available(self) -> bool:
        try:
            connection = self._reader()
            connection.close()
            return True
        except (OSError, sqlite3.Error, RuntimeError):
            return False

    @staticmethod
    def _insert_revision(connection: sqlite3.Connection, revision: ProductDraftRevision,
                         *, allow_lifecycle_update: bool = False) -> None:
        if not isinstance(revision, ProductDraftRevision):
            raise TypeError("revision must be a ProductDraftRevision")
        existing = connection.execute(
            "SELECT revision_number,previous_revision_id,created_at FROM product_draft_revisions WHERE draft_id=? AND revision_id=?",
            (revision.draft_id, revision.revision_id)).fetchone()
        payload = canonical_json(revision)
        digest = sha256_digest(revision)
        stamp = revision.identity.created_at.isoformat().replace("+00:00", "Z")
        if existing is not None:
            if not allow_lifecycle_update:
                raise DuplicateRevisionError("duplicate revision_id")
            if (int(existing["revision_number"]), existing["previous_revision_id"], existing["created_at"]) != (
                    revision.revision_number, revision.identity.previous_revision_id, stamp):
                raise RevisionChainError("revision identity/chain cannot change")
            connection.execute(
                "UPDATE product_draft_revisions SET revision_json=?,revision_digest=?,lifecycle_state=?,updated_at=? WHERE draft_id=? AND revision_id=?",
                (payload, digest, revision.state.value, stamp, revision.draft_id, revision.revision_id))
            return
        current = connection.execute(
            "SELECT revision_id,revision_number FROM product_draft_revisions WHERE draft_id=? ORDER BY revision_number DESC LIMIT 1",
            (revision.draft_id,)).fetchone()
        if current is None:
            if revision.revision_number != 1 or revision.identity.previous_revision_id is not None:
                raise RevisionSequenceError("first stored revision must be number 1")
        else:
            if revision.revision_number != int(current["revision_number"]) + 1:
                raise RevisionSequenceError("revision numbers must be monotonic")
            if revision.identity.previous_revision_id != current["revision_id"]:
                raise RevisionChainError("previous_revision_id must reference current revision")
        connection.execute(
            "INSERT INTO product_draft_revisions VALUES (?,?,?,?,?,?,?,?,?)",
            (revision.draft_id, revision.revision_id, revision.revision_number,
             revision.identity.previous_revision_id, payload, digest, revision.state.value, stamp, stamp))

    def store(self, revision: ProductDraftRevision) -> None:
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._insert_revision(connection, revision)
            connection.commit()
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally:
            connection.close()

    def fetch(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None:
        return self.fetch_revision(draft_id, revision_id)

    def fetch_revision(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None:
        connection = self._reader()
        try:
            row = connection.execute("SELECT revision_json FROM product_draft_revisions WHERE draft_id=? AND revision_id=?",
                                     (draft_id, revision_id)).fetchone()
            return None if row is None else product_draft_from_json(row[0])
        finally: connection.close()

    def fetch_current(self, draft_id: str) -> ProductDraftRevision | None:
        connection = self._reader()
        try:
            row = connection.execute("SELECT revision_json FROM product_draft_revisions WHERE draft_id=? ORDER BY revision_number DESC LIMIT 1",
                                     (draft_id,)).fetchone()
            return None if row is None else product_draft_from_json(row[0])
        finally: connection.close()

    def list_revisions(self) -> tuple[ProductDraftRevision, ...]:
        connection = self._reader()
        try:
            return tuple(product_draft_from_json(row[0]) for row in connection.execute(
                "SELECT revision_json FROM product_draft_revisions ORDER BY draft_id,revision_number,revision_id"))
        finally: connection.close()

    def get_idempotency(self, draft_id: str, key: str) -> tuple[str, TransitionResult] | None:
        connection = self._reader()
        try:
            row = connection.execute("SELECT command_digest,result_json FROM product_draft_transition_idempotency WHERE draft_id=? AND idempotency_key=?",
                                     (draft_id, key)).fetchone()
            return None if row is None else (row[0], _transition_from_json(row[1]))
        finally: connection.close()

    def bind_idempotency(self, draft_id: str, key: str, digest: str, result: TransitionResult) -> None:
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT command_digest,result_json FROM product_draft_transition_idempotency WHERE draft_id=? AND idempotency_key=?",
                                          (draft_id, key)).fetchone()
            candidate = canonical_json(result)
            if existing is not None and tuple(existing) != (digest, candidate):
                raise ValueError("idempotency records are immutable")
            if existing is None:
                connection.execute("INSERT INTO product_draft_transition_idempotency VALUES (?,?,?,?)",
                                   (draft_id, key, digest, candidate))
            connection.commit()
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def transition(self, command: TransitionCommand, completed_at: datetime) -> TransitionResult:
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT command_digest,result_json FROM product_draft_transition_idempotency WHERE draft_id=? AND idempotency_key=?",
                                     (command.draft_id, command.idempotency_key)).fetchone()
            if row is not None:
                saved = _transition_from_json(row["result_json"])
                if row["command_digest"] == command.command_digest:
                    connection.commit(); return replay_result(saved)
                rejected = replace(saved, outcome=TransitionOutcome.REJECTED_IDEMPOTENCY_KEY_REUSE,
                                   command_digest=command.command_digest, result_digest=command.command_digest)
                seed = {name: getattr(rejected, name) for name in rejected.__dataclass_fields__ if name != "result_digest"}
                connection.commit(); return replace(rejected, result_digest=sha256_digest(seed))
            revision_row = connection.execute("SELECT revision_json FROM product_draft_revisions WHERE draft_id=? ORDER BY revision_number DESC LIMIT 1",
                                              (command.draft_id,)).fetchone()
            if revision_row is None: raise KeyError(command.draft_id)
            revision = product_draft_from_json(revision_row[0])
            result = evaluate_transition(revision, command, completed_at)
            if result.outcome is TransitionOutcome.APPLIED:
                self._insert_revision(connection, revision.with_state(result.state), allow_lifecycle_update=True)
            connection.execute("INSERT INTO product_draft_transition_idempotency VALUES (?,?,?,?)",
                               (command.draft_id, command.idempotency_key, command.command_digest, canonical_json(result)))
            connection.commit(); return result
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()
