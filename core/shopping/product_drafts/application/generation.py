"""SHOP-AI-01A ProductDraft generation/preparation foundation."""
from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
import json
import re
from threading import Lock
from types import MappingProxyType
from typing import Mapping, Protocol

from core.providers.contracts import (
    JsonValue, ProviderAdapter, ProviderMessage, ProviderRequest, ProviderResponse,
    RetryPolicy, TimeoutPolicy,
)

from ..models import (
    LifecycleState, ProductDraftRevision, ProposedFields, ProvenanceType,
    RevisionIdentity, SourceSnapshotReference, StockStatus, SuggestionProvenance,
)
from ..serialization import sha256_digest, to_json_compatible
from ..values import ActorReference, Reference, require_text, require_utc

GENERATION_CONTRACT_VERSION = "1.0.0"
_PRICE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_FIELD_NAMES = frozenset(item.name for item in fields(ProposedFields))
_REFERENCE_FIELDS = frozenset(("categories", "tags", "image_references"))
_STRING_FIELDS = frozenset(("name", "description", "sku"))
_PRICE_FIELDS = frozenset(("regular_price", "sale_price"))


class GenerationContractError(ValueError):
    """The provider result did not satisfy the closed generation contract."""


class GenerationOperationInFlight(RuntimeError):
    """The operation key has already been consumed and is not replayable."""


class GenerationOperationTerminalFailure(RuntimeError):
    """The operation previously failed and cannot be retried automatically."""


class GenerationOperationConflict(ValueError):
    """An operation key was reused for a different command digest."""


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GenerationContractError("duplicate JSON fields are prohibited")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> object:
    raise GenerationContractError(f"non-finite JSON value {value} is prohibited")


def _canonical_context(value: Mapping[str, JsonValue]) -> str:
    if not isinstance(value, Mapping) or not value:
        raise ValueError("source_context must be a non-empty mapping")
    if any(not isinstance(key, str) for key in value):
        raise ValueError("source_context keys must be strings")
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("source_context must be JSON-safe") from exc


def _freeze_json(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class StructuredGenerationResult:
    proposed_fields: ProposedFields
    generated_fields: tuple[str, ...]
    provider: str
    model: str
    provider_request_id: str | None
    response_digest: str


class ProductDraftGenerationPort(Protocol):
    """Shopping-owned port; callers have no dependency on a vendor SDK."""

    def generate(self, *, source: SourceSnapshotReference,
                 source_context_json: str) -> StructuredGenerationResult: ...


def _reference(value: object, field_name: str) -> Reference:
    if not isinstance(value, dict) or set(value) - {"id", "label"} or "id" not in value:
        raise GenerationContractError(f"{field_name} references require only id and optional label")
    if not isinstance(value["id"], str) or not value["id"]:
        raise GenerationContractError(f"{field_name} reference id must be a non-empty string")
    if "label" in value and value["label"] is not None and not isinstance(value["label"], str):
        raise GenerationContractError(f"{field_name} reference label must be a string or null")
    return Reference(value["id"], value.get("label"))


def parse_generation_contract(payload: str, *, provider: str, model: str,
                              provider_request_id: str | None) -> StructuredGenerationResult:
    """Parse JSON with an exact envelope and exact ProposedFields-shaped body."""
    if not isinstance(payload, str):
        raise GenerationContractError("provider content must be a JSON string")
    try:
        document = json.loads(payload, object_pairs_hook=_closed_object,
                              parse_constant=_reject_non_finite)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GenerationContractError("provider content is malformed JSON") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "proposed_fields"}:
        raise GenerationContractError("generation envelope fields are invalid")
    if document["schema_version"] != GENERATION_CONTRACT_VERSION:
        raise GenerationContractError("unsupported generation schema_version")
    values = document["proposed_fields"]
    if not isinstance(values, dict) or not values or set(values) - _FIELD_NAMES:
        raise GenerationContractError("proposed_fields are empty or contain unknown fields")

    mapped: dict[str, object] = {}
    for name, value in values.items():
        if name in _STRING_FIELDS:
            if not isinstance(value, str):
                raise GenerationContractError(f"{name} must be a string")
            mapped[name] = value
        elif name in _PRICE_FIELDS:
            if not isinstance(value, str) or not _PRICE.fullmatch(value):
                raise GenerationContractError(f"{name} must be a non-negative decimal string")
            try:
                mapped[name] = Decimal(value)
            except InvalidOperation as exc:
                raise GenerationContractError(f"{name} is not a decimal") from exc
        elif name == "inventory_quantity":
            if type(value) is not int or value < 0:
                raise GenerationContractError("inventory_quantity must be a non-negative integer")
            mapped[name] = value
        elif name == "stock_status":
            if not isinstance(value, str):
                raise GenerationContractError("stock_status must be a string")
            try:
                mapped[name] = StockStatus(value)
            except ValueError as exc:
                raise GenerationContractError("stock_status is unsupported") from exc
        elif name in _REFERENCE_FIELDS:
            if not isinstance(value, list):
                raise GenerationContractError(f"{name} must be an array")
            mapped[name] = tuple(_reference(item, name) for item in value)
    try:
        proposed = ProposedFields(**mapped)
    except (TypeError, ValueError) as exc:
        raise GenerationContractError("generated fields violate ProductDraft constraints") from exc
    return StructuredGenerationResult(
        proposed, tuple(sorted(values)), provider, model, provider_request_id,
        sha256_digest(document),
    )


