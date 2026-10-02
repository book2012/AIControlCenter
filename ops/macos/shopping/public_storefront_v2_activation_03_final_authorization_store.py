"""Durable, issuer-created SQLite store for PUBLIC-STOREFRONT-V2-ACTIVATION-01."""

from __future__ import annotations

import os
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.public_storefront_v2_activation_03_final_authorization import (
    AuthorizationError, ConsumptionFailure, PublicStorefrontV2ActivationAuthorization,
    PublicStorefrontV2ActivationConsumptionReceipt, PublicStorefrontV2ActivationConsumptionResult,
    validate_authorization,
)
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import AUTHORITY_ID, MAXIMUM_USES, parse_preconditions


APPLICATION_ID = 0x50535632
USER_VERSION = 1
_COMPONENTS = ("Library", "Application Support", "AIControlCenter", "authorization",
               "public-storefront-v2-activation-01-authorization.sqlite3")
_TABLE = "public_storefront_v2_activation_03_final_authorizations"
_FIELDS = tuple(PublicStorefrontV2ActivationAuthorization.__dataclass_fields__)
_COLUMNS = ",".join(_FIELDS)
_DDL = f"""
CREATE TABLE {_TABLE} (
 authorization_id TEXT PRIMARY KEY NOT NULL,
 issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 trusted_uid INTEGER NOT NULL, trusted_gid INTEGER NOT NULL,
 authority_id TEXT NOT NULL CHECK(authority_id='PUBLIC-STOREFRONT-V2-ACTIVATION-01'),
 authoritative_work_item TEXT NOT NULL CHECK(authoritative_work_item='PUBLIC-STOREFRONT-V2-ACTIVATION-01'),
 mutation_id TEXT NOT NULL CHECK(mutation_id='PUBLIC-STOREFRONT-V2-ACTIVATION-01:ONE_SHOT_PUBLIC_RUNTIME_AND_CADDY_ACTIVATION'),
 profile TEXT NOT NULL CHECK(profile='aicontrolcenter-commerce'),
 profile_file TEXT NOT NULL CHECK(profile_file='/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml'),
 source_head TEXT NOT NULL CHECK(length(source_head)=40),
 activation_bundle_sha256 TEXT NOT NULL CHECK(length(activation_bundle_sha256)=64),
 precondition_json TEXT NOT NULL, artifact_identities_json TEXT NOT NULL,
 expected_ports_json TEXT NOT NULL,
 maximum_uses INTEGER NOT NULL CHECK(maximum_uses=1),
 activation_authority INTEGER NOT NULL CHECK(activation_authority=1),
 lifecycle_authority INTEGER NOT NULL CHECK(lifecycle_authority=1),
 caddy_reload_authority INTEGER NOT NULL CHECK(caddy_reload_authority=1),
 production_write_authority INTEGER NOT NULL CHECK(production_write_authority=0),
 ubuntu_authority INTEGER NOT NULL CHECK(ubuntu_authority=0),
 business_mutation_authority INTEGER NOT NULL CHECK(business_mutation_authority=0),
 database_recreation_allowed INTEGER NOT NULL CHECK(database_recreation_allowed=0),
 volume_recreation_allowed INTEGER NOT NULL CHECK(volume_recreation_allowed=0),
 dns_change_allowed INTEGER NOT NULL CHECK(dns_change_allowed=0),
 woo_write_authority INTEGER NOT NULL CHECK(woo_write_authority=0),
 state TEXT NOT NULL CHECK(state IN ('AVAILABLE','DURABLY_CLAIMED','COMMITTED')),
 claimed_at TEXT, committed_at TEXT,
 CHECK((state='AVAILABLE' AND claimed_at IS NULL AND committed_at IS NULL) OR
       (state='DURABLY_CLAIMED' AND claimed_at IS NOT NULL AND committed_at IS NULL) OR
       (state='COMMITTED' AND claimed_at IS NOT NULL AND committed_at IS NOT NULL))
) STRICT;
"""


class PublicStorefrontV2ActivationStoreError(RuntimeError):
    pass


def _fingerprint(db: sqlite3.Connection):
    return tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))


with sqlite3.connect(":memory:") as _db:
    _db.executescript(_DDL)
    _EXPECTED = _fingerprint(_db)


def _validate_db(db: sqlite3.Connection) -> None:
    try:
        if (db.execute("PRAGMA application_id").fetchone()[0], db.execute("PRAGMA user_version").fetchone()[0]) != (APPLICATION_ID, USER_VERSION):
            raise PublicStorefrontV2ActivationStoreError("foreign schema")
        if _fingerprint(db) != _EXPECTED or tuple(db.execute("PRAGMA integrity_check")) != (("ok",),):
            raise PublicStorefrontV2ActivationStoreError("corrupt schema")
    except sqlite3.DatabaseError as exc:
        raise PublicStorefrontV2ActivationStoreError("schema validation failed") from exc


