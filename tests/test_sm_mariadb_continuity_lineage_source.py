import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_sources import ContinuityEvidenceCategory
from core.secrets.mariadb_continuity_descriptors import (
    ContinuityEvidenceCategory as DescriptorContinuityEvidenceCategory,
)
from ops.macos.shopping.mariadb_continuity_lineage_source import LineageSource, canonical_lineage_source


ROOT = Path(__file__).parents[1]
FILE = ROOT / "ops/macos/shopping/mariadb_continuity_lineage_source.py"
ACTIONS = {"SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE", "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE", "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE", "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE", "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE", "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE"}


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_closed_evidence_categories_and_canonical_false_readiness():
    source = canonical_lineage_source()
    assert DescriptorContinuityEvidenceCategory is ContinuityEvidenceCategory
    assert source.evidence_categories == tuple(ContinuityEvidenceCategory)
    assert all(type(item) is ContinuityEvidenceCategory for item in source.evidence_categories)
    assert source.continuity_baseline_available is False
    assert source.mandatory_provenance_facts_available is False
    assert source.ready is False
    assert all(getattr(source, item.name) is False for item in fields(source) if item.name.endswith("available") or item.name == "bound_to_data_identity_baseline")


@pytest.mark.parametrize("override", ({"continuity_baseline_available": True}, {"immutable_artifact_identity_available": True}, {"ready": True}, {"evidence_categories": ()}))
def test_readiness_and_facts_cannot_be_caller_supplied(override):
    with pytest.raises(TypeError):
        LineageSource(**override)


def test_no_artifact_filesystem_docker_or_network_inspection():
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker", "os", "pathlib", "glob"})
    calls = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))}
    assert calls.isdisjoint({"open", "read", "read_text", "read_bytes", "iterdir", "glob", "rglob", "connect", "execute"})


def test_exact_actions_and_target_only_are_preserved_by_ast():
    path = ROOT / "ops/macos/shopping/secret_provisioning_adapters.py"
    tree = ast.parse(path.read_text())
    assignments = {target.id: node.value.value for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) for target in ((node.targets if isinstance(node, ast.Assign) else [node.target])) if isinstance(target, ast.Name)}
    discovered = {value for value in assignments.values() if re.fullmatch(r"SHOPPING_SECRET_(?:TOOL|IDENTITY|RECIPIENT):.+", value)}
    assert discovered == ACTIONS
    assert assignments["SHOPPING_SECRET_PROVISIONING"] == "SHOPPING_SECRET_PROVISIONING"
    assert "SHOPPING_SECRET_PROVISIONING" not in discovered


def test_projection_is_value_free_and_zero_authority():
    projection = canonical_lineage_source().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
