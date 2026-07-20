import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGETS = {
    "binary": Path("/opt/homebrew/bin/ollama"),
    "plist": Path("/Library/LaunchDaemons/com.aicontrolcenter.ollama.plist"),
    "environment": Path("/Library/Application Support/AIControlCenter/ollama.env"),
    "models": Path.home() / "Library/Application Support/Ollama/models",
}

LAUNCHD_SERVICE = "system/com.aicontrolcenter.ollama"


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_state(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_directory": path.is_dir(),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }


def inspect_launchd() -> dict[str, Any]:
    result = subprocess.run(
        ["launchctl", "print", LAUNCHD_SERVICE],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "service": LAUNCHD_SERVICE,
            "present": False,
            "running": False,
            "pid": None,
        }

    running = False
    pid = None

    for line in result.stdout.splitlines():
        value = line.strip()
        if value == "state = running":
            running = True
        if value.startswith("pid = "):
            raw_pid = value.split("=", 1)[1].strip()
            if raw_pid.isdigit():
                pid = int(raw_pid)

    return {
        "service": LAUNCHD_SERVICE,
        "present": True,
        "running": running,
        "pid": pid,
    }


def copy_file(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        return {
            "source": str(source),
            "destination": None,
            "copied": False,
            "reason": "source-not-present",
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "copied": True,
        "reason": None,
    }


def build_backup(
    output_root: Path,
    write_backup: bool = False,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_directory = output_root / f"ollama-{timestamp}"

    states = {
        name: path_state(path)
        for name, path in TARGETS.items()
    }

    copies: list[dict[str, Any]] = []

    if write_backup:
        copies.append(
            copy_file(TARGETS["binary"], backup_directory / "binary/ollama")
        )
        copies.append(
            copy_file(
                TARGETS["plist"],
                backup_directory / "launchd/com.aicontrolcenter.ollama.plist",
            )
        )
        copies.append(
            copy_file(
                TARGETS["environment"],
                backup_directory / "environment/ollama.env",
            )
        )

    result = {
        "schema_version": "1.0",
        "service_id": "ollama",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "write-backup" if write_backup else "dry-run",
        "write_performed": write_backup,
        "backup_directory": str(backup_directory),
        "targets": states,
        "launchd": inspect_launchd(),
        "copies": copies,
        "models_policy": {
            "copy_models": False,
            "preserve_models": True,
            "metadata_only": True,
        },
        "restore_plan": [
            "stop-launchdaemon-if-running",
            "restore-plist-if-backed-up",
            "restore-environment-if-backed-up",
            "restore-binary-if-backed-up",
            "bootstrap-previous-launchdaemon-if-present",
            "validate-health-or-absence",
        ],
    }

    if write_backup:
        backup_directory.mkdir(parents=True, exist_ok=True)
        manifest_path = backup_directory / "backup-manifest.json"
        manifest_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        result["manifest_path"] = str(manifest_path)
    else:
        result["manifest_path"] = None

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an Ollama rollback backup."
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--write-backup", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_backup(
        args.output_root,
        write_backup=args.write_backup,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
