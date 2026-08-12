#!/usr/bin/env python3

"""Fail-closed executor for one canonical API first installation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

MODULE_DIRECTORY = Path(__file__).resolve().parent
if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(MODULE_DIRECTORY))

from canonical_api_daemon import (  # noqa: E402
    INSTALLED_PLIST, INSTALLED_RUNNER, LABEL, SERVICE, build_install_plan,
)

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def compile_step(step: Mapping[str, Any]) -> list[dict[str, Any]]:
    kind = str(step["step"])
    if kind == "ensure_directory":
        argv = ["/usr/bin/install", "-d", "-o", str(step["owner"]), "-g", str(step["group"]), "-m", str(step["mode"]), str(step["path"])]
        return [{"step": kind, "argv": argv}]
    if kind == "install_file":
        argv = ["/usr/bin/install", "-o", str(step["owner"]), "-g", str(step["group"]), "-m", str(step["mode"]), str(step["source"]), str(step["destination"])]
        return [{"step": kind, "argv": argv}]
    if kind == "ensure_file":
        path = str(step["path"])
        return [
            {"step": kind, "phase": "touch", "argv": ["/usr/bin/touch", path]},
            {"step": kind, "phase": "ownership", "argv": ["/usr/sbin/chown", f"{step['owner']}:{step['group']}", path]},
            {"step": kind, "phase": "mode", "argv": ["/bin/chmod", str(step["mode"]), path]},
        ]
    if kind == "launchctl_bootstrap":
        return [{"step": kind, "argv": ["/bin/launchctl", "bootstrap", str(step["domain"]), str(step["plist"])]}]
    if kind == "launchctl_enable":
        return [{"step": kind, "argv": ["/bin/launchctl", "enable", str(step["service"])]}]
    if kind == "launchctl_kickstart":
        return [{"step": kind, "argv": ["/bin/launchctl", "kickstart", str(step["service"])]}]
    raise ValueError(f"Unsupported installation step: {kind}")


def compile_commands(installation_plan: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for step in installation_plan:
        commands.extend(compile_step(step))
    return commands


def authorization_gate(*, apply: bool, confirmation: str, environment: Mapping[str, str], effective_user_id: int) -> dict[str, bool]:
    root = apply and effective_user_id == 0
    environment_authorized = apply and environment.get("AICONTROLCENTER_ALLOW_SYSTEM_WRITE") == "1"
    confirmed = apply and confirmation == LABEL
    return {
        "dry_run": not apply,
        "root_required": True,
        "root_verified": root,
        "environment_authorized": environment_authorized,
        "label_confirmed": confirmed,
        "apply_authorized": root and environment_authorized and confirmed,
    }


def _base_result(plan: Mapping[str, Any], commands: list[dict[str, Any]], authorization: Mapping[str, bool]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "canonical_contract_gate_passed": plan["canonical_launchd_contract_gate_passed"],
        "canonical_executor_gate_passed": False,
        "write_operations_executed": False,
        "authorization": dict(authorization),
        "commands": commands,
        "results": [],
        "installation": plan["installation"],
        "first_activation_only": True,
    }


def execute(*, root: Path, apply: bool, confirmation: str = "", environment: Mapping[str, str] | None = None,
            effective_user_id: int | None = None, runner: CommandRunner = default_runner,
            installed_plist: Path = INSTALLED_PLIST, installed_runner: Path = INSTALLED_RUNNER) -> dict[str, Any]:
    plan = build_install_plan(root.resolve())
    commands = compile_commands(plan["installation_plan"])
    authorization = authorization_gate(
        apply=apply, confirmation=confirmation,
        environment=os.environ if environment is None else environment,
        effective_user_id=os.geteuid() if effective_user_id is None else effective_user_id,
    )
    result = _base_result(plan, commands, authorization)
    if not apply:
        result["canonical_executor_gate_passed"] = bool(plan["canonical_launchd_contract_gate_passed"])
        return result
    if not plan["canonical_launchd_contract_gate_passed"]:
        result["failure"] = {"step": "canonical_contract"}
        return result
    if not authorization["apply_authorized"]:
        result["failure"] = {"step": "system_write_authorization"}
        return result

    # This is the only command permitted before the first write; it is read-only.
    probe = runner(["/bin/launchctl", "print", SERVICE])
    service_registered = probe.returncode == 0
    service_confirmed_absent = probe.returncode == 113
    result["preflight_inspection"] = {
        "service_registered": service_registered,
        "service_confirmed_absent": service_confirmed_absent,
        "installed_plist_exists": installed_plist.exists() or installed_plist.is_symlink(),
        "installed_runner_exists": installed_runner.exists() or installed_runner.is_symlink(),
        "service_probe_returncode": probe.returncode,
    }
    if not service_registered and not service_confirmed_absent:
        result["failure"] = {
            "step": "service_registration_probe",
            "returncode": probe.returncode,
            "detail": "Canonical service registration state is indeterminate",
        }
        return result
    blockers = [name for name in ("service_registered", "installed_plist_exists", "installed_runner_exists") if result["preflight_inspection"][name]]
    if blockers:
        result["failure"] = {"step": "first_install_precondition", "blockers": blockers,
                             "detail": "A separately authorized lifecycle task is required"}
        return result

    for index, command in enumerate(commands, start=1):
        completed = runner(command["argv"])
        command_result = {
            "index": index, "step": command["step"], "phase": command.get("phase", ""),
            "argv": command["argv"], "returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr,
        }
        result["results"].append(command_result)
        result["write_operations_executed"] = True
        if completed.returncode != 0:
            result["failure"] = {"step": command["step"], "returncode": completed.returncode, "stderr": completed.stderr}
            return result
    result["canonical_executor_gate_passed"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("dry-run", "apply"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--confirm", default="")
    arguments = parser.parse_args()
    result = execute(root=arguments.root, apply=arguments.action == "apply", confirmation=arguments.confirm)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["canonical_executor_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
