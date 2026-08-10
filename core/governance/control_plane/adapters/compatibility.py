"""Immutable, declarative A7 mappings for future governance adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Iterable, Mapping


class IntegrationMode(StrEnum):
    REUSE_UNCHANGED_BEHIND_PORT = "REUSE_UNCHANGED_BEHIND_PORT"
    WRAP_AS_ADAPTER_LATER = "WRAP_AS_ADAPTER_LATER"
    RETAIN_DOMAIN_SPECIFIC = "RETAIN_DOMAIN_SPECIFIC"
    REFACTOR_BEFORE_INTEGRATION = "REFACTOR_BEFORE_INTEGRATION"


class GovernancePortId(StrEnum):
    PRECONDITION_OBSERVATION = "PRECONDITION_OBSERVATION"
    GIT_READONLY_EVIDENCE = "GIT_READONLY_EVIDENCE"
    RUNTIME_IDENTITY_OBSERVATION = "RUNTIME_IDENTITY_OBSERVATION"
    AUDIT = "AUDIT"
    EVIDENCE_PERSISTENCE = "EVIDENCE_PERSISTENCE"
    CONTROLLED_EXECUTION = "CONTROLLED_EXECUTION"
    OPERATIONAL_AUDIT_READ_MODEL = "OPERATIONAL_AUDIT_READ_MODEL"
    SHOPPING_DOMAIN = "SHOPPING_DOMAIN"


class AuthorityOwner(StrEnum):
    GOVERNANCE_CONTROL_PLANE = "AICONTROLCENTER_GOVERNANCE_CONTROL_PLANE"
    GOVERNANCE_OPERATIONS = "AICONTROLCENTER_GOVERNANCE_OPERATIONS"
    SHOPPING_DOMAIN = "AICONTROLCENTER_SHOPPING_DOMAIN"


class CompatibilityMappingError(ValueError):
    """Declarative compatibility catalog is structurally invalid."""


@dataclass(frozen=True, slots=True)
class AdapterCompatibilityMapping:
    capability_id: str
    existing_boundary: str
    governance_port: GovernancePortId
    integration_mode: IntegrationMode
    authority_owner: AuthorityOwner
    read_only: bool
    concrete_adapter_present: bool
    classification_code: str


def build_compatibility_map(
    entries: Iterable[AdapterCompatibilityMapping],
) -> Mapping[str, AdapterCompatibilityMapping]:
    """Build a deterministic immutable catalog and reject duplicate identities."""
    ordered = sorted(tuple(entries), key=lambda item: item.capability_id)
    identifiers = tuple(item.capability_id for item in ordered)
    if len(identifiers) != len(set(identifiers)):
        raise CompatibilityMappingError("duplicate capability_id")
    return MappingProxyType({item.capability_id: item for item in ordered})


COMPATIBILITY_MAPPINGS = build_compatibility_map((
    AdapterCompatibilityMapping(
        "DEPLOYMENT_PREFLIGHT", "core/deployment/operational_bootstrap_preflight/",
        GovernancePortId.PRECONDITION_OBSERVATION, IntegrationMode.WRAP_AS_ADAPTER_LATER,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, True, False,
        "PURE_VALIDATORS_REUSABLE_OPERATIONAL_COLLECTION_ADAPTER_SIDE",
    ),
    AdapterCompatibilityMapping(
        "GIT_READONLY_EVIDENCE", "core/deployment/git_readonly_evidence/",
        GovernancePortId.GIT_READONLY_EVIDENCE, IntegrationMode.REUSE_UNCHANGED_BEHIND_PORT,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, True, False,
        "READ_ONLY_EVIDENCE_REUSE",
    ),
    AdapterCompatibilityMapping(
        "MACOS_RUNTIME_IDENTITY", "ops/macos/runtime/",
        GovernancePortId.RUNTIME_IDENTITY_OBSERVATION, IntegrationMode.WRAP_AS_ADAPTER_LATER,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, True, False,
        "OBSERVATION_ONLY_NO_ACTIVATION_OR_RESTART",
    ),
    AdapterCompatibilityMapping(
        "DEPLOYMENT_AUDIT", "core/deployment/audit_contracts/;core/deployment/audit_sqlite/;core/deployment/audit_sqlite_writer/;core/deployment/audit_sqlite_recovery/",
        GovernancePortId.AUDIT, IntegrationMode.REUSE_UNCHANGED_BEHIND_PORT,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, False, False,
        "CONTRACT_PORT_WRITER_RECOVERY_REUSE_POLICY_REMAINS_GOVERNANCE",
    ),
    AdapterCompatibilityMapping(
        "GOVERNANCE_OPERATIONS", "core/governance/operations/",
        GovernancePortId.OPERATIONAL_AUDIT_READ_MODEL, IntegrationMode.RETAIN_DOMAIN_SPECIFIC,
        AuthorityOwner.GOVERNANCE_OPERATIONS, True, False,
        "AUDIT_SCHEDULER_READ_MODEL_NOT_AUTHORIZATION_AUTHORITY",
    ),
    AdapterCompatibilityMapping(
        "OPERATIONAL_BOOTSTRAP_EXECUTION", "core/deployment/operational_bootstrap_execution/",
        GovernancePortId.CONTROLLED_EXECUTION, IntegrationMode.WRAP_AS_ADAPTER_LATER,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, False, False,
        "ONE_BOUNDED_INVOCATION_NO_INTERNAL_RETRY_OR_ROLLBACK",
    ),
    AdapterCompatibilityMapping(
        "BOOTSTRAP_EVIDENCE_RECOVERY", "core/deployment/bootstrap_evidence_recovery/",
        GovernancePortId.EVIDENCE_PERSISTENCE, IntegrationMode.REFACTOR_BEFORE_INTEGRATION,
        AuthorityOwner.GOVERNANCE_CONTROL_PLANE, False, False,
        "CHAIN_RECOVERY_REUSABLE_PRIVATE_TMP_NOT_DURABLE_GOVERNANCE_STORAGE",
    ),
    AdapterCompatibilityMapping(
        "SHOPPING_DEPLOYMENT_AUTHORIZATION_IDEMPOTENCY", "core/shopping/product_drafts/deployment/authorization.py;core/shopping/product_drafts/deployment/idempotency.py",
        GovernancePortId.SHOPPING_DOMAIN, IntegrationMode.RETAIN_DOMAIN_SPECIFIC,
        AuthorityOwner.SHOPPING_DOMAIN, False, False,
        "SHOPPING_ELIGIBILITY_BUSINESS_WRITES_RETAINED_GENERIC_SAFETY_FROM_GOVERNANCE",
    ),
))


__all__ = (
    "AdapterCompatibilityMapping", "AuthorityOwner", "COMPATIBILITY_MAPPINGS",
    "CompatibilityMappingError", "GovernancePortId", "IntegrationMode",
    "build_compatibility_map",
)
