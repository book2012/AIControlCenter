from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from core.deployment.operational_bootstrap_execution import (
    OperationalBootstrapIssuanceEvidence,
    OperationalBootstrapLivePermitEvidence,
    OperationalBootstrapLivePermitValidator,
    OperationalBootstrapRuntimeMode,
    OperationalBootstrapRuntimeRequest,
)
from core.deployment.operational_bootstrap_live import *

COMMIT = "f67fb970df322d2c84850be094ea56e8134d9c4b"
NOW = "2026-07-30T12:02:00+09:00"


def digest(label: str) -> str:
    return canonical_digest(label)


def request(tmp_path: Path, evidence=None, **changes):
    request_id = "m3-a4b2b2b-r5-test-request"
    restrictions = tuple(
        ("warnings-427" if index == 0 else f"restriction-{index}",
         digest(f"restriction-{index}")) for index in range(9))
    entries = tuple(
        ControlledRestrictionAcknowledgement(
            restriction_id, identity, digest(f"ack-{restriction_id}-{identity}"),
            restriction_digest, "feature/deployment-package", COMMIT, request_id)
        for restriction_id, restriction_digest in restrictions
        for identity in ("test:operator:r5", "test:approver:r5"))
    if evidence is not None:
        entries = tuple(evidence)
    root = tmp_path / "evidence"
    permit = root / "permit.json"
    values = dict(
        request_id=request_id, branch="feature/deployment-package", commit=COMMIT,
        trusted_operational_root=tmp_path / "home/Library/Application Support/AIControlCenter",
        requester_identity="test:requester:r5",
        operator_identity="test:operator:r5",
        independent_approver_identity="test:approver:r5",
        artifacts=ControlledOperationalBootstrapArtifactPaths(
            root / "approval.json", root / "preflight.json",
            root / "activation-request.json", root / "activation.json",
            root / "activation-evidence.json", permit, root / "issuance.json",
            root / "permit.json.claim.json", root / "receipt.json",
            root / "bootstrap-evidence.json", root / "validation.json"),
        time_policy=ControlledOperationalBootstrapTimePolicy(
            "2026-07-30T12:00:00+09:00", 3600,
            "2026-07-30T12:00:00+09:00", "2026-07-30T13:00:00+09:00",
            "2026-07-30T12:01:00+09:00", "2026-07-30T12:59:00+09:00",
            "2026-07-30T12:30:00+09:00"),
        restriction_acknowledgement_digests=tuple(
            item.acknowledgement_digest for item in entries),
        active_restriction_digests=tuple(
            sorted({item.restriction_digest for item in entries})),
        scope=ControlledOperationalBootstrapScope.CONTROLLED_NON_PRODUCTION,
        restriction_acknowledgements=entries)
    values.update(changes)
    return ControlledOperationalBootstrapRequest(**values)


def projection(req):
    return ControlledWarningAcknowledgementProjector().project(
        evidence=req.restriction_acknowledgements, request=req)


def compatibility(req):
    return ControlledLivePermitCompatibilityValidator().validate(
        request=req, projection=projection(req))


def issued(req):
    return ControlledLivePermitService().issue(
        request=req, approval={"status": "APPROVED"},
        activation_authorization=object(), now=NOW,
        compatibility_report=compatibility(req))[0]


def test_full_nine_category_dual_evidence_projects_exact_pair_and_is_preserved(tmp_path):
    req = request(tmp_path)
    result = projection(req)
    assert len(result.full_restriction_acknowledgements) == 18
    assert len({item.restriction_identifier
                for item in result.full_restriction_acknowledgements}) == 9
    assert len(result.warning_acknowledgements) == 2
    assert {item.acknowledging_identity for item in result.warning_acknowledgements} == {
        req.operator_identity, req.independent_approver_identity}
    permit = issued(req)
    assert permit.full_restriction_acknowledgement_digest == (
        result.full_restriction_acknowledgement_digest)


def test_projection_and_serialization_are_order_independent(tmp_path):
    req = request(tmp_path)
    reversed_req = request(tmp_path, reversed(req.restriction_acknowledgements))
    assert projection(req) == projection(reversed_req)
    assert issued(req).as_dict() == issued(reversed_req).as_dict()


def test_plain_mapping_at_typed_projection_boundary_is_rejected(tmp_path):
    req = request(tmp_path)
    with pytest.raises(ControlledOperationalBootstrapError,
                       match="TYPED_RESTRICTION"):
        ControlledWarningAcknowledgementProjector().project(
            evidence=({"restriction_identifier": "warnings-427"},), request=req)


@pytest.mark.parametrize("mutation,code", [
    (lambda values: tuple(x for x in values
                          if x.restriction_identifier != "warnings-427"),
     "EVIDENCE_MISSING|EXACT_WARNING"),
    (lambda values: tuple(x for x in values if not (
        x.restriction_identifier == "warnings-427"
        and x.acknowledging_identity == "test:approver:r5")),
     "EXACT_WARNING"),
    (lambda values: values + (next(
        x for x in values if x.restriction_identifier == "warnings-427"),),
     "EXACT_WARNING"),
])
def test_missing_one_entry_and_extra_warning_evidence_rejected(tmp_path, mutation, code):
    req = request(tmp_path)
    changed = mutation(req.restriction_acknowledgements)
    unbound = dataclasses.replace(req, restriction_acknowledgements=())
    with pytest.raises(ControlledOperationalBootstrapError, match=code):
        ControlledWarningAcknowledgementProjector().project(
            evidence=changed, request=unbound)


