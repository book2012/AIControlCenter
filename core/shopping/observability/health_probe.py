from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, cast

from core.shopping.contracts.provisional import AdapterHealth


class HealthProbeContractError(
    ValueError
):
    pass


class HealthState(
    str,
    Enum,
):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class HealthFailureCode(
    str,
    Enum,
):
    NONE = "none"
    LATENCY = "latency"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    TRANSPORT = "transport"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INVALID_PAYLOAD = "invalid_payload"
    SCHEMA_MISMATCH = "schema_mismatch"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


DEFAULT_STATE_BY_FAILURE = MappingProxyType(
    {
        HealthFailureCode.NONE: HealthState.HEALTHY,
        HealthFailureCode.LATENCY: HealthState.DEGRADED,
        HealthFailureCode.RATE_LIMIT: HealthState.DEGRADED,
        HealthFailureCode.TIMEOUT: HealthState.UNAVAILABLE,
        HealthFailureCode.TRANSPORT: HealthState.UNAVAILABLE,
        HealthFailureCode.AUTHENTICATION: HealthState.UNAVAILABLE,
        HealthFailureCode.AUTHORIZATION: HealthState.UNAVAILABLE,
        HealthFailureCode.INVALID_PAYLOAD: HealthState.UNAVAILABLE,
        HealthFailureCode.SCHEMA_MISMATCH: HealthState.UNAVAILABLE,
        HealthFailureCode.DEPENDENCY_UNAVAILABLE: HealthState.UNAVAILABLE,
        HealthFailureCode.CONFIGURATION: HealthState.UNAVAILABLE,
        HealthFailureCode.UNKNOWN: HealthState.UNAVAILABLE,
    }
)


CANONICAL_SCHEMA_ID = "urn:aicontrolcenter:shopping:contract:v1:adapter-health"
CANONICAL_STATUS_FIELD = "status"
CANONICAL_LATENCY_FIELD = "latency_ms"

CANONICAL_STATUS_VALUES = MappingProxyType(
    {"DEGRADED": "degraded", "HEALTHY": "healthy", "UNAVAILABLE": "unavailable"}
)

CANONICAL_PROPERTIES = frozenset(
    ["adapter", "checked_at", "latency_ms", "message", "status"]
)

CANONICAL_REQUIRED_FIELDS = frozenset(
    ["adapter", "checked_at", "latency_ms", "message", "status"]
)


_DETAIL_CODE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,127}$"
)


@dataclass(
    frozen=True,
    slots=True,
)
class HealthProbeResult:
    health: AdapterHealth
    state: HealthState
    failure_code: HealthFailureCode
    latency_ms: int | None
    detail_code: str | None

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "detail_code": self.detail_code,
            "failure_code": self.failure_code.value,
            "health": dict(
                self.health
            ),
            "latency_ms": self.latency_ms,
            "state": self.state.value,
        }


def _coerce_state(
    value: HealthState | str,
) -> HealthState:
    if isinstance(
        value,
        HealthState,
    ):
        return value

    try:
        return HealthState(
            str(value).upper()
        )
    except ValueError as error:
        raise HealthProbeContractError(
            "shopping.health.invalid_state"
        ) from None


def _coerce_failure(
    value: HealthFailureCode | str,
) -> HealthFailureCode:
    if isinstance(
        value,
        HealthFailureCode,
    ):
        return value

    try:
        return HealthFailureCode(
            str(value).lower()
        )
    except ValueError as error:
        raise HealthProbeContractError(
            "shopping.health.invalid_failure_code"
        ) from None


def normalize_adapter_health(
    *,
    base: Mapping[str, Any],
    state: HealthState | str,
    failure_code: HealthFailureCode | str = HealthFailureCode.NONE,
    latency_ms: int | None = None,
    detail_code: str | None = None,
) -> HealthProbeResult:
    if not isinstance(
        base,
        Mapping,
    ):
        raise HealthProbeContractError(
            "shopping.health.base_mapping_required"
        )

    normalized_state = _coerce_state(
        state
    )

    normalized_failure = _coerce_failure(
        failure_code
    )

    expected_state = DEFAULT_STATE_BY_FAILURE[
        normalized_failure
    ]

    if normalized_state is not expected_state:
        raise HealthProbeContractError(
            "shopping.health.state_failure_mismatch"
        )

    if latency_ms is not None:
        if (
            isinstance(
                latency_ms,
                bool,
            )
            or not isinstance(
                latency_ms,
                int,
            )
            or latency_ms < 0
        ):
            raise HealthProbeContractError(
                "shopping.health.invalid_latency"
            )

    if detail_code is not None:
        if (
            not isinstance(
                detail_code,
                str,
            )
            or _DETAIL_CODE_PATTERN.fullmatch(
                detail_code
            )
            is None
        ):
            raise HealthProbeContractError(
                "shopping.health.invalid_detail_code"
            )

    unknown_fields = (
        set(
            base
        )
        - CANONICAL_PROPERTIES
    )

    if unknown_fields:
        raise HealthProbeContractError(
            "shopping.health.unknown_canonical_field"
        )

    payload = dict(
        base
    )

    payload[
        CANONICAL_STATUS_FIELD
    ] = CANONICAL_STATUS_VALUES[
        normalized_state.value
    ]

    if (
        CANONICAL_LATENCY_FIELD
        is not None
        and latency_ms is not None
    ):
        payload[
            CANONICAL_LATENCY_FIELD
        ] = latency_ms

    missing = (
        CANONICAL_REQUIRED_FIELDS
        - set(
            payload
        )
    )

    if missing:
        raise HealthProbeContractError(
            "shopping.health.required_field_missing"
        )

    monitoring_json = {
        "detail_code": detail_code,
        "failure_code": normalized_failure.value,
        "health": payload,
        "latency_ms": latency_ms,
        "state": normalized_state.value,
    }

    try:
        json.dumps(
            monitoring_json,
            sort_keys=True,
        )
    except (
        TypeError,
        ValueError,
    ):
        raise HealthProbeContractError(
            "shopping.health.non_json_value"
        ) from None

    return HealthProbeResult(
        health=cast(
            AdapterHealth,
            payload,
        ),
        state=normalized_state,
        failure_code=normalized_failure,
        latency_ms=latency_ms,
        detail_code=detail_code,
    )


def health_probe_contract_manifest(
) -> dict[str, Any]:
    return {
        "authoritative_port": "AdapterHealthPort",
        "bounded_timeout_required": True,
        "canonical_schema_id": CANONICAL_SCHEMA_ID,
        "canonical_status_field": CANONICAL_STATUS_FIELD,
        "canonical_status_values": dict(
            CANONICAL_STATUS_VALUES
        ),
        "capability_id": "shopping.adapter.health.get",
        "failure_codes": [
            value.value
            for value in HealthFailureCode
        ],
        "health_states": [
            value.value
            for value in HealthState
        ],
        "live_vendor_connection": False,
        "probe_layer_retry": False,
        "raw_vendor_error_allowed": False,
        "read_only": True,
        "write_methods_allowed": False,
    }


__all__ = (
    "CANONICAL_LATENCY_FIELD",
    "CANONICAL_PROPERTIES",
    "CANONICAL_REQUIRED_FIELDS",
    "CANONICAL_SCHEMA_ID",
    "CANONICAL_STATUS_FIELD",
    "CANONICAL_STATUS_VALUES",
    "DEFAULT_STATE_BY_FAILURE",
    "HealthFailureCode",
    "HealthProbeContractError",
    "HealthProbeResult",
    "HealthState",
    "health_probe_contract_manifest",
    "normalize_adapter_health",
)
