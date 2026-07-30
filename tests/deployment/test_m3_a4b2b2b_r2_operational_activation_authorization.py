from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from core.deployment.operational_activation_authorization import *
from core.deployment.policy.dependency_boundaries import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
COMMIT = "6" * 40
NOW = "2026-07-30T12:00:00+09:00"
DIGEST = "sha256:" + "a" * 64


def request(tmp_path: Path, **changes):
    value = OperationalActivationAuthorizationRequest(
        "approval-test", DIGEST, "review-test", DIGEST,
        OperationalActivationAuthorizationIdentityBinding(
            "synthetic-requester-r2", "synthetic-operator-r2",
            "synthetic-approver-r2", synthetic=True),
        OperationalActivationAuthorizationRestrictionBinding(
            (DIGEST, "sha256:" + "b" * 64), (DIGEST,)),
        OperationalActivationAuthorizationCommitBinding(
            "feature/deployment-package", COMMIT, True, 0, 0),
        OperationalActivationAuthorizationWindow(
            "2026-07-30T11:00:00+09:00", "2026-07-30T11:30:00+09:00",
            "2026-07-30T13:00:00+09:00"),
        OperationalActivationAuthorizationSafetyBinding(
            {"operational_permits_issued": 0, "live_claims": 0,
             "bootstrap_executions": 0, "production_activations": 0}),
        DIGEST, tmp_path / "Library/Application Support/AIControlCenter",
        DIGEST, DIGEST, {"audit": DIGEST, "replay": DIGEST}, DIGEST)
    return dataclasses.replace(value, **changes)


def build(tmp_path):
    value = request(tmp_path)
    config = OperationalActivationAuthorizationConfig(
        value.git.branch, value.git.commit, value.operational_target_path)
    decision, permit = OperationalActivationAuthorizationCoordinator().build(
        config=config, request=value, decided_at=NOW, issued_at=NOW)
    return config, decision, permit


def test_immutable_deterministic_contracts_and_explicit_stage(tmp_path):
    config, first, permit = build(tmp_path)
    _, second, duplicate = build(tmp_path)
    assert first == second
    assert permit == duplicate
    assert first.status is OperationalActivationAuthorizationStatus.AUTHORIZED
    assert permit.stage is OperationalActivationAuthorizationStage.CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION
    with pytest.raises(dataclasses.FrozenInstanceError):
        permit.authorization_id = "changed"
    with pytest.raises(OperationalActivationAuthorizationError):
        OperationalActivationAuthorizationConfig(
            config.approved_branch, config.approved_commit, config.trusted_operational_path,
            production_authorized=True)


def test_default_deny_tamper_time_commit_identity_and_path(tmp_path):
    config, _, permit = build(tmp_path)
    validator = OperationalActivationAuthorizationValidator()
    assert validator.validate(config=config, permit=None, validated_at=NOW).reason_codes == (
        "ACTIVATION_AUTHORIZATION_REQUIRED",)
    tampered = dataclasses.replace(permit, authorization_digest=DIGEST)
    assert "ACTIVATION_AUTHORIZATION_DIGEST_INVALID" in validator.validate(
        config=config, permit=tampered, validated_at=NOW).reason_codes
    assert "ACTIVATION_AUTHORIZATION_EXPIRED" in validator.validate(
        config=config, permit=permit, validated_at="2026-07-30T13:00:00+09:00").reason_codes
    mismatch = OperationalActivationAuthorizationConfig(
        config.approved_branch, "7" * 40, config.trusted_operational_path)
    assert "GIT_BINDING_MISMATCH" in validator.validate(
        config=mismatch, permit=permit, validated_at=NOW).reason_codes
    assert "IDENTITY_MISMATCH" in validator.validate(
        config=config, permit=permit, validated_at=NOW,
        operator_identity="synthetic-other").reason_codes
    different = OperationalActivationAuthorizationConfig(
        config.approved_branch, config.approved_commit, tmp_path / "other")
    assert "TARGET_PATH_MISMATCH" in validator.validate(
        config=different, permit=permit, validated_at=NOW).reason_codes


@pytest.mark.parametrize("value", [
    "AUTOMATIC", "SELF_APPROVED", "GENERAL_OPERATIONAL", "LIVE_CUSTOMER",
    "PRODUCTION", "CUSTOMER_PRODUCTION", "Ubuntu", "worker",
])
def test_scope_names_rejected(value):
    with pytest.raises(ValueError):
        OperationalActivationAuthorizationScope(value)


def test_security_scope_maximum_use_and_identity_default_deny(tmp_path):
    with pytest.raises(OperationalActivationAuthorizationError):
        OperationalActivationAuthorizationWindow(NOW, NOW, "2026-07-30T13:00:00+09:00", 2)
    with pytest.raises(OperationalActivationAuthorizationError):
        OperationalActivationAuthorizationIdentityBinding("a", "same", "same")
    with pytest.raises(OperationalActivationAuthorizationError):
        OperationalActivationAuthorizationSafetyBinding({"x": 0}, writers_authorized=True)
    with pytest.raises(OperationalActivationAuthorizationError):
        request(tmp_path, human_approval_report_id="api_key")


def test_dependency_boundary_and_forbidden_imports():
    paths = [str(path.relative_to(ROOT)) for path in
             (ROOT / "core/deployment/operational_activation_authorization").glob("*.py")]
    assert validate_dependency_boundaries(
        repository_root=ROOT, paths=paths)["overall_result"] == "PASS"
    source = "\n".join((ROOT / path).read_text() for path in paths)
    for forbidden in ("subprocess", "socket", "requests", "core.api", "core.worker",
                      "UbuntuWorkerClient", "Docker", "n8n", "WordPress", "WooCommerce"):
        assert forbidden not in source
