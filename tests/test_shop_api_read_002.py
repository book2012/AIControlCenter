"""Fixture-only read health, failure classification and deterministic errors."""
from copy import deepcopy

import pytest
import requests

from core.shopping.adapters import woocommerce_rest
from core.shopping.adapters.woocommerce_rest import WooCommerceAPIError
from core.shopping.observability.health_probe import HealthFailureCode
from core.shopping.ports import CatalogReadUnavailable
from test_shop_api_read_001 import FakeResponse, PRODUCT, canonical_bytes, make_client


HEALTH_PATH = "/shopping/health/read-path"
PRODUCT_PATHS = ["/shopping/products", "/shopping/products/42"]
FAILURES = [
    (requests.Timeout("PRIVATE_VENDOR_DATA"), "timeout"),
    (requests.ConnectionError("PRIVATE_VENDOR_DATA"), "transport"),
    (requests.RequestException("PRIVATE_VENDOR_DATA"), "transport"),
    (FakeResponse(status=401), "authentication"),
    (FakeResponse(status=403), "authorization"),
    (FakeResponse(status=429), "rate_limit"),
    (FakeResponse(status=500), "dependency_unavailable"),
    (FakeResponse(status=503), "dependency_unavailable"),
    (FakeResponse(status=301), "dependency_unavailable"),
    (FakeResponse(status=204), "dependency_unavailable"),
    (FakeResponse(ValueError("PRIVATE_VENDOR_DATA")), "invalid_payload"),
]


def health_body(failure="none"):
    return {
        "service": "AIShoppingPlatform", "healthy": failure == "none",
        "state": ("HEALTHY" if failure == "none" else
                  "DEGRADED" if failure == "rate_limit" else "UNAVAILABLE"),
        "failure_code": failure, "read_only": True,
    }


@pytest.mark.parametrize("upstream,failure", FAILURES)
@pytest.mark.parametrize("operation", ["list", "detail", "health"])
def test_adapter_classifies_failures_without_raw_transport_context(upstream, failure, operation):
    _, session, service = make_client(upstream)
    with pytest.raises(WooCommerceAPIError) as caught:
        if operation == "list":
            service.catalog.list_products(1, 1)
        elif operation == "detail":
            service.catalog.get_product("42")
        else:
            service.catalog.health()
    assert caught.value.failure_code.value == failure
    assert "PRIVATE_VENDOR_DATA" not in str(caught.value)
    if isinstance(upstream, requests.RequestException):
        assert caught.value.__context__ is None
        assert caught.value.__cause__ is None
    assert len(session.calls) == 1


@pytest.mark.parametrize("upstream,failure", FAILURES)
def test_read_health_exposes_only_stable_failure_metadata(upstream, failure):
    client, session, _ = make_client(upstream, upstream)
    first = client.get(HEALTH_PATH)
    second = client.get(HEALTH_PATH)
    assert first.status_code == second.status_code == 503
    assert first.content == second.content == canonical_bytes(health_body(failure))
    assert first.headers["content-type"] == "application/json"
    assert len(session.calls) == 2
    assert all(call["params"] == {
        "context": "view", "status": "publish", "page": 1, "per_page": 1,
        "orderby": "id", "order": "asc",
    } for call in session.calls)


@pytest.mark.parametrize("payload,total", [([PRODUCT], "1"), ([], "0")])
def test_health_validates_nonempty_and_empty_catalogs(payload, total):
    before = deepcopy(payload)
    client, session, service = make_client(FakeResponse(payload, total=total),
                                          FakeResponse(payload, total=total))
    assert service.catalog.health()["healthy"] is True
    response = client.get(HEALTH_PATH)
    assert response.status_code == 200
    assert response.content == canonical_bytes(health_body())
    assert len(session.calls) == 2
    assert payload == before


