#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPOSITORY_ROOT),
    )

from core.governance.operations.scheduler_policy import (
    load_policy,
    write_documents,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        type=Path,
        default=(
            REPOSITORY_ROOT
            / "config/"
            "governance_operations_"
            "scheduler_policy.json"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--json",
        action="store_true",
    )
    arguments = parser.parse_args()

    document = load_policy(
        arguments.policy
    )
    paths = write_documents(
        document,
        output_directory=(
            arguments.output_dir
        ),
        repository_root=REPOSITORY_ROOT,
        python_executable=(
            REPOSITORY_ROOT
            / ".venv/bin/python"
        ),
        log_directory=(
            Path.home()
            / "Library/Logs/"
            "AIControlCenter/governance"
        ),
    )

    result = {
        "activated": False,
        "installed": False,
        "paths": [
            str(path)
            for path in paths
        ],
        "rendered_count": len(paths),
        "result": "PASS",
    }

    if arguments.json:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    else:
        for path in paths:
            print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
