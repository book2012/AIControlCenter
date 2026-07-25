from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.shopping.observability.health_probe import (
    CANONICAL_LATENCY_FIELD,
    CANONICAL_STATUS_FIELD,
    CANONICAL_STATUS_VALUES,
    HealthFailureCode,
    HealthProbeContractError,
    HealthState,
    health_probe_contract_manifest,
    normalize_adapter_health,
)


def _base_health():
    return {"adapter": "test", "checked_at": "2026-07-23T00:00:00Z", "latency_ms": "test", "message": "test"}


def test_manifest_is_read_only_and_vendor_neutral():
    manifest = health_probe_contract_manifest()

    assert manifest[
        "authoritative_port"
    ] == "AdapterHealthPort"

    assert manifest[
        "capability_id"
    ] == "shopping.adapter.health.get"

    assert manifest[
        "read_only"
    ] is True

    assert manifest[
        "write_methods_allowed"
    ] is False

    assert manifest[
        "live_vendor_connection"
    ] is False

    assert manifest[
        "probe_layer_retry"
    ] is False


def test_healthy_normalization_uses_canonical_status():
    result = normalize_adapter_health(
        base=_base_health(),
        state=HealthState.HEALTHY,
        failure_code=HealthFailureCode.NONE,
    )

    assert (
        result.health[
            CANONICAL_STATUS_FIELD
        ]
        == CANONICAL_STATUS_VALUES[
            "HEALTHY"
        ]
    )


def test_degraded_latency_normalization():
    result = normalize_adapter_health(
        base=_base_health(),
        state="DEGRADED",
        failure_code="latency",
        latency_ms=125,
        detail_code="shopping.health.latency",
    )

    assert result.state is HealthState.DEGRADED
    assert result.failure_code is HealthFailureCode.LATENCY
    assert result.latency_ms == 125

    if CANONICAL_LATENCY_FIELD is not None:
        assert (
            result.health[
                CANONICAL_LATENCY_FIELD
            ]
            == 125
        )


def test_unavailable_timeout_normalization():
    result = normalize_adapter_health(
        base=_base_health(),
        state="UNAVAILABLE",
        failure_code="timeout",
        detail_code="shopping.health.timeout",
    )

    assert result.state is HealthState.UNAVAILABLE
    assert result.failure_code is HealthFailureCode.TIMEOUT


def test_state_failure_mismatch_is_rejected():
    with pytest.raises(
        HealthProbeContractError,
        match=(
            "shopping.health.state_failure_mismatch"
        ),
    ):
        normalize_adapter_health(
            base=_base_health(),
            state="HEALTHY",
            failure_code="timeout",
        )


def test_unknown_state_is_rejected():
    with pytest.raises(
        HealthProbeContractError,
        match="shopping.health.invalid_state",
    ):
        normalize_adapter_health(
            base=_base_health(),
            state="BROKEN",
            failure_code="none",
        )


def test_unknown_failure_code_is_rejected():
    with pytest.raises(
        HealthProbeContractError,
        match=(
            "shopping.health.invalid_failure_code"
        ),
    ):
        normalize_adapter_health(
            base=_base_health(),
            state="UNAVAILABLE",
            failure_code="vendor_magic",
        )


def test_negative_latency_is_rejected():
    with pytest.raises(
        HealthProbeContractError,
        match="shopping.health.invalid_latency",
    ):
        normalize_adapter_health(
            base=_base_health(),
            state="DEGRADED",
            failure_code="latency",
            latency_ms=-1,
        )


def test_raw_error_text_is_not_accepted_as_detail_code():
    with pytest.raises(
        HealthProbeContractError,
        match=(
            "shopping.health.invalid_detail_code"
        ),
    ):
        normalize_adapter_health(
            base=_base_health(),
            state="UNAVAILABLE",
            failure_code="transport",
            detail_code=(
                "HTTP 500 raw vendor body secret=abc"
            ),
        )


def test_unknown_canonical_field_is_rejected():
    base = _base_health()
    base[
        "vendor_private_payload"
    ] = {
        "secret": "value",
    }

    with pytest.raises(
        HealthProbeContractError,
        match=(
            "shopping.health.unknown_canonical_field"
        ),
    ):
        normalize_adapter_health(
            base=base,
            state="HEALTHY",
            failure_code="none",
        )


def test_input_is_not_mutated_and_result_is_json_safe():
    base = _base_health()
    before = json.loads(
        json.dumps(
            base,
            sort_keys=True,
        )
    )

    result = normalize_adapter_health(
        base=base,
        state="UNAVAILABLE",
        failure_code="configuration",
        detail_code=(
            "shopping.health.configuration"
        ),
    )

    assert base == before

    rendered = json.dumps(
        result.to_json(),
        sort_keys=True,
    )

    assert rendered


def test_module_has_no_network_environment_or_filesystem_imports():
    path = Path(
        "core/shopping/observability/health_probe.py"
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
