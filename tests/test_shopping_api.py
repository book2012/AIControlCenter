from fastapi.testclient import TestClient

from core.api.app import app
from core.shopping.config import ShoppingSettings
from core.shopping.service import ShoppingService


client = TestClient(app)


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
