from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api.dependencies.audit import get_audit_query_service
from core.api.app import create_app
from core.api.routes import dashboard, shopping
from core.shopping.product_drafts.read import (
    InMemoryProductDraftSnapshotSource, ProductDraftQueryService, UnavailableProductDraftReadSource,
)
from core.shopping.product_drafts.runtime import (
    FailClosedProductDraftReadSource,
    ProductDraftCapability,
)
from core.shopping.runtime_composition import ShoppingRuntime
from core.shopping.secure_runtime import build_default_shopping_service


def _app(query_service):
    app = FastAPI()
    runtime = ShoppingRuntime(
        build_default_shopping_service(environment={}), query_service,
        ProductDraftCapability(True, True, True, True, "AVAILABLE"),
    )
    app.state.shopping_runtime = runtime
    app.include_router(shopping.router)
    return app, runtime


def test_app_creation_does_not_create_product_draft_database(tmp_path, monkeypatch):
    data_root = tmp_path / "configured-but-unsafe-for-production"
    monkeypatch.setenv("AICONTROLCENTER_DATA_ROOT", str(data_root))
    target = data_root / "shopping" / "product-drafts.sqlite3"
    app = create_app()
    assert app.state.shopping_runtime.product_draft_capability.durable_reads_available is False
    assert not target.exists()
    assert not data_root.exists()


def test_shopping_get_uses_composed_runtime_without_provider_configuration():
    app, runtime = _app(ProductDraftQueryService(InMemoryProductDraftSnapshotSource()))
    response = TestClient(app).get("/shopping/product-drafts")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert runtime.catalog_service.capabilities()["read_catalog"] is True
    assert runtime.product_draft_mutation_available is False


def test_dashboard_and_shopping_share_query_service(monkeypatch):
    service = ProductDraftQueryService(UnavailableProductDraftReadSource())
    app, runtime = _app(service)
    app.include_router(dashboard.router)
    app.dependency_overrides[get_audit_query_service] = lambda: object()
    monkeypatch.setattr(dashboard, "build_governance_audit_dashboard_read_model", lambda value: type("M", (), {"to_dict": lambda self: {}})())
    monkeypatch.setattr(dashboard, "build_governance_audit_operations_dashboard_payload", lambda: {})
    response = TestClient(app).get("/dashboard")
    assert response.status_code == 200
    assert response.json()["product_draft_review"]["status"] == "UNAVAILABLE"
    assert runtime.product_draft_query_service is service


def test_product_draft_routes_are_get_only_and_mutation_absent():
    routes = [route for route in shopping.router.routes if "product-drafts" in route.path]
    assert routes
    assert all(route.methods == {"GET"} for route in routes)
    app, _ = _app(ProductDraftQueryService(InMemoryProductDraftSnapshotSource()))
    assert TestClient(app).post("/shopping/product-drafts").status_code == 405


class _CorruptedReadSource:
    def is_available(self):
        return True

    @staticmethod
    def _fail():
        raise ValueError("raw SQL /private/product-drafts.sqlite3 secret detail")

    def list_revisions(self):
        self._fail()

    def fetch_current(self, draft_id):
        self._fail()

    def fetch_revision(self, draft_id, revision_id):
        self._fail()


def _corrupted_query_service():
    return ProductDraftQueryService(
        FailClosedProductDraftReadSource(_CorruptedReadSource())
    )


def test_product_draft_http_reads_sanitize_post_startup_corruption():
    app, _ = _app(_corrupted_query_service())
    client = TestClient(app)

    for path in (
        "/shopping/product-drafts",
        "/shopping/product-drafts/draft",
        "/shopping/product-drafts/draft/revisions/r1",
    ):
        response = client.get(path)
        assert response.status_code == 503
        assert response.json() == {
            "detail": {
                "code": "product_draft_read_unavailable",
                "retryable": True,
            }
        }
        assert "raw SQL" not in response.text
        assert "/private/product-drafts.sqlite3" not in response.text
        assert "secret detail" not in response.text

    capabilities = client.get("/shopping/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["read_catalog"] is True


def test_dashboard_isolates_post_startup_product_draft_corruption(monkeypatch):
    app, _ = _app(_corrupted_query_service())
    app.include_router(dashboard.router)
    app.dependency_overrides[get_audit_query_service] = lambda: object()
    monkeypatch.setattr(
        dashboard,
        "build_governance_audit_dashboard_read_model",
        lambda value: type("M", (), {"to_dict": lambda self: {}})(),
    )
    monkeypatch.setattr(
        dashboard, "build_governance_audit_operations_dashboard_payload", lambda: {}
    )

    response = TestClient(app).get("/dashboard")

    assert response.status_code == 200
    assert response.json()["product_draft_review"]["status"] == "UNAVAILABLE"
    assert "raw SQL" not in response.text
    assert "/private/product-drafts.sqlite3" not in response.text


def test_catalog_route_uses_runtime_owned_service():
    catalog = build_default_shopping_service(environment={})

    class CatalogSpy:
        def __init__(self, wrapped):
            self.wrapped = wrapped
            self.health_calls = 0

        def health(self):
            self.health_calls += 1
            return self.wrapped.health()

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    spy = CatalogSpy(catalog)
    app = FastAPI()
    app.state.shopping_runtime = ShoppingRuntime(
        spy,
        ProductDraftQueryService(InMemoryProductDraftSnapshotSource()),
        ProductDraftCapability(True, True, True, True, "AVAILABLE"),
    )
    app.include_router(shopping.router)

    response = TestClient(app).get("/shopping/health")

    assert response.status_code == 200
    assert spy.health_calls == 1
