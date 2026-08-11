#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import sys
from typing import Any


LABEL = "com.aicontrolcenter.api"
RUNNER_NAME = "run-canonical-api-immutable-source.sh"
HOST = "127.0.0.1"
PORT = 58081


def paths(home: Path) -> dict[str, Path]:
    application_root = home / "Library" / "Application Support" / "AIControlCenter"
    return {
        "application_root": application_root,
        "data_root": application_root / "data",
        "runner": application_root / "bin" / RUNNER_NAME,
        "plist": home / "Library" / "LaunchAgents" / f"{LABEL}.plist",
        "stdout": home / "Library" / "Logs" / "AIControlCenter" / "canonical-api.stdout.log",
        "stderr": home / "Library" / "Logs" / "AIControlCenter" / "canonical-api.stderr.log",
    }


def launchagent(home: Path) -> dict[str, Any]:
    resolved = paths(home)
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/bash", str(resolved["runner"])],
        "EnvironmentVariables": {
            "AICONTROLCENTER_DATA_ROOT": str(resolved["data_root"]),
            "HOME": str(home),
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONUNBUFFERED": "1",
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Background",
        "ThrottleInterval": 10,
        "StandardOutPath": str(resolved["stdout"]),
        "StandardErrorPath": str(resolved["stderr"]),
    }


def render(home: Path) -> bytes:
    return plistlib.dumps(launchagent(home), fmt=plistlib.FMT_XML, sort_keys=True)


def build_plan(root: Path, home: Path, uid: int) -> dict[str, Any]:
    resolved = paths(home)
    source = root / "ops" / "macos" / "runtime" / RUNNER_NAME
    return {
        "schema_version": 1,
        "write_operations_executed": False,
        "activation_authorized": False,
        "contract": {
            "label": LABEL,
            "service": f"gui/{uid}/{LABEL}",
            "app": "core.api.app:app",
            "host": HOST,
            "port": PORT,
            "data_root": str(resolved["data_root"]),
        },
        "install": [
            {"operation": "install_file", "source": str(source), "destination": str(resolved["runner"]), "mode": "0755"},
            {"operation": "render_plist", "destination": str(resolved["plist"]), "deterministic": True},
        ],
        "activation_next_task_only": [
            ["launchctl", "bootstrap", f"gui/{uid}", str(resolved["plist"])],
            ["launchctl", "kickstart", f"gui/{uid}/{LABEL}"],
        ],
        "verification_next_task_only": {
            "listener": f"{HOST}:{PORT}",
            "url": f"http://{HOST}:{PORT}/health",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pure canonical API LaunchAgent IaC renderer")
    parser.add_argument("action", choices=("plan", "render-plist"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--uid", type=int, required=True)
    arguments = parser.parse_args()

    root = arguments.root.expanduser().resolve()
    home = arguments.home.expanduser().resolve()
    if arguments.action == "render-plist":
        sys.stdout.buffer.write(render(home))
    else:
        print(json.dumps(build_plan(root, home, arguments.uid), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
