"""Deterministic ProductDraft queries and detached JSON projections."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..models import LifecycleState, ProductDraftRevision
from ..serialization import to_json_compatible
from .source import ProductDraftReadSource


class ProductDraftReadUnavailable(RuntimeError):
    pass


class ProductDraftRevisionNotFound(LookupError):
    pass


def unavailable_dashboard_projection() -> dict[str, Any]:
    return {
        "schema_version": "1.0", "status": "UNAVAILABLE", "source": "PRODUCT_DRAFT_READ_SOURCE",
        "mode": "READ_ONLY", "summary": {"draft_count": 0, "revision_count": 0, "lifecycle_counts": {}},
        "pending_review_count": 0, "pending_review_items": [], "read_only": True,
        "mutation_capabilities": False,
        "error": {"code": "PRODUCT_DRAFT_READ_UNAVAILABLE", "retryable": True},
    }


class ProductDraftQueryService:
    MAX_PAGE_SIZE = 100

    def __init__(self, source: ProductDraftReadSource):
        self._source = source

    def _require_available(self) -> None:
        if not self._source.is_available():
            raise ProductDraftReadUnavailable("ProductDraft read source unavailable")

    @staticmethod
    def _project(revision: ProductDraftRevision) -> dict[str, Any]:
        return deepcopy(to_json_compatible(revision))

    def list_revisions(self, *, page: int = 1, page_size: int = 20, lifecycle_state: str | None = None) -> dict[str, Any]:
        self._require_available()
        if page < 1 or page_size < 1 or page_size > self.MAX_PAGE_SIZE:
            raise ValueError("invalid pagination")
        state = LifecycleState(lifecycle_state) if lifecycle_state is not None else None
        revisions = sorted(self._source.list_revisions(), key=lambda item: (item.draft_id, item.revision_number, item.revision_id))
        if state is not None:
            revisions = [item for item in revisions if item.state is state]
        total = len(revisions)
        start = (page - 1) * page_size
        items = [self._project(item) for item in revisions[start:start + page_size]]
        return {"schema_version": "1.0", "status": "AVAILABLE", "source": "PRODUCT_DRAFT_READ_SOURCE", "items": items,
                "pagination": {"page": page, "page_size": page_size, "total_items": total,
                               "total_pages": (total + page_size - 1) // page_size, "has_next": start + page_size < total}}

    def current_revision(self, draft_id: str) -> dict[str, Any]:
        self._require_available()
        revision = self._source.fetch_current(draft_id)
        if revision is None:
            raise ProductDraftRevisionNotFound(draft_id)
        return self._project(revision)

    def exact_revision(self, draft_id: str, revision_id: str) -> dict[str, Any]:
        self._require_available()
        revision = self._source.fetch_revision(draft_id, revision_id)
        if revision is None:
            raise ProductDraftRevisionNotFound(f"{draft_id}/{revision_id}")
        return self._project(revision)

    def review_queue(self, *, limit: int = 25) -> dict[str, Any]:
        self._require_available()
        if limit < 1 or limit > self.MAX_PAGE_SIZE:
            raise ValueError("invalid review queue limit")
        current: dict[str, ProductDraftRevision] = {}
        for item in self._source.list_revisions():
            prior = current.get(item.draft_id)
            if prior is None or (item.revision_number, item.revision_id) > (prior.revision_number, prior.revision_id):
                current[item.draft_id] = item
        pending = sorted((item for item in current.values() if item.state is LifecycleState.REVIEW_REQUIRED),
                         key=lambda item: (item.identity.created_at, item.draft_id, item.revision_number, item.revision_id))
        items = [{"draft_id": item.draft_id, "revision_id": item.revision_id, "revision_number": item.revision_number,
                  "lifecycle_state": item.state.value,
                  "validation_status": item.validation.status.value if item.validation else None,
                  "created_at": to_json_compatible(item.identity.created_at),
                  "name": item.proposed_fields.name, "sku": item.proposed_fields.sku} for item in pending[:limit]]
        return {"schema_version": "1.0", "status": "AVAILABLE", "items": deepcopy(items), "pending_review_count": len(pending)}

    def dashboard_projection(self, *, pending_limit: int = 10) -> dict[str, Any]:
        self._require_available()
        revisions = tuple(self._source.list_revisions())
        current: dict[str, ProductDraftRevision] = {}
        for item in revisions:
            prior = current.get(item.draft_id)
            if prior is None or (item.revision_number, item.revision_id) > (prior.revision_number, prior.revision_id):
                current[item.draft_id] = item
        counts = {state.value: 0 for state in LifecycleState}
        for item in current.values():
            counts[item.state.value] += 1
        queue = self.review_queue(limit=pending_limit)
        return {"schema_version": "1.0", "status": "AVAILABLE", "source": "PRODUCT_DRAFT_READ_SOURCE",
                "mode": "READ_ONLY", "summary": {"draft_count": len(current), "revision_count": len(revisions), "lifecycle_counts": counts},
                "pending_review_count": queue["pending_review_count"], "pending_review_items": queue["items"],
                "read_only": True, "mutation_capabilities": False}


__all__ = ("ProductDraftQueryService", "ProductDraftReadUnavailable", "ProductDraftRevisionNotFound", "unavailable_dashboard_projection")
