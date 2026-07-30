from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.deployment.operational_bootstrap_live import (
    AtomicControlledOperationalArtifactWriter,
    ControlledLivePermitResult,
    ControlledLivePermitService,
    ControlledOperationalBootstrapArtifactPaths,
    ControlledOperationalBootstrapError,
    ControlledOperationalBootstrapOrchestrator,
    ControlledOperationalBootstrapRequest,
    ControlledOperationalBootstrapScope,
    ControlledOperationalBootstrapTimePolicy,
    StrictControlledOperationalPreflightArtifactReader,
    canonical_digest,
    canonical_json,
)
from core.deployment.operational_bootstrap_execution import (
    MacOperationalBootstrapRuntimeAdapter,
)

COMMIT = "aebaefe5153b56ba74fb78980cc02b2603a9c4e5"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
NOW = "2026-07-30T12:02:00+09:00"


def request(tmp_path: Path) -> ControlledOperationalBootstrapRequest:
    evidence = tmp_path / "evidence"
    permit = evidence / "permit.json"
    return ControlledOperationalBootstrapRequest(
        request_id="m3-a4b2b2b-r4-test-request",
        branch="feature/deployment-package",
        commit=COMMIT,
        trusted_operational_root=(
            tmp_path / "home/Library/Application Support/AIControlCenter"),
        requester_identity="test:requester:r4",
        operator_identity="test:operator:r4",
        independent_approver_identity="test:approver:r4",
        artifacts=ControlledOperationalBootstrapArtifactPaths(
            evidence / "approval.json", evidence / "preflight.json",
            evidence / "activation-request.json", evidence / "activation.json",
            evidence / "activation-evidence.json", permit,
            evidence / "issuance.json", evidence / "permit.json.claim.json",
            evidence / "receipt.json", evidence / "bootstrap-evidence.json",
            evidence / "validation.json"),
        time_policy=ControlledOperationalBootstrapTimePolicy(
            "2026-07-30T12:00:00+09:00", 3600,
            "2026-07-30T12:00:00+09:00", "2026-07-30T13:00:00+09:00",
            "2026-07-30T12:01:00+09:00", "2026-07-30T12:59:00+09:00",
            "2026-07-30T12:30:00+09:00"),
        restriction_acknowledgement_digests=(DIGEST_A, DIGEST_B),
        active_restriction_digests=(DIGEST_A,),
        scope=ControlledOperationalBootstrapScope.CONTROLLED_NON_PRODUCTION)


def preflight(tmp_path: Path, **changes) -> Path:
    value = {
        "status": "PASS", "branch": "feature/deployment-package",
        "commit": COMMIT,
        "trusted_operational_root": str(
            tmp_path / "home/Library/Application Support/AIControlCenter"),
        "managed_targets_absent": True,
        "shared_parent_digest": DIGEST_A,
        "ubuntu_participation": False,
    }
    value.update(changes)
    path = tmp_path / "preflight.json"
    path.write_text(canonical_json(value), encoding="utf-8")
    return path


def issued_permit(tmp_path: Path, **changes) -> ControlledLivePermitResult:
    req = request(tmp_path)
    values = {
        "permit_id": "m3-a4b2b2b-r4-test-permit",
        "branch": req.branch, "commit": req.commit,
        "requester_identity": req.requester_identity,
        "operator_identity": req.operator_identity,
        "approver_identity": req.independent_approver_identity,
        "issued_at": "2026-07-30T12:02:00+09:00",
        "not_before": req.time_policy.permit_not_before,
        "expires_at": req.time_policy.permit_expires_at,
        "bootstrap_execution_deadline":
            req.time_policy.bootstrap_execution_deadline,
        "maximum_uses": 1, "claimed": False,
        "environment": "CONTROLLED_NON_PRODUCTION",
        "warning_acknowledgements": (DIGEST_A, DIGEST_B),
        "readiness_report_digest": DIGEST_A,
        "preflight_report_digest": DIGEST_A,
        "schema_binding_digest": DIGEST_A,
        "target_binding_digest": DIGEST_A,
        "plan_binding_digest": DIGEST_A,
        "bootstrap_authorized": True,
        "writers_authorized": False,
        "monitoring_authorized": False,
        "external_dispatch_authorized": False,
        "production_authorized": False,
    }
    values.update(changes)
    return ControlledLivePermitResult.issue(**values)


