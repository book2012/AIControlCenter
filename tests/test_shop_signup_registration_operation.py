from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import sqlite3

from core.shopping.signup_registration_operation import SignupRegistrationOperationService
from tests.test_shop_signup_email_and_claim import candidate, setup, verified_contact_pair


class FakeCustomerPort:
    """Memory-only customer adapter. Never calls WooCommerce or any network."""

    def __init__(self, *, existing=(), unknown_after_write=False, lookup_error=False, reconcile="FOUND"):
        self.existing = set(existing)
        self.unknown_after_write = unknown_after_write
        self.lookup_error = lookup_error
        self.reconcile_state = reconcile
        self.lookups, self.creates, self.readbacks, self.reconciliations = [], [], [], []
        self.customers = {}

    def _exists(self, kind, value):
        self.lookups.append((kind, value))
        if self.lookup_error:
            raise TimeoutError("private")
        return (kind, value) in self.existing

    def username_exists(self, value):
        return self._exists("username", value)

    def email_exists(self, value):
        return self._exists("email", value)

    def phone_exists(self, value):
        return self._exists("phone", value)

    def create_customer(self, item, claim_ref):
        self.creates.append(claim_ref)
        self.customers[claim_ref] = ("fake-customer-0001", item.phone, item.email)
        if self.unknown_after_write:
            raise TimeoutError("private")
        return "fake-customer-0001"

    def customer_matches(self, provider_ref, item):
        self.readbacks.append(provider_ref)
        return any(ref == provider_ref and phone == item.phone and email == item.email
                   for ref, phone, email in self.customers.values())

    def find_by_claim(self, claim_ref):
        self.reconciliations.append(claim_ref)
        if self.reconcile_state == "UNKNOWN":
            return "UNKNOWN", None
        if self.reconcile_state == "ABSENT":
            return "ABSENT", None
        value = self.customers.get(claim_ref)
        return ("FOUND", value[0]) if value else ("ABSENT", None)


def claim_ready_signup(tmp_path):
    store, clock, pp, ep, phone, email, claim_service = setup(tmp_path)
    phone_ticket, email_ticket = verified_contact_pair(phone, email)
    claim = claim_service.claim(
        phone_ticket=phone_ticket, email_ticket=email_ticket,
        session_ref="session-binding-000001", idempotency_key="signup-operation-0001",
        candidate=candidate(),
    )
    assert claim.state == "CLAIMED"
    service_storage = SignupRegistrationOperationService(
        store=store, port=FakeCustomerPort(), clock=clock,
    )
    service_storage.initialize()
    return store, clock, claim, candidate(), service_storage


def test_duplicate_identity_uses_uniform_reply_checks_every_field_and_never_writes(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort(existing={("email", item.email)})
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    result = service.execute(claim_ref=claim.claim_ref, candidate=item)
    assert result.state == "NOT_COMPLETED"
    assert [kind for kind, _ in fake.lookups] == ["username", "email", "phone"]
    assert fake.creates == []
    with sqlite3.connect(store.path) as db:
        state = db.execute("SELECT lifecycle FROM signup_registration_claims").fetchone()[0]
    assert state == "DUPLICATE"


def test_identity_lookup_failure_fails_closed_without_write_or_claim_transition(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort(lookup_error=True)
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    assert service.execute(claim_ref=claim.claim_ref, candidate=item).state == "CHECK_UNAVAILABLE"
    assert fake.creates == []
    with sqlite3.connect(store.path) as db:
        state = db.execute("SELECT lifecycle FROM signup_registration_claims").fetchone()[0]
    assert state == "CLAIMED"


def test_success_creates_once_reads_back_and_replay_does_not_write_again(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort()
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    first = service.execute(claim_ref=claim.claim_ref, candidate=item)
    second = service.execute(claim_ref=claim.claim_ref, candidate=item)
    assert first.state == "ACTIVE" and first.operation_ref
    assert second.state == "ACTIVE"
    assert len(fake.creates) == 1
    assert fake.readbacks == ["fake-customer-0001"]
    with sqlite3.connect(store.path) as db:
        state = db.execute("SELECT lifecycle FROM signup_registration_claims").fetchone()[0]
        operation = db.execute("SELECT lifecycle FROM signup_registration_operations").fetchone()[0]
    assert state == operation == "ACTIVE"


def test_ambiguous_write_is_quarantined_no_retry_then_reconciled_read_only(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort(unknown_after_write=True)
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    first = service.execute(claim_ref=claim.claim_ref, candidate=item)
    assert first.state == "UNKNOWN_OUTCOME"
    again = service.execute(claim_ref=claim.claim_ref, candidate=item)
    assert again.state == "UNKNOWN_OUTCOME"
    assert len(fake.creates) == 1
    reconciled = service.reconcile(
        operation_ref=first.operation_ref, claim_ref=claim.claim_ref, candidate=item,
    )
    assert reconciled.state == "ACTIVE"
    assert len(fake.creates) == 1
    assert fake.reconciliations == [claim.claim_ref]


def test_unknown_reconciliation_stays_quarantined_and_does_not_retry(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort(unknown_after_write=True, reconcile="UNKNOWN")
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    first = service.execute(claim_ref=claim.claim_ref, candidate=item)
    result = service.reconcile(
        operation_ref=first.operation_ref, claim_ref=claim.claim_ref, candidate=item,
    )
    assert result.state == "UNKNOWN_OUTCOME"
    assert fake.creates == [claim.claim_ref]


def test_definitive_absence_reconciles_failed_and_never_retries(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort(unknown_after_write=True, reconcile="ABSENT")
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    first = service.execute(claim_ref=claim.claim_ref, candidate=item)
    result = service.reconcile(
        operation_ref=first.operation_ref, claim_ref=claim.claim_ref, candidate=item,
    )
    assert result.state == "FAILED"
    assert service.execute(claim_ref=claim.claim_ref, candidate=item).state == "FAILED"
    assert len(fake.creates) == 1


def test_operation_persists_no_profile_or_password(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = FakeCustomerPort()
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    service.execute(claim_ref=claim.claim_ref, candidate=item)
    with sqlite3.connect(store.path) as db:
        serialized = " ".join(str(value) for table in
            ("signup_registration_claims", "signup_registration_operations")
            for row in db.execute(f"SELECT * FROM {table}") for value in row)
    for secret in ("customer@example.test", "+821012345678", "S3cure-pass-123",
                   "Kim Customer", "customer_1"):
        assert secret not in serialized

class BarrierCustomerPort(FakeCustomerPort):
    def __init__(self):
        super().__init__()
        self.barrier = Barrier(2)

    def username_exists(self, value):
        self.barrier.wait(timeout=2)
        return self._exists("username", value)


def test_concurrent_same_claim_dispatches_customer_write_once(tmp_path):
    store, clock, claim, item, _ = claim_ready_signup(tmp_path)
    fake = BarrierCustomerPort()
    service = SignupRegistrationOperationService(store=store, port=fake, clock=clock)
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(
            lambda _: service.execute(claim_ref=claim.claim_ref, candidate=item),
            range(2),
        ))
    assert len(fake.creates) == 1
    assert any(reply.state == "ACTIVE" for reply in replies)
    assert all(reply.state in {"ACTIVE", "DISPATCHING", "CREATE_ACCEPTED"} for reply in replies)
