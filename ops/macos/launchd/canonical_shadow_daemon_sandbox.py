#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import stat
import sys
from typing import Any


MODULE_DIRECTORY = Path(__file__).resolve().parent

if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(MODULE_DIRECTORY))


from canonical_shadow_daemon import (  # noqa: E402
    INSTALLED_PLIST,
    INSTALLED_RUNNER,
    STDERR_LOG,
    STDOUT_LOG,
    canonical_paths,
)


SCHEMA_VERSION = "1.0"
BACKUP_DIRECTORY_NAME = ".aicontrolcenter-shadow-backup"
BACKUP_MANIFEST_NAME = "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def plist_semantic_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        payload = plistlib.load(stream)

    normalized = plistlib.dumps(
        payload,
        fmt=plistlib.FMT_BINARY,
        sort_keys=True,
    )

    return hashlib.sha256(normalized).hexdigest()


def file_mode(path: Path) -> str:
    mode = stat.S_IMODE(path.stat().st_mode)

    return format(mode, "04o")


def sandbox_path(
    sandbox_root: Path,
    system_path: Path,
) -> Path:
    if not system_path.is_absolute():
        raise ValueError(
            f"System path must be absolute: {system_path}"
        )

    return (
        sandbox_root.resolve()
        / system_path.relative_to("/")
    )


def sandbox_destinations(
    sandbox_root: Path,
) -> dict[str, Path]:
    return {
        "plist": sandbox_path(
            sandbox_root,
            INSTALLED_PLIST,
        ),
        "runner": sandbox_path(
            sandbox_root,
            INSTALLED_RUNNER,
        ),
        "stdout_log": sandbox_path(
            sandbox_root,
            STDOUT_LOG,
        ),
        "stderr_log": sandbox_path(
            sandbox_root,
            STDERR_LOG,
        ),
    }


def backup_paths(
    sandbox_root: Path,
) -> dict[str, Path]:
    backup_root = (
        sandbox_root.resolve()
        / BACKUP_DIRECTORY_NAME
    )

    return {
        "root": backup_root,
        "manifest": (
            backup_root
            / BACKUP_MANIFEST_NAME
        ),
        "plist": backup_root / "previous.plist",
        "runner": backup_root / "previous-runner.sh",
    }


def copy_with_mode(
    source: Path,
    destination: Path,
    mode: int,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copyfile(
        source,
        destination,
    )

    destination.chmod(mode)


def capture_backup(
    sandbox_root: Path,
) -> dict[str, Any]:
    destinations = sandbox_destinations(
        sandbox_root
    )

    backups = backup_paths(
        sandbox_root
    )

    backups["root"].mkdir(
        parents=True,
        exist_ok=True,
    )

    assets: dict[str, Any] = {}

    for name in ("plist", "runner"):
        destination = destinations[name]
        backup = backups[name]

        existed = destination.is_file()

        asset: dict[str, Any] = {
            "destination": str(destination),
            "backup": str(backup),
            "existed": existed,
            "sha256": None,
            "mode": None,
        }

        if existed:
            shutil.copyfile(
                destination,
                backup,
            )

            asset["sha256"] = sha256(
                destination
            )

            asset["mode"] = file_mode(
                destination
            )

        assets[name] = asset

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "assets": assets,
    }

    backups["manifest"].write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest


def validate_install(
    repository_root: Path,
    sandbox_root: Path,
) -> dict[str, Any]:
    sources = canonical_paths(
        repository_root.resolve()
    )

    destinations = sandbox_destinations(
        sandbox_root
    )

    checks = {
        "plist_installed":
            destinations["plist"].is_file(),

        "runner_installed":
            destinations["runner"].is_file(),

        "stdout_log_created":
            destinations["stdout_log"].is_file(),

        "stderr_log_created":
            destinations["stderr_log"].is_file(),
    }

    if checks["plist_installed"]:
        checks["plist_semantic_match"] = (
            plist_semantic_sha256(
                sources["plist"]
            )
            ==
            plist_semantic_sha256(
                destinations["plist"]
            )
        )

        checks["plist_mode_0644"] = (
            file_mode(
                destinations["plist"]
            )
            == "0644"
        )
    else:
        checks["plist_semantic_match"] = False
        checks["plist_mode_0644"] = False

    if checks["runner_installed"]:
        checks["runner_sha256_match"] = (
            sha256(sources["runner"])
            ==
            sha256(destinations["runner"])
        )

        checks["runner_mode_0755"] = (
            file_mode(
                destinations["runner"]
            )
            == "0755"
        )
    else:
        checks["runner_sha256_match"] = False
        checks["runner_mode_0755"] = False

    for log_name in (
        "stdout_log",
        "stderr_log",
    ):
        check_name = f"{log_name}_mode_0640"

        checks[check_name] = (
            destinations[log_name].is_file()
            and
            file_mode(
                destinations[log_name]
            )
            == "0640"
        )

    gate = all(checks.values())

    return {
        "sandbox_install_gate_passed": gate,
        "checks": checks,
        "destinations": {
            key: str(value)
            for key, value
            in destinations.items()
        },
    }


