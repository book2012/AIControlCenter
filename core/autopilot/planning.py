"""Pure deterministic roadmap/DAG compiler."""

from __future__ import annotations

from dataclasses import replace

from core.deployment.contracts import sha256_digest

from .manifest import validate_manifest
from .models import (
    AutopilotPolicyError,
    AutonomousDeliveryArchitectureDecision,
    DeliveryPlan,
    DeliveryPlanStep,
    SprintManifest,
)


def compile_roadmap(
    manifests: tuple[SprintManifest, ...],
    *,
    completed_task_ids: frozenset[str] = frozenset(),
) -> DeliveryPlan:
    by_id: dict[str, SprintManifest] = {}
    for manifest in manifests:
        task_id = str(manifest.task_id)
        if task_id in by_id:
            raise AutopilotPolicyError("DUPLICATE_TASK_ID")
        result = validate_manifest(manifest)
        if not result.valid:
            raise AutopilotPolicyError(result.errors[0])
        by_id[task_id] = manifest
    for task_id, manifest in by_id.items():
        for dependency in manifest.dependencies:
            if str(dependency.task_id) not in by_id and str(dependency.task_id) not in completed_task_ids:
                raise AutopilotPolicyError(f"UNKNOWN_DEPENDENCY:{task_id}")
    indegree = {task_id: 0 for task_id in by_id}
    children = {task_id: [] for task_id in by_id}
    for task_id, manifest in by_id.items():
        for dependency in manifest.dependencies:
            dep = str(dependency.task_id)
            if dep in by_id:
                indegree[task_id] += 1
                children[dep].append(task_id)
    ready = sorted(task_id for task_id, count in indegree.items() if count == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(by_id):
        raise AutopilotPolicyError("DEPENDENCY_CYCLE")
    steps = []
    for sequence, task_id in enumerate(order, 1):
        dependencies = tuple(str(item.task_id) for item in by_id[task_id].dependencies)
        blockers = tuple(sorted(dep for dep in dependencies if dep not in completed_task_ids))
        steps.append(DeliveryPlanStep(sequence, SprintTaskId(task_id), bool(blockers), blockers))
    plan = DeliveryPlan(
        steps=tuple(steps),
        decision=AutonomousDeliveryArchitectureDecision.READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE,
    )
    return replace(plan, plan_digest=sha256_digest(plan.payload()))


from .models import SprintTaskId  # kept last to make the planner dependency explicit
