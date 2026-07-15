from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import ModuleType
from typing import Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "canonical_shadow_daemon_executor.py"
)


Runner = Callable[
    [Sequence[str]],
    subprocess.CompletedProcess[str],
]


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "canonical_shadow_daemon_transaction",
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


def authorized_execute(
    module: ModuleType,
    runner: Runner,
) -> dict:
    return module.execute(
        root=ROOT,
        apply=True,
        confirmation=(
            "com.aicontrolcenter.api.shadow"
        ),
        environment={
            "AICONTROLCENTER_ALLOW_SYSTEM_WRITE":
                "1",
        },
        effective_user_id=0,
        runner=runner,
    )


def success(
    argv: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    command = list(argv)

    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout="",
        stderr="",
    )


def test_bootstrap_failure_runs_rollback() -> None:
    module = load_module()

    failed_apply_bootstrap = False

    def runner(
        argv: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        nonlocal failed_apply_bootstrap

        command = list(argv)

        is_bootstrap = (
            command[:3]
            == [
                "/bin/launchctl",
                "bootstrap",
                "system",
            ]
        )

        if (
            is_bootstrap
            and
            not failed_apply_bootstrap
        ):
            failed_apply_bootstrap = True

            return subprocess.CompletedProcess(
                args=command,
                returncode=5,
                stdout="",
                stderr=(
                    "Bootstrap failed: 5: "
                    "Input/output error"
                ),
            )

        return success(command)

    result = authorized_execute(
        module,
        runner,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is False

    assert result["failure"]["step"] == (
        "launchctl_bootstrap"
    )

    transaction = result["transaction"]

    assert transaction[
        "snapshot_created"
    ] is True

    assert transaction[
        "rollback_attempted"
    ] is True

    assert transaction[
        "rollback_gate_passed"
    ] is True

    rollback_steps = [
        item["step"]
        for item in transaction["results"]
    ]

    assert "rollback_bootout" in rollback_steps
    assert "rollback_bootstrap" in rollback_steps
    assert "rollback_enable" in rollback_steps
    assert "rollback_kickstart" in rollback_steps


def test_rollback_failure_is_reported() -> None:
    module = load_module()

    failed_apply_bootstrap = False
    rollback_started = False

    def runner(
        argv: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        nonlocal failed_apply_bootstrap
        nonlocal rollback_started

        command = list(argv)

        if (
            command[:3]
            == [
                "/bin/launchctl",
                "bootstrap",
                "system",
            ]
            and
            not failed_apply_bootstrap
        ):
            failed_apply_bootstrap = True

            return subprocess.CompletedProcess(
                args=command,
                returncode=5,
                stdout="",
                stderr="apply bootstrap failure",
            )

        if (
            command[:3]
            == [
                "/bin/launchctl",
                "bootout",
                "system/com.aicontrolcenter.api.shadow",
            ]
            and
            failed_apply_bootstrap
        ):
            rollback_started = True

            return success(command)

        is_restore = (
            rollback_started
            and
            command
            and
            command[0] == "/usr/bin/install"
        )

        if is_restore:
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr="rollback restore failure",
            )

        return success(command)

    result = authorized_execute(
        module,
        runner,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is False

    transaction = result["transaction"]

    assert transaction[
        "rollback_attempted"
    ] is True

    assert transaction[
        "rollback_gate_passed"
    ] is False

    assert transaction["failure"]["returncode"] == 1

    assert transaction["failure"]["stderr"] == (
        "rollback restore failure"
    )


def test_successful_apply_does_not_rollback() -> None:
    module = load_module()

    result = authorized_execute(
        module,
        success,
    )

    assert result[
        "canonical_executor_gate_passed"
    ] is True

    transaction = result["transaction"]

    assert transaction[
        "snapshot_created"
    ] is True

    assert transaction[
        "rollback_attempted"
    ] is False

    assert transaction[
        "rollback_gate_passed"
    ] is False
