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
        self._session.trust_env = False
        if isinstance(self._session, requests.Session):
            self._session.proxies.clear()
            self._session.auth = None
            self._session.cookies.clear()
            self._session.headers.clear()
            self._session.hooks = {"response": []}
            for scheme in ("http://", "https://"):
                self._session.mount(scheme, requests.adapters.HTTPAdapter(max_retries=0))
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
        self._session.trust_env = False
        failure = None
        response = None
        try:
            response = self._session.get(
                url,
                params=params,
                auth=auth,
                headers=headers,
                timeout=(connect_timeout, read_timeout),
                allow_redirects=False,
            )
        except requests.RequestException as error:
            self._scrub(getattr(error, "request", None))
            self._scrub_response(getattr(error, "response", None))
            failure = requests.Timeout if isinstance(error, requests.Timeout) else requests.RequestException
        finally:
            if isinstance(headers, dict):
                headers.pop("Authorization", None)
        # Raise outside the handler so raw exception context is not retained.
        if failure is not None:
            raise failure("WooCommerce read transport failed")
        self._scrub_response(response)
        elapsed = self._monotonic() - started
        if elapsed > self.total_timeout_seconds:
            closer = getattr(response, "close", None)
            if callable(closer):
                closer()
            raise requests.Timeout("WooCommerce total read deadline exceeded")
        return response

    @staticmethod
    def _scrub(request):
        if request is not None:
            request.headers.clear()
            request.body = None

    @classmethod
    def _scrub_response(cls, response):
        if response is not None:
            cls._scrub(getattr(response, "request", None))
            if hasattr(response, "_next"):
                response._next = None
            for previous in getattr(response, "history", ()):
                cls._scrub(getattr(previous, "request", None))
