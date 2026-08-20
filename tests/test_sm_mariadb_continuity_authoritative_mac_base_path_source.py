import ast
import re
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_authoritative_mac_base_path_source import (
    MariaDBContinuityAuthoritativeMacBasePathPolicySource,
    canonical_mariadb_continuity_authoritative_mac_base_path_policy_source,
)


ROOT = Path(__file__).parents[1]
IMPLEMENTATION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_authoritative_mac_base_path.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_authoritative_mac_base_path_source.py",
)


def test_implementation_ast_has_no_runtime_path_or_external_io_capability():
    prohibited_imports = {"pathlib", "os", "pwd", "sys", "glob", "socket", "subprocess", "pymysql", "docker"}
    prohibited_calls = {"open", "exists", "stat", "lstat", "resolve", "realpath", "is_file", "is_dir", "is_symlink", "read", "read_text", "read_bytes", "glob", "rglob", "iterdir", "walk", "listdir", "scandir", "getenv", "getpwuid", "getuid", "getgid"}
    prohibited_sql = re.compile(r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b", re.IGNORECASE)
    for path in IMPLEMENTATION_FILES:
        source_text = path.read_text()
        tree = ast.parse(source_text)
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
        assert prohibited_sql.search(source_text) is None


def test_source_projection_is_inert_and_preserves_control_plane_ownership():
    source = canonical_mariadb_continuity_authoritative_mac_base_path_policy_source()
    assert all((source.frozen, source.slotted, source.repository_only, source.zero_io, source.zero_authority, source.mac_aicontrolcenter_sole_control_plane, source.ubuntu_stateless_infrastructure_worker))
    assert not any((source.ubuntu_control_plane_authority, source.path_resolver_exposed, source.home_resolver_exposed, source.filesystem_adapter_exposed, source.metadata_inspector_exposed, source.content_reader_exposed, source.production_adapter_exposed, source.authority_bearing_capability_exposed, source.filesystem_io_performed, source.protected_source_access_performed, source.production_access_performed))
    assert all(item.init is False for item in fields(source))
    with pytest.raises(TypeError):
        MariaDBContinuityAuthoritativeMacBasePathPolicySource(zero_io=False)
