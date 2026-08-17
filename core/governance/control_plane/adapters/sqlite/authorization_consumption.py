"""Narrow durable SQLite implementation of AuthorizationConsumptionPort."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from ...domain import (
    AuthorizationState,
    ConsumptionTransactionStatus,
    GovernanceAuthorizationConsumptionReceipt,
    RepeatedAuthorizationConsumption,
    consume_mutation_budget,
    transition_authorization,
)
from ...ports import AuthorizationConsumptionCommand, AuthorizationConsumptionResult
from .codec import digest_canonical, digest_text, encode_binding, encode_committed
from .path_policy import SQLiteAuthorizationConsumptionPathPolicy, SQLiteOwnershipIdentity
from .schema import SQLiteSchemaError, initialize_or_validate_schema


class SQLiteAuthorizationConsumptionError(RuntimeError):
    """Durable consumption failed closed."""


class SQLiteAuthorizationConsumptionAdapter:
    """One-shot authorization consumer with an irreversible durable barrier."""

    def __init__(
        self,
        *,
        repository_root: Path,
        ownership_identity: SQLiteOwnershipIdentity,
        busy_timeout_ms: int = 1000,
        home: Path | None = None,
        _test_database_path: Path | None = None,
        _fault: Callable[[str, sqlite3.Connection], None] | None = None,
        _clock: Callable[[], datetime] | None = None,
    ) -> None:
        if isinstance(busy_timeout_ms, bool) or not 1 <= busy_timeout_ms <= 30_000:
            raise ValueError("busy_timeout_ms must be bounded between 1 and 30000")
        if _test_database_path is None:
            policy = SQLiteAuthorizationConsumptionPathPolicy.production(
                repository_root=repository_root, home=home, ownership_identity=ownership_identity
            )
            database_path = policy.production_path()
        else:
            test_path = Path(_test_database_path)
            policy = SQLiteAuthorizationConsumptionPathPolicy.isolated_test(
                repository_root=repository_root, test_root=test_path.parent
                , ownership_identity=ownership_identity
            )
            database_path = policy.validate(test_path)
        self._database_path = database_path
        self._busy_timeout_ms = busy_timeout_ms
        self._fault = _fault
        self._clock = _clock or (lambda: datetime.now(timezone.utc))
        try:
            policy.prepare(database_path)
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
            policy.secure_database(database_path)
        except (OSError, sqlite3.DatabaseError, SQLiteSchemaError) as exc:
            if isinstance(exc, SQLiteSchemaError):
                raise
            raise SQLiteAuthorizationConsumptionError("cannot initialize durable evidence store") from exc

    @classmethod
    def for_test(
        cls,
        database_path: Path,
        *,
        repository_root: Path,
        ownership_identity: SQLiteOwnershipIdentity,
        busy_timeout_ms: int = 1000,
        fault: Callable[[str, sqlite3.Connection], None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> "SQLiteAuthorizationConsumptionAdapter":
        return cls(
            repository_root=repository_root,
            ownership_identity=ownership_identity,
            busy_timeout_ms=busy_timeout_ms,
            _test_database_path=database_path,
            _fault=fault,
            _clock=clock,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path,
            timeout=self._busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _inject(self, stage: str, connection: sqlite3.Connection) -> None:
        if self._fault is not None:
            self._fault(stage, connection)

    @staticmethod
    def _row(connection: sqlite3.Connection, identifiers: tuple[str, ...]) -> tuple[object, ...] | None:
        return connection.execute(
            """SELECT lifecycle_id, authorization_id, mutation_budget_id, claim_id,
                      execution_request_id, authorization_request_id,
                      authorization_decision_id, consumption_binding_digest,
                      binding_json, barrier_state, committed_json, integrity_hash
                 FROM authorization_consumptions
                WHERE lifecycle_id=? OR authorization_id=? OR mutation_budget_id=?
                   OR claim_id=? OR execution_request_id=?
                   OR authorization_request_id=? OR authorization_decision_id=?""",
            identifiers,
        ).fetchone()

    def consume_once(self, command: AuthorizationConsumptionCommand) -> AuthorizationConsumptionResult:
        if type(command) is not AuthorizationConsumptionCommand:
            raise ValueError("command must be exactly AuthorizationConsumptionCommand")
        binding_json, binding_digest = encode_binding(command)
        authorization = command.authorization
        decision = authorization.decision
        assert authorization.authorization_id is not None and decision is not None
        identifiers = (
            authorization.request.lifecycle_id,
            authorization.authorization_id,
            command.mutation_budget.budget_id,
            command.execution_request.claim_id,
            command.execution_request.execution_request_id,
            authorization.request.request_id,
            decision.decision_id,
        )
        try:
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                existing = self._row(connection, identifiers)
                if existing is not None:
                    connection.rollback()
                    raise RepeatedAuthorizationConsumption(
                        "protected authorization identity was already durably consumed or claimed"
                    )
                connection.execute(
                    """INSERT INTO authorization_consumptions
                       (lifecycle_id, authorization_id, mutation_budget_id, claim_id,
                        execution_request_id, authorization_request_id,
                        authorization_decision_id, consumption_binding_digest,
                        binding_json, barrier_state)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DURABLY_CLAIMED')""",
                    (*identifiers, binding_digest, binding_json),
                )
                self._inject("before_claim_commit", connection)
                connection.commit()
        except RepeatedAuthorizationConsumption:
            raise
        except (sqlite3.DatabaseError, SQLiteSchemaError) as exc:
            raise SQLiteAuthorizationConsumptionError("durable claim failed closed") from exc

        consumed_at = self._clock()
        consumed_authorization = transition_authorization(
            authorization,
            AuthorizationState.CONSUMED,
            "ATOMIC_CONSUMPTION",
            consumed_at,
        ).authorization
        consumed_budget = consume_mutation_budget(command.mutation_budget)
        receipt_seed = {
            "codec_version": 1,
            "identifiers": list(identifiers),
            "consumption_binding_digest": binding_digest,
            "consumed_at": consumed_at.isoformat(),
        }
        receipt = GovernanceAuthorizationConsumptionReceipt(
            schema_version=authorization.request.schema_version,
            claim_id=command.execution_request.claim_id,
            lifecycle_id=authorization.request.lifecycle_id,
            authorization_id=authorization.authorization_id,
            mutation_budget_id=command.mutation_budget.budget_id,
            execution_request_id=command.execution_request.execution_request_id,
            consumed_at=consumed_at,
            transaction_status=ConsumptionTransactionStatus.COMMITTED,
            replay_sequence=0,
            replay_hash=digest_canonical(receipt_seed),
        )
        expected = AuthorizationConsumptionResult(
            consumed_authorization, consumed_budget, receipt, command.execution_request
        )
        committed_json, integrity_hash = encode_committed(expected, binding_digest)

        attempted_commit = False
        try:
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                row = self._row(connection, identifiers)
                if row is None or row[:9] != (*identifiers, binding_digest, binding_json) or row[9:] != (
                    "DURABLY_CLAIMED", None, None
                ):
                    connection.rollback()
                    raise SQLiteAuthorizationConsumptionError("durable claim is absent or inconsistent")
                self._inject("during_final_transaction", connection)
                connection.execute(
                    """UPDATE authorization_consumptions
                          SET barrier_state='COMMITTED', committed_json=?, integrity_hash=?
                        WHERE lifecycle_id=? AND barrier_state='DURABLY_CLAIMED'""",
                    (committed_json, integrity_hash, identifiers[0]),
                )
                self._inject("before_final_commit", connection)
                attempted_commit = True
                connection.commit()
                self._inject("after_final_commit", connection)
        except (sqlite3.DatabaseError, SQLiteSchemaError, SQLiteAuthorizationConsumptionError) as exc:
            if not attempted_commit:
                if isinstance(exc, SQLiteAuthorizationConsumptionError):
                    raise
                raise SQLiteAuthorizationConsumptionError("final consumption failed closed") from exc
            return self._reconcile_same_call(
                identifiers, binding_digest, binding_json, committed_json, integrity_hash, expected, exc
            )
        return self._validate_committed(
            identifiers, binding_digest, binding_json, committed_json, integrity_hash, expected
        )

    def _validate_committed(
        self,
        identifiers: tuple[str, ...],
        binding_digest: str,
        binding_json: str,
        committed_json: str,
        integrity_hash: str,
        expected: AuthorizationConsumptionResult,
    ) -> AuthorizationConsumptionResult:
        try:
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
                row = self._row(connection, identifiers)
        except (sqlite3.DatabaseError, SQLiteSchemaError) as exc:
            raise SQLiteAuthorizationConsumptionError("committed evidence cannot be read") from exc
        exact = (*identifiers, binding_digest, binding_json, "COMMITTED", committed_json, integrity_hash)
        if row != exact or digest_text(committed_json) != integrity_hash:
            raise SQLiteAuthorizationConsumptionError("committed evidence is not exact and complete")
        return expected

    def _reconcile_same_call(
        self,
        identifiers: tuple[str, ...],
        binding_digest: str,
        binding_json: str,
        committed_json: str,
        integrity_hash: str,
        expected: AuthorizationConsumptionResult,
        cause: BaseException,
    ) -> AuthorizationConsumptionResult:
        try:
            return self._validate_committed(
                identifiers, binding_digest, binding_json, committed_json, integrity_hash, expected
            )
        except SQLiteAuthorizationConsumptionError as exc:
            raise SQLiteAuthorizationConsumptionError(
                "ambiguous final commit could not be reconciled exactly"
            ) from cause


__all__ = ("SQLiteAuthorizationConsumptionAdapter", "SQLiteAuthorizationConsumptionError")
