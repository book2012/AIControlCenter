"""Non-operational contract for exact create-only Production journal provisioning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .pre_bootstrap_remediation_journal import FUTURE_PRODUCTION_JOURNAL_PATH


class JournalProvisioningPurpose(Enum):
    CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL = (
        "CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL"
    )


class JournalProvisioningEligibility(Enum):
    ELIGIBLE = "ELIGIBLE"
    DENIED = "DENIED"


class JournalTargetState(Enum):
    ABSENT = "ABSENT"
    SAFE_EXISTING = "SAFE_EXISTING"
    UNSAFE_EXISTING = "UNSAFE_EXISTING"
    AMBIGUOUS = "AMBIGUOUS"


class JournalProvisioningAction(Enum):
    CREATE_ONCE = "CREATE_ONCE"
    RECOGNIZE_READ_ONLY = "RECOGNIZE_READ_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class JournalProvisioningReceipt:
    schema_version: int
    purpose: JournalProvisioningPurpose
    provisioning_replay_fingerprint: str
    terminal_provisioning_state: str


def decide_journal_provisioning(
    state: JournalTargetState, receipt: JournalProvisioningReceipt | None = None
) -> JournalProvisioningAction:
    if state is JournalTargetState.ABSENT and receipt is None:
        return JournalProvisioningAction.CREATE_ONCE
    matching = (
        state is JournalTargetState.SAFE_EXISTING
        and type(receipt) is JournalProvisioningReceipt
        and receipt.schema_version == 1
        and receipt.purpose is JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL
        and bool(receipt.provisioning_replay_fingerprint)
        and receipt.terminal_provisioning_state == "COMPLETED"
    )
    return JournalProvisioningAction.RECOGNIZE_READ_ONLY if matching else JournalProvisioningAction.FAIL_CLOSED


@dataclass(frozen=True, slots=True)
class JournalProvisioningPlan:
    purpose: JournalProvisioningPurpose = (
        JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL
    )
    create_only: bool = True


@dataclass(frozen=True, slots=True)
class JournalProvisioningAuthorization:
    purpose: JournalProvisioningPurpose
    request_identity: str
    one_use: bool = True


class JournalProvisioningAdapter(Protocol):
    def create_exact_journal(self, plan: JournalProvisioningPlan) -> bool: ...


def validate_journal_provisioning_plan(
    plan: object, *, observed_target: object = FUTURE_PRODUCTION_JOURNAL_PATH
) -> JournalProvisioningEligibility:
    exact = (
        type(plan) is JournalProvisioningPlan
        and plan.purpose is JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL
        and plan.create_only is True
        and observed_target == FUTURE_PRODUCTION_JOURNAL_PATH
    )
    return JournalProvisioningEligibility.ELIGIBLE if exact else JournalProvisioningEligibility.DENIED


def authorize_journal_provisioning(
    plan: object, authorization: object
) -> JournalProvisioningEligibility:
    exact_authorization = (
        type(authorization) is JournalProvisioningAuthorization
        and authorization.purpose
        is JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL
        and type(authorization.request_identity) is str
        and bool(authorization.request_identity)
        and authorization.one_use is True
    )
    if not exact_authorization:
        return JournalProvisioningEligibility.DENIED
    return validate_journal_provisioning_plan(plan)


__all__ = (
    "JournalProvisioningAdapter", "JournalProvisioningAuthorization",
    "JournalProvisioningEligibility", "JournalProvisioningPlan",
    "JournalProvisioningAction", "JournalProvisioningReceipt", "JournalTargetState",
    "JournalProvisioningPurpose", "authorize_journal_provisioning",
    "decide_journal_provisioning",
    "validate_journal_provisioning_plan",
)
