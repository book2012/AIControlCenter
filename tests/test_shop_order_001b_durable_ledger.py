from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import sqlite3

import pytest

from core.shopping.order_core import (
    OrderCreateAmbiguousFailure, OrderCreateAuthority, OrderCreateCommand,
    OrderCreateDefinitiveFailure, OrderCreateLine, OrderCreateOperationConflict,
    OrderCreateOperationTerminalFailure, OrderCreateOperationUnknownOutcome,
    OrderCreateService, OrderLineItem, OrderSnapshot, SQLiteOrderCreateLedger,
)
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy


NOW=datetime(2026,10,5,10,0,tzinfo=timezone.utc)
CUSTOMER="AG-CUS-"+"1"*12+"4"+"1"*3+"8"+"1"*15
SESSION="AG-SES-"+"2"*12+"4"+"2"*3+"8"+"2"*15
SESSION2="AG-SES-"+"3"*12+"4"+"3"*3+"8"+"3"*15


class Clock:
    def __init__(self): self.value=NOW
    def __call__(self): return self.value
    def tick(self,seconds=1): self.value+=timedelta(seconds=seconds)


def authority(*,session=SESSION):
    return OrderCreateAuthority(
        customer_id=CUSTOMER,session_id=session,authorization_reference="auth-001",
        authorized_at=NOW,expires_at=NOW+timedelta(minutes=10),
    )


def command(*,key="order-001",quantity=1):
    return OrderCreateCommand(
        customer_id=CUSTOMER,line_items=(OrderCreateLine("mock-001",None,quantity),),
        idempotency_key=key,correlation_id="corr-001",audit_reference="audit-001",
        requested_at=NOW,
    )


def snapshot(order_id=501,*,quantity=1):
    return OrderSnapshot(
        provider="woocommerce",provider_order_id=order_id,
        provider_reference=f"woocommerce:order:{order_id}",order_number=str(order_id),
        status="pending",currency="KRW",customer_reference=None,
        line_items=(OrderLineItem(7001,901,0,None,"Canonical Product",quantity,
                                  Decimal("10000"),Decimal("10000"),Decimal("0")),),
        total=Decimal("10000"),total_tax=Decimal("0"),created_at=NOW,updated_at=NOW,
        provider_version="test",
    )


class FakeResolved:
    def __init__(self, quantity=1):
        self.customer_id=CUSTOMER
        self.line_items=(type("Line",(),{
            "product_id":"mock-001","variation_id":None,
            "provider_product_id":901,"provider_variation_id":0,"quantity":quantity,
        })(),)


class FakeResolver:
    def resolve(self,value): return FakeResolved(value.line_items[0].quantity)


class FakeWriter:
    def __init__(self,result=None,error=None):
        self.result=result if result is not None else snapshot();self.error=error;self.calls=[]
    def create_order(self,value):
        self.calls.append(value)
        if self.error: raise self.error
        return self.result


def ledger(tmp_path,clock):
    value=SQLiteOrderCreateLedger(
        tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path),
    )
    value.initialize();return value


def test_claim_is_durable_and_completed_replay_survives_new_instance(tmp_path):
    clock=Clock(); first=ledger(tmp_path,clock); writer=FakeWriter()
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=first)
    result=service.execute(command(),authority())
    assert result.snapshot.provider_order_id==501 and len(writer.calls)==1
    clock.tick()
    second=SQLiteOrderCreateLedger(tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    replay=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=second).execute(command(),authority())
    assert replay.idempotent_replay is True and replay.snapshot==result.snapshot
    assert len(writer.calls)==1


def test_same_key_different_command_or_session_conflicts_before_writer(tmp_path):
    clock=Clock(); store=ledger(tmp_path,clock); writer=FakeWriter()
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=store)
    service.execute(command(key="same"),authority())
    with pytest.raises(OrderCreateOperationConflict):
        service.execute(command(key="same",quantity=2),authority())
    with pytest.raises(OrderCreateOperationConflict):
        service.execute(command(key="same"),authority(session=SESSION2))
    assert len(writer.calls)==1



