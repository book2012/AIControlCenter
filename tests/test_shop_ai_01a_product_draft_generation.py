from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from threading import Event, Thread

import pytest

from core.providers.contracts import ProviderResponse
from core.shopping.product_drafts import (
    ActorReference, ActorType, LifecycleState, ProductDraftRevision,
    ProvenanceType, SourceSnapshotReference,
)
from core.shopping.product_drafts.application import (
    CanonicalProviderProductDraftGenerationAdapter, GenerateProductDraftCommand,
    GenerationContractError, GenerationOperationConflict,
    GenerationOperationInFlight, GenerationOperationTerminalFailure,
    InMemoryProductDraftGenerationOperationCoordinator,
    ProductDraftGenerationService, parse_generation_contract,
)

NOW = datetime(2026, 8, 11, 3, 0, tzinfo=timezone.utc)
SOURCE = SourceSnapshotReference("product-42", NOW, snapshot_digest="sha256:" + "a" * 64)
ACTOR = ActorReference("shopping-ai-service", ActorType.SERVICE)
VALID_FIELDS = {
    "name": "Orange Coco", "description": "Source-backed description",
    "regular_price": "12.30", "inventory_quantity": 4,
    "stock_status": "IN_STOCK",
    "categories": [{"id": "fruit", "label": "Fruit"}],
}


def payload(fields=None, version="1.0.0", **extra):
    return json.dumps({"schema_version": version,
                       "proposed_fields": fields or VALID_FIELDS, **extra})


class FakeProvider:
    provider = "fake"

    def __init__(self, content=None, failure=None, entered=None, release=None):
        self.content = content or payload()
        self.failure = failure
        self.requests = []
        self.entered = entered
        self.release = release

    def invoke(self, request):
        self.requests.append(request)
        if self.entered:
            self.entered.set()
        if self.release:
            assert self.release.wait(2)
        if self.failure:
            raise self.failure
        return ProviderResponse("fake", request.model, self.content,
                                provider_request_id="safe-request-reference")


def command(revision_id="revision-ai-1", key="generation-key-1", *,
            context=None, current_revision=None):
    return GenerateProductDraftCommand(
        "draft-1", revision_id, SOURCE,
        context or {"source_name": "Orange", "source_digest": SOURCE.snapshot_digest},
        ACTOR, NOW, "correlation-ai-1", "audit-ai-1", key, current_revision,
    )


def system(provider=None, coordinator=None):
    provider = provider or FakeProvider()
    coordinator = coordinator or InMemoryProductDraftGenerationOperationCoordinator()
    service = ProductDraftGenerationService(
        CanonicalProviderProductDraftGenerationAdapter(provider, model="fake-model"),
        coordinator,
    )
    return service, provider, coordinator


def test_valid_contract_maps_existing_fields_and_creates_ai_draft_candidate():
    service, provider, _ = system()
    result = service.execute(command())
    fields = result.revision.proposed_fields
    assert fields.name == "Orange Coco" and str(fields.regular_price) == "12.30"
    assert fields.inventory_quantity == 4 and fields.categories[0].id == "fruit"
    assert {item.field for item in result.revision.suggestions} == set(VALID_FIELDS)
    assert all(item.provenance is ProvenanceType.AI for item in result.revision.suggestions)
    assert all(item.provider_model_reference == "fake:fake-model"
               for item in result.revision.suggestions)
    assert result.outcome == "PREPARED"
    assert result.revision.state is LifecycleState.DRAFT
    with pytest.raises(FrozenInstanceError):
        result.revision.state = LifecycleState.APPROVED
    assert len(provider.requests) == 1


def test_service_has_only_generation_and_operation_coordinator_collaborators():
    service, _, _ = system()
    assert set(vars(service)) == {"_generation", "_coordinator"}
    assert not any(hasattr(service, name) for name in
                   ("_repository", "_audit", "_idempotency", "_commerce", "_authorization"))


def test_explicit_current_revision_builds_chain_without_hidden_read_or_store():
    service, _, _ = system()
    first = service.execute(command())
    second_service, _, _ = system()
    second = second_service.execute(command("revision-ai-2", "generation-key-2",
                                            current_revision=first.revision))
    assert second.revision.revision_number == 2
    assert second.revision.identity.previous_revision_id == first.revision_id