def install(
    repository_root: Path,
    sandbox_root: Path,
) -> dict[str, Any]:
    resolved_repository = (
        repository_root.resolve()
    )

    resolved_sandbox = sandbox_root.resolve()

    sources = canonical_paths(
        resolved_repository
    )

    destinations = sandbox_destinations(
        resolved_sandbox
    )

    backup = capture_backup(
        resolved_sandbox
    )

    copy_with_mode(
        sources["plist"],
        destinations["plist"],
        0o644,
    )

    copy_with_mode(
        sources["runner"],
        destinations["runner"],
        0o755,
    )

    for log_name in (
        "stdout_log",
        "stderr_log",
    ):
        log_path = destinations[log_name]

        log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        log_path.touch(
            exist_ok=True,
        )

        log_path.chmod(0o640)

    validation = validate_install(
        resolved_repository,
        resolved_sandbox,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "action": "install",
        **validation,
        "system_write_operations_executed": False,
        "launchctl_commands_executed": False,
        "write_scope": "sandbox_only",
        "sandbox_root": str(resolved_sandbox),
        "backup": backup,
    }


def rollback(
    sandbox_root: Path,
) -> dict[str, Any]:
    resolved_sandbox = sandbox_root.resolve()

    destinations = sandbox_destinations(
        resolved_sandbox
    )

    backups = backup_paths(
        resolved_sandbox
    )

    manifest_path = backups["manifest"]

    if not manifest_path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "action": "rollback",
            "sandbox_rollback_gate_passed": False,
            "system_write_operations_executed": False,
            "launchctl_commands_executed": False,
            "failure": {
                "step": "load_backup_manifest",
                "detail": "Backup manifest not found",
            },
        }

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    checks: dict[str, bool] = {}

    for name in ("plist", "runner"):
        asset = manifest["assets"][name]
        destination = destinations[name]
        backup = Path(asset["backup"])

        if asset["existed"]:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copyfile(
                backup,
                destination,
            )

            destination.chmod(
                int(asset["mode"], 8)
            )

            checks[f"{name}_restored"] = (
                destination.is_file()
                and
                sha256(destination)
                == asset["sha256"]
                and
                file_mode(destination)
                == asset["mode"]
            )
        else:
            destination.unlink(
                missing_ok=True
            )

            checks[f"{name}_removed"] = (
                not destination.exists()
            )

    gate = all(checks.values())

    return {
        "schema_version": SCHEMA_VERSION,
        "action": "rollback",
        "sandbox_rollback_gate_passed": gate,
        "checks": checks,
        "system_write_operations_executed": False,
        "launchctl_commands_executed": False,
        "write_scope": "sandbox_only",
        "sandbox_root": str(resolved_sandbox),
    }


def cycle(
    repository_root: Path,
    sandbox_root: Path,
) -> dict[str, Any]:
    install_result = install(
        repository_root,
        sandbox_root,
    )

    rollback_result = rollback(
        sandbox_root,
    )

    gate = (
        install_result[
            "sandbox_install_gate_passed"
        ]
        and
        rollback_result[
            "sandbox_rollback_gate_passed"
        ]
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "action": "cycle",
        "sandbox_cycle_gate_passed": gate,
        "system_write_operations_executed": False,
        "launchctl_commands_executed": False,
        "install": install_result,
        "rollback": rollback_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=(
            "install",
            "rollback",
            "cycle",
        ),
    )

    parser.add_argument(
        "--root",
        type=Path,
    )

    parser.add_argument(
        "--sandbox",
        type=Path,
        required=True,
    )

    arguments = parser.parse_args()

    if arguments.action in (
        "install",
        "cycle",
    ) and arguments.root is None:
        parser.error(
            "--root is required for install and cycle"
        )

    if arguments.action == "install":
        result = install(
            arguments.root,
            arguments.sandbox,
        )

        gate = result[
            "sandbox_install_gate_passed"
        ]

    elif arguments.action == "rollback":
        result = rollback(
            arguments.sandbox,
        )

        gate = result[
            "sandbox_rollback_gate_passed"
        ]

    else:
        result = cycle(
            arguments.root,
            arguments.sandbox,
        )

        gate = result[
            "sandbox_cycle_gate_passed"
        ]

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
