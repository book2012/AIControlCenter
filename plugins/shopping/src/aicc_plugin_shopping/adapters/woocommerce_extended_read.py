"""Non-product reads with explicit ports; no credentials or HTTP defaults."""
from typing import Any
import re
from aicc_plugin_shopping.models import Product
from .woocommerce_product_read import WooCommerceProductReadAdapter, WooCommerceAPIError
from aicc_plugin_shopping.observability.health_probe import HealthFailureCode


class WooCommerceCatalogReadAdapter(WooCommerceProductReadAdapter):
    @staticmethod
    def _validate_scope(path, params):
        if path == "/products/categories":
            if not isinstance(params, dict) or any(str(k).lower().startswith(("oauth_", "consumer_", "authorization")) for k in params):
                raise WooCommerceAPIError("invalid category read", failure_code=HealthFailureCode.AUTHORIZATION)
            return
        WooCommerceProductReadAdapter._validate_scope(path, params)

    def list_categories(self) -> list[dict[str, Any]]:
        response = self._request(
            "/products/categories",
            params={
                "per_page": 100,
                "hide_empty": "false",
            },
        )

        return [
            {
                "id": str(item["id"]),
                "name": str(item.get("name", "")),
                "slug": str(item.get("slug", "")),
                "count": int(item.get("count", 0)),
            }
            for item in response.json()
        ]

    def search_products(
        self,
        *,
        query: str | None,
        category: str | None,
        minimum_price: float | None,
        maximum_price: float | None,
        in_stock: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        params: dict[str, Any] = {
            "page": page,
            "per_page": page_size,
            "status": "publish",
        }

        if query:
            params["search"] = query

        if category:
            params["category"] = category

        if minimum_price is not None:
            params["min_price"] = str(minimum_price)

        if maximum_price is not None:
            params["max_price"] = str(maximum_price)

        if in_stock is True:
            params["stock_status"] = "instock"
        elif in_stock is False:
            params["stock_status"] = "outofstock"

        response = self._request(
            "/products",
            params=params,
        )

        products = [
            self._to_product(item)
            for item in response.json()
        ]

        total = int(
            response.headers.get(
                "X-WP-Total",
                len(products),
            )
        )

        return products, total


class _OrderRequest(WooCommerceProductReadAdapter):
    @staticmethod
    def _validate_scope(path, params):
        if (not isinstance(path, str) or re.fullmatch(r"/orders/[1-9][0-9]{0,19}", path) is None
                or not isinstance(params, dict) or set(params) != {"context"} or params["context"] != "view"):
            raise WooCommerceAPIError("invalid order read", failure_code=HealthFailureCode.AUTHORIZATION)


class WooCommerceOrderReadAdapter:
    def __init__(self, request_port, *, authorize):
        self._order_request = _OrderRequest(request_port, authorize=authorize)

    def _request(self, path, params=None):
        return self._order_request._request(path, params)

    def get_order_summary_raw(
        self,
        order_id: str,
    ) -> dict[str, Any] | None:
        try:
            response = self._request(
                "/orders/" + str(order_id),
                params={"context": "view"},
            )
        except WooCommerceAPIError as error:
            if error.status_code == 404:
                return None
            raise
        payload = response.json()
        if not isinstance(payload, dict):
            raise WooCommerceAPIError("invalid order payload")
        return dict(payload)
