"""Issuer-created, irreversible SQLite store for fixed WordPress restart-policy authority."""

from __future__ import annotations

import os
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.wordpress_restart_policy_authorization import (
    AuthorizationConsumptionState, ConsumptionFailure, AuthorizationError, ConsumptionState, WordPressRestartPolicyAuthorization,
    WordPressRestartPolicyConsumptionReceipt, WordPressRestartPolicyConsumptionResult,
    validate_authorization,
)

from core.shopping.wordpress_restart_policy_reconciliation import DENIED

APPLICATION_ID = 0x57314630
USER_VERSION = 1
_COMPONENTS = ("Library", "Application Support", "AIControlCenter", "authorization", "wordpress-restart-policy-01g1f0-authorization.sqlite3")
_FIELDS = tuple(WordPressRestartPolicyAuthorization.__dataclass_fields__)
_COLUMNS = ",".join(_FIELDS)
_DDL = """
CREATE TABLE wordpress_restart_policy_authorizations (
 authorization_id TEXT PRIMARY KEY NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 trusted_uid INTEGER NOT NULL, trusted_gid INTEGER NOT NULL,
 authoritative_work_item TEXT NOT NULL CHECK(authoritative_work_item='SHOP-SERVICE-START-01G1F0'),
 mutation_id TEXT NOT NULL CHECK(mutation_id='SHOP-SERVICE-START-01G1F0:WORDPRESS_RESTART_POLICY_RECONCILIATION'),
 profile TEXT NOT NULL CHECK(profile='aicontrolcenter-commerce'),
 profile_file TEXT NOT NULL CHECK(profile_file='/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml'),
 precondition_json TEXT NOT NULL,
 maximum_uses INTEGER NOT NULL CHECK(maximum_uses=1),
 lifecycle_authority INTEGER NOT NULL CHECK(lifecycle_authority=0),
 production_authority INTEGER NOT NULL CHECK(production_authority=0),
 ubuntu_authority INTEGER NOT NULL CHECK(ubuntu_authority=0),
 business_mutation_authority INTEGER NOT NULL CHECK(business_mutation_authority=0),
 wordpress_generation_recovery_allowed INTEGER NOT NULL CHECK(wordpress_generation_recovery_allowed=0),
 capability_authority INTEGER NOT NULL CHECK(capability_authority=0),
 verifier_authority INTEGER NOT NULL CHECK(verifier_authority=0),
 state TEXT NOT NULL CHECK(state IN ('AVAILABLE','DURABLY_CLAIMED','COMMITTED')),
 claimed_at TEXT, committed_at TEXT,
 CHECK((state='AVAILABLE' AND claimed_at IS NULL AND committed_at IS NULL) OR
 (state='DURABLY_CLAIMED' AND claimed_at IS NOT NULL AND committed_at IS NULL) OR
 (state='COMMITTED' AND claimed_at IS NOT NULL AND committed_at IS NOT NULL))
) STRICT;
"""

class WordPressRestartPolicyStoreError(RuntimeError): pass

def _fingerprint(db):
    return tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))

with sqlite3.connect(":memory:") as _db:
    _db.executescript(_DDL); _EXPECTED = _fingerprint(_db)

def _validate(db):
    try:
        if (db.execute("PRAGMA application_id").fetchone()[0], db.execute("PRAGMA user_version").fetchone()[0]) != (APPLICATION_ID, USER_VERSION) or _fingerprint(db) != _EXPECTED:
            raise WordPressRestartPolicyStoreError("foreign or corrupt schema")
        if tuple(db.execute("PRAGMA integrity_check")) != (("ok",),):
            raise WordPressRestartPolicyStoreError("database integrity failure")
    except sqlite3.DatabaseError as exc:
        raise WordPressRestartPolicyStoreError("schema validation failed") from exc

