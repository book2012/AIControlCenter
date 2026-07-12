from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.datacenter.snapshot import DatacenterSnapshotService
from core.worker.local_runner import LocalRunner
from core.worker.ubuntu import UbuntuWorkerClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATACENTER_ROOT = Path("/opt/aihomedatacenter")


def command_ok(
    command: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
) -> bool:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def git_clean(path: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return False

    lines = [
        line
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if path == DATACENTER_ROOT:
        allowed = {
            "?? reports/storage-agent/",
            "?? scripts/deferred/nextcloud-files-scan.sh",
        }
        lines = [line for line in lines if line not in allowed]

    return not lines


def main() -> int:
    checks: dict[str, Any] = {}

    checks["tests"] = command_ok(
        [sys.executable, "-m", "pytest", "-q"]
    )

    checks["controlcenter_git_clean"] = git_clean(
        PROJECT_ROOT
    )

    checks["datacenter_git_clean"] = git_clean(
        DATACENTER_ROOT
    )

    checks["mac_profile"] = command_ok(
        ["bash", "deploy/macos/validate-macos-profile.sh"]
    )

    worker = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    snapshot = DatacenterSnapshotService(
        worker
    ).status()

    checks["snapshot_available"] = (
        snapshot["overall_status"]
        in {"HEALTHY", "WARNING"}
    )

    checks["storage_integrity"] = (
        snapshot["storage"]
        .get("database", {})
        .get("integrity")
        == "ok"
    )

    checks["storage_schema_v3"] = (
        snapshot["database"].get("schema_version")
        == "3"
    )

    checks["backup_read_only"] = (
        snapshot["backup"]
        .get("safety", {})
        .get("read_only")
        is True
    )

    checks["services_read_only"] = (
        snapshot["services"]
        .get("safety", {})
        .get("read_only")
        is True
    )

    shutdown = worker.shutdown_plan()

    checks["shutdown_dry_run"] = (
        shutdown.get("mode") == "dry-run"
        and shutdown.get("executed") is False
        and shutdown.get("safety", {}).get(
            "forced_shutdown"
        ) is False
    )

    overall_ready = all(checks.values())

    payload = {
        "platform": "AI Home Datacenter",
        "control_plane": str(PROJECT_ROOT),
        "datacenter": str(DATACENTER_ROOT),
        "checks": checks,
        "snapshot": {
            "overall_status": snapshot[
                "overall_status"
            ],
            "unavailable_components": snapshot.get(
                "unavailable_components",
                [],
            ),
            "storage_schema": snapshot[
                "database"
            ].get("schema_version"),
            "backup_status": snapshot[
                "backup"
            ].get("overall_status"),
            "services_status": snapshot[
                "services"
            ].get("overall_status"),
        },
        "overall": (
            "READY"
            if overall_ready
            else "NOT_READY"
        ),
    }

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if overall_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
