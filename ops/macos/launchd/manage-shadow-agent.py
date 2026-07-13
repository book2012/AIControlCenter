#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LABEL = "com.aicontrolcenter.api.shadow"
HOST = "127.0.0.1"
PORT = 18100


def run(
    arguments: list[str],
    *,
    check: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=check,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def git(root: Path, *arguments: str) -> str:
    result = run(
        [
            "git",
            "-C",
            str(root),
            *arguments,
        ]
    )

    return result.stdout.strip()


def request(
    method: str,
    path: str,
) -> tuple[int, Any]:
    request_object = Request(
        f"http://{HOST}:{PORT}{path}",
        method=method,
    )

    try:
        with urlopen(
            request_object,
            timeout=2,
        ) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8")
    except (URLError, TimeoutError, OSError):
        return 0, None

    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, body


class ShadowAgent:
    def __init__(self) -> None:
        self.home = Path.home()
        self.root = Path(
            os.environ.get(
                "AICONTROLCENTER_ROOT",
                self.home / "AIControlCenter",
            )
        ).expanduser().resolve()

        self.uid = os.getuid()
        self.domain = f"gui/{self.uid}"
        self.service = f"{self.domain}/{LABEL}"

        self.runtime_root = (
            self.home
            / "Library"
            / "Application Support"
            / "AIControlCenter"
            / "runtime"
        )

        self.current_runtime = (
            self.runtime_root / "current"
        )

        self.launch_agents = (
            self.home
            / "Library"
            / "LaunchAgents"
        )

        self.plist_path = (
            self.launch_agents
            / f"{LABEL}.plist"
        )

        self.log_root = (
            self.home
            / "Library"
            / "Logs"
            / "AIControlCenter"
        )

        self.stdout_log = (
            self.log_root
            / "shadow-api.stdout.log"
        )

        self.stderr_log = (
            self.log_root
            / "shadow-api.stderr.log"
        )

        self.runner = (
            self.root
            / "ops"
            / "macos"
            / "launchd"
            / "run-shadow-api.sh"
        )

    def preflight(self) -> dict[str, Any]:
        commit = ""
        short_commit = ""
        runtime_target = ""

        checks = {
            "macos": platform.system() == "Darwin",
            "repository_exists":
                (self.root / ".git").is_dir(),
            "runner_executable":
                os.access(self.runner, os.X_OK),
            "current_runtime_active":
                self.current_runtime.is_symlink(),
            "repository_clean": False,
            "runtime_matches_commit": False,
            "shadow_import": False,
        }

        if checks["repository_exists"]:
            commit = git(
                self.root,
                "rev-parse",
                "HEAD",
            )

            short_commit = git(
                self.root,
                "rev-parse",
                "--short=12",
                "HEAD",
            )

            checks["repository_clean"] = (
                git(
                    self.root,
                    "status",
                    "--porcelain",
                )
                == ""
            )

        if self.current_runtime.is_symlink():
            runtime_target = os.readlink(
                self.current_runtime
            )

            checks["runtime_matches_commit"] = (
                Path(runtime_target).name
                == short_commit
            )

            python_path = (
                Path(runtime_target)
                / "bin"
                / "python"
            )

            if (
                python_path.is_file()
                and checks["repository_exists"]
            ):
                environment = os.environ.copy()
                environment["PYTHONPATH"] = str(
                    self.root
                )

                result = subprocess.run(
                    [
                        str(python_path),
                        "-c",
                        (
                            "from core.api.shadow "
                            "import app; "
                            "print(type(app).__name__)"
                        ),
                    ],
                    cwd=self.root,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                checks["shadow_import"] = (
                    result.returncode == 0
                )

        return {
            "passed": all(checks.values()),
            "checks": checks,
            "repository": {
                "path": str(self.root),
                "commit": commit,
                "short_commit": short_commit,
            },
            "runtime": {
                "current": runtime_target,
            },
        }

    def write_plist(self) -> None:
        self.launch_agents.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        plist = {
            "Label": LABEL,
            "ProgramArguments": [
                "/bin/bash",
                str(self.runner),
            ],
            "WorkingDirectory": str(self.root),
            "RunAtLoad": True,
            "KeepAlive": True,
            "ThrottleInterval": 10,
            "ProcessType": "Background",
            "Umask": 0o077,
            "EnvironmentVariables": {
                "HOME": str(self.home),
                "PATH": (
                    "/opt/homebrew/bin:"
                    "/usr/local/bin:"
                    "/usr/bin:"
                    "/bin:"
                    "/usr/sbin:"
                    "/sbin"
                ),
                "PYTHONUNBUFFERED": "1",
                "AICONTROLCENTER_MODE":
                    "shadow-read-only",
                "AICONTROLCENTER_SHADOW_HOST":
                    HOST,
                "AICONTROLCENTER_SHADOW_PORT":
                    str(PORT),
            },
            "StandardOutPath":
                str(self.stdout_log),
            "StandardErrorPath":
                str(self.stderr_log),
        }

        temporary_path = self.plist_path.with_suffix(
            ".plist.tmp"
        )

        with temporary_path.open("wb") as stream:
            plistlib.dump(
                plist,
                stream,
                sort_keys=True,
            )

        temporary_path.chmod(0o600)
        os.replace(
            temporary_path,
            self.plist_path,
        )

        validation = run(
            [
                "plutil",
                "-lint",
                str(self.plist_path),
            ]
        )

        if validation.returncode != 0:
            raise RuntimeError(
                validation.stderr
                or validation.stdout
            )

    def status(self) -> dict[str, Any]:
        launchctl = run(
            [
                "launchctl",
                "print",
                self.service,
            ]
        )

        loaded = launchctl.returncode == 0

        pid = None

        if loaded:
            match = re.search(
                r"\bpid = (\d+)",
                launchctl.stdout,
            )

            if match:
                pid = int(match.group(1))

        health_code, health_body = request(
            "GET",
            "/health",
        )

        probe_code, probe_body = request(
            "POST",
            "/__shadow_write_probe__",
        )

        listener = run(
            [
                "lsof",
                "-nP",
                f"-iTCP:{PORT}",
                "-sTCP:LISTEN",
            ]
        )

        listener_output = listener.stdout

        listener_local_only = (
            f"{HOST}:{PORT}" in listener_output
            and f"*:{PORT}" not in listener_output
            and f"0.0.0.0:{PORT}"
            not in listener_output
        )

        runtime_target = ""

        if self.current_runtime.is_symlink():
            runtime_target = os.readlink(
                self.current_runtime
            )

        short_commit = ""

        if (self.root / ".git").is_dir():
            short_commit = git(
                self.root,
                "rev-parse",
                "--short=12",
                "HEAD",
            )

        runtime_matches = (
            bool(runtime_target)
            and Path(runtime_target).name
            == short_commit
        )

        checks = {
            "loaded": loaded,
            "pid_active": pid is not None,
            "runtime_matches_commit":
                runtime_matches,
            "health_http_200":
                health_code == 200,
            "health_json_object":
                isinstance(health_body, dict),
            "mutating_requests_blocked":
                probe_code == 405,
            "listener_local_only":
                listener_local_only,
        }

        return {
            "schema_version": "1.0",
            "shadow_supervisor_gate_passed":
                all(checks.values()),
            "label": LABEL,
            "service": self.service,
            "checks": checks,
            "process": {
                "pid": pid,
                "launchctl_loaded": loaded,
            },
            "runtime": {
                "current": runtime_target,
                "expected_commit":
                    short_commit,
            },
            "endpoint": {
                "host": HOST,
                "port": PORT,
                "health_code": health_code,
                "health_response": health_body,
                "write_probe_code":
                    probe_code,
                "write_probe_response":
                    probe_body,
            },
            "logs": {
                "stdout": str(
                    self.stdout_log
                ),
                "stderr": str(
                    self.stderr_log
                ),
            },
            "safety": {
                "localhost_only": True,
                "shadow_read_only": True,
                "ubuntu_modified": False,
                "secrets_migrated": False,
            },
        }

    def install(self) -> dict[str, Any]:
        preflight = self.preflight()

        if not preflight["passed"]:
            return {
                "schema_version": "1.0",
                "shadow_supervisor_gate_passed":
                    False,
                "failure": {
                    "step": "preflight",
                },
                "preflight": preflight,
            }

        self.write_plist()

        run(
            [
                "launchctl",
                "bootout",
                self.service,
            ]
        )

        run(
            [
                "launchctl",
                "bootout",
                self.domain,
                str(self.plist_path),
            ]
        )

        bootstrap = run(
            [
                "launchctl",
                "bootstrap",
                self.domain,
                str(self.plist_path),
            ]
        )

        if bootstrap.returncode != 0:
            return {
                "schema_version": "1.0",
                "shadow_supervisor_gate_passed":
                    False,
                "failure": {
                    "step": "launchctl bootstrap",
                    "stdout":
                        bootstrap.stdout,
                    "stderr":
                        bootstrap.stderr,
                },
                "preflight": preflight,
            }

        run(
            [
                "launchctl",
                "enable",
                self.service,
            ]
        )

        run(
            [
                "launchctl",
                "kickstart",
                "-k",
                self.service,
            ]
        )

        status = self.status()

        for _ in range(40):
            if status[
                "shadow_supervisor_gate_passed"
            ]:
                break

            time.sleep(0.25)
            status = self.status()

        status["preflight"] = preflight
        status["plist"] = str(
            self.plist_path
        )

        return status

    def uninstall(self) -> dict[str, Any]:
        run(
            [
                "launchctl",
                "bootout",
                self.service,
            ]
        )

        run(
            [
                "launchctl",
                "bootout",
                self.domain,
                str(self.plist_path),
            ]
        )

        if self.plist_path.exists():
            self.plist_path.unlink()

        time.sleep(0.5)

        listener = run(
            [
                "lsof",
                "-nP",
                f"-iTCP:{PORT}",
                "-sTCP:LISTEN",
            ]
        )

        return {
            "schema_version": "1.0",
            "uninstalled": True,
            "label": LABEL,
            "plist_removed":
                not self.plist_path.exists(),
            "port_released":
                listener.returncode != 0,
            "safety": {
                "ubuntu_modified": False,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices={
            "preflight",
            "install",
            "status",
            "uninstall",
        },
    )

    arguments = parser.parse_args()
    agent = ShadowAgent()

    if arguments.action == "preflight":
        result = agent.preflight()
        passed = result["passed"]
    elif arguments.action == "install":
        result = agent.install()
        passed = result.get(
            "shadow_supervisor_gate_passed",
            False,
        )
    elif arguments.action == "status":
        result = agent.status()
        passed = result.get(
            "shadow_supervisor_gate_passed",
            False,
        )
    else:
        result = agent.uninstall()
        passed = (
            result["plist_removed"]
            and result["port_released"]
        )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
