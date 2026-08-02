"""Replaceable, side-effect-free ProductDraft revision read sources."""
from __future__ import annotations

from typing import Protocol

from ..models import ProductDraftRevision


class ProductDraftReadSource(Protocol):
    def is_available(self) -> bool: ...
    def list_revisions(self) -> tuple[ProductDraftRevision, ...]: ...
    def fetch_current(self, draft_id: str) -> ProductDraftRevision | None: ...
    def fetch_revision(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None: ...


class UnavailableProductDraftReadSource:
    def is_available(self) -> bool:
        return False

    def list_revisions(self) -> tuple[ProductDraftRevision, ...]:
        return ()

    def fetch_current(self, draft_id: str) -> ProductDraftRevision | None:
        return None

    def fetch_revision(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None:
        return None


class InMemoryProductDraftSnapshotSource:
    """Isolated non-persistent snapshot adapter for tests/development."""

    def __init__(self, revisions: tuple[ProductDraftRevision, ...] | list[ProductDraftRevision] = ()):
        copied = tuple(revisions)
        if any(not isinstance(item, ProductDraftRevision) for item in copied):
            raise TypeError("revisions must contain ProductDraftRevision values")
        self._revisions = tuple(sorted(copied, key=lambda item: (item.draft_id, item.revision_number, item.revision_id)))
        self._exact = {(item.draft_id, item.revision_id): item for item in self._revisions}
        self._current: dict[str, ProductDraftRevision] = {}
        for item in self._revisions:
            current = self._current.get(item.draft_id)
            if current is None or (item.revision_number, item.revision_id) > (current.revision_number, current.revision_id):
                self._current[item.draft_id] = item

    def is_available(self) -> bool:
        return True

    def list_revisions(self) -> tuple[ProductDraftRevision, ...]:
        return tuple(self._revisions)

    def fetch_current(self, draft_id: str) -> ProductDraftRevision | None:
        return self._current.get(draft_id)

    def fetch_revision(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None:
        return self._exact.get((draft_id, revision_id))


__all__ = ("InMemoryProductDraftSnapshotSource", "ProductDraftReadSource", "UnavailableProductDraftReadSource")
