from __future__ import annotations

import ast
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SERVICE = (
    REPOSITORY
    / "core/governance/operations/application/service.py"
)
HELPERS = (
    REPOSITORY
    / "tests/model_governance/audit_operations/"
    "application_helpers.py"
)

TARGET_METHODS = {"execute", "verify"}


def _tree(path: Path) -> ast.Module:
    return ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )


def test_application_capability_calls_only_receive_scheduled_for() -> None:
    calls = [
        node
        for node in ast.walk(_tree(SERVICE))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in TARGET_METHODS
        )
    ]

    assert {
        node.func.attr
        for node in calls
    } == TARGET_METHODS

    for node in calls:
        assert {
            keyword.arg
            for keyword in node.keywords
        } == {"scheduled_for"}


def test_application_doubles_match_capability_boundary() -> None:
    methods = {
        node.name: node
        for node in ast.walk(_tree(HELPERS))
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in TARGET_METHODS
        )
    }

    assert set(methods) == TARGET_METHODS

    for method in methods.values():
        parameters = {
            argument.arg
            for argument in (
                method.args.posonlyargs
                + method.args.args
                + method.args.kwonlyargs
            )
        }

        assert "run_id" not in parameters
        assert "scheduled_for" in parameters