def test_same_session_can_replay_with_refreshed_authority_evidence(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock);writer=FakeWriter()
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=store)
    first=service.execute(command(),authority())
    refreshed=OrderCreateAuthority(
        customer_id=CUSTOMER,session_id=SESSION,authorization_reference="auth-002",
        authorized_at=NOW,expires_at=NOW+timedelta(minutes=9),
    )
    replay=service.execute(command(),refreshed)
    assert first.idempotent_replay is False and replay.idempotent_replay is True
    assert replay.snapshot==first.snapshot and len(writer.calls)==1


def test_concurrent_exact_claims_allow_one_claim_and_one_inflight(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    clock=Clock();store=ledger(tmp_path,clock);cmd=command();auth=authority()
    def attempt():
        try:
            return store.claim(cmd,auth).status.value
        except Exception as exc:
            return type(exc).__name__
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=sorted(pool.map(lambda _: attempt(), range(2)))
    assert results==["CLAIMED","OrderCreateOperationInFlight"]

def test_ambiguous_failure_persists_unknown_outcome_across_restart(tmp_path):
    clock=Clock(); store=ledger(tmp_path,clock)
    writer=FakeWriter(error=OrderCreateAmbiguousFailure("TIMEOUT_UNKNOWN"))
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=store)
    with pytest.raises(OrderCreateAmbiguousFailure): service.execute(command(),authority())
    assert store.inspect_operation("order-001")["state"]=="UNKNOWN_OUTCOME"
    second=SQLiteOrderCreateLedger(tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    with pytest.raises(OrderCreateOperationUnknownOutcome):
        OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=second).execute(command(),authority())
    assert len(writer.calls)==1


def test_unclassified_postwrite_contract_failure_is_unknown_not_terminal(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock);writer=FakeWriter(result=snapshot(quantity=2))
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=store)
    with pytest.raises(Exception,match="LINE_ITEMS_MISMATCH"): service.execute(command(),authority())
    assert store.inspect_operation("order-001")["state"]=="UNKNOWN_OUTCOME"
    assert len(writer.calls)==1


def test_definitive_no_write_failure_is_terminal_and_durable(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock)
    writer=FakeWriter(error=OrderCreateDefinitiveFailure("PROVIDER_REJECTED"))
    service=OrderCreateService(catalog_resolver=FakeResolver(),order_creator=writer,coordinator=store)
    with pytest.raises(OrderCreateDefinitiveFailure): service.execute(command(),authority())
    assert store.inspect_operation("order-001")["state"]=="TERMINAL_FAILED"
    with pytest.raises(OrderCreateOperationTerminalFailure): service.execute(command(),authority())
    assert len(writer.calls)==1


def test_unknown_outcome_requires_explicit_reconciliation_before_replay(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock);cmd=command();auth=authority()
    claim=store.claim(cmd,auth); assert claim.status.value=="CLAIMED"
    store.unknown(cmd.idempotency_key,cmd.command_digest,"TIMEOUT_UNKNOWN")
    with pytest.raises(OrderCreateOperationUnknownOutcome): store.claim(cmd,auth)
    result=__import__("core.shopping.order_core",fromlist=["OrderCreateResult"]).OrderCreateResult(
        customer_id=CUSTOMER,snapshot=snapshot(777),idempotency_key=cmd.idempotency_key,
        command_digest=cmd.command_digest,correlation_id=cmd.correlation_id,
        audit_reference=cmd.audit_reference,
    )
    clock.tick();store.reconcile_completed(cmd.idempotency_key,cmd.command_digest,result)
    replay=store.claim(cmd,auth)
    assert replay.status.value=="COMPLETED" and replay.result.snapshot.provider_order_id==777


