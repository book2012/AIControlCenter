"""Deterministic contracts for A7's declarative compatibility catalog."""

from __future__ import annotations

import pytest

from core.governance.control_plane.adapters.compatibility import (
    AdapterCompatibilityMapping,
    AuthorityOwner,
    COMPATIBILITY_MAPPINGS,
    CompatibilityMappingError,
    GovernancePortId,
    IntegrationMode,
    build_compatibility_map,
)


REQUIRED = {
    "DEPLOYMENT_PREFLIGHT", "GIT_READONLY_EVIDENCE", "MACOS_RUNTIME_IDENTITY",
    "DEPLOYMENT_AUDIT", "GOVERNANCE_OPERATIONS", "OPERATIONAL_BOOTSTRAP_EXECUTION",
    "BOOTSTRAP_EVIDENCE_RECOVERY", "SHOPPING_DEPLOYMENT_AUTHORIZATION_IDEMPOTENCY",
}


def test_all_required_existing_capabilities_are_mapped_deterministically() -> None:
    assert set(COMPATIBILITY_MAPPINGS) == REQUIRED
    assert tuple(COMPATIBILITY_MAPPINGS) == tuple(sorted(REQUIRED))
    assert all(key == value.capability_id for key, value in COMPATIBILITY_MAPPINGS.items())


def test_duplicate_capability_ids_are_rejected() -> None:
    item = next(iter(COMPATIBILITY_MAPPINGS.values()))
    with pytest.raises(CompatibilityMappingError, match="duplicate capability_id"):
        build_compatibility_map((item, item))


def test_integration_modes_are_closed_and_stable() -> None:
    assert tuple(mode.value for mode in IntegrationMode) == (
        "REUSE_UNCHANGED_BEHIND_PORT", "WRAP_AS_ADAPTER_LATER",
        "RETAIN_DOMAIN_SPECIFIC", "REFACTOR_BEFORE_INTEGRATION",
    )
    assert COMPATIBILITY_MAPPINGS["GIT_READONLY_EVIDENCE"].integration_mode is IntegrationMode.REUSE_UNCHANGED_BEHIND_PORT
    assert COMPATIBILITY_MAPPINGS["OPERATIONAL_BOOTSTRAP_EXECUTION"].integration_mode is IntegrationMode.WRAP_AS_ADAPTER_LATER


def test_generic_safety_policy_authority_is_governance() -> None:
    generic = REQUIRED - {
        "GOVERNANCE_OPERATIONS", "SHOPPING_DEPLOYMENT_AUTHORIZATION_IDEMPOTENCY"
    }
    assert all(
        COMPATIBILITY_MAPPINGS[key].authority_owner is AuthorityOwner.GOVERNANCE_CONTROL_PLANE
        for key in generic
    )


def test_governance_operations_is_read_model_not_authorization_authority() -> None:
    mapping = COMPATIBILITY_MAPPINGS["GOVERNANCE_OPERATIONS"]
    assert mapping.governance_port is GovernancePortId.OPERATIONAL_AUDIT_READ_MODEL
    assert mapping.integration_mode is IntegrationMode.RETAIN_DOMAIN_SPECIFIC
    assert mapping.authority_owner is AuthorityOwner.GOVERNANCE_OPERATIONS
    assert "NOT_AUTHORIZATION_AUTHORITY" in mapping.classification_code


def test_shopping_business_semantics_remain_domain_specific() -> None:
    mapping = COMPATIBILITY_MAPPINGS["SHOPPING_DEPLOYMENT_AUTHORIZATION_IDEMPOTENCY"]
    assert mapping.governance_port is GovernancePortId.SHOPPING_DOMAIN
    assert mapping.integration_mode is IntegrationMode.RETAIN_DOMAIN_SPECIFIC
    assert mapping.authority_owner is AuthorityOwner.SHOPPING_DOMAIN
    assert "BUSINESS_WRITES_RETAINED" in mapping.classification_code


def test_bootstrap_evidence_requires_durable_storage_refactor() -> None:
    mapping = COMPATIBILITY_MAPPINGS["BOOTSTRAP_EVIDENCE_RECOVERY"]
    assert mapping.integration_mode is IntegrationMode.REFACTOR_BEFORE_INTEGRATION
    assert "PRIVATE_TMP_NOT_DURABLE" in mapping.classification_code


def test_no_mapping_claims_a_concrete_production_adapter() -> None:
    assert all(not mapping.concrete_adapter_present for mapping in COMPATIBILITY_MAPPINGS.values())
