from __future__ import annotations

import ast
from pathlib import Path


def _imports(root: Path) -> set[str]:
    found: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
    return found


def test_no_ubuntu_adapter_or_generic_command_port_exists() -> None:
    adapter_files = [path.name.lower() for path in Path("core/deployment/adapters").rglob("*.py")]
    port_text = Path("core/deployment/ports/inventory.py").read_text("utf-8").lower()
    assert not any("ubuntu" in name for name in adapter_files)
    assert "commandexecution" not in port_text
    assert "shellrunner" not in port_text


def test_adapters_do_not_import_mutating_or_remote_executors() -> None:
    imports = _imports(Path("core/deployment/adapters/macos"))
    prohibited = {
        "core.worker",
        "paramiko",
        "subprocess",
        "core.deployment.inspect",
        "ops.macos.launchd.canonical_shadow_daemon_executor",
    }
    assert not any(
        imported == denied or imported.startswith(denied + ".")
        for imported in imports
        for denied in prohibited
    )


def test_no_api_route_was_added_under_inventory_layers() -> None:
    text = "\n".join(
        path.read_text("utf-8")
        for root in (
            Path("core/deployment/application"),
            Path("core/deployment/ports"),
            Path("core/deployment/adapters/macos"),
        )
        for path in root.rglob("*.py")
    )
    assert "APIRouter" not in text
    assert "@app." not in text
