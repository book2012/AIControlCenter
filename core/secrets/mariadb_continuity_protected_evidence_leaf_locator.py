"""Repository-owned, lexical-only protected-evidence leaf locations."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import (
    ConcreteProtectedEvidencePath,
)
from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING,
    ProtectedExternalEvidenceConcreteSourceLocationIdentity,
)
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
)


LOCATION_TO_EXACT_LEAF_BASENAME: Mapping[
    ProtectedExternalEvidenceConcreteSourceLocationIdentity, str
] = MappingProxyType({
    ProtectedExternalEvidenceConcreteSourceLocationIdentity.AUTH_PLUGIN_PROTECTED_EVIDENCE_LOCATION:
        "auth-plugin.evidence",
    ProtectedExternalEvidenceConcreteSourceLocationIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION:
        "pymysql-1.2.0-compatibility.evidence",
    ProtectedExternalEvidenceConcreteSourceLocationIdentity.DATA_IDENTITY_PROTECTED_EVIDENCE_LOCATION:
        "data-identity.evidence",
    ProtectedExternalEvidenceConcreteSourceLocationIdentity.CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_LOCATION:
        "continuity-lineage.evidence",
})


@dataclass(frozen=True, slots=True, init=False)
class ConcreteProtectedEvidenceLeafPath:
    """A lexical value with no filesystem fact, capability, or authority."""

    fixed_source_slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity
    concrete_source_location_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    leaf_basename: str
    concrete_parent_path: str
    concrete_leaf_path: str

    def __new__(cls):
        raise TypeError("ConcreteProtectedEvidenceLeafPath is repository-composed only")


def compose_concrete_protected_evidence_leaf_path(
    parent: ConcreteProtectedEvidencePath,
    fixed_source_slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity,
) -> ConcreteProtectedEvidenceLeafPath:
    """Append exactly one frozen basename without normalization or observation."""

    if type(parent) is not ConcreteProtectedEvidencePath:
        raise TypeError("parent must be exactly ConcreteProtectedEvidencePath")
    if type(fixed_source_slot_identity) is not ProtectedExternalEvidenceFixedSourceSlotIdentity:
        raise TypeError("fixed_source_slot_identity has an invalid type")
    location = FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING[fixed_source_slot_identity]
    basename = LOCATION_TO_EXACT_LEAF_BASENAME[location]
    value = object.__new__(ConcreteProtectedEvidenceLeafPath)
    object.__setattr__(value, "fixed_source_slot_identity", fixed_source_slot_identity)
    object.__setattr__(value, "concrete_source_location_identity", location)
    object.__setattr__(value, "leaf_basename", basename)
    object.__setattr__(value, "concrete_parent_path", parent.concrete_path)
    object.__setattr__(value, "concrete_leaf_path", parent.concrete_path + "/" + basename)
    return value


__all__ = (
    "ConcreteProtectedEvidenceLeafPath",
    "LOCATION_TO_EXACT_LEAF_BASENAME",
    "compose_concrete_protected_evidence_leaf_path",
)
