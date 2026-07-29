"""Default-deny, non-production fake apply composition for DPL-03D."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.planning import stable_topological_order, validate_deployment_plan

from .ports import ReplayGuard, SimulationExecutor, SimulationIntent
from .receipt import SimulationExecutionReceiptBuilder
from .validation import SimulationValidationResult

_FORBIDDEN = {
    "argv", "command", "credential", "password", "private_key", "script",
    "secret", "shell", "token",
}
_NON_PRODUCTION = {"development", "test", "staging", "sandbox"}


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an offset")
    return parsed.astimezone(timezone.utc)


def _security_check(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("unsafe simulation input")
            normalized = key.lower()
            if normalized in _FORBIDDEN or any(
                marker in normalized
                for marker in ("credential", "_password", "_secret", "_token")
            ):
                raise ValueError("unsafe simulation input")
            _security_check(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _security_check(child)
    elif isinstance(value, str):
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("unsafe simulation input")


class SimulationApplyService:
    def __init__(
        self,
        *,
        replay_guard: ReplayGuard | None,
        executor: SimulationExecutor | None,
        receipt_builder: SimulationExecutionReceiptBuilder | None = None,
    ) -> None:
        self._replay_guard = replay_guard
        self._executor = executor
        self._receipt_builder = receipt_builder or SimulationExecutionReceiptBuilder()

    def apply(
        self,
        *,
        authorization: Mapping[str, Any],
        plan: Mapping[str, Any],
        package_digest: str,
        target_identity: str,
        environment: str,
        action_scope: Sequence[str],
        started_timestamp: str,
        completed_timestamp: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        authorization_copy = copy.deepcopy(dict(authorization))
        plan_copy = copy.deepcopy(dict(plan))
        reasons: list[str] = []
        status = "DENIED"
        try:
            _security_check(
                {
                    "authorization": authorization_copy, "plan": plan_copy,
                    "package_digest": package_digest, "target_identity": target_identity,
                    "environment": environment, "action_scope": list(action_scope),
                    "started_timestamp": started_timestamp,
                    "completed_timestamp": completed_timestamp,
                }
            )
            validate_contract_payload(
                registry=load_schema_registry(),
                contract_name="ExecutionAuthorization",
                payload=authorization_copy,
            )
            validate_deployment_plan(plan_copy)
            started = _timestamp(started_timestamp)
            completed = _timestamp(completed_timestamp)
            expiry = _timestamp(authorization_copy["expiry_timestamp"])
        except Exception:
            reasons.append("INVALID_INPUT")
            status = "INVALID"
            started = completed = expiry = None

        if not reasons:
            bindings = (
                ("PACKAGE_DIGEST_MISMATCH", authorization_copy["package_digest"], package_digest),
                ("PACKAGE_DIGEST_MISMATCH", authorization_copy["package_digest"], plan_copy["package_digest"]),
                ("PLAN_DIGEST_MISMATCH", authorization_copy["plan_digest"], plan_copy["plan_digest"]),
                ("TARGET_IDENTITY_MISMATCH", authorization_copy["target_identity"], target_identity),
                ("TARGET_IDENTITY_MISMATCH", authorization_copy["target_identity"], plan_copy["target_identity"]),
                ("ENVIRONMENT_MISMATCH", authorization_copy["environment"], environment),
                ("ACTION_SCOPE_MISMATCH", authorization_copy["action_scope"], list(action_scope)),
            )
            reasons.extend(code for code, left, right in bindings if left != right)
            if not authorization_copy["execution_authorized"]:
                reasons.append("AUTHORIZATION_NOT_AUTHORIZED")
            if authorization_copy["production_authorized"]:
                reasons.append("PRODUCTION_AUTHORIZATION_PROHIBITED")
            if environment not in _NON_PRODUCTION:
                reasons.append("PRODUCTION_ENVIRONMENT_PROHIBITED")
            if authorization_copy["maximum_uses"] != 1:
                reasons.append("MAXIMUM_USES_NOT_ONE")
            if plan_copy["overall_status"] != "READY_FOR_APPROVAL":
                reasons.append("PLAN_NOT_READY_FOR_APPROVAL")
            if plan_copy["risk_level"] == "CRITICAL" or any(
                action["risk"] == "CRITICAL" for action in plan_copy["actions"]
            ):
                reasons.append("PLAN_CONTAINS_CRITICAL_RISK")
            if started is not None and completed is not None and completed < started:
                reasons.append("TIMESTAMP_ORDER_INVALID")
            if expiry is not None and started is not None and expiry <= started:
                reasons.append("AUTHORIZATION_EXPIRED")
                status = "EXPIRED"
            if self._replay_guard is None:
                reasons.append("REPLAY_GUARD_UNAVAILABLE")
            if self._executor is None:
                reasons.append("FAKE_EXECUTOR_UNAVAILABLE")
            elif getattr(self._executor, "executor_type", None) != "fake":
                reasons.append("EXECUTOR_TYPE_INVALID")
            available = {item["action_id"]: item for item in plan_copy["actions"]}
            if set(action_scope) - set(available):
                reasons.append("ACTION_SCOPE_MISMATCH")
        consumed = False
        if not reasons:
            consumed = bool(
                self._replay_guard.consume(
                    authorization_copy["authorization_id"], authorization_copy["nonce"]
                )
            )
            if not consumed:
                reasons.append("AUTHORIZATION_REPLAYED")
                status = "REPLAYED"

        receipt = None
        if not reasons:
            selected = {
                item["action_id"]: {
                    **item,
                    "dependency_ids": [
                        dependency for dependency in item["dependency_ids"]
                        if dependency in set(action_scope)
                    ],
                }
                for item in plan_copy["actions"]
                if item["action_id"] in set(action_scope)
            }
            ordered_ids = stable_topological_order(tuple(selected.values()))
            intents = tuple(
                SimulationIntent(
                    action_id=item["action_id"],
                    action_type=item["action_type"],
                    target=item["target"],
                    dependency_ids=tuple(
                        dep for dep in item["dependency_ids"] if dep in selected
                    ),
                    result_expectation=item["result_expectation"],
                )
                for item in (selected[action_id] for action_id in ordered_ids)
            )
            try:
                results = self._executor.execute(intents)
                if len(results) != len(intents) or len({
                    item.get("action_id") for item in results
                }) != len(results):
                    raise ValueError("invalid fake result")
                if stable_topological_order(results) != tuple(
                    item["action_id"] for item in results
                ):
                    raise ValueError("invalid fake result graph")
                receipt = self._receipt_builder.build(
                    authorization=authorization_copy,
                    plan=plan_copy,
                    actions=results,
                    started_timestamp=started_timestamp,
                    completed_timestamp=completed_timestamp,
                )
                status = "SIMULATED"
            except Exception:
                reasons.append("FAKE_EXECUTION_FAILED")
                status = "FAILED"

        result = SimulationValidationResult(status, tuple(sorted(set(reasons))))
        report = {
            "schema_version": "dpl/v1",
            "status": result.status,
            "reason_codes": list(result.reason_codes),
            "authorization_id": authorization_copy.get("authorization_id"),
            "receipt_id": receipt["receipt_id"] if receipt else None,
            "receipt_digest": receipt["receipt_digest"] if receipt else None,
            "execution_mode": "simulation",
            "executor_type": "fake",
            "nonce_consumed": consumed,
            "production_authorized": False,
            "production_writes": 0,
            "ubuntu_changes": 0,
            "network_accesses": 0,
            "runtime_commands": 0,
            "executor_invocations": 1 if consumed and status in {"SIMULATED", "FAILED"} else 0,
        }
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="SimulationExecutionReport",
            payload=report,
        )
        return receipt, report


__all__ = ("SimulationApplyService",)
