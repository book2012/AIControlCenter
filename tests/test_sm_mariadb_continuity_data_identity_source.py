import ast
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_sources import DataIdentityCategory
from ops.macos.shopping.mariadb_continuity_data_identity_source import DataIdentitySource, canonical_data_identity_source


FILE = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_data_identity_source.py"


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_closed_categories_and_historical_baseline_unavailable():
    expected = ["WORDPRESS_IDENTITY", "SITE_IDENTITY", "APPLICATION_IDENTITY", "CLOSED_SCHEMA_CHARACTERISTICS", "CLOSED_TABLE_CHARACTERISTICS"]
    assert [item.value for item in DataIdentityCategory] == expected
    source = canonical_data_identity_source()
    assert source.fact_categories == tuple(DataIdentityCategory)
    assert all(type(item) is DataIdentityCategory for item in source.fact_categories)
    assert source.historical_data_identity_baseline_available is False
    assert source.ready is False
    with pytest.raises(TypeError):
        DataIdentitySource(historical_data_identity_baseline_available=True)
    with pytest.raises(TypeError):
        DataIdentitySource(ready=True)


def test_no_invented_data_identity_value_fields():
    names = {item.name.lower() for item in fields(DataIdentitySource)}
    assert names.isdisjoint({"db_name", "site_url", "table_names", "schema_digest", "site_id", "application_id", "value", "host", "port"})
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker", "os", "pathlib", "glob"})


def test_projection_is_value_free_and_zero_authority():
    projection = canonical_data_identity_source().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
