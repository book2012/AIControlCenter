import ast
import inspect
import re
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_trusted_mac_account_home_policy_source import (
    MariaDBContinuityTrustedMacAccountHomePolicySource,
    canonical_mariadb_continuity_trusted_mac_account_home_policy_source,
)


ROOT = Path(__file__).parents[1]
IMPLEMENTATION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_trusted_mac_account_home_policy.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_trusted_mac_account_home_policy_source.py",
)


def test_implementation_ast_has_no_runtime_lookup_path_or_external_io_capability():
    prohibited_imports = {
        "os", "pwd", "pathlib", "platform", "subprocess", "socket", "pymysql", "docker"
    }
    prohibited_calls = {
        "getuid", "geteuid", "getpwuid", "getenv", "home", "expanduser",
        "resolve", "exists", "stat", "lstat", "open", "read", "read_text",
        "read_bytes", "glob", "rglob", "iterdir", "walk", "listdir", "scandir",
    }
    prohibited_sql = re.compile(
        r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )
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


def test_source_factory_has_zero_inputs_and_projection_is_inert():
    factory = canonical_mariadb_continuity_trusted_mac_account_home_policy_source
    assert not inspect.signature(factory).parameters
    source = factory()
    assert all((source.frozen, source.slotted, source.repository_only, source.zero_io, source.zero_authority, source.mac_aicontrolcenter_sole_control_plane, source.ubuntu_stateless_infrastructure_worker))
    assert not any((source.ubuntu_control_plane_authority, source.account_lookup_exposed, source.path_resolver_exposed, source.home_resolver_exposed, source.filesystem_adapter_exposed, source.protected_source_adapter_exposed, source.production_adapter_exposed, source.authority_bearing_capability_exposed, source.filesystem_io_performed, source.protected_source_access_performed, source.production_access_performed))
    assert all(item.init is False for item in fields(source))
    with pytest.raises(TypeError):
        MariaDBContinuityTrustedMacAccountHomePolicySource(policy="caller-value")
    with pytest.raises(TypeError):
        factory(home="caller-value")
