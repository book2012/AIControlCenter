"""Deterministic governance operation identities."""

from __future__ import annotations

from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from ..domain.events import (
    EventType,
    Operation,
    require_utc,
)

RUN_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aicontrolcenter/governance-audit-operations/runs",
)
EVENT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aicontrolcenter/governance-audit-operations/events",
)


def run_id_for(
    operation: Operation,
    scheduled_for: datetime,
    attempt: int,
) -> UUID:
    if not isinstance(operation, Operation):
        raise TypeError(
            "operation must be Operation"
        )

    if attempt < 1:
        raise ValueError(
            "attempt must be at least one"
        )

    normalized = require_utc(
        scheduled_for,
        "scheduled_for",
    )

    key = (
        f"{operation.value}|"
        f"{normalized.isoformat()}|"
        f"attempt:{attempt}"
    )

    return uuid5(RUN_NAMESPACE, key)


def event_id_for(
    run_id: UUID,
    event_type: EventType,
) -> UUID:
    if not isinstance(run_id, UUID):
        raise TypeError("run_id must be UUID")

    if not isinstance(event_type, EventType):
        raise TypeError(
            "event_type must be EventType"
        )

    return uuid5(
        EVENT_NAMESPACE,
        f"{run_id}|{event_type.value}",
    )
