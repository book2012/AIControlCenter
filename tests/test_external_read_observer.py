from __future__ import annotations

import asyncio

import pytest

from core.monitoring.external_read_observer import ExternalReadObserver, ObservationContractError


def test_observer_executes_health_schema_snapshot_drift_in_order() -> None:
    calls = []

    def health():
        calls.append("health")
        return {"ok": True, "status": "healthy"}

    def schema():
        calls.append("schema")
        return {"ok": True, "schema_version": "v1"}

    def snapshot():
        calls.append("snapshot")
        return {"ok": True, "count": 0}

    def drift(value):
        calls.append("drift")
        assert value["count"] == 0
        return {"ok": True, "drifted": False}

    observer = ExternalReadObserver(
        health_probe=health,
        schema_probe=schema,
        snapshot_reader=snapshot,
        drift_detector=drift,
    )

    result = asyncio.run(observer.observe(source="woocommerce"))

    assert calls == ["health", "schema", "snapshot", "drift"]
    assert result.ok is True
    assert result.to_json_dict()["result"] == "PASS"


def test_observer_supports_async_stage_dependencies() -> None:
    async def health():
        return {"ok": True}

    async def schema():
        return {"ok": True}

    async def snapshot():
        return {"ok": True, "items": []}

    async def drift(value):
        assert value["items"] == []
        return {"ok": True, "drifted": False}

    observer = ExternalReadObserver(
        health_probe=health,
        schema_probe=schema,
        snapshot_reader=snapshot,
        drift_detector=drift,
    )

    assert asyncio.run(observer.observe(source="wordpress")).ok is True


def test_failed_stage_produces_failed_observation_without_mutation_semantics() -> None:
    observer = ExternalReadObserver(
        health_probe=lambda: {"ok": False, "reason": "unreachable"},
        schema_probe=lambda: {"ok": True},
        snapshot_reader=lambda: {"ok": True, "items": []},
        drift_detector=lambda value: {"ok": True, "drifted": False},
    )

    result = asyncio.run(observer.observe(source="woocommerce"))

    assert result.ok is False
    assert result.to_json_dict()["result"] == "FAIL"


@pytest.mark.parametrize(
    "payload",
    [
        {"ok": True, "token": "denied"},
        {"ok": True, "nested": {"consumer_secret": "denied"}},
        {"ok": True, "authorization_header": "denied"},
    ],
)
def test_secret_like_evidence_keys_are_rejected(payload) -> None:
    observer = ExternalReadObserver(
        health_probe=lambda: payload,
        schema_probe=lambda: {"ok": True},
        snapshot_reader=lambda: {"ok": True},
        drift_detector=lambda value: {"ok": True},
    )

    with pytest.raises(ObservationContractError):
        asyncio.run(observer.observe(source="woocommerce"))


def test_stage_requires_boolean_ok() -> None:
    observer = ExternalReadObserver(
        health_probe=lambda: {"ok": "yes"},
        schema_probe=lambda: {"ok": True},
        snapshot_reader=lambda: {"ok": True},
        drift_detector=lambda value: {"ok": True},
    )

    with pytest.raises(ObservationContractError):
        asyncio.run(observer.observe(source="wordpress"))


def test_observer_rejects_empty_source() -> None:
    observer = ExternalReadObserver(
        health_probe=lambda: {"ok": True},
        schema_probe=lambda: {"ok": True},
        snapshot_reader=lambda: {"ok": True},
        drift_detector=lambda value: {"ok": True},
    )

    with pytest.raises(ObservationContractError):
        asyncio.run(observer.observe(source=""))
