from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import multiprocessing
import sqlite3

import pytest

from core.shopping.product_drafts import (ActorReference, ActorType, LifecycleState,
    ProductDraftRevision, ProposedFields, RevisionIdentity, SourceSnapshotReference)
from core.shopping.product_drafts.application import GenerationOperationInFlight
from core.shopping.product_drafts.persistence import (SQLiteProductDraftGenerationTransactions,
    IsolatedTestDatabasePathPolicy, SQLiteProductDraftStore, connect_database, initialize_database)

DIGEST = "sha256:" + "b" * 64
NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)


def revision(revision_id: str, number: int, previous: str | None) -> ProductDraftRevision:
    identity = RevisionIdentity("draft", revision_id, number, previous, NOW,
        ActorReference("service", ActorType.SERVICE), "corr", "audit")
    source = SourceSnapshotReference("product", NOW, snapshot_digest="sha256:" + "a" * 64)
    return ProductDraftRevision(identity, source, LifecycleState.DRAFT,
                                ProposedFields(name=revision_id, regular_price=Decimal("1")))


def _process_claim(path_string: str, barrier, output) -> None:
    path = Path(path_string); policy = IsolatedTestDatabasePathPolicy(path.parent)
    barrier.wait()
    try:
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim(
            "key", DIGEST, "draft", "r1")
        output.put("CLAIMED")
    except GenerationOperationInFlight:
        output.put("DENIED")


def test_competing_same_key_claim_has_exactly_one_winner(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    def claim():
        try:
            SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim("key", DIGEST, "draft", "r1")
            return "CLAIMED"
        except GenerationOperationInFlight:
            return "DENIED"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(lambda _: claim(), range(2)))
    assert sorted(outcomes) == ["CLAIMED", "DENIED"]


def test_sqlite_busy_is_exposed_and_never_reclassified_as_retry(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    lock = connect_database(path, path_policy=policy); lock.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            SQLiteProductDraftGenerationTransactions(path, path_policy=policy, busy_timeout_ms=1).claim("key", DIGEST, "draft", "r1")
    finally:
        lock.rollback(); lock.close()


def test_competing_next_revisions_validate_current_under_writer_lock(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    SQLiteProductDraftStore(path, path_policy=policy).store(revision("r1", 1, None))
    def store(candidate):
        try:
            SQLiteProductDraftStore(path, path_policy=policy).store(candidate)
            return "STORED"
        except Exception:
            return "CONFLICT"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(store, (revision("r2-a", 2, "r1"), revision("r2-b", 2, "r1"))))
    assert sorted(outcomes) == ["CONFLICT", "STORED"]
    assert SQLiteProductDraftStore(path, path_policy=policy).fetch_current("draft").revision_number == 2


def test_two_processes_receive_exactly_one_claim_authority(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2); output = context.Queue()
    processes = [context.Process(target=_process_claim, args=(str(path), barrier, output)) for _ in range(2)]
    for process in processes: process.start()
    for process in processes: process.join(15)
    assert all(process.exitcode == 0 for process in processes)
    assert sorted((output.get(timeout=2), output.get(timeout=2))) == ["CLAIMED", "DENIED"]
