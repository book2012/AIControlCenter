#!/usr/bin/env python3
"""Explicit operator for materializing the immutable PROD storefront release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.shopping.storefront_prod_release_materialization import (  # noqa: E402
    ACCEPTED_GIT_COMMIT,
    DEFAULT_RELEASE_ROOT,
    AuthorizationRequiredError,
    ReleaseMaterializationError,
    issue_authorization,
    load_authorization,
    materialize_release,
    save_authorization,
)


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--authorization-file", type=Path, required=True)
    authorize.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    authorize.add_argument("--commit", default=ACCEPTED_GIT_COMMIT)

    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--repo", type=Path, required=True)
    materialize.add_argument("--authorization-file", type=Path, required=True)
    materialize.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    materialize.add_argument("--commit", default=ACCEPTED_GIT_COMMIT)

    args = parser.parse_args(argv)
    try:
        if args.command == "authorize":
            authorization = issue_authorization(args.release_root, git_commit=args.commit)
            save_authorization(args.authorization_file, authorization)
            _json({"authorized": True, "authorization_id": authorization.authorization_id,
                   "git_commit": authorization.git_commit,
                   "release_root": authorization.release_root,
                   "single_use": True})
            return 0

        authorization = load_authorization(args.authorization_file, args.release_root)
        _json(materialize_release(
            args.repo,
            args.release_root,
            authorization=authorization,
            authorization_file=args.authorization_file,
            commit=args.commit,
        ))
        return 0
    except (AuthorizationRequiredError, ReleaseMaterializationError) as exc:
        _json({"materialized": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
