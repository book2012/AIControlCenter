"""Dedicated irreversible SQLite authority store for the fixed 01B mutation."""

from __future__ import annotations

import os
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.runtime_cutover_secret_source import SOURCE_ROLE, WORDPRESS_PORT_KEY
from core.shopping.runtime_cutover_source_authorization import (
    AUTHORITATIVE_WORK_ITEM, DESIRED_VALUE, ENVIRONMENT, MAXIMUM_USES, MUTATION_ID,
    AuthorizationError, ConsumptionState, SourceMutationAuthorization,
    SourceMutationConsumptionReceipt, SourceMutationConsumptionResult, validate_authorization,
)

APPLICATION_ID = 0x53524341  # SRCA
USER_VERSION = 1
_LEAF = "runtime-cutover-source-authorization.sqlite3"
_COMPONENTS = ("Library", "Application Support", "AIControlCenter", "authorization", _LEAF)
_DDL = """
CREATE TABLE source_mutation_authorizations (
 authorization_id TEXT PRIMARY KEY NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 trusted_uid INTEGER NOT NULL, trusted_gid INTEGER NOT NULL,
 authoritative_work_item TEXT NOT NULL CHECK(authoritative_work_item='SHOP-SERVICE-START-01B'),
 environment TEXT NOT NULL CHECK(environment='CONTROLLED_NON_PRODUCTION'),
 mutation_id TEXT NOT NULL CHECK(mutation_id='SHOP-SERVICE-START-01B:RUNTIME_CUTOVER_SOURCE_PORT_TO_58082'),
 source_role TEXT NOT NULL CHECK(source_role='runtime_cutover_variable_source'),
 source_key TEXT NOT NULL CHECK(source_key='SHOPPING_WORDPRESS_PORT'),
 desired_value TEXT NOT NULL CHECK(desired_value='58082'), maximum_uses INTEGER NOT NULL CHECK(maximum_uses=1),
 state TEXT NOT NULL CHECK(state IN ('AVAILABLE','DURABLY_CLAIMED','COMMITTED')),
 claimed_at TEXT, committed_at TEXT,
 CHECK((state='AVAILABLE' AND claimed_at IS NULL AND committed_at IS NULL) OR
       (state='DURABLY_CLAIMED' AND claimed_at IS NOT NULL AND committed_at IS NULL) OR
       (state='COMMITTED' AND claimed_at IS NOT NULL AND committed_at IS NOT NULL))
) STRICT;
"""


class SourceAuthorizationStoreError(RuntimeError):
    pass


def _schema_fingerprint(connection: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))


with sqlite3.connect(":memory:") as _reference:
    _reference.executescript(_DDL)
    _EXPECTED_SCHEMA = _schema_fingerprint(_reference)


def _validate_schema(connection: sqlite3.Connection) -> None:
    try:
        app_id = connection.execute("PRAGMA application_id").fetchone()[0]
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        objects = _schema_fingerprint(connection)
        if (app_id, version) != (APPLICATION_ID, USER_VERSION) or objects != _EXPECTED_SCHEMA:
            raise SourceAuthorizationStoreError("foreign or corrupt schema")
        if tuple(connection.execute("PRAGMA integrity_check")) != (("ok",),):
            raise SourceAuthorizationStoreError("database integrity failure")
    except sqlite3.DatabaseError as exc:
        raise SourceAuthorizationStoreError("schema validation failed") from exc


