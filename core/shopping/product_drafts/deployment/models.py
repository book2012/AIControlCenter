"""Immutable controlled Commerce write application models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ..serialization import sha256_digest
from ..values import ActorReference, SCHEMA_VERSION, require_digest, require_text, require_utc


class CommerceOperation(str, Enum):
    UPDATE_PRODUCT = "UPDATE_PRODUCT"


class WriteMode(str, Enum):
    FAKE = "FAKE"
    DRY_RUN = "DRY_RUN"


@dataclass(frozen=True, slots=True)
class SourceFreshnessPolicy:
    max_age: timedelta

    def __post_init__(self) -> None:
        if not isinstance(self.max_age, timedelta) or self.max_age < timedelta(0):
            raise ValueError("max_age must be a non-negative timedelta")


@dataclass(frozen=True, slots=True)
class ControlledDeploymentIntent:
    """Application binding around, without changing, deployment-intent v1.0.0."""

    deployment_intent_id: str
    draft_id: str
    revision_id: str
    expected_revision_number: int
    expected_source_snapshot_digest: str
    target_product_identifier: str
    operation: CommerceOperation
    requested_actor_reference: ActorReference
    authorization_reference: str
    audit_reference: str
    correlation_id: str
    idempotency_key: str
    requested_at: datetime
    payload_digest: str
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("deployment_intent_id", "draft_id", "revision_id",
                     "target_product_identifier", "authorization_reference",
                     "audit_reference", "correlation_id", "idempotency_key"):
            require_text(getattr(self, name), name)
        if type(self.expected_revision_number) is not int or self.expected_revision_number < 1:
            raise ValueError("expected_revision_number must be >= 1")
        require_digest(self.expected_source_snapshot_digest, "expected_source_snapshot_digest")
        require_digest(self.payload_digest, "payload_digest")
        if not isinstance(self.operation, CommerceOperation):
            object.__setattr__(self, "operation", CommerceOperation(self.operation))
        if not isinstance(self.requested_actor_reference, ActorReference):
            raise ValueError("requested_actor_reference must be an ActorReference")
        require_utc(self.requested_at, "requested_at")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")


@dataclass(frozen=True, slots=True)
class ControlledWritePlan:
    schema_version: str
    mode: WriteMode
    operation: CommerceOperation
    draft_id: str
    revision_id: str
    revision_number: int
    deployment_intent_id: str
    target_product_identifier: str
    expected_source_digest: str
    payload_digest: str
    actor_reference: ActorReference
    authorization_reference: str
    authorization_policy_reference: str
    audit_reference: str
    correlation_id: str
    idempotency_key: str
    requested_at: datetime
    evaluated_at: datetime
    plan_digest: str

    @classmethod
    def create(cls, intent: ControlledDeploymentIntent, *, mode: WriteMode,
               policy_reference: str, evaluated_at: datetime) -> "ControlledWritePlan":
        require_utc(evaluated_at, "evaluated_at")
        seed = {
            "schema_version": SCHEMA_VERSION, "mode": mode.value,
            "operation": intent.operation.value, "draft_id": intent.draft_id,
            "revision_id": intent.revision_id,
            "revision_number": intent.expected_revision_number,
            "deployment_intent_id": intent.deployment_intent_id,
            "target_product_identifier": intent.target_product_identifier,
            "expected_source_digest": intent.expected_source_snapshot_digest,
            "payload_digest": intent.payload_digest,
            "actor_reference": intent.requested_actor_reference,
            "authorization_reference": intent.authorization_reference,
            "authorization_policy_reference": policy_reference,
            "audit_reference": intent.audit_reference,
            "correlation_id": intent.correlation_id,
            "idempotency_key": intent.idempotency_key,
            "requested_at": intent.requested_at, "evaluated_at": evaluated_at,
        }
        return cls(**seed, plan_digest=sha256_digest(seed))
