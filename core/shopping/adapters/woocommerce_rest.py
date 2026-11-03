from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from core.shopping.models import Product, ProductVariant
from aicc_plugin_shopping.adapters.woocommerce_product_read import (
    WooCommerceAPIError, WooCommerceProductReadAdapter,
)
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable
from core.shopping.observability.health_probe import HealthFailureCode
from aicc_plugin_shopping.adapters.woocommerce_extended_read import WooCommerceCatalogReadAdapter, WooCommerceOrderReadAdapter
from core.shopping.adapters.woocommerce_read_transport import WooCommerceReadTransportSession
from core.shopping.governance.external_read_policy import evaluate_external_read




def _percent_encode(value: Any) -> str:
    return quote(str(value), safe="~-._")


class WooCommerceRESTAdapter(WooCommerceCatalogReadAdapter, WooCommerceOrderReadAdapter):
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
                raise WooCommerceAPIError("Invalid WooCommerce identity",
                                          failure_code=HealthFailureCode.CONFIGURATION)
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
    def transport_kind(self) -> str:
        return "https_basic" if self._uses_https else "http_oauth1"

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
            raise WooCommerceAPIError("Invalid WooCommerce read request",
                                      failure_code=HealthFailureCode.AUTHORIZATION)
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

        failure = None
        try:
            response = self._transport.get(
                request_url,
                params=query,
                auth=auth,
                headers=headers,
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
        except requests.Timeout:
            failure = HealthFailureCode.TIMEOUT
        except requests.RequestException:
            failure = HealthFailureCode.TRANSPORT
        finally:
            headers.pop("Authorization", None)

        if failure is not None:
            raise WooCommerceAPIError("WooCommerce request failed", failure_code=failure)

        if response.status_code != 200:
            raise WooCommerceAPIError(
                f"WooCommerce returned HTTP {response.status_code}",
                status_code=response.status_code,
                failure_code={
                    401: HealthFailureCode.AUTHENTICATION,
                    403: HealthFailureCode.AUTHORIZATION,
                    429: HealthFailureCode.RATE_LIMIT,
                }.get(response.status_code, HealthFailureCode.DEPENDENCY_UNAVAILABLE),
            )

        return response




    @staticmethod
    def _authorize_product_read(path: str, params: dict[str, Any]) -> None:
        decision = evaluate_external_read(
            provider="woocommerce", method="GET", path="/wp-json/wc/v3" + path,
            query={key: str(value) for key, value in params.items()},
        )
        if not decision.allowed:
            raise WooCommerceAPIError("WooCommerce product read denied",
                                      failure_code=HealthFailureCode.AUTHORIZATION)
