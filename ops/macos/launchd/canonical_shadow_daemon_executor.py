#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
from typing import Any, Callable, Mapping, Sequence


MODULE_DIRECTORY = Path(__file__).resolve().parent

if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(MODULE_DIRECTORY),
    )

from canonical_shadow_daemon import (  # noqa: E402
    INSTALLED_PLIST,
    INSTALLED_RUNNER,
    LABEL,
    SERVICE,
    build_install_plan,
)


CommandRunner = Callable[
    [Sequence[str]],
    subprocess.CompletedProcess[str],
]


def compile_step(
    step: Mapping[str, Any],
) -> list[dict[str, Any]]:
    step_type = str(step["step"])

    if step_type == "ensure_directory":
        return [
            {
                "step": step_type,
                "argv": [
                    "/usr/bin/install",
                    "-d",
                    "-o",
                    str(step["owner"]),
                    "-g",
                    str(step["group"]),
                    "-m",
                    str(step["mode"]),
                    str(step["path"]),
                ],
                "allow_nonzero": False,
            }
        ]

    if step_type == "install_file":
        return [
            {
                "step": step_type,
                "argv": [
                    "/usr/bin/install",
                    "-o",
                    str(step["owner"]),
                    "-g",
                    str(step["group"]),
                    "-m",
                    str(step["mode"]),
                    str(step["source"]),
                    str(step["destination"]),
                ],
                "allow_nonzero": False,
            }
        ]

    if step_type == "ensure_file":
        path = str(step["path"])
        owner_group = (
            f"{step['owner']}:{step['group']}"
        )

        return [
            {
                "step": step_type,
                "phase": "touch",
                "argv": [
                    "/usr/bin/touch",
                    path,
                ],
                "allow_nonzero": False,
            },
            {
                "step": step_type,
                "phase": "ownership",
                "argv": [
                    "/usr/sbin/chown",
                    owner_group,
                    path,
                ],
                "allow_nonzero": False,
            },
            {
                "step": step_type,
                "phase": "mode",
                "argv": [
                    "/bin/chmod",
                    str(step["mode"]),
                    path,
                ],
                "allow_nonzero": False,
            },
        ]

    if step_type == "launchctl_bootout_if_loaded":
        return [
            {
                "step": step_type,
                "argv": [
                    "/bin/launchctl",
                    "bootout",
                    str(step["service"]),
                ],
                "allow_nonzero": True,
            }
        ]

    if step_type == "launchctl_bootstrap":
        return [
            {
                "step": step_type,
                "argv": [
                    "/bin/launchctl",
                    "bootstrap",
                    str(step["domain"]),
                    str(step["plist"]),
                ],
                "allow_nonzero": False,
            }
        ]

    if step_type == "launchctl_enable":
        return [
            {
                "step": step_type,
                "argv": [
                    "/bin/launchctl",
                    "enable",
                    str(step["service"]),
                ],
                "allow_nonzero": False,
            }
        ]

    if step_type == "launchctl_kickstart":
        return [
            {
                "step": step_type,
                "argv": [
                    "/bin/launchctl",
                    "kickstart",
                    "-k",
                    str(step["service"]),
                ],
                "allow_nonzero": False,
            }
        ]

    raise ValueError(
        f"Unsupported installation step: {step_type}"
    )


def compile_commands(
    installation_plan: Sequence[
        Mapping[str, Any]
    ],
) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []

    for step in installation_plan:
        commands.extend(
            compile_step(step)
        )

    return commands


def authorization_gate(
    *,
    apply: bool,
    confirmation: str,
    environment: Mapping[str, str],
    effective_user_id: int,
) -> dict[str, bool]:
    if not apply:
        return {
            "dry_run": True,
            "root_required": True,
            "root_verified": False,
            "environment_authorized": False,
            "label_confirmed": False,
            "apply_authorized": False,
        }

    root_verified = (
        effective_user_id == 0
    )

    environment_authorized = (
        environment.get(
            "AICONTROLCENTER_ALLOW_SYSTEM_WRITE"
        )
        == "1"
    )

    label_confirmed = (
        confirmation == LABEL
    )

    return {
        "dry_run": False,
        "root_required": True,
        "root_verified": root_verified,
        "environment_authorized":
            environment_authorized,
        "label_confirmed":
            label_confirmed,
        "apply_authorized": all(
            (
                root_verified,
                environment_authorized,
                label_confirmed,
            )
        ),
    }


def default_runner(
    argv: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )



