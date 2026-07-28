from __future__ import annotations

import asyncio
from typing import Any, Mapping

import requests

from core.cms.adapters.wordpress_normalization import WordPressCanonicalNormalizer
from core.cms.models import ContentSnapshot, ContentSnapshotPage, PageRequest, ReadContext


class WordPressCMSReadError(RuntimeError):
    pass


class WordPressRESTAdapter:
    def __init__(
        self,
        base_url: str,
        *,
        session: Any | None = None,
        normalizer: WordPressCanonicalNormalizer | None = None,
        connect_timeout_seconds: float = 5.0,
        read_timeout_seconds: float = 15.0,
    ) -> None:
        normalized = base_url.rstrip("/")
        if not normalized.startswith("https://"):
            raise ValueError("WordPress CMS base_url must use HTTPS")
        if connect_timeout_seconds <= 0 or read_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")

        self._base_url = normalized
        self._session = session if session is not None else requests.Session()
        self._normalizer = normalizer if normalizer is not None else WordPressCanonicalNormalizer()
        self._timeout = (connect_timeout_seconds, read_timeout_seconds)

    @staticmethod
    def _resource(content_type: str) -> str:
        if content_type == "post":
            return "posts"
        if content_type == "page":
            return "pages"
        raise WordPressCMSReadError("unsupported CMS content type")

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        response = self._session.get(
            self._base_url + path,
            params=params,
            headers={"Accept": "application/json"},
            timeout=self._timeout,
            allow_redirects=False,
        )

        return response

    async def get_content(
        self,
        *,
        context: ReadContext,
        content_id: str,
    ) -> ContentSnapshot | None:
        if not content_id or not content_id.isdigit():
            raise ValueError("content_id must be a positive numeric identifier")
        if int(content_id) < 1:
            raise ValueError("content_id must be positive")

        resource = self._resource(context.content_type)

        response = await asyncio.to_thread(
            self._get,
            "/wp-json/wp/v2/" + resource + "/" + content_id,
            params={"context": "view"},
        )

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise WordPressCMSReadError(
                "WordPress CMS detail GET failed status=" + str(response.status_code)
            )

        payload = response.json()
        if not isinstance(payload, Mapping):
            raise WordPressCMSReadError("WordPress CMS detail response must be an object")

        return self._normalizer.normalize_content(
            payload,
            expected_type=context.content_type,
        )

    async def list_content(
        self,
        *,
        context: ReadContext,
        page: PageRequest,
    ) -> ContentSnapshotPage:
        resource = self._resource(context.content_type)

        response = await asyncio.to_thread(
            self._get,
            "/wp-json/wp/v2/" + resource,
            params={
                "context": "view",
                "status": "publish",
                "page": page.page,
                "per_page": page.page_size,
            },
        )

        if response.status_code != 200:
            raise WordPressCMSReadError(
                "WordPress CMS collection GET failed status=" + str(response.status_code)
            )

        payload = response.json()
        if not isinstance(payload, list):
            raise WordPressCMSReadError("WordPress CMS collection response must be a list")

        try:
            total = int(response.headers.get("X-WP-Total", len(payload)))
            total_pages = int(response.headers.get("X-WP-TotalPages", 1 if payload else 0))
        except Exception as error:
            raise WordPressCMSReadError("WordPress CMS pagination headers invalid") from error

        return self._normalizer.normalize_page(
            payload,
            expected_type=context.content_type,
            total=total,
            total_pages=total_pages,
            page_request=page,
        )
