"""Strict `--request`-only controlled operational coordinator CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import (ControlledOperationalBootstrapError,
                     ControlledOperationalBootstrapStatus, canonical_json)
from .validation import ControlledOperationalBootstrapRequestValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--request", required=True)
    try:
        args = parser.parse_args(argv)
        request = ControlledOperationalBootstrapRequestValidator().parse(
            Path(args.request))
        from .composition import build_default_live_orchestrator
        orchestrator = build_default_live_orchestrator(request)
        result = orchestrator.execute(request)
        print(canonical_json(result.as_dict()))
        return 0 if result.status is ControlledOperationalBootstrapStatus.COMPLETE else 2
    except SystemExit:
        raise
    except Exception as exc:
        code = (exc.code if isinstance(exc, ControlledOperationalBootstrapError)
                else "CONTROLLED_OPERATION_FAILED")
        print(canonical_json({"status": "BLOCKED", "reason_code": code,
                              "production_authorized": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
