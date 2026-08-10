"""Declarative A7 adapter compatibility API; no concrete adapters exist here."""

from .compatibility import (
    AdapterCompatibilityMapping,
    AuthorityOwner,
    COMPATIBILITY_MAPPINGS,
    CompatibilityMappingError,
    GovernancePortId,
    IntegrationMode,
    build_compatibility_map,
)

__all__ = (
    "AdapterCompatibilityMapping", "AuthorityOwner", "COMPATIBILITY_MAPPINGS",
    "CompatibilityMappingError", "GovernancePortId", "IntegrationMode",
    "build_compatibility_map",
)
