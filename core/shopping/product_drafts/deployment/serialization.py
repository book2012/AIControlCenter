"""Detached deterministic preview projection."""
from __future__ import annotations

from typing import Mapping

from ..serialization import to_json_compatible
from .results import ControlledWriteServiceResult


def preview_projection(result: ControlledWriteServiceResult) -> Mapping[str, object]:
    return {
        "schema_version": "1.0.0", "mode": result.mode.value,
        "operation": result.operation, "draft_id": result.draft_id,
        "revision_id": result.revision_id,
        "deployment_intent_id": result.deployment_intent_id,
        "eligibility": result.eligibility,
        "authorization_decision": result.authorization_decision.value,
        "expected_source_digest": result.expected_source_digest,
        "plan_digest": result.plan_digest,
        "idempotency_status": result.idempotency_status,
        "outcome": result.outcome.value, "audit_reference": result.audit_reference,
        "correlation_id": result.correlation_id,
        "completed_at": to_json_compatible(result.completed_at),
        "live_write_performed": False,
    }