@pytest.mark.parametrize("content, message", [
    ("not-json", "malformed JSON"),
    (payload(extra="ignored"), "envelope"),
    (payload(version="2.0.0"), "schema_version"),
    (payload({"name": 7}), "name must be a string"),
    (payload({"inventory_quantity": True}), "non-negative integer"),
    (payload({"unsupported": "x"}), "unknown fields"),
    (json.dumps({"proposed_fields": {"name": "x"}}), "envelope"),
    ('{"schema_version":"1.0.0","schema_version":"1.0.0","proposed_fields":{"name":"x"}}', "duplicate"),
    ('{"schema_version":"1.0.0","proposed_fields":{"regular_price":NaN}}', "non-finite"),
])
def test_contract_fails_closed(content, message):
    with pytest.raises(GenerationContractError, match=message):
        parse_generation_contract(content, provider="fake", model="m",
                                  provider_request_id=None)


def test_provider_failure_has_no_successful_candidate_and_is_terminal():
    provider = FakeProvider(failure=RuntimeError("safe fake failure"))
    service, _, _ = system(provider)
    cmd = command()
    with pytest.raises(RuntimeError, match="safe fake failure"):
        service.execute(cmd)
    with pytest.raises(GenerationOperationTerminalFailure):
        service.execute(cmd)
    assert len(provider.requests) == 1


def test_normal_operation_and_sequential_replay_invoke_provider_once_total():
    service, provider, _ = system()
    first = service.execute(command())
    replay = service.execute(command())
    assert replay.idempotent_replay is True
    assert replay.revision_digest == first.revision_digest
    assert replay.audit_projection == first.audit_projection
    assert len(provider.requests) == 1


def test_concurrent_duplicate_fails_closed_without_second_provider_call():
    entered, release = Event(), Event()
    provider = FakeProvider(entered=entered, release=release)
    service, _, _ = system(provider)
    outcomes = []

    def first_call():
        outcomes.append(service.execute(command()))

    thread = Thread(target=first_call)
    thread.start()
    assert entered.wait(2)
    with pytest.raises(GenerationOperationInFlight):
        service.execute(command())
    assert len(provider.requests) == 1
    release.set()
    thread.join(2)
    assert not thread.is_alive() and len(outcomes) == 1
    assert service.execute(command()).idempotent_replay is True
    assert len(provider.requests) == 1


def test_same_key_different_digest_conflicts_without_provider_call():
    service, provider, _ = system()
    service.execute(command())
    with pytest.raises(GenerationOperationConflict):
        service.execute(command(revision_id="different-revision"))
    assert len(provider.requests) == 1


def test_source_context_is_snapshotted_for_digest_and_provider_payload():
    context = {"source_name": "Orange", "nested": {"labels": ["original"]}}
    cmd = command(context=context)
    original_digest = cmd.command_digest
    context["source_name"] = "MUTATED"
    context["nested"]["labels"].append("MUTATED")
    service, provider, _ = system()
    service.execute(cmd)
    assert cmd.command_digest == original_digest
    sent = json.loads(provider.requests[0].messages[0].content)
    assert sent["context"] == {"source_name": "Orange",
                                "nested": {"labels": ["original"]}}
    with pytest.raises(TypeError):
        cmd.source_context["source_name"] = "changed"


def test_provider_traceability_survives_in_result_and_audit_projection():
    result = system()[0].execute(command())
    assert (result.provider, result.model, result.provider_request_id) == (
        "fake", "fake-model", "safe-request-reference")
    audit = result.audit_projection
    assert (audit.provider, audit.model, audit.provider_request_id,
            audit.response_digest) == (result.provider, result.model,
                                       result.provider_request_id,
                                       result.response_digest)


def test_candidate_has_no_validation_approval_or_deployment_intent():
    result = system()[0].execute(command())
    assert result.revision.validation is None
    assert result.revision.human_decision is None
    assert result.revision.deployment_intent is None


def test_adapter_uses_one_attempt_bounded_timeout_and_no_fallback():
    service, provider, _ = system()
    service.execute(command())
    request = provider.requests[0]
    assert request.retry.max_attempts == 1
    assert request.timeout.seconds == 30.0
    assert request.provider == "fake"
    assert not hasattr(service._generation, "_providers")


def test_provider_response_identity_mismatch_is_terminal_and_has_no_candidate():
    class WrongModel(FakeProvider):
        def invoke(self, request):
            self.requests.append(request)
            return ProviderResponse("fake", "different", self.content)

    service, provider, _ = system(WrongModel())
    with pytest.raises(GenerationContractError, match="identity"):
        service.execute(command())
    with pytest.raises(GenerationOperationTerminalFailure):
        service.execute(command())
    assert len(provider.requests) == 1