def test_exact_ubuntu_participation_false_is_accepted_and_canonical(tmp_path):
    path = preflight(tmp_path)
    result = StrictControlledOperationalPreflightArtifactReader().read(path)
    assert result["ubuntu_participation"] is False
    assert path.read_text(encoding="utf-8") == canonical_json(result)


@pytest.mark.parametrize("value", [True, None, "false", 0, [], {}])
def test_invalid_ubuntu_participation_values_are_rejected(tmp_path, value):
    with pytest.raises(
            ControlledOperationalBootstrapError,
            match="UBUNTU_PARTICIPATION_MUST_BE_FALSE"):
        StrictControlledOperationalPreflightArtifactReader().read(
            preflight(tmp_path, ubuntu_participation=value))


def test_missing_ubuntu_participation_is_rejected(tmp_path):
    path = preflight(tmp_path)
    value = json.loads(path.read_text())
    value.pop("ubuntu_participation")
    path.write_text(canonical_json(value))
    with pytest.raises(ControlledOperationalBootstrapError):
        StrictControlledOperationalPreflightArtifactReader().read(path)


@pytest.mark.parametrize("field,value", [
    ("ubuntu", False), ("ubuntu_runtime", False), ("ubuntu_host", "disabled"),
    ("ubuntu_command", False), ("ubuntu_worker", False),
    ("ubuntu_destination", False), ("host", "Darwin"), ("command", False),
    ("destination", False), ("environment", "test"),
    ("production_authorized", False),
])
def test_other_unsafe_fields_remain_rejected(tmp_path, field, value):
    with pytest.raises(ControlledOperationalBootstrapError):
        StrictControlledOperationalPreflightArtifactReader().read(
            preflight(tmp_path, **{field: value}))


def test_nested_ubuntu_field_is_rejected(tmp_path):
    with pytest.raises(
            ControlledOperationalBootstrapError, match="UNSAFE_FIELD_REJECTED"):
        StrictControlledOperationalPreflightArtifactReader().read(
            preflight(tmp_path, evidence={"ubuntu_participation": False}))


def test_permit_service_returns_immutable_typed_deterministic_result(tmp_path):
    req = request(tmp_path)
    service = ControlledLivePermitService()
    first, evidence = service.issue(
        request=req, approval={"status": "APPROVED"},
        activation_authorization=object(), now=NOW)
    second, _ = service.issue(
        request=req, approval={"status": "APPROVED"},
        activation_authorization=object(), now=NOW)
    assert isinstance(first, ControlledLivePermitResult)
    assert first == second
    assert first.as_dict() == second.as_dict()
    assert first.permit_digest == canonical_digest(first.content())
    assert evidence == {
        "permit_id": first.permit_id, "permit_digest": first.permit_digest}
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.maximum_uses = 2


@pytest.mark.parametrize("changes", [
    {"maximum_uses": 2},
    {"production_authorized": True},
    {"environment": "PRODUCTION"},
    {"operator_identity": "root"},
])
def test_invalid_permit_scope_is_rejected(tmp_path, changes):
    with pytest.raises(ControlledOperationalBootstrapError):
        issued_permit(tmp_path, **changes)


