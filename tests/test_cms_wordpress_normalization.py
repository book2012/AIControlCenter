from __future__ import annotations

import pytest

from core.cms.adapters.wordpress_normalization import WordPressCanonicalNormalizer, WordPressNormalizationError
from core.cms.models import PageRequest, ReadContext


def payload(content_type: str = "post", status: str = "publish") -> dict:
    return {
        "id": 42,
        "date": "2026-07-28T10:00:00",
        "date_gmt": "2026-07-28T01:00:00",
        "modified": "2026-07-28T11:00:00",
        "modified_gmt": "2026-07-28T02:00:00",
        "slug": "hello",
        "status": status,
        "type": content_type,
        "link": "https://example.test/hello/",
        "title": {"rendered": "Hello"},
        "content": {"rendered": "<p>Body</p>"},
        "excerpt": {"rendered": "<p>Excerpt</p>"},
    }


def test_read_context_allows_only_post_page_and_publish() -> None:
    assert ReadContext(content_type="post").status == "publish"
    assert ReadContext(content_type="page").content_type == "page"
    with pytest.raises(ValueError):
        ReadContext(content_type="product")
    with pytest.raises(ValueError):
        ReadContext(status="draft")


def test_page_request_enforces_wordpress_pagination_bounds() -> None:
    assert PageRequest(page=1, page_size=100).page_size == 100
    with pytest.raises(ValueError):
        PageRequest(page=0)
    with pytest.raises(ValueError):
        PageRequest(page_size=101)


def test_normalizer_maps_public_post_to_canonical_snapshot() -> None:
    item = WordPressCanonicalNormalizer().normalize_content(
        payload(),
        expected_type="post",
    )
    assert item.content_id == "42"
    assert item.content_type == "post"
    assert item.title == "Hello"
    assert item.content_html == "<p>Body</p>"
    assert item.status == "publish"


def test_normalizer_rejects_private_or_wrong_type_content() -> None:
    normalizer = WordPressCanonicalNormalizer()
    with pytest.raises(WordPressNormalizationError):
        normalizer.normalize_content(payload(status="draft"), expected_type="post")
    with pytest.raises(WordPressNormalizationError):
        normalizer.normalize_content(payload(content_type="page"), expected_type="post")


def test_normalizer_builds_page_with_server_totals() -> None:
    page = WordPressCanonicalNormalizer().normalize_page(
        [payload()],
        expected_type="post",
        total=7,
        total_pages=7,
        page_request=PageRequest(page=1, page_size=1),
    )
    assert len(page.items) == 1
    assert page.total == 7
    assert page.total_pages == 7
