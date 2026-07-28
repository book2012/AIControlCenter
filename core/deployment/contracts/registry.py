"""Local-only JSON Schema registry for DPL v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


class DeploymentSchemaRegistryError(RuntimeError):
    pass


class UnknownDeploymentContractError(DeploymentSchemaRegistryError, KeyError):
    pass


@dataclass(frozen=True, slots=True)
class ContractSchemaBinding:
    contract_name: str
    path: str
    schema_id: str
    schema_version: str


@dataclass(frozen=True, slots=True)
class DeploymentSchemaRegistry:
    schema_root: Path
    manifest: Mapping[str, Any]
    contracts: Mapping[str, ContractSchemaBinding]
    schemas_by_id: Mapping[str, Mapping[str, Any]]
    reference_registry: Registry

    def contract_schema(self, contract_name: str) -> Mapping[str, Any]:
        try:
            binding = self.contracts[contract_name]
            return self.schemas_by_id[binding.schema_id]
        except KeyError as error:
            raise UnknownDeploymentContractError(contract_name) from error


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DeploymentSchemaRegistryError(
            "Unable to load deployment schema asset."
        ) from error
    if not isinstance(value, dict):
        raise DeploymentSchemaRegistryError("Schema asset must be an object.")
    return value


def _has_remote_ref(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (
                key == "$ref"
                and isinstance(child, str)
                and child.startswith(("http://", "https://"))
            )
            or _has_remote_ref(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_has_remote_ref(child) for child in value)
    return False


def load_schema_registry(
    *, schema_root: Path | None = None
) -> DeploymentSchemaRegistry:
    root = (
        schema_root
        if schema_root is not None
        else Path(__file__).resolve().parent / "schemas" / "v1"
    ).resolve()
    manifest = _read_object(root / "registry.json")
    if (
        manifest.get("manifest_version") != 1
        or manifest.get("schema_version") != "dpl/v1"
        or manifest.get("network_resolution") is not False
    ):
        raise DeploymentSchemaRegistryError("Unsupported registry manifest.")
    raw_resources = manifest.get("resources")
    raw_contracts = manifest.get("contracts")
    if not isinstance(raw_resources, list) or not isinstance(raw_contracts, dict):
        raise DeploymentSchemaRegistryError("Invalid registry scope.")

    schemas: dict[str, Mapping[str, Any]] = {}
    resources: list[tuple[str, Resource]] = []
    paths: set[str] = set()
    for item in raw_resources:
        if not isinstance(item, dict):
            raise DeploymentSchemaRegistryError("Invalid resource entry.")
        relative = item.get("path")
        schema_id = item.get("schema_id")
        if (
            not isinstance(relative, str)
            or Path(relative).name != relative
            or not isinstance(schema_id, str)
            or relative in paths
            or schema_id in schemas
        ):
            raise DeploymentSchemaRegistryError("Invalid resource identity.")
        path = (root / relative).resolve()
        if path.parent != root:
            raise DeploymentSchemaRegistryError("Resource escaped registry root.")
        schema = _read_object(path)
        if schema.get("$id") != schema_id or _has_remote_ref(schema):
            raise DeploymentSchemaRegistryError("Resource policy failed.")
        try:
            Draft202012Validator.check_schema(schema)
            resource = Resource.from_contents(schema)
        except Exception as error:
            raise DeploymentSchemaRegistryError(
                "Resource meta-validation failed."
            ) from error
        schemas[schema_id] = MappingProxyType(schema)
        paths.add(relative)
        resources.extend(
            ((schema_id, resource), (relative, resource), (path.as_uri(), resource))
        )

    contracts: dict[str, ContractSchemaBinding] = {}
    for name, item in raw_contracts.items():
        if not isinstance(name, str) or not isinstance(item, dict):
            raise DeploymentSchemaRegistryError("Invalid contract binding.")
        relative = item.get("path")
        schema_id = item.get("schema_id")
        version = item.get("schema_version")
        if (
            relative not in paths
            or schema_id not in schemas
            or version != "dpl/v1"
        ):
            raise DeploymentSchemaRegistryError("Invalid contract policy.")
        contracts[name] = ContractSchemaBinding(
            name, relative, schema_id, version
        )
    return DeploymentSchemaRegistry(
        root,
        MappingProxyType(manifest),
        MappingProxyType(contracts),
        MappingProxyType(schemas),
        Registry().with_resources(resources),
    )


__all__ = (
    "ContractSchemaBinding",
    "DeploymentSchemaRegistry",
    "DeploymentSchemaRegistryError",
    "UnknownDeploymentContractError",
    "load_schema_registry",
)
