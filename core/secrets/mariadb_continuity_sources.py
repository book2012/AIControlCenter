"""Value-free contracts for protected MariaDB continuity evidence sources."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceCategory(str, Enum):
    CREDENTIAL_SOURCE = "CREDENTIAL_SOURCE"
    EXPECTED_IDENTITY_DESCRIPTOR = "EXPECTED_IDENTITY_DESCRIPTOR"
    DATA_IDENTITY_BASELINE = "DATA_IDENTITY_BASELINE"
    DATA_CONTINUITY_BASELINE = "DATA_CONTINUITY_BASELINE"


class DataIdentityCategory(str, Enum):
    WORDPRESS_IDENTITY = "WORDPRESS_IDENTITY"
    SITE_IDENTITY = "SITE_IDENTITY"
    APPLICATION_IDENTITY = "APPLICATION_IDENTITY"
    CLOSED_SCHEMA_CHARACTERISTICS = "CLOSED_SCHEMA_CHARACTERISTICS"
    CLOSED_TABLE_CHARACTERISTICS = "CLOSED_TABLE_CHARACTERISTICS"


class ContinuityEvidenceCategory(str, Enum):
    LOGICAL_EXPORT = "LOGICAL_EXPORT"
    RECOVERY_ARTIFACT = "RECOVERY_ARTIFACT"
    PERSISTENT_VOLUME_SNAPSHOT = "PERSISTENT_VOLUME_SNAPSHOT"


@dataclass(frozen=True, slots=True)
class CredentialSourceContract:
    category: SourceCategory = field(default=SourceCategory.CREDENTIAL_SOURCE, init=False)
    mac_control_plane_owned: bool = field(default=True, init=False)
    external_protected_fixed_slot: bool = field(default=True, init=False)
    outside_git: bool = field(default=True, init=False)
    protected_parent_required: bool = field(default=True, init=False)
    parent_mode_0700_required: bool = field(default=True, init=False)
    regular_non_symlink_file_required: bool = field(default=True, init=False)
    file_mode_0600_required: bool = field(default=True, init=False)
    explicit_trusted_uid_gid_required: bool = field(default=True, init=False)
    ambient_home_uid_authority: bool = field(default=False, init=False)
    environment_transport: bool = field(default=False, init=False)
    argv_transport: bool = field(default=False, init=False)
    json_secret_value_transport: bool = field(default=False, init=False)
    governance_transport: bool = field(default=False, init=False)
    secret_value_logging_or_hashing: bool = field(default=False, init=False)
    fallback: bool = field(default=False, init=False)
    enumeration: bool = field(default=False, init=False)
    candidate_iteration: bool = field(default=False, init=False)
    acquisition_maximum: int = field(default=1, init=False)
    acquisition_only_after_capability_consumption: bool = field(
        default=True, init=False
    )


@dataclass(frozen=True, slots=True)
class ExpectedIdentityContract:
    category: SourceCategory = field(
        default=SourceCategory.EXPECTED_IDENTITY_DESCRIPTOR, init=False
    )
    independent_from_credential_evidence: bool = field(default=True, init=False)
    fixed_canonical_profile: bool = field(default=True, init=False)
    expected_database_facts: bool = field(default=True, init=False)
    expected_account_facts: bool = field(default=True, init=False)
    expected_grants_facts: bool = field(default=True, init=False)
    derivation_from_credential_compose_container_or_volume_alone: bool = field(
        default=False, init=False
    )


@dataclass(frozen=True, slots=True)
class DataIdentityContract:
    category: SourceCategory = field(
        default=SourceCategory.DATA_IDENTITY_BASELINE, init=False
    )
    independent_historical_baseline_required: bool = field(default=True, init=False)
    allowed_categories: tuple[DataIdentityCategory, ...] = field(
        default_factory=lambda: tuple(DataIdentityCategory), init=False
    )
    infrastructure_names_alone_sufficient: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class DataContinuityContract:
    category: SourceCategory = field(
        default=SourceCategory.DATA_CONTINUITY_BASELINE, init=False
    )
    independently_verified_historical_lineage_required: bool = field(
        default=True, init=False
    )
    allowed_categories: tuple[ContinuityEvidenceCategory, ...] = field(
        default_factory=lambda: tuple(ContinuityEvidenceCategory), init=False
    )
    artifact_exists: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class MariaDBContinuitySourceContracts:
    credential: CredentialSourceContract = field(
        default_factory=CredentialSourceContract, init=False
    )
    expected_identity: ExpectedIdentityContract = field(
        default_factory=ExpectedIdentityContract, init=False
    )
    data_identity: DataIdentityContract = field(
        default_factory=DataIdentityContract, init=False
    )
    data_continuity: DataContinuityContract = field(
        default_factory=DataContinuityContract, init=False
    )
    credential_source_contract_defined: bool = field(default=True, init=False)
    credential_material_available: bool = field(default=False, init=False)
    expected_identity_source_defined: bool = field(default=True, init=False)
    expected_identity_descriptor_available: bool = field(default=False, init=False)
    data_identity_baseline_contract_defined: bool = field(default=True, init=False)
    data_identity_baseline_available: bool = field(default=False, init=False)
    data_continuity_baseline_contract_defined: bool = field(default=True, init=False)
    data_continuity_baseline_available: bool = field(default=False, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "categories": tuple(item.value for item in SourceCategory),
            "credential_source_contract_defined": self.credential_source_contract_defined,
            "credential_material_available": self.credential_material_available,
            "expected_identity_source_defined": self.expected_identity_source_defined,
            "expected_identity_descriptor_available": self.expected_identity_descriptor_available,
            "data_identity_baseline_contract_defined": self.data_identity_baseline_contract_defined,
            "data_identity_baseline_available": self.data_identity_baseline_available,
            "data_continuity_baseline_contract_defined": self.data_continuity_baseline_contract_defined,
            "data_continuity_baseline_available": self.data_continuity_baseline_available,
            "value_free": True,
        }


def canonical_phase_b1_source_contracts() -> MariaDBContinuitySourceContracts:
    return MariaDBContinuitySourceContracts()
