from __future__ import annotations

import time
from typing import Any, Callable

import requests

class WooCommerceReadTransportSession:
    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        connect_timeout_seconds: float = 5.0,
        read_timeout_seconds: float = 15.0,
        total_timeout_seconds: float = 20.0,
        max_retries: int = 0,
        retry_after_max_seconds: float = 0.0,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if connect_timeout_seconds <= 0 or read_timeout_seconds <= 0 or total_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")
        self._session = session or requests.Session()
        self.connect_timeout_seconds = float(connect_timeout_seconds)
        self.read_timeout_seconds = float(read_timeout_seconds)
        self.total_timeout_seconds = float(total_timeout_seconds)
        # Retained as disabled compatibility projections only. Constructor
        # arguments cannot grant retry authority.
        self.max_retries = 0
        self.retry_after_max_seconds = 0.0
        self._monotonic = monotonic

    def get(
        self,
        url: str,
        *,
        params: Any = None,
        auth: Any = None,
        headers: Any = None,
        timeout: Any = None,
        allow_redirects: bool = False,
    ) -> requests.Response:
        if allow_redirects is not False:
            raise ValueError("redirects must remain disabled")
        started = self._monotonic()
        elapsed = self._monotonic() - started
        remaining = self.total_timeout_seconds - elapsed
        if remaining <= 0:
            raise requests.Timeout("WooCommerce total read deadline exceeded")
        connect_timeout = min(self.connect_timeout_seconds, remaining)
        read_timeout = min(self.read_timeout_seconds, remaining)
        response = self._session.get(
            url,
            params=params,
            auth=auth,
            headers=headers,
            timeout=(connect_timeout, read_timeout),
            allow_redirects=False,
        )
        elapsed = self._monotonic() - started
        if elapsed > self.total_timeout_seconds:
            closer = getattr(response, "close", None)
            if callable(closer):
                closer()
            raise requests.Timeout("WooCommerce total read deadline exceeded")
        return response
