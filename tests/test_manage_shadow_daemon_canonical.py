from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "manage_shadow_daemon_canonical.py"
)


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "manage_shadow_daemon_canonical",
            MODULE_PATH,
        )
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(
        specification
    )

    specification.loader.exec_module(
        module
    )

    return module


def test_manager_module_exists() -> None:
    assert MODULE_PATH.is_file()


def test_preflight_passes() -> None:
    module = load_module()

    result = module.manager_result(
        action="preflight",
        root=ROOT,
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False


def test_plan_passes() -> None:
    module = load_module()

    result = module.manager_result(
        action="plan",
        root=ROOT,
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False

    assert result["plan"][
        "installation_plan"
    ]


def test_dry_run_executes_no_writes() -> None:
    module = load_module()

    result = module.manager_result(
        action="dry-run",
        root=ROOT,
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False

    executor = result["executor"]

    assert executor[
        "write_operations_executed"
    ] is False

    assert executor["results"] == []


def test_apply_without_authorization_is_blocked() -> None:
    module = load_module()

    result = module.manager_result(
        action="apply",
        root=ROOT,
        confirmation="",
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is False

    assert result[
        "write_operations_executed"
    ] is False

    assert result["executor"][
        "failure"
    ]["step"] == (
        "system_write_authorization"
    )


def test_results_are_json_serializable() -> None:
    module = load_module()

    for action in (
        "preflight",
        "plan",
        "dry-run",
    ):
        result = module.manager_result(
            action=action,
            root=ROOT,
        )

        json.dumps(result)


def test_manager_preserves_json_first_contract() -> None:
    module = load_module()

    result = module.manager_result(
        action="dry-run",
        root=ROOT,
    )

    assert result["schema_version"] == "1.0"
    assert result["action"] == "dry-run"

    assert isinstance(
        result["executor"]["commands"],
        list,
    )
