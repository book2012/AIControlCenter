#!/usr/bin/env python3
"""Read-only JSON CLI for the immutable PROD storefront plugin runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.shopping.storefront_prod_runtime import (  # noqa: E402
    DEFAULT_RELEASE_ROOT,
    ReleaseManifestError,
    plan_contract,
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
        sub.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--repo", type=Path, required=True)
    plan.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
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
        _json(plan_contract(args.repo, args.release_root, args.commit))
    except ReleaseManifestError as exc:
        _json({
            "schema_version": 1,
            "environment": "prod",
            "service": "storefront",
            "mode": "plan_only",
            "execute": False,
            "approved": False,
            "error": str(exc),
        })
        return 1


if __name__ == "__main__":
    sys.exit(main())
