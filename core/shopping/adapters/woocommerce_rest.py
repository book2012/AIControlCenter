from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from core.shopping.models import Product
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable
from core.shopping.adapters.woocommerce_read_transport import WooCommerceReadTransportSession
from core.shopping.governance.external_read_policy import evaluate_external_read


class WooCommerceAPIError(CatalogReadUnavailable):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _percent_encode(value: Any) -> str:
    return quote(str(value), safe="~-._")


class WooCommerceRESTAdapter:
    def __init__(
        self,
        base_url: str,
        consumer_key: str,
        consumer_secret: str,
        timeout_seconds: int = 10,
        session: requests.Session | None = None,
        connect_base_url: str | None = None,
    ):
        for value in (base_url, connect_base_url or base_url):
            parsed = urlsplit(value)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.username is not None or parsed.password is not None
                    or parsed.query or parsed.fragment
                    or any(ord(char) < 33 for char in value)):
                raise WooCommerceAPIError("Invalid WooCommerce identity")
        self.base_url = base_url.rstrip("/")
        self.connect_base_url = (
            connect_base_url.rstrip("/")
            if connect_base_url
            else self.base_url
        )
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.trust_env = False
        self._transport = WooCommerceReadTransportSession(
            session=self.session,
            connect_timeout_seconds=min(5.0, timeout_seconds),
            read_timeout_seconds=min(15.0, timeout_seconds),
            total_timeout_seconds=min(20.0, timeout_seconds),
        )

    @property
    def _uses_https(self) -> bool:
        return self.base_url.lower().startswith("https://")

    def _oauth_params(
        self,
        method: str,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, str]:
        oauth = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": str(int(time.time())),
        }

        signature_params = {
            **{key: str(value) for key, value in params.items()},
            **oauth,
        }

        encoded_pairs = sorted(
            (
                _percent_encode(key),
                _percent_encode(value),
            )
            for key, value in signature_params.items()
        )

        normalized = "&".join(
            f"{key}={value}"
            for key, value in encoded_pairs
        )

        split = urlsplit(url)
        base_uri = urlunsplit(
            (
                split.scheme,
                split.netloc,
                split.path,
                "",
                "",
            )
        )

        signature_base = "&".join(
            (
                method.upper(),
                _percent_encode(base_uri),
                _percent_encode(normalized),
            )
        )

        signing_key = f"{_percent_encode(self.consumer_secret)}&"

        digest = hmac.new(
            signing_key.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        oauth["oauth_signature"] = base64.b64encode(
            digest
        ).decode("ascii")

        return oauth

    def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        query = dict(params or {})
        if (not path.startswith("/") or any(char in path for char in "?#\\")
                or any(str(key).lower().startswith(("oauth_", "consumer_", "authorization"))
                       for key in query)):
            raise WooCommerceAPIError("Invalid WooCommerce read request")
        signature_url = (
            f"{self.base_url}/wp-json/wc/v3{path}"
        )
        request_url = (
            f"{self.connect_base_url}/wp-json/wc/v3{path}"
        )

        auth = None
        headers = {}

        if self.connect_base_url != self.base_url:
            headers["Host"] = urlsplit(
                self.base_url
            ).netloc

        if self._uses_https and self.connect_base_url.lower().startswith("https://"):
            auth = (
                self.consumer_key,
                self.consumer_secret,
            )
        else:
            oauth = self._oauth_params("GET", signature_url, query)
            headers["Authorization"] = "OAuth " + ", ".join(
                f'{_percent_encode(key)}="{_percent_encode(value)}"'
                for key, value in sorted(oauth.items())
            )

        failed = False
        try:
            response = self._transport.get(
                request_url,
                params=query,
                auth=auth,
                headers=headers,
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
        except requests.RequestException:
            failed = True
        finally:
            headers.pop("Authorization", None)

        if failed:
            raise WooCommerceAPIError("WooCommerce request failed")

        if response.status_code != 200:
            raise WooCommerceAPIError(
                f"WooCommerce returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

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
            # Normalize equivalent vendor money strings without decimal-context rounding.
            amount = format(price, "f")
            if "." in amount:
                amount = amount.rstrip("0").rstrip(".")
            return Product(
                id=str(data["id"]), name=name, slug=slug, description=description,
                price=Decimal(amount), currency="KRW", category=category,
                in_stock=stock_status == "instock", source="woocommerce", image_url=image_url,
            )
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise WooCommerceAPIError("Invalid WooCommerce product payload") from None

    @staticmethod
    def _product_identifier(product_id: str) -> str:
        if (not isinstance(product_id, str) or not product_id.isascii()
                or not product_id.isdecimal() or len(product_id) > 20
                or product_id.startswith("0")):
            raise CatalogReadQueryError("shopping_invalid_product_query")
        return product_id

    @staticmethod
    def _authorize_product_read(path: str, params: dict[str, Any]) -> None:
        decision = evaluate_external_read(
            provider="woocommerce", method="GET", path="/wp-json/wc/v3" + path,
            query={key: str(value) for key, value in params.items()},
        )
        if not decision.allowed:
            raise WooCommerceAPIError("WooCommerce product read denied")

    @staticmethod
    def _json_payload(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            raise WooCommerceAPIError("Invalid WooCommerce JSON") from None

    def health(self) -> dict:
        response = self._request(
            "/products",
            params={
                "page": 1,
                "per_page": 1,
            },
        )

        return {
            "healthy": response.status_code == 200,
            "source": "woocommerce",
            "status_code": response.status_code,
            "transport": (
                "https_basic"
                if self._uses_https
                else "http_oauth1"
            ),
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
            raise WooCommerceAPIError("invalid product payload")
        if type(payload.get("id")) is not int or str(payload["id"]) != identifier:
            raise WooCommerceAPIError("WooCommerce product identity mismatch")
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
            raise WooCommerceAPIError("invalid product list payload")
        items = []
        for item in payload:
            if not isinstance(item, dict):
                raise WooCommerceAPIError("invalid product list item")
            items.append(dict(item))
        raw_total = response.headers.get("X-WP-Total")
        if (not isinstance(raw_total, str) or not raw_total.isascii()
                or not raw_total.isdecimal() or len(raw_total) > 20):
            raise WooCommerceAPIError("Invalid WooCommerce product total")
        total = int(raw_total)
        expected_count = min(page_size, max(0, total - (page - 1) * page_size))
        identifiers = [item.get("id") for item in items]
        if (len(items) != expected_count
                or any(type(identifier) is not int or identifier <= 0 for identifier in identifiers)
                or identifiers != sorted(set(identifiers))):
            raise WooCommerceAPIError("Inconsistent WooCommerce product page")
        return items, total

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
            if "HTTP 404" in str(error):
                return None
            raise
        payload = response.json()
        if not isinstance(payload, dict):
            raise WooCommerceAPIError("invalid order payload")
        return dict(payload)

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        items, total = self.list_products_raw(page, page_size)
        if any(item.get("status") != "publish" for item in items):
            raise WooCommerceAPIError("Unexpected WooCommerce product visibility")
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
            raise WooCommerceAPIError("Invalid WooCommerce product visibility")
        if visibility in {"draft", "pending", "private", "trash", "future"}:
            return None
        if visibility != "publish":
            raise WooCommerceAPIError("Invalid WooCommerce product visibility")
        return self._to_product(payload)

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
