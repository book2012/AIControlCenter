"""Synthetic B3-E contracts and isolated legacy authorization regressions."""
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from core.shopping.migration_contract import (
    CONTRACT_VERSION, EXPECTED_CORE_TABLES, EXPECTED_OWNERSHIP_COLUMNS,
    EXPLICIT_UNOWNED_MARKER, PERSISTENCE_SCHEMA_VERSION,
    BackupRestoreEvidence, ClassificationEvidence, ContractValidation,
    DryRunEvidence, LegacyInquiryClassification, MigrationPrerequisites,
    OperationalApprovalGate, OwnershipEvidence, RollbackInvariants,
    SchemaEvidence, StopReason, SyntheticLegacyInquiry, ValidationOutcome,
    classify_legacy_inquiry, validate_classification_set,
    validate_migration_prerequisites,
)


@pytest.fixture(autouse=True)
def no_io(monkeypatch, tmp_path):
    attempts = []
    connect = sqlite3.connect

    def deny(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("only explicitly isolated synthetic I/O is permitted")

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", deny)
    monkeypatch.setattr(sqlite3, "connect", deny)

    def temporary_connect(database, *args, **kwargs):
        if (kwargs.get("uri") or not isinstance(database, (str, Path))
                or (database != ":memory:" and not
                    Path(database).resolve().is_relative_to(tmp_path.resolve()))):
            return deny()
        return connect(database, *args, **kwargs)

    assert "core.api.app" not in sys.modules
    # Pure contract tests retain the SQLite prohibition. Only legacy_api opts
    # into this guarded connector, restricted to this test's temporary path.
    yield temporary_connect
    assert not attempts
    assert "core.api.app" not in sys.modules


def schema(**updates):
    payload = dict(provenance="synthetic_fixture", version=PERSISTENCE_SCHEMA_VERSION,
                   tables=EXPECTED_CORE_TABLES, ownership_columns=EXPECTED_OWNERSHIP_COLUMNS)
    payload.update(updates)
    return SchemaEvidence(**payload)


def record(**updates):
    payload = dict(provenance="synthetic_fixture", inquiry_id="AG-INQ-000001", schema_evidence=schema(),
                   ownership=None, payload_marker=EXPLICIT_UNOWNED_MARKER,
                   legacy_token_hash_present=True)
    payload.update(updates)
    return SyntheticLegacyInquiry(**payload)


def owned():
    return record(ownership=OwnershipEvidence(inquiry_id="AG-INQ-000001",
        customer_id="AG-CUS-000001", session_id="AG-SES-000001", version=0), payload_marker=None)


def test_contract_is_closed_versioned_and_matches_evidenced_schema():
    assert CONTRACT_VERSION == "aicc-b3e-migration-contract/v1"
    assert PERSISTENCE_SCHEMA_VERSION == "shopping-customer-persistence/v1"
    assert EXPECTED_OWNERSHIP_COLUMNS == ("inquiry_id", "customer_id", "session_id", "version")
    assert record().contract_version == CONTRACT_VERSION
    with pytest.raises(ValidationError):
        SyntheticLegacyInquiry.model_validate({**record().model_dump(), "customer_id": "claim"})


def test_explicit_unowned_and_owned_are_distinct_and_never_auto_claimed():
    unowned = classify_legacy_inquiry(record())
    assert unowned.classification is LegacyInquiryClassification.EXPLICITLY_UNOWNED
    assert unowned.legacy_access_permitted is True
    assert unowned.automatic_claim_permitted is False
    owned_result = classify_legacy_inquiry(owned())
    assert owned_result.classification is LegacyInquiryClassification.OWNED
    assert owned_result.legacy_access_permitted is False
    assert owned_result.automatic_claim_permitted is False


@pytest.mark.parametrize("candidate", [
    record(payload_marker=None),
    record(payload_marker="unowned/v0"),
    record(ownership=OwnershipEvidence(inquiry_id="AG-INQ-000001", customer_id="AG-CUS-000001",
                                       session_id="AG-SES-000001", version=0)),
])
def test_ambiguous_or_conflicting_provenance_fails_closed(candidate):
    result = classify_legacy_inquiry(candidate)
    assert result.classification in {LegacyInquiryClassification.AMBIGUOUS,
                                     LegacyInquiryClassification.MALFORMED}
    assert result.legacy_access_permitted is False


@pytest.mark.parametrize("changes", [
    {"version": "future"},
    {"tables": tuple(name for name in EXPECTED_CORE_TABLES if name != "shopping_inquiry_ownership")},
    {"ownership_columns": ("inquiry_id", "customer_id", "session_id")},
])
def test_schema_mismatch_is_not_treated_as_unowned(changes):
    result = classify_legacy_inquiry(record(schema_evidence=schema(**changes)))
    assert result.classification is LegacyInquiryClassification.INCOMPATIBLE_SCHEMA
    assert result.legacy_access_permitted is False


def test_classification_set_requires_complete_nonambiguous_evidence():
    conflict = validate_classification_set((record(), owned()))
    assert conflict.outcome is ValidationOutcome.BLOCKED
    assert conflict.stop_reasons == (StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,)
    assert conflict.details == ("classification_evidence_conflict",)
    assert validate_classification_set((owned(), record())) == conflict
    assert validate_classification_set((record(inquiry_id="AG-INQ-000002"), owned())).accepted
    blocked = validate_classification_set((record(payload_marker=None), owned()))
    assert blocked.outcome is ValidationOutcome.BLOCKED
    assert blocked.stop_reasons == (StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,)
    assert blocked.details == ("classification_evidence_ambiguous", "classification_evidence_conflict")
    assert not validate_classification_set(()).accepted


@pytest.mark.parametrize("field,value", [
    ("customer_id", "AG-CUS-000002"),
    ("session_id", "AG-SES-000002"),
    ("version", 1),
])
def test_conflicting_owner_evidence_is_blocked_in_either_order(field, value):
    first = owned()
    changed = first.model_dump()
    changed["ownership"][field] = value
    second = SyntheticLegacyInquiry.model_validate(changed)
    expected = ContractValidation(outcome=ValidationOutcome.BLOCKED,
        stop_reasons=(StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,),
        details=("classification_evidence_conflict",))
    for candidates in ((first, second), (second, first), (first, second, first)):
        assert validate_classification_set(candidates) == expected


@pytest.mark.parametrize("candidate", [record(), owned()])
def test_identical_evidence_is_accepted_and_deterministic(candidate):
    repeated = SyntheticLegacyInquiry.model_validate(candidate.model_dump())
    for _ in range(3):
        assert validate_classification_set((candidate, repeated)) == ContractValidation(
            outcome=ValidationOutcome.ACCEPTED)


@pytest.mark.parametrize("changes", [
    {"provenance": "repository_source"},
    {"tables": (*EXPECTED_CORE_TABLES, "different_observation")},
    {"version": "future"},
    {"ownership_columns": ("inquiry_id",)},
])
def test_conflicting_schema_or_provenance_evidence_is_blocked(changes):
    first, second = record(), record(schema_evidence=schema(**changes))
    forward = validate_classification_set((first, second))
    assert forward.outcome is ValidationOutcome.BLOCKED
    assert "classification_evidence_conflict" in forward.details
    assert validate_classification_set((second, first)) == forward


@pytest.mark.parametrize("level", ["record", "schema"])
@pytest.mark.parametrize("provenance", [None, "untrusted-client-secret"])
def test_missing_or_untrusted_provenance_is_a_bounded_validation_error(level, provenance):
    values = record().model_dump()
    target = values if level == "record" else values["schema_evidence"]
    if provenance is None:
        target.pop("provenance")
    else:
        target["provenance"] = provenance
    with pytest.raises(ValidationError) as error:
        SyntheticLegacyInquiry.model_validate(values)
    assert "untrusted-client-secret" not in str(error.value)


@pytest.mark.parametrize("field", ["provenance", "contract_version"])
def test_unvalidated_copies_cannot_bypass_contract_validation(field):
    candidate = record().model_copy(update={field: "untrusted-client-secret"})
    result = validate_classification_set((candidate,))
    assert result.outcome is ValidationOutcome.BLOCKED
    assert result.details == ("classification_evidence_invalid",)
    assert "untrusted-client-secret" not in result.model_dump_json()
    with pytest.raises(ValidationError):
        classify_legacy_inquiry(candidate)


@pytest.mark.parametrize("version", [None, "unsupported/v99"])
def test_missing_or_unsupported_schema_version_blocks_the_set(version):
    result = validate_classification_set((record(schema_evidence=schema(version=version)),))
    assert result.outcome is ValidationOutcome.BLOCKED
    assert result.details == ("classification_evidence_ambiguous",)


def test_failure_projection_is_bounded_secret_free_and_order_independent():
    candidates = tuple(record(inquiry_id=f"synthetic-private-token-{index}", payload_marker=None)
                       for index in range(20))
    result = validate_classification_set(candidates)
    assert result.outcome is ValidationOutcome.BLOCKED
    assert result.details == ("classification_evidence_ambiguous",)
    assert "synthetic-private-token" not in result.model_dump_json()
    for _ in range(3):
        assert validate_classification_set(tuple(reversed(candidates))) == result


@pytest.fixture
def legacy_api(no_io, monkeypatch, tmp_path):
    monkeypatch.setattr(sqlite3, "connect", no_io)
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from core.config.loader import ConfigLoader
    from core.api.dependencies.inquiries import get_inquiry_repository
    from core.api.dependencies.shopping import get_shopping_service
    from core.api.routes.shopping import router
    from core.shopping.adapters.mock_commerce import MockCommerceCatalogAdapter
    from core.shopping.config import ShoppingSettings
    from core.shopping.inquiries import SQLiteInquiryRepository
    from core.shopping.service import ShoppingService

    def deny_config(*args, **kwargs):
        raise AssertionError("operational configuration access is prohibited")

    monkeypatch.setattr(ConfigLoader, "load", deny_config)
    monkeypatch.setenv("AICC_OPERATOR_TOKEN", "synthetic-operator-credential")
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    path = tmp_path / "synthetic-legacy.sqlite3"
    repository = SQLiteInquiryRepository(str(path))
    catalog = ShoppingService(settings=ShoppingSettings(
        enabled=True, environment="test", runtime="virtual", deployment_target="mac-mini-m4",
        write_mode="read_only", approval_required=True, automation_enabled=False,
        ai_enabled=False, catalog_adapter="mock"), catalog=MockCommerceCatalogAdapter())
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_inquiry_repository] = lambda: repository
    app.dependency_overrides[get_shopping_service] = lambda: catalog
    with TestClient(app) as client:
        created = client.post("/shopping/inquiries", json={"product_id": "mock-001"})
        assert created.status_code == 200
        item = created.json()
        yield SimpleNamespace(client=client, repository=repository, path=path, item=item,
            url="/shopping/inquiries/" + item["id"],
            headers={"X-Inquiry-Access-Token": item["public_access_token"]})


