"""Pure C4 migration planning: no operational execution or invented evidence."""
import pytest
from pydantic import ValidationError

from core.shopping.c4_migration_contract import (
    C4MigrationBlocker, C4MigrationDecision, HISTORICAL_PERSISTENCE_SCHEMA_VERSION,
    HistoricalUnknownStart, SYNTHETIC_C1_BACKFILL, TARGET_PERSISTENCE_SCHEMA_VERSION,
    plan_c4_migration,
)


def historical(**updates):
    payload = dict(
        challenge_id="challenge-1", customer_id="customer-1",
        provider_source="synthetic.mock", replay_reference="replay-1",
        purpose="SESSION_ISSUANCE", challenge_version=1,
    )
    payload.update(updates)
    return HistoricalUnknownStart(**payload)


def test_c4_plan_projects_open_start_quarantine_and_synthetic_event():
    validation = plan_c4_migration((historical(),))
    assert validation.decision is C4MigrationDecision.READY
    assert validation.plan.source_schema == HISTORICAL_PERSISTENCE_SCHEMA_VERSION
    assert validation.plan.target_schema == TARGET_PERSISTENCE_SCHEMA_VERSION
    item = validation.plan.items[0]
    assert item.quarantine.state == "OPEN"
    assert item.quarantine.operation == "START"
    assert item.quarantine.reason_code == SYNTHETIC_C1_BACKFILL
    assert item.event.from_lifecycle == "START_UNKNOWN"
    assert item.event.to_lifecycle == "START_UNKNOWN"
    assert item.event.outcome == "QUARANTINED"
    assert item.provider_identifier_inferred is False
    assert item.provider_outcome_inferred is False
    assert item.quarantine.provider_verification_id is None
    assert item.event.provider_started_at is None
    assert item.event.provider_expires_at is None


@pytest.mark.parametrize("source", ["shopping-customer-persistence/v1", "future/v9"])
def test_c4_plan_requires_the_separate_v2_source_contract(source):
    result = plan_c4_migration((historical(),), source_schema=source)
    assert result.decision is C4MigrationDecision.BLOCKED
    assert C4MigrationBlocker.WRONG_SOURCE_SCHEMA in result.blockers
    assert result.plan is None


def test_c4_plan_never_authorizes_operational_migration():
    result = plan_c4_migration((historical(),), execution_authorized=True)
    assert result.decision is C4MigrationDecision.BLOCKED
    assert C4MigrationBlocker.OPERATIONAL_EXECUTION_FORBIDDEN in result.blockers
    assert result.plan is None


def test_malformed_historical_evidence_is_blocked_without_projection():
    result = plan_c4_migration(({"challenge_id": "secret"},))
    assert result.decision is C4MigrationDecision.BLOCKED
    assert C4MigrationBlocker.HISTORICAL_EVIDENCE_MALFORMED in result.blockers
    assert result.plan is None
    with pytest.raises(ValidationError):
        HistoricalUnknownStart(challenge_id="secret")
