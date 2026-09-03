from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path

import pytest

from core.shopping.observability.service_start import (
    ShoppingComponent,
    build_service_start_projection,
)
from core.shopping.ports.service_start import ShoppingServiceStartObservationPort
from ops.macos.shopping.service_start_observer import (
    HttpObservation,
    MacShoppingServiceStartObserver,
)


ROOT = Path(__file__).resolve().parents[1]
FACTS = {"wordpress_port": 58082}


def runtime(
    *,
    available: bool = True,
    database: dict | None = None,
    wordpress: dict | None = None,
    database_publishers: object = None,
    wordpress_publishers: object = None,
) -> dict:
    return {
        "available": available,
        "database": database if database is not None else {
            "present": True, "running": True, "healthy": True,
        },
        "wordpress": wordpress if wordpress is not None else {
            "present": True, "running": True, "healthy": True,
        },
        "publishers": {
            "database": [] if database_publishers is None else database_publishers,
            "wordpress": ([{
                "URL": "127.0.0.1", "TargetPort": 80,
                "PublishedPort": 58082, "Protocol": "tcp",
            }] if wordpress_publishers is None else wordpress_publishers),
        },
    }


def healthy_http(url: str) -> HttpObservation:
    if url.endswith("/wp-json/"):
        return HttpObservation(200, {"namespaces": ["wp/v2", "wc/v3"]})
    if url.endswith("/shopping/health"):
        return HttpObservation(200, {
            "service": "AIShoppingPlatform", "status": "ONLINE",
            "environment": "test", "runtime": "virtual",
            "deployment_target": "mac-mini-m4", "control_plane": "AIControlCenter",
            "write_mode": "read_only",
        })
    if url.endswith("/dashboard"):
        return HttpObservation(200, {
            "brain": {"state": "ONLINE"}, "control_plane": {"health": "ONLINE"},
            "storage": {}, "backup": {}, "workers": {},
        })
    return HttpObservation(200, {
        "brain": {}, "scheduler": {}, "memory": {}, "knowledge": {},
        "platform": {"status": "ONLINE"},
    })


def observe(runtime_value: dict, http=healthy_http):
    adapter = MacShoppingServiceStartObserver(
        repository_facts=FACTS,
        runtime_observer=lambda: runtime_value,
        http_observer=http,
    )
    port: ShoppingServiceStartObservationPort = adapter
    assert callable(port.observe)
    return asyncio.run(adapter.observe())


def states(rows) -> dict[str, str]:
    projection = build_service_start_projection(rows, FACTS)
    return {item["component"]: item["status"] for item in projection["components"]}


def component(rows, name: str) -> dict:
    projection = build_service_start_projection(rows, FACTS)
    return next(item for item in projection["components"] if item["component"] == name)


def test_healthy_running_snapshot_is_complete_and_deterministic() -> None:
    rows = observe(runtime())
    first = build_service_start_projection(rows, FACTS)
    second = build_service_start_projection(rows, FACTS)
    assert {item["status"] for item in first["components"]} == {"RUNNING"}
    assert first["overall_status"] == "RUNNING"
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":"),
    )


def test_runtime_absent_and_unavailable_fail_closed() -> None:
    absent = runtime(
        database={"present": False, "running": False, "healthy": False},
        wordpress={"present": False, "running": False, "healthy": False},
    )
    absent_states = states(observe(absent))
    assert absent_states["mariadb"] == absent_states["wordpress"] == "ABSENT"
    assert absent_states["woocommerce"] == "UNKNOWN"
    unavailable_states = states(observe(runtime(available=False)))
    assert unavailable_states["mariadb"] == unavailable_states["wordpress"] == "UNKNOWN"


def test_runtime_unavailable_diagnostic_survives_into_json() -> None:
    snapshot = runtime(available=False)
    snapshot["error_type"] = "RuntimeUnavailable"
    item = component(observe(snapshot), "mariadb")
    assert item["status"] == "UNKNOWN"
    assert item["diagnostics"] == [
        {"category": category, "completeness": "unavailable",
         "error": "source_unavailable", "source": "container_runtime",
         "reason": "runtime_unavailable"}
        for category in ("binding", "health", "inventory", "lifecycle")
    ]
    assert "RuntimeUnavailable" not in json.dumps(item, sort_keys=True)


