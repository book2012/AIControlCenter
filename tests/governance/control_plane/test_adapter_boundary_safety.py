"""AST and metadata safety checks for the non-operational A7 boundary."""

from __future__ import annotations

import ast
from pathlib import Path

from core.governance.control_plane.adapters.compatibility import COMPATIBILITY_MAPPINGS


ROOT = Path(__file__).parents[3]
A7_MODULES = tuple(sorted(
    (ROOT / "core/governance/control_plane/ports").glob("*.py")
)) + tuple(sorted(
    (ROOT / "core/governance/control_plane/adapters").glob("*.py")
))
PROHIBITED_IMPORT_ROOTS = {
    "os", "pathlib", "subprocess", "sqlite3", "socket", "urllib", "http", "requests",
    "aiohttp", "core.deployment", "core.shopping", "ops",
}
PROHIBITED_API_MARKERS = {
    "authorize", "approve", "retry", "rollback", "compensate", "widen_scope",
    "widen_budget", "launchctl", "checkout", "reset", "commit", "push", "fetch",
    "getenv", "environ",
}


def _trees() -> tuple[ast.AST, ...]:
    return tuple(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in A7_MODULES)


def test_a7_modules_do_not_import_operational_or_side_effect_facilities() -> None:
    imports: list[str] = []
    for tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not any(
        name == root or name.startswith(root + ".")
        for name in imports for root in PROHIBITED_IMPORT_ROOTS
    )


def test_a7_exposes_no_mutation_control_or_secret_environment_api() -> None:
    defined_names = {
        node.name.lower()
        for tree in _trees()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not any(marker in name for name in defined_names for marker in PROHIBITED_API_MARKERS)


def test_no_production_mutation_loop_exists() -> None:
    assert not any(isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for tree in _trees() for node in ast.walk(tree))


def test_ubuntu_has_no_governance_mapping_or_adapter() -> None:
    assert all("UBUNTU" not in mapping.capability_id for mapping in COMPATIBILITY_MAPPINGS.values())
    assert all("UBUNTU" not in mapping.authority_owner.value for mapping in COMPATIBILITY_MAPPINGS.values())


def test_shopping_mapping_retains_business_logic_outside_governance() -> None:
    mapping = COMPATIBILITY_MAPPINGS["SHOPPING_DEPLOYMENT_AUTHORIZATION_IDEMPOTENCY"]
    assert mapping.authority_owner.value == "AICONTROLCENTER_SHOPPING_DOMAIN"
    assert mapping.existing_boundary.startswith("core/shopping/")


def test_future_operational_mappings_have_no_concrete_adapter() -> None:
    assert all(not mapping.concrete_adapter_present for mapping in COMPATIBILITY_MAPPINGS.values())
