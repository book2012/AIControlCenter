from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import stat

import pytest

import ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_adapter as adapter_module

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import ConcreteProtectedEvidencePath
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import ProtectedExternalEvidenceFixedSourceSlotIdentity as Slot
from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import ProtectedEvidenceAcquisitionAuthorizationConsumptionResult, ProtectedEvidenceAcquisitionConsumptionReceipt, ProtectedEvidenceHumanAuthorizationEvidence, ProtectedEvidenceHumanAuthorizationValidation, RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption, acquisition_request, issue_acquisition_authorization
from core.secrets.mariadb_continuity_protected_evidence_leaf_locator import compose_concrete_protected_evidence_leaf_path
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_adapter import PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE, ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism, ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter, ProtectedEvidenceAcquisitionAuthorizationSQLiteError
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_path_policy import ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity, ProtectedEvidenceAcquisitionSQLitePathPolicy
from ops.macos.shopping.mariadb_continuity_protected_evidence_acquisition_authorization_sqlite_schema import APPLICATION_ID, USER_VERSION, SUPPORTED_SCHEMA_FINGERPRINT

REPOSITORY = Path(__file__).resolve().parents[1]


def authorization(number=1):
    parent = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(parent, "concrete_path", "/synthetic/protected")
    request = acquisition_request(f"request-{number}", compose_concrete_protected_evidence_leaf_path(parent, Slot.AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT))
    return issue_acquisition_authorization(f"authorization-{number}", request)


def consume(store, value):
    evidence = object.__new__(ProtectedEvidenceHumanAuthorizationEvidence)
    object.__setattr__(evidence, "authorization_id", value.authorization_id)
    object.__setattr__(evidence, "acquisition_request_id", value.acquisition_request_id)
    validation = synthetic_validation(evidence)
    assert validation.production_authority is False
    return store.consume_durably(value)


def synthetic_validation(evidence):
    value = object.__new__(ProtectedEvidenceHumanAuthorizationValidation)
    object.__setattr__(value, "authorization_id", evidence.authorization_id)
    object.__setattr__(value, "acquisition_request_id", evidence.acquisition_request_id)
    object.__setattr__(value, "production_authority", False)
    return value


def adapter(tmp_path, fault=None):
    identity = ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    return ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism.for_test(
        tmp_path / "acquisition.sqlite3", repository_root=REPOSITORY,
        ownership_identity=identity, fault=fault)