@pytest.mark.parametrize("payload,total", [
    ({"message": "PRIVATE_VENDOR_DATA"}, "0"), ([None], "1"),
    ([PRODUCT], None), ([PRODUCT], "bad"), ([PRODUCT], "0"), ([], "1"),
    ([PRODUCT, PRODUCT], "2"), ([{**PRODUCT, "status": "draft"}], "1"),
    ([{**PRODUCT, "price": "NaN"}], "1"),
    ([{**PRODUCT, "stock_status": {}}], "1"),
    ([{**PRODUCT, "name": "\ud800"}], "1"),
])
def test_malformed_http_200_is_observable_and_never_healthy(payload, total):
    client, session, service = make_client(FakeResponse(payload, total=total),
                                          FakeResponse(payload, total=total))
    with pytest.raises(WooCommerceAPIError) as caught:
        service.catalog.health()
    assert caught.value.failure_code is HealthFailureCode.SCHEMA_MISMATCH
    response = client.get(HEALTH_PATH)
    assert response.status_code == 503
    assert response.content == canonical_bytes(health_body("schema_mismatch"))
    assert len(session.calls) == 2


@pytest.mark.parametrize("field,value", [
    ("id", 43), ("status", {}), ("price", "Infinity"), ("name", None),
    ("categories", "bad"), ("images", [None]),
])
def test_malformed_detail_classification(field, value):
    _, _, service = make_client(FakeResponse({**PRODUCT, field: value}))
    with pytest.raises(CatalogReadUnavailable) as caught:
        service.get_product("42")
    assert caught.value.failure_code is HealthFailureCode.SCHEMA_MISMATCH


def test_health_is_fresh_and_does_not_cache_or_fallback_after_failure():
    client, session, _ = make_client(FakeResponse([PRODUCT]), FakeResponse(status=503),
                                    FakeResponse([], total="0"))
    assert [client.get(HEALTH_PATH).status_code for _ in range(3)] == [200, 503, 200]
    assert len(session.calls) == 3


def test_disabled_health_fails_closed_and_liveness_remains_configuration_only():
    client, session, _ = make_client(enabled=False)
    assert client.get("/shopping/health").json()["status"] == "DISABLED"
    assert client.get("/shopping/readiness").json()["ready"] is False
    response = client.get(HEALTH_PATH)
    assert response.status_code == 503
    assert response.content == canonical_bytes(health_body("configuration"))
    assert session.calls == []


def test_enabled_liveness_and_readiness_do_not_probe_upstream():
    client, session, _ = make_client()
    assert client.get("/shopping/health").status_code == 200
    assert client.get("/shopping/readiness").status_code == 200
    assert session.calls == []


def test_openapi_describes_health_and_canonical_product_errors():
    client, session, _ = make_client()
    paths = client.get("/openapi.json").json()["paths"]
    for code in ("200", "503"):
        schema = paths[HEALTH_PATH]["get"]["responses"][code]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ShoppingReadPathHealthResponse"}
    for path, codes in [("/shopping/products", ("422", "503")),
                        ("/shopping/products/{product_id}", ("404", "422", "503"))]:
        for code in codes:
            schema = paths[path]["get"]["responses"][code]["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/ProductReadErrorResponse"}
    assert session.calls == []


def test_other_shopping_query_validation_retains_framework_contract():
    client, session, _ = make_client()
    response = client.get("/shopping/search?page=0")
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert session.calls == []


def test_health_policy_denial_prevents_io(monkeypatch):
    from core.shopping.governance.external_read_policy import evaluate_external_read

    denial = evaluate_external_read(provider="woocommerce", method="POST", path="/wp-json/wc/v3/products")
    monkeypatch.setattr(woocommerce_rest, "evaluate_external_read", lambda **kwargs: denial)
    client, session, _ = make_client()
    response = client.get(HEALTH_PATH)
    assert response.status_code == 503
    assert response.content == canonical_bytes(health_body("authorization"))
    assert session.calls == []


