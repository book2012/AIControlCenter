"""Deterministic, non-production bootstrap evidence generation."""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from core.deployment.contracts import canonical_json_bytes
from core.deployment.operational_bootstrap_execution.models import (
    RUNTIME_STEP_CODES, OperationalBootstrapRuntimePlan,
)
from core.deployment.operational_bootstrap_live.models import (
    ControlledRestrictionAcknowledgement, canonical_digest,
)

from .service import (
    BRANCH, COMMIT, BootstrapEvidenceRecoveryError,
    TrustedBootstrapEvidenceBinding,
)


@dataclass(frozen=True, slots=True)
class ControlledEvidenceInput:
    root: Path
    requester_identity: str
    operator_identity: str
    independent_approver_identity: str
    identity_seed: str
    branch: str = BRANCH
    commit: str = COMMIT
    environment: str = "CONTROLLED_NON_PRODUCTION"
    production_authorized: bool = False

    def __post_init__(self) -> None:
        root = Path(self.root)
        identities = (self.requester_identity, self.operator_identity,
                      self.independent_approver_identity, self.identity_seed)
        if (not root.is_absolute() or not str(root).startswith("/private/tmp/")
                or ".." in root.parts or any(not value for value in identities)
                or self.operator_identity == self.independent_approver_identity
                or self.environment != "CONTROLLED_NON_PRODUCTION"
                or self.production_authorized or self.branch != BRANCH
                or self.commit != COMMIT):
            raise BootstrapEvidenceRecoveryError("CONTROLLED_EVIDENCE_INPUT_REJECTED")
        object.__setattr__(self, "root", root)


@dataclass(frozen=True, slots=True)
class ControlledEvidenceResult:
    evidence_directory: Path
    trusted_binding: TrustedBootstrapEvidenceBinding
    receipt: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt", dict(self.receipt))

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_directory": str(self.evidence_directory),
            "trusted_binding": self.trusted_binding.as_dict(),
            "receipt": dict(self.receipt),
            "production_authorized": False,
        }


