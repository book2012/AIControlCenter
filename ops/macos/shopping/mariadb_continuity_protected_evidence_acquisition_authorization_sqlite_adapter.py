"""Dedicated irreversible SQLite consumer for acquisition authorizations."""

from collections.abc import Callable
from pathlib import Path
import sqlite3

from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import (
    AcquisitionAuthorizationConsumptionState,
    AcquisitionAuthorizationError,
    ProtectedEvidenceAcquisitionAuthorization,
    ProtectedEvidenceAcquisitionAuthorizationConsumptionResult,
    ProtectedEvidenceAcquisitionConsumptionReceipt,
    ProtectedEvidenceAcquisitionRequest,
    ProtectedEvidenceHumanAuthorizationEvidence,
    ProtectedEvidenceHumanAuthorizationValidation,
    RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption,
    validate_acquisition_request,
)
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_codec import (
    digest_text, encode_binding, encode_committed,
)
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_path_policy import (
    ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity,
    ProtectedEvidenceAcquisitionSQLitePathPolicy,
)
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_schema import (
    ProtectedEvidenceAcquisitionSQLiteSchemaError, initialize_or_validate_schema,
)


class ProtectedEvidenceAcquisitionAuthorizationSQLiteError(RuntimeError):
    pass


PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE = False


class ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism:
    """Irreversible storage mechanism; it does not validate human authorization."""
    def __init__(self, *, repository_root: Path,
                 ownership_identity: ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity,
                 home: Path | None = None, busy_timeout_ms: int = 1000,
                 _test_database_path: Path | None = None,
                 _fault: Callable[[str, sqlite3.Connection], None] | None = None) -> None:
        if type(busy_timeout_ms) is not int or not 1 <= busy_timeout_ms <= 30_000:
            raise ValueError("busy_timeout_ms is invalid")
        if _test_database_path is None:
            if home is None:
                raise ValueError("explicit trusted home is required")
            policy = ProtectedEvidenceAcquisitionSQLitePathPolicy.production(
                repository_root=repository_root, home=home, ownership_identity=ownership_identity)
            path = policy.production_path()
        else:
            path = Path(_test_database_path)
            policy = ProtectedEvidenceAcquisitionSQLitePathPolicy.isolated_test(
                repository_root=repository_root, test_root=path.parent,
                ownership_identity=ownership_identity)
            path = policy.validate(path)
        self._database_path = path
        self._busy_timeout_ms = busy_timeout_ms
        self._fault = _fault
        try:
            policy.prepare(path)
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
            policy.secure_database(path)
        except (OSError, sqlite3.DatabaseError, ProtectedEvidenceAcquisitionSQLiteSchemaError) as exc:
            raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError("dedicated store initialization failed") from exc

    @classmethod
    def for_test(cls, database_path: Path, *, repository_root: Path,
                 ownership_identity: ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity,
                 busy_timeout_ms: int = 1000,
                 fault: Callable[[str, sqlite3.Connection], None] | None = None):
        return cls(repository_root=repository_root, ownership_identity=ownership_identity,
                   busy_timeout_ms=busy_timeout_ms, _test_database_path=database_path,
                   _fault=fault)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=self._busy_timeout_ms / 1000,
                                     isolation_level=None)
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _inject(self, stage: str, connection: sqlite3.Connection) -> None:
        if self._fault is not None:
            self._fault(stage, connection)

    @staticmethod
    def _row(connection: sqlite3.Connection, authorization_id: str,
             request_id: str) -> tuple[object, ...] | None:
        return connection.execute(
            """SELECT authorization_id,acquisition_request_id,fixed_source_slot_identity,
                      concrete_source_location_identity,leaf_basename,concrete_leaf_path,
                      maximum_acquisition_attempts,binding_digest,barrier_state,
                      committed_json,committed_digest
                 FROM protected_evidence_acquisition_authorization_consumptions
                WHERE authorization_id=? OR acquisition_request_id=?""",
            (authorization_id, request_id)).fetchone()

    @staticmethod
    def _validate_authorization(value: ProtectedEvidenceAcquisitionAuthorization) -> None:
        if type(value) is not ProtectedEvidenceAcquisitionAuthorization:
            raise AcquisitionAuthorizationError("authorization has an invalid type")
        if type(value.authorization_id) is not str or not value.authorization_id:
            raise AcquisitionAuthorizationError("authorization id is invalid")
        if value.maximum_acquisition_attempts != 1:
            raise AcquisitionAuthorizationError("authorization attempt count is invalid")
        request = object.__new__(ProtectedEvidenceAcquisitionRequest)
        for name in ("acquisition_request_id", "fixed_source_slot_identity",
                     "concrete_source_location_identity", "leaf_basename", "concrete_parent_path", "concrete_leaf_path"):
            object.__setattr__(request, name, getattr(value, name))
        object.__setattr__(request, "_repository_composed_concrete_leaf_path", value.concrete_leaf_path)
        validate_acquisition_request(request)

    def consume_durably(self, authorization: ProtectedEvidenceAcquisitionAuthorization,
                        ) -> ProtectedEvidenceAcquisitionAuthorizationConsumptionResult:
        self._validate_authorization(authorization)
        _, binding_digest = encode_binding(authorization)
        identifiers = (authorization.authorization_id, authorization.acquisition_request_id)
        values = (*identifiers, authorization.fixed_source_slot_identity.value,
                  authorization.concrete_source_location_identity.value,
                  authorization.leaf_basename, authorization.concrete_leaf_path,
                  authorization.maximum_acquisition_attempts, binding_digest)
        try:
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                if self._row(connection, *identifiers) is not None:
                    connection.rollback()
                    raise RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption(
                        "authorization or request was already permanently exhausted")
                connection.execute(
                    """INSERT INTO protected_evidence_acquisition_authorization_consumptions
                       (authorization_id,acquisition_request_id,fixed_source_slot_identity,
                        concrete_source_location_identity,leaf_basename,concrete_leaf_path,
                        maximum_acquisition_attempts,binding_digest,barrier_state)
                       VALUES (?,?,?,?,?,?,?,?, 'DURABLY_CLAIMED')""", values)
                self._inject("before_claim_commit", connection)
                connection.commit()
        except RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption:
            raise
        except (sqlite3.DatabaseError, ProtectedEvidenceAcquisitionSQLiteSchemaError) as exc:
            raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError(
                "durable claim failed closed") from exc

        committed_json, committed_digest = encode_committed(binding_digest)
        expected_row = (*values, "COMMITTED", committed_json, committed_digest)
        attempted_commit = False
        try:
            with self._connect() as connection:
                initialize_or_validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                row = self._row(connection, *identifiers)
                if row != (*values, "DURABLY_CLAIMED", None, None):
                    connection.rollback()
                    raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError(
                        "durable claim binding is inconsistent")
                self._inject("during_final_transaction", connection)
                connection.execute(
                    """UPDATE protected_evidence_acquisition_authorization_consumptions
                          SET barrier_state='COMMITTED',committed_json=?,committed_digest=?
                        WHERE authorization_id=? AND barrier_state='DURABLY_CLAIMED'""",
                    (committed_json, committed_digest, authorization.authorization_id))
                self._inject("before_final_commit", connection)
                attempted_commit = True
                connection.commit()
                self._inject("after_final_commit", connection)
        except (sqlite3.DatabaseError, ProtectedEvidenceAcquisitionSQLiteSchemaError,
                ProtectedEvidenceAcquisitionAuthorizationSQLiteError) as exc:
            if not attempted_commit:
                if isinstance(exc, ProtectedEvidenceAcquisitionAuthorizationSQLiteError):
                    raise
                raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError(
                    "final commit failed closed") from exc
            self._reconcile_same_call(identifiers, expected_row, exc)
        else:
            self._validate_committed(identifiers, expected_row)
        return self._result_after_validated_commit(
            authorization, binding_digest, committed_digest)

    def _validate_committed(self, identifiers: tuple[str, str], expected_row: tuple[object, ...],
                            ) -> None:
        try:
            uri = self._database_path.as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True) as connection:
                initialize_or_validate_schema(connection)
                row = self._row(connection, *identifiers)
        except (sqlite3.DatabaseError, ProtectedEvidenceAcquisitionSQLiteSchemaError) as exc:
            raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError("committed receipt is unreadable") from exc
        if row != expected_row or digest_text(expected_row[-2]) != expected_row[-1]:
            raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError("committed receipt binding is inconsistent")
        return None

    def _reconcile_same_call(self, identifiers, expected_row, cause):
        try:
            self._validate_committed(identifiers, expected_row)
        except ProtectedEvidenceAcquisitionAuthorizationSQLiteError:
            raise ProtectedEvidenceAcquisitionAuthorizationSQLiteError(
                "same-call ambiguous final commit did not reconcile") from cause

    @staticmethod
    def _result_after_validated_commit(authorization, binding_digest, committed_digest):
        receipt = object.__new__(ProtectedEvidenceAcquisitionConsumptionReceipt)
        for name in ("authorization_id", "acquisition_request_id", "fixed_source_slot_identity",
                     "concrete_source_location_identity", "leaf_basename", "concrete_parent_path",
                     "concrete_leaf_path", "maximum_acquisition_attempts"):
            object.__setattr__(receipt, name, getattr(authorization, name))
        object.__setattr__(receipt, "state", AcquisitionAuthorizationConsumptionState.COMMITTED)
        object.__setattr__(receipt, "binding_digest", binding_digest)
        object.__setattr__(receipt, "committed_digest", committed_digest)
        result = object.__new__(ProtectedEvidenceAcquisitionAuthorizationConsumptionResult)
        object.__setattr__(result, "receipt", receipt)
        return result


class ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter(
        ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism):
    """Production facade; unavailable until a trusted human issuer is composed."""

    def consume_once(self, authorization: ProtectedEvidenceAcquisitionAuthorization,
                     human_authorization_evidence: ProtectedEvidenceHumanAuthorizationEvidence,
                     human_authorization_validation: ProtectedEvidenceHumanAuthorizationValidation | None = None,
                     ) -> ProtectedEvidenceAcquisitionAuthorizationConsumptionResult:
        self._validate_authorization(authorization)
        if (type(human_authorization_evidence) is not ProtectedEvidenceHumanAuthorizationEvidence
                or human_authorization_evidence.authorization_id != authorization.authorization_id
                or human_authorization_evidence.acquisition_request_id != authorization.acquisition_request_id):
            raise AcquisitionAuthorizationError(
                "separate exactly-bound human authorization evidence is required")
        if (type(human_authorization_validation) is not ProtectedEvidenceHumanAuthorizationValidation
                or human_authorization_validation.authorization_id != authorization.authorization_id
                or human_authorization_validation.acquisition_request_id != authorization.acquisition_request_id
                or human_authorization_validation.production_authority is not True):
            raise AcquisitionAuthorizationError(
                "separate exactly-bound human authorization validation is required")
        # A caller-controlled boolean is factual data, not trusted authority.
        raise AcquisitionAuthorizationError(
            "no trusted Production human-authorization issuer is available")


__all__ = (
    "PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE",
    "ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism",
    "ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter",
    "ProtectedEvidenceAcquisitionAuthorizationSQLiteError",
)
