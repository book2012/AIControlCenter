import pytest

from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    ProtectedExternalEvidenceConcreteSourceLocationIdentity as SourceIdentity,
)

from core.secrets.mariadb_continuity_protected_source_metadata import (
    MetadataInspectionOutcome as Outcome,
    MetadataInspectionReason as Reason,
    MetadataEvidenceProvenance as Provenance,
    OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED,
    ProtectedSourceMetadataEvidence,
    ProtectedSourceMetadataInspectionRequest,
    metadata_evidence_for_reason,
)


def test_closed_outcomes_reasons_and_safe_facts() -> None:
    assert {x.value for x in Outcome} == {"SAFE_BOUND", "ABSENT", "UNSAFE", "UNAVAILABLE", "UNCERTAIN"}
    assert len(Reason) == 13
    for reason, outcome in [
        (Reason.METADATA_SAFE_AND_STABLY_BOUND, Outcome.SAFE_BOUND),
        (Reason.SOURCE_ABSENT, Outcome.ABSENT), (Reason.PARENT_ABSENT, Outcome.ABSENT),
        (Reason.SYMLINK_REJECTED, Outcome.UNSAFE), (Reason.WRONG_FILE_TYPE, Outcome.UNSAFE),
        (Reason.PARENT_MODE_MISMATCH, Outcome.UNSAFE), (Reason.LEAF_PERMISSIONS_TOO_BROAD, Outcome.UNSAFE),
        (Reason.PARENT_UID_GID_MISMATCH, Outcome.UNSAFE), (Reason.LEAF_UID_GID_MISMATCH, Outcome.UNSAFE),
        (Reason.INODE_DEVICE_INSTABILITY, Outcome.UNCERTAIN), (Reason.PATH_REPLACEMENT_RACE, Outcome.UNCERTAIN),
        (Reason.METADATA_ACCESS_FAILURE, Outcome.UNAVAILABLE), (Reason.AMBIGUOUS_METADATA_RESULT, Outcome.UNCERTAIN),
    ]:
        result = metadata_evidence_for_reason(reason)
        expected = outcome is Outcome.SAFE_BOUND
        assert (result.source_exists, result.metadata_inspected, result.metadata_safe) == (expected,) * 3
        assert result.provenance is Provenance.INERT_TEST_CLASSIFICATION
        assert result.operationally_observed is False
        assert result.human_authorized_operational_inspection is False
        assert result.is_operational_evidence is False
        assert not any((result.content_acquired, result.evidence_admitted, result.evidence_verified,
                        result.recover_evidence_sufficient, result.production_validation_ready,
                        result.shopping_runtime_activated, result.mutation_authority,
                        result.acquisition_authority, result.admission_authority,
                        result.verification_authority))


def test_direct_evidence_construction_and_operational_issuance_are_closed() -> None:
    with pytest.raises(TypeError, match="repository-owned"):
        ProtectedSourceMetadataEvidence(Outcome.ABSENT, Reason.SOURCE_ABSENT, False, False, False)
    assert OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED is False
    assert {item.value for item in Provenance} == {
        "INERT_TEST_CLASSIFICATION", "HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION"
    }


def test_request_is_canonical_path_free_and_zero_mutation() -> None:
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    assert request.mutation_budget == 0
    assert request.source_identity is SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION
    assert not any(word in request.__slots__ for word in ("path", "slot", "fd"))
    with pytest.raises(TypeError):
        ProtectedSourceMetadataInspectionRequest(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    with pytest.raises(TypeError):
        ProtectedSourceMetadataInspectionRequest.canonical("/tmp/source")