def test_operation_identity_and_audit_are_immutable_and_delete_denied(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock);cmd=command();store.claim(cmd,authority())
    path=tmp_path/"orders.sqlite3"; connection=sqlite3.connect(path)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("UPDATE shopping_order_create_operations SET customer_id='x' WHERE operation_key=?",
                               (cmd.idempotency_key,))
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM shopping_order_create_operations WHERE operation_key=?",
                               (cmd.idempotency_key,))
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM shopping_order_create_audit")
    finally: connection.close()


def test_schema_contains_no_contact_payment_or_secret_fields(tmp_path):
    clock=Clock();store=ledger(tmp_path,clock)
    connection=sqlite3.connect(tmp_path/"orders.sqlite3")
    try:
        columns={row[1] for row in connection.execute("PRAGMA table_info(shopping_order_create_operations)")}
    finally: connection.close()
    forbidden={"email","phone","address","billing","shipping","payment","secret","cookie","csrf"}
    assert forbidden.isdisjoint(columns)
    assert store.production_safe is True


def test_default_path_policy_rejects_temporary_order_ledger():
    with pytest.raises(ValueError, match="outside the Mac Control Plane policy|cannot traverse symlinks"):
        SQLiteOrderCreateLedger("/tmp/orders.sqlite3",clock=Clock())


def test_completion_persistence_failure_quarantines_provider_success(tmp_path):
    clock = Clock()
    store = ledger(tmp_path, clock)
    writer = FakeWriter()
    def fail_completion(*args):
        raise sqlite3.OperationalError("injected completion persistence failure")
    store.complete = fail_completion
    service = OrderCreateService(catalog_resolver=FakeResolver(), order_creator=writer, coordinator=store)
    with pytest.raises(sqlite3.OperationalError):
        service.execute(command(), authority())
    assert store.inspect_operation("order-001")["state"] == "UNKNOWN_OUTCOME"
    with pytest.raises(OrderCreateOperationUnknownOutcome):
        service.execute(command(), authority())
    assert len(writer.calls) == 1


@pytest.mark.parametrize("seconds", [-1, 600])
def test_claim_rejects_authority_not_current_at_ledger_clock(tmp_path, seconds):
    clock = Clock()
    store = ledger(tmp_path, clock)
    clock.tick(seconds)
    writer = FakeWriter()
    service = OrderCreateService(catalog_resolver=FakeResolver(), order_creator=writer, coordinator=store)
    with pytest.raises(Exception, match="authority:NOT_CURRENT"):
        service.execute(command(), authority())
    assert store.inspect_operation("order-001") is None
    assert writer.calls == []



def test_completion_committed_then_error_preserves_completed_replay(tmp_path):
    clock = Clock()
    store = ledger(tmp_path, clock)
    complete = store.complete
    writer = FakeWriter()
    def commit_then_error(*args):
        complete(*args)
        raise sqlite3.OperationalError("injected post-commit error")
    store.complete = commit_then_error
    service = OrderCreateService(catalog_resolver=FakeResolver(), order_creator=writer, coordinator=store)
    with pytest.raises(sqlite3.OperationalError):
        service.execute(command(), authority())
    assert store.inspect_operation("order-001")["state"] == "COMPLETED"
    assert service.execute(command(), authority()).idempotent_replay
    assert len(writer.calls) == 1


def test_completion_and_quarantine_failure_keep_claim_blocked(tmp_path):
    from core.shopping.order_core import OrderCreateOperationInFlight
    clock = Clock()
    store = ledger(tmp_path, clock)
    writer = FakeWriter()
    def fail_completion(*args):
        raise sqlite3.OperationalError("completion failure")
    def fail_quarantine(*args):
        raise sqlite3.OperationalError("quarantine failure")
    store.complete = fail_completion
    store.unknown = fail_quarantine
    service = OrderCreateService(catalog_resolver=FakeResolver(), order_creator=writer, coordinator=store)
    with pytest.raises(sqlite3.OperationalError, match="completion failure"):
        service.execute(command(), authority())
    assert store.inspect_operation("order-001")["state"] == "CLAIMED"
    with pytest.raises(OrderCreateOperationInFlight):
        service.execute(command(), authority())
    assert len(writer.calls) == 1
