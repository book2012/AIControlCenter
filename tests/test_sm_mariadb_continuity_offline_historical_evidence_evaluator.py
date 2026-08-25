import ast
import dataclasses
from pathlib import Path

import pytest

import core.secrets.mariadb_continuity_offline_historical_evidence_evaluator as evaluator
from core.secrets.mariadb_continuity_descriptors import RecoverEvidenceGate
from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import EvidenceAcquisitionCategory
from core.secrets.mariadb_continuity_evidence_source_binding import (
    MariaDBContinuityEvidenceSourceBindingContract,
)
from core.secrets.mariadb_continuity_offline_historical_evidence_evaluator import (
    ContinuityLineageEvidenceFact, DataIdentityEvidenceFact,
    HistoricalEvidenceDimensionFact, HistoricalEvidenceFact,
    HistoricalEvidenceFactState, OfflineEvaluation,
    OfflineHistoricalEvidenceClassification, REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES,
    REQUIRED_DATA_IDENTITY_CATEGORIES, REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES,
    evaluate_offline_historical_evidence,
)
from core.secrets.mariadb_continuity_sources import ContinuityEvidenceCategory, DataIdentityCategory


FILE = Path(__file__).parents[1] / "core/secrets/mariadb_continuity_offline_historical_evidence_evaluator.py"
PRESENT = HistoricalEvidenceFactState.PRESENT


def fact(kind: type, category: object, state: object = PRESENT):
    return evaluator._construct_fact(kind, category, state)


def complete() -> HistoricalEvidenceFact:
    return evaluator._construct_historical_evidence_fact(
        tuple(fact(HistoricalEvidenceDimensionFact, item) for item in REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES),
        tuple(fact(DataIdentityEvidenceFact, item) for item in REQUIRED_DATA_IDENTITY_CATEGORIES),
        tuple(fact(ContinuityLineageEvidenceFact, item) for item in REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES),
        provenance_valid=True,
    )


def replace_fact(facts: HistoricalEvidenceFact, group: str, index: int, state: object) -> HistoricalEvidenceFact:
    groups = {name: getattr(facts, name) for name in ("dimensions", "data_identities", "continuity_lineage", "provenance_valid")}
    values = list(groups[group])
    old = values[index]
    values[index] = fact(type(old), old.category, state)
    groups[group] = tuple(values)
    return evaluator._construct_historical_evidence_fact(**groups)


def test_exact_existing_contract_reuse_without_duplicate_dimension_enum() -> None:
    assert REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES == tuple(
        EvidenceAcquisitionCategory[name] for name in (
            "AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE", "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE",
            "EXPECTED_DATABASE_IDENTITY", "EXPECTED_ACCOUNT_IDENTITY", "REQUIRED_GRANTS",
            "ACCOUNT_BINDING", "BASELINE_BINDING", "TIMESTAMP_EVIDENCE",
            "IMMUTABLE_INTEGRITY_BINDING", "TRUSTED_ISSUER",
        )
    )
    assert "HistoricalEvidenceDimension" not in vars(evaluator)
    assert len(REQUIRED_DATA_IDENTITY_CATEGORIES) == 5
    assert tuple(item.name for item in REQUIRED_DATA_IDENTITY_CATEGORIES) == (
        "WORDPRESS_IDENTITY", "SITE_IDENTITY", "APPLICATION_IDENTITY",
        "CLOSED_SCHEMA_CHARACTERISTICS", "CLOSED_TABLE_CHARACTERISTICS",
    )
    assert len(REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES) == 3
    assert tuple(item.name for item in REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES) == (
        "LOGICAL_EXPORT", "RECOVERY_ARTIFACT", "PERSISTENT_VOLUME_SNAPSHOT",
    )
    assert EvidenceAcquisitionCategory.FIVE_CATEGORY_DATA_IDENTITY not in REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES
    assert EvidenceAcquisitionCategory.THREE_CATEGORY_CONTINUITY_LINEAGE not in REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES


def test_direct_construction_of_every_input_and_result_type_fails() -> None:
    for kind, args in (
        (HistoricalEvidenceDimensionFact, (EvidenceAcquisitionCategory.ACCOUNT_BINDING, PRESENT)),
        (DataIdentityEvidenceFact, (DataIdentityCategory.WORDPRESS_IDENTITY, PRESENT)),
        (ContinuityLineageEvidenceFact, (ContinuityEvidenceCategory.LOGICAL_EXPORT, PRESENT)),
        (HistoricalEvidenceFact, ((), (), ())),
        (OfflineEvaluation, ()),
        (OfflineEvaluation, (OfflineHistoricalEvidenceClassification.EVIDENCE_COMPLETE,)),
    ):
        with pytest.raises(TypeError):
            kind(*args)


def test_private_fixtures_complete_and_never_promote_recover() -> None:
    result = evaluate_offline_historical_evidence(complete())
    assert result.classification is OfflineHistoricalEvidenceClassification.EVIDENCE_COMPLETE
    assert result.recover_evidence_sufficient is False
    assert result.recover_evidence_gate is RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT


def test_existing_structural_provenance_contract_is_reused_and_required() -> None:
    assert "provenance_valid" in vars(MariaDBContinuityEvidenceSourceBindingContract)
    assert MariaDBContinuityEvidenceSourceBindingContract().provenance_valid is False
    facts = complete()
    without_provenance = evaluator._construct_historical_evidence_fact(
        facts.dimensions, facts.data_identities, facts.continuity_lineage,
        provenance_valid=False,
    )
    assert evaluate_offline_historical_evidence(without_provenance).classification is OfflineHistoricalEvidenceClassification.EVIDENCE_INCOMPLETE
    assert "Provenance" not in vars(evaluator)


@pytest.mark.parametrize("group", ("dimensions", "data_identities", "continuity_lineage"))
def test_each_missing_requirement_is_incomplete(group: str) -> None:
    facts = complete()
    for index in range(len(getattr(facts, group))):
        assert evaluate_offline_historical_evidence(replace_fact(facts, group, index, HistoricalEvidenceFactState.MISSING)).classification is OfflineHistoricalEvidenceClassification.EVIDENCE_INCOMPLETE
        groups = {name: getattr(facts, name) for name in ("dimensions", "data_identities", "continuity_lineage", "provenance_valid")}
        groups[group] = getattr(facts, group)[:index] + getattr(facts, group)[index + 1:]
        shortened = evaluator._construct_historical_evidence_fact(**groups)
        assert evaluate_offline_historical_evidence(shortened).classification is OfflineHistoricalEvidenceClassification.EVIDENCE_INCOMPLETE


@pytest.mark.parametrize("state, expected", [
    (HistoricalEvidenceFactState.UNAVAILABLE, OfflineHistoricalEvidenceClassification.EVIDENCE_UNAVAILABLE),
    (HistoricalEvidenceFactState.UNSAFE, OfflineHistoricalEvidenceClassification.EVIDENCE_UNSAFE),
    (HistoricalEvidenceFactState.AMBIGUOUS, OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN),
])
def test_fail_closed_states(state, expected) -> None:
    assert evaluate_offline_historical_evidence(replace_fact(complete(), "dimensions", 0, state)).classification is expected


