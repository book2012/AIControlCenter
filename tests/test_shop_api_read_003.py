"""Fixture-only operational telemetry and Dashboard consumption; no runtime I/O."""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.api.dependencies.shopping import get_shopping_service
from core.api.routes import dashboard as dashboard_route
from core.dashboard.api import DashboardAPI
from core.dashboard.shopping_read_telemetry import unavailable_shopping_read_telemetry_dashboard_payload
from core.shopping.contracts.schema_registry import load_schema_registry
from core.shopping.contracts.validation import validate_contract_payload
from core.shopping.observability.health_probe import HealthFailureCode
from core.shopping.observability.read_telemetry import (
    CatalogReadOperation, CatalogReadOutcome, CatalogReadTelemetry,
)
from core.shopping.ports import CatalogReadQueryError
from core.shopping.service import ShoppingService
from test_shop_api_read_001 import FakeResponse, PRODUCT, SETTINGS, canonical_bytes, make_client
from test_shop_api_read_002 import BrokenCatalog, FAILURES


NOW = datetime(2026, 9, 13, tzinfo=timezone.utc)
DASHBOARD_PATH = "/dashboard/shopping/read-telemetry"
PATHS = [
    ("/shopping/products", "list_products"),
    ("/shopping/products/42", "get_product"),
    ("/shopping/health/read-path", "read_path_health"),
]


class Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 12_345_678
        return self.value


def fixture_client(*responses, enabled=True, clock=None):
    client, session, original = make_client(*responses, enabled=enabled)
    service = ShoppingService(
        original.settings, original.catalog,
        read_telemetry=CatalogReadTelemetry(clock_ns=clock or Clock(), utc_now=lambda: NOW),
    )
    client.app.dependency_overrides[get_shopping_service] = lambda: service
    client.app.include_router(dashboard_route.router)
    return client, session, service


def entry(service, operation):
    return service.read_path_telemetry().to_json()["operations"][operation]


def test_unobserved_and_repeated_dashboard_reads_are_local_and_deterministic():
    client, session, service = fixture_client()
    first = client.get(DASHBOARD_PATH)
    assert first.status_code == 200
    assert first.content == client.get(DASHBOARD_PATH).content
    payload = first.json()
    assert payload["status"] == "UNAVAILABLE"
    assert payload["error"] is None
    assert payload["telemetry"]["total"] == 0
    assert payload["telemetry"]["health"]["empty"] is True
    assert set(payload["telemetry"]["operations"]) == {operation for _, operation in PATHS}
    assert all(value["last"] is None for value in payload["telemetry"]["operations"].values())
    assert service.read_path_telemetry().health.total == 0
    assert session.calls == []


@pytest.mark.parametrize("path,operation", PATHS)
@pytest.mark.parametrize("upstream,failure", FAILURES + [
    (FakeResponse([None]), "schema_mismatch"),
    (RuntimeError("PRIVATE_VENDOR_DATA"), "unknown"),
])
def test_outcome_failure_latency_and_health_reuse_existing_contracts(path, operation, upstream, failure):
    client, session, service = fixture_client(upstream)
    assert client.get(path).status_code == 503
    observed = entry(service, operation)
    assert observed["total"] == observed["outcomes"]["unavailable"] == 1
    assert observed["failures"][failure] == 1
    assert sum(observed["failures"].values()) == 1
    probe = observed["last"]["probe"]
    assert probe["failure_code"] == failure
    assert probe["latency_ms"] == probe["health"]["latency_ms"] == 12
    assert probe["state"] == ("DEGRADED" if failure == "rate_limit" else "UNAVAILABLE")
    assert probe["health"]["checked_at"] == "2026-09-13T00:00:00Z"
    validate_contract_payload(registry=load_schema_registry(), contract_name="AdapterHealth",
                              payload=probe["health"])
    dashboard = client.get(DASHBOARD_PATH)
    assert dashboard.json()["telemetry"] == service.read_path_telemetry().to_json()
    assert dashboard.json()["status"] == probe["state"]
    assert dashboard.content == client.get(DASHBOARD_PATH).content
    for private in (b"PRIVATE_VENDOR_DATA", b"fixture-key", b"fixture-value", b"commerce.example", b"/42"):
        assert private not in dashboard.content
    assert service.read_path_telemetry().total == len(session.calls) == 1


