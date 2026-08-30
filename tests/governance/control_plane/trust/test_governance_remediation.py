from dataclasses import FrozenInstanceError, fields

import pytest

from core.governance.control_plane.trust.governance_remediation import (
    GovernanceRemediationPlan, RemediationEligibility as E, RemediationPostcondition,
    plan_governance_remediation, validate_governance_remediation_plan,
    validate_remediation_postcondition,
)
from core.governance.control_plane.trust.pre_bootstrap_filesystem import (
    ExistingObjectKind as K, FilesystemObservation as O, GovernedPath as P,
    PreBootstrapFilesystemPlan as F, TrustedFilesystemIdentity as I,
)

IDENTITY = I(501, 20, "/Users/operator")
FS_PLAN = F(IDENTITY, "/Users/operator/Library/Application Support/AIControlCenter/governance",
            "/Users/operator/Library/Application Support/AIControlCenter/governance/trust")


def observed(**overrides):
    values = dict(path=P.GOVERNANCE, object_kind=K.DIRECTORY, uid=501, gid=20,
                  mode=0o755, descriptor_identity_proven=True)
    values.update(overrides)
    return O(**values)


def test_exact_0755_shape_produces_only_exact_immutable_plan():
    decision = plan_governance_remediation(FS_PLAN, observed())
    assert decision.eligibility is E.ELIGIBLE
    assert decision.plan.target == FS_PLAN.governance_path
    assert (decision.plan.observed_mode, decision.plan.required_mode) == (0o755, 0o700)
    assert (decision.plan.owner_uid, decision.plan.owner_gid) == (501, 20)
    assert [field.name for field in fields(GovernanceRemediationPlan)] == [
        "target", "observed_mode", "required_mode", "owner_uid", "owner_gid", "operation"
    ]
    with pytest.raises(FrozenInstanceError): decision.plan.required_mode = 0o777
    assert not hasattr(decision.plan, "retry") and not hasattr(decision.plan, "chown")


@pytest.mark.parametrize("mode,eligibility", [(0o700, E.NOT_REQUIRED), (0o750, E.DENIED), (0o775, E.DENIED)])
def test_other_modes_are_not_eligible(mode, eligibility):
    assert plan_governance_remediation(FS_PLAN, observed(mode=mode)).eligibility is eligibility


@pytest.mark.parametrize("changes", [
    {"uid": 502}, {"gid": 21}, {"object_kind": K.SYMLINK}, {"object_kind": K.OTHER},
    {"descriptor_identity_proven": False}, {"observation_complete": False}, {"path": P.TRUST},
])
def test_every_non_exact_shape_denied(changes):
    assert plan_governance_remediation(FS_PLAN, observed(**changes)).eligibility is E.DENIED


def test_planner_has_no_arbitrary_path_mode_or_identity_inputs():
    with pytest.raises(TypeError):
        plan_governance_remediation(FS_PLAN, observed(), path="/tmp", mode=0o777, uid=0, gid=0)
    forged = F(IDENTITY, "/tmp/governance", "/tmp/governance/trust")
    assert plan_governance_remediation(forged, observed()).eligibility is E.DENIED


@pytest.mark.parametrize("changes", [
    {"target": "/tmp/governance"}, {"observed_mode": 0o750},
    {"required_mode": 0o777}, {"owner_uid": 0}, {"owner_gid": 0},
])
def test_plan_validator_denies_arbitrary_target_mode_and_identity(changes):
    values = dict(target=FS_PLAN.governance_path, observed_mode=0o755,
                  required_mode=0o700, owner_uid=501, owner_gid=20)
    values.update(changes)
    assert not validate_governance_remediation_plan(FS_PLAN, GovernanceRemediationPlan(**values))


def test_plan_validator_accepts_only_the_exact_fixed_plan():
    assert validate_governance_remediation_plan(
        FS_PLAN, GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o700, 501, 20)
    )


def test_postcondition_requires_exact_safe_governance_state():
    assert validate_remediation_postcondition(FS_PLAN, RemediationPostcondition(observed(mode=0o700)))
    assert not validate_remediation_postcondition(FS_PLAN, RemediationPostcondition(observed()))
    assert not validate_remediation_postcondition(FS_PLAN, RemediationPostcondition(observed(path=P.TRUST, mode=0o700)))
