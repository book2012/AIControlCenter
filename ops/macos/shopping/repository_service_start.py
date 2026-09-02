"""Repository-only desired-state facts for Shopping service-start observation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


class RepositoryFactError(ValueError):
    """Raised when canonical repository configuration cannot be trusted."""


@dataclass(frozen=True, slots=True)
class ShoppingRepositoryPaths:
    compose: Path
    services: Path
    capabilities: Path
    environment_example: Path

    @classmethod
    def canonical(cls, root: Path) -> "ShoppingRepositoryPaths":
        return cls(
            compose=root / "deploy/shopping/compose.yaml",
            services=root / "config/services/mac-standalone-production.json",
            capabilities=root / "config/capabilities/mac-standalone-production.json",
            environment_example=root / "deploy/shopping/.env.example",
        )


def _mapping(path: Path, *, yaml_document: bool = False) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        value = yaml.safe_load(text) if yaml_document else json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError):
        raise RepositoryFactError("canonical repository configuration is unavailable") from None
    if not isinstance(value, Mapping):
        raise RepositoryFactError("canonical repository configuration is malformed")
    return value


def _example_port(path: Path) -> int:
    try:
        entries = dict(
            line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#") and "=" in line
        )
        port = int(entries["SHOPPING_WORDPRESS_PORT"])
    except (OSError, UnicodeError, KeyError, ValueError):
        raise RepositoryFactError("canonical WordPress port is unavailable") from None
    if not 1 <= port <= 65535:
        raise RepositoryFactError("canonical WordPress port is invalid")
    return port


def load_shopping_repository_facts(paths: ShoppingRepositoryPaths) -> dict[str, Any]:
    """Read canonical repository files only and return value-free facts."""
    compose = _mapping(paths.compose, yaml_document=True)
    manifest = _mapping(paths.services)
    capabilities = _mapping(paths.capabilities)
    try:
        services = manifest["services"]
        runtime = next(
            item for item in services
            if item["service_id"] == "shopping-runtime"
        )
        capability = next(
            item for item in capabilities["capabilities"]
            if item["capability_id"] == "woocommerce"
        )
        compose_services = compose["services"]
        database = compose_services["database"]
        wordpress = compose_services["wordpress"]
        wordpress_ports = wordpress["ports"]
    except (KeyError, TypeError, StopIteration):
        raise RepositoryFactError("canonical Shopping configuration is incomplete") from None
    if not isinstance(database, Mapping) or not isinstance(wordpress, Mapping):
        raise RepositoryFactError("canonical Shopping services are malformed")
    port = _example_port(paths.environment_example)
    expected_binding = f"127.0.0.1:${{SHOPPING_WORDPRESS_PORT}}:80"
    facts = {
        "runtime_owner": (
            "mac"
            if runtime.get("state_policy") == "mac-owned-docker-volumes"
            else "unknown"
        ),
        "ubuntu_dependency": runtime.get("ubuntu_dependency"),
        "mariadb_host_published_port": bool(database.get("ports")),
        "wordpress_bind_host": (
            "127.0.0.1"
            if wordpress_ports == [expected_binding]
            else "unknown"
        ),
        "wordpress_port": port if wordpress_ports == [expected_binding] else None,
        "woocommerce_host_service_id": capability.get("host_service_id"),
        "woocommerce_kind": capability.get("kind"),
        "deployment_status": runtime.get("production_status"),
    }
    expected = {
        "runtime_owner": "mac",
        "ubuntu_dependency": False,
        "mariadb_host_published_port": False,
        "wordpress_bind_host": "127.0.0.1",
        "woocommerce_host_service_id": "shopping-runtime",
        "woocommerce_kind": "wordpress-plugin-commerce-engine",
        "deployment_status": "NOT_DEPLOYED",
    }
    if {key: facts[key] for key in expected} != expected:
        raise RepositoryFactError("canonical Shopping desired state is unsupported")
    return facts


__all__ = (
    "RepositoryFactError",
    "ShoppingRepositoryPaths",
    "load_shopping_repository_facts",
)
