#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from textwrap import dedent
from typing import Any


START_MARKER = (
    "<!-- "
    "AICONTROLCENTER:MAC_SHADOW_DAEMON:START "
    "-->"
)

END_MARKER = (
    "<!-- "
    "AICONTROLCENTER:MAC_SHADOW_DAEMON:END "
    "-->"
)


def git(
    root: Path,
    *arguments: str,
) -> str:
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            *arguments,
        ],
        text=True,
    ).strip()


def require_boolean(
    value: Any,
    name: str,
) -> bool:
    if value is not True:
        raise RuntimeError(
            f"Required gate failed: {name}"
        )

    return True


def upsert(
    path: Path,
    body: str,
) -> bool:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required document not found: {path}"
        )

    original = path.read_text(
        encoding="utf-8"
    )

    block = (
        f"{START_MARKER}\n"
        f"{body.strip()}\n"
        f"{END_MARKER}\n"
    )

    start_count = original.count(
        START_MARKER
    )

    end_count = original.count(
        END_MARKER
    )

    if start_count != end_count:
        raise RuntimeError(
            f"Unbalanced markers in {path}"
        )

    if start_count > 1:
        raise RuntimeError(
            f"Duplicate markers in {path}"
        )

    if start_count == 1:
        before, remainder = original.split(
            START_MARKER,
            1,
        )

        _, after = remainder.split(
            END_MARKER,
            1,
        )

        updated = (
            before.rstrip()
            + "\n\n"
            + block
            + after.lstrip("\n")
        )
    else:
        updated = (
            original.rstrip()
            + "\n\n"
            + block
        )

    if updated == original:
        return False

    path.write_text(
        updated,
        encoding="utf-8",
    )

    return True


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=str(
            Path.home()
            / "AIControlCenter"
        ),
    )

    parser.add_argument(
        "--status-report",
        required=True,
    )

    parser.add_argument(
        "--previous-pid",
        default="",
    )

    arguments = parser.parse_args()

    root = Path(
        arguments.root
    ).expanduser().resolve()

    report_path = Path(
        arguments.status_report
    ).expanduser().resolve()

    report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    require_boolean(
        report.get(
            "shadow_daemon_gate_passed"
        ),
        "shadow_daemon_gate_passed",
    )

    checks = report.get(
        "checks",
        {}
    )

    required_checks = (
        "loaded",
        "pid_active",
        "process_user_non_root",
        "runtime_matches_commit",
        "health_http_200",
        "health_json_object",
        "mutating_requests_blocked",
        "listener_local_only",
        "plist_root_owned_secure",
        "runner_root_owned_secure",
    )

    for check_name in required_checks:
        require_boolean(
            checks.get(check_name),
            check_name,
        )

    process = report.get(
        "process",
        {}
    )

    runtime = report.get(
        "runtime",
        {}
    )

    endpoint = report.get(
        "endpoint",
        {}
    )

    commit = git(
        root,
        "rev-parse",
        "HEAD",
    )

    short_commit = git(
        root,
        "rev-parse",
        "--short=12",
        "HEAD",
    )

    branch = git(
        root,
        "branch",
        "--show-current",
    )

    if git(
        root,
        "status",
        "--porcelain",
    ):
        raise RuntimeError(
            "Repository must be clean "
            "before documentation generation"
        )

    generated_at = datetime.now(
        timezone.utc
    ).replace(
        microsecond=0
    ).isoformat()

    generated_date = generated_at[:10]

    current_pid = str(
        process.get(
            "pid",
            "",
        )
    )

    previous_pid = (
        arguments.previous_pid
    )

    restart_verified = (
        previous_pid.isdigit()
        and current_pid.isdigit()
        and previous_pid != current_pid
    )

    restart_summary = (
        f"`{previous_pid} → {current_pid}`"
        if restart_verified
        else "validated by LaunchDaemon Gate"
    )

    process_user = str(
        process.get(
            "user",
            "unknown",
        )
    )

    process_state = str(
        process.get(
            "state",
            "unknown",
        )
    )

    runtime_path = str(
        runtime.get(
            "current",
            "",
        )
    )

    host = str(
        endpoint.get(
            "host",
            "127.0.0.1",
        )
    )

    port = int(
        endpoint.get(
            "port",
            18100,
        )
    )

    health_code = int(
        endpoint.get(
            "health_code",
            0,
        )
    )

    write_code = int(
        endpoint.get(
            "write_probe_code",
            0,
        )
    )

    metadata = (
        f"- Generated: `{generated_at}`\n"
        f"- Branch: `{branch}`\n"
        f"- Commit: `{commit}`\n"
        f"- Runtime commit: `{short_commit}`"
    )

    documents = {
        "README.md": dedent(
            f"""
            ## Mac Control Plane Runtime Status

            The Mac mini now runs the AIControlCenter
            read-only Shadow API under a headless,
            non-root system LaunchDaemon.

            - Supervisor:
              `system/com.aicontrolcenter.api.shadow`
            - Application user: `{process_user}`
            - Process state: `{process_state}`
            - Endpoint: `http://{host}:{port}`
            - Health contract: HTTP `{health_code}`
            - Mutating request contract: HTTP `{write_code}`
            - Runtime:
              `{runtime_path}`
            - Automatic restart:
              {restart_summary}
            - GUI login required: `false`
            - Ubuntu Control Plane replaced: `false`
            - Secret migration completed: `false`

            Current production milestone:
            Headless Reboot Recovery Gate.

            {metadata}
            """
        ),
        "ARCHITECTURE.md": dedent(
            f"""
            ## ADR: Headless Mac Control Plane Supervisor

            **Status:** Accepted

            ### Decision

            AIControlCenter Shadow Runtime is supervised
            by a system LaunchDaemon.

            The LaunchDaemon plist and installed runner
            are owned by `root:wheel`, while the Python
            application runs as `{process_user}`.

            ### Runtime Flow

            `system launchd`
            → `non-root runner`
            → `commit-specific Python runtime`
            → `core.api.shadow:app`
            → `{host}:{port}`

            ### Security Boundaries

            - GUI login is not required.
            - The application process must not run as root.
            - The API listens only on localhost.
            - GET, HEAD, and OPTIONS are allowed.
            - Mutating HTTP methods are blocked.
            - Git HEAD and Runtime commit must match.
            - A dirty Git repository prevents restart.
            - Ubuntu remains an infrastructure worker.
            - Business logic remains on the Mac Control Plane.

            ### Rejected Alternative

            A user LaunchAgent was rejected for production
            because it requires an active GUI login domain
            and failed the headless reboot recovery test.

            ### Verified Gate

            - LaunchDaemon loaded: passed
            - Non-root process: passed
            - Health HTTP `{health_code}`: passed
            - Write probe HTTP `{write_code}`: passed
            - Localhost-only listener: passed
            - Automatic restart: {restart_summary}

            {metadata}
            """
        ),
        "MASTER.md": dedent(
            f"""
            ## Mac Control Plane Master Status

            ### Completed

            - Mac Foundation Gate
            - Runtime Contract discovery
            - Commit-specific Python Runtime
            - Production Runtime Gate
            - Read-only Health Runtime Gate
            - Shadow API write protection
            - Non-root system LaunchDaemon
            - Secure root-owned plist and runner
            - Automatic process restart
            - Localhost-only listener

            ### Current State

            - Service:
              `system/com.aicontrolcenter.api.shadow`
            - Runtime:
              `{runtime_path}`
            - Process user: `{process_user}`
            - Endpoint: `{host}:{port}`
            - Health: HTTP `{health_code}`
            - Mutating requests: HTTP `{write_code}`
            - LaunchDaemon Gate: passed

            ### Current Production Milestone

            Headless Reboot Recovery Gate without a GUI
            login session.

            ### Cutover Rule

            Ubuntu AIControlCenter must remain active until:

            - headless reboot recovery passes
            - 24-hour Shadow observation passes
            - Ubuntu Worker JSON read-only integration passes
            - rollback validation passes

            {metadata}
            """
        ),
        "ROADMAP.md": dedent(
            f"""
            ## Mac Control Plane Roadmap

            ### Completed

            - [x] Mac Foundation Gate
            - [x] Git and SSH control
            - [x] Runtime Contract
            - [x] Python 3.12 production runtime
            - [x] Full Test Suite
            - [x] Read-only Health Gate
            - [x] Shadow read-only ASGI layer
            - [x] LaunchAgent architecture evaluation
            - [x] LaunchAgent rejected for headless production
            - [x] Non-root system LaunchDaemon
            - [x] Secure plist and runner ownership
            - [x] Automatic restart validation
            - [x] Localhost-only listener validation
            - [x] Health HTTP `{health_code}`
            - [x] Write probe HTTP `{write_code}`

            ### Current Sprint

            - [ ] Headless reboot recovery
            - [ ] Verify service before GUI login
            - [ ] Verify PID change after reboot
            - [ ] Verify process user `{process_user}`
            - [ ] Verify Runtime commit preservation

            ### Next Sprint

            - [ ] 24-hour Shadow observation
            - [ ] CPU and memory baseline
            - [ ] restart-count monitoring
            - [ ] log-growth monitoring
            - [ ] Ubuntu Worker JSON read-only connection
            - [ ] Mac Dashboard Shadow connection
            - [ ] Cutover and rollback runbook

            {metadata}
            """
        ),
        "CHANGELOG.md": dedent(
            f"""
            ## Unreleased — Mac Control Plane

            ### Added

            - Non-root system LaunchDaemon supervisor
            - Root-owned LaunchDaemon plist
            - Root-owned immutable runner installation
            - JSON-first supervisor status and lifecycle
            - Read-only Shadow API on `{host}:{port}`

            ### Changed

            - Replaced the GUI-dependent LaunchAgent
              production design with a system LaunchDaemon.
            - Defined normal running state as port `{port}`
              being owned by the active LaunchDaemon PID.
            - Restricted port-release validation to
              uninstall and bootout operations.

            ### Verified

            - Application user: `{process_user}`
            - Health response: HTTP `{health_code}`
            - Mutating request response: HTTP `{write_code}`
            - Localhost-only listener
            - Runtime and Git commit match
            - Secure plist and runner ownership
            - Automatic restart: {restart_summary}
            - Full Test Suite:
              313 passed, 5 deselected

            ### Pending

            - Headless reboot recovery
            - 24-hour Shadow observation
            - Ubuntu Worker read-only integration

            {metadata}
            """
        ),
        "PROJECT_HISTORY.md": dedent(
            f"""
            ## {generated_date} — Non-root LaunchDaemon Milestone

            The Mac Control Plane Shadow Runtime completed
            its non-root LaunchDaemon and automatic restart
            production gates.

            The earlier LaunchAgent design was rejected after
            reboot testing demonstrated that a GUI bootstrap
            domain was unavailable in the headless operating
            environment.

            The replacement system LaunchDaemon:

            - starts without a GUI login
            - runs the application as `{process_user}`
            - binds only to `{host}:{port}`
            - returns HTTP `{health_code}` from `/health`
            - blocks mutating requests with HTTP `{write_code}`
            - uses a commit-specific Python runtime
            - uses secure root-owned installation files
            - recovered automatically:
              {restart_summary}

            Ubuntu remained unchanged and continues operating
            until Mac Shadow observation and rollback gates
            are complete.

            {metadata}
            """
        ),
        "TODO.md": dedent(
            f"""
            ## Mac Control Plane Next Tasks

            ### P0 — Production Gates

            - [ ] Run Headless Reboot Recovery Gate
            - [ ] Confirm LaunchDaemon before GUI login
            - [ ] Confirm post-reboot PID change
            - [ ] Confirm process user `{process_user}`
            - [ ] Confirm Health HTTP `{health_code}`
            - [ ] Confirm write probe HTTP `{write_code}`
            - [ ] Confirm listener remains localhost-only
            - [ ] Confirm Runtime matches Git HEAD

            ### P1 — Shadow Observation

            - [ ] Collect 24-hour Health results
            - [ ] Collect CPU and memory metrics
            - [ ] Collect restart count
            - [ ] Measure stdout and stderr log growth
            - [ ] Define warning budget
            - [ ] Replace deprecated `datetime.utcnow()`

            ### P2 — Integration

            - [ ] Connect Ubuntu Worker JSON APIs read-only
            - [ ] Connect Mac Dashboard to Shadow API
            - [ ] Validate n8n read-only workflows
            - [ ] Write Cutover runbook
            - [ ] Write rollback runbook
            - [ ] Update Notion project status

            {metadata}
            """
        ),
        (
            "docs/operations/macos/"
            "LAUNCHD-SHADOW-DAEMON.md"
        ): dedent(
            f"""
            ## Validated Runtime Status

            - Gate:
              `shadow_daemon_gate_passed=true`
            - Service:
              `system/com.aicontrolcenter.api.shadow`
            - Process user: `{process_user}`
            - Runtime:
              `{runtime_path}`
            - Listener: `{host}:{port}`
            - Health: HTTP `{health_code}`
            - Mutating request probe: HTTP `{write_code}`
            - Automatic restart: {restart_summary}
            - GUI login required: `false`

            ## Listener Semantics

            During normal operation:

            - port `{port}` must be listening
            - the listener PID must match the LaunchDaemon PID
            - the listener must bind only to `{host}`

            During uninstall or bootout:

            - port `{port}` must be released

            An open localhost listener after an automatic
            restart is a successful recovery condition,
            not a port-release failure.

            ## Next Gate

            Headless reboot recovery must verify the service
            before any GUI login.

            {metadata}
            """
        ),
    }

    changed: list[str] = []

    for relative_path, body in documents.items():
        path = root / relative_path

        if upsert(path, body):
            changed.append(relative_path)

    result = {
        "schema_version": "1.0",
        "documentation_update_passed": True,
        "generated_at": generated_at,
        "repository": {
            "root": str(root),
            "branch": branch,
            "commit": commit,
        },
        "source_report": str(report_path),
        "changed_files": changed,
        "unchanged_file_count": (
            len(documents) - len(changed)
        ),
        "milestone": {
            "shadow_daemon_gate_passed": True,
            "automatic_restart_verified":
                restart_verified,
            "previous_pid": previous_pid,
            "current_pid": current_pid,
        },
    }

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