def test_permit_binding_expiry_and_tamper_are_rejected(tmp_path):
    req = request(tmp_path)
    issued_permit(tmp_path).validate_for(req, NOW)
    for changes, code in (
        ({"commit": "0" * 40}, "GIT_BINDING"),
        ({"requester_identity": "test:other:r4"}, "IDENTITY_BINDING"),
    ):
        permit = issued_permit(tmp_path, **changes)
        with pytest.raises(ControlledOperationalBootstrapError, match=code):
            permit.validate_for(req, NOW)
    with pytest.raises(ControlledOperationalBootstrapError, match="EXPIRED"):
        issued_permit(tmp_path).validate_for(
            req, "2026-07-30T13:01:00+09:00")
    value = issued_permit(tmp_path).as_dict()
    value["permit_digest"] = DIGEST_B
    with pytest.raises(
            ControlledOperationalBootstrapError, match="DIGEST_INVALID"):
        ControlledLivePermitResult(**value)


class _Reader:
    def __init__(self, value):
        self.value = value

    def read(self, _path):
        return self.value


class _Clock:
    def now(self):
        return NOW


class _Activation:
    authorization_id = "test-r4-activation"
    authorization_digest = DIGEST_A

    def as_dict(self):
        return {"authorization_id": self.authorization_id,
                "authorization_digest": self.authorization_digest}


class _ActivationRequest:
    def as_dict(self):
        return {"request_id": "test-r4-activation-request"}


class _ActivationService:
    def authorize(self, **_kwargs):
        return _ActivationRequest(), _Activation(), {"status": "AUTHORIZED"}


class _Host:
    def collect(self):
        return {}

    def runtime_evidence(self):
        return object()

    def target_evidence(self):
        return object()


class _Execution:
    def execute(self, **_kwargs):
        receipt = SimpleNamespace(
            claim_id="test-r4-claim", receipt_id="test-r4-receipt",
            as_dict=lambda: {"receipt_id": "test-r4-receipt"})
        return SimpleNamespace(
            bundle_id="test-r4-bundle", receipt=receipt,
            receipt_digest=DIGEST_A, claim_digest=DIGEST_A,
            plan_digest=DIGEST_A, evidence_digest=DIGEST_A)


class _PermitService:
    def __init__(self, result):
        self.result = result

    def issue(self, **_kwargs):
        if isinstance(self.result, ControlledLivePermitResult):
            return self.result, {
                "permit_id": self.result.permit_id,
                "permit_digest": self.result.permit_digest}
        return self.result, {}


def orchestrator(tmp_path, permit):
    return ControlledOperationalBootstrapOrchestrator(
        approval_reader=_Reader({}), preflight_reader=_Reader({}),
        artifact_writer=AtomicControlledOperationalArtifactWriter(),
        git_evidence=SimpleNamespace(collect=lambda: None),
        host_evidence=_Host(), clock=_Clock(),
        activation_service=_ActivationService(),
        permit_service=_PermitService(permit),
        execution_coordinator=_Execution(),
        runtime_adapter=MacOperationalBootstrapRuntimeAdapter())


def test_orchestrator_rejects_plain_mapping_at_typed_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.deployment.operational_bootstrap_live.coordinator."
        "ControlledOperationalBootstrapArtifactValidator.validate",
        lambda self, **kwargs: None)
    with pytest.raises(
            ControlledOperationalBootstrapError, match="TYPED_LIVE_PERMIT_REQUIRED"):
        orchestrator(tmp_path, {"permit_id": "arbitrary"}).execute(request(tmp_path))


def test_orchestrator_serializes_typed_permit_and_reaches_coordinator(
        tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.deployment.operational_bootstrap_live.coordinator."
        "ControlledOperationalBootstrapArtifactValidator.validate",
        lambda self, **kwargs: None)
    req = request(tmp_path)
    result = orchestrator(tmp_path, issued_permit(tmp_path)).execute(req)
    serialized = json.loads(req.artifacts.operational_permit_output.read_text())
    assert serialized == issued_permit(tmp_path).as_dict()
    assert result.status.value == "COMPLETE"
    assert result.claim_id == "test-r4-claim"
    assert not result.production_authorized
    actual = Path.home() / "Library/Application Support/AIControlCenter"
    assert not str(req.trusted_operational_root).startswith(str(actual))
