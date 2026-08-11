from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path

import pytest

from core.shopping.product_drafts import ActorReference, ActorType, ProposedFields, SourceSnapshotReference
from core.shopping.product_drafts.application import (
    GenerateProductDraftCommand, GenerationOperationConflict, GenerationOperationInFlight,
    GenerationOperationTerminalFailure, ProductDraftGenerationService, StructuredGenerationResult,
    InMemoryProductDraftGenerationOperationCoordinator,
)
from core.shopping.product_drafts.persistence import (IsolatedTestDatabasePathPolicy,
    SQLiteProductDraftGenerationTransactions, connect_database, initialize_database)
from core.shopping.product_drafts.serialization import sha256_digest

NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)
SOURCE = SourceSnapshotReference("product", NOW, snapshot_digest="sha256:" + "a" * 64)


class Generation:
    def generate(self, **_):
        return StructuredGenerationResult(ProposedFields(name="Generated"), ("name",), "fake", "model", "safe-id", sha256_digest({"safe": True}))


def command(key="key", revision_id="r1"):
    return GenerateProductDraftCommand("draft", revision_id, SOURCE, {"safe": True},
        ActorReference("service", ActorType.SERVICE), NOW, "corr", "audit", key)


def test_claim_complete_and_durable_replay(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    coordinator = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    service = ProductDraftGenerationService(Generation(), coordinator)
    first = service.execute(command())
    replay = SQLiteProductDraftGenerationTransactions(path, path_policy=policy).replay_generation("key", command().command_digest)
    assert replay is not None and replay.idempotent_replay and replay.revision == first.revision
    with pytest.raises(GenerationOperationConflict):
        coordinator.claim("key", command(revision_id="other").command_digest, "draft", "other")


def test_claimed_and_terminal_failed_never_restore_invocation_authority(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path); initialize_database(path, path_policy=policy)
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy); digest = command().command_digest
    tx.claim("key", digest, "draft", "r1")
    with pytest.raises(GenerationOperationInFlight): tx.claim("key", digest, "draft", "r1")
    tx.fail("key", digest)
    with pytest.raises(GenerationOperationTerminalFailure): tx.claim("key", digest, "draft", "r1")


def test_service_provider_callback_observes_committed_claim(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    class ObservingGeneration(Generation):
        def generate(self, **kwargs):
            connection = connect_database(path, read_only=True)
            try:
                row = connection.execute("SELECT state,draft_id,revision_id FROM product_draft_generation_operations WHERE operation_key='key'").fetchone()
                assert tuple(row) == ("CLAIMED", "draft", "r1")
            finally: connection.close()
            return super().generate(**kwargs)
    ProductDraftGenerationService(ObservingGeneration(),
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy)).execute(command())


UNSAFE_EVIDENCE_IDENTIFIERS = [
    '{"error":"provider response"}', '{"id":"resp_123"}', '["provider","response"]',
    "Authorization:Bearer", "Authorization=Bearer", "Authorization: Bearer",
    "password:exposed", "password=exposed", "token:exposed", "token=exposed",
    "access_token:exposed", "access_token=exposed", "client_secret:exposed",
    "client_secret=exposed", "api_key:exposed", "api_key=exposed",
    "x-api-key:exposed", "x-api-key=exposed", "error:provider-response", "status:500",
    "?token=exposed", "?access_token=exposed", "-----BEGIN PRIVATE KEY-----",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJl",
]


def test_completion_rejects_cross_binding(tmp_path: Path):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(Generation(),
        InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    tx.claim("key", command().command_digest, "draft", "r1")
    with pytest.raises(RuntimeError, match="claimed resource"):
        tx.complete("key", command().command_digest, replace(result, revision_id="other"))


@pytest.mark.parametrize("field", [
    "actor_reference", "correlation_id", "audit_reference", "provider", "model",
    "provider_request_id",
])
@pytest.mark.parametrize("unsafe", UNSAFE_EVIDENCE_IDENTIFIERS)
def test_each_persisted_evidence_identifier_rejects_payloads(
        tmp_path: Path, field: str, unsafe: str):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(Generation(),
        InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    audit = replace(result.audit_projection, **{field: unsafe})
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    tx.claim("key", command().command_digest, "draft", "r1")
    with pytest.raises(ValueError, match="syntax|credential-shaped"):
        tx.complete("key", command().command_digest, replace(result, audit_projection=audit))


@pytest.mark.parametrize("provider,model,request_id", [
    ("fake", "model", "resp_123"),
    ("openai", "gpt-test", "safe-request-reference"),
    ("provider.v2", "org/model:v1+preview", None),
])
def test_completion_accepts_normal_generation_evidence_identifiers(
        tmp_path: Path, provider: str, model: str, request_id: str | None):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(Generation(),
        InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    audit = replace(result.audit_projection, provider=provider, model=model,
                    provider_request_id=request_id)
    result = replace(result, provider=provider, model=model, provider_request_id=request_id,
                     audit_projection=audit)
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    tx.claim("key", command().command_digest, "draft", "r1")
    tx.complete("key", command().command_digest, result)


def test_business_content_is_not_filtered_as_evidence(tmp_path: Path):
    class BusinessDataGeneration(Generation):
        def generate(self, **_):
            fields = ProposedFields(
                name='token password: ordinary product',
                description='Spaces and punctuation: {"token":"business data"}',
            )
            return StructuredGenerationResult(fields, ("name", "description"), "fake", "model",
                "safe-id", sha256_digest({"safe": True}))

    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(BusinessDataGeneration(),
        SQLiteProductDraftGenerationTransactions(path, path_policy=policy)).execute(command())
    assert result.revision.proposed_fields.description == \
        'Spaces and punctuation: {"token":"business data"}'


@pytest.mark.parametrize("field", [
    "actor_reference", "correlation_id", "audit_reference", "provider", "model",
    "provider_request_id",
])
def test_each_generation_evidence_field_enforces_its_positive_syntax(
        tmp_path: Path, field: str):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(Generation(),
        InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    audit = replace(result.audit_projection, **{field: '{"raw":"payload"}'})
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    tx.claim("key", command().command_digest, "draft", "r1")
    with pytest.raises(ValueError, match="syntax"):
        tx.complete("key", command().command_digest, replace(result, audit_projection=audit))


@pytest.mark.parametrize("field,value,expected", [
    ("event_type", "GENERATION_RESPONSE_STORED", "PRODUCT_DRAFT_GENERATED"),
    ("outcome", "COMPLETED", "PREPARED"),
])
def test_generation_event_type_and_outcome_are_closed(
        tmp_path: Path, field: str, value: str, expected: str):
    path = tmp_path / "drafts.sqlite3"; policy = IsolatedTestDatabasePathPolicy(tmp_path)
    initialize_database(path, path_policy=policy)
    result = ProductDraftGenerationService(Generation(),
        InMemoryProductDraftGenerationOperationCoordinator()).execute(command())
    audit = replace(result.audit_projection, **{field: value})
    tx = SQLiteProductDraftGenerationTransactions(path, path_policy=policy)
    tx.claim("key", command().command_digest, "draft", "r1")
    with pytest.raises(ValueError, match=expected):
        tx.complete("key", command().command_digest, replace(result, audit_projection=audit))
