from __future__ import annotations

import time
from typing import Any, Callable

import requests

RETRY_STATUSES = frozenset({429, 502, 503, 504})

class WooCommerceReadTransportSession:
    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        connect_timeout_seconds: float = 5.0,
        read_timeout_seconds: float = 15.0,
        total_timeout_seconds: float = 20.0,
        max_retries: int = 1,
        retry_after_max_seconds: float = 5.0,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if connect_timeout_seconds <= 0 or read_timeout_seconds <= 0 or total_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")
        if max_retries < 0:
            raise ValueError("max retries must be nonnegative")
        if retry_after_max_seconds < 0:
            raise ValueError("Retry-After cap must be nonnegative")
        self._session = session or requests.Session()
        self.connect_timeout_seconds = float(connect_timeout_seconds)
        self.read_timeout_seconds = float(read_timeout_seconds)
        self.total_timeout_seconds = float(total_timeout_seconds)
        self.max_retries = int(max_retries)
        self.retry_after_max_seconds = float(retry_after_max_seconds)
        self._monotonic = monotonic
        self._sleep = sleep

    def _retry_after(self, response: Any) -> float:
        raw = response.headers.get("Retry-After")
        if raw is None:
            return 0.0
        try:
            value = float(str(raw).strip())
        except ValueError:
            return 0.0
        if value <= 0:
            return 0.0
        return min(value, self.retry_after_max_seconds)

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
        response = None
        for attempt in range(self.max_retries + 1):
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
            if response.status_code not in RETRY_STATUSES:
                return response
            if attempt >= self.max_retries:
                return response
            delay = self._retry_after(response)
            if delay > 0:
                remaining = self.total_timeout_seconds - (self._monotonic() - started)
                if delay >= remaining:
                    raise requests.Timeout("WooCommerce retry exceeds total read deadline")
                self._sleep(delay)
        if response is None:
            raise requests.RequestException("WooCommerce GET produced no response")
        return response
