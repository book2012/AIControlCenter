"""Narrow, deterministic parsers for repository ingress desired state."""

from __future__ import annotations

import json
import re
from typing import Any

import yaml

from .repository import RepositoryFileReader

_ENDPOINT = re.compile(r"^(127\.0\.0\.1|localhost|\[?::1\]?):([1-9][0-9]{0,4})$")
_BINDING = re.compile(
    r"^(127\.0\.0\.1|localhost|\[?::1\]?):(?:\$\{([A-Z][A-Z0-9_]*)\}|([1-9][0-9]{0,4})):([1-9][0-9]{0,4})$"
)


def _evidence(kind: str, reference: str) -> list[dict[str, str]]:
    return [{"kind": kind, "reference": reference}]


class IngressContractFileAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def read_ingress_contract(self) -> dict[str, Any]:
        value = json.loads(self._files.read_text(self._path))
        if not isinstance(value, dict):
            raise ValueError("malformed ingress contract")
        return value


class CaddyIngressAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe(self) -> dict[str, Any]:
        text = re.sub(r"#[^\n]*", "", self._files.read_text(self._path))
        upstreams = re.findall(r"(?m)^\s*reverse_proxy\s+([^\s{]+)", text)
        if len(upstreams) != 1:
            raise ValueError("Caddy desired state must define exactly one upstream")
        match = _ENDPOINT.fullmatch(upstreams[0])
        if not match or int(match.group(2)) > 65535:
            raise ValueError("Caddy upstream is malformed or non-loopback")
        return {
            "owner": "host-caddy",
            "host": match.group(1).strip("[]"),
            "port": int(match.group(2)),
            "endpoint": f"{match.group(1).strip('[]')}:{int(match.group(2))}",
            "evidence": _evidence("caddy-desired-state", self._path),
        }


class ColimaIngressAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe(self) -> dict[str, Any]:
        value = json.loads(self._files.read_text(self._path))
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ValueError("malformed Commerce runtime contract")
        binding = value.get("wordpress_host_binding")
        match = _BINDING.fullmatch(binding) if isinstance(binding, str) else None
        if not match:
            raise ValueError("Commerce runtime binding is malformed")
        return {
            "runtime_owner": "mac-control-plane",
            "ubuntu_runtime_allowed": value.get("ubuntu_runtime_allowed"),
            "public_edge_owner": value.get("public_ingress_owner"),
            "host": match.group(1).strip("[]"),
            "port_source": match.group(2),
            "port": int(match.group(3)) if match.group(3) else None,
            "container_port": int(match.group(4)),
            "allowed_workloads": sorted(value.get("allowed_workloads", [])),
            "evidence": _evidence("colima-contract", self._path),
        }


class ComposeIngressAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe(self) -> dict[str, Any]:
        value = yaml.safe_load(self._files.read_text(self._path))
        services = value.get("services") if isinstance(value, dict) else None
        if not isinstance(services, dict):
            raise ValueError("malformed Compose desired state")
        wordpress, database = services.get("wordpress"), services.get("database")
        if not isinstance(wordpress, dict) or not isinstance(database, dict):
            raise ValueError("required Compose services missing")
        ports = wordpress.get("ports")
        if not isinstance(ports, list) or len(ports) != 1:
            raise ValueError("WordPress must define exactly one published binding")
        match = _BINDING.fullmatch(str(ports[0]))
        if not match:
            raise ValueError("WordPress binding is malformed or not loopback-only")
        database_ports = database.get("ports", [])
        if not isinstance(database_ports, list):
            raise ValueError("MariaDB ports malformed")
        environment = wordpress.get("environment", {})
        return {
            "host": match.group(1).strip("[]"),
            "port_source": match.group(2),
            "port": int(match.group(3)) if match.group(3) else None,
            "container_port": int(match.group(4)),
            "database_host_published": bool(database_ports),
            "wordpress": True,
            "woocommerce": isinstance(environment, dict)
            and any(str(key).startswith("WORDPRESS_") for key in environment),
            "direct_public_ports": False,
            "evidence": _evidence("compose-desired-state", self._path),
        }


__all__ = (
    "CaddyIngressAdapter",
    "ColimaIngressAdapter",
    "ComposeIngressAdapter",
    "IngressContractFileAdapter",
)
