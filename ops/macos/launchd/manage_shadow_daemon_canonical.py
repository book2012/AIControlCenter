#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


MODULE_DIRECTORY = Path(__file__).resolve().parent

if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(MODULE_DIRECTORY),
    )


from canonical_shadow_daemon import (  # noqa: E402
    build_install_plan,
    validate_contract,
)

from canonical_shadow_daemon_executor import (  # noqa: E402
    execute,
)


SCHEMA_VERSION = "1.0"


def manager_result(
    *,
    action: str,
    root: Path,
    confirmation: str = "",
) -> dict[str, Any]:
    resolved_root = root.resolve()

    if action == "preflight":
        payload = validate_contract(
            resolved_root
        )

        gate = payload[
            "canonical_launchd_contract_gate_passed"
        ]

        return {
            "schema_version":
                SCHEMA_VERSION,
            "action":
                action,
            "canonical_manager_gate_passed":
                gate,
            "write_operations_executed":
                False,
            "contract":
                payload,
            "next_action": (
                "Generate canonical install plan"
                if gate
                else
                "Fix canonical contract"
            ),
        }

    if action == "plan":
        payload = build_install_plan(
            resolved_root
        )

        gate = payload[
            "canonical_launchd_contract_gate_passed"
        ]

        return {
            "schema_version":
                SCHEMA_VERSION,
            "action":
                action,
            "canonical_manager_gate_passed":
                gate,
            "write_operations_executed":
                False,
            "plan":
                payload,
            "next_action": (
                "Run canonical dry-run"
                if gate
                else
                "Fix canonical contract"
            ),
        }

    if action == "dry-run":
        payload = execute(
            root=resolved_root,
            apply=False,
        )

        gate = payload[
            "canonical_executor_gate_passed"
        ]

        return {
            "schema_version":
                SCHEMA_VERSION,
            "action":
                action,
            "canonical_manager_gate_passed":
                gate,
            "write_operations_executed":
                payload[
                    "write_operations_executed"
                ],
            "executor":
                payload,
            "next_action": (
                "Apply remains blocked during observation"
                if gate
                else
                "Fix canonical executor"
            ),
        }

    if action == "apply":
        payload = execute(
            root=resolved_root,
            apply=True,
            confirmation=confirmation,
        )

        gate = payload[
            "canonical_executor_gate_passed"
        ]

        return {
            "schema_version":
                SCHEMA_VERSION,
            "action":
                action,
            "canonical_manager_gate_passed":
                gate,
            "write_operations_executed":
                payload[
                    "write_operations_executed"
                ],
            "executor":
                payload,
            "next_action": (
                "Validate installed service"
                if gate
                else
                "System write remains blocked"
            ),
        }

    raise ValueError(
        f"Unsupported manager action: {action}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "AIControlCenter canonical "
            "Shadow LaunchDaemon manager"
        )
    )

    parser.add_argument(
        "action",
        choices=(
            "preflight",
            "plan",
            "dry-run",
            "apply",
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

    arguments = parser.parse_args()

    result = manager_result(
        action=arguments.action,
        root=arguments.root,
        confirmation=
            arguments.confirm_label,
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


if __name__ == "__main__":
    raise SystemExit(main())
