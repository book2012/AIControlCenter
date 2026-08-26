"""Fail-closed WU09 desired-state deployment wrapper.

This module neither grants nor consumes authorization.  Its caller must supply
the single bounded execution capability; no runtime adapter is provided here.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPOSITORY_ROOT / "config/shopping-mariadb-loopback.json"
COMPOSE_PATH = REPOSITORY_ROOT / "deploy/shopping/mariadb-loopback/compose.yaml"
SCHEMA_VERSION = "1.0"
PROJECT = "ai-shopping-mariadb-loopback"
SERVICE = "mariadb-loopback-adapter"
BIND_HOST = "127.0.0.1"
TARGET_HOST = "database"
TARGET_PORT = 3306
EXTERNAL_NETWORK = "ai-shopping-internal"
EXPECTED_FIELDS = frozenset(
    {
        "schema_version",
        "service",
        "project",
        "bind_host",
        "host_port",
        "target_host",
        "target_port",
        "external_network",
    }
)


class ConfigurationError(ValueError):
    """The durable WU09 transport authority is invalid."""


@dataclass(frozen=True)
class TransportConfiguration:
    host_port: int


@dataclass(frozen=True)
class ComposeInvocation:
    """A fully fixed, non-secret invocation supplied to one outer capability."""

    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]


ExecutionCapability = Callable[[ComposeInvocation], int]


def validate_configuration(document: object) -> TransportConfiguration:
    if not isinstance(document, dict) or set(document) != EXPECTED_FIELDS:
        raise ConfigurationError("configuration fields are not exact")

    expected_strings: Mapping[str, str] = {
        "schema_version": SCHEMA_VERSION,
        "service": SERVICE,
        "project": PROJECT,
        "bind_host": BIND_HOST,
        "target_host": TARGET_HOST,
        "external_network": EXTERNAL_NETWORK,
    }
    for field, expected in expected_strings.items():
        value = document[field]
        if type(value) is not str or value != expected:
            raise ConfigurationError(f"invalid {field}")

    target_port = document["target_port"]
    host_port = document["host_port"]
    if type(target_port) is not int or target_port != TARGET_PORT:
        raise ConfigurationError("invalid target_port")
    if type(host_port) is not int or not 1 <= host_port <= 65535:
        raise ConfigurationError("invalid host_port")
    return TransportConfiguration(host_port=host_port)


def load_configuration(path: Path | None = None) -> TransportConfiguration:
    authority_path = CONFIG_PATH if path is None else path
    try:
        document = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConfigurationError("configuration cannot be read") from error
    return validate_configuration(document)


def _compose_invocation(configuration: TransportConfiguration) -> ComposeInvocation:
    return ComposeInvocation(
        argv=(
            "docker",
            "compose",
            "--project-name",
            PROJECT,
            "--file",
            str(COMPOSE_PATH),
            "up",
            "--detach",
            "--no-deps",
            "--force-recreate",
            SERVICE,
        ),
        environment=(
            ("MARIADB_LOOPBACK_BIND_HOST", BIND_HOST),
            ("MARIADB_LOOPBACK_HOST_PORT", str(configuration.host_port)),
            ("MARIADB_LOOPBACK_TARGET_HOST", TARGET_HOST),
            ("MARIADB_LOOPBACK_TARGET_PORT", str(TARGET_PORT)),
        ),
    )


def deploy(execution_capability: ExecutionCapability) -> int:
    """Validate desired state and perform exactly one bounded invocation."""

    if not callable(execution_capability):
        raise TypeError("execution_capability must be callable")
    invocation = _compose_invocation(load_configuration())
    result = execution_capability(invocation)
    if type(result) is not int:
        raise TypeError("execution capability result must be an integer")
    return result
