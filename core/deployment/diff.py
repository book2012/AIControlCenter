import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.deployment.inspect import inspect_manifest
from core.deployment.plan import build_deployment_plan


def required_actions_for_service(
    plan: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    actions: list[str] = []

    if not actual.get("installed", False):
        actions.append("install")

    if not actual.get("running", False):
        actions.append("start")

    health_declared = bool(plan.get("health_endpoint"))
    if health_declared and not actual.get("healthy", False):
        actions.append("health")

    return actions


def build_service_diff(
    plan: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    required_actions = required_actions_for_service(plan, actual)
    write_actions = {
        action["action"]
        for action in plan["actions"]
        if action["write"]
    }

    write_required = any(
        action in write_actions
        for action in required_actions
    )

    converged = not required_actions

    return {
        "service_id": plan["service_id"],
        "declared_status": plan["production_status"],
        "required_service": plan["required_service"],
        "desired": {
            "installed": True,
            "running": True,
            "healthy": bool(plan.get("health_endpoint")),
        },
        "actual": {
            "installed": bool(actual.get("installed", False)),
            "running": bool(actual.get("running", False)),
            "listening": bool(actual.get("listening", False)),
            "healthy": bool(actual.get("healthy", False)),
        },
        "required_actions": required_actions,
        "write_required": write_required,
        "approval_required": write_required,
        "converged": converged,
    }


def build_deployment_diff(
    manifest_path: Path,
    service_id: str | None = None,
) -> dict[str, Any]:
    plan_result = build_deployment_plan(
        manifest_path,
        service_id=service_id,
    )

    if not plan_result["valid"]:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "profile": plan_result.get("profile"),
            "service_count": 0,
            "diffs": [],
            "write_required": False,
            "errors": plan_result["errors"],
        }

    inspection_result = inspect_manifest(
        manifest_path,
        service_id=service_id,
    )

    if not inspection_result["valid"]:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "profile": inspection_result.get("profile"),
            "service_count": 0,
            "diffs": [],
            "write_required": False,
            "errors": inspection_result["errors"],
        }

    actual_by_service = {
        item["service_id"]: item
        for item in inspection_result["services"]
    }

    diffs = [
        build_service_diff(
            plan,
            actual_by_service[plan["service_id"]],
        )
        for plan in plan_result["plans"]
    ]

    return {
        "schema_version": "1.0",
        "valid": True,
        "read_only": True,
        "profile": plan_result["profile"],
        "service_count": len(diffs),
        "diffs": diffs,
        "write_required": any(
            item["write_required"]
            for item in diffs
        ),
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare desired and actual Mac service state."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--service", dest="service_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_deployment_diff(
        args.manifest,
        service_id=args.service_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
