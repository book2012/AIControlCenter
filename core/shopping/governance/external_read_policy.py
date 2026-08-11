from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


POLICY_VERSION = "1.0.0"

DEFAULT_DECISION = "DENY"

ALLOWED_HTTP_METHODS = ("GET",)

WRITE_HTTP_METHODS = (
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
)

CONNECT_TIMEOUT_SECONDS = 5.0
READ_TIMEOUT_SECONDS = 15.0
TOTAL_TIMEOUT_SECONDS = 20.0

MAX_RETRIES = 0
RETRY_STATUS_CODES: tuple[int, ...] = ()
MAX_RETRY_AFTER_SECONDS = 0

AUTHORIZATION_BEFORE_NETWORK = True

WRITE_OPERATIONS_ENABLED = False
AUTOMATIC_PUBLISHING_ENABLED = False
AUTOMATIC_SCHEMA_ADOPTION_ENABLED = False
AUTOMATIC_SCHEMA_MIGRATION_ENABLED = False

SECRET_VALUES_IN_LOGS = False
SECRET_VALUES_IN_EVIDENCE = False
RAW_AUTH_HEADERS_IN_LOGS = False

UBUNTU_BUSINESS_LOGIC_ALLOWED = False
UBUNTU_APPLICATION_STATE_ALLOWED = False
UBUNTU_AI_WORKLOAD_ALLOWED = False


class ExternalProvider(str, Enum):
    WOOCOMMERCE = "woocommerce"
    WORDPRESS = "wordpress"


@dataclass(frozen=True)
class ExternalReadRule:
    provider: ExternalProvider
    path_template: str
    capability_id: str
    query_keys: tuple[str, ...]
    context_values: tuple[str, ...]
    authentication_required: bool


@dataclass(frozen=True)
class ExternalReadDecision:
    allowed: bool
    decision: str
    reason_code: str
    provider: str
    capability_id: str | None
    path_template: str | None


WOOCOMMERCE_PRODUCT_QUERY_KEYS = (
    "context",
    "page",
    "per_page",
    "search",
    "after",
    "before",
    "modified_after",
    "modified_before",
    "include",
    "exclude",
    "offset",
    "order",
    "orderby",
    "sku",
    "slug",
    "status",
    "category",
    "tag",
    "featured",
    "on_sale",
    "min_price",
    "max_price",
    "stock_status",
)

WORDPRESS_CONTENT_QUERY_KEYS = (
    "context",
    "page",
    "per_page",
    "search",
    "after",
    "modified_after",
    "before",
    "modified_before",
    "exclude",
    "include",
    "offset",
    "order",
    "orderby",
    "slug",
    "status",
)


EXTERNAL_READ_RULES = (
    ExternalReadRule(
        provider=ExternalProvider.WOOCOMMERCE,
        path_template="/wp-json/wc/v3/products",
        capability_id="shopping.product.list",
        query_keys=WOOCOMMERCE_PRODUCT_QUERY_KEYS,
        context_values=("view",),
        authentication_required=True,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WOOCOMMERCE,
        path_template="/wp-json/wc/v3/products/{id}",
        capability_id="shopping.product.get",
        query_keys=("context",),
        context_values=("view",),
        authentication_required=True,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WOOCOMMERCE,
        path_template="/wp-json/wc/v3/orders/{id}",
        capability_id="shopping.order.summary.get",
        query_keys=("context",),
        context_values=("view",),
        authentication_required=True,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WORDPRESS,
        path_template="/wp-json/wp/v2/posts",
        capability_id="shopping.content.list",
        query_keys=WORDPRESS_CONTENT_QUERY_KEYS + ("sticky",),
        context_values=("view", "embed"),
        authentication_required=False,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WORDPRESS,
        path_template="/wp-json/wp/v2/posts/{id}",
        capability_id="shopping.content.get",
        query_keys=("context",),
        context_values=("view", "embed"),
        authentication_required=False,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WORDPRESS,
        path_template="/wp-json/wp/v2/pages",
        capability_id="shopping.content.list",
        query_keys=WORDPRESS_CONTENT_QUERY_KEYS
        + (
            "parent",
            "parent_exclude",
            "menu_order",
        ),
        context_values=("view", "embed"),
        authentication_required=False,
    ),
    ExternalReadRule(
        provider=ExternalProvider.WORDPRESS,
        path_template="/wp-json/wp/v2/pages/{id}",
        capability_id="shopping.content.get",
        query_keys=("context",),
        context_values=("view", "embed"),
        authentication_required=False,
    ),
)


