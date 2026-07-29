"""Deterministic DPL-03D simulation receipt composition."""

from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)


class SimulationExecutionReceiptBuilder:
    def build(
        self,
        *,
        authorization: Mapping[str, Any],
        plan: Mapping[str, Any],
        actions: Sequence[Mapping[str, Any]],
        started_timestamp: str,
        completed_timestamp: str,
    ) -> dict[str, Any]:
        semantic = {
            "schema_version": "dpl/v1",
            "authorization_id": authorization["authorization_id"],
            "approval_request_id": authorization["request_id"],
            "approval_decision_id": authorization["decision_id"],
            "package_digest": authorization["package_digest"],
            "plan_digest": authorization["plan_digest"],
            "target_identity": authorization["target_identity"],
            "environment": authorization["environment"],
            "action_scope": list(authorization["action_scope"]),
            "actor_identity": authorization["requester_identity"],
            "approver_identity": authorization["approver_identity"],
            "nonce_digest": sha256_digest({"nonce": authorization["nonce"]}),
            "execution_mode": "simulation",
            "executor_type": "fake",
            "result_status": "SIMULATED",
            "simulated_actions": copy.deepcopy(list(actions)),
            "input_evidence_digests": copy.deepcopy(dict(plan["evidence_digests"])),
            "started_timestamp": started_timestamp,
            "completed_timestamp": completed_timestamp,
            "production_authorized": False,
            "production_writes": 0,
            "ubuntu_changes": 0,
            "network_accesses": 0,
            "runtime_commands": 0,
            "executor_invocations": 1,
        }
        receipt = {
            "receipt_id": "sim-" + sha256_digest(semantic)[7:39],
            **semantic,
        }
        receipt["receipt_digest"] = sha256_digest(receipt)
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="SimulationExecutionReceipt",
            payload=receipt,
        )
        return receipt


__all__ = ("SimulationExecutionReceiptBuilder",)
