import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WRITE_ACTIONS = {
    "install-native-binary",
    "create-model-storage",
    "install-environment-contract",
    "install-launchdaemon",
    "start-service",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def plan_hash(plan: dict[str, Any]) -> str:
    payload = canonical_json(plan).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def build_approval_request(
    plan: dict[str, Any],
    requested_by: str,
    expires_at: str,
) -> dict[str, Any]:
    errors: list[str] = []

    if plan.get("valid") is not True:
        errors.append("dry-run plan must be valid")
    if plan.get("read_only") is not True:
        errors.append("dry-run plan must be read-only")
    if plan.get("execution_enabled") is not False:
        errors.append("dry-run execution must remain disabled")
    if plan.get("service_id") != "ollama":
        errors.append("service_id must be ollama")
    if not requested_by.strip():
        errors.append("requested_by must be non-empty")

    try:
        expiry = parse_timestamp(expires_at)
    except ValueError as exc:
        expiry = None
        errors.append(f"invalid expires_at: {exc}")

    now = datetime.now(timezone.utc)
    if expiry is not None and expiry <= now:
        errors.append("expires_at must be in the future")

    allowed_actions = [
        step["action"]
        for step in plan.get("steps", [])
        if step.get("write") is True
        and step.get("action") in WRITE_ACTIONS
    ]

    if not allowed_actions:
        errors.append("no approved write actions found")

    return {
        "schema_version": "1.0",
        "valid": not errors,
        "approval_status": "PENDING" if not errors else "INVALID",
        "execution_enabled": False,
        "service_id": plan.get("service_id"),
        "plan_hash": plan_hash(plan),
        "requested_by": requested_by,
        "approved_by": None,
        "requested_at": now.isoformat(),
        "expires_at": expires_at,
        "allowed_actions": allowed_actions,
        "dry_run_reference": {
            "service_id": plan.get("service_id"),
            "step_count": len(plan.get("steps", [])),
            "rollback_step_count": len(plan.get("rollback_steps", [])),
        },
        "rollback_required": True,
        "errors": errors,
    }


def validate_approval(
    approval: dict[str, Any],
    plan: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if approval.get("schema_version") != "1.0":
        errors.append("approval schema_version must be 1.0")
    if approval.get("service_id") != "ollama":
        errors.append("approval service_id must be ollama")
    if approval.get("execution_enabled") is not False:
        errors.append("approval cannot enable execution")
    if approval.get("plan_hash") != plan_hash(plan):
        errors.append("plan hash mismatch")
    if approval.get("rollback_required") is not True:
        errors.append("rollback must remain required")

    allowed_actions = approval.get("allowed_actions")
    if not isinstance(allowed_actions, list):
        errors.append("allowed_actions must be an array")
    else:
        invalid_actions = sorted(set(allowed_actions) - WRITE_ACTIONS)
        if invalid_actions:
            errors.append(f"disallowed actions: {invalid_actions}")

    expires_at = approval.get("expires_at")
    if not isinstance(expires_at, str):
        errors.append("expires_at must be a string")
    else:
        try:
            expiry = parse_timestamp(expires_at)
            if expiry <= datetime.now(timezone.utc):
                errors.append("approval has expired")
        except ValueError as exc:
            errors.append(f"invalid expires_at: {exc}")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an Ollama installation approval request."
    )
    parser.add_argument("plan", type=Path)
    parser.add_argument("--requested-by", required=True)
    parser.add_argument("--expires-at", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        plan = load_json(args.plan)
        result = build_approval_request(
            plan,
            requested_by=args.requested_by,
            expires_at=args.expires_at,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "schema_version": "1.0",
            "valid": False,
            "approval_status": "INVALID",
            "execution_enabled": False,
            "service_id": "ollama",
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