def provision_synthetic_schema(api):
    from core.shopping.customer_persistence import initialize_schema
    initialize_schema(api.path)


def set_synthetic_marker(api, marker):
    with sqlite3.connect(api.path) as connection:
        payload = json.loads(connection.execute("SELECT payload FROM inquiries").fetchone()[0])
        payload.pop("_ownership", None)
        if marker is not None:
            payload["_ownership"] = marker
        connection.execute("UPDATE inquiries SET payload=?", (json.dumps(payload),))


def synthetic_snapshot(api):
    with sqlite3.connect(api.path) as connection:
        return tuple(connection.iterdump())


def assert_legacy_denied_without_writes(api):
    before = synthetic_snapshot(api)
    assert not api.repository.authorize(api.item["id"], api.item["public_access_token"])
    responses = [api.client.get(api.url, headers=api.headers),
        api.client.get(api.url + "/messages", headers=api.headers),
        api.client.post(api.url + "/messages", headers=api.headers, json={"body": "Denied"}),
        api.client.get("/shopping/inquiries/AG-INQ-999999", headers=api.headers)]
    for response in responses:
        assert response.status_code == 403
        assert response.json() == {"detail": {"code": "inquiry_access_denied"}}
        assert api.item["public_access_token"] not in response.text
    assert synthetic_snapshot(api) == before