class CanonicalProviderProductDraftGenerationAdapter(ProductDraftGenerationPort):
    """Exactly one invocation of one explicitly injected canonical provider."""

    def __init__(self, provider: ProviderAdapter, *, model: str,
                 timeout_seconds: float = 30.0) -> None:
        require_text(model, "model")
        if not 0 < timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be in the bounded range (0, 60]")
        self._provider = provider
        self._model = model
        self._timeout = TimeoutPolicy(timeout_seconds)

    def generate(self, *, source: SourceSnapshotReference,
                 source_context_json: str) -> StructuredGenerationResult:
        if not isinstance(source, SourceSnapshotReference):
            raise ValueError("source must be a SourceSnapshotReference")
        if not isinstance(source_context_json, str) or not source_context_json:
            raise ValueError("source_context_json must be a canonical JSON snapshot")
        context_json = json.dumps(
            {"source": to_json_compatible(source),
             "context": json.loads(source_context_json)},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        )
        request = ProviderRequest(
            provider=self._provider.provider, model=self._model,
            messages=(ProviderMessage("user", context_json),),
            instructions=("Return only JSON for ProductDraft generation contract 1.0.0 with exact "
                          "envelope keys schema_version and proposed_fields. Do not add fields."),
            metadata={"operation": "product_draft_generation",
                      "contract_version": GENERATION_CONTRACT_VERSION},
            timeout=self._timeout, retry=RetryPolicy(max_attempts=1),
        )
        response = self._provider.invoke(request)
        if not isinstance(response, ProviderResponse):
            raise GenerationContractError("provider returned an invalid response type")
        if response.provider != request.provider or response.model != request.model:
            raise GenerationContractError("provider response identity does not match request")
        if response.status != "completed" or not response.content:
            raise GenerationContractError("provider response is incomplete")
        return parse_generation_contract(
            response.content, provider=response.provider, model=response.model,
            provider_request_id=response.provider_request_id,
        )


@dataclass(frozen=True, slots=True)
class GenerateProductDraftCommand:
    draft_id: str
    revision_id: str
    source: SourceSnapshotReference
    source_context: Mapping[str, JsonValue]
    actor: ActorReference
    created_at: datetime
    correlation_id: str
    audit_reference: str
    idempotency_key: str
    current_revision: ProductDraftRevision | None = None
    source_context_json: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        for name in ("draft_id", "revision_id", "correlation_id", "audit_reference", "idempotency_key"):
            require_text(getattr(self, name), name)
        if not isinstance(self.source, SourceSnapshotReference):
            raise ValueError("source must be a SourceSnapshotReference")
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        if self.current_revision is not None and not isinstance(self.current_revision, ProductDraftRevision):
            raise ValueError("current_revision must be a ProductDraftRevision or null")
        canonical = _canonical_context(self.source_context)
        object.__setattr__(self, "source_context_json", canonical)
        object.__setattr__(self, "source_context", _freeze_json(json.loads(canonical)))
        require_utc(self.created_at, "created_at")

    @property
    def command_digest(self) -> str:
        return sha256_digest({
            "draft_id": self.draft_id, "revision_id": self.revision_id,
            "source": to_json_compatible(self.source),
            "source_context": json.loads(self.source_context_json),
            "actor": to_json_compatible(self.actor), "created_at": self.created_at,
            "correlation_id": self.correlation_id, "audit_reference": self.audit_reference,
            "idempotency_key": self.idempotency_key,
            "current_revision": (to_json_compatible(self.current_revision)
                                 if self.current_revision is not None else None),
        })


@dataclass(frozen=True, slots=True)
class ProductDraftGenerationAuditProjection:
    event_type: str
    draft_id: str
    revision_id: str
    actor_reference: str
    correlation_id: str
    audit_reference: str
    occurred_at: datetime
    outcome: str
    provider: str
    model: str
    provider_request_id: str | None
    response_digest: str
    revision_digest: str


@dataclass(frozen=True, slots=True)
class ProductDraftGenerationResult:
    draft_id: str
    revision_id: str
    revision_number: int
    outcome: str
    correlation_id: str
    audit_reference: str
    provider: str
    model: str
    provider_request_id: str | None
    response_digest: str
    revision_digest: str
    revision: ProductDraftRevision
    audit_projection: ProductDraftGenerationAuditProjection
    idempotent_replay: bool = False

    @property
    def provider_reference(self) -> str:
        return f"{self.provider}:{self.model}"

    def as_replay(self) -> "ProductDraftGenerationResult":
        return replace(self, idempotent_replay=True)


class GenerationOperationClaimStatus(str, Enum):
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class GenerationOperationClaim:
    status: GenerationOperationClaimStatus
    result: ProductDraftGenerationResult | None = None


