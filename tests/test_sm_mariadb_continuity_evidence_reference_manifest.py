from dataclasses import fields

import pytest

from core.secrets.mariadb_continuity_evidence_reference_manifest import (
    EvidenceReferenceManifest,
    EvidenceRequirementCategory,
    VerificationState,
    canonical_evidence_reference_manifest,
    verified_external_reference_semantics,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


def test_exact_closed_vocabularies_and_direct_frozen_type_reuse():
    assert [item.value for item in EvidenceRequirementCategory] == [
        "AUTH_PLUGIN_HISTORICAL_EVIDENCE",
        "PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE",
        "EXPECTED_DATABASE_IDENTITY",
        "EXPECTED_ACCOUNT_IDENTITY",
        "REQUIRED_GRANTS_PROFILE",
    ]
    assert [item.value for item in VerificationState] == [
        "UNAVAILABLE",
        "REFERENCED_UNVERIFIED",
        "VERIFICATION_REQUIRED",
        "VERIFIED_EXTERNAL_REFERENCE",
    ]
    manifest = canonical_evidence_reference_manifest()
    assert manifest.data_identity_requirements == tuple(DataIdentityCategory)
    assert all(type(item) is DataIdentityCategory for item in manifest.data_identity_requirements)
    assert manifest.continuity_requirements == tuple(ContinuityEvidenceCategory)
    assert all(type(item) is ContinuityEvidenceCategory for item in manifest.continuity_requirements)


@pytest.mark.parametrize("field_name", [item.name for item in fields(EvidenceReferenceManifest)])
def test_no_manifest_field_is_caller_injectable(field_name):
    with pytest.raises(TypeError):
        EvidenceReferenceManifest(**{field_name: True})


def test_verified_reference_is_strictly_reference_local_and_fail_closed():
    semantics = verified_external_reference_semantics()
    assert semantics.verification_state is VerificationState.VERIFIED_EXTERNAL_REFERENCE
    assert semantics.evidence_exists_authoritatively is False
    assert semantics.provenance_valid is False
    assert semantics.authority is False
    assert semantics.canonical_available is False
    assert semantics.compatible is False
    assert semantics.reference_readiness_established is False
    assert semantics.recover_evidence_sufficient is False
    with pytest.raises(TypeError):
        type(semantics)(authority=True)


def test_frozen_value_free_reference_contract_and_prohibited_fields_absent():
    manifest = canonical_evidence_reference_manifest()
    assert manifest.manifest_value_free is True
    false_flags = [
        "reference_can_be_caller_supplied", "reference_asserts_existence",
        "reference_asserts_authority", "reference_asserts_compatibility",
        "reference_asserts_readiness", "reference_can_contain_secret_value",
        "reference_can_contain_credential_hash",
        "reference_can_contain_arbitrary_free_text", "reference_can_contain_sql",
        "reference_can_trigger_io", "reference_can_trigger_network",
        "reference_can_trigger_production_access",
    ]
    assert all(getattr(manifest, name) is False for name in false_flags)
    names = {item.name.lower() for item in fields(EvidenceReferenceManifest)}
    prohibited = {
        "path", "url", "text", "hash", "digest", "plugin_name", "account_name",
        "database_name", "runtime_identifier", "credential", "credential_hash",
        "secret", "secret_value", "sql", "runtime_dump", "port",
    }
    assert names.isdisjoint(prohibited)
