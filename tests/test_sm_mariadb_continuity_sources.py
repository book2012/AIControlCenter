import ast
import hashlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    CredentialSourceContract,
    DataContinuityContract,
    DataIdentityCategory,
    MariaDBContinuitySourceContracts,
    SourceCategory,
    canonical_phase_b1_source_contracts,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILE = ROOT / "core/secrets/mariadb_continuity_sources.py"
PRESERVED = {
    "core/secrets/mariadb_continuity_validation.py": "ebf5b7e6bc02eaaf3d789525d92f8274758eba75f3dc7bda75577722a6dccb66",
    "core/secrets/mariadb_continuity_validation_port.py": "fd91b54225472d38549351693edb0c1469fe6816131575eaa6c590b1f4f76c1c",
    "ops/macos/shopping/mariadb_continuity_validation_adapter.py": "298872771a7c67c3bdf2504b2bb1fc8073394c794f23b50403af27f76926b987",
    "core/secrets/mariadb_continuity_prerequisites.py": "4f5331b0fb2e791d27ec2c37a86f213af59dd28c2a23d847441f4f5d55391095",
    "ops/macos/shopping/mariadb_continuity_validation_composition.py": "d8a2fc40e99f1fea176f1f63df3395f98bead368019ee972a19d4d07472acbef",
}


def test_exact_four_categories_and_frozen_availability():
    contracts = canonical_phase_b1_source_contracts()
    assert tuple(item.value for item in SourceCategory) == (
        "CREDENTIAL_SOURCE", "EXPECTED_IDENTITY_DESCRIPTOR",
        "DATA_IDENTITY_BASELINE", "DATA_CONTINUITY_BASELINE",
    )
    projection = contracts.to_projection()
    available = {key: value for key, value in projection.items() if key.endswith("_available")}
    assert available and set(available.values()) == {False}
    assert projection["credential_source_contract_defined"] is True
    assert projection["expected_identity_source_defined"] is True
    assert projection["data_identity_baseline_contract_defined"] is True
    assert projection["data_continuity_baseline_contract_defined"] is True


def test_credential_contract_preserves_every_frozen_characteristic():
    contract = canonical_phase_b1_source_contracts().credential
    true_facts = (
        contract.mac_control_plane_owned, contract.external_protected_fixed_slot,
        contract.outside_git, contract.protected_parent_required,
        contract.parent_mode_0700_required, contract.regular_non_symlink_file_required,
        contract.file_mode_0600_required, contract.explicit_trusted_uid_gid_required,
        contract.acquisition_only_after_capability_consumption,
    )
    false_facts = (
        contract.ambient_home_uid_authority, contract.environment_transport,
        contract.argv_transport, contract.json_secret_value_transport,
        contract.governance_transport, contract.secret_value_logging_or_hashing,
        contract.fallback, contract.enumeration, contract.candidate_iteration,
    )
    assert all(true_facts)
    assert not any(false_facts)
    assert contract.acquisition_maximum == 1


def test_identity_and_continuity_independence_contracts():
    contracts = canonical_phase_b1_source_contracts()
    expected = contracts.expected_identity
    assert expected.independent_from_credential_evidence
    assert expected.fixed_canonical_profile
    assert expected.expected_database_facts and expected.expected_account_facts and expected.expected_grants_facts
    assert not expected.derivation_from_credential_compose_container_or_volume_alone
    assert contracts.data_identity.independent_historical_baseline_required
    assert contracts.data_identity.allowed_categories == tuple(DataIdentityCategory)
    assert not contracts.data_identity.infrastructure_names_alone_sufficient
    assert contracts.data_continuity.independently_verified_historical_lineage_required
    assert contracts.data_continuity.allowed_categories == tuple(ContinuityEvidenceCategory)
    assert contracts.data_continuity.artifact_exists is False


@pytest.mark.parametrize(
    ("contract_type", "override"),
    (
        (CredentialSourceContract, {"mac_control_plane_owned": False}),
        (CredentialSourceContract, {"acquisition_maximum": 2}),
        (DataContinuityContract, {"artifact_exists": True}),
        (MariaDBContinuitySourceContracts, {"credential_material_available": True}),
        (
            MariaDBContinuitySourceContracts,
            {"expected_identity_descriptor_available": True},
        ),
        (MariaDBContinuitySourceContracts, {"data_identity_baseline_available": True}),
        (
            MariaDBContinuitySourceContracts,
            {"data_continuity_baseline_available": True},
        ),
        (
            MariaDBContinuitySourceContracts,
            {"credential": CredentialSourceContract()},
        ),
    ),
)
def test_frozen_source_facts_reject_constructor_overrides(contract_type, override):
    with pytest.raises(TypeError):
        contract_type(**override)


def test_source_truth_fields_are_not_init_fields_and_replace_rejects_them():
    contracts = canonical_phase_b1_source_contracts()
    frozen_names = {
        "credential",
        "expected_identity",
        "data_identity",
        "data_continuity",
        "credential_source_contract_defined",
        "credential_material_available",
        "expected_identity_source_defined",
        "expected_identity_descriptor_available",
        "data_identity_baseline_contract_defined",
        "data_identity_baseline_available",
        "data_continuity_baseline_contract_defined",
        "data_continuity_baseline_available",
    }
    metadata = {item.name: item.init for item in fields(contracts)}
    assert frozen_names <= metadata.keys()
    assert not any(metadata[name] for name in frozen_names)
    assert not any(item.init for item in fields(CredentialSourceContract))
    assert not any(item.init for item in fields(DataContinuityContract))
    with pytest.raises(TypeError):
        replace(contracts, data_continuity_baseline_available=True)


def test_positive_continuity_availability_and_contradiction_are_unconstructable():
    contracts = MariaDBContinuitySourceContracts()
    assert contracts.data_continuity_baseline_available is False
    assert contracts.data_continuity.artifact_exists is False
    with pytest.raises(TypeError):
        MariaDBContinuitySourceContracts(data_continuity_baseline_available=True)


def test_value_free_field_surface_and_no_implementation_dependencies():
    contracts = canonical_phase_b1_source_contracts()
    objects = (contracts, contracts.credential, contracts.expected_identity, contracts.data_identity, contracts.data_continuity)
    names = {item.name.lower() for obj in objects for item in fields(obj)}
    forbidden_fields = {"path", "host", "port", "dsn", "database", "username", "password", "authorization_id", "capability_id", "token", "nonce"}
    assert names.isdisjoint(forbidden_fields)
    source = PRODUCTION_FILE.read_text()
    tree = ast.parse(source)
    imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert imports.isdisjoint({"subprocess", "socket", "requests", "urllib", "docker", "pymysql", "MySQLdb", "mysql", "mariadb", "sqlalchemy", "pathlib", "os"})
    assert not any(term in source for term in ("GovernanceAuthorization", "ControlledExecutionPort"))
    assert not any(keyword in source.upper() for keyword in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP "))


def test_named_phase_a_and_sm_01b_02d_06_files_are_byte_identical_to_head():
    for relative, expected in PRESERVED.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
