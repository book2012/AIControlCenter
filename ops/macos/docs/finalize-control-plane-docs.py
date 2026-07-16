#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


BASELINE_MARKER = (
    "AICONTROLCENTER:CONTROL_PLANE_BASELINE"
)

LEGACY_MARKERS = (
    "AICONTROLCENTER:MAC_SHADOW_DAEMON",
    "AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY",
    "AICONTROLCENTER:SHADOW_OBSERVATION",
)


def marker_block(
    marker: str,
    body: str,
) -> str:
    return (
        f"<!-- {marker}:START -->\n"
        f"{body.strip()}\n"
        f"<!-- {marker}:END -->"
    )


def remove_marker(
    text: str,
    marker: str,
) -> str:
    pattern = re.compile(
        rf"\n?<!-- {re.escape(marker)}:START -->"
        rf".*?"
        rf"<!-- {re.escape(marker)}:END -->\n?",
        flags=re.DOTALL,
    )

    return pattern.sub(
        "\n",
        text,
    )


def replace_or_append(
    path: Path,
    marker: str,
    body: str,
    *,
    remove_legacy: bool = False,
    after_heading: bool = False,
) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    if remove_legacy:
        for legacy in LEGACY_MARKERS:
            text = remove_marker(
                text,
                legacy,
            )

    text = remove_marker(
        text,
        marker,
    ).rstrip()

    block = marker_block(
        marker,
        body,
    )

    if after_heading:
        lines = text.splitlines()

        if (
            lines
            and
            lines[0].startswith("# ")
        ):
            text = "\n".join(
                [
                    lines[0],
                    "",
                    block,
                    "",
                    *lines[1:],
                ]
            ).rstrip()
        else:
            text = (
                f"{block}\n\n{text}"
            )
    else:
        text = (
            f"{text}\n\n{block}"
        )

    path.write_text(
        normalize_markdown(text),
        encoding="utf-8",
    )