class ControlledBootstrapEvidenceGenerator:
    """Writes one owned canonical evidence set below ``/private/tmp``."""

    ARTIFACTS = (
        "approval-input.json", "shared-parent-preflight.json",
        "live-bootstrap-request.json", "activation-authorization-request.json",
        "activation-authorization-evidence.json", "activation-authorization.json",
        "operational-permit.json", "permit-issuance-evidence.json",
        "operational-permit.json.claim.json", "bootstrap-receipt.json",
        "bootstrap-evidence.json", "post-bootstrap-validation.json",
        "source-human-attestation.json", "source-shared-parent-observation.json",
    )

    def generate(self, specification: ControlledEvidenceInput) -> ControlledEvidenceResult:
        root = specification.root
        if root.exists() or root.is_symlink():
            raise BootstrapEvidenceRecoveryError("EVIDENCE_DESTINATION_CONFLICT")
        try:
            root.mkdir(mode=0o700)
            values, binding = self._values(specification)
            if set(values) != set(self.ARTIFACTS):
                raise BootstrapEvidenceRecoveryError("EVIDENCE_OUTPUT_INCOMPLETE")
            for name in self.ARTIFACTS:
                path = root / name
                path.write_bytes(canonical_json_bytes(values[name]))
                os.chmod(path, 0o600)
            if ({path.name for path in root.iterdir()} != set(self.ARTIFACTS)
                    or any(path.is_symlink() or not path.is_file()
                           for path in root.iterdir())):
                raise BootstrapEvidenceRecoveryError("EVIDENCE_OUTPUT_INCOMPLETE")
            return ControlledEvidenceResult(root, binding, values["bootstrap-receipt.json"])
        except Exception:
            if root.exists() and root.is_dir() and not root.is_symlink():
                shutil.rmtree(root)
            raise

    @staticmethod
    def _values(spec: ControlledEvidenceInput) -> tuple[dict[str, dict[str, Any]], TrustedBootstrapEvidenceBinding]:
        digest = lambda label: canonical_digest({"identity_seed": spec.identity_seed, "label": label})
        request_id = "test-infra-02-request-" + digest("request")[7:23]
        typed_acknowledgements = []
        for index in range(12):
            restriction = "warnings-427" if index == 0 else f"restriction-{index:02d}"
            for role in (spec.operator_identity, spec.independent_approver_identity):
                item = ControlledRestrictionAcknowledgement(
                    restriction, role, digest(f"ack-{index}-{role}"),
                    digest(f"restriction-{index}"), spec.branch, spec.commit, request_id)
                typed_acknowledgements.append(item)
        acknowledgements = [item.as_dict() for item in sorted(typed_acknowledgements)]
        ack_digests = sorted(item["acknowledgement_digest"] for item in acknowledgements)
        warning = sorted(item["acknowledgement_digest"] for item in acknowledgements
                         if item["restriction_identifier"] == "warnings-427")
        trusted_root = "controlled-operational-root:" + digest("root")[7:39]
        approval = {
            "branch": spec.branch, "commit": spec.commit,
            "requester_identity": spec.requester_identity,
            "operator_identity": spec.operator_identity,
            "independent_approver_identity": spec.independent_approver_identity,
            "production_authorized": False, "status": "APPROVED",
        }
        preflight = {"branch": spec.branch, "commit": spec.commit,
                     "status": "READY_WITH_RESTRICTIONS", "ubuntu_participation": False,
                     "trusted_operational_root": trusted_root}
        request = {
            "branch": spec.branch, "commit": spec.commit, "maximum_uses": 1,
            "trusted_operational_root": trusted_root,
            "restriction_acknowledgements": acknowledgements,
            "restriction_acknowledgement_digests": ack_digests,
            "production_authorized": False, "writers_authorized": False,
            "monitoring_authorized": False, "external_dispatch_authorized": False,
        }
        auth_request = {"environment": spec.environment, "request_id": request_id,
                        "production_authorized": False}
        authorization_id = "test-infra-02-authorization-" + digest("authorization-id")[7:39]
        authorization_content = {"authorization_id": authorization_id,
                                 "request": auth_request, "status": "AUTHORIZED"}
        authorization_digest = canonical_digest(authorization_content)
        authorization = {**authorization_content, "authorization_digest": authorization_digest}
        permit_id = "test-infra-02-permit-" + digest("permit-id")[7:39]
        permit_content = {
            "branch": spec.branch, "commit": spec.commit, "permit_id": permit_id,
            "issued_at": "2026-07-30T12:02:00+00:00",
            "not_before": "2026-07-30T12:00:00+00:00",
            "bootstrap_execution_deadline": "2026-07-30T13:00:00+00:00",
            "expires_at": "2026-07-30T14:00:00+00:00",
            "warning_acknowledgements": warning,
            "full_restriction_acknowledgement_digest": canonical_digest(acknowledgements),
            "production_authorized": False, "writers_authorized": False,
            "monitoring_authorized": False, "external_dispatch_authorized": False,
        }
        permit_digest = canonical_digest(permit_content)
        permit = {**permit_content, "permit_digest": permit_digest}
        claim = {"branch": spec.branch, "commit": spec.commit, "permit_id": permit_id,
                 "permit_digest": permit_digest, "claimed_at": "2026-07-30T12:03:00+00:00",
                 "production_authorized": False}
        claim_digest = canonical_digest(claim)
        claim_id = "m3-a4b2b2a-claim-" + claim_digest[7:39]
        steps = [{"sequence": index, "code": code, "complete": True,
                  "evidence_digest": digest(f"step-{index}")}
                 for index, code in enumerate(RUNTIME_STEP_CODES, 1)]
        receipt = {"branch": spec.branch, "commit": spec.commit,
                   "permit_id": permit_id, "claim_id": claim_id, "status": "COMPLETE",
                   "findings": [], "step_receipts": steps,
                   "completed_at": "2026-07-30T12:04:00+00:00",
                   "production_authorized": False, "writers_activated": False,
                   "monitoring_activated": False, "external_dispatch_activated": False}
        receipt_digest = canonical_digest(receipt)
        plan_digest = OperationalBootstrapRuntimePlan.build().plan_digest
        evidence_content = {"receipt_digest": receipt_digest,
                            "claim_digest": claim_digest, "plan_digest": plan_digest}
        evidence_digest = canonical_digest(evidence_content)
        bundle = {**evidence_content, "evidence_digest": evidence_digest,
                  "bundle_id": "m3-a4b2b2a-evidence-" + evidence_digest[7:39]}
        post = {"activation_authorization_id": authorization_id, "permit_id": permit_id,
                "claim_id": claim_id, "status": "COMPLETE", "findings": [],
                "checks": [{"code": "CONTROLLED_OUTPUT", "passed": True}],
                "production_authorized": False}
        values = {
            "approval-input.json": approval, "shared-parent-preflight.json": preflight,
            "live-bootstrap-request.json": request,
            "activation-authorization-request.json": auth_request,
            "activation-authorization-evidence.json": {
                "decision_id": authorization_id,
                "request_digest": canonical_digest(auth_request), "status": "AUTHORIZED"},
            "activation-authorization.json": authorization,
            "operational-permit.json": permit,
            "permit-issuance-evidence.json": {"permit_digest": permit_digest,
                                               "permit_id": permit_id},
            "operational-permit.json.claim.json": claim,
            "bootstrap-receipt.json": receipt, "bootstrap-evidence.json": bundle,
            "post-bootstrap-validation.json": post,
            "source-human-attestation.json": {"synthetic": True, "production_authorized": False},
            "source-shared-parent-observation.json": {"synthetic": True,
                                                       "production_authorized": False},
        }
        binding = TrustedBootstrapEvidenceBinding(
            spec.requester_identity, spec.operator_identity,
            spec.independent_approver_identity, authorization_id,
            authorization_digest, permit_id, permit_digest, claim_id, claim_digest)
        return values, binding
