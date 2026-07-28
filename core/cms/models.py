from __future__ import annotations

from dataclasses import dataclass


_CONTENT_TYPES = frozenset({"post", "page"})


@dataclass(frozen=True, slots=True)
class ReadContext:
    content_type: str = "post"
    status: str = "publish"

    def __post_init__(self) -> None:
        if self.content_type not in _CONTENT_TYPES:
            raise ValueError("unsupported CMS content type")
        if self.status != "publish":
            raise ValueError("only published CMS content is permitted")


@dataclass(frozen=True, slots=True)
class PageRequest:
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be at least 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("page_size must be between 1 and 100")


@dataclass(frozen=True, slots=True)
class ContentSnapshot:
    content_id: str
    content_type: str
    slug: str
    status: str
    title: str
    content_html: str
    excerpt_html: str
    url: str
    published_at: str | None
    modified_at: str | None

    def __post_init__(self) -> None:
        if not self.content_id:
            raise ValueError("content_id is required")
        if self.content_type not in _CONTENT_TYPES:
            raise ValueError("unsupported CMS content type")
        if self.status != "publish":
            raise ValueError("only published CMS snapshots are permitted")
        if not self.url:
            raise ValueError("content URL is required")


@dataclass(frozen=True, slots=True)
class ContentSnapshotPage:
    items: tuple[ContentSnapshot, ...]
    total: int
    total_pages: int
    page: int
    page_size: int

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("total must not be negative")
        if self.total_pages < 0:
            raise ValueError("total_pages must not be negative")
        if self.page < 1:
            raise ValueError("page must be at least 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("page_size must be between 1 and 100")
