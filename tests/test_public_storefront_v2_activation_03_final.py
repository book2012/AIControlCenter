"""Focused offline tests for PUBLIC-STOREFRONT-V2-ACTIVATION-01."""

from datetime import datetime, timezone
import inspect
import json
import os

import pytest

from core.shopping.public_storefront_v2_activation_03_final_authorization import validate_authorization
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    ARTIFACTS, AUTHORITY_ID, CADDYFILE_SHA256, ContractError,
    EXPECTED_PORTS, MUTATION_ID, POLICY_VERSION, PROFILE, PROFILE_FILE,
    precondition_template, projection, validate_post_activation, validate_preconditions,
)
from ops.macos.shopping.issue_public_storefront_v2_activation_03_final_authorization import _authorization
from ops.macos.shopping.public_storefront_v2_activation_03_final_authorization_store import (
    PublicStorefrontV2ActivationAuthorizationStore,
)
from ops.macos.shopping.public_storefront_v2_activation_03_final_operator import (
    ActivationRunner, MacActivationPort,
)


def source():
    return {"head": "1" * 40, "clean": True, "artifacts": ARTIFACTS,
            "activation_bundle_sha256": "2" * 64}


def preconditions():
    return precondition_template(
        source=source(),
        colima={"profile": PROFILE, "profile_file": PROFILE_FILE,
                "profile_sha256": "61a9194ab22dfff9515d44d3d41af9eafdf3647e8ee5d6f0cb6fe92f77f473ea",
                "status": "Broken"},
        forwarding={"owner": "colima", "profile": PROFILE, "host": "127.0.0.1",
                     "port": 58082, "required_for_lifecycle": True},
        wordpress={"container_id": "43d8d4f9e370ac066a77cbf1b346002df6d11cff00e3212bc0a3c6b668745648",
                   "state": "created", "running": False, "published": "127.0.0.1:58082->80/tcp"},
        database={"container_id": "434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323",
                  "state": "running", "healthy": True, "published": False,
                  "volume": "ai-shopping-database"},
    )


def auth(pre):
    return _authorization(preconditions=pre, uid=os.getuid(), gid=os.getgid())


def post(*, empty=False):
    return {
        "public": {"https_success": True, "basic_auth": False, "storefront_rendered": True},
        "shopping_reads": {"categories": True, "search": True, "featured_products": True, "products": True},
        "product_catalog": "VALID_EMPTY" if empty else "VALID_NONEMPTY",
        "private_boundary": {"wordpress_paths_denied": True, "rest_routes_denied": True,
                              "management_paths_denied": True, "shopping_writes_not_proxied": True,
                              "order_payment_cart_checkout_not_proxied": True},
        "dev": {"https_success": False, "basic_auth_required": True,
                "production_never_uses_dev": True},
        "legacy": {"path": "/homepage/storefront", "status": 301, "location": "/"},
        "direct_browser_woo_denied": True,
        "wordpress_loopback": "127.0.0.1:58082", "server_side_api": "127.0.0.1:58081",
        "database_continuity": True, "effective_caddy_v2": True,
        "rest_route_live_proof": True, "product_detail_dynamic_id": not empty,
        "public_commerce_write_request": "NOT_PERFORMED", "caddy_reload_count": 1,
    }


def test_authority_is_distinct_and_hard_bound():
    value = auth(preconditions())
    assert value.authority_id == AUTHORITY_ID
    assert value.authoritative_work_item == AUTHORITY_ID
    assert value.mutation_id == MUTATION_ID
    assert value.maximum_uses == 1
    assert value.production_write_authority is False
    assert value.ubuntu_authority is False
    assert value.database_recreation_allowed is False
    assert value.volume_recreation_allowed is False
    assert value.dns_change_allowed is False
    assert value.woo_write_authority is False
    validate_authorization(value, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())


