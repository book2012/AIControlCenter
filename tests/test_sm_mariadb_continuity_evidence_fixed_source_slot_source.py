import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    MariaDBContinuityEvidenceFixedSourceSlotContract,
)
from ops.macos.shopping.mariadb_continuity_evidence_fixed_source_slot_source import (
    MariaDBContinuityEvidenceFixedSourceSlotSource,
    canonical_mariadb_continuity_evidence_fixed_source_slot_source,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_evidence_fixed_source_slot.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_evidence_fixed_source_slot_source.py",
)
ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}


def _imported_roots(tree: ast.AST) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_production_ast_has_zero_filesystem_network_database_process_or_sql():
    prohibited_imports = {
        "pathlib", "os", "glob", "socket", "requests", "urllib", "httpx",
        "aiohttp", "subprocess", "pymysql", "mysql", "mariadb", "sqlalchemy",
        "docker",
    }
    prohibited_calls = {
        "open", "stat", "read", "read_text", "read_bytes", "connect", "execute",
        "run", "popen", "getenv", "resolve", "acquire", "inspect_metadata",
    }
    prohibited_sql = re.compile(
        r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )
    for path in PRODUCTION_FILES:
        source = path.read_text()
        tree = ast.parse(source)
        assert _imported_roots(tree).isdisjoint(prohibited_imports)
        calls = {
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Attribute, ast.Name))
        }
        assert calls.isdisjoint(prohibited_calls)
        assert prohibited_sql.search(source) is None
        assert "SHOPPING_SECRET_PROVISIONING" not in source


def test_mac_projection_is_frozen_slotted_inert_and_control_plane_safe():
    source = canonical_mariadb_continuity_evidence_fixed_source_slot_source()
    assert type(source.contract) is MariaDBContinuityEvidenceFixedSourceSlotContract
    assert all((
        source.frozen,
        source.slotted,
        source.repository_only,
        source.zero_io,
        source.zero_authority,
        source.mac_aicontrolcenter_sole_control_plane,
        source.ubuntu_stateless_infrastructure_worker,
    ))
    assert not any((
        source.ubuntu_control_plane_authority,
        source.path_resolver_exposed,
        source.filesystem_io_performed,
        source.metadata_inspection_performed,
        source.source_resolution_performed,
        source.content_acquisition_performed,
        source.evidence_admission_performed,
        source.evidence_verification_performed,
        source.network_performed,
        source.process_performed,
        source.sql_performed,
        source.production_access_performed,
        source.runtime_mutation_performed,
    ))
    for item in fields(source):
        assert item.init is False
        with pytest.raises(TypeError):
            MariaDBContinuityEvidenceFixedSourceSlotSource(**{item.name: True})


def test_projection_exposes_no_resolver_path_metadata_or_acquisition_method():
    method_names = {
        name.lower()
        for name, value in vars(MariaDBContinuityEvidenceFixedSourceSlotSource).items()
        if callable(value)
    }
    prohibited_fragments = {
        "resolver", "path", "filesystem", "reader", "metadata", "acquisition",
        "acquire", "network", "process", "sql", "database", "connect",
    }
    assert not any(
        fragment in method_name
        for method_name in method_names
        for fragment in prohibited_fragments
    )


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
