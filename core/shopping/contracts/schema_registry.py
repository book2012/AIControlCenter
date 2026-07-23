from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


class ShoppingSchemaRegistryError(RuntimeError):
    pass


class UnknownShoppingContractError(
    ShoppingSchemaRegistryError,
    KeyError,
):
    pass


@dataclass(frozen=True, slots=True)
class ContractSchemaBinding:
    contract_name: str
    path: str
    schema_id: str
    schema_version: str


@dataclass(frozen=True, slots=True)
class ShoppingSchemaRegistry:
    schema_root: Path
    manifest: Mapping[str, Any]
    contracts: Mapping[str, ContractSchemaBinding]
    schemas_by_id: Mapping[str, Mapping[str, Any]]
    reference_registry: Registry

    def contract_binding(
        self,
        contract_name: str,
    ) -> ContractSchemaBinding:
        try:
            return self.contracts[contract_name]
        except KeyError as error:
            raise UnknownShoppingContractError(
                contract_name
            ) from error

    def contract_schema(
        self,
        contract_name: str,
    ) -> Mapping[str, Any]:
        binding = self.contract_binding(
            contract_name
        )

        try:
            return self.schemas_by_id[
                binding.schema_id
            ]
        except KeyError as error:
            raise ShoppingSchemaRegistryError(
                "Contract schema resource is unavailable."
            ) from error


def _read_json_object(
    path: Path,
) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ShoppingSchemaRegistryError(
            "Unable to load schema registry asset."
        ) from error

    if not isinstance(
        value,
        dict,
    ):
        raise ShoppingSchemaRegistryError(
            "Schema registry asset must contain an object."
        )

    return value


def _remote_references(
    value: Any,
) -> tuple[str, ...]:
    references: list[str] = []

    if isinstance(
        value,
        dict,
    ):
        for key, child in value.items():
            if (
                key == "$ref"
                and isinstance(
                    child,
                    str,
                )
                and child.startswith(
                    (
                        "http://",
                        "https://",
                    )
                )
            ):
                references.append(
                    child
                )

            references.extend(
                _remote_references(
                    child
                )
            )

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            references.extend(
                _remote_references(
                    child
                )
            )

    return tuple(
        references
    )


def _safe_resource_path(
    *,
    schema_root: Path,
    relative_path: str,
) -> Path:
    candidate = (
        schema_root
        / relative_path
    ).resolve()

    try:
        candidate.relative_to(
            schema_root
        )
    except ValueError as error:
        raise ShoppingSchemaRegistryError(
            "Schema resource escaped the registry root."
        ) from error

    if candidate.parent != schema_root:
        raise ShoppingSchemaRegistryError(
            "Nested schema resource paths are not approved."
        )

    return candidate


def load_schema_registry(
    *,
    schema_root: Path | None = None,
) -> ShoppingSchemaRegistry:
    root = (
        schema_root
        if schema_root is not None
        else (
            Path(__file__).resolve().parent
            / "schemas"
            / "v1"
        )
    ).resolve()

    manifest = _read_json_object(
        root
        / "registry.json"
    )

    if (
        manifest.get("manifest_version")
        != 1
        or manifest.get("schema_version")
        != "1.0.0"
        or manifest.get("network_resolution")
        is not False
    ):
        raise ShoppingSchemaRegistryError(
            "Unsupported schema registry manifest."
        )

    raw_resources = manifest.get(
        "resources"
    )
    raw_contracts = manifest.get(
        "contracts"
    )

    if (
        not isinstance(
            raw_resources,
            list,
        )
        or not isinstance(
            raw_contracts,
            dict,
        )
        or len(
            raw_resources
        )
        != 17
        or len(
            raw_contracts
        )
        != 15
    ):
        raise ShoppingSchemaRegistryError(
            "Schema registry manifest scope is invalid."
        )

    schemas_by_id: dict[
        str,
        Mapping[str, Any],
    ] = {}
    resources: list[
        tuple[str, Resource],
    ] = []
    resource_paths: set[str] = set()

    for item in raw_resources:
        if not isinstance(
            item,
            dict,
        ):
            raise ShoppingSchemaRegistryError(
                "Schema resource entry is invalid."
            )

        relative_path = item.get(
            "path"
        )
        expected_id = item.get(
            "schema_id"
        )

        if (
            not isinstance(
                relative_path,
                str,
            )
            or not isinstance(
                expected_id,
                str,
            )
            or relative_path
            in resource_paths
            or expected_id
            in schemas_by_id
        ):
            raise ShoppingSchemaRegistryError(
                "Schema resource identity is invalid."
            )

        resource_path = _safe_resource_path(
            schema_root=root,
            relative_path=relative_path,
        )
        schema = _read_json_object(
            resource_path
        )

        if (
            schema.get("$id")
            != expected_id
            or _remote_references(
                schema
            )
        ):
            raise ShoppingSchemaRegistryError(
                "Schema resource policy validation failed."
            )

        try:
            Draft202012Validator.check_schema(
                schema
            )
            resource = Resource.from_contents(
                schema
            )
        except Exception as error:
            raise ShoppingSchemaRegistryError(
                "Schema resource meta-validation failed."
            ) from error

        schemas_by_id[
            expected_id
        ] = MappingProxyType(
            schema
        )
        resource_paths.add(
            relative_path
        )

        resources.extend(
            [
                (
                    expected_id,
                    resource,
                ),
                (
                    relative_path,
                    resource,
                ),
                (
                    resource_path.as_uri(),
                    resource,
                ),
            ]
        )

    contracts: dict[
        str,
        ContractSchemaBinding,
    ] = {}

    for (
        contract_name,
        item,
    ) in raw_contracts.items():
        if (
            not isinstance(
                contract_name,
                str,
            )
            or not isinstance(
                item,
                dict,
            )
        ):
            raise ShoppingSchemaRegistryError(
                "Contract binding is invalid."
            )

        path_value = item.get(
            "path"
        )
        schema_id = item.get(
            "schema_id"
        )
        schema_version = item.get(
            "schema_version"
        )

        if (
            not isinstance(
                path_value,
                str,
            )
            or not isinstance(
                schema_id,
                str,
            )
            or schema_version
            != "1.0.0"
            or path_value
            not in resource_paths
            or schema_id
            not in schemas_by_id
        ):
            raise ShoppingSchemaRegistryError(
                "Contract binding policy validation failed."
            )

        contracts[
            contract_name
        ] = ContractSchemaBinding(
            contract_name=contract_name,
            path=path_value,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    return ShoppingSchemaRegistry(
        schema_root=root,
        manifest=MappingProxyType(
            manifest
        ),
        contracts=MappingProxyType(
            contracts
        ),
        schemas_by_id=MappingProxyType(
            schemas_by_id
        ),
        reference_registry=(
            Registry()
            .with_resources(
                resources
            )
        ),
    )


__all__ = (
    "ContractSchemaBinding",
    "ShoppingSchemaRegistry",
    "ShoppingSchemaRegistryError",
    "UnknownShoppingContractError",
    "load_schema_registry",
)
