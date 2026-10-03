#!/usr/bin/env python3
"""Read-only JSON CLI for the managed Homepage DEV runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.homepage.managed_runtime import (
    build_plan,
    status_contract,
    validate_contract,
)


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("status", "validate"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--release-root", type=Path, required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--repo", type=Path, required=True)
    plan.add_argument("--release-root", type=Path, required=True)
    plan.add_argument("--commit")

    args = parser.parse_args(argv)
    if args.command == "status":
        _json(status_contract(args.release_root))
        return 0
    if args.command == "validate":
        result = validate_contract(args.release_root)
        _json(result)
        return 0 if result["valid"] else 1
    try:
        _json(build_plan(args.repo, args.release_root, args.commit))
    except ValueError as exc:
        _json({"schema_version": 1, "environment": "dev", "service": "homepage", "execute": False,
               "approved": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
