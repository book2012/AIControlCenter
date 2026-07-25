from __future__ import annotations

import json

import pytest

from core.shopping.observability.health_monitor import (
    aggregate_health,
)
from core.shopping.observability.health_probe import (
    HealthProbeContractError,
    HealthState,
    health_probe_contract_manifest,
    normalize_adapter_health,
)


def _base_health():
    return {"adapter": "test", "checked_at": "2026-07-23T00:00:00Z", "latency_ms": "test", "message": "test"}


def _result(
    *,
    state,
    failure_code,
    detail_code=None,
    latency_ms=None,
):
    return normalize_adapter_health(
        base=_base_health(),
        state=state,
        failure_code=failure_code,
        detail_code=detail_code,
        latency_ms=latency_ms,
    )


def test_probe_contract_requires_bounded_timeout_and_disables_retry():
    manifest = (
        health_probe_contract_manifest()
    )

    assert manifest[
        "bounded_timeout_required"
    ] is True

    assert manifest[
        "probe_layer_retry"
    ] is False

    assert manifest[
        "raw_vendor_error_allowed"
    ] is False

    assert manifest[
        "write_methods_allowed"
    ] is False


def test_timeout_is_unavailable_end_to_end():
    result = _result(
        state="UNAVAILABLE",
        failure_code="timeout",
        detail_code="shopping.health.timeout",
    )

    snapshot = aggregate_health(
        adapters={
            "commerce": result,
        }
    )

    assert (
        snapshot.overall_state
        is HealthState.UNAVAILABLE
    )


def test_transport_is_unavailable_end_to_end():
    result = _result(
        state="UNAVAILABLE",
        failure_code="transport",
        detail_code="shopping.health.transport",
    )

    assert (
        aggregate_health(
            adapters={
                "commerce": result,
            }
        ).overall_state
        is HealthState.UNAVAILABLE
    )


def test_authentication_is_unavailable_end_to_end():
    result = _result(
        state="UNAVAILABLE",
        failure_code="authentication",
        detail_code=(
            "shopping.health.authentication"
        ),
    )

    assert (
        aggregate_health(
            adapters={
                "cms": result,
            }
        ).overall_state
        is HealthState.UNAVAILABLE
    )


def test_authorization_is_unavailable_end_to_end():
    result = _result(
        state="UNAVAILABLE",
        failure_code="authorization",
        detail_code=(
            "shopping.health.authorization"
        ),
    )

    assert result.state is (
        HealthState.UNAVAILABLE
    )


def test_rate_limit_is_degraded_end_to_end():
    result = _result(
        state="DEGRADED",
        failure_code="rate_limit",
        detail_code=(
            "shopping.health.rate_limit"
        ),
    )

    assert (
        aggregate_health(
            adapters={
                "commerce": result,
            }
        ).overall_state
        is HealthState.DEGRADED
    )


def test_latency_is_degraded_end_to_end():
    result = _result(
        state="DEGRADED",
        failure_code="latency",
        detail_code=(
            "shopping.health.latency"
        ),
        latency_ms=500,
    )

    assert (
        aggregate_health(
            adapters={
                "commerce": result,
            }
        ).overall_state
        is HealthState.DEGRADED
    )


def test_remaining_fail_closed_failures_are_unavailable():
    for failure_code in (
        "invalid_payload",
        "schema_mismatch",
        "dependency_unavailable",
        "configuration",
        "unknown",
    ):
        result = _result(
            state="UNAVAILABLE",
            failure_code=failure_code,
            detail_code=(
                "shopping.health."
                + failure_code
            ),
        )

        assert (
            result.state
            is HealthState.UNAVAILABLE
        )


def test_raw_vendor_exception_text_is_rejected():
    with pytest.raises(
        HealthProbeContractError,
        match=(
            "shopping.health.invalid_detail_code"
        ),
    ):
        _result(
            state="UNAVAILABLE",
            failure_code="transport",
            detail_code=(
                "HTTP 500 Authorization: Bearer secret-token"
            ),
        )


def test_monitoring_snapshot_exposes_only_sanitized_failure_metadata():
    result = _result(
        state="UNAVAILABLE",
        failure_code="timeout",
        detail_code=(
            "shopping.health.timeout"
        ),
    )

    payload = aggregate_health(
        adapters={
            "commerce": result,
        }
    ).to_json()

    rendered = json.dumps(
        payload,
        sort_keys=True,
    )

    adapter = payload[
        "adapters"
    ][
        "commerce"
    ]

    assert adapter[
        "failure_code"
    ] == "timeout"

    assert adapter[
        "detail_code"
    ] == "shopping.health.timeout"

    assert "Bearer " not in rendered
    assert "Authorization:" not in rendered
    assert "secret-token" not in rendered
