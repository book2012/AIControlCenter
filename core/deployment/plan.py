import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.deployment.manifest import run_validation


ACTION_ORDER = [
    "validate",
    "inspect",
    "install",
    "start",
    "health",
    "rollback",
]


def build_service_plan(service: dict[str, Any]) -> dict[str, Any]:
    service_id = service["service_id"]
    production_status = service["production_status"]
    required = service["required"]

    install_required = production_status in {
        "NOT_DEPLOYED",
        "NOT_RUNNING",
    }

    start_required = production_status in {
        "NOT_RUNNING",
        "NOT_DEPLOYED",
    }

    health_available = bool(service.get("health_endpoint"))

    actions = [
        {
            "order": 1,
            "action": "validate",
            "write": False,
            "required": True,
        },
        {
            "order": 2,
            "action": "inspect",
            "write": False,
            "required": True,
        },
        {
            "order": 3,
            "action": "install",
            "write": True,
            "required": install_required,
        },
        {
            "order": 4,
            "action": "start",
            "write": True,
            "required": start_required,
        },
        {
            "order": 5,
            "action": "health",
            "write": False,
            "required": health_available,
        },
        {
            "order": 6,
            "action": "rollback",
            "write": True,
            "required": install_required or start_required,
        },
    ]

    return {
        "service_id": service_id,
        "role": service["role"],
        "owner": service["owner"],
        "required_service": required,
        "production_status": production_status,
        "runtime": service["runtime"],
        "supervisor": service["supervisor"],
        "health_endpoint": service.get("health_endpoint"),
        "port": service.get("port"),
        "ubuntu_dependency": service["ubuntu_dependency"],
        "actions": actions,
    }


def build_deployment_plan(
    manifest_path: Path,
    service_id: str | None = None,
) -> dict[str, Any]:
    validation = run_validation(manifest_path)

    if not validation["valid"]:
        return {
            "schema_version": "1.0",
            "valid": False,
            "manifest_path": str(manifest_path),
            "profile": validation["profile"],
            "read_only": True,
            "service_count": 0,
            "plans": [],
            "errors": validation["errors"],
        }

    manifest = json.loads(manifest_path.read_text())
    services = manifest["services"]

    if service_id is not None:
        services = [
            service
            for service in services
            if service["service_id"] == service_id
        ]

        if not services:
            return {
                "schema_version": "1.0",
                "valid": False,
                "manifest_path": str(manifest_path),
                "profile": manifest["profile"],
                "read_only": True,
                "service_count": 0,
                "plans": [],
                "errors": [f"service not found: {service_id}"],
            }

    plans = [build_service_plan(service) for service in services]

    return {
        "schema_version": "1.0",
        "valid": True,
        "manifest_path": str(manifest_path),
        "profile": manifest["profile"],
        "read_only": True,
        "service_count": len(plans),
        "plans": plans,
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a read-only deployment plan."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--service", dest="service_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_deployment_plan(
        args.manifest,
        service_id=args.service_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
