"""Canonical value-free encoding for authorization-consumption evidence."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from ...ports import AuthorizationConsumptionCommand, AuthorizationConsumptionResult


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def digest_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def digest_canonical(value: object) -> str:
    return digest_text(canonical_json(value))


def binding_document(command: AuthorizationConsumptionCommand) -> dict[str, Any]:
    authorization = command.authorization
    request = authorization.request
    decision = authorization.decision
    receipt = authorization.receipt
    execution = command.execution_request
    budget = command.mutation_budget
    assert decision is not None and receipt is not None
    return {
        "codec_version": 1,
        "schema_versions": {
            "authorization_request": request.schema_version,
            "authorization_decision": decision.schema_version,
            "authorization_receipt": receipt.schema_version,
            "mutation_budget": budget.schema_version,
            "execution_request": execution.schema_version,
        },
        "identifiers": {
            "lifecycle_id": request.lifecycle_id,
            "authorization_id": authorization.authorization_id,
            "mutation_budget_id": budget.budget_id,
            "claim_id": execution.claim_id,
            "execution_request_id": execution.execution_request_id,
            "authorization_request_id": request.request_id,
            "authorization_decision_id": decision.decision_id,
        },
        "states": {"authorization": authorization.state.value, "mutation_budget": budget.status.value},
        "scope": {
            "target": request.target,
            "operation_type": request.operation_type,
            "requested": sorted(request.requested_scope),
            "approved": sorted(receipt.approved_scope),
            "execution_action": execution.action_type,
        },
        "digests": {
            "precondition_snapshot": receipt.precondition_snapshot_digest,
            "plan": execution.plan_digest,
        },
        "timestamps": {
            "requested_at": request.requested_at.isoformat(),
            "decided_at": decision.decided_at.isoformat(),
            "expires_at": receipt.expires_at.isoformat(),
            "issued_at": receipt.issued_at.isoformat(),
            "execution_requested_at": execution.requested_at.isoformat(),
        },
        "line_items": [
            {"action_type": item.action_type, "allowed_count": item.allowed_count}
            for item in budget.line_items
        ],
    }


def encode_binding(command: AuthorizationConsumptionCommand) -> tuple[str, str]:
    encoded = canonical_json(binding_document(command))
    return encoded, digest_text(encoded)


def committed_document(result: AuthorizationConsumptionResult, binding_digest: str) -> dict[str, Any]:
    receipt = result.consumption_receipt
    return {
        "codec_version": 1,
        "consumption_binding_digest": binding_digest,
        "authorization_state": result.authorization.state.value,
        "mutation_budget_state": result.mutation_budget.status.value,
        "line_items": [
            {
                "action_type": item.action_type,
                "allowed_count": item.allowed_count,
                "actual_invocation_count": 0,
                "completed_count": 0,
                "uncertain_count": 0,
                "state": item.status.value,
            }
            for item in result.mutation_budget.line_items
        ],
        "receipt": receipt.to_dict(),
    }


def encode_committed(result: AuthorizationConsumptionResult, binding_digest: str) -> tuple[str, str]:
    encoded = canonical_json(committed_document(result, binding_digest))
    return encoded, digest_text(encoded)


__all__ = (
    "binding_document", "canonical_json", "committed_document", "digest_canonical", "digest_text",
    "encode_binding", "encode_committed",
)
