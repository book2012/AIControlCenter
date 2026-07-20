import argparse
import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.deployment.manifest import load_manifest, validate_manifest


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_health(
    host: str,
    port: int,
    endpoint: str,
    timeout: float = 2.0,
) -> dict[str, Any]:
    url = f"http://{host}:{port}{endpoint}"

    try:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "AIControlCenter-ServiceInspector/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            return {
                "checked": True,
                "url": url,
                "status_code": status_code,
                "healthy": 200 <= status_code < 400,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "checked": True,
            "url": url,
            "status_code": exc.code,
            "healthy": 200 <= exc.code < 400,
            "error": None,
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "checked": True,
            "url": url,
            "status_code": None,
            "healthy": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }


def inspect_launchd(label: str | None) -> dict[str, Any]:
    if not label:
        return {
            "checked": False,
            "label": None,
            "available": False,
            "running": False,
            "pid": None,
            "error": None,
        }

    target = f"system/{label}"
    result = subprocess.run(
        ["launchctl", "print", target],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "checked": True,
            "label": label,
            "available": False,
            "running": False,
            "pid": None,
            "error": {
                "type": "LaunchctlError",
                "message": result.stderr.strip() or "service unavailable",
            },
        }

    pid = None
    running = False

    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped == "state = running":
            running = True
        if stripped.startswith("pid = "):
            raw_pid = stripped.split("=", 1)[1].strip()
            if raw_pid.isdigit():
                pid = int(raw_pid)

    return {
        "checked": True,
        "label": label,
        "available": True,
        "running": running,
        "pid": pid,
        "error": None,
    }


def inspect_service(service: dict[str, Any]) -> dict[str, Any]:
    host = service.get("listen_host")
    port = service.get("port")
    endpoint = service.get("health_endpoint")
    supervisor = service.get("supervisor")
    launchd_label = service.get("launchd_label")

    launchd = inspect_launchd(
        launchd_label if supervisor == "system-launchdaemon" else None
    )

    listening = False
    if isinstance(host, str) and isinstance(port, int):
        listening = port_listening(host, port)

    if (
        isinstance(host, str)
        and isinstance(port, int)
        and isinstance(endpoint, str)
    ):
        health = http_health(host, port, endpoint)
    else:
        health = {
            "checked": False,
            "url": None,
            "status_code": None,
            "healthy": False,
            "error": None,
        }

    runtime = service.get("runtime")
    command_name = None

    if service["service_id"] == "ollama":
        command_name = "ollama"
    elif runtime == "python-immutable-venv":
        command_name = "python3"

    installed = (
        command_available(command_name)
        if command_name is not None
        else launchd["available"] or listening
    )

    running = launchd["running"] or listening

    return {
        "service_id": service["service_id"],
        "required": service["required"],
        "declared_status": service["production_status"],
        "installed": installed,
        "running": running,
        "listening": listening,
        "healthy": health["healthy"],
        "supervisor": {
            "type": supervisor,
            "inspection": launchd,
        },
        "health": health,
        "command": {
            "name": command_name,
            "available": (
                command_available(command_name)
                if command_name is not None
                else None
            ),
        },
    }


def inspect_manifest(
    manifest_path: Path,
    service_id: str | None = None,
) -> dict[str, Any]:
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "profile": None,
            "service_count": 0,
            "services": [],
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    errors = validate_manifest(manifest)
    if errors:
        return {
            "schema_version": "1.0",
            "valid": False,
            "read_only": True,
            "profile": manifest.get("profile"),
            "service_count": 0,
            "services": [],
            "errors": errors,
        }

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
                "read_only": True,
                "profile": manifest["profile"],
                "service_count": 0,
                "services": [],
                "errors": [f"service not found: {service_id}"],
            }

    inspections = [inspect_service(service) for service in services]

    return {
        "schema_version": "1.0",
        "valid": True,
        "read_only": True,
        "profile": manifest["profile"],
        "service_count": len(inspections),
        "services": inspections,
        "errors": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Mac services without changing system state."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--service", dest="service_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = inspect_manifest(args.manifest, args.service_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
