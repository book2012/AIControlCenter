"""Bounded composition of existing authorization, permit and execution services."""

from __future__ import annotations

from dataclasses import asdict

from core.deployment.operational_bootstrap_execution import (
    MacOperationalBootstrapRuntimeAdapter,
    OperationalBootstrapRuntimeMode,
    OperationalBootstrapRuntimeRequest,
    TestOnlyOperationalBootstrapRuntimeAdapter,
)

from .models import *
from .acknowledgements import (
    ControlledLivePermitCompatibilityValidator,
    ControlledWarningAcknowledgementProjector,
)
from .validation import ControlledOperationalBootstrapArtifactValidator


class ControlledOperationalBootstrapOrchestrator:
    """The only reviewed local live composition boundary.

    Authorization and issuance collaborators must return the existing public
    contracts.  Keeping them injected makes deterministic test execution
    possible without weakening live adapter selection.
    """

    def __init__(self, *, approval_reader, preflight_reader, artifact_writer,
                 git_evidence, host_evidence, clock, activation_service,
                 permit_service, execution_coordinator,
                 runtime_adapter: MacOperationalBootstrapRuntimeAdapter) -> None:
        if isinstance(runtime_adapter, TestOnlyOperationalBootstrapRuntimeAdapter):
            raise ControlledOperationalBootstrapError("TEST_ADAPTER_REJECTED")
        if not isinstance(runtime_adapter, MacOperationalBootstrapRuntimeAdapter):
            raise ControlledOperationalBootstrapError("OPERATIONAL_ADAPTER_REQUIRED")
        self.approval_reader = approval_reader
        self.preflight_reader = preflight_reader
        self.writer = artifact_writer
        self.git = git_evidence
        self.host = host_evidence
        self.clock = clock
        self.activation_service = activation_service
        self.permit_service = permit_service
        self.execution_coordinator = execution_coordinator
        self.runtime_adapter = runtime_adapter

    def execute(self, request: ControlledOperationalBootstrapRequest
                ) -> ControlledOperationalBootstrapResult:
        digest = canonical_digest(request.as_dict())
        approval = self.approval_reader.read(request.artifacts.approval_input)
        preflight = self.preflight_reader.read(
            request.artifacts.shared_parent_preflight_evidence)
        now = self.clock.now()
        ControlledOperationalBootstrapArtifactValidator().validate(
            request=request, approval=approval, preflight=preflight,
            git=self.git.collect(), host=self.host.collect(), now=now)
        projection = ControlledWarningAcknowledgementProjector().project(
            evidence=request.restriction_acknowledgements, request=request)
        compatibility = ControlledLivePermitCompatibilityValidator().validate(
            request=request, projection=projection)
        activation_request, activation, activation_evidence = (
            self.activation_service.authorize(
                request=request, approval=approval, preflight=preflight, now=now))
        if activation is None:
            raise ControlledOperationalBootstrapError(
                "ACTIVATION_AUTHORIZATION_REQUIRED")
        self.writer.write(request.artifacts.activation_authorization_request_output,
                          activation_request.as_dict())
        self.writer.write(request.artifacts.activation_authorization_output,
                          activation.as_dict())
        self.writer.write(request.artifacts.activation_authorization_evidence_output,
                          activation_evidence)
        permit, issuance_evidence = self.permit_service.issue(
            request=request, approval=approval, activation_authorization=activation,
            now=now, compatibility_report=compatibility)
        if not isinstance(permit, ControlledLivePermitResult):
            raise ControlledOperationalBootstrapError("TYPED_LIVE_PERMIT_REQUIRED")
        permit.validate_for(request, now)
        ControlledLivePermitCompatibilityValidator().validate_permit(
            request=request, permit=permit, report=compatibility)
        self.writer.write(request.artifacts.operational_permit_output, permit.as_dict())
        self.writer.write(request.artifacts.permit_issuance_evidence_output,
                          issuance_evidence)
        runtime_request = OperationalBootstrapRuntimeRequest(
            request_id=request.request_id,
            mode=OperationalBootstrapRuntimeMode.CONTROLLED_NON_PRODUCTION_OPERATIONAL_BOOTSTRAP,
            branch=request.branch, commit=request.commit,
            operator_identity=request.operator_identity,
            requested_at=now, claim_at=now,
            permit_path=request.artifacts.operational_permit_output,
            issuance_evidence_path=request.artifacts.permit_issuance_evidence_output,
            evidence_directory=request.artifacts.bootstrap_evidence_output.parent,
            metadata={"scope": request.scope.value},
            activation_authorization_digest=activation.authorization_digest)
        host = self.host.runtime_evidence()
        target = self.host.target_evidence()
        bundle = self.execution_coordinator.execute(
            request=runtime_request, host=host, target=target,
            activation_authorization=activation)
        claim_path = request.artifacts.operational_permit_output.with_name(
            request.artifacts.operational_permit_output.name + ".claim.json")
        if claim_path != request.artifacts.permit_claim_output:
            raise ControlledOperationalBootstrapError("CLAIM_PATH_BINDING_INVALID")
        self.writer.write(request.artifacts.bootstrap_receipt_output,
                          bundle.receipt.as_dict())
        self.writer.write(request.artifacts.bootstrap_evidence_output, {
            "bundle_id": bundle.bundle_id, "receipt_digest": bundle.receipt_digest,
            "claim_digest": bundle.claim_digest, "plan_digest": bundle.plan_digest,
            "evidence_digest": bundle.evidence_digest})
        result = ControlledOperationalBootstrapResult(
            "m3-a4b2b2b-r3-" + digest[7:39],
            ControlledOperationalBootstrapStatus.COMPLETE, digest,
            tuple(ControlledOperationalBootstrapCheck(code, True) for code in (
                "REQUEST", "APPROVAL", "PREFLIGHT", "GIT", "HOST",
                "ACTIVATION_AUTHORIZATION", "PERMIT", "CLAIM", "BOOTSTRAP")),
            (), activation.authorization_id, permit.permit_id,
            bundle.receipt.claim_id, bundle.receipt.receipt_id)
        self.writer.write(request.artifacts.post_bootstrap_validation_output,
                          result.as_dict())
        return result
