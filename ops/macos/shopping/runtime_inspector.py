"""Read-only, value-free inspection for the Mac-owned shopping runtime."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ROOT / "deploy/shopping/compose.yaml"
CONTEXT = "colima-aicontrolcenter-commerce"
PROFILE = "aicontrolcenter-commerce"
PROJECT = "ai-shopping"
VOLUMES = {
    "wordpress_content_and_configuration": "ai-shopping-wordpress",
    "commerce_database": "ai-shopping-database",
}


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""


Runner = Callable[[Sequence[str]], CommandResult]


def _run(argv: Sequence[str]) -> CommandResult:
    completed = subprocess.run(
        list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=10, check=False,
    )
    return CommandResult(completed.returncode, completed.stdout)


def _json(stdout: str) -> object:
    return json.loads(stdout)


def _compose_rows(stdout: str) -> list[dict[str, object]]:
    value = _json(stdout)
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError("compose output is not an object array")
    return value


def inspect_runtime(runner: Runner = _run) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": "1.0", "project": PROJECT, "context": CONTEXT,
        "colima_profile": PROFILE, "inspection": "read-only",
        "available": False, "healthy": False, "ready": False,
        "wordpress": {"present": False, "running": False, "healthy": False},
        "database": {"present": False, "running": False, "healthy": False},
        "woocommerce": {"kind": "wordpress-hosted-capability", "ready": False},
        "error_type": None,
    }
    colima = runner(("colima", "status", "--profile", PROFILE))
    if colima.returncode != 0:
        result["error_type"] = "RuntimeUnavailable"
        return result
    try:
        compose = runner((
            "docker", "--context", CONTEXT, "compose", "--project-name", PROJECT,
            "--file", str(COMPOSE), "ps", "--all", "--format", "json",
        ))
        if compose.returncode != 0:
            result["error_type"] = "DockerInspectionUnavailable"
            return result
        rows = _compose_rows(compose.stdout)
        by_service = {str(row.get("Service")): row for row in rows}
        for key, service in (("wordpress", "wordpress"), ("database", "database")):
            row = by_service.get(service)
            if row is None:
                continue
            state = str(row.get("State", "")).lower()
            health = str(row.get("Health", "")).lower()
            result[key] = {
                "present": True,
                "running": state == "running",
                "healthy": state == "running" and health == "healthy",
            }
        wordpress = result["wordpress"]
        database = result["database"]
        healthy = bool(wordpress["healthy"] and database["healthy"])
        result.update(available=True, healthy=healthy, ready=healthy)
        result["woocommerce"] = {
            "kind": "wordpress-hosted-capability", "ready": False,
            "reason": "Capability activation and API readability require separate observation",
        }
        if not healthy:
            result["error_type"] = "RuntimeNotHealthy"
        return result
    except (json.JSONDecodeError, TypeError, ValueError):
        result["error_type"] = "MalformedDockerInspection"
        return result


def inspect_storage(runner: Runner = _run) -> dict[str, object]:
    volumes: list[dict[str, object]] = []
    for purpose, name in VOLUMES.items():
        observed = runner(("docker", "--context", CONTEXT, "volume", "inspect", name))
        exists = False
        if observed.returncode == 0:
            try:
                payload = _json(observed.stdout)
                exists = isinstance(payload, list) and len(payload) == 1
            except json.JSONDecodeError:
                exists = False
        volumes.append({"purpose": purpose, "name": name, "exists": exists})
    ready = all(item["exists"] for item in volumes)
    return {
        "schema_version": "1.0", "inspection": "read-only", "owner": "mac-mini-m4",
        "storage_model": "docker-named-volumes-in-dedicated-colima-profile",
        "volumes": volumes, "backup_ready": ready, "restore_ready": ready,
        "mutation_performed": False,
    }


def build_plan(kind: str) -> dict[str, object]:
    steps = {
        "backup": ["preflight", "quiescence-authorization", "database-logical-export", "wordpress-volume-archive", "checksums", "read-only-verification"],
        "restore": ["preflight", "explicit-target-validation", "restore-authorization", "database-import", "wordpress-volume-restore", "read-only-reconciliation"],
        "activation": ["preflight", "storage-and-secrets-validation", "compose-config-validation", "authorized-pull-or-provision", "bounded-up", "read-only-reconciliation", "runtime-health", "woocommerce-readiness"],
    }[kind]
    return {
        "schema_version": "1.0", "action": f"{kind}-plan", "project": PROJECT,
        "human_authorization_required": True, "single_invocation": True,
        "automatic_retry": False, "automatic_rollback": False,
        "steps": steps, "mutation_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("runtime", "storage", "backup-plan", "restore-plan", "activation-plan"))
    args = parser.parse_args()
    if args.action == "runtime":
        payload = inspect_runtime()
    elif args.action == "storage":
        payload = inspect_storage()
    else:
        payload = build_plan(args.action.removesuffix("-plan"))
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
