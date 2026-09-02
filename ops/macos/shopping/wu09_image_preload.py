"""Mac-only, exact and non-generic Macro-WU09 image preload adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import socket
import subprocess
from typing import Callable, Protocol, Sequence
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
class ReadOnlyCommandResult:
    returncode: int
    stdout: str


class ReadOnlyProcessRunner(Protocol):
    def __call__(self, argv: Sequence[str], *, cwd: Path | None = None) -> ReadOnlyCommandResult: ...


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


def _run_read_only(argv: Sequence[str], *, cwd: Path | None = None) -> ReadOnlyCommandResult:
    completed = subprocess.run(
        list(argv), cwd=cwd, shell=False, check=False, capture_output=True,
        text=True, timeout=10,
    )
    return ReadOnlyCommandResult(completed.returncode, completed.stdout)


def _host_port_available() -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        probe.bind(("127.0.0.1", HOST_PORT))
        return True
    except OSError:
        return False
    finally:
        probe.close()


class WU09ProductionReadOnlyObservation:
    """Collect only the fixed WU09 facts using bounded, read-only probes."""

    __slots__ = ("_repository_root", "_runner", "_platform_system", "_port_available")

    def __init__(
        self,
        repository_root: Path,
        *,
        _runner: ReadOnlyProcessRunner = _run_read_only,
        _platform_system: Callable[[], str] = platform.system,
        _port_available: Callable[[], bool] = _host_port_available,
    ) -> None:
        root = Path(repository_root)
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("repository_root must be absolute without traversal")
        self._repository_root = root.resolve()
        self._runner = _runner
        self._platform_system = _platform_system
        self._port_available = _port_available

    def _output(self, argv: tuple[str, ...], *, cwd: Path | None = None) -> str:
        result = self._runner(argv, cwd=cwd)
        if type(result) is not ReadOnlyCommandResult or result.returncode != 0:
            raise RuntimeError("WU09 read-only observation failed")
        if not isinstance(result.stdout, str) or len(result.stdout) > 1_000_000:
            raise RuntimeError("WU09 read-only observation output is invalid")
        return result.stdout

    @staticmethod
    def _json_rows(value: str) -> list[dict[str, object]]:
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise RuntimeError("WU09 observation JSON is malformed") from exc
        rows = parsed if isinstance(parsed, list) else [parsed]
        if len(rows) > 128 or any(type(row) is not dict for row in rows):
            raise RuntimeError("WU09 observation JSON is ambiguous")
        return rows

    def _runtime(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        context = self._json_rows(self._output(("docker", "context", "inspect", DOCKER_CONTEXT)))
        if len(context) != 1 or context[0].get("Name") != DOCKER_CONTEXT:
            raise RuntimeError("fixed Docker context is not exact")
        images = tuple(filter(None, self._output((
            "docker", "--context", DOCKER_CONTEXT, "image", "ls", "--quiet",
            "--no-trunc", EXACT_IMAGE,
        )).splitlines()))
        if len(images) > 1 or any(not item.startswith("sha256:") for item in images):
            raise RuntimeError("exact image observation is ambiguous")
        containers = self._json_rows(self._output((
            "docker", "--context", DOCKER_CONTEXT, "container", "ls", "--all",
            "--filter", f"name=^/{SERVICE}$", "--format", "json",
        )))
        if len(containers) > 1:
            raise RuntimeError("adapter container observation is ambiguous")
        networks = self._json_rows(self._output((
            "docker", "--context", DOCKER_CONTEXT, "network", "inspect", NETWORK,
        )))
        if len(networks) != 1 or networks[0].get("Name") != NETWORK:
            raise RuntimeError("required network observation is ambiguous")
        internal = networks[0].get("Internal")
        if type(internal) is not bool:
            raise RuntimeError("required network internal state is malformed")
        databases = self._json_rows(self._output((
            "docker", "--context", DOCKER_CONTEXT, "container", "inspect", DATABASE_CONTAINER,
        )))
        if len(databases) != 1:
            raise RuntimeError("database container observation is ambiguous")
        database = databases[0]
        state, settings = database.get("State"), database.get("NetworkSettings")
        if type(state) is not dict or type(settings) is not dict:
            raise RuntimeError("database container observation is malformed")
        running = state.get("Running")
        attached = settings.get("Networks")
        if type(running) is not bool or type(attached) is not dict:
            raise RuntimeError("database runtime state is malformed")
        return True, bool(images), bool(containers), internal, running, NETWORK in attached

    def observe_preload_preconditions(self) -> WU09PreloadPreconditions:
        clean = self._output(("git", "status", "--porcelain=v1"), cwd=self._repository_root)
        alignment = self._output(
            ("git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"),
            cwd=self._repository_root,
        )
        reachable, image, adapter, internal, database, attached = self._runtime()
        port_free = self._port_available()
        if type(port_free) is not bool:
            raise RuntimeError("host-port observation is malformed")
        return WU09PreloadPreconditions(
            self._platform_system(), clean == "", alignment.strip() == "0\t0",
            DOCKER_CONTEXT, reachable, image, adapter, port_free, True, internal,
            database, attached, adapter,
        )

    def observe_preload_postconditions(self) -> WU09PreloadPostconditions:
        _, image, adapter, internal, database, attached = self._runtime()
        port_free = self._port_available()
        if type(port_free) is not bool:
            raise RuntimeError("host-port observation is malformed")
        unrelated = adapter or not internal or not database or not attached or not port_free
        return WU09PreloadPostconditions(
            DOCKER_CONTEXT, EXACT_IMAGE, image, adapter, unrelated
        )


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
    mac = GovernanceIdentity(
        identity_id="MAC_MINI_M4", identity_type="CONTROL_PLANE"
    )
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


def validate_expected_precondition_snapshot(
    request: GovernanceAuthorizationRequest,
    snapshot: GovernancePreconditionSnapshot,
) -> None:
    """Admit the complete frozen WU09 snapshot; its digest field is not trusted alone."""
    if type(snapshot) is not GovernancePreconditionSnapshot:
        raise TypeError("expected snapshot must be exactly GovernancePreconditionSnapshot")
    payload = {
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
    digest = _digest(payload)
    mac = GovernanceIdentity("MAC_MINI_M4", "CONTROL_PLANE")
    expected = (
        snapshot.schema_version == "1.0",
        snapshot.snapshot_id == "wu09-preload-" + digest.removeprefix("sha256:")[:16],
        snapshot.lifecycle_id == request.lifecycle_id,
        snapshot.request_id == request.request_id,
        snapshot.collector_identities == (mac,),
        snapshot.target_identity == mac,
        snapshot.git_state_binding == PreconditionBinding("git_clean_upstream_aligned", "TRUE"),
        snapshot.runtime_identity_binding == PreconditionBinding("docker_context", DOCKER_CONTEXT),
        snapshot.security_state_bindings == (PreconditionBinding("control_plane", "DARWIN_MAC_ONLY"),),
        snapshot.manifest_bindings == (PreconditionBinding("exact_preload_plan", wu09_preload_plan_digest()),),
        snapshot.operational_state_bindings == tuple(sorted(
            (PreconditionBinding(name, str(value).upper()) for name, value in payload.items()),
            key=lambda item: item.name,
        )),
        snapshot.policy_version == "SEC-02",
        snapshot.snapshot_digest == digest,
    )
    if not all(expected):
        raise ValueError("expected WU09 precondition snapshot is not exact and complete")


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
    "WU09ProductionReadOnlyObservation", "ReadOnlyCommandResult",
    "build_precondition_snapshot", "validate_expected_precondition_snapshot",
)