def test_duplicate_warning_identity_rejected(tmp_path):
    req = request(tmp_path)
    warnings = [x for x in req.restriction_acknowledgements
                if x.restriction_identifier == "warnings-427"]
    duplicate = dataclasses.replace(
        warnings[1], acknowledging_identity=warnings[0].acknowledging_identity)
    evidence = tuple(x for x in req.restriction_acknowledgements
                     if x != warnings[1]) + (duplicate,)
    with pytest.raises(ControlledOperationalBootstrapError, match="DUPLICATE"):
        ControlledWarningAcknowledgementProjector().project(
            evidence=evidence, request=dataclasses.replace(
                req, restriction_acknowledgements=()))


@pytest.mark.parametrize("field,value", [
    ("restriction_identifier", "427_EXISTING_DEPRECATION_WARNINGS"),
    ("branch", "main"), ("commit", "0" * 40),
    ("request_id", "wrong-request"),
])
def test_wrong_semantic_or_request_binding_rejected(tmp_path, field, value):
    req = request(tmp_path)
    item = next(x for x in req.restriction_acknowledgements
                if x.restriction_identifier == "warnings-427")
    if field == "branch":
        with pytest.raises(ControlledOperationalBootstrapError):
            dataclasses.replace(item, **{field: value})
        return
    changed = dataclasses.replace(item, **{field: value})
    evidence = tuple(changed if entry == item else entry
                     for entry in req.restriction_acknowledgements)
    if field == "restriction_identifier":
        with pytest.raises(ControlledOperationalBootstrapError, match="EXACT_WARNING"):
            ControlledWarningAcknowledgementProjector().project(
                evidence=evidence, request=dataclasses.replace(
                    req, restriction_acknowledgements=()))
    else:
        with pytest.raises(ControlledOperationalBootstrapError, match="BINDING"):
            dataclasses.replace(req, restriction_acknowledgements=evidence)


@pytest.mark.parametrize("identity", ["unknown", "unassigned"])
def test_synthetic_or_placeholder_identity_rejected(identity):
    with pytest.raises(ControlledOperationalBootstrapError):
        ControlledRestrictionAcknowledgement(
            "warnings-427", identity, digest("ack"), digest("restriction"),
            "feature/deployment-package", COMMIT, "request",
            synthetic=identity == "unknown", placeholder=identity == "unassigned")


def test_tampering_either_collection_digest_invalidates_permit(tmp_path):
    permit = issued(request(tmp_path)).as_dict()
    for field in ("full_restriction_acknowledgement_digest",
                  "warning_acknowledgement_digest"):
        changed = dict(permit)
        changed[field] = digest("tampered")
        with pytest.raises(ControlledOperationalBootstrapError,
                           match="PERMIT_DIGEST_INVALID"):
            ControlledLivePermitResult(**changed)


def test_executor_accepts_projected_permit_and_rejects_incident_shape(tmp_path):
    req = request(tmp_path)
    permit = issued(req).as_dict()
    runtime = OperationalBootstrapRuntimeRequest(
        req.request_id,
        OperationalBootstrapRuntimeMode.TEST_ONLY_OPERATIONAL_EXECUTION_VALIDATION,
        req.branch, req.commit, req.operator_identity, NOW, NOW,
        req.artifacts.operational_permit_output,
        req.artifacts.permit_issuance_evidence_output,
        req.artifacts.bootstrap_evidence_output.parent, {})
    evidence = {"permit_id": permit["permit_id"],
                "permit_digest": permit["permit_digest"]}
    validator = OperationalBootstrapLivePermitValidator()
    findings = validator.validate(
        live=OperationalBootstrapLivePermitEvidence(
            permit, canonical_json(permit), permit["permit_digest"]),
        issuance=OperationalBootstrapIssuanceEvidence(
            evidence, canonical_json(evidence)), request=runtime)
    assert findings == ()
    incident = dict(permit)
    incident["warning_acknowledgements"] = list(
        req.restriction_acknowledgement_digests)
    unsigned = dict(incident)
    unsigned.pop("permit_digest")
    incident["permit_digest"] = canonical_digest(unsigned)
    evidence = {"permit_id": incident["permit_id"],
                "permit_digest": incident["permit_digest"]}
    findings = validator.validate(
        live=OperationalBootstrapLivePermitEvidence(
            incident, canonical_json(incident), incident["permit_digest"]),
        issuance=OperationalBootstrapIssuanceEvidence(
            evidence, canonical_json(evidence)), request=runtime)
    assert "DUAL_WARNING_ACKNOWLEDGEMENTS_REQUIRED" in {
        item.code for item in findings}


def test_no_first_two_slicing_and_production_remains_unauthorized(tmp_path):
    req = request(tmp_path)
    assert all(item.restriction_identifier != "warnings-427"
               for item in req.restriction_acknowledgements[:2])
    permit = issued(req)
    assert set(permit.warning_acknowledgements) != set(
        req.restriction_acknowledgement_digests[:2])
    assert permit.maximum_uses == 1
    assert not permit.production_authorized
    assert not permit.writers_authorized
    assert not permit.monitoring_authorized
    assert not permit.external_dispatch_authorized
