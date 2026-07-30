"""Strict local JSON validation entrypoint. Controlled execution is not implicit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import (OperationalBootstrapExecutionError,
                     OperationalBootstrapRuntimeMode,
                     OperationalBootstrapRuntimeRequest, canonical_json)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    try:
        path = Path(args.request)
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or canonical_json(payload) != raw:
            raise OperationalBootstrapExecutionError("STRICT_CANONICAL_JSON_REQUIRED")
        fields = __import__("dataclasses").fields(OperationalBootstrapRuntimeRequest)
        expected = {field.name for field in fields}
        required = {field.name for field in fields
                    if field.default is __import__("dataclasses").MISSING}
        if not required <= set(payload) or not set(payload) <= expected:
            raise OperationalBootstrapExecutionError("REQUEST_FIELDS_INVALID")
        payload["mode"] = OperationalBootstrapRuntimeMode(payload["mode"])
        request = OperationalBootstrapRuntimeRequest(**payload)
        if request.mode is not OperationalBootstrapRuntimeMode.TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION:
            if not request.activation_authorization_digest:
                raise OperationalBootstrapExecutionError("ACTIVATION_AUTHORIZATION_REQUIRED")
            raise OperationalBootstrapExecutionError("CONTROLLED_EXECUTION_REQUIRES_COORDINATOR")
        print(canonical_json({"request_id": request.request_id, "status": "VALIDATED",
                              "production_authorized": False}))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, OperationalBootstrapExecutionError) as exc:
        code = exc.code if isinstance(exc, OperationalBootstrapExecutionError) else "INVALID_REQUEST"
        print(canonical_json({"status": "BLOCKED", "reason_code": code,
                              "production_authorized": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
