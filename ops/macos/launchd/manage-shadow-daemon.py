#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Sequence


MODULE_DIRECTORY = Path(__file__).resolve().parent

if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(MODULE_DIRECTORY),
    )


from manage_shadow_daemon_canonical import (  # noqa: E402
    manager_result,
)


LEGACY_MANAGER = (
    MODULE_DIRECTORY
    / "_shadow_daemon_legacy.py"
)

CANONICAL_ACTION_MAP = {
    "canonical-preflight": "preflight",
    "canonical-plan": "plan",
    "canonical-dry-run": "dry-run",
    "canonical-apply": "apply",
}


LegacyRunner = Callable[
    [Sequence[str]],
    subprocess.CompletedProcess[Any],
]


def build_legacy_command(
    arguments: Sequence[str],
) -> list[str]:
    return [
        sys.executable,
        str(LEGACY_MANAGER),
        *arguments,
    ]


def run_legacy(
    arguments: Sequence[str],
    *,
    runner: LegacyRunner = subprocess.run,
) -> subprocess.CompletedProcess[Any]:
    if not LEGACY_MANAGER.is_file():
        raise FileNotFoundError(
            f"Legacy manager not found: {LEGACY_MANAGER}"
        )

    command = build_legacy_command(
        arguments
    )

    return runner(
        command,
        check=False,
    )


def run_canonical(
    *,
    action_token: str,
    root: Path,
    confirmation: str = "",
) -> dict[str, Any]:
    canonical_action = (
        CANONICAL_ACTION_MAP[
            action_token
        ]
    )

    return manager_result(
        action=canonical_action,
        root=root,
        confirmation=confirmation,
    )


def print_public_help() -> None:
    print(
        """usage: manage-shadow-daemon.py [-h] ACTION

AIControlCenter Shadow LaunchDaemon manager

Legacy actions:
  status                 Show current daemon status
  install                Install the legacy daemon contract
  preflight              Validate legacy installation readiness
  uninstall              Remove the legacy daemon service

Canonical actions:
  canonical-preflight    Validate canonical plist and runner
  canonical-plan         Emit the JSON installation plan
  canonical-dry-run      Compile commands without system writes
  canonical-apply        Apply with root, environment and label approval

options:
  -h, --help             Show this help message and exit
"""
    )


def canonical_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage-shadow-daemon.py",
        description=(
            "AIControlCenter Shadow LaunchDaemon "
            "canonical manager"
        ),
    )

    parser.add_argument(
        "action",
        choices=tuple(
            CANONICAL_ACTION_MAP
        ),
    )

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--confirm-label",
        default="",
    )

    return parser


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    active_arguments = list(
        sys.argv[1:]
        if arguments is None
        else arguments
    )

    if active_arguments in (
        ["-h"],
        ["--help"],
    ):
        print_public_help()
        return 0

    if (
        active_arguments
        and
        active_arguments[0]
        in CANONICAL_ACTION_MAP
    ):
        parser = canonical_parser()

        parsed = parser.parse_args(
            active_arguments
        )

        result = run_canonical(
            action_token=parsed.action,
            root=parsed.root,
            confirmation=
                parsed.confirm_label,
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

        return (
            0
            if result[
                "canonical_manager_gate_passed"
            ]
            else 1
        )

    completed = run_legacy(
        active_arguments
    )

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
