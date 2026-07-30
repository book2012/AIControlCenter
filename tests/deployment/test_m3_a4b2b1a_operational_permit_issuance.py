from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.operational_permit_issuance import *
from core.deployment.policy.dependency_boundaries import validate_dependency_boundaries

NOW = "2026-07-30T12:00:00+09:00"
COMMIT = "a" * 40
DIGEST = "sha256:" + "b" * 64


def window(**changes):
    return replace(OperationalPermitExecutionWindow(3600, 900, 300, 1800), **changes)


def config(**changes):
    return replace(OperationalPermitIssuanceConfig(
        "feature/deployment-package", COMMIT, window()), **changes)


def restriction(**changes):
    return replace(OperationalPermitRestrictionReview(
        "warnings-427", "preflight-1", DIGEST, "ACKNOWLEDGED_427_WARNINGS",
        DIGEST, "WARNING", False, "M3-A4B2B1B"), **changes)


def evidence(**changes):
    value = OperationalPermitIssuanceEvidence(
        "evidence-1", NOW, "feature/deployment-package", COMMIT,
        "readiness-1", DIGEST, "READY_WITH_RESTRICTIONS",
        "authorization-closure-1", DIGEST, DIGEST,
        "executor-1", DIGEST, True, True, True, True, True,
        "preflight-1", DIGEST, "READY_WITH_RESTRICTIONS",
        True, True, True, True, True, 1600, 0, 300, 0, True, 0, 0,
        {name: 0 for name in REQUIRED_COUNTERS},
        {name: DIGEST for name in REQUIRED_BINDINGS},
        (restriction(),),
    )
    return replace(value, **changes)


def build(**changes):
    args = {"config": config(), "evidence": evidence(), "evaluated_at": NOW}
    args.update(changes)
    return OperationalPermitIssuanceReviewPackageBuilder().build(**args)


def test_immutable_deterministic_review_package_and_zero_state():
    first = build()
    second = build()
    assert first == second
    assert first.decision is OperationalPermitIssuanceDecision.READY_WITH_RESTRICTIONS
    assert first.review_package_id == second.review_package_id
    assert first.canonical_json == second.canonical_json
    assert len(first.missing_human_approvals) == 12
    assert not first.restrictions[0].acknowledgement_supplied
    assert all(not getattr(first, name) for name in (
        "operational_permit_issued", "permit_claimed", "bootstrap_authorized",
        "bootstrap_executed", "writers_authorized", "monitoring_authorized",
        "external_dispatch_authorized", "production_authorized"))
    assert OperationalPermitIssuanceValidator().validate(first).status is OperationalPermitIssuanceStatus.PASS
    with pytest.raises(FrozenInstanceError):
        first.decision = OperationalPermitIssuanceDecision.BLOCKED


@pytest.mark.parametrize("stage", [
    "PERMIT_ISSUED", "BOOTSTRAP_AUTHORIZED", "OPERATIONAL", "ACTIVE", "LIVE",
    "PRODUCTION", "CUSTOMER_PRODUCTION", "UNKNOWN_PRIVILEGED",
])
def test_privileged_stages_rejected(stage):
    with pytest.raises(OperationalPermitIssuanceError):
        config(stage=stage)


def test_execution_window_and_requests_fail_closed():
    for field, value in (
        ("maximum_permit_ttl_seconds", 0),
        ("maximum_approval_to_issuance_seconds", -1),
        ("maximum_issuance_to_claim_seconds", 2_592_001),
        ("maximum_bootstrap_execution_seconds", 0),
        ("maximum_uses", 2),
        ("environment", "PRODUCTION"),
    ):
        with pytest.raises(OperationalPermitIssuanceError):
            window(**{field: value})
    for field in ("production_authorized", "permit_issuance_requested",
                  "permit_claim_requested", "bootstrap_execution_requested"):
        with pytest.raises(OperationalPermitIssuanceError):
            config(**{field: True})


@pytest.mark.parametrize("change", [
    {"branch": "other"}, {"commit": "c" * 40}, {"git_clean": False},
    {"upstream_ahead": 1}, {"upstream_behind": 1},
    {"full_regression_failed": 1}, {"deployment_tests_failed": 1},
    {"operational_targets_absent": False}, {"filesystem_policy_passed": False},
    {"capacity_passed": False}, {"permission_feasibility_passed": False},
    {"executor_validation_passed": False}, {"ubuntu_participation": True},
])
def test_evidence_failures_are_not_ready(change):
    assert build(evidence=evidence(**change)).decision is OperationalPermitIssuanceDecision.NOT_READY


def test_missing_restriction_binding_and_nonzero_safety_fail_closed():
    assert build(evidence=evidence(restrictions=())).decision is OperationalPermitIssuanceDecision.NOT_READY
    assert build(evidence=evidence(restrictions=(restriction(blocking=True),))).decision is OperationalPermitIssuanceDecision.BLOCKED
    counters = {name: 0 for name in REQUIRED_COUNTERS}
    counters["filesystem_writes"] = 1
    assert build(evidence=evidence(safety_counters=counters)).decision is OperationalPermitIssuanceDecision.NOT_READY
    assert build(evidence=evidence(binding_digests={})).decision is OperationalPermitIssuanceDecision.NOT_READY


def test_adapters_secrets_and_writes_rejected(tmp_path):
    before = tuple(tmp_path.iterdir())
    for name in ("adapter", "persistence_adapter", "filesystem_adapter",
                 "database_adapter", "notification_adapter"):
        with pytest.raises(OperationalPermitIssuanceError):
            build(**{name: object()})
    with pytest.raises(OperationalPermitIssuanceError):
        evidence(binding_digests={"api_key": DIGEST})
    assert tuple(tmp_path.iterdir()) == before


def test_dependency_policy_passes_and_forbidden_dependencies_are_absent():
    root = Path(__file__).parents[2]
    paths = [str(path.relative_to(root)) for path in
             (root / "core/deployment/operational_permit_issuance").glob("*.py")]
    report = validate_dependency_boundaries(repository_root=root, paths=paths)
    assert report["overall_result"] == "PASS"
    source = "\n".join((root / path).read_text() for path in paths)
    for forbidden in ("subprocess", "socket", "requests", "core.api", "core.worker",
                      "UbuntuWorkerClient", "sqlite3"):
        assert forbidden not in source
