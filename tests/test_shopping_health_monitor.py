from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.shopping.observability.health_monitor import (
    HealthMonitorContractError,
    aggregate_health,
    health_monitor_contract_manifest,
)
from core.shopping.observability.health_probe import (
    CANONICAL_STATUS_FIELD,
    HealthFailureCode,
    HealthProbeResult,
    HealthState,
    normalize_adapter_health,
)


def _base_health():
    return {"adapter": "test", "checked_at": "2026-07-23T00:00:00Z", "latency_ms": "test", "message": "test"}


def _healthy():
    return normalize_adapter_health(
        base=_base_health(),
        state="HEALTHY",
        failure_code="none",
    )


def _degraded():
    return normalize_adapter_health(
        base=_base_health(),
        state="DEGRADED",
        failure_code="latency",
        latency_ms=250,
        detail_code=(
            "shopping.health.latency"
        ),
    )


def _unavailable():
    return normalize_adapter_health(
        base=_base_health(),
        state="UNAVAILABLE",
        failure_code="timeout",
        detail_code=(
            "shopping.health.timeout"
        ),
    )


def test_manifest_is_stateless_read_only():
    manifest = (
        health_monitor_contract_manifest()
    )

    assert manifest[
        "control_plane_owner"
    ] == "AIControlCenter"

    assert manifest[
        "read_only"
    ] is True

    assert manifest[
        "persistence"
    ] is False

    assert manifest[
        "network"
    ] is False

    assert manifest[
        "scheduler"
    ] is False

    assert manifest[
        "retry"
    ] is False

    assert manifest[
        "write_methods_allowed"
    ] is False


def test_empty_input_fails_closed_as_unavailable():
    snapshot = aggregate_health(
        adapters={}
    )

    assert (
        snapshot.overall_state
        is HealthState.UNAVAILABLE
    )

    assert snapshot.empty is True
    assert snapshot.total == 0


def test_all_healthy_aggregates_healthy():
    snapshot = aggregate_health(
        adapters={
            "commerce": _healthy(),
            "cms": _healthy(),
        }
    )

    assert (
        snapshot.overall_state
        is HealthState.HEALTHY
    )


def test_degraded_has_precedence_over_healthy():
    snapshot = aggregate_health(
        adapters={
            "commerce": _healthy(),
            "cms": _degraded(),
        }
    )

    assert (
        snapshot.overall_state
        is HealthState.DEGRADED
    )


def test_unavailable_has_highest_precedence():
    snapshot = aggregate_health(
        adapters={
            "commerce": _degraded(),
            "cms": _unavailable(),
            "catalog": _healthy(),
        }
    )

    assert (
        snapshot.overall_state
        is HealthState.UNAVAILABLE
    )


def test_snapshot_counts_are_exact():
    snapshot = aggregate_health(
        adapters={
            "a": _healthy(),
            "b": _healthy(),
            "c": _degraded(),
            "d": _unavailable(),
        }
    )

    assert snapshot.total == 4
    assert snapshot.healthy == 2
    assert snapshot.degraded == 1
    assert snapshot.unavailable == 1


def test_adapter_output_order_is_deterministic():
    snapshot = aggregate_health(
        adapters={
            "zeta": _healthy(),
            "alpha": _healthy(),
            "middle": _healthy(),
        }
    )

    assert list(
        snapshot.to_json()[
            "adapters"
        ]
    ) == [
        "alpha",
        "middle",
        "zeta",
    ]


def test_invalid_adapter_identifier_is_rejected():
    with pytest.raises(
        HealthMonitorContractError,
        match=(
            "shopping.health.monitor.invalid_adapter_id"
        ),
    ):
        aggregate_health(
            adapters={
                "Vendor Secret URL": (
                    _healthy()
                ),
            }
        )


def test_non_probe_result_is_rejected():
    with pytest.raises(
        HealthMonitorContractError,
        match=(
            "shopping.health.monitor.invalid_probe_result"
        ),
    ):
        aggregate_health(
            adapters={
                "commerce": object(),
            }
        )


def test_forged_state_failure_pair_is_rejected():
    good = _healthy()

    forged = HealthProbeResult(
        health=good.health,
        state=HealthState.HEALTHY,
        failure_code=(
            HealthFailureCode.TIMEOUT
        ),
        latency_ms=None,
        detail_code=None,
    )

    with pytest.raises(
        HealthMonitorContractError,
        match=(
            "shopping.health.monitor.state_failure_mismatch"
        ),
    ):
        aggregate_health(
            adapters={
                "commerce": forged,
            }
        )


def test_snapshot_is_stable_after_probe_payload_mutation():
    result = _healthy()

    snapshot = aggregate_health(
        adapters={
            "commerce": result,
        }
    )

    before = snapshot.to_json()

    result.health[
        CANONICAL_STATUS_FIELD
    ] = "mutated-after-aggregation"

    assert (
        snapshot.to_json()
        == before
    )

    assert json.dumps(
        snapshot.to_json(),
        sort_keys=True,
    )


def test_module_has_no_network_persistence_or_scheduler_imports():
    path = Path(
        "core/shopping/observability/health_monitor.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    imported = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            for item in node.names:
                imported.add(
                    item.name.split(
                        "."
                    )[0]
                )

        elif (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
        ):
            imported.add(
                node.module.split(
                    "."
                )[0]
            )

    assert not (
        imported
        & forbidden
    )
