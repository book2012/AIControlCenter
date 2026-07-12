from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from decimal import Decimal
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from core.shopping.models import Product


class WooCommerceAPIError(RuntimeError):
    pass


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

        if self._uses_https:
            auth = (
                self.consumer_key,
                self.consumer_secret,
            )
        else:
            query.update(
                self._oauth_params(
                    method="GET",
                    url=signature_url,
                    params=query,
                )
            )

        try:
            response = self.session.get(
                request_url,
                params=query,
                auth=auth,
                headers=headers,
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise WooCommerceAPIError(
                f"WooCommerce request failed: {error}"
            ) from error

        if response.status_code >= 400:
            try:
                payload = response.json()
                code = payload.get("code", "unknown")
                message = payload.get("message", "")
            except ValueError:
                code = "unknown"
                message = response.text[:200]

            raise WooCommerceAPIError(
                "WooCommerce returned "
                f"HTTP {response.status_code}: {code}: {message}"
            )

        return response

    @staticmethod
    def _to_product(data: dict[str, Any]) -> Product:
        categories = data.get("categories") or []
        images = data.get("images") or []

        category = (
            categories[0].get("name", "Uncategorized")
            if categories
            else "Uncategorized"
        )

        image_url = None

        if images:
            first_image = images[0] or {}
            image_url = (
                first_image.get("src")
                or first_image.get("thumbnail")
            )

        return Product(
            id=str(data["id"]),
            name=str(data.get("name", "")),
            slug=str(data.get("slug", "")),
            description=str(data.get("description", "")),
            price=Decimal(str(data.get("price") or "0")),
            currency="KRW",
            category=str(category),
            in_stock=data.get("stock_status") == "instock",
            source="woocommerce",
            image_url=(
                str(image_url)
                if image_url
                else None
            ),
        )

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

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        response = self._request(
            "/products",
            params={
                "page": page,
                "per_page": page_size,
                "status": "publish",
            },
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

    def get_product(
        self,
        product_id: str,
    ) -> Product | None:
        try:
            response = self._request(
                f"/products/{product_id}",
            )
        except WooCommerceAPIError as error:
            if "HTTP 404" in str(error):
                return None
            raise

        return self._to_product(response.json())

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
