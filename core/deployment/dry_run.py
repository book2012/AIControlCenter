import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_design(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("design root must be an object")
    return data


def validate_design(design: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if design.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")

    if design.get("service_id") != "ollama":
        errors.append("service_id must be ollama")

    if design.get("status") != "DESIGN_ONLY":
        errors.append("design status must be DESIGN_ONLY")

    if design.get("ubuntu_dependency") is not False:
        errors.append("Ollama cannot depend on Ubuntu")

    deployment = design.get("deployment", {})
    network = design.get("network", {})
    safety = design.get("safety", {})

    if deployment.get("supervisor") != "system-launchdaemon":
        errors.append("supervisor must be system-launchdaemon")

    if network.get("listen_host") != "127.0.0.1":
        errors.append("Ollama must listen on loopback")

    if safety.get("write_execution_enabled") is not False:
        errors.append("write execution must remain disabled")

    if safety.get("human_approval_required") is not True:
        errors.append("human approval must be required")

    if safety.get("rollback_required") is not True:
        errors.append("rollback must be required")

    return errors


def build_ollama_dry_run(
    design_path: Path,
) -> dict[str, Any]:
    try:
        design = load_design(design_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "execution_enabled": False,
            "approval_required": True,
            "service_id": "ollama",
            "steps": [],
            "rollback_steps": [],
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    errors = validate_design(design)
    if errors:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "execution_enabled": False,
            "approval_required": True,
            "service_id": design.get("service_id"),
            "steps": [],
            "rollback_steps": [],
            "errors": errors,
        }

    deployment = design["deployment"]
    network = design["network"]
    storage = design["storage"]
    environment = design["environment"]

    binary_path = deployment["preferred_binary_path"]
    plist_path = (
        "/Library/LaunchDaemons/"
        + deployment["launchd_label"]
        + ".plist"
    )

    health_url = (
        f"http://{network["listen_host"]}:"
        f"{network["port"]}"
        f"{network["health_endpoint"]}"
    )

    steps = [
        {
            "order": 1,
            "action": "inspect-existing-installation",
            "write": False,
            "command_preview": "command -v ollama",
        },
        {
            "order": 2,
            "action": "validate-target-paths",
            "write": False,
            "targets": [
                binary_path,
                environment["contract_path"],
                plist_path,
                storage["models_path"],
            ],
        },
        {
            "order": 3,
            "action": "install-native-binary",
            "write": True,
            "approval_required": True,
            "command_preview": "brew install ollama",
        },
        {
            "order": 4,
            "action": "create-model-storage",
            "write": True,
            "approval_required": True,
            "target": storage["models_path"],
        },
        {
            "order": 5,
            "action": "install-environment-contract",
            "write": True,
            "approval_required": True,
            "target": environment["contract_path"],
            "mode": environment["mode"],
        },
        {
            "order": 6,
            "action": "install-launchdaemon",
            "write": True,
            "approval_required": True,
            "target": plist_path,
        },
        {
            "order": 7,
            "action": "start-service",
            "write": True,
            "approval_required": True,
            "launchd_label": deployment["launchd_label"],
        },
        {
            "order": 8,
            "action": "validate-health",
            "write": False,
            "url": health_url,
        },
        {
            "order": 9,
            "action": "validate-model-inventory",
            "write": False,
            "model_download_allowed": False,
        },
    ]

    rollback_steps = [
        {
            "order": 1,
            "action": "stop-launchdaemon",
            "write": True,
            "launchd_label": deployment["launchd_label"],
        },
        {
            "order": 2,
            "action": "restore-previous-plist",
            "write": True,
            "target": plist_path,
        },
        {
            "order": 3,
            "action": "restore-previous-environment-contract",
            "write": True,
            "target": environment["contract_path"],
        },
        {
            "order": 4,
            "action": "restore-previous-binary",
            "write": True,
            "target": binary_path,
        },
        {
            "order": 5,
            "action": "validate-rollback-health",
            "write": False,
        },
    ]

    return {
        "schema_version": "1.0",
        "valid": True,
        "read_only": True,
        "execution_enabled": False,
        "approval_required": True,
        "service_id": "ollama",
        "binary_path": binary_path,
        "plist_path": plist_path,
        "environment_path": environment["contract_path"],
        "models_path": storage["models_path"],
        "steps": steps,
        "rollback_steps": rollback_steps,
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a read-only Ollama deployment dry-run."
    )
    parser.add_argument("design", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_ollama_dry_run(args.design)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
