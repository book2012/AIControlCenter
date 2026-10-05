"""SHOP_ORDER_001B durable SQLite order-create operation ledger."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import quote
from typing import Callable, Final

from core.shopping.product_drafts.persistence.path_policy import (
    DatabasePathPolicy, DEFAULT_DURABLE_PATH_POLICY,
)

from .create import (
    OrderCreateAuthority, OrderCreateClaim, OrderCreateClaimStatus, OrderCreateCommand,
    OrderCreateContractError, OrderCreateOperationConflict, OrderCreateOperationInFlight,
    OrderCreateOperationTerminalFailure, OrderCreateOperationUnknownOutcome,
    OrderCreateResult, _digest, _idempotency_key, _reason_code, _validate_authority,
)
from .domain import OrderLineItem, OrderSnapshot


APPLICATION_ID: Final[int] = 0x53484F52  # SHOR
SCHEMA_VERSION: Final[int] = 1
BUSY_TIMEOUT_MS: Final[int] = 2500
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class OrderLedgerError(RuntimeError):
    pass


def _utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise OrderCreateContractError("timestamp:UTC_REQUIRED")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise OrderLedgerError("stored timestamp is not UTC")
    return parsed


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _snapshot_document(snapshot: OrderSnapshot) -> dict[str, object]:
    return {
        "provider": snapshot.provider, "provider_order_id": snapshot.provider_order_id,
        "provider_reference": snapshot.provider_reference, "order_number": snapshot.order_number,
        "status": snapshot.status, "currency": snapshot.currency,
        "customer_reference": snapshot.customer_reference,
        "line_items": [
            {
                "provider_line_item_id": item.provider_line_item_id,
                "product_id": item.product_id, "variation_id": item.variation_id,
                "sku": item.sku, "name": item.name, "quantity": item.quantity,
                "subtotal": format(item.subtotal, "f"), "total": format(item.total, "f"),
                "total_tax": format(item.total_tax, "f"),
            } for item in snapshot.line_items
        ],
        "total": format(snapshot.total, "f"), "total_tax": format(snapshot.total_tax, "f"),
        "created_at": _utc(snapshot.created_at), "updated_at": _utc(snapshot.updated_at),
        "provider_version": snapshot.provider_version,
    }


def _result_json(result: OrderCreateResult) -> str:
    return _canonical_json({
        "customer_id": result.customer_id, "snapshot": _snapshot_document(result.snapshot),
        "idempotency_key": result.idempotency_key, "command_digest": result.command_digest,
        "correlation_id": result.correlation_id, "audit_reference": result.audit_reference,
    })


def _result_digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decode_result(raw: str) -> OrderCreateResult:
    try:
        data = json.loads(raw)
        snap = data["snapshot"]
        lines = tuple(
            OrderLineItem(
                provider_line_item_id=item["provider_line_item_id"], product_id=item["product_id"],
                variation_id=item["variation_id"], sku=item["sku"], name=item["name"],
                quantity=item["quantity"], subtotal=Decimal(item["subtotal"]),
                total=Decimal(item["total"]), total_tax=Decimal(item["total_tax"]),
            ) for item in snap["line_items"]
        )
        snapshot = OrderSnapshot(
            provider=snap["provider"], provider_order_id=snap["provider_order_id"],
            provider_reference=snap["provider_reference"], order_number=snap["order_number"],
            status=snap["status"], currency=snap["currency"],
            customer_reference=snap["customer_reference"], line_items=lines,
            total=Decimal(snap["total"]), total_tax=Decimal(snap["total_tax"]),
            created_at=_parse_utc(snap["created_at"]), updated_at=_parse_utc(snap["updated_at"]),
            provider_version=snap["provider_version"],
        )
        return OrderCreateResult(
            customer_id=data["customer_id"], snapshot=snapshot,
            idempotency_key=data["idempotency_key"], command_digest=data["command_digest"],
            correlation_id=data["correlation_id"], audit_reference=data["audit_reference"],
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise OrderLedgerError("stored order result is invalid") from exc


SCHEMA_SQL = """
CREATE TABLE order_ledger_metadata (
 schema_version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, component TEXT NOT NULL
);
CREATE TABLE shopping_order_create_operations (
 operation_key TEXT PRIMARY KEY, command_digest TEXT NOT NULL
   CHECK(length(command_digest)=64 AND command_digest NOT GLOB '*[^0-9a-f]*'),
 customer_id TEXT NOT NULL, session_id TEXT NOT NULL, authorization_reference TEXT NOT NULL,
 correlation_reference TEXT NOT NULL, audit_reference TEXT NOT NULL,
 requested_at TEXT NOT NULL, authorized_at TEXT NOT NULL, authority_expires_at TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('CLAIMED','COMPLETED','TERMINAL_FAILED','UNKNOWN_OUTCOME')),
 claimed_at TEXT NOT NULL, terminal_at TEXT, quarantined_at TEXT, reason_code TEXT,
 provider_order_id INTEGER, provider_reference TEXT, result_json TEXT, result_digest TEXT,
 CHECK(
   (state='CLAIMED' AND terminal_at IS NULL AND quarantined_at IS NULL AND reason_code IS NULL
      AND provider_order_id IS NULL AND provider_reference IS NULL AND result_json IS NULL AND result_digest IS NULL)
   OR
   (state='COMPLETED' AND terminal_at IS NOT NULL AND reason_code IS NULL
      AND provider_order_id IS NOT NULL AND provider_order_id > 0 AND provider_reference IS NOT NULL
      AND result_json IS NOT NULL AND json_valid(result_json) AND result_digest IS NOT NULL)
   OR
   (state='TERMINAL_FAILED' AND terminal_at IS NOT NULL AND reason_code IS NOT NULL
      AND provider_order_id IS NULL AND provider_reference IS NULL AND result_json IS NULL AND result_digest IS NULL)
   OR
   (state='UNKNOWN_OUTCOME' AND terminal_at IS NULL AND quarantined_at IS NOT NULL AND reason_code IS NOT NULL
      AND provider_order_id IS NULL AND provider_reference IS NULL AND result_json IS NULL AND result_digest IS NULL)
 )
) WITHOUT ROWID;
CREATE TRIGGER shopping_order_create_identity_immutable BEFORE UPDATE ON shopping_order_create_operations
WHEN OLD.operation_key != NEW.operation_key OR OLD.command_digest != NEW.command_digest
 OR OLD.customer_id != NEW.customer_id OR OLD.session_id != NEW.session_id
 OR OLD.authorization_reference != NEW.authorization_reference
 OR OLD.correlation_reference != NEW.correlation_reference OR OLD.audit_reference != NEW.audit_reference
 OR OLD.requested_at != NEW.requested_at OR OLD.authorized_at != NEW.authorized_at
 OR OLD.authority_expires_at != NEW.authority_expires_at OR OLD.claimed_at != NEW.claimed_at