class RuntimeCutoverSourceAuthorizationStore:
    """Fixed store with separate issuer-create and consumer-open boundaries."""

    def __init__(self) -> None:
        raise TypeError("use the fixed issuer or open-existing boundary")

    @classmethod
    def _initialize_for_issuer(cls):
        """Create/harden the live store; callable only after issuer acknowledgement."""
        home = resolve_trusted_mac_account_home()
        ownership = issue_trusted_ownership_expectation(home)
        value = object.__new__(cls)
        value._initialize(Path(home.passwd_home).joinpath(*_COMPONENTS),
                          ownership.expected_uid, ownership.expected_gid, None)
        return value

    @classmethod
    def open_existing(cls):
        """Read-only discovery of one usable authorization in the fixed live store."""
        home = resolve_trusted_mac_account_home()
        ownership = issue_trusted_ownership_expectation(home)
        value = object.__new__(cls)
        value._open_existing(Path(home.passwd_home).joinpath(*_COMPONENTS),
                             ownership.expected_uid, ownership.expected_gid)
        return value

    @classmethod
    def _for_test(cls, path: Path, *, uid: int, gid: int,
                  fault: Callable[[str, sqlite3.Connection], None] | None = None):
        value = object.__new__(cls)
        value._initialize(path, uid, gid, fault, test=True)
        return value

    @classmethod
    def _open_existing_for_test(cls, path: Path, *, uid: int, gid: int):
        value = object.__new__(cls)
        value._open_existing(path, uid, gid, test=True)
        return value

    def _initialize(self, path: Path, uid: int, gid: int, fault=None, test=False) -> None:
        path = Path(path)
        if not path.is_absolute() or ".." in path.parts or path.is_symlink():
            raise SourceAuthorizationStoreError("unsafe database path")
        if not test and path.parts[-len(_COMPONENTS):] != _COMPONENTS:
            raise SourceAuthorizationStoreError("database path is not repository-fixed")
        for parent in (path.parent, *path.parents):
            if parent.exists() and parent.is_symlink():
                raise SourceAuthorizationStoreError("symlink path rejected")
            if parent == path.anchor:
                break
        path.parent.mkdir(parents=test, mode=0o700, exist_ok=True)
        path.parent.chmod(0o700)
        self._require(path.parent, uid, gid, 0o700, True)
        if path.exists():
            self._require(path, uid, gid, 0o600, False)
        self._path, self._uid, self._gid, self._fault = path, uid, gid, fault
        try:
            if not path.exists():
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                descriptor = os.open(path, flags, 0o600)
                os.close(descriptor)
            with self._connect_write() as connection:
                objects = _schema_fingerprint(connection)
                if not objects:
                    app_id = connection.execute("PRAGMA application_id").fetchone()[0]
                    version = connection.execute("PRAGMA user_version").fetchone()[0]
                    if (app_id, version) != (0, 0):
                        raise SourceAuthorizationStoreError("foreign empty database")
                    connection.executescript(_DDL)
                    connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
                    connection.execute(f"PRAGMA user_version={USER_VERSION}")
                _validate_schema(connection)
            path.chmod(0o600)
            self._require(path, uid, gid, 0o600, False)
        except (OSError, sqlite3.DatabaseError) as exc:
            raise SourceAuthorizationStoreError("store initialization failed") from exc

    def _open_existing(self, path: Path, uid: int, gid: int, test=False) -> None:
        path = Path(path)
        if not path.is_absolute() or ".." in path.parts or path.is_symlink():
            raise SourceAuthorizationStoreError("unsafe database path")
        if not test and path.parts[-len(_COMPONENTS):] != _COMPONENTS:
            raise SourceAuthorizationStoreError("database path is not repository-fixed")
        for parent in (path.parent, *path.parents):
            if parent.is_symlink():
                raise SourceAuthorizationStoreError("symlink path rejected")
            if parent == path.anchor:
                break
        try:
            self._require(path.parent, uid, gid, 0o700, True)
            self._require(path, uid, gid, 0o600, False)
            self._path, self._uid, self._gid, self._fault = path, uid, gid, None
            now = datetime.now(timezone.utc)
            with self._connect_readonly() as connection:
                _validate_schema(connection)
                rows = connection.execute(
                    "SELECT * FROM source_mutation_authorizations WHERE state='AVAILABLE' AND expires_at>?",
                    (now.isoformat(),)).fetchall()
            if len(rows) != 1:
                raise AuthorizationError("exactly one available authorization required")
            validate_authorization(self._authorization(rows[0]), now=now, uid=uid, gid=gid)
        except (OSError, sqlite3.DatabaseError) as exc:
            raise SourceAuthorizationStoreError("read-only authorization discovery failed") from exc

    @staticmethod
    def _require(path: Path, uid: int, gid: int, mode: int, directory: bool) -> None:
        metadata = path.stat(follow_symlinks=False)
        expected_kind = stat.S_ISDIR(metadata.st_mode) if directory else stat.S_ISREG(metadata.st_mode)
        if (not expected_kind or stat.S_IMODE(metadata.st_mode) != mode
                or (metadata.st_uid, metadata.st_gid) != (uid, gid)):
            raise SourceAuthorizationStoreError("unsafe path ownership or mode")

    def _connect_write(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=1, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=1000")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _connect_readonly(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path.as_uri() + "?mode=ro&immutable=1", uri=True)

    def _inject(self, stage: str, connection: sqlite3.Connection) -> None:
        if self._fault:
            self._fault(stage, connection)

    def _issue(self, authorization: SourceMutationAuthorization) -> None:
        validate_authorization(authorization, now=datetime.now(timezone.utc), uid=self._uid, gid=self._gid)
        values = tuple(getattr(authorization, name) for name in (
            "authorization_id", "issued_at", "expires_at", "trusted_uid", "trusted_gid",
            "authoritative_work_item", "environment", "mutation_id", "source_role", "source_key",
            "desired_value", "maximum_uses"))
        try:
            with self._connect_write() as connection:
                _validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                usable = connection.execute(
                    "SELECT 1 FROM source_mutation_authorizations WHERE state='AVAILABLE' AND expires_at>?",
                    (datetime.now(timezone.utc).isoformat(),)).fetchone()
                if usable:
                    raise AuthorizationError("an outstanding usable authorization already exists")
                connection.execute("INSERT INTO source_mutation_authorizations VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'AVAILABLE',NULL,NULL)", values)
                connection.commit()
        except (sqlite3.DatabaseError, SourceAuthorizationStoreError) as exc:
            raise SourceAuthorizationStoreError("authorization issuance failed") from exc

    def consume(self) -> SourceMutationConsumptionResult:
        now = datetime.now(timezone.utc)
        try:
            with self._connect_write() as connection:
                _validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                rows = connection.execute(
                    "SELECT * FROM source_mutation_authorizations WHERE state='AVAILABLE' AND expires_at>?",
                    (now.isoformat(),)).fetchall()
                if len(rows) != 1:
                    raise AuthorizationError("exactly one available authorization required")
                row = rows[0]
                authorization = self._authorization(row)
                validate_authorization(authorization, now=now, uid=self._uid, gid=self._gid)
                changed = connection.execute(
                    "UPDATE source_mutation_authorizations SET state='DURABLY_CLAIMED',claimed_at=? WHERE authorization_id=? AND state='AVAILABLE'",
                    (now.isoformat(), authorization.authorization_id)).rowcount
                if changed != 1:
                    raise AuthorizationError("authorization claim lost")
                self._inject("before_claim_commit", connection)
                connection.commit()
            self._inject("after_claim_commit", connection)
        except (sqlite3.DatabaseError, SourceAuthorizationStoreError) as exc:
            raise SourceAuthorizationStoreError("durable claim failed closed") from exc

        attempted = False
        committed_at = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect_write() as connection:
                _validate_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                self._inject("during_final_transaction", connection)
                changed = connection.execute(
                    "UPDATE source_mutation_authorizations SET state='COMMITTED',committed_at=? WHERE authorization_id=? AND state='DURABLY_CLAIMED'",
                    (committed_at, authorization.authorization_id)).rowcount
                if changed != 1:
                    raise SourceAuthorizationStoreError("claim is inconsistent")
                self._inject("before_final_commit", connection)
                attempted = True
                connection.commit()
                self._inject("after_final_commit", connection)
        except (sqlite3.DatabaseError, SourceAuthorizationStoreError) as exc:
            if not attempted or not self._is_exact_committed(authorization, committed_at):
                raise SourceAuthorizationStoreError("final commit failed closed") from exc
        if not self._is_exact_committed(authorization, committed_at):
            raise SourceAuthorizationStoreError("committed authorization read-back failed")
        return self._result(authorization)

    def _is_exact_committed(self, authorization: SourceMutationAuthorization, committed_at: str) -> bool:
        try:
            with self._connect_readonly() as connection:
                _validate_schema(connection)
                row = connection.execute(
                    "SELECT * FROM source_mutation_authorizations WHERE authorization_id=?",
                    (authorization.authorization_id,)).fetchone()
            expected_binding = tuple(getattr(authorization, name) for name in (
                "authorization_id", "issued_at", "expires_at", "trusted_uid", "trusted_gid",
                "authoritative_work_item", "environment", "mutation_id", "source_role", "source_key",
                "desired_value", "maximum_uses"))
            return bool(row and row[:12] == expected_binding and row[12] == "COMMITTED"
                        and type(row[13]) is str and row[14] == committed_at)
        except Exception:
            return False

    @staticmethod
    def _authorization(row) -> SourceMutationAuthorization:
        value = object.__new__(SourceMutationAuthorization)
        names = ("authorization_id", "issued_at", "expires_at", "trusted_uid", "trusted_gid",
                 "authoritative_work_item", "environment", "mutation_id", "source_role", "source_key",
                 "desired_value", "maximum_uses")
        for name, field in zip(names, row[:12]): object.__setattr__(value, name, field)
        object.__setattr__(value, "production_authority", False)
        object.__setattr__(value, "ubuntu_authority", False)
        return value

    @staticmethod
    def _result(authorization: SourceMutationAuthorization) -> SourceMutationConsumptionResult:
        receipt = object.__new__(SourceMutationConsumptionReceipt)
        for name in SourceMutationConsumptionReceipt.__dataclass_fields__:
            if name == "state": object.__setattr__(receipt, name, ConsumptionState.COMMITTED)
            else: object.__setattr__(receipt, name, getattr(authorization, name))
        result = object.__new__(SourceMutationConsumptionResult)
        object.__setattr__(result, "receipt", receipt)
        return result


__all__ = ("RuntimeCutoverSourceAuthorizationStore", "SourceAuthorizationStoreError")
