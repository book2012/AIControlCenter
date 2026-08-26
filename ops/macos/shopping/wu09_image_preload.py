"""Mac-only, exact and non-generic Macro-WU09 image preload adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import platform
import subprocess
from typing import Callable, Protocol
import uuid

from core.governance.control_plane.application.wu09_image_preload_coordinator import (
    WU09_PRELOAD_ACTION_TYPE,
    WU09_PRELOAD_TARGET,
    wu09_preload_plan_digest,
)
from core.governance.control_plane.domain import (
    ExecutionStatus,
    GovernanceAuthorizationRequest,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernanceIdentity,
    GovernancePostconditionReport,
    GovernancePreconditionSnapshot,
    PostconditionDecision,
    PreconditionBinding,
)


DOCKER_CONTEXT = "colima-aicontrolcenter-commerce"
EXACT_IMAGE = "alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1"
PROJECT = "ai-shopping-mariadb-loopback"
SERVICE = "mariadb-loopback-adapter"
HOST_PORT = 58083
NETWORK = "ai-shopping-internal"
DATABASE_CONTAINER = "shopping-db"
TARGET_DATABASE_ENDPOINT = "database:3306"
_PULL_ARGV = ("docker", "--context", DOCKER_CONTEXT, "pull", EXACT_IMAGE)


class ProcessRunner(Protocol):
    def __call__(self, argv: list[str], **kwargs: object) -> object: ...


@dataclass(frozen=True, slots=True)
class WU09PreloadPreconditions:
    platform_system: str
    git_clean: bool
    upstream_aligned: bool
    docker_context: str
    docker_context_reachable: bool
    exact_image_present: bool
    adapter_container_present: bool
    host_port_free: bool
    network_exists: bool
    network_internal: bool
    database_container_running: bool
    database_attached_to_network: bool
    wu09_deployment_active: bool


@dataclass(frozen=True, slots=True)
class WU09PreloadPostconditions:
    docker_context: str
    exact_image: str
    exact_image_present: bool
    adapter_deployed: bool
    unrelated_runtime_mutation_claimed: bool


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validated_precondition_payload(facts: WU09PreloadPreconditions) -> dict[str, object]:
    if not isinstance(facts, WU09PreloadPreconditions):
        raise TypeError("observation must be WU09PreloadPreconditions")
    expected = {
        "platform_system": "Darwin",
        "git_clean": True,
        "upstream_aligned": True,
        "docker_context": DOCKER_CONTEXT,
        "docker_context_reachable": True,
        "exact_image_present": False,
        "adapter_container_present": False,
        "host_port_free": True,
        "network_exists": True,
        "network_internal": True,
        "database_container_running": True,
        "database_attached_to_network": True,
        "wu09_deployment_active": False,
    }
    actual = {name: getattr(facts, name) for name in expected}
    if actual != expected:
        raise ValueError("WU09 preload preconditions are not exactly satisfied")
    return actual


def build_precondition_snapshot(
    request: GovernanceAuthorizationRequest,
    facts: WU09PreloadPreconditions,
    *,
    collected_at: datetime,
) -> GovernancePreconditionSnapshot:
    payload = _validated_precondition_payload(facts)
    digest = _digest(payload)
    mac = GovernanceIdentity("CONTROL_PLANE", "MAC_MINI_M4")
    return GovernancePreconditionSnapshot(
        "1.0", "wu09-preload-" + digest.removeprefix("sha256:")[:16],
        request.lifecycle_id, request.request_id, collected_at, (mac,), mac,
        PreconditionBinding("git_clean_upstream_aligned", "TRUE"),
        PreconditionBinding("docker_context", DOCKER_CONTEXT),
        (PreconditionBinding("control_plane", "DARWIN_MAC_ONLY"),),
        (PreconditionBinding("exact_preload_plan", wu09_preload_plan_digest()),),
        tuple(PreconditionBinding(name, str(value).upper()) for name, value in payload.items()),
        "SEC-02", digest,
    )


class WU09PreloadPreconditionObserver:
    def __init__(
        self,
        observation: Callable[[], WU09PreloadPreconditions],
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._observation = observation
        self._clock = clock

    def observe_preconditions(
        self, request: GovernanceAuthorizationRequest
    ) -> GovernancePreconditionSnapshot:
        return build_precondition_snapshot(
            request, self._observation(), collected_at=self._clock()
        )


class WU09ExactImagePreloadExecution:
    """Expose only the frozen pull; there is no caller-controlled command surface."""

    def __init__(
        self,
        process_runner: ProcessRunner = subprocess.run,
        *,
        platform_system: Callable[[], str] = platform.system,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._process_runner = process_runner
        self._platform_system = platform_system
        self._clock = clock

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        if (
            request.action_type != WU09_PRELOAD_ACTION_TYPE
            or request.target != WU09_PRELOAD_TARGET
            or request.plan_digest != wu09_preload_plan_digest()
        ):
            raise ValueError("execution request is not bound to the exact preload")
        started = self._clock()
        if self._platform_system() != "Darwin":
            return self._receipt(request, ExecutionStatus.FAILED, started, "DARWIN_REQUIRED")
        try:
            completed = self._process_runner(
                list(_PULL_ARGV), shell=False, check=False, capture_output=True, text=False
            )
            returncode = getattr(completed, "returncode", None)
            if type(returncode) is not int:
                return self._receipt(
                    request, ExecutionStatus.UNCERTAIN, started,
                    "PROCESS_COMPLETION_AMBIGUOUS",
                )
            status = ExecutionStatus.COMPLETED if returncode == 0 else ExecutionStatus.FAILED
            reason = "EXACT_IMAGE_PULL_COMPLETED" if returncode == 0 else "EXACT_IMAGE_PULL_FAILED"
            return self._receipt(request, status, started, reason)
        except Exception:
            return self._receipt(
                request, ExecutionStatus.UNCERTAIN, started, "PROCESS_COMPLETION_UNCERTAIN"
            )

    def _receipt(
        self,
        request: GovernanceExecutionRequest,
        status: ExecutionStatus,
        started: datetime,
        reason: str,
    ) -> GovernanceExecutionReceipt:
        completed = self._clock()
        result_digest = _digest({"action": WU09_PRELOAD_ACTION_TYPE, "status": status.value})
        return GovernanceExecutionReceipt(
            "1.0", "wu09-preload-" + uuid.uuid4().hex, request.lifecycle_id,
            request.execution_request_id, request.authorization_id, request.claim_id,
            request.mutation_budget_id, request.action_type, status, 1,
            int(status is ExecutionStatus.COMPLETED),
            int(status is ExecutionStatus.UNCERTAIN), started, completed,
            result_digest, (reason,),
        )


class WU09PreloadPostconditionValidator:
    def __init__(
        self,
        observation: Callable[[], WU09PreloadPostconditions],
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._observation = observation
        self._clock = clock

    def validate_postconditions(
        self, receipt: GovernanceExecutionReceipt
    ) -> GovernancePostconditionReport:
        facts = self._observation()
        if not isinstance(facts, WU09PreloadPostconditions):
            raise TypeError("observation must be WU09PreloadPostconditions")
        passed = (
            facts.docker_context == DOCKER_CONTEXT
            and facts.exact_image == EXACT_IMAGE
            and facts.exact_image_present is True
            and facts.adapter_deployed is False
            and facts.unrelated_runtime_mutation_claimed is False
        )
        expected = {
            "docker_context": DOCKER_CONTEXT,
            "exact_image": EXACT_IMAGE,
            "exact_image_present": True,
            "adapter_deployed": False,
            "unrelated_runtime_mutation_claimed": False,
        }
        observed = {
            "docker_context": facts.docker_context,
            "exact_image": facts.exact_image,
            "exact_image_present": facts.exact_image_present,
            "adapter_deployed": facts.adapter_deployed,
            "unrelated_runtime_mutation_claimed": facts.unrelated_runtime_mutation_claimed,
        }
        decision = PostconditionDecision.PASS if passed else PostconditionDecision.FAIL
        expected_reference = json.dumps(expected, sort_keys=True, separators=(",", ":"))
        observed_reference = json.dumps(observed, sort_keys=True, separators=(",", ":"))
        digest = _digest({
            "decision": decision.value,
            "expected": expected,
            "observed": observed,
        })
        return GovernancePostconditionReport(
            "1.0", "wu09-postcondition-" + digest.removeprefix("sha256:")[:16],
            receipt.lifecycle_id, receipt.receipt_id, "MAC_WU09_PRELOAD_VALIDATOR",
            decision,
            ("EXACT_IMAGE_PRESENT_ADAPTER_UNDEPLOYED" if passed else "POSTCONDITION_NOT_PROVEN",),
            expected_reference, observed_reference, digest, self._clock(),
        )


__all__ = (
    "DATABASE_CONTAINER", "DOCKER_CONTEXT", "EXACT_IMAGE", "HOST_PORT", "NETWORK",
    "PROJECT", "SERVICE", "TARGET_DATABASE_ENDPOINT", "WU09ExactImagePreloadExecution",
    "WU09PreloadPostconditionValidator", "WU09PreloadPostconditions",
    "WU09PreloadPreconditionObserver", "WU09PreloadPreconditions",
    "build_precondition_snapshot",
)