def test_docker_inspection_unavailable_is_distinguishable_and_value_free() -> None:
    snapshot = runtime(available=False)
    snapshot["error_type"] = "DockerInspectionUnavailable"
    item = component(observe(snapshot), "wordpress")
    assert {row["reason"] for row in item["diagnostics"]} == {
        "docker_inspection_unavailable"
    }


def test_runtime_not_deployed_is_distinct_from_unavailable() -> None:
    snapshot = runtime(
        database={"present": False, "running": False, "healthy": False},
        wordpress={"present": False, "running": False, "healthy": False},
    )
    snapshot["error_type"] = "RuntimeNotDeployed"
    item = component(observe(snapshot), "mariadb")
    assert item["status"] == "ABSENT"
    assert item["diagnostics"] == [{
        "category": "inventory", "completeness": "complete", "error": "none",
        "source": "container_runtime", "reason": "runtime_not_deployed",
    }]


def test_malformed_runtime_diagnostic_is_value_free() -> None:
    snapshot = runtime(available=False)
    snapshot["error_type"] = "MalformedDockerInspection"
    item = component(observe(snapshot), "wordpress")
    assert item["status"] == "UNKNOWN"
    assert {row["completeness"] for row in item["diagnostics"]} == {"malformed"}
    assert {row["error"] for row in item["diagnostics"]} == {"malformed_evidence"}
    assert {row["reason"] for row in item["diagnostics"]} == {
        "malformed_docker_inspection"
    }


def test_stopped_and_unhealthy_are_distinct() -> None:
    stopped = runtime(database={"present": True, "running": False, "healthy": False})
    assert states(observe(stopped))["mariadb"] == "STOPPED"
    unhealthy = runtime(database={"present": True, "running": True, "healthy": False})
    assert states(observe(unhealthy))["mariadb"] == "UNHEALTHY"


@pytest.mark.parametrize(
    "bad_service",
    [None, {}, {"present": "yes", "running": True, "healthy": True}],
)
def test_malformed_or_missing_container_evidence_is_unknown(bad_service) -> None:
    snapshot = runtime()
    snapshot["database"] = bad_service
    assert states(observe(snapshot))["mariadb"] == "UNKNOWN"


def test_missing_binding_evidence_is_unknown_and_explicit_conflict_wins() -> None:
    missing = runtime()
    missing["publishers"]["wordpress"] = None
    assert states(observe(missing))["wordpress"] == "UNKNOWN"
    conflict = runtime(wordpress_publishers=[{
        "URL": "0.0.0.0", "TargetPort": 80,
        "PublishedPort": 58082, "Protocol": "tcp",
    }])
    assert states(observe(conflict))["wordpress"] == "CONFLICTING"
    assert states(observe(runtime(database_publishers=[{
        "URL": "127.0.0.1", "TargetPort": 3306,
        "PublishedPort": 3306, "Protocol": "tcp",
    }])))["mariadb"] == "CONFLICTING"


def test_explicit_empty_publishers_are_complete_but_omitted_publishers_are_not() -> None:
    explicit = component(observe(runtime(database_publishers=[])), "mariadb")
    assert explicit["status"] == "RUNNING"
    missing = runtime()
    missing["publishers"].pop("database")
    item = component(observe(missing), "mariadb")
    binding = next(row for row in item["diagnostics"] if row["category"] == "binding")
    assert item["status"] == "UNKNOWN"
    assert binding["completeness"] == "incomplete"
    assert binding["error"] == "ambiguous_evidence"


def test_port_collision_remains_conflicting_with_typed_reason() -> None:
    snapshot = runtime(wordpress_publishers=[{
        "URL": "0.0.0.0", "TargetPort": 80,
        "PublishedPort": 58081, "Protocol": "tcp",
    }])
    snapshot["error_type"] = "PortCollision"
    item = component(observe(snapshot), "wordpress")
    assert item["status"] == "CONFLICTING"
    assert {row["reason"] for row in item["diagnostics"]} == {"port_collision"}


def test_woocommerce_requires_its_own_namespace_evidence() -> None:
    def no_woo(url: str) -> HttpObservation:
        if url.endswith("/wp-json/"):
            return HttpObservation(200, {"namespaces": ["wp/v2"]})
        return healthy_http(url)
    result = states(observe(runtime(), no_woo))
    assert result["wordpress"] == "RUNNING"
    assert result["woocommerce"] == "ABSENT"
    item = component(observe(runtime(), no_woo), "woocommerce")
    assert item["diagnostics"][0]["source"] == "loopback_http"


