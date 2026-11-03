"""WooCommerce product reads behind explicit authorization and a trusted read port.

No credentials, URL discovery, signing, requests.Session, retries or live defaults.
The platform-owned port must preserve approved destination/transport boundaries.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Protocol, Callable

from aicc_plugin_shopping.models import Product, ProductVariant
from aicc_plugin_shopping.catalog_ports import CatalogReadQueryError, CatalogReadUnavailable
from aicc_plugin_shopping.observability.health_probe import HealthFailureCode


class WooCommerceAPIError(CatalogReadUnavailable):
    def __init__(self, message: str, *, status_code: int | None = None,
                 failure_code: HealthFailureCode = HealthFailureCode.UNKNOWN):
        super().__init__(message, failure_code=failure_code)
        self.status_code = status_code


class WooCommerceProductReadPort(Protocol):
    def read(self, path: str, *, params: dict[str, Any]) -> Any:
        """Return a response-like object; platform owns any real authentication/I/O."""
        ...


class WooCommerceProductReadAdapter:
    def __init__(self, request_port: WooCommerceProductReadPort, *,
                 authorize: Callable[[str, dict[str, Any]], bool], transport_kind="injected"):
        if not callable(getattr(request_port, "read", None)) or not callable(authorize):
            raise TypeError("explicit read port and authorizer required")
        if transport_kind not in {"injected", "https_basic", "http_oauth1"}:
            raise ValueError("invalid transport description")
        self._request_port = request_port
        self._authorize = authorize
        self._transport_kind = transport_kind

    @property
    def transport_kind(self):
        return self._transport_kind

    @staticmethod
    def _validate_scope(path, params):
        if (not isinstance(path, str) or (path != "/products" and not re.fullmatch(r"/products/[1-9][0-9]{0,19}", path))
                or not isinstance(params, dict)
                or any(str(key).lower().startswith(("oauth_", "consumer_", "authorization")) for key in params)):
            raise WooCommerceAPIError("Invalid WooCommerce product read", failure_code=HealthFailureCode.AUTHORIZATION)

    def _authorize_product_read(self, path, params):
        # Structural preflight; every actual port call authorizes in _request.
        self._validate_scope(path, params)

    def _request(self, path, params=None):
        query = dict(params or {})
        self._validate_scope(path, query)
        try:
            allowed = self._authorize(path, dict(query)) is True
        except Exception:
            allowed = False
        if not allowed:
            raise WooCommerceAPIError("WooCommerce product read denied", failure_code=HealthFailureCode.AUTHORIZATION)
        failure = None
        failure_status = None
        try:
            response = self._request_port.read(path, params=dict(query))
        except WooCommerceAPIError as error:
            failure = error.failure_code
            failure_status = error.status_code if type(error.status_code) is int else None
        except TimeoutError:
            failure = HealthFailureCode.TIMEOUT
        except Exception:
            failure = HealthFailureCode.TRANSPORT
        # Raise outside the handler; raw port errors are not retained as context.
        if failure is not None:
            raise WooCommerceAPIError("WooCommerce request failed", status_code=failure_status, failure_code=failure)
        status = getattr(response, "status_code", None)
        if type(status) is not int or status != 200:
            raise WooCommerceAPIError("WooCommerce product response unavailable", status_code=status if type(status) is int else None,
                failure_code={401: HealthFailureCode.AUTHENTICATION, 403: HealthFailureCode.AUTHORIZATION,
                              429: HealthFailureCode.RATE_LIMIT}.get(status if type(status) is int else None, HealthFailureCode.DEPENDENCY_UNAVAILABLE))
        return response

    @staticmethod
    def _to_product(data: dict[str, Any]) -> Product:
        # Vendor fields terminate here. Only the existing Product DTO escapes.
        try:
            if not isinstance(data, dict) or type(data.get("id")) is not int or data["id"] <= 0:
                raise ValueError
            name = data.get("name")
            slug = data.get("slug", "")
            description = data.get("description", "")
            if (not isinstance(name, str) or not name.strip()
                    or not isinstance(slug, str) or not isinstance(description, str)):
                raise ValueError
            raw_price = data.get("price")
            if not isinstance(raw_price, str) or not raw_price or len(raw_price) > 64:
                raise ValueError
            # WooCommerce money is a decimal string, never a float or exponent.
            parts = raw_price.split(".")
            if len(parts) > 2 or not all(part.isascii() and part.isdecimal() for part in parts):
                raise ValueError
            price = Decimal(raw_price)
            if not price.is_finite() or price < 0 or data.get("currency", "KRW") != "KRW":
                raise ValueError
            stock_status = data.get("stock_status")
            if stock_status not in {"instock", "outofstock", "onbackorder"}:
                raise ValueError
            categories = data.get("categories", [])
            images = data.get("images", [])
            if (not isinstance(categories, list) or not isinstance(images, list)
                    or not all(isinstance(item, dict) for item in categories + images)):
                raise ValueError
            category = categories[0].get("name", "Uncategorized") if categories else "Uncategorized"
            image_url = (images[0].get("src") or images[0].get("thumbnail")) if images else None
            if not isinstance(category, str) or (image_url is not None and not isinstance(image_url, str)):
                raise ValueError
            for value in (name, slug, description, category, image_url):
                if isinstance(value, str):
                    value.encode("utf-8")
            # Normalize equivalent vendor money strings without decimal-context rounding.
            amount = format(price, "f")
            if "." in amount:
                amount = amount.rstrip("0").rstrip(".")
            return Product(
                id=str(data["id"]), name=name, slug=slug, description=description,
                price=Decimal(amount), currency="KRW", category=category,
                in_stock=stock_status == "instock", source="woocommerce", image_url=image_url,
                variants=WooCommerceProductReadAdapter._to_variants(data.get("variants", [])),
            )
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise WooCommerceAPIError("Invalid WooCommerce product payload",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH) from None


    @staticmethod
    def _to_variants(raw: Any) -> tuple[ProductVariant, ...]:
        """Normalize an optional canonical variant projection without inventing options."""
        if raw is None:
            return ()
        if not isinstance(raw, list):
            raise ValueError
        variants = []
        seen = set()
        for item in raw:
            if not isinstance(item, dict):
                raise ValueError
            identifier, label, option_type, available = (item.get(key) for key in ("id", "label", "option_type", "available"))
            if (not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identifier)
                    or not isinstance(label, str) or not label.strip() or any(char.isspace() for char in label)
                    or not isinstance(option_type, str) or not option_type.strip() or not isinstance(available, bool)
                    or identifier in seen):
                raise ValueError
            seen.add(identifier)
            variants.append(ProductVariant(identifier, label, option_type, available))
        return tuple(variants)


    @staticmethod
    def _product_identifier(product_id: str) -> str:
        if (not isinstance(product_id, str) or not product_id.isascii()
                or not product_id.isdecimal() or len(product_id) > 20
                or product_id.startswith("0")):
            raise CatalogReadQueryError("shopping_invalid_product_query")
        return product_id


    @staticmethod
    def _json_payload(response: Any) -> Any:
        try:
            return response.json()
        except ValueError:
            raise WooCommerceAPIError("Invalid WooCommerce JSON",
                                      failure_code=HealthFailureCode.INVALID_PAYLOAD) from None


    def health(self) -> dict:
        # Exercise the exact authorized catalog path, including JSON, pagination,
        # visibility and product mapping. An HTTP 200 alone is not healthy.
        self.list_products(page=1, page_size=1)

        return {
            "healthy": True,
            "source": "woocommerce",
            "status_code": 200,
            "transport": self.transport_kind,
        }


    def get_product_raw(
        self,
        product_id: str,
    ) -> dict[str, Any] | None:
        identifier = self._product_identifier(product_id)
        path = "/products/" + identifier
        params = {"context": "view"}
        self._authorize_product_read(path, params)
        try:
            response = self._request(
                path, params=params,
            )
        except WooCommerceAPIError as error:
            if error.status_code == 404:
                return None
            raise
        payload = self._json_payload(response)
        if not isinstance(payload, dict):
            raise WooCommerceAPIError("invalid product payload",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        if type(payload.get("id")) is not int or str(payload["id"]) != identifier:
            raise WooCommerceAPIError("WooCommerce product identity mismatch",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        return dict(payload)


    def list_products_raw(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        if (type(page) is not int or page < 1 or type(page_size) is not int
                or not 1 <= page_size <= 100):
            raise CatalogReadQueryError("shopping_invalid_product_query")
        params = {"context": "view", "status": "publish", "page": page,
                  "per_page": page_size, "orderby": "id", "order": "asc"}
        self._authorize_product_read("/products", params)
        response = self._request("/products", params=params)
        payload = self._json_payload(response)
        if not isinstance(payload, list):
            raise WooCommerceAPIError("invalid product list payload",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        items = []
        for item in payload:
            if not isinstance(item, dict):
                raise WooCommerceAPIError("invalid product list item",
                                          failure_code=HealthFailureCode.SCHEMA_MISMATCH)
            items.append(dict(item))
        raw_total = response.headers.get("X-WP-Total")
        if (not isinstance(raw_total, str) or not raw_total.isascii()
                or not raw_total.isdecimal() or len(raw_total) > 20):
            raise WooCommerceAPIError("Invalid WooCommerce product total",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        total = int(raw_total)
        expected_count = min(page_size, max(0, total - (page - 1) * page_size))
        identifiers = [item.get("id") for item in items]
        if (len(items) != expected_count
                or any(type(identifier) is not int or identifier <= 0 for identifier in identifiers)
                or identifiers != sorted(set(identifiers))):
            raise WooCommerceAPIError("Inconsistent WooCommerce product page",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        return items, total


    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        items, total = self.list_products_raw(page, page_size)
        if any(item.get("status") != "publish" for item in items):
            raise WooCommerceAPIError("Unexpected WooCommerce product visibility",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        return [self._to_product(item) for item in items], total


    def get_product(
        self,
        product_id: str,
    ) -> Product | None:
        payload = self.get_product_raw(product_id)
        if payload is None:
            return None
        visibility = payload.get("status")
        if not isinstance(visibility, str):
            raise WooCommerceAPIError("Invalid WooCommerce product visibility",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        if visibility in {"draft", "pending", "private", "trash", "future"}:
            return None
        if visibility != "publish":
            raise WooCommerceAPIError("Invalid WooCommerce product visibility",
                                      failure_code=HealthFailureCode.SCHEMA_MISMATCH)
        return self._to_product(payload)
