import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_fixed_sql_profile import (
    ARBITRARY_SQL_ALLOWED,
    FIXED_SQL_TEXT_AVAILABLE,
    FixedOperationProfile,
    FixedSQLProfileContract,
    FixedValidationCategory,
    canonical_fixed_sql_profile,
)


FILE = Path(__file__).parents[1] / "core/secrets/mariadb_continuity_fixed_sql_profile.py"
EXPECTED = ["CREDENTIAL_ACCEPTED", "EXPECTED_DATABASE_IDENTITY", "EXPECTED_ACCOUNT_IDENTITY", "REQUIRED_GRANTS", "EXPECTED_DATA_IDENTITY", "DECLARED_DATA_CONTINUITY"]


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_option_a_profile_and_exact_closed_categories():
    assert [item.value for item in FixedValidationCategory] == EXPECTED
    assert tuple(FixedOperationProfile) == (FixedOperationProfile.CLOSED_MARIADB_CONTINUITY_VALIDATION,)
    profile = canonical_fixed_sql_profile()
    assert [item.value for item in profile.validation_categories] == EXPECTED
    assert profile.fixed_sql_text_available is FIXED_SQL_TEXT_AVAILABLE is False
    assert profile.arbitrary_sql_allowed is ARBITRARY_SQL_ALLOWED is False


@pytest.mark.parametrize("override", ({"fixed_sql_text_available": True}, {"arbitrary_sql_allowed": True}, {"validation_categories": ()}, {"profile": "caller"}))
def test_profile_cannot_be_forged(override):
    with pytest.raises(TypeError):
        FixedSQLProfileContract(**override)


def test_no_executable_sql_literals_or_execution_imports():
    source = FILE.read_text()
    tree = ast.parse(source)
    literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    statement = re.compile(r"^\s*(?:SELECT|SHOW|GRANT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", re.I)
    assert not any(statement.search(value) for value in literals)
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker"})
    assert {item.name for item in fields(FixedSQLProfileContract)}.isdisjoint({"sql", "sql_text", "statement", "query"})


def test_projection_is_value_free_and_zero_authority():
    projection = canonical_fixed_sql_profile().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