def normalize_markdown(
    text: str,
) -> str:
    text = text.replace(
        "\r\n",
        "\n",
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip() + "\n"

def required(
    payload: dict[str, Any],
    *keys: str,
) -> Any:
    value: Any = payload

    for key in keys:
        value = value[key]

    return value


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--facts",
        type=Path,
        required=True,
    )

    arguments = parser.parse_args()

    root = arguments.root.resolve()

    facts = json.loads(
        arguments.facts.read_text(
            encoding="utf-8",
        )
    )

    if not facts.get(
        "control_plane_documentation_ready"
    ):
        raise SystemExit(
            "Control Plane documentation Gate is false"
        )

    commit = required(
        facts,
        "repository",
        "commit",
    )

    short_commit = required(
        facts,
        "repository",
        "short_commit",
    )

    runtime = required(
        facts,
        "runtime",
        "current",
    )

    observation = facts["observation"]
    launchd = facts["launchd"]
    endpoint = facts["endpoint"]

    duration = observation[
        "duration_hours"
    ]

    total = observation[
        "total_samples"
    ]

    passed = observation[
        "passed_samples"
    ]

    failed = observation[
        "failed_samples"
    ]

    ratio = observation[
        "success_ratio"
    ]

    pid_transitions = observation[
        "pid_transitions"
    ]

    observation_sha = observation[
        "archive_sha256"
    ]

    summary_sha = observation[
        "summary_sha256"
    ]

    before_pid = launchd[
        "before_pid"
    ]

    after_pid = launchd[
        "after_pid"
    ]

    health_code = endpoint[
        "health_code"
    ]

    write_code = endpoint[
        "write_probe_code"
    ]

    listener = endpoint[
        "listener_addresses"
    ][0]
    readme = f"""
## Mac Control Plane Production Baseline

The Mac mini M4 is the always-on Brain and the
single AIControlCenter Control Plane.

Current validated baseline:

- Branch: `sprint/mac-control-plane-foundation`
- Commit: `{commit}`
- Runtime commit: `{short_commit}`
- Runtime: `{runtime}`
- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Listener: `{listener}`
- Health contract: HTTP `{health_code}`
- Mutating request contract: HTTP `{write_code}`
- Mode: `shadow-read-only`
- GUI login required: `false`
- Transactional canonical apply: implemented
- Transactional rollback: implemented
- launchd bootout settle policy: 2 seconds
- Final restart: `{before_pid} → {after_pid}`

Shadow observation:

- Duration: `{duration}` hours
- Samples: `{passed}/{total}` passed
- Failed samples: `{failed}`
- Success ratio: `{ratio:.1%}`
- PID transitions: `{pid_transitions}`
- Observation SHA-256:
  `{observation_sha}`
- Summary SHA-256:
  `{summary_sha}`

Control Plane implementation is complete.
Production write cutover remains blocked pending
an explicit Production approval.
"""

    architecture = f"""
## ADR: Mac Control Plane Production Baseline

**Status:** Accepted and operationally verified.

The Mac mini M4 is the sole AIControlCenter
Control Plane.

Ubuntu remains a stateless infrastructure worker.

Runtime flow:

`system launchd`
→ `root-owned runner`
→ `non-root application user`
→ `commit-specific Python runtime`
→ `AIControlCenter Shadow API`
→ `{listener}`

Validated contracts:

- Repository commit: `{commit}`
- Runtime commit: `{short_commit}`
- Health: HTTP `{health_code}`
- Write protection: HTTP `{write_code}`
- Listener: `{listener}`
- GUI login dependency: none
- Transactional install: enabled
- Transactional rollback: enabled
- launchd settle after bootout: 2 seconds
- Final restart PID: `{before_pid} → {after_pid}`

Ownership boundaries:

- Mac owns AI, orchestration, business logic,
  scheduling, workflow and application state.
- Ubuntu owns Docker, storage, backup and file
  operations only.
- Ubuntu must not own AI workloads, business
  logic, Control Plane orchestration or
  application state.
- Infrastructure is consumed through JSON APIs.
- Production writes remain disabled until a
  separate cutover Gate is approved.
"""

    detailed_architecture = f"""
## Mac Control Plane Runtime

Mac mini M4

- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Runner ownership: `root:wheel`
- Application user: `kyouhan`
- Runtime commit: `{short_commit}`
- Runtime path: `{runtime}`
- Endpoint: `{listener}`
- Mode: `shadow-read-only`

Operational contracts:

- Repository commit:
  `{commit}`
- Health: HTTP `{health_code}`
- Mutating methods: HTTP `{write_code}`
- Automatic restart:
  `{before_pid} → {after_pid}`
- Transactional canonical apply: enabled
- Transactional rollback: enabled
- launchd bootout settle interval: 2 seconds

Ubuntu remains an optional stateless worker and
does not own AIControlCenter business logic or
application state.
"""

    master = f"""
## Mac Control Plane Baseline

Status: **Implementation Complete**

- Final commit: `{commit}`
- Runtime commit: `{short_commit}`
- Service:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Health: HTTP `{health_code}`
- Write protection: HTTP `{write_code}`
- Listener: `{listener}`
- Final restart: `{before_pid} → {after_pid}`
- Observation:
  `{passed}/{total}` successful samples
- Observation duration:
  `{duration}` hours
- Transactional apply: complete
- Transactional rollback: complete
- Production write cutover: not approved

Next program milestone:

AIControlCenter Platform Integration using the
completed Mac Control Plane baseline.
"""

    roadmap = """
## Mac Control Plane Foundation

Status: **Complete**

- [x] Commit-specific Runtime
- [x] Non-root system LaunchDaemon
- [x] Headless reboot recovery
- [x] Read-only Shadow API
- [x] Localhost-only listener
- [x] 24-hour observation
- [x] Canonical installation manager
- [x] Transactional apply
- [x] Transactional rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout

### Next Program Phase

- [ ] AIControlCenter REST API consolidation
- [ ] Dashboard integration
- [ ] Homepage integration
- [ ] Ubuntu Worker read-only JSON APIs
- [ ] n8n read-only workflows
- [ ] Production cutover design and approval
"""

    changelog = f"""
## 2026-07-16 — Mac Control Plane Baseline

### Added

- Commit-specific Mac Runtime
- Non-root system LaunchDaemon
- Canonical launchd manager and executor
- Transactional canonical apply
- Transactional rollback
- launchd bootout settle policy
- Restart and recovery validation
- Read-only Shadow API monitoring

### Validation

- Final commit: `{commit}`
- Runtime: `{short_commit}`
- Observation:
  `{passed}/{total}` samples passed
- Observation duration:
  `{duration}` hours
- Health: HTTP `{health_code}`
- Write protection: HTTP `{write_code}`
- Listener: `{listener}`
- Final restart:
  `{before_pid} → {after_pid}`

### Safety

- AIControlCenter runs as `kyouhan`.
- Installed plist and runner remain root-owned.
- The API remains localhost-only.
- Mutating requests remain blocked.
- Production write cutover remains disabled.
"""

    history = f"""
## 2026-07-16 — Mac Control Plane Completed

The Mac mini M4 Control Plane completed its
foundation and operational validation program.

Milestones:

- Headless system LaunchDaemon recovery
- Non-root AIControlCenter execution
- Commit-specific Runtime enforcement
- `{duration}`-hour Shadow observation
- `{passed}/{total}` successful observations
- Canonical manager reconciliation
- Transactional apply and rollback
- launchd settle policy
- Final canonical apply
- Final restart:
  `{before_pid} → {after_pid}`
- Health HTTP `{health_code}`
- Write protection HTTP `{write_code}`
- Localhost-only listener `{listener}`

The Control Plane implementation is complete.
Ubuntu remains a stateless infrastructure worker.
Production write cutover is intentionally deferred.
"""

    todo = """
## Mac Control Plane

Status: **Complete**

- [x] Headless reboot recovery
- [x] 24-hour Shadow observation
- [x] Canonical manager reconciliation
- [x] Transactional apply and rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout

## Next Sprint — AIControlCenter Platform

### P0

- [ ] Consolidate AIControlCenter REST contracts
- [ ] Connect Dashboard to the Mac Control Plane
- [ ] Connect Homepage to Dashboard APIs
- [ ] Define Ubuntu Worker read-only JSON APIs
- [ ] Add Worker health monitoring
- [ ] Add Backup Verify monitoring

### P1

- [ ] Connect n8n read-only workflows
- [ ] Add Notion project synchronization
- [ ] Define Production write approval Gate
- [ ] Define Production cutover and rollback runbooks

Production writes remain disabled until monitoring
and validation are stable.
"""
    replace_or_append(
        root / "README.md",
        BASELINE_MARKER,
        readme,
        remove_legacy=True,
    )

    replace_or_append(
        root / "ARCHITECTURE.md",
        BASELINE_MARKER,
        architecture,
        remove_legacy=True,
    )

    replace_or_append(
        root / "docs/ARCHITECTURE.md",
        BASELINE_MARKER,
        detailed_architecture,
    )

    replace_or_append(
        root / "MASTER.md",
        BASELINE_MARKER,
        master,
        remove_legacy=True,
    )

    replace_or_append(
        root / "ROADMAP.md",
        BASELINE_MARKER,
        roadmap,
    )

    replace_or_append(
        root / "CHANGELOG.md",
        BASELINE_MARKER,
        changelog,
        after_heading=True,
    )

    replace_or_append(
        root / "PROJECT_HISTORY.md",
        BASELINE_MARKER,
        history,
    )

    replace_or_append(
        root / "TODO.md",
        BASELINE_MARKER,
        todo,
        remove_legacy=True,
    )

    print(
        json.dumps(
            {
                "documentation_updated":
                    True,
                "files": [
                    "README.md",
                    "ARCHITECTURE.md",
                    "docs/ARCHITECTURE.md",
                    "MASTER.md",
                    "ROADMAP.md",
                    "CHANGELOG.md",
                    "PROJECT_HISTORY.md",
                    "TODO.md",
                ],
                "commit":
                    commit,
                "runtime":
                    runtime,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