def _path_matches(
    template: str,
    path: str,
) -> bool:
    if template.endswith("/{id}"):
        prefix = template[:-5]

        if not path.startswith(
            prefix + "/"
        ):
            return False

        identifier = path[
            len(prefix) + 1:
        ]

        return (
            identifier.isdigit()
            and int(identifier) > 0
        )

    return path == template


def _normalize_provider(
    provider: ExternalProvider | str,
) -> ExternalProvider | None:
    if isinstance(
        provider,
        ExternalProvider,
    ):
        return provider

    try:
        return ExternalProvider(
            str(provider)
        )
    except ValueError:
        return None


def _context_value(
    value: str | Sequence[str],
) -> str:
    if isinstance(
        value,
        str,
    ):
        return value

    for item in value:
        return str(item)

    return ""


def evaluate_external_read(
    *,
    provider: ExternalProvider | str,
    method: str,
    path: str,
    query: Mapping[
        str,
        str | Sequence[str],
    ] | None = None,
) -> ExternalReadDecision:
    normalized_provider = _normalize_provider(
        provider
    )

    if normalized_provider is None:
        return ExternalReadDecision(
            False,
            "DENY",
            "provider_not_registered",
            str(provider),
            None,
            None,
        )

    if method.upper() not in ALLOWED_HTTP_METHODS:
        return ExternalReadDecision(
            False,
            "DENY",
            "http_method_not_allowed",
            normalized_provider.value,
            None,
            None,
        )

    rule = None

    for candidate in EXTERNAL_READ_RULES:
        if (
            candidate.provider
            is normalized_provider
            and _path_matches(
                candidate.path_template,
                path,
            )
        ):
            rule = candidate
            break

    if rule is None:
        return ExternalReadDecision(
            False,
            "DENY",
            "route_not_allowed",
            normalized_provider.value,
            None,
            None,
        )

    normalized_query = query or {}

    if (
        set(normalized_query)
        - set(rule.query_keys)
    ):
        return ExternalReadDecision(
            False,
            "DENY",
            "query_key_not_allowed",
            normalized_provider.value,
            rule.capability_id,
            rule.path_template,
        )

    if "context" in normalized_query:
        context = _context_value(
            normalized_query["context"]
        )

        if context not in rule.context_values:
            return ExternalReadDecision(
                False,
                "DENY",
                "context_not_allowed",
                normalized_provider.value,
                rule.capability_id,
                rule.path_template,
            )

    return ExternalReadDecision(
        True,
        "ALLOW",
        "read_route_allowed",
        normalized_provider.value,
        rule.capability_id,
        rule.path_template,
    )


def external_read_policy_manifest() -> dict[str, Any]:
    return {
        "version": POLICY_VERSION,
        "default_decision": DEFAULT_DECISION,
        "authorization_before_network": AUTHORIZATION_BEFORE_NETWORK,
        "http": {
            "allowed_methods": list(ALLOWED_HTTP_METHODS),
            "write_methods": list(WRITE_HTTP_METHODS),
            "connect_timeout_seconds": CONNECT_TIMEOUT_SECONDS,
            "read_timeout_seconds": READ_TIMEOUT_SECONDS,
            "total_timeout_seconds": TOTAL_TIMEOUT_SECONDS,
            "max_retries": MAX_RETRIES,
            "retry_status_codes": list(RETRY_STATUS_CODES),
            "max_retry_after_seconds": MAX_RETRY_AFTER_SECONDS,
        },
        "safety": {
            "write_operations_enabled": WRITE_OPERATIONS_ENABLED,
            "automatic_publishing_enabled": AUTOMATIC_PUBLISHING_ENABLED,
            "automatic_schema_adoption_enabled": AUTOMATIC_SCHEMA_ADOPTION_ENABLED,
            "automatic_schema_migration_enabled": AUTOMATIC_SCHEMA_MIGRATION_ENABLED,
            "secret_values_in_logs": SECRET_VALUES_IN_LOGS,
            "secret_values_in_evidence": SECRET_VALUES_IN_EVIDENCE,
            "raw_auth_headers_in_logs": RAW_AUTH_HEADERS_IN_LOGS,
        },
        "ubuntu": {
            "business_logic_allowed": UBUNTU_BUSINESS_LOGIC_ALLOWED,
            "application_state_allowed": UBUNTU_APPLICATION_STATE_ALLOWED,
            "ai_workload_allowed": UBUNTU_AI_WORKLOAD_ALLOWED,
        },
        "routes": [
            {
                "provider": rule.provider.value,
                "path_template": rule.path_template,
                "capability_id": rule.capability_id,
                "query_keys": list(rule.query_keys),
                "context_values": list(rule.context_values),
                "authentication_required": rule.authentication_required,
            }
            for rule in EXTERNAL_READ_RULES
        ],
    }
