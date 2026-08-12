#!/usr/bin/env python3

"""Fail-closed, bootstrap-only executor for the canonical API daemon."""

from __future__ import annotations

import argparse
import grp
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

# Immutable Production Source must never be mutated by Python import caches.
sys.dont_write_bytecode = True
from typing import Any, Callable, Mapping, Sequence

MODULE_DIRECTORY = Path(__file__).resolve().parent
if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(MODULE_DIRECTORY))

from canonical_api_daemon import (  # noqa: E402
    INSTALLED_PLIST,
    INSTALLED_RUNNER,
    LABEL,
    SERVICE,
    canonical_paths,
    validate_contract,
)
from canonical_api_daemon_refresh import (  # noqa: E402
    inspect_asset,
    validate_immutable_source_context,
)

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
BOOTSTRAP_COMMAND = [
    "/bin/launchctl",
    "bootstrap",
    "system",
    str(INSTALLED_PLIST),
]


def default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )


def authorization_gate(
    *, apply: bool, confirmation: str, environment: Mapping[str, str],
    effective_user_id: int,
) -> dict[str, bool]:
    root_verified = apply and effective_user_id == 0
    environment_authorized = (
        apply and environment.get("AICONTROLCENTER_ALLOW_SYSTEM_WRITE") == "1"
    )
    label_confirmed = apply and confirmation == LABEL
    return {
        "dry_run": not apply,
        "root_required": True,
        "root_verified": root_verified,
        "environment_authorized": environment_authorized,
        "label_confirmed": label_confirmed,
        "apply_authorized": (
            root_verified and environment_authorized and label_confirmed
        ),
    }


def validate_current(immutable_source: Mapping[str, Any]) -> dict[str, Any]:
    current = Path(str(immutable_source["runtime_root"])) / "current"
    expected = Path(str(immutable_source["runtime_release"]))
    checks = {
        "current_is_symlink": False,
        "current_resolves": False,
        "current_matches_runtime_release": False,
    }
    resolved: str | None = None
    try:
        metadata = current.lstat()
        checks["current_is_symlink"] = stat.S_ISLNK(metadata.st_mode)
        physical = current.resolve(strict=True)
        resolved = str(physical)
        checks["current_resolves"] = True
        checks["current_matches_runtime_release"] = physical == expected.resolve(strict=True)
    except OSError:
        pass
    return {
        "path": str(current),
        "resolved_path": resolved,
        "checks": checks,
        "valid": all(checks.values()),
    }


def _bytes_match(first: Path, second: Path) -> bool:
    try:
        return first.read_bytes() == second.read_bytes()
    except OSError:
        return False


def validate_installed_assets(
    root: Path, *, installed_plist: Path, installed_runner: Path,
    expected_uid: int, expected_gid: int,
) -> dict[str, Any]:
    sources = canonical_paths(root.resolve())
    specifications = {
        "plist": (installed_plist, sources["plist"], 0o644),
        "runner": (installed_runner, sources["runner"], 0o755),
    }
    assets: dict[str, Any] = {}
    for name, (installed, source, mode) in specifications.items():
        inspection = inspect_asset(
            installed, expected_uid=expected_uid, expected_gid=expected_gid,
            expected_mode=mode,
        )
        inspection["source_path"] = str(source)
        inspection["byte_match"] = (
            inspection["valid"] and _bytes_match(installed, source)
        )
        inspection["valid"] = inspection["valid"] and inspection["byte_match"]
        assets[name] = inspection
    return {"assets": assets, "valid": all(item["valid"] for item in assets.values())}


def execute(
    *, root: Path, apply: bool, confirmation: str = "",
    environment: Mapping[str, str] | None = None,
    effective_user_id: int | None = None, runner: CommandRunner = default_runner,
    installed_plist: Path = INSTALLED_PLIST,
    installed_runner: Path = INSTALLED_RUNNER,
    expected_uid: int = 0, expected_gid: int | None = None,
) -> dict[str, Any]:
    contract = validate_contract(root.resolve())
    immutable_source = validate_immutable_source_context(root)
    current = validate_current(immutable_source)
    wheel_gid = grp.getgrnam("wheel").gr_gid if expected_gid is None else expected_gid
    installed_assets = validate_installed_assets(
        root, installed_plist=installed_plist, installed_runner=installed_runner,
        expected_uid=expected_uid, expected_gid=wheel_gid,
    )
    authorization = authorization_gate(
        apply=apply, confirmation=confirmation,
        environment=os.environ if environment is None else environment,
        effective_user_id=os.geteuid() if effective_user_id is None else effective_user_id,
    )
    static_ready = bool(
        contract["canonical_launchd_contract_gate_passed"]
        and immutable_source["immutable_source_context_valid"]
        and current["valid"] and installed_assets["valid"]
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "authorization": authorization,
        "canonical_contract": contract,
        "immutable_source": immutable_source,
        "runtime_current": current,
        "installed_assets": installed_assets,
        "service_probe": {"performed": False, "returncode": None, "eligible": False},
        "command": {"argv": BOOTSTRAP_COMMAND},
        "result": {"performed": False, "returncode": None},
        "write_operations_executed": 0,
        "canonical_bootstrap_gate_passed": static_ready if not apply else False,
    }
    if not static_ready:
        result["failure"] = {"step": "static_readiness"}
        return result
    if not apply:
        return result
    if not authorization["apply_authorized"]:
        result["failure"] = {"step": "system_write_authorization"}
        return result

    try:
        probe = runner(["/bin/launchctl", "print", SERVICE])
    except OSError as error:
        result["failure"] = {
            "step": "service_registration_probe",
            "state": "indeterminate",
            "error_type": type(error).__name__,
        }
        return result
    result["service_probe"] = {
        "performed": True,
        "returncode": probe.returncode,
        "eligible": probe.returncode == 113,
    }
    if probe.returncode != 113:
        result["failure"] = {
            "step": "service_registration_probe",
            "returncode": probe.returncode,
            "state": "registered" if probe.returncode == 0 else "indeterminate",
        }
        return result

    try:
        completed = runner(BOOTSTRAP_COMMAND)
    except OSError as error:
        result["write_operations_executed"] = 1
        result["result"] = {
            "performed": True,
            "returncode": None,
            "error_type": type(error).__name__,
        }
        result["failure"] = {
            "step": "bootstrap",
            "returncode": None,
            "error_type": type(error).__name__,
        }
        return result
    result["write_operations_executed"] = 1
    result["result"] = {"performed": True, "returncode": completed.returncode}
    if completed.returncode != 0:
        result["failure"] = {
            "step": "bootstrap", "returncode": completed.returncode,
        }
        return result
    result["canonical_bootstrap_gate_passed"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("dry-run", "apply"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--confirm", default="")
    arguments = parser.parse_args()
    result = execute(
        root=arguments.root, apply=arguments.action == "apply",
        confirmation=arguments.confirm,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["canonical_bootstrap_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
