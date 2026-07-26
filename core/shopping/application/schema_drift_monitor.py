from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import is_dataclass
from enum import Enum
from typing import Any

from core.shopping.contracts.schema_drift import (
    DriftResult,
    classify_schema_drift,
)
from core.shopping.contracts.schema_validation import (
    SchemaCatalog,
    SchemaCatalogError,
    load_canonical_schema_catalog,
)


SCHEMA_DISCOVERY_CAPABILITY = "shopping.schema.discover"
SCHEMA_DISCOVERY_METHOD = "discover_schema"

AUTHORIZATION_KEYWORDS = ('capability_id', 'context')

DISCOVERY_REQUIRED_KEYWORDS = (
    "context",
    "adapter_name",
)


class SchemaDriftMonitorStatus(
    str,
    Enum,
):
    OK = "OK"
    DENIED = "DENIED"
    ERROR = "ERROR"


@dataclass(
    frozen=True,
    slots=True,
)
class SchemaDriftMonitorResult:
    schema_id: str
    adapter_name: str
    status: SchemaDriftMonitorStatus
    drift: DriftResult | None
    error_code: str | None

    @property
    def auto_adopt(
        self,
    ) -> bool:
        return False

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "auto_adopt": False,
            "drift": (
                self.drift.to_json()
                if self.drift
                is not None
                else None
            ),
            "error_code": (
                self.error_code
            ),
            "schema_id": self.schema_id,
            "status": self.status.value,
        }


def _authorization_kwargs(
    *,
    context: Any,
) -> dict[str, Any]:
    values: dict[
        str,
        Any,
    ] = {}

    for name in AUTHORIZATION_KEYWORDS:
        if name in {
            "capability",
            "capability_id",
            "capability_name",
        }:
            values[
                name
            ] = SCHEMA_DISCOVERY_CAPABILITY

        elif name in {
            "context",
            "read_context",
        }:
            values[
                name
            ] = context

        elif name in {
            "method",
            "method_name",
        }:
            values[
                name
            ] = SCHEMA_DISCOVERY_METHOD

        elif name in {
            "port",
            "port_name",
        }:
            values[
                name
            ] = "SchemaDiscoveryPort"

        elif name in {
            "operation",
            "operation_class",
        }:
            values[
                name
            ] = "read"

        else:
            raise RuntimeError(
                "shopping.schema.drift_monitor.authorization_contract_error"
            )

    return values


async def _await_if_needed(
    value: Any,
) -> Any:
    if inspect.isawaitable(
        value
    ):
        return await value

    return value


