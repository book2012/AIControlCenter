from dataclasses import FrozenInstanceError

import pytest

from core.secrets.mariadb_continuity_concrete_protected_evidence_path import ConcreteProtectedEvidencePath
from core.secrets.mariadb_continuity_evidence_concrete_source_location import FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import ProtectedExternalEvidenceFixedSourceSlotIdentity
from core.secrets.mariadb_continuity_protected_evidence_leaf_locator import LOCATION_TO_EXACT_LEAF_BASENAME, ConcreteProtectedEvidenceLeafPath, compose_concrete_protected_evidence_leaf_path


def parent(path="/synthetic/../lexical"):
    value = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(value, "concrete_path", path)
    return value


def test_exact_four_mapping_and_lexical_composition():
    expected = ("auth-plugin.evidence", "pymysql-1.2.0-compatibility.evidence", "data-identity.evidence", "continuity-lineage.evidence")
    assert tuple(LOCATION_TO_EXACT_LEAF_BASENAME.values()) == expected
    for slot, basename in zip(ProtectedExternalEvidenceFixedSourceSlotIdentity, expected):
        leaf = compose_concrete_protected_evidence_leaf_path(parent(), slot)
        assert leaf.concrete_source_location_identity is FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING[slot]
        assert leaf.concrete_leaf_path == "/synthetic/../lexical/" + basename


def test_no_caller_substitution_direct_construction_or_mutation():
    with pytest.raises(TypeError):
        ConcreteProtectedEvidenceLeafPath()
    with pytest.raises(TypeError):
        compose_concrete_protected_evidence_leaf_path(parent(), "caller")
    leaf = compose_concrete_protected_evidence_leaf_path(parent(), next(iter(ProtectedExternalEvidenceFixedSourceSlotIdentity)))
    with pytest.raises(FrozenInstanceError):
        leaf.leaf_basename = "caller"
    assert not any(hasattr(leaf, name) for name in ("authority", "filesystem_fact", "exists", "authorization"))
