#!/usr/bin/env python3

"""Canonical API system LaunchDaemon contract and first-install plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
from typing import Any


SCHEMA_VERSION = "1.0"
LABEL = "com.aicontrolcenter.api"
SERVICE = f"system/{LABEL}"
BOOTSTRAP_DOMAIN = "system"
RUNNER_NAME = "run-canonical-api-immutable-source.sh"
PLIST_NAME = f"{LABEL}.plist"

INSTALLED_PLIST = Path("/Library/LaunchDaemons") / PLIST_NAME
INSTALLED_RUNNER = Path("/usr/local/libexec/aicontrolcenter") / RUNNER_NAME
LOG_DIRECTORY = Path("/var/log/aicontrolcenter")
STDOUT_LOG = LOG_DIRECTORY / "canonical-api.stdout.log"
STDERR_LOG = LOG_DIRECTORY / "canonical-api.stderr.log"
DATA_ROOT = "/Users/kyouhan/Library/Application Support/AIControlCenter/data"

EXPECTED_ENVIRONMENT = {
    "HOME": "/Users/kyouhan",
    "AICONTROLCENTER_DATA_ROOT": DATA_ROOT,
    "PYTHONUNBUFFERED": "1",
    "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
}


def canonical_paths(root: Path) -> dict[str, Path]:
    return {
        "plist": root / "ops" / "macos" / "launchd" / PLIST_NAME,
        "runner": root / "ops" / "macos" / "runtime" / RUNNER_NAME,
    }


def load_plist(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        payload = plistlib.load(stream)
    if not isinstance(payload, dict):
        raise TypeError("LaunchDaemon plist root must be a dictionary")
    return payload


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def validate_contract(root: Path) -> dict[str, Any]:
    paths = canonical_paths(root.resolve())
    plist_exists = paths["plist"].is_file()
    runner_exists = paths["runner"].is_file()
    payload: dict[str, Any] = {}
    parseable = False
    if plist_exists:
        try:
            payload = load_plist(paths["plist"])
            parseable = True
        except (OSError, plistlib.InvalidFileException, TypeError):
            pass

    runner_text = _read_text(paths["runner"])
    plist_text = _read_text(paths["plist"])
    combined = f"{plist_text}\n{runner_text}"
    arguments = payload.get("ProgramArguments")
    environment = payload.get("EnvironmentVariables")

    checks = {
        "repository_plist_exists": plist_exists,
        "canonical_runner_exists": runner_exists,
        "canonical_runner_executable": paths["runner"].is_file() and bool(paths["runner"].stat().st_mode & 0o111),
        "canonical_plist_parseable": parseable,
        "label_matches": payload.get("Label") == LABEL,
        "user_matches": payload.get("UserName") == "kyouhan",
        "group_matches": payload.get("GroupName") == "staff",
        "program_arguments_match": arguments == ["/bin/bash", str(INSTALLED_RUNNER)],
        "environment_matches_exactly": environment == EXPECTED_ENVIRONMENT,
        "run_at_load_enabled": payload.get("RunAtLoad") is True,
        "keep_alive_enabled": payload.get("KeepAlive") is True,
        "process_type_background": payload.get("ProcessType") == "Background",
        "throttle_interval_matches": payload.get("ThrottleInterval") == 10,
        "stdout_log_matches": payload.get("StandardOutPath") == str(STDOUT_LOG),
        "stderr_log_matches": payload.get("StandardErrorPath") == str(STDERR_LOG),
        "mutable_working_directory_absent": "WorkingDirectory" not in payload,
        "runner_preserves_canonical_app": "core.api.app:app" in runner_text,
        "runner_preserves_canonical_host": "127.0.0.1" in runner_text,
        "runner_preserves_canonical_port": "58081" in runner_text,
        "runner_preserves_immutable_runtime": all(token in runner_text for token in ("runtime", "current", "sources/$RUNTIME_ID", "RUNTIME_COMMIT", "SOURCE_COMMIT")),
        "shadow_contract_absent": all(token not in combined for token in ("com.aicontrolcenter.api.shadow", "core.api.shadow:app", "18100")),
        "provider_credentials_absent": all(token not in combined.lower() for token in ("provider credential", "provider_credential", "provider-credential")),
        "provider_secret_delivery_absent": "provider-secret-delivery" not in combined,
    }
    gate = all(checks.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "canonical_launchd_contract_gate_passed": gate,
        "checks": checks,
        "source": {"repository_root": str(root.resolve()), "plist": str(paths["plist"]), "runner": str(paths["runner"])},
        "installation": {
            "label": LABEL,
            "service": SERVICE,
            "bootstrap_domain": BOOTSTRAP_DOMAIN,
            "plist": str(INSTALLED_PLIST),
            "runner": str(INSTALLED_RUNNER),
            "log_directory": str(LOG_DIRECTORY),
            "stdout_log": str(STDOUT_LOG),
            "stderr_log": str(STDERR_LOG),
            "application_user": "kyouhan",
            "application_group": "staff",
            "application": "core.api.app:app",
            "host": "127.0.0.1",
            "port": 58081,
            "data_root": DATA_ROOT,
        },
    }


def build_install_plan(root: Path) -> dict[str, Any]:
    contract = validate_contract(root)
    paths = canonical_paths(root.resolve())
    plan = [
        {"step": "ensure_directory", "path": str(INSTALLED_RUNNER.parent), "owner": "root", "group": "wheel", "mode": "0755"},
        {"step": "ensure_directory", "path": str(LOG_DIRECTORY), "owner": "root", "group": "wheel", "mode": "0755"},
        {"step": "install_file", "source": str(paths["runner"]), "destination": str(INSTALLED_RUNNER), "owner": "root", "group": "wheel", "mode": "0755"},
        {"step": "install_file", "source": str(paths["plist"]), "destination": str(INSTALLED_PLIST), "owner": "root", "group": "wheel", "mode": "0644"},
        {"step": "ensure_file", "path": str(STDOUT_LOG), "owner": "kyouhan", "group": "staff", "mode": "0640"},
        {"step": "ensure_file", "path": str(STDERR_LOG), "owner": "kyouhan", "group": "staff", "mode": "0640"},
        {"step": "launchctl_bootstrap", "domain": BOOTSTRAP_DOMAIN, "plist": str(INSTALLED_PLIST)},
        {"step": "launchctl_enable", "service": SERVICE},
        {"step": "launchctl_kickstart", "service": SERVICE},
    ]
    return {**contract, "write_operations_executed": False, "installation_plan": plan,
            "first_activation_only": True,
            "next_action": "Explicitly authorize the bounded first install" if contract["canonical_launchd_contract_gate_passed"] else "Installation blocked by canonical contract"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "plan"))
    parser.add_argument("--root", required=True, type=Path)
    arguments = parser.parse_args()
    result = validate_contract(arguments.root) if arguments.action == "preflight" else build_install_plan(arguments.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["canonical_launchd_contract_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