def test_phase_a_contract_is_host_only_and_binds_broken_profile():
    value = inspect.getsource(MacActivationPort.observe_preconditions)
    assert "_docker_inspect" not in value
    assert "Docker" in value and "never call Docker" in value
    bound = preconditions()
    validate_preconditions(bound)
    bound["colima"]["status"] = "Running"
    with pytest.raises(ContractError):
        validate_preconditions(bound)


def test_contract_rejects_drift_and_requires_dynamic_detail_contract():
    value = preconditions()
    value["desired"]["policy_version"] = "old"
    with pytest.raises(ContractError):
        validate_preconditions(value)
    assert CADDYFILE_SHA256 == ARTIFACTS["ops/macos/caddy/Caddyfile"]
    assert EXPECTED_PORTS == {"control_plane": 58081, "wordpress": 58082, "dev": 18080}
    assert POLICY_VERSION == "public-storefront-migration/v2"
    validate_post_activation(post(empty=True))
    with pytest.raises(ContractError):
        validate_post_activation({**post(), "product_detail_dynamic_id": False})


def test_store_is_durable_one_shot_and_does_not_reissue(tmp_path):
    path = tmp_path / "public-storefront-v2-activation-01.sqlite3"
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(path, uid=os.getuid(), gid=os.getgid())
    store._issue(auth(preconditions()))
    result = store.consume(lambda: preconditions())
    assert result.receipt.state == "COMMITTED"
    with pytest.raises(Exception):
        PublicStorefrontV2ActivationAuthorizationStore._open_existing_for_test(path, uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        store._issue(auth(preconditions()))


class FakePort:
    def __init__(self, before):
        self.before = before
        self.calls = []

    def observe_preconditions(self):
        self.calls.append("phase_a")
        return self.before

    def reconcile_colima(self):
        self.calls.append("colima_repair")
        return True

    def validate_existing_generations(self):
        self.calls.append("phase_b")
        return True

    def start_existing_wordpress(self):
        self.calls.append("wordpress_start")
        return True

    def wordpress_healthy(self):
        self.calls.append("wordpress_health")
        return True

    def server_side_api_connectivity(self):
        self.calls.append("server_side_api")
        return True

    def validate_caddy_offline(self):
        self.calls.append("caddy_validate")
        return True

    def reload_caddy_once(self):
        self.calls.append("caddy_reload")
        return True

    def effective_caddy_v2(self):
        self.calls.append("effective_caddy_v2")
        return True

    def post_activation(self):
        self.calls.append("post")
        return post()


def test_runner_has_two_phase_order_and_one_mutation_each(tmp_path):
    before = preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "a.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(auth(before))
    port = FakePort(before)
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "ACTIVATED"
    assert port.calls == ["phase_a", "phase_a", "colima_repair", "phase_b", "wordpress_start",
                          "wordpress_health", "server_side_api", "caddy_validate", "caddy_reload",
                          "effective_caddy_v2", "post"]
    assert result["colima_repair_attempted"] is True
    assert result["wordpress_start_attempted"] is True
    assert result["caddy_reload_attempted"] is True
    assert result["caddy_reload_count"] == 1
    assert result["colima_retry"] is False


def test_phase_b_identity_failure_never_starts_wordpress(tmp_path):
    before = preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "b.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(auth(before))
    port = FakePort(before)
    port.validate_existing_generations = lambda: port.calls.append("phase_b") or False
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "UNCERTAIN"
    assert result["colima_repair_attempted"] is True
    assert result["wordpress_start_attempted"] is False
    assert "wordpress_start" not in port.calls
    assert "caddy_reload" not in port.calls


def test_static_mutation_surface_is_closed():
    source_text = inspect.getsource(MacActivationPort)
    for forbidden in ("[\"compose\"", " compose up", "container create", "container rm", "volume create", "volume rm"):
        assert forbidden not in source_text.lower()
    assert '"container", "start"' in source_text
    assert "WORDPRESS_CONTAINER_ID" in source_text
    assert "UbuntuWorkerClient" not in source_text


def test_post_result_is_value_free():
    result = projection("BLOCKED", authorization_consumed=False)
    assert "secret" not in json.dumps(result)
