#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from textwrap import dedent


START = (
    "<!-- "
    "AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START "
    "-->"
)

END = (
    "<!-- "
    "AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:END "
    "-->"
)


def upsert(
    path: Path,
    content: str,
) -> bool:
    if not path.exists():
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            f"# {path.stem}\n",
            encoding="utf-8",
        )

    original = path.read_text(
        encoding="utf-8"
    )

    block = (
        f"{START}\n"
        f"{content.strip()}\n"
        f"{END}\n"
    )

    if START in original and END in original:
        before, remainder = original.split(
            START,
            1,
        )

        _, after = remainder.split(
            END,
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
        required=True,
    )

    parser.add_argument(
        "--recovery-report",
        required=True,
    )

    arguments = parser.parse_args()

    root = Path(arguments.root).resolve()
    report_path = Path(
        arguments.recovery_report
    ).resolve()

    report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    if report.get(
        "headless_reboot_recovery_gate_passed"
    ) is not True:
        raise RuntimeError(
            "Headless reboot recovery Gate is false"
        )

    generated_at = datetime.now(
        timezone.utc
    ).replace(
        microsecond=0
    ).isoformat()

    process = report["process"]
    repository = report["repository"]
    runtime = report["runtime"]
    endpoint = report["endpoint"]

    common = (
        f"- Verified: `{generated_at}`\n"
        f"- Commit: "
        f"`{repository['current_commit']}`\n"
        f"- Runtime: `{runtime['current']}`\n"
        f"- Pre-reboot PID: "
        f"`{process['pre_reboot_pid']}`\n"
        f"- Post-reboot PID: "
        f"`{process['post_reboot_pid']}`\n"
        f"- Process user: `{process['user']}`\n"
        f"- Health HTTP: "
        f"`{endpoint['health_code']}`\n"
        f"- Write probe HTTP: "
        f"`{endpoint['write_probe_code']}`"
    )

    documents = {
        "README.md": dedent(
            f"""
            ## Mac Headless Control Plane Status

            The AIControlCenter Shadow API recovered
            automatically after a full system reboot
            without requiring a GUI login.

            - Supervisor:
              `system/com.aicontrolcenter.api.shadow`
            - Listener: `127.0.0.1:18100`
            - Mode: `shadow-read-only`
            - Headless reboot recovery: `passed`
            - Ubuntu production cutover: `not started`

            {common}
            """
        ),

        "ARCHITECTURE.md": dedent(
            f"""
            ## ADR: Headless LaunchDaemon Recovery

            **Status:** Accepted and operationally verified.

            AIControlCenter uses a system LaunchDaemon
            as its Mac Control Plane supervisor.

            The plist and runner are root-owned, while
            the application process runs as `kyouhan`.

            Runtime startup does not depend on:

            - a GUI login
            - GitHub availability
            - an SSH agent
            - the Ubuntu Worker

            Operational logs use:

            `/var/log/aicontrolcenter`

            The API remains localhost-only and blocks
            mutating HTTP requests during Shadow Mode.

            Infrastructure-as-Code reconciliation of
            the manager installer remains required.

            {common}
            """
        ),

        "MASTER.md": dedent(
            f"""
            ## Mac Control Plane Milestone

            ### Completed

            - Non-root system LaunchDaemon
            - Automatic process restart
            - Localhost-only Shadow API
            - Health and write-protection contracts
            - GUI-independent reboot recovery
            - Commit-specific Runtime recovery

            ### Current Production Gate

            Reconcile the repository installer with the
            canonical plist, then complete the 24-hour
            Shadow observation.

            Ubuntu remains the active infrastructure and
            fallback platform until cutover approval.

            {common}
            """
        ),

        "ROADMAP.md": dedent(
            f"""
            ## Mac Control Plane Roadmap Update

            - [x] Non-root LaunchDaemon
            - [x] Automatic restart
            - [x] Headless reboot recovery
            - [x] Health HTTP 200
            - [x] Write protection HTTP 405
            - [x] Localhost-only listener
            - [ ] Reconcile manager installer with plist
            - [ ] Complete 24-hour Shadow observation
            - [ ] Validate Ubuntu Worker JSON APIs
            - [ ] Complete cutover and rollback runbooks

            {common}
            """
        ),

        "CHANGELOG.md": dedent(
            f"""
            ## Unreleased — Headless Recovery

            ### Added

            - GUI-independent system LaunchDaemon recovery
            - Headless reboot recovery JSON Gate
            - System log path:
              `/var/log/aicontrolcenter`

            ### Fixed

            - Replaced GUI-dependent supervision
            - Recovered from launchd bootstrap error 5
            - Verified non-root process ownership
            - Verified Runtime and Git commit alignment

            ### Pending

            - Manager installer reconciliation
            - 24-hour Shadow observation
            - Production cutover decision

            {common}
            """
        ),

        "PROJECT_HISTORY.md": dedent(
            f"""
            ## {generated_at[:10]} — Headless Recovery

            The Mac Control Plane recovered its read-only
            AIControlCenter API following a full reboot
            without a GUI login.

            The recovered service retained:

            - non-root application execution
            - commit-specific Runtime selection
            - localhost-only networking
            - read-only Shadow enforcement
            - system LaunchDaemon supervision

            {common}
            """
        ),

        "TODO.md": dedent(
            f"""
            ## Next Production Tasks

            ### P0

            - [ ] Update `manage-shadow-daemon.py`
              to reproduce the canonical plist
            - [ ] Add installer regression tests
            - [ ] Begin 24-hour Shadow observation
            - [ ] Validate log rotation and growth limits

            ### P1

            - [ ] Connect Ubuntu Worker JSON APIs read-only
            - [ ] Validate Dashboard Shadow integration
            - [ ] Complete cutover runbook
            - [ ] Complete rollback runbook
            - [ ] Update Notion project status

            {common}
            """
        ),

        (
            "docs/operations/macos/"
            "LAUNCHD-SHADOW-DAEMON.md"
        ): dedent(
            f"""
            ## Headless Reboot Recovery

            The system LaunchDaemon successfully recovered
            after a full reboot without a GUI login.

            ### Lifecycle

            - `bootstrap` registers an unloaded service.
            - `kickstart` restarts a loaded service.
            - `bootout` removes the service registration.
            - Port `18100` must be open during operation.
            - Port `18100` must be released after bootout.

            ### Canonical Runtime

            - Service:
              `system/com.aicontrolcenter.api.shadow`
            - Application user: `kyouhan`
            - Listener: `127.0.0.1:18100`
            - Log directory:
              `/var/log/aicontrolcenter`
            - Allowed methods:
              `GET`, `HEAD`, `OPTIONS`
            - Mutating methods: blocked

            {common}
            """
        ),
    }

    changed: list[str] = []

    for relative_path, content in documents.items():
        if upsert(
            root / relative_path,
            content,
        ):
            changed.append(relative_path)

    result = {
        "schema_version": "1.0",
        "documentation_update_passed": True,
        "generated_at": generated_at,
        "source_report": str(report_path),
        "changed_files": changed,
        "document_count": len(documents),
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
