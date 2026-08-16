"""Vendor-neutral, value-free secret provisioning plan model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class Readiness(str, Enum):
    READY = "READY"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"
    MALFORMED = "MALFORMED"


NO_AUTOMATIC_RETRY = "NO_AUTOMATIC_RETRY"
NO_AUTOMATIC_ROLLBACK = "NO_AUTOMATIC_ROLLBACK"
_VERSION_TOKEN = re.compile(r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*$")
_IDENTIFIER_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_ACTION_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]*(?::[A-Z][A-Z0-9_]*)*$")
_REASON_CODE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class ProvisioningPlan:
    schema_version: str
    backend_definition_id: str
    action: str
    current_readiness: Readiness
    missing_prerequisites: tuple[str, ...] = ()
    mutation_required: bool = False
    authorization_required: bool = False
    invocation_count: int = 0
    retry_policy: str = NO_AUTOMATIC_RETRY
    rollback_policy: str = NO_AUTOMATIC_ROLLBACK
    secret_values_read: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not _VERSION_TOKEN.fullmatch(self.schema_version):
            raise ValueError("schema version must be a safe version token")
        if not isinstance(self.backend_definition_id, str) or not _IDENTIFIER_TOKEN.fullmatch(self.backend_definition_id):
            raise ValueError("backend definition id must be a safe identifier token")
        if not isinstance(self.action, str) or not _ACTION_TOKEN.fullmatch(self.action):
            raise ValueError("action must be a safe action identifier token")
        if not isinstance(self.missing_prerequisites, tuple) or any(
            not isinstance(item, str) or not _REASON_CODE.fullmatch(item)
            for item in self.missing_prerequisites
        ):
            raise ValueError("missing prerequisites must be stable reason codes")
        if self.current_readiness is Readiness.READY and self.missing_prerequisites:
            raise ValueError("ready plans cannot have missing prerequisites")
        if self.current_readiness is not Readiness.READY and not self.missing_prerequisites:
            raise ValueError("non-ready plans require a missing prerequisite")
        expected = {
            Readiness.READY: (False, False, 0),
            Readiness.MISSING: (True, True, 1),
            Readiness.BLOCKED: (False, False, 0),
            Readiness.MALFORMED: (False, False, 0),
        }[self.current_readiness]
        actual = (
            self.mutation_required,
            self.authorization_required,
            self.invocation_count,
        )
        if actual != expected:
            raise ValueError("plan state violates readiness invariants")
        if self.retry_policy != NO_AUTOMATIC_RETRY:
            raise ValueError("automatic retry is prohibited")
        if self.rollback_policy != NO_AUTOMATIC_ROLLBACK:
            raise ValueError("automatic rollback is prohibited")
        if self.secret_values_read is not False:
            raise ValueError("secret values must never be read")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "backend_definition_id": self.backend_definition_id,
            "action": self.action,
            "current_readiness": self.current_readiness.value,
            "missing_prerequisites": list(self.missing_prerequisites),
            "mutation_required": self.mutation_required,
            "authorization_required": self.authorization_required,
            "invocation_count": self.invocation_count,
            "retry_policy": self.retry_policy,
            "rollback_policy": self.rollback_policy,
            "secret_values_read": self.secret_values_read,
        }


def plan_for(
    *, schema_version: str, backend_definition_id: str, action: str,
    readiness: Readiness, missing_prerequisites: tuple[str, ...] = (),
) -> ProvisioningPlan:
    mutation = readiness is Readiness.MISSING
    return ProvisioningPlan(
        schema_version=schema_version,
        backend_definition_id=backend_definition_id,
        action=action,
        current_readiness=readiness,
        missing_prerequisites=missing_prerequisites,
        mutation_required=mutation,
        authorization_required=mutation,
        invocation_count=1 if mutation else 0,
    )


__all__ = (
    "NO_AUTOMATIC_RETRY", "NO_AUTOMATIC_ROLLBACK", "ProvisioningPlan",
    "Readiness", "plan_for",
)
