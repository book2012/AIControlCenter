"""Focused offline Activation-02 safety tests."""

from datetime import datetime, timedelta, timezone
import copy
import inspect
import json
import os
from pathlib import Path

import pytest

from core.shopping.public_storefront_v2_activation_02_authorization import (
    ConsumptionFailure, ConsumptionState, validate_authorization,
)
from core.shopping.public_storefront_v2_activation_02_reconciliation import (
    AUTHORITY_ID, DATABASE_CONTAINER_ID, DATABASE_IMAGE, DATABASE_NETWORKS, DATABASE_VOLUME,
    EFFECTIVE_CADDY_STATE, MAXIMUM_LIFETIME_SECONDS, MUTATION_ID, PROFILE, PROFILE_FILE,
    WORDPRESS_CONTAINER_ID, WORDPRESS_IMAGE, WORDPRESS_NETWORKS, WORDPRESS_VOLUME,
    canonical_json, precondition_template, projection, validate_post_activation,
)
from ops.macos.shopping.issue_public_storefront_v2_activation_02_authorization import _authorization
from ops.macos.shopping.public_storefront_v2_activation_02_authorization_store import PublicStorefrontV2ActivationAuthorizationStore
from ops.macos.shopping.public_storefront_v2_activation_02_operator import ActivationRunner, MacActivationPort


def _source():
    return {"head": "e" * 40, "clean": True,
            "artifacts": {name: "a" * 64 for name in (
                "ops/macos/caddy/Caddyfile", "config/deployment/caddy-site-policy.json",
                "config/deployment/ingress.json", "deploy/shopping/compose.yaml",
                "ops/macos/colima/commerce-runtime.json")},
            "activation_bundle_sha256": "b" * 64}


def _wp_mounts():
    return [
        {"type": "volume", "name": WORDPRESS_VOLUME, "source": None, "destination": "/var/www/html", "rw": True},
        {"type": "bind", "name": None, "source": "deploy/shopping/config/shopping-apache-safety.conf", "destination": "/etc/apache2/sites-available/000-default.conf", "rw": False},
        {"type": "bind", "name": None, "source": "deploy/shopping/config/shopping-php-safety.ini", "destination": "/usr/local/etc/php/conf.d/zz-shopping-safety.ini", "rw": False},
        {"type": "bind", "name": None, "source": "deploy/shopping/wordpress/plugins/ai-shopping-storefront", "destination": "/var/www/html/wp-content/plugins/ai-shopping-storefront", "rw": False},
    ]


def _generation(*, database):
    return {"container_id": DATABASE_CONTAINER_ID if database else WORDPRESS_CONTAINER_ID,
            "created": "2026-10-02T00:00:00Z", "image": DATABASE_IMAGE if database else WORDPRESS_IMAGE,
            "image_id": "sha256:" + "c" * 64, "project": "ai-shopping",
            "service": "database" if database else "wordpress", "running": True, "healthy": True,
            "restart_policy": "unless-stopped" if database else "no",
            "ports": {} if database else {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]},
            "mounts": [{"type": "volume", "name": DATABASE_VOLUME, "source": None, "destination": "/var/lib/mysql", "rw": True}] if database else _wp_mounts(),
            "networks": {name: "d" * 64 for name in (DATABASE_NETWORKS if database else WORDPRESS_NETWORKS)}}


