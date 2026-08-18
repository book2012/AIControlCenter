import ast
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_credential_slot_resolver import CredentialSlot, CredentialSlotResolution, ResolverOwner, canonical_credential_slot_resolution


FILE = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_credential_slot_resolver.py"


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_closed_mac_owned_slot_and_future_requirements():
    resolution = canonical_credential_slot_resolution()
    assert tuple(CredentialSlot) == (CredentialSlot.FIXED_AUTHORITATIVE_PRODUCTION_SLOT,)
    assert tuple(ResolverOwner) == (ResolverOwner.MAC_CONTROL_PLANE,)
    assert resolution.owner is ResolverOwner.MAC_CONTROL_PLANE
    assert resolution.fixed_authoritative_slot_required is True
    assert resolution.protected_parent_required is True
    assert resolution.trusted_uid_gid_required is True
    assert resolution.fd_inode_binding_future_requirement is True
    assert resolution.one_value_acquisition_maximum is True
    assert resolution.acquisition_after_capability_consumption_required is True
    assert resolution.canonical_credential_available is False
    assert resolution.ready is False


@pytest.mark.parametrize("override", ({"canonical_credential_available": True}, {"slot": "caller-path"}, {"ready": True}))
def test_no_caller_path_or_availability_authority(override):
    with pytest.raises(TypeError):
        CredentialSlotResolution(**override)


def test_no_path_home_environment_fallback_enumeration_or_content_read():
    source = FILE.read_text()
    tree = ast.parse(source)
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker", "os", "pathlib", "glob"})
    calls = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))}
    assert calls.isdisjoint({"getenv", "expanduser", "home", "iterdir", "glob", "rglob", "listdir", "walk", "open", "read", "read_text", "read_bytes", "observe_fixed_protected_source"})
    names = {item.name.lower() for item in fields(CredentialSlotResolution)}
    assert names.isdisjoint({"path", "home", "host", "port", "value", "password", "token", "candidates", "fallback"})


def test_projection_is_value_free_and_zero_authority():
    projection = canonical_credential_slot_resolution().to_projection()
    assert projection["value_free"] is True
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
