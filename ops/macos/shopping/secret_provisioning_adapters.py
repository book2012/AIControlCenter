"""Fake-driven, non-production mutation adapters for Shopping secret provisioning."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from core.governance.control_plane.domain import (
    ExecutionStatus,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
)


SOPS_INSTALL_ENSURE = "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE"
AGE_INSTALL_ENSURE = "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE"
CONTROL_PLANE_IDENTITY_CREATE = "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE"
CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE = (
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE"
)
OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE = (
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE"
)
OFFLINE_RECOVERY_RECIPIENT_INTAKE = (
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE"
)
SHOPPING_SECRET_PROVISIONING = "SHOPPING_SECRET_PROVISIONING"


class MutationOutcome(StrEnum):
    """Value-free outcome returned by one narrowly injected capability."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


class AdapterRequestRejected(ValueError):
    """Fail-closed adapter rejection containing only a stable error code."""


class EnsureSopsTool(Protocol):
    def ensure_sops_tool(self) -> MutationOutcome: ...


class EnsureAgeTooling(Protocol):
    def ensure_age_tooling(self) -> MutationOutcome: ...


class CreateControlPlaneAgeIdentity(Protocol):
    def create_control_plane_age_identity(self) -> MutationOutcome: ...


class RegisterControlPlaneRecipientMetadata(Protocol):
    def register_control_plane_recipient_metadata(self) -> MutationOutcome: ...


class RegisterOfflineRecoveryPublicMetadata(Protocol):
    def register_offline_recovery_public_metadata(self) -> MutationOutcome: ...


class IntakeOfflineRecoveryPublicRecipient(Protocol):
    def intake_offline_recovery_public_recipient(self) -> MutationOutcome: ...


def _validate_request(
    request: GovernanceExecutionRequest, expected_action: str
) -> GovernanceExecutionRequest:
    if not isinstance(request, GovernanceExecutionRequest):
        raise AdapterRequestRejected("INVALID_EXECUTION_REQUEST")
    if request.target != SHOPPING_SECRET_PROVISIONING:
        raise AdapterRequestRejected("TARGET_NOT_SUPPORTED")
    if request.action_type != expected_action:
        raise AdapterRequestRejected("ACTION_NOT_SUPPORTED")
    return request


def _receipt(
    request: GovernanceExecutionRequest, outcome: MutationOutcome
) -> GovernanceExecutionReceipt:
    if not isinstance(outcome, MutationOutcome):
        outcome = MutationOutcome.UNCERTAIN
    status = ExecutionStatus(outcome.value)
    return GovernanceExecutionReceipt(
        schema_version=request.schema_version,
        receipt_id=f"execution-receipt:{request.execution_request_id}",
        lifecycle_id=request.lifecycle_id,
        execution_request_id=request.execution_request_id,
        authorization_id=request.authorization_id,
        claim_id=request.claim_id,
        mutation_budget_id=request.mutation_budget_id,
        action_type=request.action_type,
        status=status,
        actual_invocation_count=1,
        completed_count=int(status is ExecutionStatus.COMPLETED),
        uncertain_count=int(status is ExecutionStatus.UNCERTAIN),
        started_at=request.requested_at,
        completed_at=request.requested_at,
        result_digest=None,
        reason_codes=(f"MUTATION_{status.value}",),
    )


class SopsInstallEnsureAdapter:
    ACTION = SOPS_INSTALL_ENSURE

    def __init__(self, capability: EnsureSopsTool) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.ensure_sops_tool()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


class AgeInstallEnsureAdapter:
    ACTION = AGE_INSTALL_ENSURE

    def __init__(self, capability: EnsureAgeTooling) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.ensure_age_tooling()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


class ControlPlaneIdentityCreateAdapter:
    ACTION = CONTROL_PLANE_IDENTITY_CREATE

    def __init__(self, capability: CreateControlPlaneAgeIdentity) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.create_control_plane_age_identity()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


class ControlPlaneRecipientRegisterValidateAdapter:
    ACTION = CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE

    def __init__(self, capability: RegisterControlPlaneRecipientMetadata) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.register_control_plane_recipient_metadata()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


class OfflineRecoveryRecipientRegisterValidateAdapter:
    ACTION = OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE

    def __init__(self, capability: RegisterOfflineRecoveryPublicMetadata) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.register_offline_recovery_public_metadata()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


class OfflineRecoveryRecipientIntakeAdapter:
    ACTION = OFFLINE_RECOVERY_RECIPIENT_INTAKE

    def __init__(self, capability: IntakeOfflineRecoveryPublicRecipient) -> None:
        self._capability = capability

    def invoke_once(self, request: GovernanceExecutionRequest) -> GovernanceExecutionReceipt:
        request = _validate_request(request, self.ACTION)
        try:
            outcome = self._capability.intake_offline_recovery_public_recipient()
        except Exception:
            outcome = MutationOutcome.UNCERTAIN
        return _receipt(request, outcome)


__all__ = (
    "AGE_INSTALL_ENSURE",
    "CONTROL_PLANE_IDENTITY_CREATE",
    "CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE",
    "OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE",
    "OFFLINE_RECOVERY_RECIPIENT_INTAKE",
    "SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_PROVISIONING",
    "AdapterRequestRejected",
    "AgeInstallEnsureAdapter",
    "ControlPlaneIdentityCreateAdapter",
    "ControlPlaneRecipientRegisterValidateAdapter",
    "MutationOutcome",
    "OfflineRecoveryRecipientRegisterValidateAdapter",
    "OfflineRecoveryRecipientIntakeAdapter",
    "SopsInstallEnsureAdapter",
)
