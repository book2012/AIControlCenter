from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3

import pytest

from core.shopping.product_drafts import (
    ActorReference, ActorType, LifecycleState, ProductDraftRevision, ProposedFields,
    RevisionIdentity, SourceSnapshotReference,
)
from core.shopping.product_drafts.persistence import (
    IsolatedTestDatabasePathPolicy, SQLiteProductDraftStore, connect_database, initialize_database,
)
from core.shopping.product_drafts.read import ProductDraftReadUnavailable
from core.shopping.product_drafts.runtime import (
    FailClosedProductDraftReadSource, build_product_draft_read_runtime,
)


def _runtime(path: Path, policy: IsolatedTestDatabasePathPolicy):
    return build_product_draft_read_runtime(path_resolver=lambda: path, path_policy=policy)


def _revision() -> ProductDraftRevision:
    now = datetime(2026, 8, 11, tzinfo=timezone.utc)
    actor = ActorReference("service", ActorType.SERVICE)
    source = SourceSnapshotReference("product", now, snapshot_digest="sha256:" + "a" * 64)
    identity = RevisionIdentity("draft", "r1", 1, None, now, actor, "corr", "audit")
    return ProductDraftRevision(
        identity, source, LifecycleState.DRAFT,
        ProposedFields(name="Durable draft", regular_price=Decimal("1.20")),
    )


def test_unconfigured_and_missing_database_are_unavailable_without_creation(tmp_path, monkeypatch):
    monkeypatch.delenv("AICONTROLCENTER_DATA_ROOT", raising=False)
    unconfigured = build_product_draft_read_runtime()
    assert unconfigured.capability.reason_code == "DATA_ROOT_UNCONFIGURED"

    path = tmp_path / "missing.sqlite3"
    policy = IsolatedTestDatabasePathPolicy(tmp_path)
    missing = _runtime(path, policy)
    assert missing.capability.reason_code == "DATABASE_MISSING"
    assert not path.exists()


def test_valid_empty_and_populated_database_activate_durable_reads(tmp_path):
    path = tmp_path / "drafts.sqlite3"
    policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    empty = _runtime(path, policy)
    assert empty.capability.reason_code == "AVAILABLE"
    assert empty.query_service.list_revisions()["items"] == []

    SQLiteProductDraftStore(path, path_policy=policy).store(_revision())
    populated = _runtime(path, policy)
    assert populated.query_service.current_revision("draft")["revision_id"] == "r1"


@pytest.mark.parametrize("tamper", ["application_id", "schema", "journal_mode"])
def test_invalid_database_validation_fails_closed(tmp_path, tamper):
    path = tmp_path / "drafts.sqlite3"
    policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    connection = sqlite3.connect(path)
    try:
        if tamper == "application_id":
            connection.execute("PRAGMA application_id = 1")
        elif tamper == "schema":
            connection.execute("CREATE TABLE unexpected(value TEXT)")
        else:
            connection.execute("PRAGMA journal_mode = DELETE")
        connection.commit()
    finally:
        connection.close()
    runtime = _runtime(path, policy)
    assert runtime.capability.reason_code == "DATABASE_INVALID"
    with pytest.raises(ProductDraftReadUnavailable):
        runtime.query_service.list_revisions()


def test_read_time_database_failure_uses_unavailable_semantics():
    class VanishingSource:
        def is_available(self): return True
        def list_revisions(self): raise sqlite3.OperationalError("private path")
        def fetch_current(self, draft_id): raise sqlite3.OperationalError("private path")
        def fetch_revision(self, draft_id, revision_id): raise sqlite3.OperationalError("private path")

    source = FailClosedProductDraftReadSource(VanishingSource())
    with pytest.raises(ProductDraftReadUnavailable, match="read source unavailable") as raised:
        source.list_revisions()
    assert "private path" not in str(raised.value)


def test_post_startup_semantic_row_corruption_fails_closed(tmp_path):
    path = tmp_path / "drafts.sqlite3"
    policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    SQLiteProductDraftStore(path, path_policy=policy).store(_revision())
    runtime = _runtime(path, policy)
    assert runtime.capability.reason_code == "AVAILABLE"

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE product_draft_revisions SET revision_json = ?",
            ("{}",),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(ProductDraftReadUnavailable) as raised:
        runtime.query_service.current_revision("draft")

    assert "draft_id" not in str(raised.value)