@pytest.mark.parametrize("path", PRODUCT_PATHS)
def test_product_failures_preserve_exact_canonical_public_contract(path):
    client, session, _ = make_client(FakeResponse(status=401), FakeResponse(ValueError("PRIVATE_VENDOR_DATA")))
    expected = canonical_bytes({"detail": {"code": "shopping_catalog_unavailable"}})
    for _ in range(2):
        response = client.get(path)
        assert response.status_code == 503
        assert response.content == expected
    assert len(session.calls) == 2


@pytest.mark.parametrize("path", [
    "/shopping/products?page=bad", "/shopping/products?page=0",
    "/shopping/products?page_size=101", "/shopping/products?page_size=NaN",
    "/shopping/products?page_size=0", "/shopping/products/abc", "/shopping/products/01",
])
def test_framework_and_service_query_errors_share_canonical_json_without_input_echo(path):
    client, session, _ = make_client()
    response = client.get(path)
    assert response.status_code == 422
    assert response.content == canonical_bytes({"detail": {"code": "shopping_invalid_product_query"}})
    assert session.calls == []


def test_not_found_is_canonical_and_collection_404_is_unavailable():
    client, _, _ = make_client(FakeResponse(status=404), FakeResponse(status=404))
    response = client.get("/shopping/products/42")
    assert response.status_code == 404
    assert response.content == canonical_bytes({"detail": {
        "code": "shopping_product_not_found", "product_id": "42",
    }})
    assert client.get(HEALTH_PATH).content == canonical_bytes(health_body("dependency_unavailable"))


class BrokenCatalog:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def list_products(self, page, page_size):
        if self.error:
            raise self.error
        return self.result

    def get_product(self, product_id):
        return self.list_products(1, 1)


@pytest.mark.parametrize("path", [*PRODUCT_PATHS, HEALTH_PATH])
def test_unexpected_adapter_exception_is_sanitized_and_classified_unknown(path):
    client, session, service = make_client()
    service.catalog = BrokenCatalog(error=RuntimeError("PRIVATE_VENDOR_DATA"))
    response = client.get(path)
    assert response.status_code == 503
    expected = health_body("unknown") if path == HEALTH_PATH else {"detail": {"code": "shopping_catalog_unavailable"}}
    assert response.content == canonical_bytes(expected)
    assert session.calls == []


@pytest.mark.parametrize("result", [None, {}, (None, 0), ([object()], 1), ([], True), ([], 1), ([], -1)])
def test_invalid_replacement_catalog_observations_fail_closed(result):
    client, _, service = make_client()
    service.catalog = BrokenCatalog(result=result)
    response = client.get(HEALTH_PATH)
    assert response.status_code == 503
    assert response.content == canonical_bytes(health_body("schema_mismatch"))


def test_invalid_replacement_detail_is_not_an_unhandled_attribute_error():
    client, _, service = make_client()
    service.catalog = BrokenCatalog(result={"id": "42"})
    assert client.get("/shopping/products/42").status_code == 503


@pytest.mark.parametrize("path", [*PRODUCT_PATHS, HEALTH_PATH])
def test_unpaired_upstream_unicode_is_unavailable_instead_of_render_failure(path):
    payload = {**PRODUCT, "name": "\ud800"}
    client, _, _ = make_client(FakeResponse(payload if path.endswith("/42") else [payload]))
    response = client.get(path)
    assert response.status_code == 503
    if path == HEALTH_PATH:
        assert response.content == canonical_bytes(health_body("schema_mismatch"))


@pytest.mark.parametrize("code", ["PRIVATE_VENDOR_DATA", "none", "latency", None, {}])
def test_exception_failure_codes_cannot_inject_arbitrary_public_values(code):
    client, _, service = make_client()
    service.catalog = BrokenCatalog(error=CatalogReadUnavailable("PRIVATE_VENDOR_DATA", failure_code=code))
    assert client.get(HEALTH_PATH).content == canonical_bytes(health_body("unknown"))


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", [*PRODUCT_PATHS, HEALTH_PATH])
def test_no_write_method_or_adapter_invocation(method, path):
    client, session, _ = make_client()
    assert client.request(method, path).status_code == 405
    assert session.calls == []
