import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_evidence_reference_manifest import EvidenceReferenceManifest
from ops.macos.shopping.mariadb_continuity_evidence_reference_source import (
    EvidenceReferenceSource,
    canonical_evidence_reference_source,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_evidence_reference_manifest.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_evidence_reference_source.py",
)
ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_production_sources_have_no_io_network_sql_or_runtime_imports():
    prohibited = {
        "pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket",
        "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker",
        "pathlib", "os", "glob",
    }
    prohibited_calls = {
        "open", "stat", "read", "read_text", "read_bytes", "connect", "execute",
        "run", "popen", "getenv",
    }
    for path in PRODUCTION_FILES:
        source = path.read_text()
        tree = ast.parse(source)
        assert imported_roots(tree).isdisjoint(prohibited)
        calls = {
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
        }
        assert calls.isdisjoint(prohibited_calls)
        assert "SHOPPING_SECRET_PROVISIONING" not in source


def test_source_is_non_injectable_zero_authority_and_value_free():
    source = canonical_evidence_reference_source()
    assert type(source.manifest) is EvidenceReferenceManifest
    projection = source.to_projection()
    assert projection["mac_control_plane_owned"] is True
    assert projection["ubuntu_control_plane_authority"] is False
    assert projection["value_free"] is True
    authority_keys = (
        "authorization_authority", "capability_authority", "execution_authority",
        "mutation_authority", "retry_authority", "reconnect_authority",
        "rollback_authority",
    )
    assert all(projection[key] is False for key in authority_keys)
    assert all(projection[key] is False for key in (
        "evidence_exists", "provenance_valid", "authority", "compatible",
        "reference_readiness_established",
        "recover_evidence_sufficient",
    ))
    for item in fields(EvidenceReferenceSource):
        with pytest.raises(TypeError):
            EvidenceReferenceSource(**{item.name: True})


def test_exact_six_actions_and_target_only_semantics_remain_unchanged():
    path = ROOT / "ops/macos/shopping/secret_provisioning_adapters.py"
    tree = ast.parse(path.read_text())
    assignments = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name)
    }
    discovered = {
        value for value in assignments.values()
        if re.fullmatch(r"SHOPPING_SECRET_(?:TOOL|IDENTITY|RECIPIENT):.+", value)
    }
    assert discovered == ACTIONS
    assert assignments["SHOPPING_SECRET_PROVISIONING"] == "SHOPPING_SECRET_PROVISIONING"
    assert "SHOPPING_SECRET_PROVISIONING" not in discovered
