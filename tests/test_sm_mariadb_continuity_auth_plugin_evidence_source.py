import ast
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_auth_plugin_evidence_source import AuthPluginEvidenceSource, EvidenceSourceOwner, canonical_auth_plugin_evidence_source


FILE = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_auth_plugin_evidence_source.py"


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_symbolic_mac_source_is_canonically_unavailable():
    source = canonical_auth_plugin_evidence_source()
    assert tuple(EvidenceSourceOwner) == (EvidenceSourceOwner.MAC_CONTROL_PLANE,)
    assert source.owner is EvidenceSourceOwner.MAC_CONTROL_PLANE
    assert source.authoritative_evidence_available is False
    assert source.ready is False
    with pytest.raises(TypeError):
        AuthPluginEvidenceSource(authoritative_evidence_available=True)


def test_source_projection_is_value_free_and_zero_authority():
    projection = canonical_auth_plugin_evidence_source().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))


def test_no_inspection_imports_or_calls_exist():
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker", "os", "pathlib", "glob"})
    calls = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))}
    assert calls.isdisjoint({"connect", "execute", "getenv", "environ", "read_text", "read_bytes", "iterdir", "glob", "rglob"})
