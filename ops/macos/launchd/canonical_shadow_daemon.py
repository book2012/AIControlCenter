#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
from typing import Any


SCHEMA_VERSION = "1.0"

LABEL = "com.aicontrolcenter.api.shadow"
SERVICE = f"system/{LABEL}"

PLIST_NAME = f"{LABEL}.plist"
RUNNER_NAME = "run-shadow-daemon.sh"
SECRET_DELIVERY_NAME = "provider-secret-delivery.py"

INSTALLED_PLIST = Path(
    "/Library/LaunchDaemons"
) / PLIST_NAME

INSTALLED_RUNNER = Path(
    "/usr/local/libexec/aicontrolcenter"
) / RUNNER_NAME
INSTALLED_SECRET_DELIVERY = INSTALLED_RUNNER.parent / SECRET_DELIVERY_NAME

LOG_DIRECTORY = Path(
    "/var/log/aicontrolcenter"
)

STDOUT_LOG = (
    LOG_DIRECTORY
    / "shadow-daemon.stdout.log"
)

STDERR_LOG = (
    LOG_DIRECTORY
    / "shadow-daemon.stderr.log"
)


def canonical_paths(
    root: Path,
) -> dict[str, Path]:
    launchd = (
        root
        / "ops"
        / "macos"
        / "launchd"
    )

    return {
        "plist": launchd / PLIST_NAME,
        "runner": launchd / RUNNER_NAME,
        "secret_delivery": launchd / SECRET_DELIVERY_NAME,
    }


def load_plist(
    path: Path,
) -> dict[str, Any]:
    with path.open("rb") as stream:
        payload = plistlib.load(stream)

    if not isinstance(payload, dict):
        raise TypeError(
            "LaunchDaemon plist root must be a dictionary"
        )

    return payload


def validate_contract(
    root: Path,
) -> dict[str, Any]:
    paths = canonical_paths(root)

    plist_path = paths["plist"]
    runner_path = paths["runner"]
    secret_delivery_path = paths["secret_delivery"]

    plist_exists = plist_path.is_file()
    runner_exists = runner_path.is_file()
    secret_delivery_exists = secret_delivery_path.is_file()

    payload: dict[str, Any] = {}
    plist_parseable = False

    if plist_exists:
        try:
            payload = load_plist(
                plist_path
            )
            plist_parseable = True
        except (
            OSError,
            plistlib.InvalidFileException,
            TypeError,
        ):
            plist_parseable = False

    program_arguments = payload.get(
        "ProgramArguments"
    )

    environment = payload.get(
        "EnvironmentVariables"
    )

    checks = {
        "canonical_plist_exists":
            plist_exists,

        "canonical_runner_exists":
            runner_exists,
        "canonical_secret_delivery_exists": secret_delivery_exists,

        "canonical_plist_parseable":
            plist_parseable,

        "label_matches": (
            payload.get("Label")
            == LABEL
        ),

        "user_non_root": (
            payload.get("UserName")
            == "kyouhan"
        ),

        "group_matches": (
            payload.get("GroupName")
            == "staff"
        ),

        "mutable_working_directory_absent": (
            "WorkingDirectory" not in payload
        ),

        "program_arguments_match": (
            program_arguments
            == [
                "/bin/bash",
                str(INSTALLED_RUNNER),
            ]
        ),

        "run_at_load_enabled": (
            payload.get("RunAtLoad")
            is True
        ),

        "keep_alive_enabled": (
            payload.get("KeepAlive")
            is True
        ),

        "process_type_background": (
            payload.get("ProcessType")
            == "Background"
        ),

        "stdout_log_matches": (
            payload.get(
                "StandardOutPath"
            )
            == str(STDOUT_LOG)
        ),

        "stderr_log_matches": (
            payload.get(
                "StandardErrorPath"
            )
            == str(STDERR_LOG)
        ),

        "environment_is_object":
            isinstance(
                environment,
                dict,
            ),

        "environment_home_matches": (
            isinstance(
                environment,
                dict,
            )
            and
            environment.get("HOME")
            == "/Users/kyouhan"
        ),

        "python_unbuffered_enabled": (
            isinstance(
                environment,
                dict,
            )
            and
            environment.get(
                "PYTHONUNBUFFERED"
            )
            == "1"
        ),
    }

    gate = all(checks.values())

    return {
        "schema_version":
            SCHEMA_VERSION,

        "canonical_launchd_contract_gate_passed":
            gate,

        "checks": checks,

        "source": {
            "repository_root":
                str(root),
            "plist":
                str(plist_path),
            "runner":
                str(runner_path),
            "secret_delivery": str(secret_delivery_path),
        },

        "installation": {
            "label": LABEL,
            "service": SERVICE,
            "plist":
                str(INSTALLED_PLIST),
            "runner":
                str(INSTALLED_RUNNER),
            "secret_delivery": str(INSTALLED_SECRET_DELIVERY),
            "log_directory":
                str(LOG_DIRECTORY),
            "stdout_log":
                str(STDOUT_LOG),
            "stderr_log":
                str(STDERR_LOG),
            "application_user":
                "kyouhan",
            "application_group":
                "staff",
        },
    }


