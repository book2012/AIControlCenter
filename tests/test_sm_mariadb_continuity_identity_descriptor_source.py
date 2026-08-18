import ast
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_identity_descriptor_source import IdentityDescriptorCategory, IdentityDescriptorSource, canonical_identity_descriptor_source


FILE = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_identity_descriptor_source.py"


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_exact_categories_and_canonical_unavailability():
    assert [item.value for item in IdentityDescriptorCategory] == ["EXPECTED_DATABASE_IDENTITY", "EXPECTED_ACCOUNT_IDENTITY", "REQUIRED_GRANTS_PROFILE"]
    source = canonical_identity_descriptor_source()
    assert source.expected_database_identity_available is False
    assert source.expected_account_identity_available is False
    assert source.required_grants_profile_available is False
    assert source.ready is False


@pytest.mark.parametrize("override", ({"expected_database_identity_available": True}, {"expected_account_identity_available": True}, {"required_grants_profile_available": True}, {"ready": True}, {"categories": ()}))
def test_canonical_identity_cannot_be_caller_forged(override):
    with pytest.raises(TypeError):
        IdentityDescriptorSource(**override)


def test_no_value_derivation_surfaces_or_inspection_imports():
    names = {item.name.lower() for item in fields(IdentityDescriptorSource)}
    assert names.isdisjoint({"credential", "credential_value", "database", "account", "username", "host", "port", "container", "volume"})
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker", "os", "pathlib", "glob"})


def test_projection_is_value_free_and_zero_authority():
    projection = canonical_identity_descriptor_source().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
