"""SQLite implementation of durable Shopping generation transactions."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from typing import Callable

from .path_policy import DatabasePathPolicy, DEFAULT_DURABLE_PATH_POLICY
from .schema import BUSY_TIMEOUT_MS, connect_database, validate_database
from .sqlite import SQLiteProductDraftStore
from ..serialization import product_draft_from_json, sha256_digest
from ..values import require_digest, require_text
from ..models import LifecycleState
from ..application.generation import (
    GenerationOperationClaim, GenerationOperationClaimStatus, GenerationOperationConflict,
    GenerationOperationInFlight, GenerationOperationTerminalFailure,
    ProductDraftGenerationAuditProjection, ProductDraftGenerationResult,
)

FailureHook = Callable[[str], None]
_PROVIDER_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,79}\Z", re.ASCII)
_MODEL_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/:+\-]{0,159}\Z", re.ASCII)
_ACTOR_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,159}\Z", re.ASCII)
_CORRELATION_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,159}\Z", re.ASCII)
_AUDIT_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,159}\Z", re.ASCII)
_PROVIDER_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-]{0,127}\Z", re.ASCII)
_JWT_SHAPED = re.compile(
    r"[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\Z", re.ASCII)
_CREDENTIAL_PREFIX = re.compile(
    r"(?:sk-(?:proj-)?|AKIA|ASIA|gh[opurs]_|github_pat_|xox[baprs]-|ya29\.|AIza)", re.ASCII)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _identifier(value: str, field: str, grammar: re.Pattern[str]) -> str:
    if not isinstance(value, str) or grammar.fullmatch(value) is None:
        raise ValueError(f"{field} must use its bounded identifier syntax")
    if _JWT_SHAPED.fullmatch(value) or _CREDENTIAL_PREFIX.match(value):
        raise ValueError(f"{field} must not be credential-shaped")
    return value


def _actor_reference(value: str) -> str:
    return _identifier(value, "actor_reference", _ACTOR_REFERENCE)


def _correlation_reference(value: str) -> str:
    return _identifier(value, "correlation_id", _CORRELATION_REFERENCE)


def _audit_reference(value: str) -> str:
    return _identifier(value, "audit_reference", _AUDIT_REFERENCE)


def _provider(value: str) -> str:
    return _identifier(value, "provider", _PROVIDER_IDENTIFIER)


def _model(value: str) -> str:
    _identifier(value, "model", _MODEL_IDENTIFIER)
    if _JWT_SHAPED.fullmatch(value):
        raise ValueError("model must not be credential-shaped")
    if ":" in value:
        namespace, separator, tag = value.partition(":")
        if not separator or "/" not in namespace or not tag or ":" in tag:
            raise ValueError("model must use its bounded identifier syntax")
    return value


def _provider_request_id(value: str | None) -> str | None:
    if value is None:
        return None
    _identifier(value, "provider_request_id", _PROVIDER_REQUEST_ID)
    if _JWT_SHAPED.fullmatch(value):
        raise ValueError("provider_request_id must not be credential-shaped")
    return value


def _verified_completed_result(connection: sqlite3.Connection, row: sqlite3.Row,
                               key: str, *, replay: bool) -> ProductDraftGenerationResult:
    revision_row = connection.execute(
        "SELECT revision_json,revision_digest FROM product_draft_revisions WHERE draft_id=? AND revision_id=?",
        (row["draft_id"], row["revision_id"])).fetchone()
    audit_row = connection.execute(
        "SELECT * FROM product_draft_generation_audit_events WHERE operation_key=?", (key,)).fetchone()
    if revision_row is None or audit_row is None:
        raise RuntimeError("completed generation evidence is incomplete")
    revision = product_draft_from_json(revision_row["revision_json"])
    revision_digest = sha256_digest(revision)
    if (revision.draft_id, revision.revision_id) != (row["draft_id"], row["revision_id"]):
        raise RuntimeError("completed revision identity binding is invalid")
    if revision_row["revision_digest"] != revision_digest or audit_row["revision_digest"] != revision_digest:
        raise RuntimeError("completed revision digest binding is invalid")
    if (audit_row["draft_id"], audit_row["revision_id"]) != (row["draft_id"], row["revision_id"]):
        raise RuntimeError("completed audit identity binding is invalid")
    if (revision.identity.correlation_id, revision.identity.audit_reference,
        revision.identity.created_by.actor_id) != (audit_row["correlation_reference"],
        audit_row["audit_reference"], audit_row["actor_reference"]):
        raise RuntimeError("completed revision and audit reference binding is invalid")
    if (revision.state is not LifecycleState.DRAFT or revision.validation is not None
            or revision.human_decision is not None or revision.deployment_intent is not None):
        raise RuntimeError("completed generated revision lifecycle is invalid")
    occurred = datetime.fromisoformat(audit_row["occurred_at"].replace("Z", "+00:00"))
    audit = ProductDraftGenerationAuditProjection(
        audit_row["event_type"], audit_row["draft_id"], audit_row["revision_id"],
        audit_row["actor_reference"], audit_row["correlation_reference"], audit_row["audit_reference"],
        occurred, audit_row["outcome"], audit_row["provider"], audit_row["model"],
        audit_row["provider_request_id"], audit_row["response_digest"], audit_row["revision_digest"])
    result = ProductDraftGenerationResult(
        revision.draft_id, revision.revision_id, revision.revision_number, audit.outcome,
        audit.correlation_id, audit.audit_reference, audit.provider, audit.model,
        audit.provider_request_id, audit.response_digest, revision_digest, revision, audit)
    return result.as_replay() if replay else result


class SQLiteProductDraftGenerationTransactions:
    production_safe = True

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS,
                 failure_hook: FailureHook | None = None,
                 path_policy: DatabasePathPolicy = DEFAULT_DURABLE_PATH_POLICY) -> None:
        self._path_policy = path_policy
        self.database_path = path_policy.validate(database_path)
        self.busy_timeout_ms = busy_timeout_ms
        self._failure_hook = failure_hook

    def _writer(self) -> sqlite3.Connection:
        connection = connect_database(self.database_path, busy_timeout_ms=self.busy_timeout_ms,
                                      path_policy=self._path_policy)
        validate_database(connection)
        return connection

    def _hit(self, point: str) -> None:
        if self._failure_hook is not None:
            self._failure_hook(point)

    def claim(self, key: str, command_digest: str, draft_id: str,
              revision_id: str) -> GenerationOperationClaim:
        for value, name in ((key, "key"), (draft_id, "draft_id"), (revision_id, "revision_id")):
            require_text(value, name)
        require_digest(command_digest, "command_digest")
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM product_draft_generation_operations WHERE operation_key=?", (key,)).fetchone()
            if row is None:
                connection.execute("INSERT INTO product_draft_generation_operations(operation_key,command_digest,state,claimed_at,draft_id,revision_id) VALUES (?,?,'CLAIMED',?,?,?)",
                                   (key, command_digest, _now(), draft_id, revision_id))
                self._hit("claim_before_commit")
                connection.commit()
                return GenerationOperationClaim(GenerationOperationClaimStatus.CLAIMED)
            if row["command_digest"] != command_digest or (row["draft_id"], row["revision_id"]) != (draft_id, revision_id):
                raise GenerationOperationConflict("idempotency key conflicts with another immutable operation binding")
            if row["state"] == "COMPLETED":
                return GenerationOperationClaim(GenerationOperationClaimStatus.COMPLETED,
                                                _verified_completed_result(connection, row, key, replay=False))
            if row["state"] == "TERMINAL_FAILED":
                raise GenerationOperationTerminalFailure("operation previously failed terminally")
            raise GenerationOperationInFlight("operation is already consumed/in flight")
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def complete(self, key: str, command_digest: str, result: ProductDraftGenerationResult) -> None:
        if not isinstance(result, ProductDraftGenerationResult):
            raise TypeError("result must be ProductDraftGenerationResult")
        require_digest(command_digest, "command_digest")
        audit = result.audit_projection
        if audit.event_type != "PRODUCT_DRAFT_GENERATED":
            raise ValueError("event_type must be PRODUCT_DRAFT_GENERATED")
        if audit.outcome != "PREPARED":
            raise ValueError("outcome must be PREPARED")
        _actor_reference(audit.actor_reference)
        _correlation_reference(audit.correlation_id)
        _audit_reference(audit.audit_reference)
        _provider(audit.provider)
        _model(audit.model)
        _provider_request_id(audit.provider_request_id)
        require_digest(audit.response_digest, "response_digest")
        require_digest(audit.revision_digest, "revision_digest")
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM product_draft_generation_operations WHERE operation_key=?", (key,)).fetchone()
            if row is None or row["command_digest"] != command_digest or row["state"] != "CLAIMED":
                raise RuntimeError("only the exact CLAIMED operation can be completed")
            if (row["draft_id"], row["revision_id"]) != (result.draft_id, result.revision_id):
                raise RuntimeError("result does not match claimed resource identity")
            revision = result.revision
            if (revision.draft_id, revision.revision_id, revision.revision_number) != (
                    result.draft_id, result.revision_id, result.revision_number):
                raise RuntimeError("result revision identity is inconsistent")
            if (revision.identity.correlation_id, revision.identity.audit_reference) != (
                    result.correlation_id, result.audit_reference):
                raise RuntimeError("revision references and result bindings are inconsistent")
            if (audit.draft_id, audit.revision_id, audit.correlation_id, audit.audit_reference,
                audit.outcome, audit.provider, audit.model, audit.provider_request_id, audit.response_digest) != (
                    result.draft_id, result.revision_id, result.correlation_id, result.audit_reference,
                    result.outcome, result.provider, result.model, result.provider_request_id, result.response_digest):
                raise RuntimeError("audit and result bindings are inconsistent")
            if audit.actor_reference != revision.identity.created_by.actor_id:
                raise RuntimeError("audit actor and revision creator are inconsistent")
            computed = sha256_digest(revision)
            if computed != result.revision_digest or computed != audit.revision_digest:
                raise RuntimeError("revision digest bindings are inconsistent")
            if (revision.state is not LifecycleState.DRAFT or revision.validation is not None
                    or revision.human_decision is not None or revision.deployment_intent is not None):
                raise RuntimeError("generated revision must remain an undecided DRAFT")
            current = connection.execute("SELECT revision_id,revision_number FROM product_draft_revisions WHERE draft_id=? ORDER BY revision_number DESC LIMIT 1", (result.draft_id,)).fetchone()
            previous = revision.identity.previous_revision_id
            if ((current is None and (previous is not None or result.revision_number != 1)) or
                (current is not None and (current["revision_id"] != previous or int(current["revision_number"]) + 1 != result.revision_number))):
                raise RuntimeError("expected current revision conflict")
            SQLiteProductDraftStore._insert_revision(connection, revision)
            self._hit("completion_after_revision_insert")
            event_id = sha256_digest({"operation_key": key, "audit_reference": audit.audit_reference,
                                      "revision_digest": audit.revision_digest})
            occurred = audit.occurred_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
            connection.execute("INSERT INTO product_draft_generation_audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (event_id,key,audit.event_type,audit.draft_id,audit.revision_id,audit.actor_reference,
                 audit.correlation_id,audit.audit_reference,occurred,audit.outcome,audit.provider,audit.model,
                 audit.provider_request_id,audit.response_digest,audit.revision_digest))
            self._hit("completion_after_audit_insert")
            changed = connection.execute("UPDATE product_draft_generation_operations SET state='COMPLETED',terminal_at=? WHERE operation_key=? AND command_digest=? AND state='CLAIMED' AND draft_id=? AND revision_id=?",
                (_now(),key,command_digest,result.draft_id,result.revision_id)).rowcount
            if changed != 1: raise RuntimeError("operation completion lost its claim")
            self._hit("completion_before_commit")
            connection.commit()
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def fail(self, key: str, command_digest: str) -> None:
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT command_digest,state FROM product_draft_generation_operations WHERE operation_key=?", (key,)).fetchone()
            if row is None or row["command_digest"] != command_digest or row["state"] != "CLAIMED":
                raise RuntimeError("only the exact CLAIMED operation can fail")
            connection.execute("UPDATE product_draft_generation_operations SET state='TERMINAL_FAILED',terminal_at=?,failure_code='PROVIDER_OR_CONTRACT_FAILURE' WHERE operation_key=?", (_now(),key))
            connection.commit()
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def replay_generation(self, key: str, command_digest: str) -> ProductDraftGenerationResult | None:
        connection = connect_database(self.database_path, read_only=True, busy_timeout_ms=self.busy_timeout_ms)
        try:
            validate_database(connection)
            row = connection.execute("SELECT * FROM product_draft_generation_operations WHERE operation_key=?", (key,)).fetchone()
            if row is None: return None
            if row["command_digest"] != command_digest: raise GenerationOperationConflict("idempotency key conflicts with another command")
            if row["state"] == "CLAIMED": raise GenerationOperationInFlight("operation is consumed with unknown provider outcome")
            if row["state"] == "TERMINAL_FAILED": raise GenerationOperationTerminalFailure("operation previously failed terminally")
            return _verified_completed_result(connection, row, key, replay=True)
        finally: connection.close()
