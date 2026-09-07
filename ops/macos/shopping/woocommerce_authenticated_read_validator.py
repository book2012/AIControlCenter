"""One-shot authenticated catalog evidence; public namespace evidence is separate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from core.shopping.secure_runtime import (
    DEFAULT_WOOCOMMERCE_READ_SECRET_PATH,
    WooCommerceReadSecretFileProvider,
)
from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter
from core.shopping.adapters.woocommerce_read_transport import WooCommerceReadTransportSession
from core.shopping.governance.external_read_policy import evaluate_external_read

from ops.macos.shopping.repository_service_start import (
    ShoppingRepositoryPaths,
    load_shopping_repository_facts,
)


class _ReadFailure(Exception):
    def __init__(self, reason: str):
        self.reason = reason


class _StatusCheckedReadTransport:
    """Intercept status before the legacy adapter can read error bodies."""

    def __init__(self):
        self._transport = WooCommerceReadTransportSession()
        self.accepted = False

    def get(self, *args, **kwargs):
        response = self._transport.get(*args, **kwargs)
        status = response.status_code
        if type(status) is not int or not 100 <= status <= 599:
            response.close()
            raise _ReadFailure("MALFORMED_EVIDENCE")
        if status != 200:
            response.close()
            raise _ReadFailure(
                "AUTHENTICATION_REJECTED" if status in {401, 403} else "API_UNAVAILABLE"
            )
        self.accepted = True
        return response


def validate_once() -> dict:
    """No caller-selected credentials, configuration, target, or retry authority."""
    result = {
        "schema_version": "1.0",
        "authoritative_work_item": "SHOP-SERVICE-START-01B",
        "mode": "READ_ONLY",
        "validator": "woocommerce_authenticated_read",
        "namespace_evidence_source": "credential_blind_service_start_observer",
        "namespace_evidence_required": True,
        "credential_boundary_valid": False,
        "authentication_accepted": None,
        "api_readable": False,
        "catalog_readable": False,
        "catalog_empty": None,
        "catalog_total": None,
        "catalog_scope": "published_products",
        "automatic_retry": False,
        "mutation_performed": False,
        "secret_values_exposed": False,
        "production_authority": False,
        "ubuntu_authority": False,
        "status": "BLOCKED",
        "reason_codes": ["CREDENTIAL_BOUNDARY_INVALID"],
    }
    try:
        secret = WooCommerceReadSecretFileProvider(
            DEFAULT_WOOCOMMERCE_READ_SECRET_PATH
        ).load()
    except Exception:
        return result
    result["credential_boundary_valid"] = True
    try:
        facts = load_shopping_repository_facts(
            ShoppingRepositoryPaths.canonical(Path(__file__).resolve().parents[3])
        )
        port = facts["wordpress_port"]
        if (
            facts["runtime_owner"] != "mac"
            or facts["ubuntu_dependency"] is not False
            or facts["mariadb_host_published_port"] is not False
            or facts["wordpress_bind_host"] != "127.0.0.1"
            or type(port) is not int or not 1 <= port <= 65535
            or facts["woocommerce_host_service_id"] != "shopping-runtime"
            or facts["woocommerce_kind"] != "wordpress-plugin-commerce-engine"
        ):
            raise ValueError("invalid repository target")
        connect_base_url = f"http://127.0.0.1:{port}"
    except Exception:
        result["reason_codes"] = ["RUNTIME_TARGET_INVALID"]
        return result
    result.update(connect_target_source="repository_service_start", connect_target_loopback=True)
    transport = None
    response = None
    try:
        query = {"context": "view", "status": "publish", "page": "1", "per_page": "1"}
        decision = evaluate_external_read(
            provider="woocommerce", method="GET", path="/wp-json/wc/v3/products", query=query,
        )
        if decision.allowed is not True:
            raise _ReadFailure("EXTERNAL_READ_POLICY_DENIED")
        transport = _StatusCheckedReadTransport()
        adapter = WooCommerceRESTAdapter(
            base_url=secret.base_url,
            connect_base_url=connect_base_url,
            consumer_key=secret.consumer_key,
            consumer_secret=secret.consumer_secret,
            session=transport,
        )
        response = adapter._request("/products", params=query)
        result.update(authentication_accepted=True, api_readable=True)
        payload = response.json()
        total_value = response.headers.get("X-WP-Total")
        if (
            not isinstance(payload, list) or len(payload) > 1
            or any(not isinstance(item, dict) or type(item.get("id")) is not int
                   or item["id"] <= 0 for item in payload)
            or not isinstance(total_value, str) or not total_value.isascii()
            or not total_value.isdecimal()
        ):
            raise _ReadFailure("MALFORMED_EVIDENCE")
        total = int(total_value)
        if (total == 0) != (len(payload) == 0):
            raise _ReadFailure("MALFORMED_EVIDENCE")
        result.update(catalog_readable=True, catalog_empty=total == 0,
                      catalog_total=total, status="READY", reason_codes=["READY"])
    except _ReadFailure as error:
        result["reason_codes"] = [error.reason]
        if error.reason == "AUTHENTICATION_REJECTED":
            result["authentication_accepted"] = False
        if error.reason == "MALFORMED_EVIDENCE" and transport and transport.accepted:
            result["reason_codes"] = ["CATALOG_UNREADABLE", "MALFORMED_EVIDENCE"]
    except Exception:
        result["reason_codes"] = (
            ["CATALOG_UNREADABLE", "MALFORMED_EVIDENCE"]
            if transport and transport.accepted else ["API_UNAVAILABLE"]
        )
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
    return result


def main() -> int:
    # Do not let argparse echo rejected arguments that may contain secrets.
    if len(sys.argv) != 1:
        print('{"status":"BLOCKED","reason_codes":["CLI_ARGUMENTS_PROHIBITED"]}')
        return 2
    result = validate_once()
    print(json.dumps(result, allow_nan=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
