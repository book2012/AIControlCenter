from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

import pytest

from core.cms.adapters.wordpress_rest import WordPressRESTAdapter
from core.cms.models import PageRequest, ReadContext
from core.cms.ports import CmsReadPort
from core.shopping.ports.cms import CmsReadPort as LegacyCmsReadPort


class FakeResponse:
    def __init__(self, status_code: int, payload, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls = []

    def get(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def item(content_type: str = "post") -> dict:
    return {
        "id": 7,
        "date": "2026-07-28T10:00:00",
        "date_gmt": "2026-07-28T01:00:00",
        "modified": "2026-07-28T11:00:00",
        "modified_gmt": "2026-07-28T02:00:00",
        "slug": "cms-item",
        "status": "publish",
        "type": content_type,
        "link": "https://example.test/cms-item/",
        "title": {"rendered": "CMS Item"},
        "content": {"rendered": "<p>CMS</p>"},
        "excerpt": {"rendered": "<p>CMS excerpt</p>"},
    }


def test_generic_port_preserves_legacy_async_method_surface() -> None:
    generic_methods = {
        name
        for name, value in inspect.getmembers(CmsReadPort)
        if not name.startswith("_") and inspect.isfunction(value)
    }
    legacy_methods = {
        name
        for name, value in inspect.getmembers(LegacyCmsReadPort)
        if not name.startswith("_") and inspect.isfunction(value)
    }
    assert generic_methods == {"get_content", "list_content"}
    assert generic_methods == legacy_methods
    assert inspect.iscoroutinefunction(CmsReadPort.get_content)
    assert inspect.iscoroutinefunction(CmsReadPort.list_content)


def test_core_cms_has_no_core_shopping_dependency() -> None:
    root = Path("core/cms")
    for path in root.rglob("*.py"):
        assert "core.shopping" not in path.read_text(encoding="utf-8")


def test_wordpress_adapter_requires_https() -> None:
    with pytest.raises(ValueError):
        WordPressRESTAdapter("http://example.test")


def test_list_posts_is_get_only_and_normalized() -> None:
    session = FakeSession([
        FakeResponse(
            200,
            [item("post")],
            {"X-WP-Total": "1", "X-WP-TotalPages": "1"},
        )
    ])
    adapter = WordPressRESTAdapter("https://example.test", session=session)
    result = asyncio.run(
        adapter.list_content(
            context=ReadContext(content_type="post"),
            page=PageRequest(page=1, page_size=20),
        )
    )
    assert result.total == 1
    assert result.items[0].content_type == "post"
    assert session.calls[0][0] == "https://example.test/wp-json/wp/v2/posts"
    assert session.calls[0][1]["params"]["status"] == "publish"
    assert session.calls[0][1]["allow_redirects"] is False


def test_list_pages_uses_page_route() -> None:
    session = FakeSession([
        FakeResponse(
            200,
            [item("page")],
            {"X-WP-Total": "1", "X-WP-TotalPages": "1"},
        )
    ])
    adapter = WordPressRESTAdapter("https://example.test", session=session)
    result = asyncio.run(
        adapter.list_content(
            context=ReadContext(content_type="page"),
            page=PageRequest(page=1, page_size=1),
        )
    )
    assert result.items[0].content_type == "page"
    assert session.calls[0][0].endswith("/wp-json/wp/v2/pages")


def test_missing_detail_maps_404_to_none() -> None:
    session = FakeSession([FakeResponse(404, {"code": "rest_post_invalid_id"})])
    adapter = WordPressRESTAdapter("https://example.test", session=session)
    result = asyncio.run(
        adapter.get_content(
            context=ReadContext(content_type="post"),
            content_id="999999",
        )
    )
    assert result is None


def test_adapter_exposes_no_http_write_like_public_methods() -> None:
    public = {
        name.lower()
        for name, value in inspect.getmembers(WordPressRESTAdapter)
        if not name.startswith("_") and callable(value)
    }
    assert not ({"post", "put", "patch", "delete"} & public)