def create_transaction_snapshot(
    *,
    runner: CommandRunner,
) -> dict[str, Any]:
    snapshot_root = Path(
        tempfile.mkdtemp(
            prefix="aicontrolcenter-shadow-transaction-"
        )
    )

    assets: dict[str, dict[str, Any]] = {}

    contracts = (
        ("plist", INSTALLED_PLIST, "0644"),
        ("runner", INSTALLED_RUNNER, "0755"),
    )

    for name, installed_path, mode in contracts:
        existed = installed_path.is_file()
        backup_path = snapshot_root / f"{name}.backup"

        if existed:
            shutil.copy2(
                installed_path,
                backup_path,
            )

        assets[name] = {
            "installed_path": str(installed_path),
            "backup_path": str(backup_path),
            "existed": existed,
            "mode": mode,
        }

    service_probe = runner(
        [
            "/bin/launchctl",
            "print",
            SERVICE,
        ]
    )

    return {
        "snapshot_root": str(snapshot_root),
        "assets": assets,
        "service_was_loaded": (
            service_probe.returncode == 0
        ),
        "service_probe": {
            "returncode": service_probe.returncode,
            "stdout": service_probe.stdout,
            "stderr": service_probe.stderr,
        },
    }


def compile_rollback_commands(
    snapshot: Mapping[str, Any],
) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = [
        {
            "step": "rollback_bootout",
            "argv": [
                "/bin/launchctl",
                "bootout",
                SERVICE,
            ],
            "allow_nonzero": True,
        }
    ]

    assets = snapshot["assets"]

    for name in ("runner", "plist"):
        asset = assets[name]
        installed_path = str(asset["installed_path"])

        if asset["existed"]:
            commands.append(
                {
                    "step": f"rollback_restore_{name}",
                    "argv": [
                        "/usr/bin/install",
                        "-o",
                        "root",
                        "-g",
                        "wheel",
                        "-m",
                        str(asset["mode"]),
                        str(asset["backup_path"]),
                        installed_path,
                    ],
                    "allow_nonzero": False,
                }
            )
        else:
            commands.append(
                {
                    "step": f"rollback_remove_{name}",
                    "argv": [
                        "/bin/rm",
                        "-f",
                        installed_path,
                    ],
                    "allow_nonzero": False,
                }
            )

    if snapshot["service_was_loaded"]:
        commands.extend(
            [
                {
                    "step": "rollback_bootstrap",
                    "argv": [
                        "/bin/launchctl",
                        "bootstrap",
                        "system",
                        str(INSTALLED_PLIST),
                    ],
                    "allow_nonzero": False,
                },
                {
                    "step": "rollback_enable",
                    "argv": [
                        "/bin/launchctl",
                        "enable",
                        SERVICE,
                    ],
                    "allow_nonzero": False,
                },
                {
                    "step": "rollback_kickstart",
                    "argv": [
                        "/bin/launchctl",
                        "kickstart",
                        "-k",
                        SERVICE,
                    ],
                    "allow_nonzero": False,
                },
            ]
        )

    return commands


def execute_rollback(
    *,
    snapshot: Mapping[str, Any],
    runner: CommandRunner,
) -> dict[str, Any]:
    commands = compile_rollback_commands(snapshot)
    results: list[dict[str, Any]] = []
    rollback_gate = True
    failure: dict[str, Any] | None = None

    for index, command in enumerate(commands, start=1):
        completed = runner(command["argv"])

        command_result = {
            "index": index,
            "step": command["step"],
            "argv": command["argv"],
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "allow_nonzero": command["allow_nonzero"],
        }

        results.append(command_result)

        if (
            completed.returncode != 0
            and
            not command["allow_nonzero"]
        ):
            rollback_gate = False
            failure = {
                "step": command["step"],
                "returncode": completed.returncode,
                "stderr": completed.stderr,
            }
            break

    payload: dict[str, Any] = {
        "rollback_attempted": True,
        "rollback_gate_passed": rollback_gate,
        "commands": commands,
        "results": results,
    }

    if failure is not None:
        payload["failure"] = failure

    return payload


def cleanup_transaction_snapshot(
    snapshot: Mapping[str, Any],
) -> None:
    shutil.rmtree(
        Path(str(snapshot["snapshot_root"])),
        ignore_errors=True,
    )


def execute_rollback(
    *,
    snapshot: Mapping[str, Any],
    runner: CommandRunner,
) -> dict[str, Any]:
    commands = compile_rollback_commands(snapshot)
    results: list[dict[str, Any]] = []
    rollback_gate = True
    failure: dict[str, Any] | None = None

    for index, command in enumerate(commands, start=1):
        completed = runner(command["argv"])

        command_result = {
            "index": index,
            "step": command["step"],
            "argv": command["argv"],
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "allow_nonzero": command["allow_nonzero"],
        }

        results.append(command_result)

        if (
            completed.returncode != 0
            and
            not command["allow_nonzero"]
        ):
            rollback_gate = False
            failure = {
                "step": command["step"],
                "returncode": completed.returncode,
                "stderr": completed.stderr,
            }
            break

    payload: dict[str, Any] = {
        "rollback_attempted": True,
        "rollback_gate_passed": rollback_gate,
        "commands": commands,
        "results": results,
    }

    if failure is not None:
        payload["failure"] = failure

    return payload


def cleanup_transaction_snapshot(
    snapshot: Mapping[str, Any],
) -> None:
    shutil.rmtree(
        Path(str(snapshot["snapshot_root"])),
        ignore_errors=True,
    )

