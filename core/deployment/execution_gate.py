import argparse
import hashlib
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def canonical_hash(data: dict[str, Any]) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def create_execution_token() -> str:
    return secrets.token_hex(32)


def approve_request(
    approval: dict[str, Any],
    approved_by: str,
    execution_token: str,
) -> dict[str, Any]:
    result = dict(approval)
    errors: list[str] = []

    if approval.get("valid") is not True:
        errors.append("approval request must be valid")
    if approval.get("approval_status") != "PENDING":
        errors.append("approval request must be PENDING")
    if approval.get("execution_enabled") is not False:
        errors.append("approval request cannot enable execution")
    if not approved_by.strip():
        errors.append("approved_by must be non-empty")
    if len(execution_token) != 64:
        errors.append("execution_token must be 64 hexadecimal characters")
    else:
        try:
            int(execution_token, 16)
        except ValueError:
            errors.append("execution_token must be hexadecimal")

    if errors:
        result["valid"] = False
        result["approval_status"] = "INVALID"
        result["errors"] = errors
        return result

    result["approval_status"] = "APPROVED"
    result["approved_by"] = approved_by
    result["approved_at"] = datetime.now(timezone.utc).isoformat()
    result["execution_token_hash"] = hashlib.sha256(
        execution_token.encode("utf-8")
    ).hexdigest()
    result["execution_enabled"] = False
    result["errors"] = []
    return result


def validate_execution_gate(
    approval: dict[str, Any],
    plan: dict[str, Any],
    snapshot: dict[str, Any],
    execution_token: str,
) -> list[str]:
    errors: list[str] = []

    if approval.get("valid") is not True:
        errors.append("approval must be valid")
    if approval.get("approval_status") != "APPROVED":
        errors.append("approval status must be APPROVED")
    if not approval.get("approved_by"):
        errors.append("approved_by is required")
    if approval.get("execution_enabled") is not False:
        errors.append("approval cannot directly enable execution")
    if approval.get("plan_hash") != canonical_hash(plan):
        errors.append("plan hash mismatch")

    token_hash = hashlib.sha256(
        execution_token.encode("utf-8")
    ).hexdigest()
    if approval.get("execution_token_hash") != token_hash:
        errors.append("execution token mismatch")

    expires_at = approval.get("expires_at")
    if not isinstance(expires_at, str):
        errors.append("expires_at is required")
    else:
        try:
            if parse_timestamp(expires_at) <= datetime.now(timezone.utc):
                errors.append("approval has expired")
        except ValueError as exc:
            errors.append(f"invalid expires_at: {exc}")

    if snapshot.get("read_only") is not True:
        errors.append("rollback snapshot must be read-only")
    if snapshot.get("execution_enabled") is not False:
        errors.append("snapshot cannot enable execution")
    if snapshot.get("rollback", {}).get("required") is not True:
        errors.append("rollback snapshot is required")

    return errors


def build_gate_result(
    approval: dict[str, Any],
    plan: dict[str, Any],
    snapshot: dict[str, Any],
    execution_token: str,
) -> dict[str, Any]:
    errors = validate_execution_gate(
        approval,
        plan,
        snapshot,
        execution_token,
    )
    return {
        "schema_version": "1.0",
        "service_id": "ollama",
        "valid": not errors,
        "gate_status": "AUTHORIZED" if not errors else "BLOCKED",
        "execution_enabled": False,
        "backup_required": True,
        "rollback_required": True,
        "approved_by": approval.get("approved_by"),
        "plan_hash": canonical_hash(plan),
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Ollama privileged execution gate."
    )
    parser.add_argument("approval", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--execution-token", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = build_gate_result(
            load_json(args.approval),
            load_json(args.plan),
            load_json(args.snapshot),
            args.execution_token,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "schema_version": "1.0",
            "service_id": "ollama",
            "valid": False,
            "gate_status": "BLOCKED",
            "execution_enabled": False,
            "backup_required": True,
            "rollback_required": True,
            "errors": [f"{type(exc).__name__}: {exc}"],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
