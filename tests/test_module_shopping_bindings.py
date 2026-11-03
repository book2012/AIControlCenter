from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from pydantic import SecretBytes

pytest.importorskip("aicc_plugin_shopping", reason="optional shopping wheel required")

from core.modules.composition import create_module_app
from core.modules.shopping_bindings import ShoppingBindings, create_bound_shopping
from core.shopping.config import ShoppingSettings
from core.shopping.runtime_composition import ShoppingRuntime
from core.shopping.service import ShoppingService
from core.shopping.product_drafts.read import ProductDraftQueryService, UnavailableProductDraftReadSource
from core.shopping.product_drafts.runtime import ProductDraftCapability
from core.shopping.order_core.domain import OrderSnapshot
from core.shopping.order_core.service import OrderService
from core.notifications import NotificationPlatform
from core.api.dependencies.customer_session import CustomerSessionBoundary


def runtime():
    settings = ShoppingSettings(True, "fixture", "virtual", "mac-mini-m4", "read_only", True, False, False)
    return ShoppingRuntime(ShoppingService(settings),
        ProductDraftQueryService(UnavailableProductDraftReadSource()),
        ProductDraftCapability(False, False, False, False, "TEST_UNAVAILABLE"))


class Reader:
    def __init__(self):
        self.calls = 0
        now = datetime(2026, 11, 3, tzinfo=timezone.utc)
        self.order = OrderSnapshot("woocommerce", 1, "fixture-1", "fixture-1", "processing", "KRW",
            "fixture-customer", (), Decimal("19000.00"), Decimal("0.00"), now, now, "fixture-v1")
    def list_orders(self, query):
        self.calls += 1
        return (self.order,)
    def read_order(self, order_id):
        self.calls += 1
        return self.order if order_id == 1 else None


def client_for(bindings):
    return TestClient(create_module_app(["shopping"],
        providers={"shopping": lambda: create_bound_shopping(bindings)}))


def test_existing_order_service_is_explicitly_authorized_each_request():
    reader = Reader()
    permitted = {"allow": False}
    bindings = ShoppingBindings(runtime(), authorize=lambda request, scope: permitted["allow"],
        order_service=OrderService(reader), notifications=NotificationPlatform())
    client = client_for(bindings)
    assert client.get("/extensions/shopping/orders").status_code == 403
    assert reader.calls == 0
    permitted["allow"] = True
    result = client.get("/extensions/shopping/orders/1")
    assert result.status_code == 200
    assert result.json()["total"] == "19000.00"
    assert result.headers["cache-control"] == "no-store"
    assert client.get("/extensions/shopping/orders").status_code == 200
    assert client.get("/extensions/shopping/orders/999").status_code == 404
    assert client.get("/extensions/shopping/notifications").status_code == 200
    permitted["allow"] = False
    calls = reader.calls
    assert client.get("/extensions/shopping/orders/1").status_code == 403
    assert reader.calls == calls


@pytest.mark.parametrize("authorize", [None, lambda request, scope: 1])
def test_missing_or_nonboolean_authorization_denies_before_read(authorize):
    reader = Reader()
    client = client_for(ShoppingBindings(runtime(), authorize=authorize, order_service=OrderService(reader)))
    assert client.get("/extensions/shopping/orders").status_code == 403
    assert reader.calls == 0


def test_authorization_exception_is_denied_without_leaking_detail():
    def fail(request, scope):
        raise RuntimeError("secret-path")
    client = client_for(ShoppingBindings(runtime(), authorize=fail))
    response = client.get("/extensions/shopping/orders")
    assert response.status_code == 403 and "secret-path" not in response.text


def test_absent_bindings_are_unavailable_and_legacy_mutations_not_exposed():
    client = client_for(ShoppingBindings(runtime(), authorize=lambda r, s: True))
    for path in ["orders", "notifications"]:
        assert client.get("/extensions/shopping/" + path).status_code == 503
    for path in ["shopping/inquiries", "shopping/auth/session", "shopping/product-drafts"]:
        assert client.get("/extensions/shopping/" + path).status_code == 404
    assert client.post("/extensions/shopping/shopping/inquiries", json={}).status_code == 405
    assert client.get("/extensions/shopping/shopping/products").status_code == 200


def test_bound_session_reuses_existing_deny_without_cookie():
    boundary = CustomerSessionBoundary(service=object(), trusted_origin="https://fixture.test",
        csrf_key=SecretBytes(b"f" * 32), clock=lambda: datetime.now(timezone.utc))
    client = client_for(ShoppingBindings(runtime(), session_boundary=boundary))
    response = client.get("/extensions/shopping/shopping/auth/session")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert client.post("/extensions/shopping/shopping/auth/session", json={}).status_code == 405


def test_provider_exception_does_not_leak_customer_data_or_error():
    class Broken(Reader):
        def list_orders(self, query):
            raise RuntimeError("customer-name-secret")
    client = client_for(ShoppingBindings(runtime(), authorize=lambda r, s: True, order_service=OrderService(Broken())))
    result = client.get("/extensions/shopping/orders")
    assert result.status_code == 503
    assert "customer-name-secret" not in result.text


@pytest.mark.parametrize("field", ["runtime", "session_boundary", "order_service", "notifications"])
def test_wrong_binding_type_fails_closed(field):
    bindings = replace(ShoppingBindings(runtime()), **{field: object()})
    with pytest.raises(TypeError):
        create_bound_shopping(bindings)


def test_twilio_compatibility_exports_preserve_strict_class_identity():
    from core.shopping.adapters.twilio_authenticated_read_secret_composition import TwilioAuthenticatedReadSecretComposition as inner
    from ops.macos.shopping.twilio_authenticated_read_secret_composition import TwilioAuthenticatedReadSecretComposition as outer
    assert inner is outer
