"""Pure C4 migration contract.

This module describes the v2 -> v3 quarantine backfill.  It deliberately
does not open a database or execute a migration.  A future, separately
authorized migration may use this contract to turn historical
``START_UNKNOWN`` projections into an OPEN START quarantine and one synthetic
C1-backfill ledger event without inventing provider evidence.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field

from core.shopping.customer_identity import ClosedContract


CONTRACT_VERSION = "aicc-c4-migration-contract/v1"
HISTORICAL_PERSISTENCE_SCHEMA_VERSION = "shopping-customer-persistence/v2"
TARGET_PERSISTENCE_SCHEMA_VERSION = "shopping-customer-persistence/v3"
QUARANTINE_TABLE = "shopping_verification_unknown_outcomes"
RECONCILIATION_EVENT_TABLE = "shopping_verification_reconciliation_events"
SYNTHETIC_C1_BACKFILL = "C1_BACKFILL"


class C4MigrationDecision(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"


class C4MigrationBlocker(str, Enum):
    WRONG_SOURCE_SCHEMA = "WRONG_SOURCE_SCHEMA"
    TARGET_SCHEMA_NOT_V3 = "TARGET_SCHEMA_NOT_V3"
    OPERATIONAL_EXECUTION_FORBIDDEN = "OPERATIONAL_EXECUTION_FORBIDDEN"
    HISTORICAL_EVIDENCE_MALFORMED = "HISTORICAL_EVIDENCE_MALFORMED"


class HistoricalUnknownStart(ClosedContract):
    """Bounded row identity for a historical START_UNKNOWN projection."""

    challenge_id: str = Field(strict=True, min_length=1, max_length=128)
    customer_id: str = Field(strict=True, min_length=1, max_length=128)
    provider_source: str = Field(strict=True, min_length=1, max_length=128)
    replay_reference: str = Field(strict=True, min_length=1, max_length=128)
    purpose: str = Field(strict=True, min_length=1, max_length=64)
    challenge_version: int = Field(strict=True, ge=0)
    lifecycle: Literal["START_UNKNOWN"] = "START_UNKNOWN"


class C4BackfillQuarantine(ClosedContract):
    """The only quarantine projection a historical row may produce."""

    challenge_id: str
    state: Literal["OPEN"] = "OPEN"
    operation: Literal["START"] = "START"
    reason_code: Literal["C1_BACKFILL"] = SYNTHETIC_C1_BACKFILL
    provider_verification_id: None = None
    provider_status: Literal["UNKNOWN_OUTCOME"] = "UNKNOWN_OUTCOME"


class C4BackfillEvent(ClosedContract):
    """Append-only synthetic lineage; it carries no provider evidence."""

    challenge_id: str
    operation: Literal["START"] = "START"
    from_lifecycle: Literal["START_UNKNOWN"] = "START_UNKNOWN"
    to_lifecycle: Literal["START_UNKNOWN"] = "START_UNKNOWN"
    outcome: Literal["QUARANTINED"] = "QUARANTINED"
    reason_code: Literal["C1_BACKFILL"] = SYNTHETIC_C1_BACKFILL
    provider_verification_id: None = None
    provider_started_at: None = None
    provider_expires_at: None = None


class C4BackfillItem(ClosedContract):
    challenge_id: str
    quarantine_state: Literal["OPEN"] = "OPEN"
    operation: Literal["START"] = "START"
    reason_code: Literal["C1_BACKFILL"] = SYNTHETIC_C1_BACKFILL
    provider_identifier_inferred: Literal[False] = False
    provider_outcome_inferred: Literal[False] = False
    synthetic_event: Literal[True] = True
    quarantine: C4BackfillQuarantine | None = None
    event: C4BackfillEvent | None = None

    @classmethod
    def from_historical(cls, row: HistoricalUnknownStart) -> "C4BackfillItem":
        return cls(
            challenge_id=row.challenge_id,
            quarantine=C4BackfillQuarantine(challenge_id=row.challenge_id),
            event=C4BackfillEvent(challenge_id=row.challenge_id),
        )


class C4MigrationPlan(ClosedContract):
    source_schema: Literal[HISTORICAL_PERSISTENCE_SCHEMA_VERSION] = HISTORICAL_PERSISTENCE_SCHEMA_VERSION
    target_schema: Literal[TARGET_PERSISTENCE_SCHEMA_VERSION] = TARGET_PERSISTENCE_SCHEMA_VERSION
    execution_authorized: Literal[False] = False
    items: tuple[C4BackfillItem, ...] = ()

    @property
    def count(self) -> int:
        return len(self.items)


class C4MigrationValidation(ClosedContract):
    decision: C4MigrationDecision
    blockers: tuple[C4MigrationBlocker, ...] = ()
    plan: C4MigrationPlan | None = None

    @property
    def ready(self) -> bool:
        return self.decision is C4MigrationDecision.READY


def plan_c4_migration(
    rows: tuple[HistoricalUnknownStart, ...] | list[HistoricalUnknownStart],
    *,
    source_schema: str = HISTORICAL_PERSISTENCE_SCHEMA_VERSION,
    execution_authorized: bool = False,
) -> C4MigrationValidation:
    """Build a non-operational, deterministic v2 -> v3 backfill plan."""
    blockers: list[C4MigrationBlocker] = []
    if source_schema != HISTORICAL_PERSISTENCE_SCHEMA_VERSION:
        blockers.append(C4MigrationBlocker.WRONG_SOURCE_SCHEMA)
    if execution_authorized:
        blockers.append(C4MigrationBlocker.OPERATIONAL_EXECUTION_FORBIDDEN)
    try:
        checked = tuple(HistoricalUnknownStart.model_validate(row) for row in rows)
    except Exception:
        blockers.append(C4MigrationBlocker.HISTORICAL_EVIDENCE_MALFORMED)
        checked = ()
    if blockers:
        return C4MigrationValidation(
            decision=C4MigrationDecision.BLOCKED,
            blockers=tuple(dict.fromkeys(blockers)),
        )
    items = tuple(C4BackfillItem.from_historical(row) for row in checked)
    return C4MigrationValidation(
        decision=C4MigrationDecision.READY,
        plan=C4MigrationPlan(items=items),
    )


# Descriptive spellings used by migration reviewers and tests.
build_c4_migration_plan = plan_c4_migration
MigrationPlan = C4MigrationPlan
MigrationValidation = C4MigrationValidation


__all__ = [
    "CONTRACT_VERSION", "HISTORICAL_PERSISTENCE_SCHEMA_VERSION",
    "TARGET_PERSISTENCE_SCHEMA_VERSION", "QUARANTINE_TABLE",
    "RECONCILIATION_EVENT_TABLE", "SYNTHETIC_C1_BACKFILL",
    "C4MigrationDecision", "C4MigrationBlocker", "HistoricalUnknownStart",
    "C4BackfillQuarantine", "C4BackfillEvent", "C4BackfillItem",
    "C4MigrationPlan", "C4MigrationValidation",
    "plan_c4_migration", "build_c4_migration_plan", "MigrationPlan",
    "MigrationValidation",
]