def production_adapter(tmp_path):
    identity = ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(
        tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    return ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter.for_test(
        tmp_path / "production-facade.sqlite3", repository_root=REPOSITORY,
        ownership_identity=identity)


def state(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT barrier_state FROM protected_evidence_acquisition_authorization_consumptions").fetchone()[0]


def test_dedicated_path_identity_schema_and_permissions(tmp_path):
    store = adapter(tmp_path)
    path = tmp_path / "acquisition.sqlite3"
    assert "protected-evidence/acquisition-authorization-consumption.sqlite3" in str(ProtectedEvidenceAcquisitionSQLitePathPolicy.production(repository_root=REPOSITORY, home=Path("/Users/synthetic"), ownership_identity=ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)).production_path())
    assert APPLICATION_ID != 0x41494343 and USER_VERSION == 1 and SUPPORTED_SCHEMA_FINGERPRINT
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_claim_then_commit_fresh_replay_rejected(tmp_path):
    result = consume(adapter(tmp_path), authorization())
    assert result.receipt.state.value == "COMMITTED" and state(tmp_path / "acquisition.sqlite3") == "COMMITTED"
    assert not hasattr(result, "invocation_capability")
    assert not hasattr(result.receipt, "invocation_capability")
    assert tuple(ProtectedEvidenceAcquisitionAuthorizationConsumptionResult.__slots__) == ("receipt",)
    assert "invocation_capability" not in ProtectedEvidenceAcquisitionConsumptionReceipt.__slots__
    with pytest.raises(RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption):
        consume(adapter(tmp_path), authorization())


def test_repository_binding_id_alone_has_zero_consumption_authority(tmp_path):
    with pytest.raises(TypeError):
        production_adapter(tmp_path).consume_once(authorization())


def test_human_authorization_factual_dto_alone_has_zero_authority(tmp_path):
    value = authorization()
    evidence = object.__new__(ProtectedEvidenceHumanAuthorizationEvidence)
    object.__setattr__(evidence, "authorization_id", value.authorization_id)
    object.__setattr__(evidence, "acquisition_request_id", value.acquisition_request_id)
    with pytest.raises(Exception, match="validation"):
        production_adapter(tmp_path).consume_once(value, evidence)


def test_no_production_trusted_human_issuer_is_claimed(tmp_path):
    assert PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE is False
    value = authorization()
    evidence = object.__new__(ProtectedEvidenceHumanAuthorizationEvidence)
    object.__setattr__(evidence, "authorization_id", value.authorization_id)
    object.__setattr__(evidence, "acquisition_request_id", value.acquisition_request_id)
    validation = synthetic_validation(evidence)
    assert validation.production_authority is False
    with pytest.raises(Exception, match="validation"):
        production_adapter(tmp_path).consume_once(value, evidence, validation)
    forged = object.__new__(ProtectedEvidenceHumanAuthorizationValidation)
    object.__setattr__(forged, "authorization_id", value.authorization_id)
    object.__setattr__(forged, "acquisition_request_id", value.acquisition_request_id)
    object.__setattr__(forged, "production_authority", True)
    with pytest.raises(Exception, match="no trusted Production"):
        production_adapter(tmp_path).consume_once(value, evidence, forged)


def test_test_database_path_is_storage_only_and_cannot_grant_authority(tmp_path):
    value = authorization()
    evidence = object.__new__(ProtectedEvidenceHumanAuthorizationEvidence)
    object.__setattr__(evidence, "authorization_id", value.authorization_id)
    object.__setattr__(evidence, "acquisition_request_id", value.acquisition_request_id)
    validation = synthetic_validation(evidence)
    store = production_adapter(tmp_path)
    assert store._database_path == tmp_path / "production-facade.sqlite3"
    with pytest.raises(Exception, match="validation"):
        store.consume_once(value, evidence, validation)

    identity = ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(
        tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    direct = ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter(
        repository_root=REPOSITORY,
        ownership_identity=identity,
        _test_database_path=tmp_path / "direct.sqlite3",
    )
    with pytest.raises(Exception, match="validation"):
        direct.consume_once(value, evidence, validation)


def test_stranded_claim_is_permanent_and_not_reconciled_later(tmp_path):
    def fault(stage, connection):
        if stage == "during_final_transaction":
            raise RuntimeError("stop")
    with pytest.raises(RuntimeError):
        consume(adapter(tmp_path, fault), authorization())
    assert state(tmp_path / "acquisition.sqlite3") == "DURABLY_CLAIMED"
    with pytest.raises(RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption):
        consume(adapter(tmp_path), authorization())


def test_stranded_claim_issues_no_result_or_capability(tmp_path):
    def fault(stage, connection):
        if stage == "during_final_transaction":
            raise RuntimeError("stop")
    with pytest.raises(RuntimeError):
        consume(adapter(tmp_path, fault), authorization())
    assert state(tmp_path / "acquisition.sqlite3") == "DURABLY_CLAIMED"


def test_same_call_ambiguous_commit_only_and_concurrent_double_rejected(tmp_path):
    def ambiguous(stage, connection):
        if stage == "after_final_commit":
            raise sqlite3.OperationalError("ack lost")
    assert consume(adapter(tmp_path, ambiguous), authorization()).receipt.state.value == "COMMITTED"
    with pytest.raises(RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption):
        consume(adapter(tmp_path), authorization())

    second_root = tmp_path / "concurrent"
    second_root.mkdir(mode=0o700)
    stores = (adapter(second_root), adapter(second_root))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(consume, store, authorization(2)) for store in stores]
    outcomes = []
    for future in futures:
        try:
            future.result(); outcomes.append("success")
        except RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption:
            outcomes.append("repeated")
    assert sorted(outcomes) == ["repeated", "success"]


def test_ambiguous_commit_validates_read_back_and_returns_facts_only(tmp_path, monkeypatch):
    events = []
    original_validate = adapter_module.ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism._validate_committed
    def validate(self, identifiers, expected_row):
        events.append("validated")
        return original_validate(self, identifiers, expected_row)
    monkeypatch.setattr(adapter_module.ProtectedEvidenceAcquisitionAuthorizationDurabilityMechanism, "_validate_committed", validate)
    def ambiguous(stage, connection):
        if stage == "after_final_commit":
            raise sqlite3.OperationalError("ack lost")
    result = consume(adapter(tmp_path, ambiguous), authorization())
    assert events == ["validated"]
    assert not hasattr(result, "invocation_capability")


def test_foreign_schema_and_symlink_rejected(tmp_path):
    foreign = tmp_path / "foreign.sqlite3"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE foreign_table(value TEXT)")
    foreign.chmod(0o600)
    identity = ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    with pytest.raises(ProtectedEvidenceAcquisitionAuthorizationSQLiteError):
        ProtectedEvidenceAcquisitionAuthorizationSQLiteAdapter.for_test(foreign, repository_root=REPOSITORY, ownership_identity=identity)
