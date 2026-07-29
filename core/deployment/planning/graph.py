"""Pure validation and deterministic ordering for plan action graphs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class PlanGraphError(ValueError):
    """Raised when an action graph is unsafe or inconsistent."""


def stable_topological_order(actions: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for action in actions:
        action_id = action.get("action_id")
        if not isinstance(action_id, str) or not action_id or action_id in by_id:
            raise PlanGraphError("action IDs must be non-empty and unique")
        by_id[action_id] = action

    dependencies: dict[str, set[str]] = {}
    for action_id, action in by_id.items():
        raw = action.get("dependency_ids")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise PlanGraphError("dependency IDs must be an array")
        deps = set(raw)
        if len(deps) != len(raw) or not all(isinstance(item, str) for item in deps):
            raise PlanGraphError("dependency IDs must be unique strings")
        if not deps.issubset(by_id):
            raise PlanGraphError("action graph contains an unknown dependency")
        dependencies[action_id] = deps

    ready = sorted(key for key, deps in dependencies.items() if not deps)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for candidate in sorted(dependencies):
            if current in dependencies[candidate]:
                dependencies[candidate].remove(current)
                if not dependencies[candidate] and candidate not in ordered and candidate not in ready:
                    ready.append(candidate)
                    ready.sort()
    if len(ordered) != len(by_id):
        raise PlanGraphError("action graph contains a cycle")
    return tuple(ordered)


def validate_action_graph(actions: Sequence[Mapping[str, Any]]) -> None:
    order = stable_topological_order(actions)
    positions = {action_id: index for index, action_id in enumerate(order)}
    by_id = {action["action_id"]: action for action in actions}
    supplied = tuple(action["action_id"] for action in actions)
    if supplied != order:
        raise PlanGraphError("actions are not in deterministic topological order")
    for action in actions:
        if tuple(action["dependency_ids"]) != tuple(sorted(action["dependency_ids"])):
            raise PlanGraphError("dependency IDs are not canonically ordered")
        if any(positions[item] >= positions[action["action_id"]] for item in action["dependency_ids"]):
            raise PlanGraphError("prerequisites must precede dependents")
    approval = [item for item in actions if item.get("action_type") == "REQUIRE_APPROVAL"]
    if approval:
        approval_pos = positions[approval[0]["action_id"]]
        validation_types = {
            "VALIDATE_PACKAGE",
            "VERIFY_DEPENDENCY_POLICY",
            "VERIFY_MAC_INVENTORY",
            "VERIFY_INGRESS_READINESS",
            "VERIFY_TARGET_PROFILE",
        }
        if any(
            positions[item["action_id"]] >= approval_pos
            for item in by_id.values()
            if item.get("action_type") in validation_types
        ):
            raise PlanGraphError("approval action must follow validation actions")


__all__ = ("PlanGraphError", "stable_topological_order", "validate_action_graph")