@pytest.mark.parametrize("with_schema", [False, True])
@pytest.mark.parametrize("marker", [None, "unowned/v0", "client-supplied-claim"])
def test_missing_ownership_row_requires_positive_unowned_evidence(legacy_api, with_schema, marker):
    api = legacy_api
    if with_schema:
        provision_synthetic_schema(api)
    set_synthetic_marker(api, marker)
    assert_legacy_denied_without_writes(api)


def test_trusted_marker_without_schema_is_denied(legacy_api):
    api = legacy_api
    set_synthetic_marker(api, EXPLICIT_UNOWNED_MARKER)
    assert_legacy_denied_without_writes(api)


def test_server_evidenced_unowned_compatibility_survives_reopen_and_messages(legacy_api):
    from core.shopping.inquiries import SQLiteInquiryRepository
    api = legacy_api
    provision_synthetic_schema(api)
    reopened = SQLiteInquiryRepository(str(api.path))
    assert reopened.authorize(api.item["id"], api.item["public_access_token"])
    before = synthetic_snapshot(api)
    detail = api.client.get(api.url, headers=api.headers)
    assert detail.status_code == 200
    assert detail.json() == {**api.item, "public_access_token": None}
    assert synthetic_snapshot(api) == before
    operator = {"Authorization": "Bearer synthetic-operator-credential"}
    operator_url = "/shopping/operator/inquiries/" + api.item["id"]
    replies = [api.client.post(api.url + "/messages", headers=api.headers, json={"body": "Customer"}),
        api.client.post(operator_url + "/messages", headers=operator, json={"body": "Operator"})]
    assert all(response.status_code == 200 for response in replies)
    history = api.client.get(api.url + "/messages", headers=api.headers)
    assert history.status_code == 200
    assert [item["sender_type"] for item in history.json()["items"]] == ["customer", "operator"]
    for response in [detail, history, *replies]:
        assert api.item["public_access_token"] not in response.text
        assert "_ownership" not in response.text
    with sqlite3.connect(api.path) as connection:
        payload, token_hash = connection.execute("SELECT payload,token_hash FROM inquiries").fetchone()
        assert json.loads(payload)["_ownership"] == EXPLICIT_UNOWNED_MARKER
        assert "public_access_token" not in json.loads(payload)
        assert token_hash == hashlib.sha256(api.item["public_access_token"].encode()).hexdigest()
        for table in ("shopping_inquiry_ownership", "shopping_inquiry_audit", "shopping_inquiry_idempotency"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


@pytest.mark.parametrize("damage", ["missing_table", "missing_meta", "unknown_version", "unknown_columns"])
def test_positive_marker_never_overrides_incompatible_schema(legacy_api, damage):
    api = legacy_api
    provision_synthetic_schema(api)
    with sqlite3.connect(api.path) as connection:
        if damage == "missing_table":
            connection.execute("DROP TABLE shopping_inquiry_ownership")
        elif damage == "missing_meta":
            connection.execute("DROP TABLE shopping_customer_persistence_meta")
        elif damage == "unknown_version":
            connection.execute("UPDATE shopping_customer_persistence_meta SET version='unknown'")
        else:
            connection.execute("ALTER TABLE shopping_inquiry_ownership RENAME COLUMN session_id TO unknown")
    assert_legacy_denied_without_writes(api)


@pytest.mark.parametrize("state", ["owned", "ambiguous", "unowned"])
def test_owned_denial_and_independent_operator_authorization(legacy_api, state):
    api = legacy_api
    provision_synthetic_schema(api)
    if state == "owned":
        # Keep a valid bearer hash AND marker beside authoritative ownership
        # to ensure neither can override the ownership row.
        with sqlite3.connect(api.path) as connection:
            connection.execute("INSERT INTO shopping_inquiry_ownership VALUES(?,?,?,0)",
                (api.item["id"], "synthetic-owner", "synthetic-session"))
    elif state == "ambiguous":
        set_synthetic_marker(api, None)
    if state != "unowned":
        assert_legacy_denied_without_writes(api)
    operator_url = "/shopping/operator/inquiries/" + api.item["id"]
    for headers in ({}, api.headers, {"Authorization": "Bearer " + api.item["public_access_token"]}):
        assert api.client.get(operator_url, headers=headers).status_code == 401
        assert api.client.post(operator_url + "/messages", headers=headers, json={"body": "Denied"}).status_code == 401
    before = synthetic_snapshot(api)
    headers = {"Authorization": "Bearer synthetic-operator-credential"}
    for path in (operator_url, "/shopping/operator/inquiries"):
        response = api.client.get(path, headers=headers)
        assert response.status_code == 200
        assert api.item["public_access_token"] not in response.text
    assert synthetic_snapshot(api) == before
    if state != "unowned":
        assert api.client.post(operator_url + "/messages", headers=headers, json={"body": "Denied"}).status_code == 409
        assert synthetic_snapshot(api) == before


def test_client_classification_is_not_authority_and_default_activation_is_absent(legacy_api):
    api = legacy_api
    before = synthetic_snapshot(api)
    for field in ("_ownership", "ownership", "customer_id", "classification"):
        response = api.client.post("/shopping/inquiries", json={"product_id": "mock-001", field: "unowned/v1"})
        assert response.status_code == 422
    assert synthetic_snapshot(api) == before
    assert api.client.get("/shopping/owned-inquiries/AG-INQ-000001").status_code == 404
    app_source = (Path(__file__).resolve().parents[1] / "core/api/app.py").read_text()
    assert "owned_inquiry_router" not in app_source
    assert "initialize_persistence_schema" not in app_source
    assert "initialize_schema" not in app_source
    assert "core.api.app" not in sys.modules


def complete_prerequisites():
    return MigrationPrerequisites(
        path_policy_verified=True,
        actual_schema_version=PERSISTENCE_SCHEMA_VERSION,
        backup_restore=BackupRestoreEvidence(
            backup_created=True, backup_hash_verified=True,
            restored_to_isolated_path=True, restored_integrity_checked=True,
            restored_schema_checked=True,
        ),
        dry_run=DryRunEvidence(
            migration_plan_reviewed=True, repeated_run_idempotent=True,
            post_checks_passed=True,
        ),
        rollback=RollbackInvariants(
            owned_legacy_tokens_remain_denied=True,
            ownership_rows_are_not_rewritten=True,
            audit_history_is_preserved=True,
            no_token_expiry_extension=True,
            restore_is_verified_before_reopen=True,
        ),
        approved_gates=frozenset(OperationalApprovalGate),
    )


def test_default_planning_state_is_blocked_and_does_not_claim_evidence():
    result = validate_migration_prerequisites(MigrationPrerequisites())
    assert result.outcome is ValidationOutcome.BLOCKED
    assert StopReason.PATH_POLICY_UNVERIFIED in result.stop_reasons
    assert StopReason.BACKUP_UNVERIFIED in result.stop_reasons
    assert StopReason.TRUSTED_VERIFIER_UNAPPROVED not in result.stop_reasons
    assert MigrationPrerequisites().backup_restore.accepted is False


def test_complete_prerequisites_are_only_a_contract_projection():
    prerequisites = complete_prerequisites()
    result = validate_migration_prerequisites(prerequisites)
    assert result == ContractValidation(outcome=ValidationOutcome.ACCEPTED)
    assert prerequisites.operational_database_access is False
    assert prerequisites.dry_run.synthetic_rows_only is True


@pytest.mark.parametrize("field", ["backup_restore", "dry_run", "rollback"])
def test_each_unproven_safety_family_blocks(field):
    values = complete_prerequisites().model_dump()
    values[field] = type(getattr(complete_prerequisites(), field))()
    result = validate_migration_prerequisites(MigrationPrerequisites(**values))
    assert result.outcome is ValidationOutcome.BLOCKED


def test_operational_access_or_schema_drift_blocks_even_with_other_evidence():
    base = complete_prerequisites().model_dump()
    base["operational_database_access"] = True
    result = validate_migration_prerequisites(MigrationPrerequisites(**base))
    assert StopReason.OPERATIONAL_ACCESS_REQUIRED in result.stop_reasons
    base = complete_prerequisites().model_dump()
    base["actual_schema_version"] = "future"
    result = validate_migration_prerequisites(MigrationPrerequisites(**base))
    assert StopReason.SCHEMA_VERSION_UNVERIFIED in result.stop_reasons


def test_rollback_contract_preserves_owned_denial_and_audit_history():
    rollback = RollbackInvariants(
        owned_legacy_tokens_remain_denied=True,
        ownership_rows_are_not_rewritten=True,
        audit_history_is_preserved=True,
        no_token_expiry_extension=True,
        restore_is_verified_before_reopen=True,
    )
    assert rollback.accepted
    damaged = rollback.model_copy(update={"owned_legacy_tokens_remain_denied": False})
    assert damaged.accepted is False


def test_no_production_types_or_migration_executor_are_exposed():
    import core.shopping.migration_contract as contract
    names = set(dir(contract))
    assert "sqlite3" not in names
    assert "open_connection" not in names
    assert "initialize_schema" not in names
    assert "execute_migration" not in names