def test_malformed_wrong_exact_types_and_duplicates_are_uncertain() -> None:
    facts = complete()
    duplicate = evaluator._construct_historical_evidence_fact(
        facts.dimensions + (facts.dimensions[0],), facts.data_identities,
        facts.continuity_lineage, provenance_valid=True,
    )
    wrong_state = object.__new__(HistoricalEvidenceDimensionFact)
    object.__setattr__(wrong_state, "category", EvidenceAcquisitionCategory.ACCOUNT_BINDING)
    object.__setattr__(wrong_state, "state", "PRESENT")
    wrong_group = object.__new__(HistoricalEvidenceFact)
    object.__setattr__(wrong_group, "dimensions", [*facts.dimensions])
    object.__setattr__(wrong_group, "data_identities", facts.data_identities)
    object.__setattr__(wrong_group, "continuity_lineage", facts.continuity_lineage)
    object.__setattr__(wrong_group, "provenance_valid", facts.provenance_valid)
    wrong_fact_type = object.__new__(HistoricalEvidenceFact)
    object.__setattr__(wrong_fact_type, "dimensions", facts.dimensions)
    object.__setattr__(wrong_fact_type, "data_identities", (facts.dimensions[0],))
    object.__setattr__(wrong_fact_type, "continuity_lineage", facts.continuity_lineage)
    object.__setattr__(wrong_fact_type, "provenance_valid", facts.provenance_valid)
    bad_state_collection = object.__new__(HistoricalEvidenceFact)
    object.__setattr__(bad_state_collection, "dimensions", (wrong_state,))
    object.__setattr__(bad_state_collection, "data_identities", facts.data_identities)
    object.__setattr__(bad_state_collection, "continuity_lineage", facts.continuity_lineage)
    object.__setattr__(bad_state_collection, "provenance_valid", facts.provenance_valid)
    bad_provenance = object.__new__(HistoricalEvidenceFact)
    object.__setattr__(bad_provenance, "dimensions", facts.dimensions)
    object.__setattr__(bad_provenance, "data_identities", facts.data_identities)
    object.__setattr__(bad_provenance, "continuity_lineage", facts.continuity_lineage)
    object.__setattr__(bad_provenance, "provenance_valid", 1)
    for value in (object(), duplicate, wrong_group, wrong_fact_type, bad_state_collection, bad_provenance):
        assert evaluate_offline_historical_evidence(value).classification is OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN


def test_dataclasses_are_frozen_slotted_and_private_helpers_validate_exact_types() -> None:
    for kind in (HistoricalEvidenceDimensionFact, DataIdentityEvidenceFact, ContinuityLineageEvidenceFact, HistoricalEvidenceFact, OfflineEvaluation):
        assert dataclasses.is_dataclass(kind) and kind.__dataclass_params__.frozen
        assert "__slots__" in vars(kind)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        complete().dimensions = ()
    with pytest.raises(TypeError):
        fact(HistoricalEvidenceDimensionFact, DataIdentityCategory.WORDPRESS_IDENTITY)
    with pytest.raises(TypeError):
        evaluator._construct_evaluation("EVIDENCE_COMPLETE")


def test_zero_authority_control_plane_and_mutation_invariants_for_every_result() -> None:
    samples = [complete()] + [replace_fact(complete(), "dimensions", 0, state) for state in HistoricalEvidenceFactState]
    samples.append(object())
    for sample in samples:
        result = evaluate_offline_historical_evidence(sample)
        assert result.authorization is result.authority is result.capability is False
        assert result.production_access is result.credential_validation is False
        assert result.controlled_execution_port_coupled is False
        assert result.mac_control_plane is True and result.ubuntu_role is False
        assert type(result.mutation_budget) is int and result.mutation_budget == 0


def test_source_has_no_io_network_database_sql_or_acquisition_mechanism() -> None:
    source = FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {"os", "pathlib", "socket", "subprocess", "pymysql", "requests", "urllib"}
    imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not imports & forbidden_imports
    calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not calls & {"open", "exec", "eval", "compile"}
    assert not attributes & {"read", "read_text", "read_bytes", "open", "stat", "lstat", "connect", "execute"}
    lowered = source.lower()
    assert not any(token in lowered for token in ("runtimehomeresolver", "trustedownershipexpectation", "ubuntuworkerclient", "docker", "colima", "systemd", "select ", "insert ", "update ", "delete "))
