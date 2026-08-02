"""Immutable SHOP-02A v1.0.0 ProductDraft domain model."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .values import ActorReference, ActorType, Reference, SCHEMA_VERSION, require_digest, require_text, require_utc


class LifecycleState(str, Enum):
    DRAFT="DRAFT"; VALIDATED="VALIDATED"; REVIEW_REQUIRED="REVIEW_REQUIRED"; APPROVED="APPROVED"
    REJECTED="REJECTED"; REVOKED="REVOKED"; SUPERSEDED="SUPERSEDED"; DEPLOYMENT_READY="DEPLOYMENT_READY"


class ProvenanceType(str, Enum):
    HUMAN="HUMAN"; AI="AI"; IMPORT="IMPORT"; SYSTEM="SYSTEM"


class ValidationStatus(str, Enum): VALID="VALID"; INVALID="INVALID"
class ApprovalDecisionType(str, Enum): APPROVE="APPROVE"; REJECT="REJECT"; REVOKE="REVOKE"
class ReadinessStatus(str, Enum): NOT_READY="NOT_READY"; READY="READY"
class StockStatus(str, Enum): IN_STOCK="IN_STOCK"; OUT_OF_STOCK="OUT_OF_STOCK"; ON_BACKORDER="ON_BACKORDER"


@dataclass(frozen=True, slots=True)
class SourceSnapshotReference:
    source_product_identifier: str
    observed_at: datetime
    snapshot_reference: str | None = None
    snapshot_digest: str | None = None
    source_system: str = "WOOCOMMERCE"
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        require_text(self.source_product_identifier, "source_product_identifier"); require_utc(self.observed_at, "observed_at")
        if self.source_system != "WOOCOMMERCE": raise ValueError("source_system must be WOOCOMMERCE")
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")
        if self.snapshot_reference is None and self.snapshot_digest is None: raise ValueError("a snapshot reference or digest is required")
        if self.snapshot_reference is not None: require_text(self.snapshot_reference, "snapshot_reference")
        if self.snapshot_digest is not None: require_digest(self.snapshot_digest, "snapshot_digest")


@dataclass(frozen=True, slots=True)
class RevisionIdentity:
    draft_id: str; revision_id: str; revision_number: int; previous_revision_id: str | None
    created_at: datetime; created_by: ActorReference; correlation_id: str; audit_reference: str
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        for n in ("draft_id","revision_id","correlation_id","audit_reference"): require_text(getattr(self,n), n)
        if type(self.revision_number) is not int or self.revision_number < 1: raise ValueError("revision_number must be >= 1")
        if self.previous_revision_id is not None: require_text(self.previous_revision_id, "previous_revision_id")
        if self.revision_number == 1 and self.previous_revision_id is not None: raise ValueError("first revision cannot have a predecessor")
        if self.revision_number > 1 and self.previous_revision_id is None: raise ValueError("later revisions require a predecessor")
        require_utc(self.created_at, "created_at")
        if not isinstance(self.created_by, ActorReference):
            raise ValueError("created_by must be an ActorReference")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class SuggestionProvenance:
    suggestion_id: str; provenance: ProvenanceType; field: str; suggested_at: datetime
    provider_model_reference: str | None = None; generation_audit_reference: str | None = None
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        require_text(self.suggestion_id,"suggestion_id"); require_text(self.field,"field"); require_utc(self.suggested_at,"suggested_at")
        if not isinstance(self.provenance, ProvenanceType): object.__setattr__(self,"provenance",ProvenanceType(self.provenance))
        for name in ("provider_model_reference", "generation_audit_reference"):
            value = getattr(self, name)
            if value is not None:
                require_text(value, name)
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    revision_id: str; status: ValidationStatus; errors: tuple[str,...]; warnings: tuple[str,...]
    validator_version: str; validated_at: datetime; validation_input_digest: str; result_digest: str; audit_reference: str
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        for n in ("revision_id","validator_version","audit_reference"): require_text(getattr(self,n),n)
        if not isinstance(self.status,ValidationStatus): object.__setattr__(self,"status",ValidationStatus(self.status))
        object.__setattr__(self,"errors",tuple(self.errors)); object.__setattr__(self,"warnings",tuple(self.warnings))
        if any(not isinstance(x,str) for x in self.errors+self.warnings): raise ValueError("validation messages must be strings")
        require_utc(self.validated_at,"validated_at"); require_digest(self.validation_input_digest,"validation_input_digest"); require_digest(self.result_digest,"result_digest")
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    decision_id: str; draft_id: str; revision_id: str; reviewer: ActorReference; decision: ApprovalDecisionType
    decided_at: datetime; reason: str; correlation_id: str; audit_reference: str; idempotency_key: str
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        for n in ("decision_id","draft_id","revision_id","reason","correlation_id","audit_reference","idempotency_key"): require_text(getattr(self,n),n)
        if not isinstance(self.reviewer, ActorReference):
            raise ValueError("reviewer must be an ActorReference")
        if self.reviewer.actor_type is not ActorType.HUMAN: raise ValueError("approval reviewer must be HUMAN")
        if not isinstance(self.decision,ApprovalDecisionType): object.__setattr__(self,"decision",ApprovalDecisionType(self.decision))
        require_utc(self.decided_at,"decided_at")
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class DeploymentIntent:
    intent_id: str; draft_id: str; revision_id: str; target_adapter_reference: str; expected_source_digest: str
    idempotency_key: str; authorization_reference: str; audit_reference: str; readiness_status: ReadinessStatus
    created_by: ActorReference; correlation_id: str; created_at: datetime; schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        for n in ("intent_id","draft_id","revision_id","target_adapter_reference","idempotency_key","authorization_reference","audit_reference","correlation_id"): require_text(getattr(self,n),n)
        require_digest(self.expected_source_digest,"expected_source_digest"); require_utc(self.created_at,"created_at")
        if not isinstance(self.readiness_status,ReadinessStatus): object.__setattr__(self,"readiness_status",ReadinessStatus(self.readiness_status))
        if not isinstance(self.created_by, ActorReference):
            raise ValueError("created_by must be an ActorReference")
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class ProposedFields:
    name: str | None=None; description: str | None=None; sku: str | None=None
    regular_price: Decimal | None=None; sale_price: Decimal | None=None; inventory_quantity: int | None=None
    stock_status: StockStatus | None=None; categories: tuple[Reference,...]=(); tags: tuple[Reference,...]=(); image_references: tuple[Reference,...]=()
    def __post_init__(self):
        for n in ("categories","tags","image_references"): object.__setattr__(self,n,tuple(getattr(self,n)))
        if not any(getattr(self,n) is not None and getattr(self,n) != () for n in self.__dataclass_fields__): raise ValueError("at least one proposed field is required")
        for n in ("name", "description", "sku"):
            if getattr(self, n) is not None and not isinstance(getattr(self, n), str):
                raise ValueError(f"{n} must be a string or null")
        for n in ("categories", "tags", "image_references"):
            values = getattr(self, n)
            if any(not isinstance(value, Reference) for value in values):
                raise ValueError(f"{n} must contain Reference values")
            if len(values) != len(set(values)):
                raise ValueError(f"{n} must contain unique values")
        for n in ("regular_price","sale_price"):
            v=getattr(self,n)
            if v is not None and (not isinstance(v,Decimal) or v < 0): raise ValueError(f"{n} must be a non-negative Decimal")
        if self.inventory_quantity is not None and (type(self.inventory_quantity) is not int or self.inventory_quantity < 0): raise ValueError("inventory_quantity must be non-negative")
        if self.stock_status is not None and not isinstance(self.stock_status,StockStatus): object.__setattr__(self,"stock_status",StockStatus(self.stock_status))


@dataclass(frozen=True, slots=True)
class ProductDraftRevision:
    identity: RevisionIdentity; source: SourceSnapshotReference; state: LifecycleState; proposed_fields: ProposedFields
    suggestions: tuple[SuggestionProvenance,...]=field(default_factory=tuple); validation: ValidationResult | None=None
    human_decision: ApprovalDecision | None=None; deployment_intent: DeploymentIntent | None=None
    schema_version: str = SCHEMA_VERSION
    def __post_init__(self):
        if not isinstance(self.identity, RevisionIdentity): raise ValueError("identity must be a RevisionIdentity")
        if not isinstance(self.source, SourceSnapshotReference): raise ValueError("source must be a SourceSnapshotReference")
        if not isinstance(self.proposed_fields, ProposedFields): raise ValueError("proposed_fields must be ProposedFields")
        if not isinstance(self.state,LifecycleState): object.__setattr__(self,"state",LifecycleState(self.state))
        object.__setattr__(self,"suggestions",tuple(self.suggestions))
        if any(not isinstance(item, SuggestionProvenance) for item in self.suggestions):
            raise ValueError("suggestions must contain SuggestionProvenance values")
        if self.validation is not None and not isinstance(self.validation, ValidationResult): raise ValueError("validation must be ValidationResult or null")
        if self.human_decision is not None and not isinstance(self.human_decision, ApprovalDecision): raise ValueError("human_decision must be ApprovalDecision or null")
        if self.deployment_intent is not None and not isinstance(self.deployment_intent, DeploymentIntent): raise ValueError("deployment_intent must be DeploymentIntent or null")
        if self.schema_version != SCHEMA_VERSION: raise ValueError("unsupported schema_version")
        if self.validation and self.validation.revision_id != self.identity.revision_id: raise ValueError("validation must match exact revision")
        if self.human_decision and (self.human_decision.draft_id,self.human_decision.revision_id)!=(self.identity.draft_id,self.identity.revision_id): raise ValueError("decision must match exact revision")
        if self.deployment_intent and (self.deployment_intent.draft_id,self.deployment_intent.revision_id)!=(self.identity.draft_id,self.identity.revision_id): raise ValueError("deployment intent must match exact revision")
        if self.deployment_intent and (
            self.human_decision is None
            or self.human_decision.decision is not ApprovalDecisionType.APPROVE
        ):
            raise ValueError("deployment intent requires an active exact-revision approval")

    @property
    def draft_id(self): return self.identity.draft_id
    @property
    def revision_id(self): return self.identity.revision_id
    @property
    def revision_number(self): return self.identity.revision_number

    def new_revision(self, identity: RevisionIdentity, proposed_fields: ProposedFields, *, source: SourceSnapshotReference | None=None, suggestions: tuple[SuggestionProvenance,...]=()) -> "ProductDraftRevision":
        if identity.draft_id != self.draft_id or identity.revision_number != self.revision_number+1 or identity.previous_revision_id != self.revision_id: raise ValueError("invalid revision chain")
        return ProductDraftRevision(identity, source or self.source, LifecycleState.DRAFT, proposed_fields, suggestions)

    def with_state(self, state: LifecycleState) -> "ProductDraftRevision": return replace(self,state=state)