def _authorization_allowed(
    value: Any,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    for key in (
        "allowed",
        "allow",
        "is_allowed",
        "decision",
        "status",
        "result",
    ):
        candidate = None

        if (
            isinstance(
                value,
                Mapping,
            )
            and key in value
        ):
            candidate = value[
                key
            ]

        elif hasattr(
            value,
            key,
        ):
            candidate = getattr(
                value,
                key
            )

        if isinstance(
            candidate,
            bool,
        ):
            return candidate

        raw = getattr(
            candidate,
            "value",
            candidate,
        )

        if isinstance(
            raw,
            str,
        ):
            normalized = raw.strip().upper()

            if normalized in {
                "ALLOW",
                "ALLOWED",
                "APPROVE",
                "APPROVED",
                "PERMIT",
                "PERMITTED",
            }:
                return True

            if normalized in {
                "DENY",
                "DENIED",
                "REJECT",
                "REJECTED",
            }:
                return False

    return False


def _candidate_mapping(
    value: Any,
    *,
    depth: int = 0,
) -> Mapping[
    str,
    Any,
] | None:
    if depth > 4:
        return None

    if isinstance(
        value,
        Mapping,
    ):
        if (
            "$id"
            in value
            or "$schema"
            in value
        ):
            return value

        preferred = (
            "schema",
            "schema_document",
            "candidate_schema",
            "discovered_schema",
            "document",
            "payload",
            "data",
            "result",
            "value",
        )

        for key in preferred:
            if key not in value:
                continue

            found = _candidate_mapping(
                value[
                    key
                ],
                depth=depth + 1,
            )

            if found is not None:
                return found

        for key in sorted(
            value,
            key=str,
        ):
            found = _candidate_mapping(
                value[
                    key
                ],
                depth=depth + 1,
            )

            if found is not None:
                return found

        return None

    to_json = getattr(
        value,
        "to_json",
        None,
    )

    if callable(
        to_json
    ):
        try:
            rendered = to_json()
        except Exception:
            rendered = None

        if rendered is not None:
            found = _candidate_mapping(
                rendered,
                depth=depth + 1,
            )

            if found is not None:
                return found

    if is_dataclass(
        value
    ):
        try:
            for field in fields(
                value
            ):
                found = _candidate_mapping(
                    getattr(
                        value,
                        field.name
                    ),
                    depth=depth + 1,
                )

                if found is not None:
                    return found
        except Exception:
            return None

    for name in (
        "schema",
        "schema_document",
        "candidate_schema",
        "discovered_schema",
        "document",
        "payload",
        "data",
        "result",
        "value",
    ):
        try:
            nested = getattr(
                value,
                name,
            )
        except Exception:
            continue

        found = _candidate_mapping(
            nested,
            depth=depth + 1,
        )

        if found is not None:
            return found

    return None


def _error_result(
    *,
    schema_id: str,
    adapter_name: str,
    code: str,
) -> SchemaDriftMonitorResult:
    return SchemaDriftMonitorResult(
        schema_id=schema_id,
        adapter_name=adapter_name,
        status=(
            SchemaDriftMonitorStatus.ERROR
        ),
        drift=None,
        error_code=code,
    )


async def monitor_schema_drift(
    *,
    authorize: Any,
    discovery_port: Any,
    schema_id: str,
    adapter_name: str,
    context: Any = None,
    catalog: SchemaCatalog | None = None,
) -> SchemaDriftMonitorResult:
    if (
        not isinstance(
            schema_id,
            str,
        )
        or not schema_id
    ):
        return _error_result(
            schema_id="",
            adapter_name=(
                adapter_name
                if isinstance(
                    adapter_name,
                    str,
                )
                else ""
            ),
            code=(
                "shopping.schema.drift_monitor.schema_id_required"
            ),
        )

    if (
        not isinstance(
            adapter_name,
            str,
        )
        or not adapter_name.strip()
    ):
        return _error_result(
            schema_id=schema_id,
            adapter_name="",
            code=(
                "shopping.schema.drift_monitor.adapter_name_required"
            ),
        )

    normalized_adapter_name = (
        adapter_name.strip()
    )

    try:
        authorization_value = (
            await _await_if_needed(
                authorize(
                    **_authorization_kwargs(
                        context=context
                    )
                )
            )
        )
    except Exception:
        return _error_result(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            code=(
                "shopping.schema.drift_monitor.authorization_error"
            ),
        )

    if not _authorization_allowed(
        authorization_value
    ):
        return SchemaDriftMonitorResult(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            status=(
                SchemaDriftMonitorStatus.DENIED
            ),
            drift=None,
            error_code=(
                "shopping.schema.drift_monitor.authorization_denied"
            ),
        )

    if catalog is None:
        try:
            catalog = (
                load_canonical_schema_catalog()
            )
        except SchemaCatalogError:
            return _error_result(
                schema_id=schema_id,
                adapter_name=normalized_adapter_name,
                code=(
                    "shopping.schema.drift_monitor.catalog_error"
                ),
            )

    try:
        canonical_schema = (
            catalog.get_schema(
                schema_id
            )
        )
    except SchemaCatalogError:
        return _error_result(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            code=(
                "shopping.schema.drift_monitor.unknown_schema"
            ),
        )

    method = getattr(
        discovery_port,
        SCHEMA_DISCOVERY_METHOD,
        None,
    )

    if not callable(
        method
    ):
        return _error_result(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            code=(
                "shopping.schema.drift_monitor.discovery_contract_error"
            ),
        )

    try:
        discovered = (
            await _await_if_needed(
                method(
                    context=context,
                    adapter_name=normalized_adapter_name,
                )
            )
        )
    except Exception:
        return _error_result(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            code=(
                "shopping.schema.drift_monitor.discovery_error"
            ),
        )

    candidate_schema = (
        _candidate_mapping(
            discovered
        )
    )

    if candidate_schema is None:
        return _error_result(
            schema_id=schema_id,
            adapter_name=normalized_adapter_name,
            code=(
                "shopping.schema.drift_monitor.invalid_payload"
            ),
        )

    drift = classify_schema_drift(
        canonical_schema=canonical_schema,
        candidate_schema=candidate_schema,
    )

    return SchemaDriftMonitorResult(
        schema_id=schema_id,
        adapter_name=normalized_adapter_name,
        status=(
            SchemaDriftMonitorStatus.OK
        ),
        drift=drift,
        error_code=None,
    )


def schema_drift_monitor_contract_manifest(
) -> dict[str, Any]:
    return {
        "adapter_name_required": True,
        "authorization_before_discovery": True,
        "authorization_capability": (
            SCHEMA_DISCOVERY_CAPABILITY
        ),
        "authorization_injected": True,
        "automatic_adoption": False,
        "automatic_migration": False,
        "automatic_schema_rewrite": False,
        "canonical_catalog_reused": True,
        "classifier_reused": True,
        "database_write": False,
        "discovery_keyword_contract": [
            "context",
            "adapter_name",
        ],
        "discovery_method": (
            SCHEMA_DISCOVERY_METHOD
        ),
        "discovery_port_injected": True,
        "duplicate_authorization_framework": False,
        "filesystem_application_state_write": False,
        "machine_readable": True,
        "network_owned": False,
        "persistence": False,
        "production_registration": False,
        "raw_exception_message": False,
        "raw_vendor_payload": False,
        "schema_id_and_adapter_name_separated": True,
        "schema_mutation": False,
        "statuses": [
            status.value
            for status
            in SchemaDriftMonitorStatus
        ],
        "ubuntu_application_state": False,
        "vendor_write": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "AUTHORIZATION_KEYWORDS",
    "DISCOVERY_REQUIRED_KEYWORDS",
    "SCHEMA_DISCOVERY_CAPABILITY",
    "SCHEMA_DISCOVERY_METHOD",
    "SchemaDriftMonitorResult",
    "SchemaDriftMonitorStatus",
    "monitor_schema_drift",
    "schema_drift_monitor_contract_manifest",
)
