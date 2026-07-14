from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from types import ModuleType
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "manage-shadow-daemon.py"
)


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "manage_shadow_daemon_entrypoint",
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


def test_public_manager_entrypoint_exists() -> None:
    assert MODULE_PATH.is_file()


def test_canonical_action_mapping() -> None:
    module = load_module()

    assert module.CANONICAL_ACTION_MAP == {
        "canonical-preflight": "preflight",
        "canonical-plan": "plan",
        "canonical-dry-run": "dry-run",
        "canonical-apply": "apply",
    }


def test_canonical_preflight_passes() -> None:
    module = load_module()

    result = module.run_canonical(
        action_token="canonical-preflight",
        root=ROOT,
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False


def test_canonical_dry_run_executes_no_writes() -> None:
    module = load_module()

    result = module.run_canonical(
        action_token="canonical-dry-run",
        root=ROOT,
    )

    assert result[
        "canonical_manager_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False

    assert result["executor"][
        "results"
    ] == []


def test_canonical_result_is_json_serializable() -> None:
    module = load_module()

    result = module.run_canonical(
        action_token="canonical-plan",
        root=ROOT,
    )

    json.dumps(result)


def test_legacy_command_preserves_arguments() -> None:
    module = load_module()

    command = module.build_legacy_command(
        [
            "status",
            "--json",
        ]
    )

    assert command[0]

    assert command[1] == str(
        module.LEGACY_MANAGER
    )

    assert command[1].endswith(
        "_shadow_daemon_legacy.py"
    )

    assert not command[1].endswith(
        "/manage-shadow-daemon.py"
    )

    assert command[2:] == [
        "status",
        "--json",
    ]


def test_legacy_runner_preserves_return_code() -> None:
    module = load_module()

    calls: list[list[str]] = []

    def fake_runner(
        command: Sequence[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            list(command)
        )

        assert kwargs["check"] is False

        return subprocess.CompletedProcess(
            args=list(command),
            returncode=23,
            stdout="",
            stderr="",
        )

    completed = module.run_legacy(
        [
            "status",
            "--json",
        ],
        runner=fake_runner,
    )

    assert completed.returncode == 23

    assert calls[0][2:] == [
        "status",
        "--json",
    ]


def test_noncanonical_action_uses_legacy_path() -> None:
    module = load_module()

    assert (
        "status"
        not in module.CANONICAL_ACTION_MAP
    )

    command = module.build_legacy_command(
        ["status"]
    )

    assert command[-1] == "status"


def test_public_manager_is_single_cli_entrypoint() -> None:
    public_manager = (
        ROOT
        / "ops"
        / "macos"
        / "launchd"
        / "manage-shadow-daemon.py"
    )

    duplicate_manager = (
        ROOT
        / "ops"
        / "macos"
        / "launchd"
        / "manage-shadow-daemon-compat.py"
    )

    internal_legacy = (
        ROOT
        / "ops"
        / "macos"
        / "launchd"
        / "_shadow_daemon_legacy.py"
    )

    assert public_manager.is_file()
    assert internal_legacy.is_file()
    assert not duplicate_manager.exists()


def test_public_manager_targets_internal_legacy() -> None:
    module = load_module()

    assert module.LEGACY_MANAGER.name == (
        "_shadow_daemon_legacy.py"
    )

    assert module.LEGACY_MANAGER.is_file()


def test_public_help_exposes_all_actions(
    capsys,
) -> None:
    module = load_module()

    result = module.main(
        ["--help"]
    )

    captured = capsys.readouterr()

    assert result == 0

    assert (
        "usage: manage-shadow-daemon.py"
        in captured.out
    )

    for action in (
        "status",
        "install",
        "preflight",
        "uninstall",
        "canonical-preflight",
        "canonical-plan",
        "canonical-dry-run",
        "canonical-apply",
    ):
        assert action in captured.out

    assert "_shadow_daemon_legacy.py" not in (
        captured.out
    )