class WordPressRestartPolicyAuthorizationStore:
    def __init__(self): raise TypeError("use fixed issuer or open-existing boundary")

    @classmethod
    def _initialize_for_issuer(cls):
        home = resolve_trusted_mac_account_home(); owner = issue_trusted_ownership_expectation(home)
        return cls._create(Path(home.passwd_home).joinpath(*_COMPONENTS), owner.expected_uid, owner.expected_gid)

    @classmethod
    def open_existing(cls):
        home = resolve_trusted_mac_account_home(); owner = issue_trusted_ownership_expectation(home)
        return cls._open(Path(home.passwd_home).joinpath(*_COMPONENTS), owner.expected_uid, owner.expected_gid)

    @classmethod
    def _for_test(cls, path: Path, *, uid: int, gid: int, fault: Callable | None = None):
        return cls._create(path, uid, gid, fault, True)

    @classmethod
    def _open_existing_for_test(cls, path: Path, *, uid: int, gid: int):
        return cls._open(path, uid, gid, True)

    @classmethod
    def _create(cls, path, uid, gid, fault=None, test=False):
        value=object.__new__(cls); value._setup(Path(path), uid, gid, fault, test); return value

    @classmethod
    def _open(cls, path, uid, gid, test=False):
        value=object.__new__(cls); value._open_readonly(Path(path), uid, gid, test); return value

    @staticmethod
    def _safe(path, test):
        if not path.is_absolute() or ".." in path.parts or path.is_symlink() or (not test and path.parts[-len(_COMPONENTS):] != _COMPONENTS):
            raise WordPressRestartPolicyStoreError("unsafe database path")
        for parent in (path.parent, *path.parents):
            if parent.exists() and parent.is_symlink(): raise WordPressRestartPolicyStoreError("symlink path rejected")
            if parent == Path(path.anchor): break

    @staticmethod
    def _require(path, uid, gid, mode, directory):
        meta=path.stat(follow_symlinks=False)
        kind=stat.S_ISDIR(meta.st_mode) if directory else stat.S_ISREG(meta.st_mode)
        if (not directory and meta.st_nlink != 1) or not kind or stat.S_IMODE(meta.st_mode)!=mode or (meta.st_uid,meta.st_gid)!=(uid,gid):
            raise WordPressRestartPolicyStoreError("unsafe path ownership or mode")

    def _setup(self, path, uid, gid, fault, test):
        self._safe(path,test); path.parent.mkdir(parents=test,mode=0o700,exist_ok=True)
        self._require(path.parent,uid,gid,0o700,True)
        if path.exists(): self._require(path,uid,gid,0o600,False)
        self._path,self._uid,self._gid,self._fault=path,uid,gid,fault
        if not path.exists():
            flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|(getattr(os,"O_NOFOLLOW",0)); fd=os.open(path,flags,0o600); os.close(fd)
        with self._write() as db:
            if not _fingerprint(db):
                if (db.execute("PRAGMA application_id").fetchone()[0],db.execute("PRAGMA user_version").fetchone()[0])!=(0,0): raise WordPressRestartPolicyStoreError("foreign empty database")
                db.executescript(_DDL); db.execute(f"PRAGMA application_id={APPLICATION_ID}"); db.execute(f"PRAGMA user_version={USER_VERSION}")
            _validate(db)
        path.chmod(0o600); self._require(path,uid,gid,0o600,False)

    def _open_readonly(self,path,uid,gid,test):
        self._safe(path,test); self._require(path.parent,uid,gid,0o700,True); self._require(path,uid,gid,0o600,False)
        self._path,self._uid,self._gid,self._fault=path,uid,gid,None
        with self._read() as db:
            _validate(db); rows=db.execute("SELECT * FROM wordpress_restart_policy_authorizations WHERE state='AVAILABLE' AND expires_at>?",(datetime.now(timezone.utc).isoformat(),)).fetchall()
        if len(rows)!=1: raise AuthorizationError("exactly one available authorization required")
        validate_authorization(self._authorization(rows[0]),now=datetime.now(timezone.utc),uid=uid,gid=gid)

    def _write(self):
        self._safe(self._path, True)
        self._require(self._path.parent,self._uid,self._gid,0o700,True)
        self._require(self._path,self._uid,self._gid,0o600,False)
        db=sqlite3.connect(self._path,timeout=1,isolation_level=None); db.execute("PRAGMA busy_timeout=1000"); db.execute("PRAGMA journal_mode=DELETE"); db.execute("PRAGMA synchronous=FULL"); return db
    def _read(self): return sqlite3.connect(self._path.as_uri()+"?mode=ro&immutable=1",uri=True)
    def _inject(self,stage,db):
        if self._fault: self._fault(stage,db)

    def _issue(self, authorization):
        validate_authorization(authorization,now=datetime.now(timezone.utc),uid=self._uid,gid=self._gid)
        with self._write() as db:
            _validate(db); db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM wordpress_restart_policy_authorizations").fetchone(): raise AuthorizationError("mutation already issued; reissuance forbidden")
            placeholders=",".join("?" for _ in _FIELDS)
            db.execute(f"INSERT INTO wordpress_restart_policy_authorizations ({_COLUMNS},state,claimed_at,committed_at) VALUES ({placeholders},'AVAILABLE',NULL,NULL)",tuple(getattr(authorization,n) for n in _FIELDS)); db.commit()

    def consume(self, observe):
        progress = [AuthorizationConsumptionState.NOT_CONSUMED]
        try:
            return self._consume(progress, observe)
        except Exception:
            raise ConsumptionFailure(progress[0]) from None

    def _consume(self, progress, observe):
        now=datetime.now(timezone.utc); authorization=None
        try:
            with self._write() as db:
                _validate(db); db.execute("BEGIN IMMEDIATE"); rows=db.execute("SELECT * FROM wordpress_restart_policy_authorizations WHERE state='AVAILABLE' AND expires_at>?",(now.isoformat(),)).fetchall()
                if len(rows)!=1: raise AuthorizationError("exactly one available authorization required")
                authorization=self._authorization(rows[0]); validate_authorization(authorization,now=now,uid=self._uid,gid=self._gid)
                # Observe inside the durable claim transaction, before any consumption.
                from core.shopping.wordpress_restart_policy_reconciliation import canonical_snapshot
                if canonical_snapshot(observe()) != authorization.precondition_json:
                    raise AuthorizationError("authorization-bound identity drift")
                validate_authorization(authorization, now=datetime.now(timezone.utc), uid=self._uid, gid=self._gid)
                if db.execute("UPDATE wordpress_restart_policy_authorizations SET state='DURABLY_CLAIMED',claimed_at=? WHERE authorization_id=? AND state='AVAILABLE'",(now.isoformat(),authorization.authorization_id)).rowcount!=1: raise AuthorizationError("authorization claim lost")
                self._inject("before_claim_commit",db)
                progress[0] = AuthorizationConsumptionState.UNCERTAIN
                db.commit()
                progress[0] = AuthorizationConsumptionState.CONSUMED
            self._inject("after_claim_commit",db)
        except (sqlite3.DatabaseError,WordPressRestartPolicyStoreError) as exc: raise WordPressRestartPolicyStoreError("durable claim failed closed") from exc
        committed_at=datetime.now(timezone.utc).isoformat(); attempted=False
        try:
            with self._write() as db:
                _validate(db); db.execute("BEGIN IMMEDIATE"); self._inject("during_final_transaction",db)
                if db.execute("UPDATE wordpress_restart_policy_authorizations SET state='COMMITTED',committed_at=? WHERE authorization_id=? AND state='DURABLY_CLAIMED'",(committed_at,authorization.authorization_id)).rowcount!=1: raise WordPressRestartPolicyStoreError("claim inconsistent")
                self._inject("before_final_commit",db); attempted=True; db.commit(); self._inject("after_final_commit",db)
        except (sqlite3.DatabaseError,WordPressRestartPolicyStoreError) as exc:
            if not attempted or not self._exact(authorization,committed_at): raise WordPressRestartPolicyStoreError("final commit failed closed") from exc
        if not self._exact(authorization,committed_at): raise WordPressRestartPolicyStoreError("committed read-back failed")
        return self._result(authorization)

    def _exact(self,authorization,committed_at):
        try:
            with self._read() as db: _validate(db); row=db.execute("SELECT * FROM wordpress_restart_policy_authorizations WHERE authorization_id=?",(authorization.authorization_id,)).fetchone()
            if not row:
                return False
            expected = [getattr(authorization, name) for name in _FIELDS]
            for name in DENIED:
                expected[_FIELDS.index(name)] = 0
            return bool(
                all(type(actual) is type(wanted) and actual == wanted
                    for actual, wanted in zip(row[:len(_FIELDS)], expected))
                and row[len(_FIELDS)] == "COMMITTED"
                and type(row[-2]) is str
                and row[-1] == committed_at
            )
        except Exception: return False

    @staticmethod
    def _authorization(row):
        fields = dict(zip(_FIELDS, row))
        if type(fields["maximum_uses"]) is not int or fields["maximum_uses"] != 1:
            raise WordPressRestartPolicyStoreError("invalid maximum uses in durable row")
        for name in DENIED:
            if type(fields[name]) is not int or fields[name] != 0:
                raise WordPressRestartPolicyStoreError(
                    f"invalid {name} in durable row"
                )
            fields[name] = False
        value=object.__new__(WordPressRestartPolicyAuthorization)
        for name in _FIELDS:
            object.__setattr__(value, name, fields[name])
        return value
    @staticmethod
    def _result(auth):
        receipt=object.__new__(WordPressRestartPolicyConsumptionReceipt)
        for name in WordPressRestartPolicyConsumptionReceipt.__dataclass_fields__: object.__setattr__(receipt,name,ConsumptionState.COMMITTED if name=="state" else getattr(auth,name))
        result=object.__new__(WordPressRestartPolicyConsumptionResult); object.__setattr__(result,"receipt",receipt); return result

__all__=("WordPressRestartPolicyAuthorizationStore","WordPressRestartPolicyStoreError")
