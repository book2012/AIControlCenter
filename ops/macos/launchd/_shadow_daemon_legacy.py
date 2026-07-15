#!/usr/bin/env python3

from __future__ import annotations

import argparse
import grp
import json
import os
from pathlib import Path
import platform
import plistlib
import pwd
import re
import subprocess
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LABEL = "com.aicontrolcenter.api.shadow"
SERVICE = f"system/{LABEL}"

RUN_USER = "kyouhan"
RUN_GROUP = "staff"

HOST = "127.0.0.1"
PORT = 18100


def run(
    arguments: list[str],
    *,
    sudo: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = list(arguments)

    if sudo:
        command = [
            "sudo",
            "-n",
            *command,
        ]

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def request(
    method: str,
    path: str,
) -> tuple[int, Any]:
    data = None

    if method != "GET":
        data = b"{}"

    request_object = Request(
        f"http://{HOST}:{PORT}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
        },
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


class ShadowDaemon:
    def __init__(self) -> None:
        self.home = Path(
            f"/Users/{RUN_USER}"
        )

        self.root = Path(
            os.environ.get(
                "AICONTROLCENTER_ROOT",
                self.home / "AIControlCenter",
            )
        ).expanduser().resolve()

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

        self.source_runner = (
            self.root
            / "ops"
            / "macos"
            / "launchd"
            / "run-shadow-daemon.sh"
        )

        self.install_root = Path(
            "/usr/local/libexec/aicontrolcenter"
        )

        self.installed_runner = (
            self.install_root
            / "run-shadow-daemon.sh"
        )

        self.plist_path = Path(
            f"/Library/LaunchDaemons/{LABEL}.plist"
        )

        self.log_root = (
            self.home
            / "Library"
            / "Logs"
            / "AIControlCenter"
        )

        self.stdout_log = (
            self.log_root
            / "shadow-daemon.stdout.log"
        )

        self.stderr_log = (
            self.log_root
            / "shadow-daemon.stderr.log"
        )

    def git(self, *arguments: str) -> str:
        result = run(
            [
                "/usr/bin/git",
                "-C",
                str(self.root),
                *arguments,
            ]
        )

        return result.stdout.strip()

    def runtime_target(self) -> Path | None:
        if not self.current_runtime.is_symlink():
            return None

        target = Path(
            os.readlink(self.current_runtime)
        )

        if not target.is_absolute():
            target = (
                self.current_runtime.parent
                / target
            ).resolve()

        return target

    def preflight(self) -> dict[str, Any]:
        checks = {
            "macos":
                platform.system() == "Darwin",
            "run_user_exists": False,
            "run_group_exists": False,
            "repository_exists":
                (self.root / ".git").is_dir(),
            "repository_clean": False,
            "runner_executable":
                os.access(
                    self.source_runner,
                    os.X_OK,
                ),
            "current_runtime_active":
                self.current_runtime.is_symlink(),
            "runtime_matches_commit": False,
            "runtime_python_executable": False,
            "shadow_import": False,
        }

        try:
            pwd.getpwnam(RUN_USER)
            checks["run_user_exists"] = True
        except KeyError:
            pass

        try:
            grp.getgrnam(RUN_GROUP)
            checks["run_group_exists"] = True
        except KeyError:
            pass

        commit = ""
        short_commit = ""
        runtime = self.runtime_target()

        if checks["repository_exists"]:
            commit = self.git(
                "rev-parse",
                "HEAD",
            )

            short_commit = self.git(
                "rev-parse",
                "--short=12",
                "HEAD",
            )

            checks["repository_clean"] = (
                self.git(
                    "status",
                    "--porcelain",
                )
                == ""
            )

        if runtime is not None:
            checks["runtime_matches_commit"] = (
                runtime.name == short_commit
            )

            python_path = (
                runtime / "bin" / "python"
            )

            checks["runtime_python_executable"] = (
                os.access(
                    python_path,
                    os.X_OK,
                )
            )

            if (
                checks["runtime_python_executable"]
                and checks["repository_exists"]
            ):
                environment = os.environ.copy()

                environment.update(
                    {
                        "HOME": str(self.home),
                        "PYTHONPATH": str(self.root),
                        "PYTHONDONTWRITEBYTECODE": "1",
                    }
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
            "schema_version": "1.0",
            "passed": all(checks.values()),
            "checks": checks,
            "repository": {
                "path": str(self.root),
                "commit": commit,
                "short_commit": short_commit,
            },
            "runtime": {
                "current":
                    str(runtime or ""),
            },
            "execution": {
                "user": RUN_USER,
                "group": RUN_GROUP,
                "root_process": False,
            },
        }

    def plist(self) -> dict[str, Any]:
        return {
            "Label": LABEL,
            "ProgramArguments": [
                str(self.installed_runner),
            ],
            "UserName": RUN_USER,
            "GroupName": RUN_GROUP,
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
                "PYTHONDONTWRITEBYTECODE": "1",
                "AICONTROLCENTER_ROOT":
                    str(self.root),
                "AICONTROLCENTER_HOME":
                    str(self.home),
                "AICONTROLCENTER_RUN_USER":
                    RUN_USER,
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

    def launchctl_print(
        self,
    ) -> subprocess.CompletedProcess[str]:
        result = run(
            [
                "launchctl",
                "print",
                SERVICE,
            ]
        )

        if result.returncode != 0:
            sudo_ready = run(
                ["true"],
                sudo=True,
            )

            if sudo_ready.returncode == 0:
                result = run(
                    [
                        "launchctl",
                        "print",
                        SERVICE,
                    ],
                    sudo=True,
                )

        return result

    def status(self) -> dict[str, Any]:
        launchctl_result = (
            self.launchctl_print()
        )

        loaded = (
            launchctl_result.returncode == 0
        )

        pid = None
        state = ""

        if loaded:
            pid_match = re.search(
                r"\bpid = (\d+)",
                launchctl_result.stdout,
            )

            state_match = re.search(
                r"\bstate = ([^\n]+)",
                launchctl_result.stdout,
            )

            if pid_match:
                pid = int(pid_match.group(1))

            if state_match:
                state = state_match.group(1).strip()

        process_user = ""

        if pid is not None:
            process_result = run(
                [
                    "ps",
                    "-o",
                    "user=",
                    "-p",
                    str(pid),
                ]
            )

            process_user = (
                process_result.stdout.strip()
            )

        health_code, health_body = request(
            "GET",
            "/health",
        )

        write_code, write_body = request(
            "POST",
            "/__shadow_write_probe__",
        )

        listener_result = run(
            [
                "lsof",
                "-nP",
                f"-iTCP:{PORT}",
                "-sTCP:LISTEN",
            ]
        )

        listener_output = (
            listener_result.stdout
        )

        listener_local_only = (
            f"{HOST}:{PORT}" in listener_output
            and f"*:{PORT}" not in listener_output
            and f"0.0.0.0:{PORT}"
            not in listener_output
            and f"[::]:{PORT}"
            not in listener_output
        )

        runtime = self.runtime_target()
        expected = ""

        if (self.root / ".git").is_dir():
            expected = self.git(
                "rev-parse",
                "--short=12",
                "HEAD",
            )

        runtime_matches = (
            runtime is not None
            and runtime.name == expected
        )

        plist_secure = False
        runner_secure = False

        if self.plist_path.exists():
            stat = self.plist_path.stat()

            plist_secure = (
                stat.st_uid == 0
                and stat.st_mode & 0o022 == 0
            )

        if self.installed_runner.exists():
            stat = self.installed_runner.stat()

            runner_secure = (
                stat.st_uid == 0
                and stat.st_mode & 0o022 == 0
            )

        checks = {
            "loaded": loaded,
            "pid_active": pid is not None,
            "process_user_non_root":
                process_user == RUN_USER,
            "runtime_matches_commit":
                runtime_matches,
            "health_http_200":
                health_code == 200,
            "health_json_object":
                isinstance(health_body, dict),
            "mutating_requests_blocked":
                write_code == 405,
            "listener_local_only":
                listener_local_only,
            "plist_root_owned_secure":
                plist_secure,
            "runner_root_owned_secure":
                runner_secure,
        }

        return {
            "schema_version": "1.0",
            "shadow_daemon_gate_passed":
                all(checks.values()),
            "label": LABEL,
            "service": SERVICE,
            "checks": checks,
            "process": {
                "pid": pid,
                "state": state,
                "user": process_user,
            },
            "runtime": {
                "current": str(runtime or ""),
                "expected_commit": expected,
            },
            "endpoint": {
                "host": HOST,
                "port": PORT,
                "health_code": health_code,
                "health_response": health_body,
                "write_probe_code": write_code,
                "write_probe_response": write_body,
            },
            "installation": {
                "plist": str(self.plist_path),
                "runner":
                    str(self.installed_runner),
            },
            "logs": {
                "stdout": str(self.stdout_log),
                "stderr": str(self.stderr_log),
            },
            "safety": {
                "gui_login_required": False,
                "application_runs_as_root": False,
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
                "shadow_daemon_gate_passed":
                    False,
                "failure": {
                    "step": "preflight",
                },
                "preflight": preflight,
            }

        sudo_ready = run(
            ["true"],
            sudo=True,
        )

        if sudo_ready.returncode != 0:
            return {
                "schema_version": "1.0",
                "shadow_daemon_gate_passed":
                    False,
                "failure": {
                    "step": "sudo credentials",
                    "message":
                        "Run sudo -v before install",
                },
                "preflight": preflight,
            }

        self.log_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.stdout_log.touch(exist_ok=True)
        self.stderr_log.touch(exist_ok=True)

        self.stdout_log.chmod(0o600)
        self.stderr_log.chmod(0o600)

        with tempfile.NamedTemporaryFile(
            prefix=f"{LABEL}.",
            suffix=".plist",
            delete=False,
        ) as stream:
            plistlib.dump(
                self.plist(),
                stream,
                sort_keys=True,
            )

            temporary_plist = Path(
                stream.name
            )

        temporary_plist.chmod(0o600)

        commands = [
            [
                "install",
                "-d",
                "-o",
                "root",
                "-g",
                "wheel",
                "-m",
                "0755",
                str(self.install_root),
            ],
            [
                "install",
                "-o",
                "root",
                "-g",
                "wheel",
                "-m",
                "0755",
                str(self.source_runner),
                str(self.installed_runner),
            ],
            [
                "install",
                "-o",
                "root",
                "-g",
                "wheel",
                "-m",
                "0644",
                str(temporary_plist),
                str(self.plist_path),
            ],
        ]

        try:
            for command in commands:
                result = run(
                    command,
                    sudo=True,
                )

                if result.returncode != 0:
                    return {
                        "schema_version": "1.0",
                        "shadow_daemon_gate_passed":
                            False,
                        "failure": {
                            "step": "install files",
                            "command": command,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        },
                    }
        finally:
            temporary_plist.unlink(
                missing_ok=True
            )

        validation = run(
            [
                "plutil",
                "-lint",
                str(self.plist_path),
            ]
        )

        if validation.returncode != 0:
            return {
                "schema_version": "1.0",
                "shadow_daemon_gate_passed":
                    False,
                "failure": {
                    "step": "validate plist",
                    "stdout": validation.stdout,
                    "stderr": validation.stderr,
                },
            }

        run(
            [
                "launchctl",
                "bootout",
                SERVICE,
            ],
            sudo=True,
        )

        bootstrap = run(
            [
                "launchctl",
                "bootstrap",
                "system",
                str(self.plist_path),
            ],
            sudo=True,
        )

        if bootstrap.returncode != 0:
            return {
                "schema_version": "1.0",
                "shadow_daemon_gate_passed":
                    False,
                "failure": {
                    "step": "launchctl bootstrap",
                    "stdout": bootstrap.stdout,
                    "stderr": bootstrap.stderr,
                },
            }

        run(
            [
                "launchctl",
                "enable",
                SERVICE,
            ],
            sudo=True,
        )

        run(
            [
                "launchctl",
                "kickstart",
                "-k",
                SERVICE,
            ],
            sudo=True,
        )

        status = self.status()

        for _ in range(40):
            if status[
                "shadow_daemon_gate_passed"
            ]:
                break

            time.sleep(0.25)
            status = self.status()

        status["preflight"] = preflight

        return status

    def uninstall(self) -> dict[str, Any]:
        sudo_ready = run(
            ["true"],
            sudo=True,
        )

        if sudo_ready.returncode != 0:
            return {
                "schema_version": "1.0",
                "uninstalled": False,
                "failure": {
                    "step": "sudo credentials",
                    "message":
                        "Run sudo -v before uninstall",
                },
            }

        run(
            [
                "launchctl",
                "bootout",
                SERVICE,
            ],
            sudo=True,
        )

        run(
            [
                "rm",
                "-f",
                str(self.plist_path),
                str(self.installed_runner),
            ],
            sudo=True,
        )

        time.sleep(1)

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
            "plist_removed":
                not self.plist_path.exists(),
            "runner_removed":
                not self.installed_runner.exists(),
            "port_released":
                listener.returncode != 0,
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
    daemon = ShadowDaemon()

    if arguments.action == "preflight":
        result = daemon.preflight()
        passed = result["passed"]
    elif arguments.action == "install":
        result = daemon.install()
        passed = result.get(
            "shadow_daemon_gate_passed",
            False,
        )
    elif arguments.action == "status":
        result = daemon.status()
        passed = result.get(
            "shadow_daemon_gate_passed",
            False,
        )
    else:
        result = daemon.uninstall()
        passed = (
            result.get("uninstalled", False)
            and result.get(
                "plist_removed",
                False,
            )
            and result.get(
                "runner_removed",
                False,
            )
            and result.get(
                "port_released",
                False,
            )
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