def test_repository_defined_unhealthy_http_states_are_complete() -> None:
    def unhealthy(url: str) -> HttpObservation:
        response = healthy_http(url)
        if url.endswith("/shopping/health"):
            payload = dict(response.payload)
            payload["status"] = "DISABLED"
            return HttpObservation(200, payload)
        if url.endswith("/homepage/status"):
            payload = dict(response.payload)
            payload["platform"] = {"status": "DEGRADED"}
            return HttpObservation(200, payload)
        return response

    result = states(observe(runtime(), unhealthy))
    assert result["aicontrolcenter_shopping"] == "UNHEALTHY"
    assert result["homepage"] == "UNHEALTHY"


def test_malformed_http_schema_is_not_an_unhealthy_state() -> None:
    marker = "must-not-leak"
    def malformed(url: str) -> HttpObservation:
        if url.endswith("/shopping/health"):
            return HttpObservation(200, {"status": "BROKEN", "detail": marker})
        return healthy_http(url)

    rows = observe(runtime(), malformed)
    item = component(rows, "aicontrolcenter_shopping")
    assert item["status"] == "UNKNOWN"
    assert {row["error"] for row in item["diagnostics"]} == {"malformed_evidence"}
    assert {row["reason"] for row in item["diagnostics"]} == {
        "malformed_http_evidence"
    }
    assert marker not in json.dumps(build_service_start_projection(rows, FACTS))


def test_one_invocation_is_bounded_and_has_no_retry() -> None:
    calls = {"runtime": 0, "http": []}
    def runtime_spy():
        calls["runtime"] += 1
        return runtime()
    def http_spy(url: str):
        calls["http"].append(url)
        return healthy_http(url)
    adapter = MacShoppingServiceStartObserver(
        repository_facts=FACTS, runtime_observer=runtime_spy, http_observer=http_spy,
    )
    asyncio.run(adapter.observe())
    assert calls["runtime"] == 1
    assert len(calls["http"]) == len(set(calls["http"])) == 4


def test_observer_has_no_mutation_secret_or_ubuntu_surface() -> None:
    path = ROOT / "ops/macos/shopping/service_start_observer.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    string_literals = {
        node.value.lower() for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    forbidden_commands = {"up", "down", "start", "stop", "restart", "pull", "build", "ssh"}
    assert not forbidden_commands & string_literals
    assert "UbuntuWorkerClient" not in source
    assert "authorization" not in source.lower()
    assert "password" not in source.lower()
    assert "sql" not in source.lower()
    identifiers = {
        node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    assert not {name for name in identifiers if "credential" in name or "secret" in name}
    assert "Request(url, method=\"GET\")" in source


def test_http_unavailable_and_malformed_payload_are_unknown_without_retry() -> None:
    calls = 0
    def broken(_url: str):
        nonlocal calls
        calls += 1
        raise OSError
    rows = observe(runtime(), broken)
    result = states(rows)
    assert result[ShoppingComponent.WOOCOMMERCE.value] == "UNKNOWN"
    assert result[ShoppingComponent.AICONTROLCENTER_SHOPPING.value] == "UNKNOWN"
    assert calls == 4
    assert {row["reason"] for row in component(
        rows, "aicontrolcenter_shopping"
    )["diagnostics"]} == {"loopback_http_unavailable"}


def test_unregistered_http_endpoint_is_unknown_and_diagnostics_do_not_leak_payload() -> None:
    secret_marker = "not-for-projection"
    def wrong_endpoint(url: str) -> HttpObservation:
        if url.endswith("/dashboard"):
            return HttpObservation(404, {"detail": secret_marker})
        return healthy_http(url)
    rows = observe(runtime(), wrong_endpoint)
    item = component(rows, "dashboard")
    assert item["status"] == "UNKNOWN"
    assert {row["error"] for row in item["diagnostics"]} == {"source_unavailable"}
    assert {row["reason"] for row in item["diagnostics"]} == {"http_non_success"}
    assert secret_marker not in json.dumps(build_service_start_projection(rows, FACTS))


def test_non_mac_platform_is_unsupported_without_observer_calls() -> None:
    def forbidden():
        raise AssertionError("runtime observation attempted")
    adapter = MacShoppingServiceStartObserver(
        repository_facts=FACTS,
        runtime_observer=forbidden,
        http_observer=lambda _url: (_ for _ in ()).throw(
            AssertionError("HTTP observation attempted")
        ),
        platform="linux",
    )
    assert set(states(asyncio.run(adapter.observe())).values()) == {"UNKNOWN"}
