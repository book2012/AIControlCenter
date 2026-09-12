"""Exact human authorization contract for Production Runtime activation."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from core.deployment.contracts import sha256_digest as canonical_digest

from .models import (
    ProductionRuntimeActivationError,
    ProductionRuntimeActivationRequest,
)

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def request_digest(request: ProductionRuntimeActivationRequest) -> str:
    return canonical_digest(asdict(request))


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ProductionRuntimeActivationError(
            "AUTHORIZATION_TIMESTAMP_INVALID"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProductionRuntimeActivationError(
            "AUTHORIZATION_TIMEZONE_REQUIRED"
        )
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationAuthorizationPermit:
    authorization_id: str
    activation_request_digest: str
    candidate_runtime_id: str
    candidate_source_commit: str
    governance_commit: str
    expected_current_runtime_id: str
    plan_digest: str
    operator_identity: str
    independent_approver_identity: str
    authorized_at: str
    not_before: str
    expires_at: str
    maximum_uses: int = 1
    production_runtime_activation_authorized: bool = True

    def __post_init__(self) -> None:
        if not self.authorization_id:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_AUTHORIZATION_ID_REQUIRED"
            )
        if not _DIGEST.fullmatch(self.activation_request_digest):
            raise ProductionRuntimeActivationError(
                "ACTIVATION_REQUEST_DIGEST_INVALID"
            )
        if not self.operator_identity or not self.independent_approver_identity:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_AUTHORIZATION_IDENTITY_INVALID"
            )
        if self.operator_identity == self.independent_approver_identity:
            raise ProductionRuntimeActivationError(
                "INDEPENDENT_APPROVER_REQUIRED"
            )
        approved = _timestamp(self.authorized_at)
        start = _timestamp(self.not_before)
        end = _timestamp(self.expires_at)
        if not approved <= start < end:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_AUTHORIZATION_WINDOW_INVALID"
            )
        if self.maximum_uses != 1:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_AUTHORIZATION_MAXIMUM_USES_INVALID"
            )
        if not self.production_runtime_activation_authorized:
            raise ProductionRuntimeActivationError(
                "PRODUCTION_RUNTIME_ACTIVATION_NOT_AUTHORIZED"
            )


def validate_activation_authorization(
    *,
    request: ProductionRuntimeActivationRequest,
    permit: ProductionRuntimeActivationAuthorizationPermit | None,
    validated_at: str,
    operator_identity: str,
) -> None:
    if not isinstance(
        permit,
        ProductionRuntimeActivationAuthorizationPermit,
    ):
        raise ProductionRuntimeActivationError(
            "PRODUCTION_RUNTIME_ACTIVATION_AUTHORIZATION_REQUIRED"
        )

    bindings = (
        (permit.activation_request_digest, request_digest(request)),
        (permit.candidate_runtime_id, request.candidate_runtime_id),
        (permit.candidate_source_commit, request.candidate_source_commit),
        (permit.governance_commit, request.governance_commit),
        (
            permit.expected_current_runtime_id,
            request.expected_current_runtime_id,
        ),
        (permit.plan_digest, request.plan_digest),
    )
    if any(actual != expected for actual, expected in bindings):
        raise ProductionRuntimeActivationError(
            "ACTIVATION_AUTHORIZATION_BINDING_MISMATCH"
        )
    if permit.operator_identity != operator_identity:
        raise ProductionRuntimeActivationError(
            "ACTIVATION_AUTHORIZATION_OPERATOR_MISMATCH"
        )

    now = _timestamp(validated_at)
    if now < _timestamp(permit.not_before):
        raise ProductionRuntimeActivationError(
            "ACTIVATION_AUTHORIZATION_NOT_YET_VALID"
        )
    if now >= _timestamp(permit.expires_at):
        raise ProductionRuntimeActivationError(
            "ACTIVATION_AUTHORIZATION_EXPIRED"
        )
