"""Focused offline contract tests for PUBLIC_STOREFRONT_MIGRATION_V2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from core.deployment.adapters.macos.caddy_sites import (
    _rest_route_query_pattern,
    classify_caddy_sites,
    load_site_policy,
)
from core.deployment.contracts import load_schema_registry, validate_contract_payload


ROOT = Path(__file__).resolve().parents[1]
CADDY = (ROOT / "ops/macos/caddy/Caddyfile").read_text(encoding="utf-8")
POLICY = load_site_policy((ROOT / "config/deployment/caddy-site-policy.json").read_text())
INGRESS = json.loads((ROOT / "config/deployment/ingress.json").read_text())
CLASSIFICATION = classify_caddy_sites(CADDY, policy=POLICY, ingress_contract=INGRESS)
PUBLIC = CADDY.split("dev.bokstory.duckdns.org", 1)[0]
DEV = CADDY.split("dev.bokstory.duckdns.org", 1)[1]


def test_public_root_and_dev_identity_are_independent():
    assert CLASSIFICATION.production.hostname == "bokstory.duckdns.org"
    assert CLASSIFICATION.production.port == 58082
    assert CLASSIFICATION.production.authentication_required is False
    assert CLASSIFICATION.preview.hostname == "dev.bokstory.duckdns.org"
    assert CLASSIFICATION.preview.port == 18080
    assert CLASSIFICATION.preview.authentication_required is True
    assert "reverse_proxy 127.0.0.1:58082" in PUBLIC
    assert "basic_auth" not in PUBLIC
    assert "basic_auth" in DEV
    assert "127.0.0.1:18080" in DEV
    assert "127.0.0.1:18080" not in PUBLIC


def test_public_shopping_read_allowlist_is_get_only_and_bounded():
    assert POLICY["public_shopping_api"] == {
        "upstream": {"host": "127.0.0.1", "port": 58081},
        "authentication": "none",
        "methods": ["GET"],
        "paths": [
            "/shopping/categories", "/shopping/search", "/shopping/featured-products",
            "/shopping/products", "/shopping/products/*",
        ],
        "required": True,
    }
    assert "method GET" in PUBLIC
    assert "path /shopping/categories /shopping/search /shopping/featured-products /shopping/products /shopping/products/*" in PUBLIC
    assert 'respond @public_shopping_namespace "Not Found" 404' in PUBLIC
    assert PUBLIC.count("reverse_proxy 127.0.0.1:58081") == 1


def test_public_commerce_writes_and_non_allowlisted_shopping_paths_fail_closed():
    assert 'respond @public_shopping_namespace "Not Found" 404' in PUBLIC
    assert "method POST" not in PUBLIC
    assert "method PUT" not in PUBLIC
    assert "method PATCH" not in PUBLIC
    assert "method DELETE" not in PUBLIC
    allowlist = set(POLICY["public_shopping_api"]["paths"])
    assert not allowlist.intersection({"/shopping/cart", "/shopping/checkout", "/shopping/orders", "/shopping/payment", "/shopping/refund"})


def test_wordpress_rest_path_and_reserved_management_paths_are_denied():
    assert "@wordpress_namespace path /wp-admin /wp-admin/* /wp-login.php /xmlrpc.php /wp-cron.php /wp-json /wp-json/*" in PUBLIC
    assert 'respond @wordpress_namespace "Not Found" 404' in PUBLIC
    for marker in ("/management", "/deployment", "/runtime", "/governance", "/providers", "/tasks"):
        assert marker in PUBLIC
    assert 'respond @management_namespace "Not Found" 404' in PUBLIC
    assert "wp-admin" in PUBLIC and "wp-login.php" in PUBLIC and "xmlrpc.php" in PUBLIC


def test_rest_route_query_bypass_is_denied_for_aliases_and_ambiguity():
    matcher = re.compile(_rest_route_query_pattern())
    denied = (
        "rest_route=/aicontrolcenter/v1/shopping",
        "REST_ROUTE=/wp/v2/users",
        "rest.route=/wp/v2/users",
        "rest+route=/wp/v2/users",
        "rest%5froute=/wp/v2/users",
        "rest%2520route=/wp/v2/users",
        "x=1&rest_route=/wp/v2/users&rest_route=/aicontrolcenter/v1/shopping",
        "x=1;rest_route=",
        "x=1%26rest_route%3d%2fwp%2fv2",
    )
    for query in denied:
        assert matcher.search(query), query
    assert not matcher.search("xrest_route=/wp/v2/users")
    assert not matcher.search("rest_routes=/wp/v2/users")
    assert PUBLIC.index('respond @shopping_rest_route_ambiguous "Forbidden" 403') < PUBLIC.index("handle @public_shopping_read")


def test_server_side_storefront_identity_uses_verified_internal_api():
    plugin = (ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/ai-shopping-storefront.php").read_text()
    client = (ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/includes/class-api-client.php").read_text()
    compose = (ROOT / "deploy/shopping/compose.yaml").read_text()
    runtime = json.loads((ROOT / "config/services/mac-standalone-production.json").read_text())
    api = next(item for item in runtime["services"] if item["service_id"] == "aicontrolcenter-api")
    assert (api["listen_host"], api["port"]) == ("127.0.0.1", 58081)
    assert '"host.docker.internal:host-gateway"' in compose
    assert "http://host.docker.internal:58081" in plugin
    assert "https://bokstory.duckdns.org" not in plugin
    assert "host.docker.internal:8000" not in plugin
    assert "wp_remote_get" in client
    assert "reverse_proxy 127.0.0.1:58081" in PUBLIC


def test_browser_source_has_no_direct_woo_or_credential_access():
    sources = [
        (ROOT / "core/homepage/ui/storefront.js").read_text(),
        (ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-ui.js").read_text(),
    ]
    browser_source = "\n".join(sources)
    for forbidden in ("wc/v3", "consumer_key", "consumer_secret", "Authorization", "wp-json"):
        assert forbidden not in browser_source


def test_legacy_storefront_path_is_deterministically_redirected():
    assert "@legacy_storefront path /homepage/storefront" in PUBLIC
    assert "redir @legacy_storefront / 301" in PUBLIC


def test_schema_registry_and_logging_artifact_hashes_are_consistent():
    validate_contract_payload(registry=load_schema_registry(), contract_name="CaddySitePolicy", payload=POLICY)
    registry = load_schema_registry()
    assert registry.contracts["CaddySitePolicy"].path == "caddy-site-policy.schema.json"
    logging = json.loads((ROOT / "config/deployment/shopping-logging-policy.json").read_text())
    for path, expected in logging["reviewed_repository_artifacts"].items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert actual == expected, path


def test_public_edge_routes_only_reads_and_never_wordpress_dev():
    assert 'handle @public_shopping_read' in PUBLIC
    assert 'reverse_proxy 127.0.0.1:58081' in PUBLIC
    assert 'reverse_proxy 127.0.0.1:18080' not in PUBLIC
    assert PUBLIC.rfind('reverse_proxy 127.0.0.1:58082') > PUBLIC.index('handle @public_shopping_read')
