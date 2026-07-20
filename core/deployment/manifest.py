import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "profile",
    "control_plane",
    "services",
}

REQUIRED_SERVICE_FIELDS = {
    "service_id",
    "role",
    "owner",
    "required",
    "production_status",
    "runtime",
    "supervisor",
    "ubuntu_dependency",
    "state_policy",
}

ALLOWED_PRODUCTION_STATUSES = {
    "PRODUCTION",
    "OPTIONAL_UNAVAILABLE_ALLOWED",
    "NOT_RUNNING",
    "NOT_DEPLOYED",
}

SERVICE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing_top_level = REQUIRED_TOP_LEVEL_FIELDS - manifest.keys()
    if missing_top_level:
        errors.append(
            f"missing top-level fields: {sorted(missing_top_level)}"
        )

    if manifest.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")

    profile = manifest.get("profile")
    if not isinstance(profile, str) or not profile:
        errors.append("profile must be a non-empty string")

    control_plane = manifest.get("control_plane")
    if not isinstance(control_plane, dict):
        errors.append("control_plane must be an object")
    else:
        if control_plane.get("host_role") != "brain":
            errors.append("control_plane.host_role must be brain")
        if control_plane.get("required") is not True:
            errors.append("control_plane.required must be true")
        if control_plane.get("ubuntu_dependency") is not False:
            errors.append("control_plane cannot depend on Ubuntu")

    services = manifest.get("services")
    if not isinstance(services, list) or not services:
        errors.append("services must be a non-empty array")
        return errors

    service_ids: list[str] = []

    for index, service in enumerate(services):
        prefix = f"services[{index}]"

        if not isinstance(service, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = REQUIRED_SERVICE_FIELDS - service.keys()
        if missing:
            errors.append(f"{prefix} missing fields: {sorted(missing)}")

        service_id = service.get("service_id")
        if (
            not isinstance(service_id, str)
            or SERVICE_ID_PATTERN.fullmatch(service_id) is None
        ):
            errors.append(f"{prefix}.service_id is invalid")
        else:
            service_ids.append(service_id)

        for field_name in ("role", "owner", "runtime", "supervisor", "state_policy"):
            value = service.get(field_name)
            if not isinstance(value, str) or not value:
                errors.append(f"{prefix}.{field_name} must be a non-empty string")

        if not isinstance(service.get("required"), bool):
            errors.append(f"{prefix}.required must be boolean")

        if not isinstance(service.get("ubuntu_dependency"), bool):
            errors.append(f"{prefix}.ubuntu_dependency must be boolean")

        production_status = service.get("production_status")
        if production_status not in ALLOWED_PRODUCTION_STATUSES:
            errors.append(f"{prefix}.production_status is invalid")

        port = service.get("port")
        if port is not None and (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            errors.append(f"{prefix}.port is invalid")

        health_endpoint = service.get("health_endpoint")
        if health_endpoint is not None and (
            not isinstance(health_endpoint, str)
            or not health_endpoint.startswith("/")
        ):
            errors.append(f"{prefix}.health_endpoint is invalid")

    if len(service_ids) != len(set(service_ids)):
        errors.append("service_id values must be unique")

    return errors


def validation_result(
    manifest_path: Path,
    manifest: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, Any]:
    profile = None
    service_count = 0

    if manifest is not None:
        profile = manifest.get("profile")
        services = manifest.get("services")
        if isinstance(services, list):
            service_count = len(services)

    return {
        "schema_version": "1.0",
        "manifest_path": str(manifest_path),
        "valid": not errors,
        "profile": profile,
        "service_count": service_count,
        "errors": errors,
    }


def run_validation(manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return validation_result(
            manifest_path,
            None,
            [f"{type(exc).__name__}: {exc}"],
        )

    errors = validate_manifest(manifest)
    return validation_result(manifest_path, manifest, errors)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an AIControlCenter service manifest."
    )
    parser.add_argument("manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_validation(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
