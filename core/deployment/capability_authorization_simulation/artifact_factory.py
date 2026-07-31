"""Deterministic factory for unmistakably test-only artifacts."""

from dataclasses import replace
from datetime import datetime

from core.deployment.contracts import sha256_digest

from .models import *


def stable_id(prefix: str, seed: str, *bindings: str) -> str:
    return prefix + sha256_digest([seed, *bindings])[7:39]


class TestOnlyArtifactFactory:
    def __init__(self, *, timestamp: datetime) -> None:
        self.timestamp = timestamp

    def authorization(self, request, capability):
        return TestOnlyAuthorizationArtifact(
            stable_id("m4-a3-test-authorization-", request.scenario_seed, request.simulation_id,
                      capability.value), request.simulation_id, request.scenario_id, capability,
            request.request_digest, request.approval_digest, request.grant_plan_digest,
            self.timestamp, 1)

    def permit(self, request, authorization):
        return TestOnlyPermitArtifact(
            stable_id("m4-a3-test-permit-", request.scenario_seed, authorization.authorization_id),
            authorization.authorization_id, authorization.digest(), request.simulation_id,
            authorization.capability, request.request_digest, request.approval_digest,
            request.grant_plan_digest, self.timestamp)
    def claim(self, request, authorization, permit):
        return TestOnlyClaimArtifact(
            stable_id("m4-a3-test-claim-", request.scenario_seed, permit.permit_id),
            permit.permit_id, permit.digest(), authorization.authorization_id,
            authorization.digest(), request.simulation_id, authorization.capability,
            request.request_digest, request.approval_digest, request.grant_plan_digest,
            self.timestamp)
