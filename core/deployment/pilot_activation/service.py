"""Fail-closed M2-P2 controlled sandbox activation orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from core.deployment.executor_contracts import (
    ExecutorOperation, create_executor_request,
)
from core.deployment.executor_ports import NonProductionExecutorPort
from core.deployment.m2_readiness import M2ReadinessDecision, M2ReadinessReport
from core.deployment.pilot_authorization import PilotPermit

from .models import (
    PilotActivationDecision, PilotActivationEvidence, PilotActivationReceipt,
    PilotActivationRequest, PilotActivationStatus, PilotActivationStep,
    PilotActivationValidationReport, sha256_digest,
)

OPERATIONS = (
    ExecutorOperation.VERIFY_SANDBOX_TARGET.value,
    ExecutorOperation.PREPARE_SANDBOX.value,
    ExecutorOperation.COLLECT_EXECUTION_EVIDENCE.value,
)
ALLOWED_ENVIRONMENTS = frozenset({"development", "test", "staging"})


class PilotPermitUseRegistry(Protocol):
    def reserve(self, permit_id: str, activation_id: str) -> bool: ...
    def is_consumed(self, permit_id: str) -> bool: ...


class InMemoryPilotPermitUseRegistry:
    """Process-local test registry; not durable enough for mutable deployment."""

    def __init__(self) -> None:
        self._uses: dict[str, str] = {}

    def reserve(self, permit_id: str, activation_id: str) -> bool:
        if permit_id in self._uses:
            return False
        self._uses[permit_id] = activation_id
        return True

    def is_consumed(self, permit_id: str) -> bool:
        return permit_id in self._uses


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid timestamp")
    return parsed.astimezone(timezone.utc)


def _permit_digest(permit: PilotPermit) -> str:
    value = permit.to_dict()
    digest = value.pop("permit_digest")
    return sha256_digest(value) if digest else ""


class PilotActivationService:
    def __init__(
        self, *, executor: NonProductionExecutorPort | None,
        capability: Mapping[str, Any] | None,
        registry: PilotPermitUseRegistry | None,
    ) -> None:
        self._executor = executor
        self._capability = dict(capability) if capability is not None else None
        self._registry = registry

    def activate(
        self, *, request: PilotActivationRequest | None,
        readiness_report: M2ReadinessReport | None,
        execution_authorization: Mapping[str, Any] | None,
    ) -> PilotActivationDecision:
        if request is None:
            return self._decision(None, PilotActivationStatus.BLOCKED, ("MISSING_REQUEST",), False)
        if self._registry is None:
            return self._decision(request, PilotActivationStatus.BLOCKED, ("MISSING_PERMIT_USE_REGISTRY",), False)
        if self._executor is None or self._capability is None:
            return self._decision(request, PilotActivationStatus.BLOCKED, ("MISSING_ADAPTER",), False)

        reasons = self._validate(request, readiness_report, execution_authorization)
        if reasons:
            return self._decision(request, PilotActivationStatus.DENIED, reasons, False)
        if not self._registry.reserve(request.permit_id, request.activation_id):
            return self._decision(request, PilotActivationStatus.REPLAYED, ("PERMIT_ALREADY_CONSUMED",), True)

        assert execution_authorization is not None
        steps: list[PilotActivationStep] = []
        for sequence, operation in enumerate(OPERATIONS, 1):
            try:
                executor_request = create_executor_request(
                    authorization=execution_authorization,
                    capability=self._capability,
                    operation_scope=(operation,),
                    actor_identity=request.requester_identity,
                    nonce_reference="pilot-permit-" + request.permit_id,
                    request_timestamp=request.activation_timestamp,
                )
                result = dict(self._executor.execute(
                    executor_request, result_timestamp=request.activation_timestamp
                ))
                failure = self._result_reasons(
                    result, executor_request, self._capability, operation
                )
            except Exception:
                return self._decision(
                    request, PilotActivationStatus.FAILED,
                    ("MALFORMED_ADAPTER_RESULT",), True, tuple(steps),
                )
            if "result_digest" not in result:
                return self._decision(
                    request, PilotActivationStatus.FAILED,
                    ("MALFORMED_ADAPTER_RESULT",), True, tuple(steps),
                )
            step = PilotActivationStep(
                sequence=sequence, operation=operation,
                request_id=executor_request["request_id"],
                capability_id=self._capability["capability_id"],
                result_digest=result["result_digest"], status=result["status"],
                evidence_digests=tuple(sorted(result["evidence_digests"])),
            )
            steps.append(step)
            if failure:
                return self._decision(
                    request, PilotActivationStatus.FAILED, failure, True, tuple(steps)
                )
        return self._decision(
            request, PilotActivationStatus.ACTIVATED, (), True, tuple(steps)
        )

    @staticmethod
    def _validate(
        request: PilotActivationRequest,
        readiness: M2ReadinessReport | None,
        authorization: Mapping[str, Any] | None,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        permit = request.permit
        if request.permit_id != permit.permit_id:
            reasons.append("PERMIT_ID_MISMATCH")
        if request.permit_digest != permit.permit_digest or _permit_digest(permit) != permit.permit_digest:
            reasons.append("PERMIT_DIGEST_MISMATCH")
        try:
            if _timestamp(request.activation_timestamp) >= _timestamp(permit.expires_at):
                reasons.append("PERMIT_EXPIRED")
            if _timestamp(request.activation_timestamp) < _timestamp(permit.issued_at):
                reasons.append("PERMIT_NOT_YET_VALID")
        except Exception:
            reasons.append("MALFORMED_TIMESTAMP")
        if permit.max_uses != 1:
            reasons.append("PERMIT_USE_LIMIT_INVALID")
        if permit.pilot_activation_started:
            reasons.append("PERMIT_ACTIVATION_FLAG_INVALID")
        bindings = (
            ("EXECUTION_AUTHORIZATION_MISMATCH", request.execution_authorization_id, permit.execution_authorization_id),
            ("READINESS_REPORT_ID_MISMATCH", request.readiness_report_id, permit.readiness_report_id),
            ("READINESS_REPORT_DIGEST_MISMATCH", request.readiness_report_digest, permit.readiness_report_digest),
            ("PACKAGE_DIGEST_MISMATCH", request.package_digest, permit.package_digest),
            ("PLAN_DIGEST_MISMATCH", request.plan_digest, permit.plan_digest),
            ("TARGET_IDENTITY_MISMATCH", request.target_identity, permit.target_identity),
            ("TARGET_OWNER_MISMATCH", request.target_owner, permit.target_owner),
            ("ENVIRONMENT_MISMATCH", request.environment, permit.environment),
            ("SANDBOX_ROOT_IDENTITY_MISMATCH", request.sandbox_root_identity_digest, permit.sandbox_root_identity_digest),
            ("REQUESTER_IDENTITY_MISMATCH", request.requester_identity, permit.requester_identity),
            ("OPERATOR_IDENTITY_MISMATCH", request.operator_identity, permit.operator_identity),
            ("APPROVER_IDENTITY_MISMATCH", request.approver_identity, permit.approver_identity),
        )
        reasons.extend(code for code, left, right in bindings if left != right)
        if set(request.operation_scope) - set(permit.operation_scope) or tuple(request.operation_scope) != tuple(sorted(OPERATIONS)):
            reasons.append("OPERATION_SCOPE_MISMATCH")
        if request.target_owner != "mac-control-plane" or "ubuntu" in request.target_identity.lower():
            reasons.append("TARGET_DENIED")
        if request.environment not in ALLOWED_ENVIRONMENTS:
            reasons.append("ENVIRONMENT_DENIED")
        if request.production_authorized or permit.production_authorized:
            reasons.append("PRODUCTION_AUTHORIZATION_DENIED")
        if request.persistent_audit_operational:
            reasons.append("PERSISTENT_AUDIT_CLAIM_DENIED")
        if any(not isinstance(value, int) or isinstance(value, bool) or value != 0 for value in request.safety_counters.values()):
            reasons.append("NONZERO_SAFETY_COUNTER")
        if readiness is None:
            reasons.append("MISSING_READINESS_EVIDENCE")
        elif (
            readiness.decision is not M2ReadinessDecision.READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX
            or readiness.report_id != request.readiness_report_id
            or readiness.report_digest != request.readiness_report_digest
        ):
            reasons.append("READINESS_EVIDENCE_CHANGED")
        if authorization is None:
            reasons.append("MISSING_EXECUTION_AUTHORIZATION")
        else:
            for key, expected in (
                ("authorization_id", request.execution_authorization_id),
                ("package_digest", request.package_digest), ("plan_digest", request.plan_digest),
                ("target_identity", request.target_identity), ("environment", request.environment),
            ):
                if authorization.get(key) != expected:
                    reasons.append("EXECUTION_AUTHORIZATION_BINDING_MISMATCH")
                    break
            if authorization.get("production_authorized") is not False:
                reasons.append("PRODUCTION_AUTHORIZATION_DENIED")
        return tuple(sorted(set(reasons)))

    @staticmethod
    def _result_reasons(
        result: Mapping[str, Any], executor_request: Mapping[str, Any],
        capability: Mapping[str, Any], operation: str,
    ) -> tuple[str, ...]:
        required = {
            "result_digest", "request_id", "capability_id", "status",
            "operation_results", "evidence_digests", "production_authorized",
            "repository_writes", "production_writes", "ubuntu_changes",
            "network_accesses", "runtime_commands",
        }
        if not required.issubset(result):
            return ("MALFORMED_ADAPTER_RESULT",)
        reasons: list[str] = []
        if result["request_id"] != executor_request["request_id"] or result["capability_id"] != capability["capability_id"]:
            reasons.append("ADAPTER_RESULT_BINDING_MISMATCH")
        if result["operation_results"] != [{"operation": operation, "status": result["status"]}]:
            reasons.append("ADAPTER_RESULT_BINDING_MISMATCH")
        if result["status"] in {"DENIED", "INVALID", "UNAVAILABLE", "INCOMPLETE"}:
            reasons.append("ADAPTER_STEP_" + result["status"])
        if result["production_authorized"] is not False:
            reasons.append("PRODUCTION_AUTHORIZATION_DENIED")
        for key in ("repository_writes", "production_writes", "ubuntu_changes", "network_accesses", "runtime_commands"):
            if result[key] != 0:
                reasons.append("NONZERO_ADAPTER_SAFETY_COUNTER")
        return tuple(sorted(set(reasons)))

    @staticmethod
    def _decision(
        request: PilotActivationRequest | None, status: PilotActivationStatus,
        reasons: tuple[str, ...], consumed: bool,
        steps: tuple[PilotActivationStep, ...] = (),
    ) -> PilotActivationDecision:
        ordered_reasons = tuple(sorted(set(reasons)))
        report = PilotActivationValidationReport(
            status=status, reason_codes=ordered_reasons,
            evaluated_at=request.activation_timestamp if request else "",
            permit_consumed=consumed,
        )
        receipt = None
        if request is not None and consumed:
            evidence = PilotActivationEvidence(
                ordered_steps=steps,
                executor_result_digests=tuple(step.result_digest for step in steps),
                evidence_digests=tuple(sorted({
                    digest for step in steps for digest in step.evidence_digests
                })),
            )
            semantic = {
                "activation_id": request.activation_id, "permit_id": request.permit_id,
                "permit_digest": request.permit_digest,
                "execution_authorization_id": request.execution_authorization_id,
                "readiness_report_id": request.readiness_report_id,
                "package_digest": request.package_digest, "plan_digest": request.plan_digest,
                "target_identity": request.target_identity, "environment": request.environment,
                "sandbox_root_identity_digest": request.sandbox_root_identity_digest,
                "evidence": evidence.to_dict(), "activation_status": status.value,
                "permit_consumed": True, "controlled_test_sandbox": True,
                "production_authorized": False, "production_writes": 0,
                "repository_runtime_writes": 0, "ubuntu_changes": 0,
                "network_accesses": 0, "runtime_commands": 0, "service_restarts": 0,
            }
            receipt_values = dict(semantic)
            receipt_values["evidence"] = evidence
            receipt_values["activation_status"] = status
            receipt = PilotActivationReceipt(
                **receipt_values, receipt_digest=sha256_digest(semantic)
            )
        return PilotActivationDecision(status, ordered_reasons, receipt, report)
