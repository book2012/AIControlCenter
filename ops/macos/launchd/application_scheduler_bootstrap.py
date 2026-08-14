#!/usr/bin/env python3

"""Fail-closed, bootstrap-only lifecycle executor for Application Scheduler."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

sys.dont_write_bytecode = True
MODULE_DIRECTORY = Path(__file__).resolve().parent
if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(MODULE_DIRECTORY))

from application_scheduler_logs import LABEL, inspect_contract  # noqa: E402

SERVICE = f"system/{LABEL}"
INSTALLED_PLIST = Path("/Library/LaunchDaemons") / f"{LABEL}.plist"
BOOTSTRAP_COMMAND = ["/bin/launchctl", "bootstrap", "system", str(INSTALLED_PLIST)]
CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
INSPECTION_KEYS = {
    "path", "exists", "regular_file", "directory", "symlink",
    "owner_matches", "group_matches", "mode_matches", "inspection_error",
    "valid",
}


def default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )


def valid_contract_result(readiness: object) -> bool:
    if not isinstance(readiness, Mapping):
        return False
    ready = readiness.get("scheduler_log_contract_ready")
    parent = readiness.get("parent")
    logs = readiness.get("logs")
    if not isinstance(ready, bool) or not isinstance(parent, Mapping):
        return False
    if not isinstance(logs, Sequence) or isinstance(logs, (str, bytes)):
        return False
    inspected = [parent, *logs]
    if not logs:
        return False
    for item in inspected:
        if not isinstance(item, Mapping) or not INSPECTION_KEYS <= item.keys():
            return False
        if not isinstance(item["path"], str):
            return False
        if not all(
            isinstance(item[key], bool)
            for key in INSPECTION_KEYS - {"path", "inspection_error"}
        ):
            return False
        if item["inspection_error"] is not None and not isinstance(
            item["inspection_error"], Mapping
        ):
            return False
    return not ready or all(
        item["valid"] and item["inspection_error"] is None for item in inspected
    )


def executor_precondition_gate(
    *, apply: bool, effective_user_id: int,
) -> dict[str, Any]:
    return {
        "dry_run": not apply,
        "root_required": True,
        "root_verified": apply and effective_user_id == 0,
        "executor_preconditions_met": apply and effective_user_id == 0,
        "authorization_source": "outer_governed_executor",
    }


def execute(
    *, apply: bool,
    effective_user_id: int | None = None, runner: CommandRunner = default_runner,
    contract_inspector: Callable[..., dict[str, Any]] = inspect_contract,
    contract_arguments: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    preconditions = executor_precondition_gate(
        apply=apply,
        effective_user_id=os.geteuid() if effective_user_id is None else effective_user_id,
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "operation": "application_scheduler_bootstrap",
        "executor_preconditions": preconditions,
        "scheduler_log_readiness": {
            "scheduler_log_contract_ready": False,
        },
        "service_probe": {"performed": False, "returncode": None, "eligible": False},
        "command": {"argv": BOOTSTRAP_COMMAND},
        "result": {"performed": False, "returncode": None},
        "write_operations_executed": 0,
        "retry_operations_executed": 0,
        "rollback_operations_executed": 0,
        "scheduler_lifecycle_readiness_gate_passed": False,
    }
    try:
        readiness = contract_inspector(**dict(contract_arguments or {}))
    except Exception:
        result["failure"] = {"step": "scheduler_log_contract_inspection"}
        return result
    if not valid_contract_result(readiness):
        result["failure"] = {"step": "scheduler_log_contract_result"}
        return result
    logs = readiness["logs"]
    inspected_paths = [readiness.get("parent"), *logs]
    if any(
        isinstance(item, Mapping) and item.get("inspection_error")
        for item in inspected_paths
    ):
        result["failure"] = {"step": "scheduler_log_contract_inspection"}
        return result
    result["scheduler_log_readiness"] = dict(readiness)
    if readiness["scheduler_log_contract_ready"] is not True:
        result["failure"] = {"step": "scheduler_log_readiness"}
        return result

    try:
        probe = runner(["/bin/launchctl", "print", SERVICE])
    except Exception:
        result["failure"] = {
            "step": "service_registration_probe", "state": "indeterminate",
        }
        return result
    if not isinstance(probe, subprocess.CompletedProcess) or not isinstance(
        probe.returncode, int
    ):
        result["failure"] = {
            "step": "service_registration_probe", "state": "indeterminate",
        }
        return result
    result["service_probe"] = {
        "performed": True,
        "returncode": probe.returncode if probe.returncode in (0, 113) else None,
        "eligible": probe.returncode == 113,
    }
    if probe.returncode != 113:
        result["failure"] = {
            "step": "service_registration_probe",
            "state": "registered" if probe.returncode == 0 else "indeterminate",
        }
        return result
    if not apply:
        result["scheduler_lifecycle_readiness_gate_passed"] = True
        return result
    if not preconditions["executor_preconditions_met"]:
        result["failure"] = {"step": "executor_preconditions"}
        return result

    try:
        completed = runner(BOOTSTRAP_COMMAND)
    except OSError as error:
        result["write_operations_executed"] = 1
        result["result"] = {"performed": True, "returncode": None, "error_type": type(error).__name__}
        result["failure"] = {"step": "bootstrap", "returncode": None, "error_type": type(error).__name__}
        return result
    result["write_operations_executed"] = 1
    result["result"] = {"performed": True, "returncode": completed.returncode}
    if completed.returncode != 0:
        result["failure"] = {"step": "bootstrap", "returncode": completed.returncode}
        return result
    result["scheduler_lifecycle_readiness_gate_passed"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("dry-run", "apply"))
    arguments = parser.parse_args()
    result = execute(apply=arguments.action == "apply")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scheduler_lifecycle_readiness_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
