import ast
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory as FrozenContinuityEvidenceCategory,
)
from core.secrets.mariadb_continuity_descriptors import (
    ContinuityEvidenceCategory,
    ContinuityMetadataFacts,
    DescriptorAvailability,
    DescriptorCategory,
    canonical_continuity_metadata_facts,
    canonical_descriptor_availability,
)


FILE = Path(__file__).parents[1] / "core/secrets/mariadb_continuity_descriptors.py"
AUTHORITY = {"authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"}


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_exact_closed_vocabularies_and_canonical_false_truth():
    assert [item.value for item in DescriptorCategory] == ["EXPECTED_DATABASE_IDENTITY", "EXPECTED_ACCOUNT_IDENTITY", "REQUIRED_GRANTS_PROFILE", "DATA_IDENTITY_BASELINE", "DATA_CONTINUITY_BASELINE"]
    assert [item.value for item in ContinuityEvidenceCategory] == ["LOGICAL_EXPORT", "RECOVERY_ARTIFACT", "PERSISTENT_VOLUME_SNAPSHOT"]
    assert ContinuityEvidenceCategory is FrozenContinuityEvidenceCategory
    assert canonical_descriptor_availability().available_categories == ()
    facts = canonical_continuity_metadata_facts()
    assert facts.ready is False
    assert all(getattr(facts, item.name) is False for item in fields(facts) if item.name.endswith("available") or item.name == "bound_to_data_identity_baseline")


@pytest.mark.parametrize("model, override", [(DescriptorAvailability, {"available_categories": tuple(DescriptorCategory)}), (ContinuityMetadataFacts, {"immutable_artifact_identity_available": True}), (ContinuityMetadataFacts, {"ready": True})])
def test_caller_cannot_forge_canonical_truth(model, override):
    with pytest.raises(TypeError):
        model(**override)


def test_projections_are_value_free_and_zero_authority():
    for projection in (canonical_descriptor_availability().to_projection(), canonical_continuity_metadata_facts().to_projection()):
        assert projection["value_free"] is True
        assert all(projection[key] is False for key in AUTHORITY)
        assert not ({"password", "token", "nonce", "private_key", "dsn", "url", "host", "port", "sql_text"} & set(projection))


def test_descriptor_module_has_no_db_network_or_driver_imports():
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker"})


def test_imported_roots_detects_import_and_import_from_forms():
    tree = ast.parse("""
import pymysql
from pymysql import connect
from mariadb import Connection
from sqlalchemy import create_engine
""")
    assert {"pymysql", "mariadb", "sqlalchemy"} <= imported_roots(tree)
