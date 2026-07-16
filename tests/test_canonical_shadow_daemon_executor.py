from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import ModuleType
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "canonical_shadow_daemon_executor.py"
)


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "canonical_shadow_daemon_executor",
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


def test_executor_module_exists() -> None:
    assert MODULE_PATH.is_file()


def test_dry_run_executes_no_commands() -> None:
    module = load_module()

    def forbidden_runner(
        argv: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        raise AssertionError(
            f"Dry-run executed command: {argv}"
        )

    result = module.execute(
        root=ROOT,
        apply=False,
        runner=forbidden_runner,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is False

    assert result["results"] == []


def test_commands_use_absolute_executables() -> None:
    module = load_module()

    result = module.execute(
        root=ROOT,
        apply=False,
    )

    for command in result["commands"]:
        assert command["argv"][0].startswith(
            "/"
        )


def test_install_precedes_bootstrap() -> None:
    module = load_module()

    result = module.execute(
        root=ROOT,
        apply=False,
    )

    steps = [
        command["step"]
        for command in result["commands"]
    ]

    final_install_index = max(
        index
        for index, step in enumerate(
            steps
        )
        if step == "install_file"
    )

    bootstrap_index = steps.index(
        "launchctl_bootstrap"
    )

    assert final_install_index < bootstrap_index


def test_apply_requires_authorization() -> None:
    module = load_module()

    result = module.execute(
        root=ROOT,
        apply=True,
        confirmation="",
        environment={},
        effective_user_id=501,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is False

    assert result[
        "write_operations_executed"
    ] is False

    assert result["failure"]["step"] == (
        "system_write_authorization"
    )


def test_apply_authorization_contract() -> None:
    module = load_module()

    authorization = module.authorization_gate(
        apply=True,
        confirmation=(
            "com.aicontrolcenter.api.shadow"
        ),
        environment={
            "AICONTROLCENTER_ALLOW_SYSTEM_WRITE":
                "1"
        },
        effective_user_id=0,
    )

    assert authorization[
        "apply_authorized"
    ] is True


def test_authorized_apply_uses_injected_runner() -> None:
    module = load_module()

    executed: list[list[str]] = []

    def successful_runner(
        argv: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        executed.append(
            list(argv)
        )

        return subprocess.CompletedProcess(
            args=list(argv),
            returncode=0,
            stdout="",
            stderr="",
        )

    result = module.execute(
        root=ROOT,
        apply=True,
        confirmation=(
            "com.aicontrolcenter.api.shadow"
        ),
        environment={
            "AICONTROLCENTER_ALLOW_SYSTEM_WRITE":
                "1"
        },
        effective_user_id=0,
        runner=successful_runner,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is True

    assert result[
        "write_operations_executed"
    ] is True

    assert len(executed) == (
        len(result["commands"]) + 1
    )

    assert result["transaction"][
        "snapshot_created"
    ] is True

    assert result["transaction"][
        "rollback_attempted"
    ] is False


def test_apply_stops_on_first_required_failure() -> None:
    module = load_module()

    calls = 0

    def failing_runner(
        argv: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1

        return subprocess.CompletedProcess(
            args=list(argv),
            returncode=1,
            stdout="",
            stderr="injected failure",
        )

    result = module.execute(
        root=ROOT,
        apply=True,
        confirmation=(
            "com.aicontrolcenter.api.shadow"
        ),
        environment={
            "AICONTROLCENTER_ALLOW_SYSTEM_WRITE":
                "1"
        },
        effective_user_id=0,
        runner=failing_runner,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is False

    assert result["failure"]["returncode"] == 1
    assert calls >= 2

    assert result["transaction"][
        "snapshot_created"
    ] is True

    assert result["transaction"][
        "rollback_attempted"
    ] is True
def test_bootout_includes_settle_delay() -> None:
    module = load_module()

    result = module.execute(
        root=ROOT,
        apply=False,
    )

    commands = result["commands"]

    bootout_index = next(
        index
        for index, command in enumerate(commands)
        if (
            command["step"]
            == "launchctl_bootout_if_loaded"
            and
            command.get("phase") == "bootout"
        )
    )

    settle_command = commands[
        bootout_index + 1
    ]

    assert settle_command["step"] == (
        "launchctl_bootout_if_loaded"
    )

    assert settle_command["phase"] == "settle"

    assert settle_command["argv"] == [
        "/bin/sleep",
        "2",
    ]
