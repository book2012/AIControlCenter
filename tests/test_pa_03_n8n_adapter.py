import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.capabilities.service import CapabilityStatusService
from integrations.n8n import N8nAdapter, N8nConfiguration
from integrations.n8n.composition import build_n8n_status_service


def observe(configuration=None, observer=None):
    adapter = N8nAdapter(configuration or N8nConfiguration(), observer)
    return adapter.observe().to_dict()


def test_default_manifest_state_is_truthful_and_value_free(monkeypatch):
    monkeypatch.setenv("N8N_ENDPOINT", "https://user:secret@example.invalid/?token=private")
    monkeypatch.setenv("N8N_API_KEY", "credential-value")
    result = build_n8n_status_service().status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["available"] is result["healthy"] is result["ready"] is False
    assert result["configuration"] == {
        "status": "UNKNOWN", "configuration_configured": None,
        "authentication_configured": None,
    }
    assert result["runtime"] == {"kind": "UNKNOWN", "transport": "UNKNOWN"}
    assert all(value not in json.dumps(result) for value in ("secret", "private", "credential-value"))


def test_unavailable_observer_and_unknown_configuration_fail_closed():
    unknown = observe(N8nConfiguration(deployment_status="PRODUCTION"))
    assert unknown["status"] == "UNAVAILABLE"
    assert unknown["error"] == {"error_type": "ConfigurationEvidenceUnknown"}
    configured = observe(N8nConfiguration("PRODUCTION", True, True))
    assert configured["error"] == {"error_type": "ObserverNotConfigured"}


def test_malformed_manifest_fails_closed(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("not-json")
    result = build_n8n_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}


@pytest.mark.parametrize("identity_count", [0, 2])
def test_missing_or_duplicate_identity_fails_closed(tmp_path, identity_count):
    canonical = json.loads(Path("config/services/mac-standalone-production.json").read_text())
    entry = next(item for item in canonical["services"] if item["service_id"] == "n8n")
    canonical["services"] = [
        item for item in canonical["services"] if item["service_id"] != "n8n"
    ] + [entry] * identity_count
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(canonical))
    result = build_n8n_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}


def test_configured_unconfigured_and_unknown_evidence():
    assert observe(N8nConfiguration("PRODUCTION", False))["status"] == "NOT_CONFIGURED"
    configured = observe(N8nConfiguration("PRODUCTION", True), lambda: {"healthy": True, "ready": True})
    assert configured["status"] == "AVAILABLE"
    assert observe(N8nConfiguration("UNKNOWN", True))["status"] == "UNAVAILABLE"


@pytest.mark.parametrize("payload", [
    {}, {"healthy": True}, {"healthy": "yes", "ready": True},
    {"healthy": True, "ready": True, "token": "secret"},
])
def test_malformed_observer_payload_is_rejected_without_values(payload):
    result = observe(N8nConfiguration("PRODUCTION", True, True), lambda: payload)
    assert result["error"] == {"error_type": "MalformedObservation"}
    assert "secret" not in repr(result)


@pytest.mark.parametrize("error,error_type", [
    (TimeoutError("private"), "TimeoutError"),
    (ConnectionError("private"), "ConnectionError"),
])
def test_transport_failures_are_value_free(error, error_type):
    def failure():
        raise error
    result = observe(N8nConfiguration("PRODUCTION", True, True), failure)
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": error_type}
    assert "private" not in repr(result)


def test_available_and_degraded_normalization():
    config = N8nConfiguration("PRODUCTION", True, True, "injected", "injected")
    assert observe(config, lambda: {"healthy": True, "ready": True})["status"] == "AVAILABLE"
    degraded = observe(config, lambda: {"healthy": True, "ready": False})
    assert degraded["status"] == "DEGRADED"
    assert degraded["available"] is False
    assert degraded["healthy"] is True
    assert degraded["ready"] is False


def test_get_only_api_and_dependency_injection():
    service = CapabilityStatusService(N8nAdapter(N8nConfiguration()))
    app = create_app(n8n_status_service=service)
    assert app.state.n8n_status_service is service
    client = TestClient(app)
    assert client.get("/api/capabilities/n8n").json()["status"] == "NOT_DEPLOYED"
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)("/api/capabilities/n8n").status_code == 405


def test_platform_neutral_app_performs_no_n8n_discovery(monkeypatch):
    monkeypatch.setenv("N8N_ENDPOINT", "private-endpoint")
    monkeypatch.setenv("N8N_API_KEY", "private-key")
    result = TestClient(create_app()).get("/api/capabilities/n8n").json()
    assert result["status"] == "UNAVAILABLE"
    assert result["configuration"] == {"status": "UNKNOWN"}
    assert result["runtime"] == {"kind": "UNKNOWN", "transport": "UNKNOWN"}
    assert result["evidence"] == []
    assert "private" not in json.dumps(result)


def test_governance_and_adapter_expose_no_action_surface():
    source = Path("core/capabilities/contracts.py").read_text()
    adapter = Path("integrations/n8n/adapter.py").read_text()
    assert "def execute" not in source + adapter
    assert all(word not in adapter for word in ("launchctl", "subprocess", "requests", "httpx"))
    assert observe()["governance"] == {
        "authority": "AICONTROLCENTER", "read_only": True,
        "production_authorization": False, "infrastructure_mutation": False,
        "platform_business_policy_ownership": False, "action_execution": False,
    }


def test_core_has_no_outer_imports():
    imports = []
    for path in Path("core").rglob("*.py"):
        for line in path.read_text().splitlines():
            if line.startswith(("import ops", "from ops", "import integrations", "from integrations")):
                imports.append((path, line))
    assert imports == []


def test_macos_composition_injects_n8n_capability():
    from ops.macos.runtime.application import app as canonical_app
    result = canonical_app.state.n8n_status_service.status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["configuration"]["status"] == "UNKNOWN"


def test_optional_absence_does_not_affect_runtime_health_or_service_platform():
    manifest = json.loads(Path("config/services/mac-standalone-production.json").read_text())
    service = next(item for item in manifest["services"] if item["service_id"] == "n8n")
    assert service["required"] is False
    assert service["runtime_health"] is False
    assert service["production_status"] == "NOT_DEPLOYED"
    assert "service_platform" not in service
