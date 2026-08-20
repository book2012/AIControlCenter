import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_evidence_concrete_source_location_source import (
    MariaDBContinuityEvidenceConcreteSourceLocationSource,
    canonical_mariadb_continuity_evidence_concrete_source_location_source,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_evidence_concrete_source_location.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_evidence_concrete_source_location_source.py",
)


def test_production_ast_has_zero_filesystem_environment_network_process_or_sql():
    prohibited_imports = {"pathlib", "os", "glob", "socket", "subprocess", "pymysql", "docker"}
    prohibited_calls = {"open", "exists", "stat", "lstat", "resolve", "read_text", "read_bytes", "scandir", "glob", "rglob", "getenv"}
    prohibited_sql = re.compile(r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b", re.IGNORECASE)
    for path in PRODUCTION_FILES:
        source = path.read_text()
        tree = ast.parse(source)
        imported = {
            alias.name.split(".")[0].lower()
            for node in ast.walk(tree)
            for alias in (node.names if isinstance(node, ast.Import) else ())
        }
        imported.update(
            node.module.split(".")[0].lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        calls = {
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
        }
        assert imported.isdisjoint(prohibited_imports)
        assert calls.isdisjoint(prohibited_calls)
        assert prohibited_sql.search(source) is None


def test_mac_projection_is_frozen_inert_and_control_plane_safe():
    source = canonical_mariadb_continuity_evidence_concrete_source_location_source()
    assert all((source.frozen, source.slotted, source.repository_only, source.zero_io, source.zero_authority, source.mac_aicontrolcenter_sole_control_plane, source.ubuntu_stateless_infrastructure_worker))
    assert not any((source.ubuntu_control_plane_authority, source.absolute_path_composer_exposed, source.filesystem_io_performed, source.metadata_inspection_performed, source.content_acquisition_performed, source.network_performed, source.process_performed, source.sql_performed, source.production_access_performed, source.runtime_mutation_performed))
    assert all(item.init is False for item in fields(source))
    with pytest.raises(TypeError):
        MariaDBContinuityEvidenceConcreteSourceLocationSource(zero_io=False)
