#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPOSITORY = Path.home() / "AIControlCenter"

RUNTIME_LINK = (
    Path.home()
    / "Library"
    / "Application Support"
    / "AIControlCenter"
    / "runtime"
    / "current"
)

OBSERVATION_FILE = Path(
    "/var/log/aicontrolcenter/"
    "shadow-observation.jsonl"
)

STDOUT_LOG = Path(
    "/var/log/aicontrolcenter/"
    "shadow-daemon.stdout.log"
)

STDERR_LOG = Path(
    "/var/log/aicontrolcenter/"
    "shadow-daemon.stderr.log"
)

HOST = "127.0.0.1"
PORT = 18100


def run(
    arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_value(
    *arguments: str,
) -> str:
    result = run(
        [
            "git",
            "-C",
            str(REPOSITORY),
            *arguments,
        ]
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def http_probe(
    method: str,
    path: str,
    body: bytes | None = None,
) -> tuple[int, Any]:
    request = Request(
        f"http://{HOST}:{PORT}{path}",
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(
            request,
            timeout=5,
        ) as response:
            payload = response.read().decode(
                "utf-8",
                errors="replace",
            )

            try:
                parsed: Any = json.loads(payload)
            except json.JSONDecodeError:
                parsed = payload

            return response.status, parsed

    except HTTPError as error:
        payload = error.read().decode(
            "utf-8",
            errors="replace",
        )

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = payload

        return error.code, parsed

    except URLError as error:
        return 0, {
            "error": str(error.reason),
        }


def listener_pid() -> int | None:
    result = run(
        [
            "lsof",
            "-nP",
            f"-iTCP:{PORT}",
            "-sTCP:LISTEN",
            "-t",
        ]
    )

    if result.returncode != 0:
        return None

    first = result.stdout.strip().splitlines()

    if not first:
        return None

    try:
        return int(first[0])
    except ValueError:
        return None


def listener_addresses() -> list[str]:
    result = run(
        [
            "lsof",
            "-nP",
            f"-iTCP:{PORT}",
            "-sTCP:LISTEN",
            "-Fn",
        ]
    )

    addresses: list[str] = []

    for line in result.stdout.splitlines():
        if line.startswith("n"):
            addresses.append(line[1:])

    return sorted(set(addresses))


def process_metrics(
    pid: int | None,
) -> dict[str, Any]:
    if pid is None:
        return {
            "pid": None,
            "user": "",
            "cpu_percent": None,
            "rss_kb": None,
            "elapsed": "",
        }

    result = run(
        [
            "ps",
            "-p",
            str(pid),
            "-o",
            "user=",
            "-o",
            "%cpu=",
            "-o",
            "rss=",
            "-o",
            "etime=",
        ]
    )

    values = result.stdout.strip().split()

    if len(values) < 4:
        return {
            "pid": pid,
            "user": "",
            "cpu_percent": None,
            "rss_kb": None,
            "elapsed": "",
        }

    try:
        cpu_percent = float(values[1])
    except ValueError:
        cpu_percent = None

    try:
        rss_kb = int(values[2])
    except ValueError:
        rss_kb = None

    return {
        "pid": pid,
        "user": values[0],
        "cpu_percent": cpu_percent,
        "rss_kb": rss_kb,
        "elapsed": values[3],
    }


def file_size(
    path: Path,
) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def main() -> int:
    generated_at = datetime.now(
        timezone.utc
    ).replace(
        microsecond=0
    ).isoformat()

    commit = git_value(
        "rev-parse",
        "HEAD",
    )

    short_commit = git_value(
        "rev-parse",
        "--short=12",
        "HEAD",
    )

    git_clean = (
        git_value(
            "status",
            "--porcelain",
        )
        == ""
    )

    try:
        runtime = RUNTIME_LINK.resolve(
            strict=True
        )
        runtime_name = runtime.name
    except OSError:
        runtime = Path("")
        runtime_name = ""

    health_code, health_body = http_probe(
        "GET",
        "/health",
    )

    write_code, write_body = http_probe(
        "POST",
        "/__shadow_write_probe__",
        b'{"write":true}',
    )

    pid = listener_pid()
    addresses = listener_addresses()
    process = process_metrics(pid)

    expected_address = f"{HOST}:{PORT}"

    listener_local_only = (
        addresses == [expected_address]
    )

    runtime_matches_commit = (
        runtime_name == short_commit
        and short_commit != ""
    )

    observation_gate = all(
        (
            git_clean,
            runtime_matches_commit,
            health_code == 200,
            write_code == 405,
            listener_local_only,
            process["user"] == "kyouhan",
        )
    )

    record = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "observation_gate_passed":
            observation_gate,

        "checks": {
            "git_clean": git_clean,
            "runtime_matches_commit":
                runtime_matches_commit,
            "health_http_200":
                health_code == 200,
            "mutating_requests_blocked":
                write_code == 405,
            "listener_local_only":
                listener_local_only,
            "process_user_non_root": (
                process["user"] == "kyouhan"
                and
                process["user"] != "root"
            ),
        },

        "repository": {
            "commit": commit,
        },

        "runtime": {
            "current": (
                str(runtime)
                if runtime_name
                else ""
            ),
            "commit": runtime_name,
        },

        "process": process,

        "endpoint": {
            "host": HOST,
            "port": PORT,
            "listener_addresses": addresses,
            "health_code": health_code,
            "health_response": health_body,
            "write_probe_code": write_code,
            "write_probe_response": write_body,
        },

        "logs": {
            "stdout_bytes":
                file_size(STDOUT_LOG),
            "stderr_bytes":
                file_size(STDERR_LOG),
        },
    }

    OBSERVATION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OBSERVATION_FILE.open(
        "a",
        encoding="utf-8",
    ) as output:
        fcntl.flock(
            output.fileno(),
            fcntl.LOCK_EX,
        )

        output.write(
            json.dumps(
                record,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )

        output.flush()
        os.fsync(output.fileno())

        fcntl.flock(
            output.fileno(),
            fcntl.LOCK_UN,
        )

    print(
        json.dumps(
            record,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0 if observation_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
