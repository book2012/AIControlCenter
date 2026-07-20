import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config/schemas/mac-service-manifest.schema.json"
MANIFEST_PATH = ROOT / "config/services/mac-standalone-production.json"

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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")

    if not isinstance(manifest.get("profile"), str):
        errors.append("profile must be a string")

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
        if not isinstance(service, dict):
            errors.append(f"services[{index}] must be an object")
            continue

        missing = REQUIRED_SERVICE_FIELDS - service.keys()
        if missing:
            errors.append(
                f"services[{index}] missing fields: {sorted(missing)}"
            )

        service_id = service.get("service_id")
        if not isinstance(service_id, str) or not service_id:
            errors.append(f"services[{index}].service_id is invalid")
        else:
            service_ids.append(service_id)

        port = service.get("port")
        if port is not None:
            if (
                isinstance(port, bool)
                or not isinstance(port, int)
                or not 1 <= port <= 65535
            ):
                errors.append(f"services[{index}].port is invalid")

        health_endpoint = service.get("health_endpoint")
        if health_endpoint is not None and (
            not isinstance(health_endpoint, str)
            or not health_endpoint.startswith("/")
        ):
            errors.append(
                f"services[{index}].health_endpoint is invalid"
            )

    if len(service_ids) != len(set(service_ids)):
        errors.append("service_id values must be unique")

    return errors


def test_schema_document_is_valid_json():
    schema = load_json(SCHEMA_PATH)

    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["type"] == "object"
    assert "services" in schema["required"]
    assert "service" in schema["$defs"]


def test_mac_service_manifest_contract_is_valid():
    manifest = load_json(MANIFEST_PATH)

    assert validate_manifest(manifest) == []


def test_control_plane_cannot_depend_on_ubuntu():
    manifest = load_json(MANIFEST_PATH)
    invalid = deepcopy(manifest)
    invalid["control_plane"]["ubuntu_dependency"] = True

    errors = validate_manifest(invalid)

    assert "control_plane cannot depend on Ubuntu" in errors


def test_service_port_must_be_valid():
    manifest = load_json(MANIFEST_PATH)
    invalid = deepcopy(manifest)
    invalid["services"][0]["port"] = 70000

    errors = validate_manifest(invalid)

    assert any("port is invalid" in error for error in errors)


def test_service_ids_must_be_unique():
    manifest = load_json(MANIFEST_PATH)
    invalid = deepcopy(manifest)
    invalid["services"][1]["service_id"] = (
        invalid["services"][0]["service_id"]
    )

    errors = validate_manifest(invalid)

    assert "service_id values must be unique" in errors
