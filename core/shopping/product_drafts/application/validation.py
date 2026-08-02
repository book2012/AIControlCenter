"""Deterministic ProductDraft revision validation application service."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Protocol

from ..models import ProductDraftRevision, ValidationResult, ValidationStatus
from ..serialization import sha256_digest, to_json_compatible
from ..values import ActorReference, require_text, require_utc
from .ports import AuditEvent, AuditEventPort
from .results import ApplicationResult


class FindingSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True, order=True)
class ValidationFinding:
    severity: FindingSeverity
    code: str

    def __post_init__(self) -> None:
        if not isinstance(self.severity, FindingSeverity):
            object.__setattr__(self, "severity", FindingSeverity(self.severity))
        require_text(self.code, "code")


class ValidationRulesPort(Protocol):
    def evaluate(self, revision: ProductDraftRevision) -> tuple[ValidationFinding, ...]: ...


class ContractValidationRules:
    """Rules limited to invariants represented by the ProductDraft v1 contracts."""

    def evaluate(self, revision: ProductDraftRevision) -> tuple[ValidationFinding, ...]:
        findings: list[ValidationFinding] = []
        if revision.validation and revision.validation.revision_id != revision.revision_id:
            findings.append(ValidationFinding(FindingSeverity.ERROR, "VALIDATION_REVISION_MISMATCH"))
        if revision.human_decision and (
                revision.human_decision.draft_id != revision.draft_id or
                revision.human_decision.revision_id != revision.revision_id):
            findings.append(ValidationFinding(FindingSeverity.ERROR, "DECISION_REVISION_MISMATCH"))
        if revision.deployment_intent and (
                revision.deployment_intent.draft_id != revision.draft_id or
                revision.deployment_intent.revision_id != revision.revision_id):
            findings.append(ValidationFinding(FindingSeverity.ERROR, "INTENT_REVISION_MISMATCH"))
        return tuple(findings)


class ProductDraftValidationService:
    def __init__(self, rules: ValidationRulesPort, audit: AuditEventPort) -> None:
        self._rules = rules
        self._audit = audit

    def validate(self, revision: ProductDraftRevision, *, validator_version: str,
                 validated_at: datetime, actor: ActorReference,
                 audit_reference: str, correlation_id: str) -> ApplicationResult:
        if not isinstance(revision, ProductDraftRevision):
            raise TypeError("revision must be a ProductDraftRevision")
        require_text(validator_version, "validator_version")
        require_text(audit_reference, "audit_reference")
        require_text(correlation_id, "correlation_id")
        require_utc(validated_at, "validated_at")
        if not isinstance(actor, ActorReference):
            raise ValueError("actor must be an ActorReference")

        validation_input_digest = sha256_digest(to_json_compatible(revision))
        findings = tuple(sorted(set(self._rules.evaluate(revision)), key=lambda item: (item.code, item.severity.value)))
        errors = tuple(item.code for item in findings if item.severity is FindingSeverity.ERROR)
        warnings = tuple(item.code for item in findings if item.severity is FindingSeverity.WARNING)
        status = ValidationStatus.INVALID if errors else ValidationStatus.VALID
        result_seed = {
            "revision_id": revision.revision_id, "status": status.value,
            "errors": errors, "warnings": warnings,
            "validator_version": validator_version, "validated_at": validated_at,
            "validation_input_digest": validation_input_digest,
            "audit_reference": audit_reference,
        }
        validation = ValidationResult(
            revision.revision_id, status, errors, warnings, validator_version,
            validated_at, validation_input_digest, sha256_digest(result_seed),
            audit_reference,
        )
        updated = replace(revision, validation=validation)
        outcome = "VALID" if status is ValidationStatus.VALID else "INVALID"
        result = ApplicationResult(
            "VALIDATE", revision.draft_id, revision.revision_id, outcome, "NOT_APPLICABLE",
            audit_reference, correlation_id, validated_at, validation=validation,
            revision=updated,
        )
        self._audit.record(AuditEvent.create(
            event_type="PRODUCT_DRAFT_VALIDATED", draft_id=revision.draft_id,
            revision_id=revision.revision_id, actor=actor,
            correlation_id=correlation_id, authorization_reference="NOT_APPLICABLE",
            audit_reference=audit_reference, outcome=outcome,
            occurred_at=validated_at, payload=dict(result.projection()),
        ))
        return result