def test_success_empty_not_found_and_probe_are_each_counted_once():
    client, session, service = fixture_client(
        FakeResponse([], total="0"), FakeResponse(status=404), FakeResponse([PRODUCT]),
    )
    assert [client.get(path).status_code for path, _ in PATHS] == [200, 404, 200]
    snapshot = service.read_path_telemetry()
    assert snapshot.total == len(session.calls) == 3
    assert snapshot.health.healthy == 3
    assert entry(service, "list_products")["outcomes"]["success"] == 1
    assert entry(service, "get_product")["outcomes"]["not_found"] == 1
    assert entry(service, "read_path_health")["outcomes"]["success"] == 1
    for _, operation in PATHS:
        observed = entry(service, operation)
        assert observed["total"] == 1
        assert sum(observed["failures"].values()) == 0
        assert observed["last"]["probe"]["failure_code"] == "none"


def test_health_aggregates_latest_per_operation_and_recovery_keeps_failure_count():
    client, _, service = fixture_client(FakeResponse(status=429), FakeResponse(PRODUCT),
                                        FakeResponse(status=503), FakeResponse([], total="0"))
    assert client.get("/shopping/products").status_code == 503
    assert client.get("/shopping/products/42").status_code == 200
    assert service.read_path_telemetry().health.overall_state.value == "DEGRADED"
    assert client.get("/shopping/products").status_code == 503
    assert service.read_path_telemetry().health.overall_state.value == "UNAVAILABLE"
    old = service.read_path_telemetry()
    old_json = old.to_json()
    assert client.get("/shopping/products").status_code == 200
    assert service.read_path_telemetry().health.overall_state.value == "HEALTHY"
    assert old.to_json() == old_json
    assert old.health.overall_state.value == "UNAVAILABLE"
    observed = entry(service, "list_products")
    assert observed["total"] == 3
    assert observed["failures"]["rate_limit"] == observed["failures"]["dependency_unavailable"] == 1
    assert observed["last"]["outcome"] == "success"


def test_invalid_service_query_is_not_dependency_health_and_framework_rejection_is_not_service_invocation():
    client, session, service = fixture_client(FakeResponse(status=503))
    assert client.get("/shopping/products/42").status_code == 503
    assert client.get("/shopping/products/abc").status_code == 422
    with pytest.raises(CatalogReadQueryError):
        service.list_products(0, 20)
    health = service.read_path_telemetry().health
    assert health.empty is False
    assert health.unavailable == 1
    for operation in ("get_product", "list_products"):
        observed = entry(service, operation)
        assert observed["last"] == {"outcome": "invalid_query", "probe": None}
        assert observed["outcomes"]["invalid_query"] == 1
        assert sum(observed["failures"].values()) == (1 if operation == "get_product" else 0)
    before = service.read_path_telemetry().to_json()
    assert client.get("/shopping/products?page=bad").status_code == 422
    assert client.get("/shopping/health").status_code == 200
    assert client.get("/shopping/readiness").status_code == 200
    assert before == service.read_path_telemetry().to_json()
    assert len(session.calls) == 1


