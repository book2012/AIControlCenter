from __future__ import annotations

import json

from core.shopping.governance.external_read_policy import (
    evaluate_external_read,
    external_read_policy_manifest,
)


def test_manifest_is_get_only_and_deny_by_default():
    manifest = external_read_policy_manifest()

    assert manifest["default_decision"] == "DENY"
    assert manifest["authorization_before_network"] is True
    assert manifest["http"]["allowed_methods"] == ["GET"]
    assert manifest["http"]["max_retries"] == 0
    assert manifest["http"]["retry_status_codes"] == []
    assert manifest["http"]["max_retry_after_seconds"] == 0
    assert manifest["safety"]["write_operations_enabled"] is False


def test_all_allowed_list_routes():
    cases = (
        (
            "woocommerce",
            "/wp-json/wc/v3/products",
            "shopping.product.list",
        ),
        (
            "wordpress",
            "/wp-json/wp/v2/posts",
            "shopping.content.list",
        ),
        (
            "wordpress",
            "/wp-json/wp/v2/pages",
            "shopping.content.list",
        ),
    )

    for provider, path, capability in cases:
        decision = evaluate_external_read(
            provider=provider,
            method="GET",
            path=path,
            query={"context": "view"},
        )

        assert decision.allowed is True
        assert decision.capability_id == capability


def test_all_allowed_detail_routes():
    cases = (
        (
            "woocommerce",
            "/wp-json/wc/v3/products/42",
            "shopping.product.get",
        ),
        (
            "woocommerce",
            "/wp-json/wc/v3/orders/42",
            "shopping.order.summary.get",
        ),
        (
            "wordpress",
            "/wp-json/wp/v2/posts/5",
            "shopping.content.get",
        ),
        (
            "wordpress",
            "/wp-json/wp/v2/pages/7",
            "shopping.content.get",
        ),
    )

    for provider, path, capability in cases:
        decision = evaluate_external_read(
            provider=provider,
            method="GET",
            path=path,
            query={"context": "view"},
        )

        assert decision.allowed is True
        assert decision.capability_id == capability


def test_invalid_detail_identifiers_are_denied():
    for path in (
        "/wp-json/wc/v3/products/not-id",
        "/wp-json/wc/v3/products/0",
        "/wp-json/wp/v2/posts/-1",
    ):
        provider = (
            "woocommerce"
            if "/wc/"
            in path
            else "wordpress"
        )

        decision = evaluate_external_read(
            provider=provider,
            method="GET",
            path=path,
        )

        assert decision.allowed is False


def test_write_methods_are_denied():
    for method in (
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ):
        decision = evaluate_external_read(
            provider="woocommerce",
            method=method,
            path="/wp-json/wc/v3/products",
        )

        assert decision.allowed is False
        assert decision.reason_code == "http_method_not_allowed"


def test_unknown_provider_route_query_and_edit_context_are_denied():
    cases = (
        dict(
            provider="unknown",
            method="GET",
            path="/wp-json/wc/v3/products",
        ),
        dict(
            provider="woocommerce",
            method="GET",
            path="/wp-json/wc/v3/customers",
        ),
        dict(
            provider="woocommerce",
            method="GET",
            path="/wp-json/wc/v3/products",
            query={"future_parameter": "1"},
        ),
        dict(
            provider="wordpress",
            method="GET",
            path="/wp-json/wp/v2/posts",
            query={"context": "edit"},
        ),
    )

    for kwargs in cases:
        decision = evaluate_external_read(
            **kwargs
        )

        assert decision.allowed is False


def test_manifest_is_json_serializable_and_safe():
    manifest = external_read_policy_manifest()

    assert json.dumps(
        manifest,
        sort_keys=True,
    )

    assert len(
        manifest["routes"]
    ) == 7

    assert manifest["safety"] == {
        "write_operations_enabled": False,
        "automatic_publishing_enabled": False,
        "automatic_schema_adoption_enabled": False,
        "automatic_schema_migration_enabled": False,
        "secret_values_in_logs": False,
        "secret_values_in_evidence": False,
        "raw_auth_headers_in_logs": False,
    }

    assert manifest["ubuntu"] == {
        "business_logic_allowed": False,
        "application_state_allowed": False,
        "ai_workload_allowed": False,
    }
