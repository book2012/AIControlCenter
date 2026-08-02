from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api.routes import shopping
from core.dashboard.api import DashboardAPI
from core.shopping.product_drafts.read import (
    InMemoryProductDraftSnapshotSource, ProductDraftQueryService,
)


def test_product_draft_routes_are_get_only_and_default_is_unavailable():
    routes = [route for route in shopping.router.routes if "product-drafts" in route.path]
    assert [route.path for route in routes] == [
        "/shopping/product-drafts", "/shopping/product-drafts/{draft_id}",
        "/shopping/product-drafts/{draft_id}/revisions/{revision_id}",
    ]
    assert all(route.methods == {"GET"} for route in routes)
    app = FastAPI()
    app.include_router(shopping.router)
    response = TestClient(app).get("/shopping/product-drafts")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "product_draft_read_unavailable"


def test_route_dependency_can_be_replaced_with_empty_available_source():
    app = FastAPI()
    app.include_router(shopping.router)
    app.dependency_overrides[shopping.get_product_draft_query_service] = (
        lambda: ProductDraftQueryService(InMemoryProductDraftSnapshotSource())
    )
    response = TestClient(app).get("/shopping/product-drafts")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_dashboard_optional_injection_preserves_shape_and_isolates_failure():
    base = DashboardAPI().status([], include_datacenter=False)
    assert "product_draft_review" not in base
    injected = DashboardAPI(product_drafts=lambda: {"status": "AVAILABLE"}).status([], include_datacenter=False)
    assert injected["product_draft_review"] == {"status": "AVAILABLE"}
    assert set(base).issubset(injected)
    isolated = DashboardAPI(product_drafts=lambda: (_ for _ in ()).throw(RuntimeError("private"))).status([], include_datacenter=False)
    assert isolated["product_draft_review"]["status"] == "UNAVAILABLE"
    assert "private" not in str(isolated)
