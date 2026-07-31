"""Pure deterministic M4-A3 lifecycle simulator."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from core.deployment.contracts import sha256_digest

from .artifact_factory import TestOnlyArtifactFactory
from .models import *
from .replay import InMemoryTestOnlyReplayGuard
from .validation import (
    validate_bindings,
    validate_config,
    validate_evidence_chain,
    validate_request,
    validate_test_artifact,
)


class TestOnlyAuthorizationSimulator:
    def __init__(self, *, clock, scenario_seed: str, replay_guard=None) -> None:
        self._clock = clock
        self._seed = scenario_seed
        self._replay = replay_guard or InMemoryTestOnlyReplayGuard()

    def simulate(self, config, request) -> TestOnlyAuthorizationSimulationResult:
        scenario = TestOnlyAuthorizationScenario(
            request.scenario_id, self._seed,
            request.capability if isinstance(request.capability, ControlledActivationCapability)
            else ControlledActivationCapability.AUDIT_WRITER,
            request.dependency_authorization_reference,
            request.dependency_authorization_digest,
        )
        try:
            validate_config(config)
            now = self._clock()
            capability = validate_request(request, now=now)
            scenario = replace(scenario, capability=capability)
            factory = TestOnlyArtifactFactory(timestamp=now)
            authorization = factory.authorization(request, capability)
            permit = factory.permit(request, authorization)
            self._replay.claim_once(permit.permit_id)
            claim = factory.claim(request, authorization, permit)
            validate_test_artifact(authorization, "m4-a3-test-authorization-")
            validate_test_artifact(permit, "m4-a3-test-permit-")
            validate_test_artifact(claim, "m4-a3-test-claim-")
            artifacts = (
                request, request, request, authorization, permit, claim, claim,
            )
            evidence = []
            prior = "sha256:" + "0" * 64
            for sequence, (state, artifact) in enumerate(
                zip(TestOnlyAuthorizationStep, artifacts), start=1
            ):
                timestamp = now + timedelta(microseconds=sequence - 1)
                item = TestOnlyAuthorizationSimulationEvidence(
                    sequence, request.simulation_id, request.scenario_id,
                    request.branch, request.commit, capability,
                    request.request_digest, request.approval_digest,
                    request.grant_plan_digest, prior, timestamp, state, True,
                    artifact.digest(), "",
                )
                item = replace(item, canonical_artifact_digest=item.computed_digest())
                evidence.append(item)
                prior = item.canonical_artifact_digest
            validate_bindings(authorization, permit, claim)
            validate_evidence_chain(evidence)
            return TestOnlyAuthorizationSimulationResult(
                TASK, request.simulation_id, scenario, tuple(evidence),
                authorization, permit, claim, (),
                TestOnlyAuthorizationSimulationDecision.READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION,
            )
        except (TestOnlyAuthorizationSimulationError, ValueError) as error:
            code = getattr(error, "code", "INVALID_SIMULATION_INPUT")
            return TestOnlyAuthorizationSimulationResult(
                TASK, request.simulation_id, scenario, (), None, None, None,
                (code,), TestOnlyAuthorizationSimulationDecision.BLOCKED,
            )