@pytest.mark.parametrize("disabled", [True, False])
def test_configuration_and_policy_denials_are_observed_without_upstream(disabled, monkeypatch):
    from core.shopping.adapters import woocommerce_rest
    from core.shopping.governance.external_read_policy import evaluate_external_read

    if not disabled:
        denial = evaluate_external_read(provider="woocommerce", method="POST", path="/wp-json/wc/v3/products")
        monkeypatch.setattr(woocommerce_rest, "evaluate_external_read", lambda **kwargs: denial)
    client, session, service = fixture_client(enabled=not disabled)
    failure = "configuration" if disabled else "authorization"
    for path, operation in PATHS:
        assert client.get(path).status_code == 503
        assert entry(service, operation)["last"]["probe"]["failure_code"] == failure
    assert service.read_path_telemetry().total == 3
    assert session.calls == []


def test_fixed_probe_query_rejection_is_unknown_failure_not_success():
    client, _, service = fixture_client()
    service.catalog = BrokenCatalog(error=CatalogReadQueryError("PRIVATE_VENDOR_DATA"))
    assert client.get("/shopping/health/read-path").status_code == 503
    observed = entry(service, "read_path_health")
    assert observed["outcomes"]["unavailable"] == observed["failures"]["unknown"] == 1


def test_unavailable_without_failure_records_unknown_observation():
    telemetry = CatalogReadTelemetry(clock_ns=Clock(), utc_now=lambda: NOW)
    telemetry.record(CatalogReadOperation.LIST, CatalogReadOutcome.UNAVAILABLE,
                     None, telemetry.start())
    snapshot = telemetry.snapshot()
    observed = snapshot.to_json()["operations"]["list_products"]
    assert snapshot.total == observed["total"] == observed["outcomes"]["unavailable"] == 1
    assert observed["failures"][HealthFailureCode.UNKNOWN.value] == 1
    assert sum(observed["failures"].values()) == 1
    assert observed["last"]["outcome"] == "unavailable"
    assert observed["last"]["probe"]["failure_code"] == HealthFailureCode.UNKNOWN.value
    assert observed["last"]["probe"]["state"] == "UNAVAILABLE"
    assert snapshot.health.total == snapshot.health.unavailable == 1


def test_same_fixtures_and_clocks_produce_identical_telemetry_and_detached_json():
    results = []
    for _ in range(2):
        client, _, service = fixture_client(FakeResponse([PRODUCT]))
        assert client.get("/shopping/products").status_code == 200
        results.append(client.get(DASHBOARD_PATH).content)
        assert not any(private in results[-1] for private in
                       (b"VENDOR_ONLY", b"cotton-shirt", b"images.example", "코튼 셔츠".encode()))
        projection = service.read_path_telemetry().to_json()
        projection["operations"]["list_products"]["total"] = 99
        projection["health"]["adapters"].clear()
        assert entry(service, "list_products")["total"] == 1
        assert service.read_path_telemetry().health.total == 1
    assert results[0] == results[1]


@pytest.mark.parametrize("clock_values", [(10, 5), (None, 1), (True, 2), (-1, 2)])
def test_invalid_or_backwards_clock_does_not_fabricate_latency_or_change_read(clock_values):
    values = iter(clock_values)
    client, _, service = fixture_client(FakeResponse([PRODUCT]), clock=lambda: next(values))
    assert client.get("/shopping/products").status_code == 200
    probe = entry(service, "list_products")["last"]["probe"]
    assert probe["latency_ms"] is None
    assert probe["state"] == "HEALTHY"


def test_recording_failure_cannot_override_success_or_failure(monkeypatch):
    client, _, service = fixture_client(FakeResponse([], total="0"), FakeResponse(status=503))

    def broken(*args, **kwargs):
        raise RuntimeError("PRIVATE_VENDOR_DATA")

    monkeypatch.setattr(CatalogReadTelemetry, "record", broken)
    assert client.get("/shopping/products").status_code == 200
    response = client.get("/shopping/products")
    assert response.status_code == 503
    assert response.content == canonical_bytes({"detail": {"code": "shopping_catalog_unavailable"}})
    assert service.read_path_telemetry().total == 0


