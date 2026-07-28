from __future__ import annotations

from typing import Any, Mapping, Sequence

from core.cms.models import ContentSnapshot, ContentSnapshotPage, PageRequest


class WordPressNormalizationError(ValueError):
    pass


class WordPressCanonicalNormalizer:
    @staticmethod
    def _rendered(payload: Mapping[str, Any], key: str) -> str:
        value = payload.get(key)
        if value is None:
            return ""
        if not isinstance(value, Mapping):
            raise WordPressNormalizationError(key + " must be an object")
        rendered = value.get("rendered", "")
        if not isinstance(rendered, str):
            raise WordPressNormalizationError(key + ".rendered must be a string")
        return rendered

    def normalize_content(
        self,
        payload: Mapping[str, Any],
        *,
        expected_type: str,
    ) -> ContentSnapshot:
        identifier = payload.get("id")
        content_type = payload.get("type")
        status = payload.get("status")
        slug = payload.get("slug")
        url = payload.get("link")

        if not isinstance(identifier, int):
            raise WordPressNormalizationError("id must be an integer")
        if content_type != expected_type:
            raise WordPressNormalizationError("unexpected content type")
        if status != "publish":
            raise WordPressNormalizationError("non-published content is denied")
        if not isinstance(slug, str):
            raise WordPressNormalizationError("slug must be a string")
        if not isinstance(url, str) or not url:
            raise WordPressNormalizationError("link must be a non-empty string")

        published_at = payload.get("date_gmt") or payload.get("date")
        modified_at = payload.get("modified_gmt") or payload.get("modified")

        if published_at is not None and not isinstance(published_at, str):
            raise WordPressNormalizationError("published timestamp must be a string or null")
        if modified_at is not None and not isinstance(modified_at, str):
            raise WordPressNormalizationError("modified timestamp must be a string or null")

        return ContentSnapshot(
            content_id=str(identifier),
            content_type=content_type,
            slug=slug,
            status=status,
            title=self._rendered(payload, "title"),
            content_html=self._rendered(payload, "content"),
            excerpt_html=self._rendered(payload, "excerpt"),
            url=url,
            published_at=published_at,
            modified_at=modified_at,
        )

    def normalize_page(
        self,
        items: Sequence[Mapping[str, Any]],
        *,
        expected_type: str,
        total: int,
        total_pages: int,
        page_request: PageRequest,
    ) -> ContentSnapshotPage:
        if total < 0 or total_pages < 0:
            raise WordPressNormalizationError("pagination totals must not be negative")

        normalized = tuple(
            self.normalize_content(item, expected_type=expected_type)
            for item in items
        )

        return ContentSnapshotPage(
            items=normalized,
            total=total,
            total_pages=total_pages,
            page=page_request.page,
            page_size=page_request.page_size,
        )
