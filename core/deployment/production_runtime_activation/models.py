"""Immutable contracts for governed Production Runtime activation."""

from __future__ import annotations

import re
from dataclasses import dataclass


_RUNTIME_ID = re.compile(r"^[0-9a-f]{12}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

_CANONICAL_SERVICE_LABEL = "com.aicontrolcenter.api"
_CANONICAL_RUNTIME_TARGET = "ops.macos.runtime.application:app"


class ProductionRuntimeActivationError(ValueError):
    """Fail-closed Production Runtime activation contract error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationRequest:
    request_id: str
    candidate_runtime_id: str
    candidate_source_commit: str
    governance_commit: str
    expected_current_runtime_id: str
    canonical_service_label: str
    canonical_runtime_target: str
    human_authorization_id: str
    human_authorization_digest: str
    plan_digest: str

    def __post_init__(self) -> None:
        if not self.request_id or not self.human_authorization_id:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_IDENTITY_BINDING_INVALID"
            )

        if not _RUNTIME_ID.fullmatch(self.candidate_runtime_id):
            raise ProductionRuntimeActivationError(
                "CANDIDATE_RUNTIME_ID_INVALID"
            )

        if not _COMMIT.fullmatch(self.candidate_source_commit):
            raise ProductionRuntimeActivationError(
                "CANDIDATE_SOURCE_COMMIT_INVALID"
            )

        if self.candidate_runtime_id != self.candidate_source_commit[:12]:
            raise ProductionRuntimeActivationError(
                "CANDIDATE_SOURCE_BINDING_INVALID"
            )

        if not _COMMIT.fullmatch(self.governance_commit):
            raise ProductionRuntimeActivationError(
                "GOVERNANCE_COMMIT_INVALID"
            )

        if not _RUNTIME_ID.fullmatch(self.expected_current_runtime_id):
            raise ProductionRuntimeActivationError(
                "EXPECTED_CURRENT_RUNTIME_INVALID"
            )

        if self.canonical_service_label != _CANONICAL_SERVICE_LABEL:
            raise ProductionRuntimeActivationError(
                "CANONICAL_SERVICE_BINDING_INVALID"
            )

        if self.canonical_runtime_target != _CANONICAL_RUNTIME_TARGET:
            raise ProductionRuntimeActivationError(
                "CANONICAL_TARGET_BINDING_INVALID"
            )

        if not _DIGEST.fullmatch(self.human_authorization_digest):
            raise ProductionRuntimeActivationError(
                "HUMAN_AUTHORIZATION_DIGEST_INVALID"
            )

        if not _DIGEST.fullmatch(self.plan_digest):
            raise ProductionRuntimeActivationError(
                "PLAN_DIGEST_INVALID"
            )
