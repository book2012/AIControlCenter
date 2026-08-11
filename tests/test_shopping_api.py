from fastapi.testclient import TestClient

from core.api.app import app
from core.api.dependencies.shopping import (
    get_product_draft_query_service,
    get_shopping_runtime,
    get_shopping_service,
)
from core.api.routes import shopping as shopping_routes
from core.shopping.config import ShoppingSettings
from core.shopping.runtime_composition import ShoppingRuntime
from core.shopping.service import ShoppingService


client = TestClient(app)


def test_shopping_routes_are_read_only_and_use_application_runtime():
    shopping_api_routes = [
        route
        for route in shopping_routes.router.routes
        if getattr(route, "path", "").startswith("/shopping")
    ]

    assert shopping_api_routes
    assert all(route.methods == {"GET"} for route in shopping_api_routes)
    assert isinstance(app.state.shopping_runtime, ShoppingRuntime)
    assert get_shopping_runtime.__module__ == "core.api.dependencies.shopping"
    assert get_shopping_service.__module__ == "core.api.dependencies.shopping"
    assert get_product_draft_query_service.__module__ == (
        "core.api.dependencies.shopping"
    )
    assert not hasattr(shopping_routes, "build_default_shopping_service")
    assert not hasattr(shopping_routes, "shopping")


def test_shopping_health_api():
    response = client.get("/shopping/health")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "AIShoppingPlatform"
    assert data["status"] == "ONLINE"
    assert data["runtime"] == "virtual"
    assert data["deployment_target"] == "mac-mini-m4"
    assert data["control_plane"] == "AIControlCenter"
    assert data["write_mode"] == "read_only"


def test_shopping_readiness_api():
    response = client.get("/shopping/readiness")

    assert response.status_code == 200

    data = response.json()

    assert data["ready"] is True
    assert data["status"] == "READY"
    assert data["checks"]["enabled"] is True
    assert data["checks"]["write_mode_supported"] is True
    assert data["checks"]["safe_default_mode"] is True


def test_shopping_capabilities_are_safe_by_default():
    response = client.get("/shopping/capabilities")

    assert response.status_code == 200

    data = response.json()

    assert data["read_catalog"] is True
    assert data["write_catalog"] is False
    assert data["generate_ai_content"] is False
    assert data["execute_automation"] is False
    assert data["approval_required"] is True
    assert data["write_executor_available"] is False
    assert data["production_mutation_authorized"] is False


def test_configured_write_mode_does_not_claim_mutation_authority():
    for write_mode in ("controlled_write", "automated"):
        settings = ShoppingSettings(
            enabled=True,
            environment="test",
            runtime="virtual",
            deployment_target="mac-mini-m4",
            write_mode=write_mode,
            approval_required=True,
            automation_enabled=True,
            ai_enabled=False,
        )

        capabilities = ShoppingService(settings=settings).capabilities()

        assert capabilities["configured_write_mode"] == write_mode
        assert capabilities["write_catalog"] is False
        assert capabilities["write_executor_available"] is False
        assert capabilities["production_mutation_authorized"] is False


def test_invalid_write_mode_is_not_ready():
    settings = ShoppingSettings(
        enabled=True,
        environment="test",
        runtime="virtual",
        deployment_target="mac-mini-m4",
        write_mode="invalid",
        approval_required=True,
        automation_enabled=False,
        ai_enabled=False,
    )

    service = ShoppingService(settings=settings)
    data = service.readiness()

    assert data["ready"] is False
    assert data["status"] == "NOT_READY"
    assert data["checks"]["write_mode_supported"] is False


def test_disabled_shopping_service_reports_disabled():
    settings = ShoppingSettings(
        enabled=False,
        environment="test",
        runtime="virtual",
        deployment_target="mac-mini-m4",
        write_mode="read_only",
        approval_required=True,
        automation_enabled=False,
        ai_enabled=False,
    )

    service = ShoppingService(settings=settings)

    assert service.health()["status"] == "DISABLED"
    assert service.readiness()["ready"] is False
    assert service.capabilities()["read_catalog"] is False


def test_shopping_integration_status():
    response = client.get("/shopping/integrations")

    assert response.status_code == 200

    data = response.json()

    assert data["catalog_adapter"] == "mock"
    assert data["configured"] is True
    assert data["read_only"] is True
    assert data["source"] == "MockCommerceCatalogAdapter"