def build_install_plan(
    root: Path,
) -> dict[str, Any]:
    contract = validate_contract(
        root
    )

    paths = canonical_paths(root)

    plan = [
        {
            "step":
                "ensure_directory",
            "path":
                str(
                    INSTALLED_RUNNER.parent
                ),
            "owner":
                "root",
            "group":
                "wheel",
            "mode":
                "0755",
        },
        {
            "step":
                "ensure_directory",
            "path":
                str(LOG_DIRECTORY),
            "owner":
                "root",
            "group":
                "wheel",
            "mode":
                "0755",
        },
        {
            "step":
                "install_file",
            "source":
                str(paths["runner"]),
            "destination":
                str(INSTALLED_RUNNER),
            "owner":
                "root",
            "group":
                "wheel",
            "mode":
                "0755",
        },
        {
            "step": "install_file",
            "source": str(paths["secret_delivery"]),
            "destination": str(INSTALLED_SECRET_DELIVERY),
            "owner": "root",
            "group": "wheel",
            "mode": "0755",
        },
        {
            "step":
                "install_file",
            "source":
                str(paths["plist"]),
            "destination":
                str(INSTALLED_PLIST),
            "owner":
                "root",
            "group":
                "wheel",
            "mode":
                "0644",
        },
        {
            "step":
                "ensure_file",
            "path":
                str(STDOUT_LOG),
            "owner":
                "kyouhan",
            "group":
                "staff",
            "mode":
                "0640",
        },
        {
            "step":
                "ensure_file",
            "path":
                str(STDERR_LOG),
            "owner":
                "kyouhan",
            "group":
                "staff",
            "mode":
                "0640",
        },
        {
            "step":
                "launchctl_bootout_if_loaded",
            "service":
                SERVICE,
        },
        {
            "step":
                "launchctl_bootstrap",
            "domain":
                "system",
            "plist":
                str(INSTALLED_PLIST),
        },
        {
            "step":
                "launchctl_enable",
            "service":
                SERVICE,
        },
        {
            "step":
                "launchctl_kickstart",
            "service":
                SERVICE,
        },
    ]

    return {
        **contract,

        "write_operations_executed":
            False,

        "installation_plan": plan,

        "next_action": (
            "Manager may execute this plan"
            if contract[
                "canonical_launchd_contract_gate_passed"
            ]
            else
            "Installation blocked by canonical contract"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=(
            "preflight",
            "plan",
        ),
    )

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    arguments = parser.parse_args()

    root = arguments.root.resolve()

    if arguments.action == "preflight":
        result = validate_contract(
            root
        )
    else:
        result = build_install_plan(
            root
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
            "canonical_launchd_contract_gate_passed"
        ]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
