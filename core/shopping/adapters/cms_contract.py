from __future__ import annotations

import inspect
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from core.shopping.ports.cms import CmsReadPort
from core.shopping.governance.capabilities import (
    DEFAULT_CAPABILITY_REGISTRY,
)


class CmsAdapterContractError(
    ValueError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class CmsMethodContract:
    method_name: str
    capability_id: str
    return_contract: str


EXPECTED_RETURN_CONTRACTS = MappingProxyType(
    {
        "get_content": "ContentSnapshot",
        "list_content": "ContentSnapshotPage",
    }
)


_WRITE_TOKENS = (
    "append",
    "create",
    "delete",
    "patch",
    "persist",
    "publish",
    "register",
    "set_",
    "update",
    "write",
)


def _signature_shape(
    callable_object: Any,
):
    signature = inspect.signature(
        callable_object
    )

    return tuple(
        (
            parameter.name,
            parameter.kind,
            (
                parameter.default
                is not inspect.Signature.empty
            ),
        )
        for parameter
        in signature.parameters.values()
    )


def _annotation_name(
    annotation: Any,
) -> str:
    if annotation is (
        inspect.Signature.empty
    ):
        return ""

    if isinstance(
        annotation,
        str,
    ):
        return annotation

    name = getattr(
        annotation,
        "__name__",
        None,
    )

    if isinstance(name, str):
        return name

    return str(annotation)


def _capability_for(
    method_name: str,
) -> str:
    matches = [
        definition.capability_id
        for definition
        in DEFAULT_CAPABILITY_REGISTRY.definitions.values()
        if (
            definition.port
            == "CmsReadPort"
            and definition.method
            == method_name
        )
    ]

    if len(matches) != 1:
        raise CmsAdapterContractError(
            "shopping.cms.capability_binding_invalid"
        )

    return matches[0]


def cms_contract_manifest(
) -> dict[str, Any]:
    methods = {}

    for method_name in sorted(
        EXPECTED_RETURN_CONTRACTS
    ):
        methods[method_name] = {
            "capability_id": (
                _capability_for(
                    method_name
                )
            ),
            "return_contract": (
                EXPECTED_RETURN_CONTRACTS[
                    method_name
                ]
            ),
        }

    return {
        "authoritative_port": "CmsReadPort",
        "business_logic_in_adapter": False,
        "duplicate_callable_interface": False,
        "live_vendor_connection": False,
        "methods": methods,
        "policy_evaluation_in_adapter": False,
        "read_only": True,
        "vendor_dto_escape_allowed": False,
        "write_methods_allowed": False,
    }


def validate_cms_adapter_class(
    adapter_type: type[Any],
) -> type[Any]:
    if not inspect.isclass(
        adapter_type
    ):
        raise CmsAdapterContractError(
            "shopping.cms.adapter_class_required"
        )

    for method_name, return_contract in (
        EXPECTED_RETURN_CONTRACTS.items()
    ):
        port_method = getattr(
            CmsReadPort,
            method_name,
            None,
        )

        adapter_method = getattr(
            adapter_type,
            method_name,
            None,
        )

        if (
            port_method is None
            or adapter_method is None
        ):
            raise CmsAdapterContractError(
                "shopping.cms.required_method_missing"
            )

        if not inspect.iscoroutinefunction(
            adapter_method
        ):
            raise CmsAdapterContractError(
                "shopping.cms.async_method_required"
            )

        if (
            _signature_shape(
                adapter_method
            )
            != _signature_shape(
                port_method
            )
        ):
            raise CmsAdapterContractError(
                "shopping.cms.signature_mismatch"
            )

        return_annotation = inspect.signature(
            adapter_method
        ).return_annotation

        if return_contract not in (
            _annotation_name(
                return_annotation
            )
        ):
            raise CmsAdapterContractError(
                "shopping.cms.return_contract_mismatch"
            )

        _capability_for(
            method_name
        )

    for name, value in inspect.getmembers(
        adapter_type
    ):
        if (
            name.startswith("_")
            or name
            in EXPECTED_RETURN_CONTRACTS
            or not callable(value)
        ):
            continue

        lowered = name.lower()

        if any(
            token in lowered
            for token in _WRITE_TOKENS
        ):
            raise CmsAdapterContractError(
                "shopping.cms.write_method_forbidden"
            )

    return adapter_type


def validate_cms_adapter_instance(
    adapter: Any,
) -> Any:
    validate_cms_adapter_class(
        type(adapter)
    )

    return adapter


__all__ = (
    "CmsAdapterContractError",
    "CmsMethodContract",
    "EXPECTED_RETURN_CONTRACTS",
    "cms_contract_manifest",
    "validate_cms_adapter_class",
    "validate_cms_adapter_instance",
)