BEGIN SELECT RAISE(ABORT, 'order operation identity is immutable'); END;
CREATE TRIGGER shopping_order_create_transition BEFORE UPDATE ON shopping_order_create_operations
WHEN NOT (
 (OLD.state='CLAIMED' AND NEW.state IN ('COMPLETED','TERMINAL_FAILED','UNKNOWN_OUTCOME'))
 OR (OLD.state='UNKNOWN_OUTCOME' AND NEW.state IN ('COMPLETED','TERMINAL_FAILED'))
)
BEGIN SELECT RAISE(ABORT, 'order operation transition is invalid'); END;
CREATE TRIGGER shopping_order_create_deny_delete BEFORE DELETE ON shopping_order_create_operations
BEGIN SELECT RAISE(ABORT, 'order operation cannot be deleted'); END;
CREATE TABLE shopping_order_create_audit (
 event_id TEXT PRIMARY KEY, operation_key TEXT NOT NULL, event_type TEXT NOT NULL,
 occurred_at TEXT NOT NULL, reason_code TEXT, provider_order_id INTEGER,
 provider_reference TEXT, result_digest TEXT,
 FOREIGN KEY(operation_key) REFERENCES shopping_order_create_operations(operation_key)
) WITHOUT ROWID;
CREATE INDEX shopping_order_create_audit_operation ON shopping_order_create_audit(operation_key, occurred_at);
CREATE TRIGGER shopping_order_create_audit_immutable BEFORE UPDATE ON shopping_order_create_audit
BEGIN SELECT RAISE(ABORT, 'order audit is immutable'); END;
CREATE TRIGGER shopping_order_create_audit_deny_delete BEFORE DELETE ON shopping_order_create_audit
BEGIN SELECT RAISE(ABORT, 'order audit cannot be deleted'); END;
"""


def _execute_schema(connection: sqlite3.Connection) -> None:
    statement = ""
    for line in SCHEMA_SQL.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement); statement = ""
    if statement.strip():
        raise OrderLedgerError("incomplete order ledger schema")


def _schema_digest(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index','trigger') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type,name"
    ).fetchall()
    material = "\n".join(
        f"{row[0]}|{row[1]}|{re.sub(r'\\s+', ' ', row[2].strip()).lower()}"
        for row in rows if row[2] is not None
    )
    return hashlib.sha256(material.encode()).hexdigest()


def _expected_schema_digest() -> str:
    connection = sqlite3.connect(":memory:")
    try:
        _execute_schema(connection)
        return _schema_digest(connection)
    finally:
        connection.close()


EXPECTED_SCHEMA_DIGEST = _expected_schema_digest()


class SQLiteOrderCreateLedger:
    production_safe = True

    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime],
                 path_policy: DatabasePathPolicy = DEFAULT_DURABLE_PATH_POLICY,
                 busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
        if not callable(clock):
            raise ValueError("an explicit UTC clock is required")
        if type(busy_timeout_ms) is not int or not 1 <= busy_timeout_ms <= 30000:
            raise ValueError("busy_timeout_ms is invalid")
        self.database_path = path_policy.validate(database_path)
        self._path_policy = path_policy
        self._clock = clock
        self.busy_timeout_ms = busy_timeout_ms

    def _now(self) -> datetime:
        value = self._clock()
        _utc(value)
        return value

    def _connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        path = self.database_path
        if read_only:
            if not path.is_file(): raise OrderLedgerError("order ledger does not exist")
            uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True, isolation_level=None,
                                         timeout=self.busy_timeout_ms / 1000)
        else:
            if not path.parent.is_dir():
                raise OrderLedgerError("order ledger parent directory must already exist")
            connection = sqlite3.connect(path, isolation_level=None,
                                         timeout=self.busy_timeout_ms / 1000)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        if read_only:
            connection.execute("PRAGMA query_only = ON")
        else:
            if str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).upper() != "WAL":
                connection.close(); raise OrderLedgerError("SQLite WAL mode is required")
            connection.execute("PRAGMA synchronous = FULL")
        return connection

    def initialize(self) -> None:
        connection = self._connect()
        try:
            app_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if app_id not in (0, APPLICATION_ID):
                raise OrderLedgerError("database belongs to another application")
            if version == SCHEMA_VERSION:
                self._validate(connection); return
            if version != 0:
                raise OrderLedgerError("unsupported order ledger schema version")
            existing = connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchone()
            if existing is not None:
                raise OrderLedgerError("unversioned non-empty database cannot be initialized silently")
            now = _utc(self._now())
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                _execute_schema(connection)
                connection.execute("INSERT INTO order_ledger_metadata VALUES (?,?,?)",
                                   (SCHEMA_VERSION, now, "SHOP_ORDER_001B"))
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                connection.commit()
            except Exception:
                if connection.in_transaction: connection.rollback()
                raise
            self._validate(connection)
        finally:
            connection.close()

    def _validate(self, connection: sqlite3.Connection) -> None:
        failures=[]
        if int(connection.execute("PRAGMA application_id").fetchone()[0]) != APPLICATION_ID:
            failures.append("application_id")
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != SCHEMA_VERSION:
            failures.append("user_version")
        if str(connection.execute("PRAGMA quick_check").fetchone()[0]) != "ok":
            failures.append("quick_check")
        if str(connection.execute("PRAGMA journal_mode").fetchone()[0]).upper() != "WAL":
            failures.append("journal_mode")
        if not bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]):
            failures.append("foreign_keys")
        if _schema_digest(connection) != EXPECTED_SCHEMA_DIGEST:
            failures.append("schema")
        metadata=tuple(tuple(row) for row in connection.execute(
            "SELECT schema_version,component FROM order_ledger_metadata ORDER BY schema_version"))
        if metadata != ((SCHEMA_VERSION, "SHOP_ORDER_001B"),): failures.append("metadata")
        if failures: raise OrderLedgerError("order ledger validation failed: "+",".join(failures))

    def _audit(self, connection: sqlite3.Connection, key: str, event_type: str, now: datetime,
               *, reason_code: str | None = None, result: OrderCreateResult | None = None) -> None:
        seed = f"{key}:{event_type}:{_utc(now)}:{reason_code or ''}:{result.command_digest if result else ''}"
        event_id = hashlib.sha256(seed.encode()).hexdigest()
        connection.execute(
            "INSERT INTO shopping_order_create_audit "
            "(event_id,operation_key,event_type,occurred_at,reason_code,provider_order_id,provider_reference,result_digest) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (event_id, key, event_type, _utc(now), reason_code,
             result.snapshot.provider_order_id if result else None,
             result.snapshot.provider_reference if result else None,
             _result_digest(_result_json(result)) if result else None),
        )

    def claim(self, command: OrderCreateCommand, authority: OrderCreateAuthority) -> OrderCreateClaim:
        if type(command) is not OrderCreateCommand: raise OrderCreateContractError("command:TYPE")
        _validate_authority(command, authority)
        now=self._now(); key=command.idempotency_key; digest=command.command_digest
        connection=self._connect()
        try:
            self._validate(connection); connection.execute("BEGIN IMMEDIATE")
            row=connection.execute("SELECT * FROM shopping_order_create_operations WHERE operation_key=?",
                                   (key,)).fetchone()
            binding=(digest, authority.customer_id, authority.session_id)
            if row is None:
                connection.execute(
                    "INSERT INTO shopping_order_create_operations "
                    "(operation_key,command_digest,customer_id,session_id,authorization_reference,"
                    "correlation_reference,audit_reference,requested_at,authorized_at,authority_expires_at,"
                    "state,claimed_at) VALUES (?,?,?,?,?,?,?,?,?,?,'CLAIMED',?)",
                    (key,digest,authority.customer_id,authority.session_id,authority.authorization_reference,
                     command.correlation_id,command.audit_reference,_utc(command.requested_at),
                     _utc(authority.authorized_at),_utc(authority.expires_at),_utc(now)),
                )
                self._audit(connection,key,"CLAIMED",now); connection.commit()
                return OrderCreateClaim(OrderCreateClaimStatus.CLAIMED)
            existing=(row["command_digest"], row["customer_id"], row["session_id"])
            if existing != binding:
                raise OrderCreateOperationConflict("idempotency key conflicts with another command or session")
            state=row["state"]
            if state=="COMPLETED":
                raw=row["result_json"]; digest_stored=row["result_digest"]
                if not isinstance(raw,str) or _result_digest(raw)!=digest_stored:
                    raise OrderLedgerError("completed order result digest is invalid")
                result=_decode_result(raw)
                if (result.command_digest,result.idempotency_key,result.customer_id) != (digest,key,authority.customer_id):
                    raise OrderLedgerError("completed order result binding is invalid")
                connection.rollback()
                return OrderCreateClaim(OrderCreateClaimStatus.COMPLETED,result)
            if state=="TERMINAL_FAILED": raise OrderCreateOperationTerminalFailure(row["reason_code"])
            if state=="UNKNOWN_OUTCOME": raise OrderCreateOperationUnknownOutcome(row["reason_code"])
            raise OrderCreateOperationInFlight("operation is already durably claimed")
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def _transition(self, key: str, command_digest: str, target: str, *,
                    reason_code: str | None = None, result: OrderCreateResult | None = None,
                    reconcile: bool = False) -> None:
        key=_idempotency_key(key); digest=_digest(command_digest)
        if reason_code is not None: reason_code=_reason_code(reason_code)
        now=self._now(); connection=self._connect()
        try:
            self._validate(connection); connection.execute("BEGIN IMMEDIATE")
            row=connection.execute("SELECT * FROM shopping_order_create_operations WHERE operation_key=?",
                                   (key,)).fetchone()
            expected="UNKNOWN_OUTCOME" if reconcile else "CLAIMED"
            if row is None or row["command_digest"]!=digest or row["state"]!=expected:
                raise RuntimeError(f"only the exact {expected} operation can transition")
            if target=="COMPLETED":
                if type(result) is not OrderCreateResult:
                    raise OrderCreateContractError("result:TYPE")
                if (result.idempotency_key,result.command_digest,result.customer_id) != (key,digest,row["customer_id"]):
                    raise OrderCreateContractError("result:BINDING_MISMATCH")
                raw=_result_json(result); rd=_result_digest(raw)
                connection.execute(
                    "UPDATE shopping_order_create_operations SET state='COMPLETED',terminal_at=?,reason_code=NULL,"
                    "provider_order_id=?,provider_reference=?,result_json=?,result_digest=? WHERE operation_key=?",
                    (_utc(now),result.snapshot.provider_order_id,result.snapshot.provider_reference,raw,rd,key))
                self._audit(connection,key,"RECONCILED_COMPLETED" if reconcile else "COMPLETED",now,result=result)
            elif target=="TERMINAL_FAILED":
                if reason_code is None: raise OrderCreateContractError("reason_code:REQUIRED")
                connection.execute(
                    "UPDATE shopping_order_create_operations SET state='TERMINAL_FAILED',terminal_at=?,reason_code=? "
                    "WHERE operation_key=?", (_utc(now),reason_code,key))
                self._audit(connection,key,"RECONCILED_FAILED" if reconcile else "TERMINAL_FAILED",now,
                            reason_code=reason_code)
            elif target=="UNKNOWN_OUTCOME":
                if reconcile or reason_code is None: raise OrderCreateContractError("unknown_transition:INVALID")
                connection.execute(
                    "UPDATE shopping_order_create_operations SET state='UNKNOWN_OUTCOME',quarantined_at=?,reason_code=? "
                    "WHERE operation_key=?", (_utc(now),reason_code,key))
                self._audit(connection,key,"UNKNOWN_OUTCOME",now,reason_code=reason_code)
            else: raise OrderCreateContractError("transition:INVALID")
            connection.commit()
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally: connection.close()

    def complete(self,key:str,command_digest:str,result:OrderCreateResult)->None:
        self._transition(key,command_digest,"COMPLETED",result=result)

    def fail(self,key:str,command_digest:str,reason_code:str)->None:
        self._transition(key,command_digest,"TERMINAL_FAILED",reason_code=reason_code)

    def unknown(self,key:str,command_digest:str,reason_code:str)->None:
        self._transition(key,command_digest,"UNKNOWN_OUTCOME",reason_code=reason_code)

    def reconcile_completed(self,key:str,command_digest:str,result:OrderCreateResult)->None:
        self._transition(key,command_digest,"COMPLETED",result=result,reconcile=True)

    def reconcile_failed(self,key:str,command_digest:str,reason_code:str)->None:
        self._transition(key,command_digest,"TERMINAL_FAILED",reason_code=reason_code,reconcile=True)

    def inspect_operation(self,key:str)->dict[str,object]|None:
        key=_idempotency_key(key); connection=self._connect(read_only=True)
        try:
            self._validate(connection)
            row=connection.execute("SELECT * FROM shopping_order_create_operations WHERE operation_key=?",
                                   (key,)).fetchone()
            if row is None:return None
            return {name:row[name] for name in row.keys() if name!="result_json"}
        finally: connection.close()


__all__=("APPLICATION_ID","BUSY_TIMEOUT_MS","EXPECTED_SCHEMA_DIGEST","OrderLedgerError",
         "SCHEMA_VERSION","SQLiteOrderCreateLedger")