def execute(
    *,
    root: Path,
    apply: bool,
    confirmation: str = "",
    environment: Mapping[str, str] | None = None,
    effective_user_id: int | None = None,
    runner: CommandRunner = default_runner,
) -> dict[str, Any]:
    resolved_root = root.resolve()

    plan = build_install_plan(
        resolved_root
    )

    contract_gate = (
        plan.get(
            "canonical_launchd_contract_gate_passed"
        )
        is True
    )

    commands = compile_commands(
        plan["installation_plan"]
    )

    active_environment = (
        dict(os.environ)
        if environment is None
        else dict(environment)
    )

    active_effective_user_id = (
        os.geteuid()
        if effective_user_id is None
        else effective_user_id
    )

    authorization = authorization_gate(
        apply=apply,
        confirmation=confirmation,
        environment=active_environment,
        effective_user_id=
            active_effective_user_id,
    )

    results: list[dict[str, Any]] = []

    if not apply:
        return {
            "schema_version": "1.0",
            "canonical_executor_gate_passed":
                contract_gate,
            "canonical_contract_gate_passed":
                contract_gate,
            "write_operations_executed":
                False,
            "authorization":
                authorization,
            "commands": commands,
            "results": results,
            "installation":
                plan["installation"],
            "next_action": (
                "Apply remains blocked during observation"
                if contract_gate
                else
                "Fix canonical contract"
            ),
        }

    if not contract_gate:
        return {
            "schema_version": "1.0",
            "canonical_executor_gate_passed":
                False,
            "canonical_contract_gate_passed":
                False,
            "write_operations_executed":
                False,
            "authorization":
                authorization,
            "commands": commands,
            "results": results,
            "failure": {
                "step":
                    "canonical_contract",
            },
        }

    if not authorization[
        "apply_authorized"
    ]:
        return {
            "schema_version": "1.0",
            "canonical_executor_gate_passed":
                False,
            "canonical_contract_gate_passed":
                True,
            "write_operations_executed":
                False,
            "authorization":
                authorization,
            "commands": commands,
            "results": results,
            "failure": {
                "step":
                    "system_write_authorization",
            },
        }

    try:
        transaction_snapshot = create_transaction_snapshot(
            runner=runner,
        )
    except (OSError, shutil.Error) as error:
        return {
            "schema_version": "1.0",
            "canonical_executor_gate_passed": False,
            "canonical_contract_gate_passed": True,
            "write_operations_executed": False,
            "authorization": authorization,
            "commands": commands,
            "results": results,
            "failure": {
                "step": "transaction_snapshot",
                "detail": str(error),
            },
            "transaction": {
                "snapshot_created": False,
                "rollback_attempted": False,
                "rollback_gate_passed": False,
            },
        }

    execution_gate = True
    failure: dict[str, Any] | None = None

    for index, command in enumerate(
        commands,
        start=1,
    ):
        completed = runner(
            command["argv"]
        )

        command_result = {
            "index": index,
            "step": command["step"],
            "phase": command.get(
                "phase",
                "",
            ),
            "argv": command["argv"],
            "returncode":
                completed.returncode,
            "stdout":
                completed.stdout,
            "stderr":
                completed.stderr,
            "allow_nonzero":
                command["allow_nonzero"],
        }

        results.append(
            command_result
        )

        if (
            completed.returncode != 0
            and
            not command[
                "allow_nonzero"
            ]
        ):
            execution_gate = False

            failure = {
                "step":
                    command["step"],
                "phase":
                    command.get(
                        "phase",
                        "",
                    ),
                "returncode":
                    completed.returncode,
                "stderr":
                    completed.stderr,
            }

            break

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "canonical_executor_gate_passed":
            execution_gate,
        "canonical_contract_gate_passed":
            True,
        "write_operations_executed":
            bool(results),
        "authorization":
            authorization,
        "commands": commands,
        "results": results,
        "installation":
            plan["installation"],
        "transaction": {
            "snapshot_created": True,
            "service_was_loaded":
                transaction_snapshot[
                    "service_was_loaded"
                ],
            "rollback_attempted": False,
            "rollback_gate_passed": False,
        },
    }

    if failure is not None:
        result["failure"] = failure

        rollback = execute_rollback(
            snapshot=transaction_snapshot,
            runner=runner,
        )

        result["transaction"] = {
            "snapshot_created": True,
            "service_was_loaded":
                transaction_snapshot[
                    "service_was_loaded"
                ],
            **rollback,
        }

    cleanup_transaction_snapshot(
        transaction_snapshot
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=(
            "dry-run",
            "apply",
        ),
    )

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--confirm-label",
        default="",
    )

    arguments = parser.parse_args()

    result = execute(
        root=arguments.root,
        apply=(
            arguments.action
            == "apply"
        ),
        confirmation=
            arguments.confirm_label,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return (
        0
        if result[
            "canonical_executor_gate_passed"
        ]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
