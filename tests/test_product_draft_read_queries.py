from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from core.shopping.product_drafts import (
    ActorReference, ActorType, LifecycleState, ProductDraftRevision,
    ProposedFields, RevisionIdentity, SourceSnapshotReference,
)
from core.shopping.product_drafts.read import (
    InMemoryProductDraftSnapshotSource, ProductDraftQueryService,
    ProductDraftReadUnavailable, ProductDraftRevisionNotFound,
    UnavailableProductDraftReadSource,
)


NOW = datetime(2026, 8, 3, 1, 0, tzinfo=timezone.utc)
DIGEST = "sha256:" + "a" * 64
ACTOR = ActorReference("service", ActorType.SERVICE)


def revision(draft_id: str, number: int, state: LifecycleState, *, created_offset: int = 0) -> ProductDraftRevision:
    revision_id = f"{draft_id}-r{number}"
    identity = RevisionIdentity(draft_id, revision_id, number,
                                None if number == 1 else f"{draft_id}-r{number - 1}",
                                NOW + timedelta(minutes=created_offset), ACTOR, "corr", "audit")
    source = SourceSnapshotReference(f"product-{draft_id}", NOW, snapshot_digest=DIGEST)
    return ProductDraftRevision(identity, source, state,
                                ProposedFields(name=f"Name {draft_id}", sku=f"SKU-{draft_id}", regular_price=Decimal("1.20")))


def test_empty_available_source_is_distinct_from_unavailable_source():
    assert ProductDraftQueryService(InMemoryProductDraftSnapshotSource()).list_revisions()["status"] == "AVAILABLE"
    with pytest.raises(ProductDraftReadUnavailable):
        ProductDraftQueryService(UnavailableProductDraftReadSource()).list_revisions()


def test_collection_order_filter_and_bounded_pagination_are_deterministic():
    items = [revision("b", 1, LifecycleState.DRAFT), revision("a", 1, LifecycleState.REVIEW_REQUIRED),
             revision("a", 2, LifecycleState.APPROVED)]
    service = ProductDraftQueryService(InMemoryProductDraftSnapshotSource(items))
    result = service.list_revisions(page=1, page_size=2)
    assert [(item["draft_id"], item["revision_number"]) for item in result["items"]] == [("a", 1), ("a", 2)]
    assert result["pagination"] == {"page": 1, "page_size": 2, "total_items": 3, "total_pages": 2, "has_next": True}
    assert service.list_revisions(lifecycle_state="REVIEW_REQUIRED")["pagination"]["total_items"] == 1
    with pytest.raises(ValueError):
        service.list_revisions(page_size=101)


def test_current_exact_missing_and_detached_json_safe_projection():
    first = revision("a", 1, LifecycleState.DRAFT)
    second = revision("a", 2, LifecycleState.REVIEW_REQUIRED)
    service = ProductDraftQueryService(InMemoryProductDraftSnapshotSource([second, first]))
    current = service.current_revision("a")
    assert current["revision_id"] == "a-r2"
    assert service.exact_revision("a", "a-r1")["revision_number"] == 1
    assert current["proposed_fields"]["regular_price"] == "1.20"
    current["proposed_fields"]["name"] = "mutated"
    assert service.current_revision("a")["proposed_fields"]["name"] == "Name a"
    with pytest.raises(ProductDraftRevisionNotFound):
        service.current_revision("missing")
    with pytest.raises(ProductDraftRevisionNotFound):
        service.exact_revision("a", "missing")


def test_input_collection_mutation_does_not_change_snapshot():
    supplied = [revision("a", 1, LifecycleState.DRAFT)]
    source = InMemoryProductDraftSnapshotSource(supplied)
    supplied.clear()
    assert len(source.list_revisions()) == 1


def test_review_queue_only_contains_exact_pending_revisions_in_stable_order():
    items = [revision("z", 1, LifecycleState.APPROVED), revision("b", 1, LifecycleState.REVIEW_REQUIRED, created_offset=2),
             revision("a", 1, LifecycleState.REVIEW_REQUIRED, created_offset=1), revision("x", 1, LifecycleState.REJECTED),
             revision("y", 1, LifecycleState.REVOKED), revision("s", 1, LifecycleState.SUPERSEDED)]
    queue = ProductDraftQueryService(InMemoryProductDraftSnapshotSource(items)).review_queue()
    assert [(item["draft_id"], item["revision_id"]) for item in queue["items"]] == [("a", "a-r1"), ("b", "b-r1")]
    assert queue["pending_review_count"] == 2
    forbidden = {"consumer_key", "consumer_secret", "authorization_policy", "credentials"}
    assert forbidden.isdisjoint(str(queue).lower())


def test_superseded_older_review_revision_is_not_pending():
    items = [revision("a", 1, LifecycleState.REVIEW_REQUIRED),
             revision("a", 2, LifecycleState.APPROVED)]
    queue = ProductDraftQueryService(InMemoryProductDraftSnapshotSource(items)).review_queue()
    assert queue["items"] == []


def test_dashboard_summary_is_deterministic_and_read_only():
    items = [revision("a", 1, LifecycleState.DRAFT), revision("a", 2, LifecycleState.REVIEW_REQUIRED),
             revision("b", 1, LifecycleState.APPROVED)]
    payload = ProductDraftQueryService(InMemoryProductDraftSnapshotSource(items)).dashboard_projection()
    assert payload["summary"]["draft_count"] == 2
    assert payload["summary"]["revision_count"] == 3
    assert payload["summary"]["lifecycle_counts"]["REVIEW_REQUIRED"] == 1
    assert payload["pending_review_count"] == 1
    assert payload["read_only"] is True and payload["mutation_capabilities"] is False
