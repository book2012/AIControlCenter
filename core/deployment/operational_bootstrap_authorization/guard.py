"""Injected single-use guard contracts; no persistence implementation."""

from __future__ import annotations

from typing import Protocol

from .models import (
    OperationalBootstrapAuthorizationError,
    OperationalBootstrapAuthorizationRequest,
    OperationalBootstrapAuthorizationDecision,
    OperationalBootstrapPermit,
    OperationalBootstrapPermitUseClaim,
    canonical_digest,
    parse_timestamp,
    require_identity,
)
from .service import OperationalBootstrapPermitValidator


class OperationalBootstrapPermitUseRegistryPort(Protocol):
    def inspect(self, permit_id: str) -> OperationalBootstrapPermitUseClaim | None: ...

    def claim_unused(
        self, claim: OperationalBootstrapPermitUseClaim,
    ) -> OperationalBootstrapPermitUseClaim: ...


class OperationalBootstrapPermitUseGuard:
    def __init__(self, registry: OperationalBootstrapPermitUseRegistryPort) -> None:
        if registry is None:
            raise OperationalBootstrapAuthorizationError("injected registry required")
        self._registry = registry

    def claim(
        self, *, permit: OperationalBootstrapPermit,
        request: OperationalBootstrapAuthorizationRequest,
        decision: OperationalBootstrapAuthorizationDecision,
        claimant_identity: str, claimed_at: str, branch: str, commit: str,
    ) -> OperationalBootstrapPermitUseClaim:
        require_identity(claimant_identity)
        parse_timestamp(claimed_at)
        validation = OperationalBootstrapPermitValidator().validate(
            permit=permit, request=request, decision=decision,
            validated_at=claimed_at, branch=branch, commit=commit)
        if not validation.valid:
            raise OperationalBootstrapAuthorizationError("invalid permit cannot be claimed")
        if self._registry.inspect(permit.permit_id) is not None:
            raise OperationalBootstrapAuthorizationError("permit already claimed")
        content = {
            "permit_id": permit.permit_id, "permit_digest": permit.permit_digest,
            "claimant_identity": claimant_identity, "claimed_at": claimed_at,
            "maximum_uses": 1, "production_authorized": False,
        }
        claim = OperationalBootstrapPermitUseClaim(
            "m3-a4b1-claim-" + canonical_digest(content)[7:39], **content)
        return self._registry.claim_unused(claim)