class ProductDraftGenerationOperationCoordinator(Protocol):
    """Atomically consumes operation keys within the coordinator's durability scope."""

    def claim(self, key: str, command_digest: str, draft_id: str,
              revision_id: str) -> GenerationOperationClaim: ...
    def complete(self, key: str, command_digest: str,
                 result: ProductDraftGenerationResult) -> None: ...
    def fail(self, key: str, command_digest: str) -> None: ...


@dataclass(slots=True)
class _OperationRecord:
    command_digest: str
    draft_id: str
    revision_id: str
    state: str = "IN_FLIGHT"
    result: ProductDraftGenerationResult | None = None


class InMemoryProductDraftGenerationOperationCoordinator:
    """Thread-safe, explicitly non-Production coordinator for SHOP-AI-01A."""

    production_safe = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._operations: dict[str, _OperationRecord] = {}

    def claim(self, key: str, command_digest: str, draft_id: str,
              revision_id: str) -> GenerationOperationClaim:
        require_text(key, "key")
        require_text(command_digest, "command_digest")
        with self._lock:
            record = self._operations.get(key)
            if record is None:
                self._operations[key] = _OperationRecord(command_digest, draft_id, revision_id)
                return GenerationOperationClaim(GenerationOperationClaimStatus.CLAIMED)
            if (record.command_digest, record.draft_id, record.revision_id) != (command_digest, draft_id, revision_id):
                raise GenerationOperationConflict("idempotency key conflicts with another command")
            if record.state == "COMPLETED":
                return GenerationOperationClaim(GenerationOperationClaimStatus.COMPLETED,
                                                record.result)
            if record.state == "TERMINAL_FAILED":
                raise GenerationOperationTerminalFailure("operation previously failed terminally")
            raise GenerationOperationInFlight("operation is already consumed/in flight")

    def complete(self, key: str, command_digest: str,
                 result: ProductDraftGenerationResult) -> None:
        with self._lock:
            record = self._operations.get(key)
            if record is None or record.command_digest != command_digest or record.state != "IN_FLIGHT":
                raise RuntimeError("only the claimed operation can be completed")
            record.state = "COMPLETED"
            record.result = result

    def fail(self, key: str, command_digest: str) -> None:
        with self._lock:
            record = self._operations.get(key)
            if record is None or record.command_digest != command_digest or record.state != "IN_FLIGHT":
                raise RuntimeError("only the claimed operation can be failed")
            record.state = "TERMINAL_FAILED"


class ProductDraftGenerationService:
    def __init__(self, generation: ProductDraftGenerationPort,
                 coordinator: ProductDraftGenerationOperationCoordinator) -> None:
        self._generation = generation
        self._coordinator = coordinator

    def execute(self, command: GenerateProductDraftCommand) -> ProductDraftGenerationResult:
        if not isinstance(command, GenerateProductDraftCommand):
            raise ValueError("command must be a GenerateProductDraftCommand")
        digest = command.command_digest
        claim = self._coordinator.claim(command.idempotency_key, digest,
                                        command.draft_id, command.revision_id)
        if claim.status is GenerationOperationClaimStatus.COMPLETED:
            if claim.result is None:
                raise RuntimeError("completed operation has no result")
            return claim.result.as_replay()
        try:
            generated = self._generation.generate(
                source=command.source, source_context_json=command.source_context_json)
            current = command.current_revision
            number = 1 if current is None else current.revision_number + 1
            previous = None if current is None else current.revision_id
            identity = RevisionIdentity(
                command.draft_id, command.revision_id, number, previous, command.created_at,
                command.actor, command.correlation_id, command.audit_reference,
            )
            provider_reference = f"{generated.provider}:{generated.model}"
            suggestions = tuple(
                SuggestionProvenance(
                    suggestion_id=sha256_digest({"revision_id": command.revision_id,
                                                 "field": name,
                                                 "response_digest": generated.response_digest}),
                    provenance=ProvenanceType.AI, field=name,
                    suggested_at=command.created_at,
                    provider_model_reference=provider_reference,
                    generation_audit_reference=command.audit_reference,
                ) for name in generated.generated_fields
            )
            if current is None:
                revision = ProductDraftRevision(identity, command.source, LifecycleState.DRAFT,
                                                generated.proposed_fields, suggestions)
            else:
                revision = current.new_revision(identity, generated.proposed_fields,
                                                source=command.source, suggestions=suggestions)
            revision_digest = sha256_digest(revision)
            audit = ProductDraftGenerationAuditProjection(
                "PRODUCT_DRAFT_GENERATED", command.draft_id, command.revision_id,
                command.actor.actor_id, command.correlation_id, command.audit_reference,
                command.created_at, "PREPARED", generated.provider, generated.model,
                generated.provider_request_id, generated.response_digest, revision_digest,
            )
            result = ProductDraftGenerationResult(
                command.draft_id, command.revision_id, number, "PREPARED",
                command.correlation_id, command.audit_reference, generated.provider,
                generated.model, generated.provider_request_id, generated.response_digest,
                revision_digest, revision, audit,
            )
        except Exception:
            self._coordinator.fail(command.idempotency_key, digest)
            raise
        self._coordinator.complete(command.idempotency_key, digest, result)
        return result