class PublicStorefrontV2ActivationAuthorizationStore:
    def __init__(self):
        raise TypeError("use the fixed issuer or open-existing boundary")

    @classmethod
    def _initialize_for_issuer(cls):
        home = resolve_trusted_mac_account_home()
        owner = issue_trusted_ownership_expectation(home)
        return cls._create(Path(home.passwd_home).joinpath(*_COMPONENTS), owner.expected_uid, owner.expected_gid)

    @classmethod
    def open_existing(cls):
        home = resolve_trusted_mac_account_home()
        owner = issue_trusted_ownership_expectation(home)
        return cls._open(Path(home.passwd_home).joinpath(*_COMPONENTS), owner.expected_uid, owner.expected_gid)

    @classmethod
    def _for_test(cls, path: Path, *, uid: int, gid: int, fault: Callable | None = None):
        return cls._create(path, uid, gid, fault, test=True)

    @classmethod
    def _open_existing_for_test(cls, path: Path, *, uid: int, gid: int):
        return cls._open(path, uid, gid, test=True)

    @classmethod
    def _create(cls, path: Path, uid: int, gid: int, fault=None, test=False):
        value = object.__new__(cls)
        value._setup(path, uid, gid, fault, test)
        return value

    @classmethod
    def _open(cls, path: Path, uid: int, gid: int, test=False):
        value = object.__new__(cls)
        value._open_readonly(path, uid, gid, test)
        return value

    @staticmethod
    def _safe(path: Path, test: bool) -> None:
        if (not path.is_absolute() or ".." in path.parts or path.is_symlink() or
                (not test and path.parts[-len(_COMPONENTS):] != _COMPONENTS)):
            raise PublicStorefrontV2ActivationStoreError("unsafe database path")
        for parent in (path.parent, *path.parents):
            if parent.exists() and parent.is_symlink():
                raise PublicStorefrontV2ActivationStoreError("symlink path rejected")
            if parent == Path(path.anchor):
                break

    @staticmethod
    def _require(path: Path, uid: int, gid: int, mode: int, directory: bool) -> None:
        meta = path.stat(follow_symlinks=False)
        kind = stat.S_ISDIR(meta.st_mode) if directory else stat.S_ISREG(meta.st_mode)
        if (not kind or (not directory and meta.st_nlink != 1) or stat.S_IMODE(meta.st_mode) != mode or
                (meta.st_uid, meta.st_gid) != (uid, gid)):
            raise PublicStorefrontV2ActivationStoreError("unsafe path ownership or mode")

    def _setup(self, path: Path, uid: int, gid: int, fault, test: bool) -> None:
        self._safe(path, test)
        path.parent.mkdir(parents=test, mode=0o700, exist_ok=True)
        self._require(path.parent, uid, gid, 0o700, True)
        if path.exists():
            self._require(path, uid, gid, 0o600, False)
        self._path, self._uid, self._gid, self._fault = path, uid, gid, fault
        if not path.exists():
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(path, flags, 0o600)
            os.close(fd)
        with self._write() as db:
            if not _fingerprint(db):
                if (db.execute("PRAGMA application_id").fetchone()[0], db.execute("PRAGMA user_version").fetchone()[0]) != (0, 0):
                    raise PublicStorefrontV2ActivationStoreError("foreign empty database")
                db.executescript(_DDL)
                db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                db.execute(f"PRAGMA user_version={USER_VERSION}")
            _validate_db(db)
        path.chmod(0o600)
        self._require(path, uid, gid, 0o600, False)

    def _open_readonly(self, path: Path, uid: int, gid: int, test: bool) -> None:
        self._safe(path, test)
        self._require(path.parent, uid, gid, 0o700, True)
        self._require(path, uid, gid, 0o600, False)
        self._path, self._uid, self._gid, self._fault = path, uid, gid, None
        with self._read() as db:
            _validate_db(db)
            rows = db.execute(f"SELECT * FROM {_TABLE} WHERE state='AVAILABLE' AND expires_at>?", (datetime.now(timezone.utc).isoformat(),)).fetchall()
        if len(rows) != 1:
            raise AuthorizationError("exactly one available activation authorization required")
        validate_authorization(self._authorization(rows[0]), now=datetime.now(timezone.utc), uid=uid, gid=gid)

    def _write(self):
        self._safe(self._path, True)
        self._require(self._path.parent, self._uid, self._gid, 0o700, True)
        self._require(self._path, self._uid, self._gid, 0o600, False)
        db = sqlite3.connect(self._path, timeout=1, isolation_level=None)
        db.execute("PRAGMA busy_timeout=1000")
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _read(self):
        return sqlite3.connect(self._path.as_uri() + "?mode=ro&immutable=1", uri=True)

    def _inject(self, stage, db):
        if self._fault:
            self._fault(stage, db)

    def _issue(self, authorization: PublicStorefrontV2ActivationAuthorization) -> None:
        validate_authorization(authorization, now=datetime.now(timezone.utc), uid=self._uid, gid=self._gid)
        parse_preconditions(authorization.precondition_json)
        with self._write() as db:
            _validate_db(db)
            db.execute("BEGIN IMMEDIATE")
            if db.execute(f"SELECT 1 FROM {_TABLE}").fetchone():
                raise AuthorizationError("mutation already issued; reissuance forbidden")
            placeholders = ",".join("?" for _ in _FIELDS)
            db.execute(f"INSERT INTO {_TABLE} ({_COLUMNS},state,claimed_at,committed_at) VALUES ({placeholders},'AVAILABLE',NULL,NULL)", tuple(getattr(authorization, field) for field in _FIELDS))
            db.commit()

    def consume(self, observe):
        progress = ["NOT_CONSUMED"]
        try:
            return self._consume(progress, observe)
        except Exception:
            raise ConsumptionFailure(progress[0]) from None

    def _consume(self, progress, observe):
        now = datetime.now(timezone.utc)
        authorization = None
        with self._write() as db:
            _validate_db(db)
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute(f"SELECT * FROM {_TABLE} WHERE state='AVAILABLE' AND expires_at>?", (now.isoformat(),)).fetchall()
            if len(rows) != 1:
                raise AuthorizationError("exactly one available activation authorization required")
            authorization = self._authorization(rows[0])
            validate_authorization(authorization, now=now, uid=self._uid, gid=self._gid)
            if observe() != parse_preconditions(authorization.precondition_json):
                raise AuthorizationError("authorization-bound precondition drift")
            if db.execute(f"UPDATE {_TABLE} SET state='DURABLY_CLAIMED',claimed_at=? WHERE authorization_id=? AND state='AVAILABLE'", (now.isoformat(), authorization.authorization_id)).rowcount != 1:
                raise AuthorizationError("authorization claim lost")
            self._inject("before_claim_commit", db)
            progress[0] = "UNCERTAIN"
            db.commit()
            progress[0] = "CONSUMED"
        committed_at = datetime.now(timezone.utc).isoformat()
        attempted = False
        try:
            with self._write() as db:
                _validate_db(db)
                db.execute("BEGIN IMMEDIATE")
                if db.execute(f"UPDATE {_TABLE} SET state='COMMITTED',committed_at=? WHERE authorization_id=? AND state='DURABLY_CLAIMED'", (committed_at, authorization.authorization_id)).rowcount != 1:
                    raise PublicStorefrontV2ActivationStoreError("claim inconsistent")
                self._inject("before_final_commit", db)
                attempted = True
                db.commit()
                self._inject("after_final_commit", db)
        except Exception as exc:
            if not attempted or not self._exact(authorization, committed_at):
                raise PublicStorefrontV2ActivationStoreError("final commit failed closed") from exc
        if not self._exact(authorization, committed_at):
            raise PublicStorefrontV2ActivationStoreError("committed read-back failed")
        receipt = object.__new__(PublicStorefrontV2ActivationConsumptionReceipt)
        for name in PublicStorefrontV2ActivationConsumptionReceipt.__dataclass_fields__:
            object.__setattr__(receipt, name, "COMMITTED" if name == "state" else getattr(authorization, name))
        result = object.__new__(PublicStorefrontV2ActivationConsumptionResult)
        object.__setattr__(result, "receipt", receipt)
        return result

    def _exact(self, authorization, committed_at) -> bool:
        try:
            with self._read() as db:
                _validate_db(db)
                row = db.execute(f"SELECT * FROM {_TABLE} WHERE authorization_id=?", (authorization.authorization_id,)).fetchone()
            expected = [getattr(authorization, field) for field in _FIELDS]
            boolean_fields = {
                "activation_authority", "lifecycle_authority", "caddy_reload_authority",
                "production_write_authority", "ubuntu_authority", "business_mutation_authority",
                "database_recreation_allowed", "volume_recreation_allowed", "dns_change_allowed",
                "woo_write_authority",
            }
            exact = all(
                (type(actual) is int and actual == int(wanted)) if field in boolean_fields
                else type(actual) is type(wanted) and actual == wanted
                for field, actual, wanted in zip(_FIELDS, row[:len(_FIELDS)] if row else (), expected)
            )
            return bool(row and exact and
                        row[len(_FIELDS)] == "COMMITTED" and type(row[-1]) is str and row[-1] == committed_at)
        except Exception:
            return False

    @staticmethod
    def _authorization(row):
        fields = dict(zip(_FIELDS, row))
        if type(fields["maximum_uses"]) is not int or fields["maximum_uses"] != MAXIMUM_USES:
            raise PublicStorefrontV2ActivationStoreError("invalid maximum uses")
        for name in (
            "activation_authority", "lifecycle_authority", "caddy_reload_authority",
            "production_write_authority", "ubuntu_authority", "business_mutation_authority",
            "database_recreation_allowed", "volume_recreation_allowed", "dns_change_allowed",
            "woo_write_authority",
        ):
            if type(fields[name]) is not int or fields[name] not in (0, 1):
                raise PublicStorefrontV2ActivationStoreError("invalid boolean capability")
            fields[name] = bool(fields[name])
        value = object.__new__(PublicStorefrontV2ActivationAuthorization)
        for field in _FIELDS:
            object.__setattr__(value, field, fields[field])
        return value


__all__ = ("PublicStorefrontV2ActivationAuthorizationStore", "PublicStorefrontV2ActivationStoreError")
