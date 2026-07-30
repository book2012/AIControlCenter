"""Authorized Mac bootstrap execution coordinator."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from .models import *
from .validation import OperationalBootstrapLivePermitValidator, OperationalBootstrapRuntimeValidator


class OperationalMacBootstrapExecutionCoordinator:
    def __init__(self, *, config, artifact_reader, claim_registry, path_policy,
                 runtime_adapter) -> None:
        self.config = config
        self.reader = artifact_reader
        self.claim_registry = claim_registry
        self.path_policy = path_policy
        self.adapter = runtime_adapter

    def execute(self, *, request, host, target) -> OperationalBootstrapRuntimeEvidenceBundle:
        plan = OperationalBootstrapRuntimePlan.build()
        findings = OperationalBootstrapRuntimeValidator().validate(
            config=self.config, request=request, host=host, target=target)
        if findings:
            raise OperationalBootstrapExecutionError(findings[0].code)
        test_only = request.mode is OperationalBootstrapRuntimeMode.TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION
        paths = self.path_policy.resolve(test_only=test_only)
        if paths.root != target.operational_root:
            raise OperationalBootstrapExecutionError("TARGET_BINDING_INVALID")
        if test_only:
            allowed = Path(os.environ.get("AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT", "")).resolve()
            try:
                request.permit_path.resolve().relative_to(allowed)
                paths.root.resolve().relative_to(
                    Path(os.environ["AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_HOME"]).resolve())
            except (KeyError, ValueError):
                raise OperationalBootstrapExecutionError("TEST_CONFINEMENT_INVALID")
        permit_raw, permit = self.reader.read(request.permit_path)
        issuance_raw, issuance = self.reader.read(request.issuance_evidence_path)
        live = OperationalBootstrapLivePermitEvidence(
            permit, permit_raw, permit.get("permit_digest", ""))
        issuance_contract = OperationalBootstrapIssuanceEvidence(issuance, issuance_raw)
        permit_findings = OperationalBootstrapLivePermitValidator().validate(
            live=live, issuance=issuance_contract, request=request)
        if permit_findings:
            raise OperationalBootstrapExecutionError(permit_findings[0].code)
        if any(path.exists() for path in (
                paths.audit_database, paths.audit_backups, paths.replay_database,
                paths.replay_backups, paths.monitoring)):
            raise OperationalBootstrapExecutionError("TARGET_ALREADY_EXISTS")
        claim_request = OperationalBootstrapClaimRequest(
            permit["permit_id"], live.permit_digest, request.branch, request.commit,
            request.operator_identity, request.claim_at, request.request_id)
        claim = self.claim_registry.claim(request.permit_path, claim_request)
        if any(path.exists() for path in (
                paths.audit_database, paths.audit_backups, paths.replay_database,
                paths.replay_backups, paths.monitoring)):
            raise OperationalBootstrapExecutionError("TARGET_APPEARED_AFTER_CLAIM")
        receipt = self.adapter.execute(
            request=request, paths=paths, claim=claim, plan=plan)
        receipt_digest = canonical_digest(receipt.as_dict())
        content = {"receipt_digest": receipt_digest, "claim_digest": claim.claim_digest,
                   "plan_digest": plan.plan_digest}
        evidence_digest = canonical_digest(content)
        return OperationalBootstrapRuntimeEvidenceBundle(
            "m3-a4b2b2a-evidence-" + evidence_digest[7:39], receipt, receipt_digest,
            claim.claim_digest, plan.plan_digest, evidence_digest)
