from datetime import datetime, timezone
from pathlib import Path
import multiprocessing
import os

import pytest

from core.shopping.product_drafts import ActorReference, ActorType, ProposedFields, SourceSnapshotReference
from core.shopping.product_drafts.application import (
    GenerateProductDraftCommand, GenerationOperationInFlight, ProductDraftGenerationService,
    StructuredGenerationResult,
)
from core.shopping.product_drafts.persistence import (
    IsolatedTestDatabasePathPolicy, SQLiteProductDraftGenerationTransactions,
    SQLiteProductDraftStore, connect_database, initialize_database,
)
from core.shopping.product_drafts.serialization import sha256_digest

NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)
SOURCE = SourceSnapshotReference("product", NOW, snapshot_digest="sha256:" + "a" * 64)


class Generation:
    def generate(self, **_):
        return StructuredGenerationResult(ProposedFields(name="Generated"), ("name",), "fake", "model", None, sha256_digest("response"))


def command():
    return GenerateProductDraftCommand("draft", "r1", SOURCE, {"safe": True},
        ActorReference("service", ActorType.SERVICE), NOW, "corr", "audit", "key")


def _crash_complete(path_string: str, result) -> None:
    path = Path(path_string); policy = IsolatedTestDatabasePathPolicy(path.parent)
    def hook(point: str) -> None:
        if point == "completion_after_audit_insert": os._exit(73)
    SQLiteProductDraftGenerationTransactions(path, path_policy=policy,
        failure_hook=hook).complete("key", command().command_digest, result)


@pytest.mark.parametrize("failure_point", [
    "completion_after_revision_insert", "completion_after_audit_insert", "completion_before_commit",
])
def test_completion_interruptions_rollback_revision_audit_and_completion(tmp_path: Path, failure_point: str):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    def hook(point):
        if point == failure_point: raise RuntimeError("injected interruption")
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy, failure_hook=hook)
    with pytest.raises(RuntimeError, match="injected"):
        ProductDraftGenerationService(Generation(), tx).execute(command())
    assert SQLiteProductDraftStore(path, path_policy=policy).fetch_current("draft") is None
    with pytest.raises(GenerationOperationInFlight):
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim("key", command().command_digest, "draft", "r1")


def test_claim_failure_rolls_back_but_committed_claim_survives_reopen(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    def fail_claim(point):
        if point == "claim_before_commit": raise RuntimeError("claim interruption")
    with pytest.raises(RuntimeError):
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy, failure_hook=fail_claim).claim("key", command().command_digest, "draft", "r1")
    SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim("key", command().command_digest, "draft", "r1")
    with pytest.raises(GenerationOperationInFlight):
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim("key", command().command_digest, "draft", "r1")


def test_abrupt_process_exit_rolls_back_completion_and_preserves_claim(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    # Claim is committed in the parent, proving it also survives the child reopen.
    SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim(
        "key", command().command_digest, "draft", "r1")
    # Child completes an already-claimed operation directly with a result obtained locally.
    generated = ProductDraftGenerationService(Generation(), __import__(
        "core.shopping.product_drafts.application", fromlist=["InMemoryProductDraftGenerationOperationCoordinator"]
    ).InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    process = multiprocessing.get_context("spawn").Process(target=_crash_complete, args=(str(path), generated))
    process.start(); process.join(15)
    assert process.exitcode == 73
    assert SQLiteProductDraftStore(path, path_policy=policy).fetch_current("draft") is None
    connection = connect_database(path, read_only=True)
    try:
        assert connection.execute("SELECT state FROM product_draft_generation_operations").fetchone()[0] == "CLAIMED"
        assert connection.execute("SELECT count(*) FROM product_draft_generation_audit_events").fetchone()[0] == 0
    finally: connection.close()
    with pytest.raises(GenerationOperationInFlight):
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy).claim(
            "key", command().command_digest, "draft", "r1")
