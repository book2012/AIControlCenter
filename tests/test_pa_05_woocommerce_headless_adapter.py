import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.capabilities import CapabilityGovernanceExtensions, CapabilityObservation, CapabilityStatus
from core.capabilities.service import CapabilityStatusService
from integrations.woocommerce import WooCommerceAdapter, WooCommerceConfiguration
from integrations.woocommerce.composition import build_woocommerce_status_service


def observe(configuration=None, observer=None):
    return WooCommerceAdapter(configuration or WooCommerceConfiguration(), observer).observe().to_dict()


def test_canonical_service_manifest_has_no_woocommerce_identity_and_capability_is_fail_closed():
    canonical = json.loads(Path("config/services/mac-standalone-production.json").read_text())
    assert [item for item in canonical["services"] if item["service_id"] == "woocommerce"] == []
    result = build_woocommerce_status_service().status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["error"] is None
    assert result["evidence"] == [{"type": "canonical_capability_manifest", "deployment_status": "NOT_DEPLOYED"}]
    assert result["configuration"] == {
        "status": "UNKNOWN", "configuration_configured": None,
        "authentication_configured": None,
    }
    assert result["runtime"] == {"kind": "UNKNOWN", "transport": "UNKNOWN"}
    assert "consumer_secret" not in json.dumps(result)


@pytest.mark.parametrize("contents", ["not-json", "{}"])
def test_malformed_or_schema_invalid_manifest_fails_closed(tmp_path, contents):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(contents)
    result = build_woocommerce_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}
    assert result["evidence"] == []
    assert str(manifest) not in json.dumps(result)


def test_duplicate_manifest_identity_fails_closed(tmp_path):
    canonical = json.loads(Path("config/capabilities/mac-standalone-production.json").read_text())
    canonical["capabilities"].append(dict(canonical["capabilities"][0]))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(canonical))
    result = build_woocommerce_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["evidence"] == []
    assert str(manifest) not in json.dumps(result)


def test_unreadable_manifest_fails_closed_without_path_or_exception_leak(tmp_path):
    manifest = tmp_path / "missing-sensitive-name.json"
    result = build_woocommerce_status_service(manifest_path=manifest).status()
    assert result["status"] == "UNAVAILABLE"
    assert result["evidence"] == []
    assert result["error"] == {"error_type": "IndeterminateDeploymentStatus"}
    assert str(manifest) not in json.dumps(result)


def test_successful_injected_manifest_identity_is_truthful_evidence(tmp_path):
    canonical = json.loads(Path("config/capabilities/mac-standalone-production.json").read_text())
    entry = canonical["capabilities"][0]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(canonical))
    result = build_woocommerce_status_service(manifest_path=manifest).status()
    assert result["evidence"] == [{
        "type": "canonical_capability_manifest", "deployment_status": entry["production_status"],
    }]


def test_configuration_and_authentication_unknown_fail_closed():
    configured_unknown = observe(WooCommerceConfiguration("PRODUCTION"))
    assert configured_unknown["error"] == {"error_type": "ConfigurationEvidenceUnknown"}
    auth_unknown = observe(WooCommerceConfiguration("PRODUCTION", True))
    assert auth_unknown["error"] == {"error_type": "AuthenticationEvidenceUnknown"}
    assert observe(WooCommerceConfiguration("PRODUCTION", False))["status"] == "NOT_CONFIGURED"


def test_unavailable_and_malformed_observer():
    config = WooCommerceConfiguration("PRODUCTION", True, True)
    assert observe(config)["error"] == {"error_type": "ObserverNotConfigured"}
    for payload in ({}, {"healthy": True, "ready": True},
                    {"healthy": True, "ready": True, "catalog_readable": "yes"}):
        assert observe(config, lambda payload=payload: payload)["error"] == {"error_type": "MalformedObservation"}


@pytest.mark.parametrize("error,error_type", [
    (TimeoutError("secret endpoint"), "TimeoutError"),
    (ConnectionError("secret credential"), "ConnectionError"),
])
def test_transport_failure_is_value_free(error, error_type):
    def failure():
        raise error
    result = observe(WooCommerceConfiguration("PRODUCTION", True, True), failure)
    assert result["error"] == {"error_type": error_type}
    assert "secret" not in repr(result)


