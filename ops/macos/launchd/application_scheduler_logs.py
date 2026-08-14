#!/usr/bin/env python3

"""Fail-closed readiness and bounded provisioning for Scheduler launchd logs."""

from __future__ import annotations

import argparse
import errno
import grp
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys
from typing import Any, Callable, Sequence


sys.dont_write_bytecode = True

LABEL = "com.aicontrolcenter.application-scheduler"
LOG_DIRECTORY = Path("/var/log/aicontrolcenter")
STDOUT_LOG = LOG_DIRECTORY / "application-scheduler.stdout.log"
STDERR_LOG = LOG_DIRECTORY / "application-scheduler.stderr.log"
LOG_PATHS = (STDOUT_LOG, STDERR_LOG)
CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, env=environment,
    )


def inspect_path(
    path: Path, *, expected_type: str, expected_uid: int,
    expected_gid: int, expected_mode: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path), "exists": False, "regular_file": False,
        "directory": False, "symlink": False, "owner_matches": False,
        "group_matches": False, "mode_matches": False, "inspection_error": None,
        "valid": False,
    }
    try:
        metadata = path.lstat()
    except OSError as error:
        if error.errno == errno.ENOENT:
            return result
        result["inspection_error"] = {
            "error_type": type(error).__name__,
            "errno": errno.errorcode.get(error.errno, "UNKNOWN"),
        }
        return result
    result.update({
        "exists": True,
        "regular_file": stat.S_ISREG(metadata.st_mode),
        "directory": stat.S_ISDIR(metadata.st_mode),
        "symlink": stat.S_ISLNK(metadata.st_mode),
        "owner_matches": metadata.st_uid == expected_uid,
        "group_matches": metadata.st_gid == expected_gid,
        "mode_matches": stat.S_IMODE(metadata.st_mode) == expected_mode,
    })
    type_matches = result["regular_file"] if expected_type == "file" else result["directory"]
    result["valid"] = bool(
        type_matches and not result["symlink"] and result["owner_matches"]
        and result["group_matches"] and result["mode_matches"]
    )
    return result


def inspect_contract(
    *, log_directory: Path = LOG_DIRECTORY,
    log_paths: Sequence[Path] = LOG_PATHS,
    root_uid: int = 0, wheel_gid: int | None = None,
    service_uid: int | None = None, staff_gid: int | None = None,
) -> dict[str, Any]:
    resolved_wheel_gid = grp.getgrnam("wheel").gr_gid if wheel_gid is None else wheel_gid
    resolved_service_uid = pwd.getpwnam("kyouhan").pw_uid if service_uid is None else service_uid
    resolved_staff_gid = grp.getgrnam("staff").gr_gid if staff_gid is None else staff_gid
    parent = inspect_path(
        log_directory, expected_type="directory", expected_uid=root_uid,
        expected_gid=resolved_wheel_gid, expected_mode=0o755,
    )
    logs = [
        inspect_path(
            path, expected_type="file", expected_uid=resolved_service_uid,
            expected_gid=resolved_staff_gid, expected_mode=0o640,
        )
        for path in log_paths
    ]
    return {
        "parent": parent, "logs": logs,
        "scheduler_log_contract_ready": parent["valid"] and all(item["valid"] for item in logs),
    }


def executor_precondition_gate(
    *, apply: bool, effective_user_id: int,
) -> dict[str, Any]:
    return {
        "root_required": True,
        "root_verified": apply and effective_user_id == 0,
        "executor_preconditions_met": apply and effective_user_id == 0,
        "authorization_source": "outer_governed_executor",
    }


def execute(
    *, apply: bool,
    effective_user_id: int | None = None, runner: CommandRunner = default_runner,
    log_directory: Path = LOG_DIRECTORY, log_paths: Sequence[Path] = LOG_PATHS,
    root_uid: int = 0, wheel_gid: int | None = None,
    service_uid: int | None = None, staff_gid: int | None = None,
) -> dict[str, Any]:
    executor_preconditions = executor_precondition_gate(
        effective_user_id=os.geteuid() if effective_user_id is None else effective_user_id,
        apply=apply,
    )
    inspection_arguments = {
        "log_directory": log_directory, "log_paths": log_paths,
        "root_uid": root_uid, "wheel_gid": wheel_gid,
        "service_uid": service_uid, "staff_gid": staff_gid,
    }
    before = inspect_contract(**inspection_arguments)
    inspected = [before["parent"], *before["logs"]]
    inspection_errors = [item["path"] for item in inspected if item["inspection_error"]]
    invalid_existing = [item["path"] for item in before["logs"] if item["exists"] and not item["valid"]]
    missing = [item["path"] for item in before["logs"] if not item["exists"] and not item["inspection_error"]]
    commands = [
        {
            "step": "provision_scheduler_log",
            "argv": ["/usr/bin/install", "-o", "kyouhan", "-g", "staff", "-m", "0640", "/dev/null", path],
        }
        for path in missing
    ]
    result: dict[str, Any] = {
        "schema_version": "1.0", "operation": "application_scheduler_log_provisioning",
        "executor_preconditions": executor_preconditions, "readiness": before,
        "commands": commands,
        "results": [], "write_operations_executed": 0,
        "launchctl_operations_executed": 0, "retry_operations_executed": 0,
        "rollback_operations_executed": 0,
        "scheduler_log_readiness_gate_passed": before["scheduler_log_contract_ready"],
    }
    if before["scheduler_log_contract_ready"]:
        return result
    if inspection_errors:
        result["failure"] = {"step": "filesystem_inspection", "paths": inspection_errors}
        result["commands"] = []
        return result
    if not before["parent"]["valid"]:
        result["failure"] = {"step": "log_parent_contract"}
        return result
    if invalid_existing:
        result["failure"] = {"step": "existing_log_contract", "paths": invalid_existing}
        return result
    if not apply:
        result["failure"] = {"step": "missing_scheduler_logs", "paths": missing}
        return result
    if not executor_preconditions["executor_preconditions_met"]:
        result["failure"] = {"step": "executor_preconditions"}
        return result

    for command in commands:
        try:
            completed = runner(command["argv"])
        except OSError as error:
            result["failure"] = {
                "step": command["step"], "error_type": type(error).__name__,
            }
            return result
        result["write_operations_executed"] += 1
        result["results"].append({
            "step": command["step"], "argv": command["argv"],
            "returncode": completed.returncode,
        })
        if completed.returncode != 0:
            result["failure"] = {
                "step": command["step"], "returncode": completed.returncode,
            }
            return result

    after = inspect_contract(**inspection_arguments)
    result["readiness"] = after
    result["scheduler_log_readiness_gate_passed"] = after["scheduler_log_contract_ready"]
    if not after["scheduler_log_contract_ready"]:
        result["failure"] = {"step": "post_provision_log_contract"}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "provision"))
    arguments = parser.parse_args()
    result = execute(apply=arguments.action == "provision")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scheduler_log_readiness_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
