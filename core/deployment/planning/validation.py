"""Contract, digest, and graph validation for DPL-03B plans."""

from __future__ import annotations

import copy
import hmac
from collections.abc import Mapping
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)

from .graph import PlanGraphError, validate_action_graph


def _semantic_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    semantic = copy.deepcopy(dict(plan))
    semantic.pop("plan_digest", None)
    return semantic


def validate_deployment_plan(plan: Mapping[str, Any]) -> None:
    registry = load_schema_registry()
    validate_contract_payload(registry=registry, contract_name="DeploymentPlan", payload=plan)
    expected = sha256_digest(_semantic_plan(plan))
    if not hmac.compare_digest(expected, str(plan.get("plan_digest", ""))):
        raise ValueError("deployment plan digest mismatch")
    validate_action_graph(plan["actions"])
    expected_edges = sorted(
        (
            {"from_action_id": dependency, "to_action_id": action["action_id"]}
            for action in plan["actions"]
            for dependency in action["dependency_ids"]
        ),
        key=lambda item: (item["from_action_id"], item["to_action_id"]),
    )
    if list(plan["dependency_edges"]) != expected_edges:
        raise PlanGraphError("dependency edges do not match action dependencies")
    if plan["overall_status"] == "READY_FOR_APPROVAL":
        if any(item["action_type"] == "RECORD_BLOCKER" for item in plan["actions"]):
            raise PlanGraphError("blocker action prevents approval readiness")
        if any(item["risk"] == "CRITICAL" for item in plan["actions"]):
            raise PlanGraphError("critical risk prevents approval readiness")


def validate_deployment_plan_report(report: Mapping[str, Any]) -> None:
    registry = load_schema_registry()
    validate_contract_payload(
        registry=registry, contract_name="DeploymentPlanReport", payload=report
    )
    validate_deployment_plan(report["plan"])


__all__ = (
    "validate_deployment_plan",
    "validate_deployment_plan_report",
)
