"""Pure B3-E migration planning and legacy classification contracts.

This module describes evidence and decisions; it never opens a database,
performs a migration, creates a backup, or reads an operating environment.
Only schema and provenance facts already established by the repository are
encoded. Unknown production facts remain explicit unmet prerequisites.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


CONTRACT_VERSION = "aicc-b3e-migration-contract/v1"
PERSISTENCE_SCHEMA_VERSION = "shopping-customer-persistence/v1"
# Historical B3 evidence remains v1. C1 describes, but does not execute, the
# separately approved v1 -> v2 migration and never reclassifies old evidence.
HISTORICAL_PERSISTENCE_SCHEMA_VERSION = PERSISTENCE_SCHEMA_VERSION
CURRENT_PERSISTENCE_SCHEMA_VERSION = "shopping-customer-persistence/v2"
TARGET_PERSISTENCE_SCHEMA_VERSION = CURRENT_PERSISTENCE_SCHEMA_VERSION
C1_VERIFICATION_TABLES = (
    "shopping_verification_challenges",
    "shopping_verification_attempts",
    "shopping_trusted_receipts",
)
C1_START_LIFECYCLE = ("START_CLAIMED", "START_UNKNOWN", "STARTED", "PENDING")
C1_PROVIDER_START_STATUS = ("STARTED", "PENDING")
EXPLICIT_UNOWNED_MARKER = "unowned/v1"
SYNTHETIC_PROVENANCE = "synthetic_fixture"

EXPECTED_OWNERSHIP_TABLE = "shopping_inquiry_ownership"
EXPECTED_OWNERSHIP_COLUMNS = (
    "inquiry_id", "customer_id", "session_id", "version",
)
EXPECTED_CORE_TABLES = (
    "shopping_customer_persistence_meta",
    "shopping_inquiry_ownership",
    "shopping_inquiry_idempotency",
    "shopping_inquiry_audit",
    "shopping_customers",
    "shopping_sessions",
)


class ClosedContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )

    contract_version: Literal[CONTRACT_VERSION] = CONTRACT_VERSION


class LegacyInquiryClassification(str, Enum):
    OWNED = "OWNED"
    EXPLICITLY_UNOWNED = "EXPLICITLY_UNOWNED"
    AMBIGUOUS = "AMBIGUOUS"
    INCOMPATIBLE_SCHEMA = "INCOMPATIBLE_SCHEMA"
    MALFORMED = "MALFORMED"


class ValidationOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    BLOCKED = "BLOCKED"


class StopReason(str, Enum):
    OPERATIONAL_ACCESS_REQUIRED = "OPERATIONAL_ACCESS_REQUIRED"
    PATH_POLICY_UNVERIFIED = "PATH_POLICY_UNVERIFIED"
    SCHEMA_VERSION_UNVERIFIED = "SCHEMA_VERSION_UNVERIFIED"
    BACKUP_UNVERIFIED = "BACKUP_UNVERIFIED"
    RESTORE_UNVERIFIED = "RESTORE_UNVERIFIED"
    DRY_RUN_UNVERIFIED = "DRY_RUN_UNVERIFIED"
    INTEGRITY_CHECK_UNVERIFIED = "INTEGRITY_CHECK_UNVERIFIED"
    ROLLBACK_INVARIANT_UNVERIFIED = "ROLLBACK_INVARIANT_UNVERIFIED"
    TRUSTED_VERIFIER_UNAPPROVED = "TRUSTED_VERIFIER_UNAPPROVED"
    RUNTIME_COMPOSITION_UNREVIEWED = "RUNTIME_COMPOSITION_UNREVIEWED"
    LEGACY_CLASSIFICATION_AMBIGUOUS = "LEGACY_CLASSIFICATION_AMBIGUOUS"
    APPROVAL_GATE_MISSING = "APPROVAL_GATE_MISSING"


class OperationalApprovalGate(str, Enum):
    TRUSTED_VERIFIER = "TRUSTED_VERIFIER"
    DATABASE_INVENTORY = "DATABASE_INVENTORY"
    BACKUP_RESTORE = "BACKUP_RESTORE"
    MIGRATION_DRY_RUN = "MIGRATION_DRY_RUN"
    RUNTIME_COMPOSITION = "RUNTIME_COMPOSITION"
    AUTHENTICATED_QA = "AUTHENTICATED_QA"
    ACTIVATION_ROLLBACK_DRILL = "ACTIVATION_ROLLBACK_DRILL"
    DEV_INGRESS_ATTESTATION = "DEV_INGRESS_ATTESTATION"


class SchemaEvidence(ClosedContract):
    """A repository- or syntheticly-described schema observation."""

    provenance: Literal[SYNTHETIC_PROVENANCE, "repository_source"]
    version: str | None = Field(default=None, min_length=1, max_length=96)
    tables: tuple[str, ...] = Field(default=(), max_length=32)
    ownership_columns: tuple[str, ...] = Field(default=(), max_length=16)

    @field_validator("tables", "ownership_columns")
    @classmethod
    def bounded_names(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("schema names must be unique")
        if any(type(value) is not str or not 1 <= len(value) <= 96 for value in values):
            raise ValueError("schema names must be bounded strings")
        return values


class OwnershipEvidence(ClosedContract):
    """The only ownership fields evidenced by the current B3-D schema."""

    inquiry_id: str = Field(min_length=1, max_length=80)
    customer_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=80)
    version: int = Field(strict=True, ge=0)


class SyntheticLegacyInquiry(ClosedContract):
    """Synthetic classification input; it carries no customer content/token."""

    provenance: Literal[SYNTHETIC_PROVENANCE]
    inquiry_id: str = Field(min_length=1, max_length=80)
    schema_evidence: SchemaEvidence
    ownership: OwnershipEvidence | None = None
    payload_marker: str | None = Field(default=None, max_length=32)
    legacy_token_hash_present: bool = False

    @model_validator(mode="after")
    def marker_is_bounded(self) -> SyntheticLegacyInquiry:
        if self.payload_marker is not None and not self.payload_marker:
            raise ValueError("payload marker cannot be empty")
        if self.ownership is not None and self.ownership.inquiry_id != self.inquiry_id:
            raise ValueError("ownership must reference the same inquiry")
        return self


class ClassificationEvidence(ClosedContract):
    inquiry_id: str
    classification: LegacyInquiryClassification
    reasons: tuple[str, ...] = Field(min_length=1, max_length=4)
    legacy_access_permitted: bool
    automatic_claim_permitted: Literal[False] = False

    @model_validator(mode="after")
    def access_matches_classification(self) -> ClassificationEvidence:
        permitted = self.classification is LegacyInquiryClassification.EXPLICITLY_UNOWNED
        if self.legacy_access_permitted is not permitted:
            raise ValueError("legacy access must match explicit-unowned classification")
        return self


class BackupRestoreEvidence(ClosedContract):
    """Acceptance envelope for a future separately approved backup operation."""

    backup_created: bool = False
    backup_hash_verified: bool = False
    restored_to_isolated_path: bool = False
    restored_integrity_checked: bool = False
    restored_schema_checked: bool = False

    @property
    def accepted(self) -> bool:
        return all((self.backup_created, self.backup_hash_verified,
                    self.restored_to_isolated_path, self.restored_integrity_checked,
                    self.restored_schema_checked))


class DryRunEvidence(ClosedContract):
    migration_plan_reviewed: bool = False
    synthetic_rows_only: bool = True
    no_operational_write: bool = True
    repeated_run_idempotent: bool = False
    post_checks_passed: bool = False

    @property
    def accepted(self) -> bool:
        return (self.migration_plan_reviewed and self.synthetic_rows_only
                and self.no_operational_write and self.repeated_run_idempotent
                and self.post_checks_passed)


class RollbackInvariants(ClosedContract):
    owned_legacy_tokens_remain_denied: bool = False
    ownership_rows_are_not_rewritten: bool = False
    audit_history_is_preserved: bool = False
    no_token_expiry_extension: bool = False
    restore_is_verified_before_reopen: bool = False

    @property
    def accepted(self) -> bool:
        return all((self.owned_legacy_tokens_remain_denied,
                    self.ownership_rows_are_not_rewritten,
                    self.audit_history_is_preserved, self.no_token_expiry_extension,
                    self.restore_is_verified_before_reopen))


class MigrationPrerequisites(ClosedContract):
    """Read-only planning state; false/unknown facts block execution."""

    repository_only: bool = True
    operational_database_access: bool = False
    path_policy_verified: bool = False
    expected_schema_version: Literal[PERSISTENCE_SCHEMA_VERSION] = PERSISTENCE_SCHEMA_VERSION
    actual_schema_version: str | None = None
    backup_restore: BackupRestoreEvidence = BackupRestoreEvidence()
    dry_run: DryRunEvidence = DryRunEvidence()
    rollback: RollbackInvariants = RollbackInvariants()
    approved_gates: frozenset[OperationalApprovalGate] = frozenset()

    @property
    def schema_version_matches(self) -> bool:
        return self.actual_schema_version == self.expected_schema_version


class ContractValidation(ClosedContract):
    outcome: ValidationOutcome
    stop_reasons: tuple[StopReason, ...] = Field(default=(), max_length=16)
    details: tuple[str, ...] = Field(default=(), max_length=16)

    @property
    def accepted(self) -> bool:
        return self.outcome is ValidationOutcome.ACCEPTED


def classify_legacy_inquiry(record: SyntheticLegacyInquiry) -> ClassificationEvidence:
    """Classify only explicit, bounded synthetic evidence; ambiguity denies access."""
    record = SyntheticLegacyInquiry.model_validate(record)
    schema = record.schema_evidence
    expected_tables = set(EXPECTED_CORE_TABLES)
    if (schema.version != PERSISTENCE_SCHEMA_VERSION
            or not expected_tables.issubset(schema.tables)
            or tuple(schema.ownership_columns) != EXPECTED_OWNERSHIP_COLUMNS):
        return ClassificationEvidence(
            inquiry_id=record.inquiry_id,
            classification=LegacyInquiryClassification.INCOMPATIBLE_SCHEMA,
            reasons=("schema_version_or_shape_unverified",),
            legacy_access_permitted=False,
        )

    if record.ownership is not None:
        if record.payload_marker is not None:
            return ClassificationEvidence(
                inquiry_id=record.inquiry_id,
                classification=LegacyInquiryClassification.AMBIGUOUS,
                reasons=("owned_row_and_unowned_marker_conflict",),
                legacy_access_permitted=False,
            )
        if record.ownership.customer_id and record.ownership.session_id:
            return ClassificationEvidence(
                inquiry_id=record.inquiry_id,
                classification=LegacyInquiryClassification.OWNED,
                reasons=("immutable_ownership_row_present",),
                legacy_access_permitted=False,
            )
        return ClassificationEvidence(
            inquiry_id=record.inquiry_id,
            classification=LegacyInquiryClassification.MALFORMED,
            reasons=("ownership_row_missing_required_references",),
            legacy_access_permitted=False,
        )

    if record.payload_marker == EXPLICIT_UNOWNED_MARKER:
        return ClassificationEvidence(
            inquiry_id=record.inquiry_id,
            classification=LegacyInquiryClassification.EXPLICITLY_UNOWNED,
            reasons=("explicit_unowned_provenance_marker",),
            legacy_access_permitted=True,
        )
    return ClassificationEvidence(
        inquiry_id=record.inquiry_id,
        classification=LegacyInquiryClassification.AMBIGUOUS,
        reasons=("no_ownership_and_no_explicit_unowned_marker",),
        legacy_access_permitted=False,
    )


def validate_migration_prerequisites(prerequisites: MigrationPrerequisites) -> ContractValidation:
    """Return a deterministic gate decision without inspecting any environment."""
    reasons: list[StopReason] = []
    details: list[str] = []
    if not prerequisites.repository_only or prerequisites.operational_database_access:
        reasons.append(StopReason.OPERATIONAL_ACCESS_REQUIRED)
    if not prerequisites.path_policy_verified:
        reasons.append(StopReason.PATH_POLICY_UNVERIFIED)
    if not prerequisites.schema_version_matches:
        reasons.append(StopReason.SCHEMA_VERSION_UNVERIFIED)
    if not prerequisites.backup_restore.accepted:
        reasons.append(StopReason.BACKUP_UNVERIFIED)
        reasons.append(StopReason.RESTORE_UNVERIFIED)
    if not prerequisites.dry_run.accepted:
        reasons.append(StopReason.DRY_RUN_UNVERIFIED)
    if not prerequisites.rollback.accepted:
        reasons.append(StopReason.ROLLBACK_INVARIANT_UNVERIFIED)
    required = {
        OperationalApprovalGate.TRUSTED_VERIFIER,
        OperationalApprovalGate.DATABASE_INVENTORY,
        OperationalApprovalGate.BACKUP_RESTORE,
        OperationalApprovalGate.MIGRATION_DRY_RUN,
        OperationalApprovalGate.RUNTIME_COMPOSITION,
        OperationalApprovalGate.AUTHENTICATED_QA,
        OperationalApprovalGate.ACTIVATION_ROLLBACK_DRILL,
        OperationalApprovalGate.DEV_INGRESS_ATTESTATION,
    }
    if not required.issubset(prerequisites.approved_gates):
        reasons.append(StopReason.APPROVAL_GATE_MISSING)
    if reasons:
        return ContractValidation(
            outcome=ValidationOutcome.BLOCKED,
            stop_reasons=tuple(dict.fromkeys(reasons)),
            details=tuple(details),
        )
    return ContractValidation(outcome=ValidationOutcome.ACCEPTED)


def validate_classification_set(records: tuple[SyntheticLegacyInquiry, ...]) -> ContractValidation:
    """Require consistent, validated evidence for each inquiry; never resolve conflicts."""
    if not records:
        return ContractValidation(
            outcome=ValidationOutcome.BLOCKED,
            stop_reasons=(StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,),
            details=("classification_set_is_empty",),
        )
    try:
        records = tuple(SyntheticLegacyInquiry.model_validate(record) for record in records)
    except ValidationError:
        return ContractValidation(
            outcome=ValidationOutcome.BLOCKED,
            stop_reasons=(StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,),
            details=("classification_evidence_invalid",),
        )
    observed: dict[str, tuple[SyntheticLegacyInquiry, ClassificationEvidence]] = {}
    conflict = False
    results: list[ClassificationEvidence] = []
    for record in records:
        result = classify_legacy_inquiry(record)
        results.append(result)
        # Compare both the derived decision and the full evidence, including
        # owner/session/version and schema provenance. Identical observations
        # are safe repeats; no record may silently replace another decision.
        previous = observed.setdefault(record.inquiry_id, (record, result))
        if previous != (record, result):
            conflict = True
    results = tuple(results)
    ambiguous = any(result.classification not in {
            LegacyInquiryClassification.OWNED,
            LegacyInquiryClassification.EXPLICITLY_UNOWNED,
    } for result in results)
    if ambiguous or conflict:
        return ContractValidation(
            outcome=ValidationOutcome.BLOCKED,
            stop_reasons=(StopReason.LEGACY_CLASSIFICATION_AMBIGUOUS,),
            # Fixed codes keep failure projections bounded and secret-free,
            # regardless of input size, ordering or caller-supplied references.
            details=(("classification_evidence_ambiguous",) if ambiguous else ())
                    + (("classification_evidence_conflict",) if conflict else ()),
        )
    return ContractValidation(outcome=ValidationOutcome.ACCEPTED)
