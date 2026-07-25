from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from core.shopping.observability.health_probe import (
    DEFAULT_STATE_BY_FAILURE,
    HealthProbeResult,
    HealthState,
)


class HealthMonitorContractError(
    ValueError
):
    pass


_STATE_PRECEDENCE = MappingProxyType(
    {
        HealthState.HEALTHY: 0,
        HealthState.DEGRADED: 1,
        HealthState.UNAVAILABLE: 2,
    }
)


_ADAPTER_ID_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]{0,127}$"
)


@dataclass(
    frozen=True,
    slots=True,
)
class HealthMonitorSnapshot:
    overall_state: HealthState
    total: int
    healthy: int
    degraded: int
    unavailable: int
    empty: bool
    _adapter_json: tuple[
        tuple[
            str,
            str,
        ],
        ...,
    ]

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "adapters": {
                adapter_id: json.loads(
                    serialized
                )
                for (
                    adapter_id,
                    serialized,
                )
                in self._adapter_json
            },
            "counts": {
                "degraded": self.degraded,
                "healthy": self.healthy,
                "total": self.total,
                "unavailable": (
                    self.unavailable
                ),
            },
            "empty": self.empty,
            "overall_state": (
                self.overall_state.value
            ),
        }


def aggregate_health(
    *,
    adapters: Mapping[
        str,
        HealthProbeResult,
    ],
) -> HealthMonitorSnapshot:
    if not isinstance(
        adapters,
        Mapping,
    ):
        raise HealthMonitorContractError(
            "shopping.health.monitor.mapping_required"
        )

    serialized_results: list[
        tuple[
            str,
            str,
            HealthState,
        ]
    ] = []

    for (
        adapter_id,
        result,
    ) in adapters.items():
        if (
            not isinstance(
                adapter_id,
                str,
            )
            or _ADAPTER_ID_PATTERN.fullmatch(
                adapter_id
            )
            is None
        ):
            raise HealthMonitorContractError(
                "shopping.health.monitor.invalid_adapter_id"
            )

        if not isinstance(
            result,
            HealthProbeResult,
        ):
            raise HealthMonitorContractError(
                "shopping.health.monitor.invalid_probe_result"
            )

        try:
            expected_state = (
                DEFAULT_STATE_BY_FAILURE[
                    result.failure_code
                ]
            )
        except (
            KeyError,
            TypeError,
        ):
            raise HealthMonitorContractError(
                "shopping.health.monitor.invalid_failure_code"
            ) from None

        if result.state is not expected_state:
            raise HealthMonitorContractError(
                "shopping.health.monitor.state_failure_mismatch"
            )

        try:
            serialized = json.dumps(
                result.to_json(),
                allow_nan=False,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
                sort_keys=True,
            )
        except (
            TypeError,
            ValueError,
        ):
            raise HealthMonitorContractError(
                "shopping.health.monitor.non_json_probe_result"
            ) from None

        serialized_results.append(
            (
                adapter_id,
                serialized,
                result.state,
            )
        )

    serialized_results.sort(
        key=lambda item: item[0]
    )

    states = [
        item[2]
        for item in serialized_results
    ]

    healthy = sum(
        state is HealthState.HEALTHY
        for state in states
    )

    degraded = sum(
        state is HealthState.DEGRADED
        for state in states
    )

    unavailable = sum(
        state is HealthState.UNAVAILABLE
        for state in states
    )

    if not states:
        overall_state = (
            HealthState.UNAVAILABLE
        )
    else:
        overall_state = max(
            states,
            key=lambda value: (
                _STATE_PRECEDENCE[
                    value
                ]
            ),
        )

    snapshot = HealthMonitorSnapshot(
        overall_state=overall_state,
        total=len(
            serialized_results
        ),
        healthy=healthy,
        degraded=degraded,
        unavailable=unavailable,
        empty=not bool(
            serialized_results
        ),
        _adapter_json=tuple(
            (
                adapter_id,
                serialized,
            )
            for (
                adapter_id,
                serialized,
                _,
            )
            in serialized_results
        ),
    )

    try:
        json.dumps(
            snapshot.to_json(),
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
    except (
        TypeError,
        ValueError,
    ):
        raise HealthMonitorContractError(
            "shopping.health.monitor.non_json_snapshot"
        ) from None

    return snapshot


def health_monitor_contract_manifest(
) -> dict[str, Any]:
    return {
        "authorization_decision": False,
        "control_plane_owner": (
            "AIControlCenter"
        ),
        "deterministic": True,
        "empty_input_state": (
            HealthState.UNAVAILABLE.value
        ),
        "input_contract": (
            "Mapping[str, HealthProbeResult]"
        ),
        "network": False,
        "overall_state_precedence": [
            HealthState.UNAVAILABLE.value,
            HealthState.DEGRADED.value,
            HealthState.HEALTHY.value,
        ],
        "persistence": False,
        "read_only": True,
        "retry": False,
        "scheduler": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "HealthMonitorContractError",
    "HealthMonitorSnapshot",
    "aggregate_health",
    "health_monitor_contract_manifest",
)