def _preconditions():
    return precondition_template(
        source=_source(), colima={"profile": PROFILE, "status": "Running", "semantic_profile": "PASS"},
        wordpress=_generation(database=False), database=_generation(database=True),
        volumes={"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME},
        networks={name: "d" * 64 for name in WORDPRESS_NETWORKS},
        caddy={"state": EFFECTIVE_CADDY_STATE, "trusted_executable": "/opt/homebrew/Cellar/caddy/2.11.4/bin/caddy",
               "listeners": ["127.0.0.1:2019", "*:58080", "*:58443"]},
    )


def _auth(pre):
    return _authorization(preconditions=pre, uid=os.getuid(), gid=os.getgid())


def _post():
    return {"loaded_v2": True, "public_host": "bokstory.duckdns.org", "public_root": "127.0.0.1:58082",
            "public_root_upstream": True, "shopping_read_upstream": True,
            "shopping_get_allowlist": True, "public_basic_auth_absent": True, "dev_basic_auth_preserved": True,
            "management_denied": True, "wordpress_private_denied": True, "rest_route_guard": True,
            "shopping_writes_not_proxied": True, "legacy_redirect": True,
            "wordpress_generation_unchanged": True, "database_generation_unchanged": True,
            "colima_lifecycle_mutation": False, "caddy_reload_count": 1}


def test_new_authority_is_exact_and_forbids_runtime_capabilities():
    value = _auth(_preconditions())
    assert value.authority_id == AUTHORITY_ID
    assert value.mutation_id == MUTATION_ID
    assert value.maximum_uses == 1
    assert value.caddy_reload_authority is True
    assert value.colima_restart_authority is False
    assert value.wordpress_runtime_mutation_authority is False
    assert value.database_recreation_allowed is False
    assert value.volume_recreation_allowed is False
    assert value.woo_write_authority is False
    validate_authorization(value, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())


def test_generation_requires_full_running_signature():
    value = _preconditions()
    value["wordpress"]["mounts"] = value["wordpress"]["mounts"][:-1]
    with pytest.raises(Exception):
        precondition_template(**{key: value[key] for key in ("source", "colima", "wordpress", "database", "volumes", "networks", "caddy")})


def test_durable_store_is_one_shot_and_consumption_rechecks(tmp_path):
    pre = _preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "a.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(_auth(pre))
    assert store.consume(lambda: pre).receipt.state is ConsumptionState.COMMITTED
    with pytest.raises(Exception):
        store.consume(lambda: pre)


class FakePort:
    def __init__(self, before):
        self.before = before
        self.calls = []

    def observe_preconditions(self):
        self.calls.append("observe")
        return self.before

    def validate_caddy_offline(self):
        self.calls.append("validate")
        return True

    def reload_caddy_once(self):
        self.calls.append("reload")
        return True

    def effective_caddy_v2(self):
        self.calls.append("effective")
        return True

    def post_activation(self):
        self.calls.append("post")
        return _post()


def test_runner_consumes_then_freshly_reobserves_before_one_reload(tmp_path):
    pre = _preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "b.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(_auth(pre))
    port = FakePort(pre)
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "ACTIVATED"
    assert port.calls == ["observe", "observe", "validate", "reload", "effective", "post"]
    assert result["fresh_pre_reload_reobservation"] is True
    assert result["caddy_reload_count"] == 1


def test_drift_after_consumption_fails_closed_without_reload(tmp_path):
    pre = _preconditions()
    drifted = copy.deepcopy(pre)
    drifted["wordpress"]["created"] = "2026-10-02T00:01:00Z"
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "c.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(_auth(pre))

    class DriftPort(FakePort):
        def observe_preconditions(self):
            self.calls.append("observe")
            return pre if self.calls.count("observe") == 1 else drifted

    port = DriftPort(pre)
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "UNCERTAIN"
    assert result["authorization_consumed"] is True
    assert "reload" not in port.calls


def test_operator_has_no_lifecycle_or_compose_mutation_surface():
    source = inspect.getsource(MacActivationPort)
    lowered = source.lower()
    for forbidden in ("colima, \"restart\"", "container\", \"start\"", "compose\", \"up\"", "container\", \"rm\"", "volume\", \"create\""):
        assert forbidden not in lowered
    assert '[CADDY, "reload"' in source


def test_wrong_docker_identity_fails_closed_before_inspection(monkeypatch, tmp_path):
    port = object.__new__(MacActivationPort)
    port.runtime_root = tmp_path
    monkeypatch.setattr(
        "ops.macos.shopping.public_storefront_v2_activation_02_operator._trusted_docker_executable",
        lambda: (_ for _ in ()).throw(RuntimeError("unexpected Docker executable identity")),
    )
    with pytest.raises(RuntimeError, match="unexpected Docker executable identity"):
        port._docker_inspect("0" * 64)


def test_post_security_facts_are_observer_derived(monkeypatch):
    port = object.__new__(MacActivationPort)
    port._bound_wordpress = _generation(database=False)
    port._bound_database = _generation(database=True)
    port._reload_count = 1
    monkeypatch.setattr(port, "_generation", lambda identity, database: _generation(database=database))
    proof = {key: False for key in (
        "loaded_config_matches_reviewed_adaptation", "production_host", "public_root_upstream",
        "shopping_read_upstream", "public_get_allowlist_matcher_loaded", "shopping_writes_not_proxied",
        "private_management_matcher_loaded", "wordpress_rest_matcher_loaded",
        "raw_query_rest_route_ambiguity_guard_loaded", "dev_host", "dev_basic_auth_loaded",
        "public_has_no_basic_auth", "legacy_redirect_loaded",
    )}
    monkeypatch.setattr(port, "_effective_caddy_proof", lambda: proof)
    result = port.post_activation()
    assert result["public_basic_auth_absent"] is False
    assert result["shopping_writes_not_proxied"] is False
    with pytest.raises(Exception):
        validate_post_activation(result)


@pytest.mark.parametrize("stage, expected_state", [
    ("before_claim_commit", "DURABLY_CLAIMED"),
    ("before_final_commit", "DURABLY_CLAIMED"),
])
def test_commit_boundary_uncertainty_is_irreversible(tmp_path, stage, expected_state):
    pre = _preconditions()

    def fault(observed_stage, _db):
        if observed_stage == stage:
            raise RuntimeError("injected commit ambiguity")

    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(
        tmp_path / (stage + ".sqlite3"), uid=os.getuid(), gid=os.getgid(), fault=fault,
    )
    store._issue(_auth(pre))
    with pytest.raises(ConsumptionFailure):
        store.consume(lambda: pre)
    with store._read() as db:
        state = db.execute(
            "SELECT state FROM public_storefront_v2_activation_02_authorizations"
        ).fetchone()[0]
    assert state == expected_state
    with pytest.raises(ConsumptionFailure):
        store.consume(lambda: pre)


def test_after_final_commit_uncertainty_is_committed_and_not_retried(tmp_path):
    pre = _preconditions()

    def fault(stage, _db):
        if stage == "after_final_commit":
            raise RuntimeError("injected post-commit ambiguity")

    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(
        tmp_path / "after-final.sqlite3", uid=os.getuid(), gid=os.getgid(), fault=fault,
    )
    store._issue(_auth(pre))
    with pytest.raises(ConsumptionFailure):
        store.consume(lambda: pre)
    with store._read() as db:
        state = db.execute(
            "SELECT state FROM public_storefront_v2_activation_02_authorizations"
        ).fetchone()[0]
    assert state == "COMMITTED"


def test_output_projection_is_value_bounded_and_secret_blind():
    value = json.dumps(projection("BLOCKED"), sort_keys=True)
    assert len(value) < 4096
    assert "password" not in value.lower()
    assert "secret" not in value.lower()


def test_post_contract_is_closed():
    validate_post_activation(_post())
    with pytest.raises(Exception):
        validate_post_activation({**_post(), "caddy_reload_count": 2})