def test_available_and_degraded_require_explicit_observation():
    config = WooCommerceConfiguration("PRODUCTION", True, True, "injected", "read-only")
    available = observe(config, lambda: {"healthy": True, "ready": True, "catalog_readable": True})
    assert available["status"] == "AVAILABLE"
    degraded = observe(config, lambda: {"healthy": True, "ready": False, "catalog_readable": True})
    assert degraded["status"] == "DEGRADED"
    assert degraded["healthy"] is True and degraded["ready"] is False


def test_get_only_api_and_dependency_injection():
    service = CapabilityStatusService(WooCommerceAdapter(WooCommerceConfiguration("NOT_DEPLOYED")))
    app = create_app(woocommerce_status_service=service)
    assert app.state.woocommerce_status_service is service
    client = TestClient(app)
    assert client.get("/shopping/providers/woocommerce").json()["status"] == "NOT_DEPLOYED"
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)("/shopping/providers/woocommerce").status_code == 405


def test_platform_neutral_app_does_no_woocommerce_discovery():
    result = TestClient(create_app()).get("/shopping/providers/woocommerce").json()
    assert result["status"] == "UNAVAILABLE"
    assert result["evidence"] == []


def test_governance_and_no_mutation_surface():
    result = observe()
    assert result["governance"] == {
        "authority": "AICONTROLCENTER", "read_only": True,
        "production_authorization": False, "infrastructure_mutation": False,
        "platform_business_policy_ownership": False, "action_execution": False,
        "commerce_engine_only": True, "automatic_retry": False,
    }
    adapter = WooCommerceAdapter(WooCommerceConfiguration())
    for name in ("create_product", "update_product", "delete_product", "create_order",
                 "update_order", "update_inventory", "mutate_customer", "mutate_coupon", "execute"):
        assert not hasattr(adapter, name)


@pytest.mark.parametrize("reserved,value", [
    ("authority", "OUTER"), ("read_only", False),
    ("production_authorization", True), ("infrastructure_mutation", True),
    ("action_execution", True),
])
def test_reserved_governance_keys_cannot_be_supplied(reserved, value):
    with pytest.raises(TypeError):
        CapabilityGovernanceExtensions(**{reserved: value})


def test_governance_extensions_reject_unsupported_keys_and_non_booleans():
    with pytest.raises(TypeError):
        CapabilityGovernanceExtensions(secret="do-not-project")
    with pytest.raises(TypeError):
        CapabilityGovernanceExtensions(automatic_retry="false")
    with pytest.raises(TypeError):
        CapabilityObservation(
            provider="test", service_id="test", status=CapabilityStatus.UNAVAILABLE,
            available=False, healthy=False, ready=False, capabilities=(), configuration={},
            runtime={}, evidence=(), governance_extensions={"authority": "OUTER"},
        )


def test_canonical_governance_is_core_owned_and_prior_adapters_remain_compatible():
    observation = CapabilityObservation(
        provider="test", service_id="test", status=CapabilityStatus.UNAVAILABLE,
        available=False, healthy=False, ready=False, capabilities=(), configuration={},
        runtime={}, evidence=(),
    ).to_dict()
    assert observation["governance"] == {
        "authority": "AICONTROLCENTER", "read_only": True,
        "production_authorization": False, "infrastructure_mutation": False,
        "platform_business_policy_ownership": False, "action_execution": False,
    }


def test_shopping_and_product_draft_runtime_remain_authoritative():
    app = create_app()
    assert app.state.shopping_runtime.product_draft_mutation_available is False
    assert app.state.shopping_runtime.catalog_service.integration_status()["catalog_adapter"] == "mock"


def test_core_has_no_outer_imports_and_macos_injects_adapter():
    imports = []
    for path in Path("core").rglob("*.py"):
        for line in path.read_text().splitlines():
            if line.startswith(("import ops", "from ops", "import integrations", "from integrations")):
                imports.append((path, line))
    assert imports == []
    from ops.macos.runtime.application import app as canonical_app
    result = canonical_app.state.woocommerce_status_service.status()
    assert result["status"] == "NOT_DEPLOYED"
    assert result["evidence"] == [{
        "type": "canonical_capability_manifest",
        "deployment_status": "NOT_DEPLOYED",
    }]
