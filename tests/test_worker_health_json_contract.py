from core.worker.health import parse_health_json


def test_worker_health_json_contract() -> None:
    output = (
        '{"schema_version":1,"worker_id":"ubuntu-main",'
        '"role":"stateless-infrastructure-worker",'
        '"health":"ONLINE","available":true}'
    )

    data = parse_health_json(output)

    assert data["schema_version"] == 1
    assert data["worker_id"] == "ubuntu-main"
    assert data["role"] == "stateless-infrastructure-worker"
    assert data["health"] == "ONLINE"
    assert data["available"] is True


import pytest


def test_worker_health_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="invalid_worker_health_json"):
        parse_health_json("not-json")


def test_worker_health_rejects_non_object() -> None:
    with pytest.raises(ValueError, match="invalid_worker_health_shape"):
        parse_health_json("[]")


def test_worker_health_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing_worker_health_fields"):
        parse_health_json('{"schema_version":1}')


def test_worker_health_rejects_unknown_schema() -> None:
    output = (
        '{"schema_version":2,"worker_id":"ubuntu-main",'
        '"role":"stateless-infrastructure-worker",'
        '"health":"ONLINE","available":true}'
    )
    with pytest.raises(ValueError, match="unsupported_worker_health_schema"):
        parse_health_json(output)
