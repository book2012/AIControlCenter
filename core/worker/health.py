import json
from typing import Any, Dict

from core.worker.runner import Runner

WORKER_HEALTH_SCHEMA_VERSION = 1
WORKER_HEALTH_STATES = {"ONLINE", "READY", "WARNING", "RECOVERY", "OFFLINE", "UNKNOWN"}


def parse_health_json(output: str) -> Dict[str, Any]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_worker_health_json") from exc

    if not isinstance(data, dict):
        raise ValueError("invalid_worker_health_shape")

    required = ("schema_version", "worker_id", "role", "health", "available")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing_worker_health_fields:" + ",".join(missing))

    if data["schema_version"] != WORKER_HEALTH_SCHEMA_VERSION:
        raise ValueError("unsupported_worker_health_schema")
    if not isinstance(data["worker_id"], str) or not data["worker_id"]:
        raise ValueError("invalid_worker_id")
    if not isinstance(data["role"], str) or not data["role"]:
        raise ValueError("invalid_worker_role")
    if data["health"] not in WORKER_HEALTH_STATES:
        raise ValueError("invalid_worker_health_state")
    if not isinstance(data["available"], bool):
        raise ValueError("invalid_worker_availability")

    return data


def run_json_script(runner: Runner, script_path: str) -> Dict[str, Any]:
    output = runner.run(["bash", script_path])

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from {script_path}: {exc}") from exc


def run_worker_command(
    runner: Runner,
    script_path: str,
    command: str,
) -> Dict[str, Any]:
    output = runner.run(["bash", script_path, command])

    try:
        parsed = json.loads(output)
        return {
            "command": command,
            "ok": True,
            "format": "json",
            "result": parsed,
        }
    except json.JSONDecodeError:
        return {
            "command": command,
            "ok": True,
            "format": "text",
            "output": output,
        }


def decide_worker_status(
    ready: Dict[str, Any],
    heartbeat: Dict[str, Any],
    recovery: Dict[str, Any],
) -> str:
    if not ready.get("ready"):
        return "OFFLINE"

    if recovery.get("issues"):
        return "RECOVERY"

    checks = ready.get("checks", {})
    if any(value != "OK" for value in checks.values()):
        return "WARNING"

    if heartbeat.get("state") == "ONLINE":
        return "ONLINE"

    if ready.get("state") == "READY":
        return "READY"

    return "UNKNOWN"
