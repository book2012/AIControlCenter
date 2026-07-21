from core.governance.operations.application.identity import (
    event_id_for,
    run_id_for,
)
from core.governance.operations.domain.events import (
    EventType,
    Operation,
)

from .application_helpers import utc


def test_run_identity_is_stable():
    first = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
        1,
    )
    second = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
        1,
    )

    assert first == second


def test_run_identity_separates_operation_and_attempt():
    audit = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
        1,
    )
    backup = run_id_for(
        Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
        utc(1),
        1,
    )
    second_attempt = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
        2,
    )

    assert audit != backup
    assert audit != second_attempt


def test_event_identity_is_stable_and_type_specific():
    run_id = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2),
        1,
    )

    scheduled_first = event_id_for(
        run_id,
        EventType.RUN_SCHEDULED,
    )
    scheduled_second = event_id_for(
        run_id,
        EventType.RUN_SCHEDULED,
    )
    started = event_id_for(
        run_id,
        EventType.RUN_STARTED,
    )

    assert scheduled_first == scheduled_second
    assert scheduled_first != started
