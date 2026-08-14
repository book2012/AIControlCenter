import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.capabilities.service import CapabilityStatusService
from integrations.openclaw import OpenClawAdapter, OpenClawConfiguration
from integrations.openclaw.composition import build_openclaw_status_service


def observe(configuration=None, observer=None):
    adapter = OpenClawAdapter(configuration or OpenClawConfiguration(), observer)
    return adapter.observe().to_dict()


def test_optional_not_deployed_is_truthful_and_json_compatible():
    result = observe()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["available"] is result["healthy"] is result["ready"] is False
    assert result["governance"]["production_authorization"] is False
    json.dumps(result)


def test_default_composition_ignores_unproven_environment_conventions(monkeypatch):
    monkeypatch.setenv("OPENCLAW_ENDPOINT", "https://user:secret@example.invalid/?token=private")
    monkeypatch.setenv("OPENCLAW_API_KEY", "credential-value")
    result = build_openclaw_status_service().status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["configuration"]["status"] == "UNKNOWN"
    assert result["configuration"]["endpoint_configured"] is None
    assert result["configuration"]["authentication_configured"] is None
    assert result["runtime"] == {"kind": "UNKNOWN"}
    serialized = json.dumps(result)
    assert all(value not in serialized for value in ("secret", "private", "credential-value"))


def test_malformed_manifest_fails_closed(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("not-json")
    result = build_openclaw_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}


@pytest.mark.parametrize("identity_count", [0, 2])
def test_missing_or_duplicate_manifest_identity_fails_closed(tmp_path, identity_count):
    canonical = json.loads(Path("config/services/mac-standalone-production.json").read_text())
    entry = next(item for item in canonical["services"] if item["service_id"] == "openclaw")
    canonical["services"] = [
        item for item in canonical["services"] if item["service_id"] != "openclaw"
    ] + [entry] * identity_count
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(canonical))
    result = build_openclaw_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}


def test_configured_and_unconfigured_states_fail_closed():
    unknown = observe(OpenClawConfiguration(deployment_status="PRODUCTION"))
    assert unknown["status"] == "UNAVAILABLE"
    assert unknown["error"] == {"error_type": "ConfigurationEvidenceUnknown"}
    unconfigured = observe(OpenClawConfiguration(deployment_status="PRODUCTION", endpoint_configured=False))
    assert unconfigured["status"] == "NOT_CONFIGURED"
    configured = observe(OpenClawConfiguration("PRODUCTION", True, True))
    assert configured["status"] == "UNAVAILABLE"
    assert configured["error"] == {"error_type": "ObserverNotConfigured"}


@pytest.mark.parametrize("payload", [{}, {"healthy": True}, {"healthy": "yes", "ready": True}, {"healthy": True, "ready": True, "token": "secret"}])
def test_malformed_response_fails_closed(payload):
    result = observe(OpenClawConfiguration("PRODUCTION", True, True), lambda: payload)
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "MalformedObservation"}
    assert "secret" not in repr(result)


@pytest.mark.parametrize("error,error_type", [(TimeoutError("private"), "TimeoutError"), (ConnectionError("private"), "ConnectionError")])
def test_transport_failures_are_value_free(error, error_type):
    def failure():
        raise error
    result = observe(OpenClawConfiguration("PRODUCTION", True, True), failure)
    assert result["error"] == {"error_type": error_type}
    assert "private" not in repr(result)


def test_available_and_degraded_observations():
    config = OpenClawConfiguration("PRODUCTION", True, True, "injected-test-transport")
    assert observe(config, lambda: {"healthy": True, "ready": True})["status"] == "AVAILABLE"
    assert observe(config, lambda: {"healthy": True, "ready": False})["status"] == "DEGRADED"


def test_api_is_get_only_and_dependency_is_injected():
    service = CapabilityStatusService(OpenClawAdapter(OpenClawConfiguration()))
    app = create_app(openclaw_status_service=service)
    assert app.state.openclaw_status_service is service
    client = TestClient(app)
    assert client.get("/api/capabilities/openclaw").json()["status"] == "NOT_DEPLOYED"
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)("/api/capabilities/openclaw").status_code == 405


def test_platform_neutral_app_fails_closed_without_external_discovery(monkeypatch):
    monkeypatch.setenv("OPENCLAW_ENDPOINT", "private-endpoint")
    monkeypatch.setenv("OPENCLAW_API_KEY", "private-key")
    result = TestClient(create_app()).get("/api/capabilities/openclaw").json()
    assert result["status"] == "UNAVAILABLE"
    assert result["configuration"] == {"status": "UNKNOWN"}
    assert result["runtime"] == {"kind": "UNKNOWN"}
    assert result["evidence"] == []
    assert "private" not in json.dumps(result)


def test_contract_has_no_execution_or_production_operation():
    source = Path("core/capabilities/contracts.py").read_text()
    adapter = Path("integrations/openclaw/adapter.py").read_text()
    assert "def execute" not in source + adapter
    assert "launchctl" not in adapter
    result = observe()
    assert result["governance"] == {
        "authority": "AICONTROLCENTER", "read_only": True,
        "production_authorization": False, "infrastructure_mutation": False,
        "platform_business_policy_ownership": False,
        "action_execution": False,
    }


def test_core_has_no_outer_import_and_adapter_is_outer():
    imports = []
    for path in Path("core").rglob("*.py"):
        for line in path.read_text().splitlines():
            if line.startswith(("import ops", "from ops", "import integrations", "from integrations")):
                imports.append((path, line))
    assert imports == []
    assert not Path("core").joinpath("openclaw").exists()


def test_canonical_macos_application_injects_outer_openclaw_service():
    from ops.macos.runtime.application import app as canonical_app

    result = canonical_app.state.openclaw_status_service.status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["configuration"]["status"] == "UNKNOWN"


def test_optional_absence_does_not_affect_runtime_health():
    manifest = json.loads(Path("config/services/mac-standalone-production.json").read_text())
    service = next(item for item in manifest["services"] if item["service_id"] == "openclaw")
    assert service["required"] is False
    assert service["runtime_health"] is False
    assert service["production_status"] == "NOT_DEPLOYED"
    assert "service_platform" not in service
