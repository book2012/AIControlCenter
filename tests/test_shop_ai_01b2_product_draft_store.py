from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.shopping.product_drafts import (
    ActorReference, ActorType, DuplicateRevisionError, LifecycleState, ProductDraftRevision,
    ProposedFields, RevisionChainError, RevisionIdentity, SourceSnapshotReference,
    PERMITTED_TRANSITIONS, TransitionCommand,
)
from core.shopping.product_drafts.persistence import (IsolatedTestDatabasePathPolicy,
    SQLiteProductDraftStore, connect_database, initialize_database)
from core.shopping.product_drafts.serialization import sha256_digest

NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)
ACTOR = ActorReference("service", ActorType.SERVICE)
SOURCE = SourceSnapshotReference("product", NOW, snapshot_digest="sha256:" + "a" * 64)


def revision(number: int, previous: str | None = None) -> ProductDraftRevision:
    identity = RevisionIdentity("draft", f"r{number}", number, previous, NOW, ACTOR, "corr", "audit")
    return ProductDraftRevision(identity, SOURCE, LifecycleState.DRAFT,
                                ProposedFields(name=f"Name {number}", regular_price=Decimal("1.20")))


def test_store_exact_current_list_chain_and_duplicate_contract(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    store = SQLiteProductDraftStore(path, path_policy=policy)
    first, second = revision(1), revision(2, "r1")
    store.store(first); store.store(second)
    assert store.fetch("draft", "r1") == first
    assert store.fetch_revision("draft", "r2") == second
    assert store.fetch_current("draft") == second
    assert store.list_revisions() == (first, second)
    with pytest.raises(DuplicateRevisionError): store.store(second)


def test_store_rejects_non_current_predecessor(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    store = SQLiteProductDraftStore(path, path_policy=policy); store.store(revision(1)); store.store(revision(2, "r1"))
    with pytest.raises(RevisionChainError): store.store(revision(3, "r1"))


def test_all_domain_lifecycle_transitions_work_and_identity_stays_immutable(tmp_path: Path):
    for index, (before, after) in enumerate(sorted(PERMITTED_TRANSITIONS,
                                                   key=lambda pair: (pair[0].value, pair[1].value))):
        root = tmp_path / str(index); root.mkdir(); policy = IsolatedTestDatabasePathPolicy(root)
        path = root / "drafts.sqlite3"; initialize_database(path, path_policy=policy)
        store = SQLiteProductDraftStore(path, path_policy=policy)
        item = revision(1).with_state(before); store.store(item)
        command = TransitionCommand("draft", "r1", "r1", 1, before, after, ACTOR,
            "corr", "audit", f"key-{index}", sha256_digest({"case": index}), NOW)
        result = store.transition(command, NOW)
        assert result.state is after and store.fetch_current("draft").state is after
        connection = connect_database(path, path_policy=policy)
        try:
            with pytest.raises(Exception, match="identity and chain"):
                connection.execute("UPDATE product_draft_revisions SET revision_id='changed' WHERE draft_id='draft'")
        finally: connection.close()