def test_concurrent_service_reads_publish_atomic_counts_with_bounded_retention():
    service = ShoppingService(SETTINGS, BrokenCatalog(result=([], 0)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: service.list_products(1, 1), range(240)))
    assert all(result["items"] == [] for result in results)
    snapshot = service.read_path_telemetry().to_json()
    assert snapshot["total"] == 240
    assert len(snapshot["operations"]) == 3
    assert snapshot["operations"]["list_products"]["outcomes"]["success"] == 240
    assert snapshot["health"]["counts"]["total"] == 1
    assert ShoppingService(SETTINGS, BrokenCatalog(result=([], 0))).read_path_telemetry().total == 0


def dashboard_api(**kwargs):
    status = SimpleNamespace(status=lambda: {})
    summary = SimpleNamespace(summary=lambda: {})
    return DashboardAPI(snapshot=SimpleNamespace(collect=lambda workers: {}), brain=status,
                        storage=summary, backup=summary, datacenter=status, control_plane=status, **kwargs)


def test_dashboard_failure_isolation_and_optional_shape():
    assert "shopping_read_telemetry" not in dashboard_api().status()
    api = dashboard_api(shopping_read_telemetry=lambda: "PRIVATE_VENDOR_DATA")
    result = api.status()
    assert result["shopping_read_telemetry"] == unavailable_shopping_read_telemetry_dashboard_payload()
    assert result["brain"] == {}
    assert "PRIVATE_VENDOR_DATA" not in str(result)


def test_dedicated_dashboard_projection_failure_is_sanitized(monkeypatch):
    client, session, service = fixture_client()

    def broken():
        raise RuntimeError("PRIVATE_VENDOR_DATA")

    monkeypatch.setattr(service, "read_path_telemetry", broken)
    result = client.get(DASHBOARD_PATH)
    assert result.json() == unavailable_shopping_read_telemetry_dashboard_payload()
    assert session.calls == []


def test_dashboard_default_wiring_shares_runtime_service_and_adds_no_catalog_read(monkeypatch):
    from core.shopping.runtime_composition import ShoppingRuntime

    client, session, service = fixture_client(FakeResponse([], total="0"))
    client.app.dependency_overrides.clear()
    client.app.state.shopping_runtime = ShoppingRuntime(service, SimpleNamespace(), SimpleNamespace())
    client.app.dependency_overrides[dashboard_route.get_audit_query_service] = lambda: SimpleNamespace()
    monkeypatch.setattr(dashboard_route, "DashboardAPI", dashboard_api)
    monkeypatch.setattr(dashboard_route, "build_product_draft_dashboard_payload", lambda service: {})
    monkeypatch.setattr(dashboard_route, "build_governance_audit_dashboard_read_model",
                        lambda service: SimpleNamespace(to_dict=lambda: {}))
    monkeypatch.setattr(dashboard_route, "build_governance_audit_operations_dashboard_payload", lambda: {})
    payload = client.get("/dashboard").json()
    assert payload["shopping_management"]["summary"]["catalog_total"] == 0
    telemetry = payload["shopping_read_telemetry"]
    assert telemetry == client.get(DASHBOARD_PATH).json()
    assert telemetry["telemetry"]["total"] == len(session.calls) == 1


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_dashboard_telemetry_is_get_only(method):
    client, session, service = fixture_client()
    assert client.request(method, DASHBOARD_PATH).status_code == 405
    assert service.read_path_telemetry().total == 0
    assert session.calls == []


def test_new_projection_and_collector_have_no_vendor_transport_or_persistence_imports():
    for path in ("core/dashboard/shopping_read_telemetry.py", "core/dashboard/api.py",
                 "core/api/routes/dashboard.py", "core/shopping/observability/read_telemetry.py"):
        tree = ast.parse(Path(path).read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(token in module.lower() for module in imports for token in
                       ("woocommerce", "requests", "httpx", "urllib", "sqlite", "subprocess"))
