from __future__ import annotations

from core.deployment.bootstrap_evidence_recovery import (
    BootstrapEvidenceRecoveryConfig,
    BootstrapEvidenceRecoveryValidator,
)


def test_retained_snapshot_is_immutable_and_sqlite_sidecars_are_confined(
    sqlite_snapshot_workspace,
):
    retained = sqlite_snapshot_workspace.retained
    retained_before = (
        retained.operational_state,
        retained.evidence_state,
    )
    report = BootstrapEvidenceRecoveryValidator(
        BootstrapEvidenceRecoveryConfig(
            sqlite_snapshot_workspace.operational,
            sqlite_snapshot_workspace.evidence,
            sqlite_snapshot_workspace.recovery,
            sqlite_snapshot_workspace.trusted_binding,
        )
    ).validate()

    assert report["source_immutability"] is True
    retained.assert_unchanged()
    assert retained_before == (
        retained.operational_state,
        retained.evidence_state,
    )
    inspection_roots = {
        sqlite_snapshot_workspace.recovery / "audit-inspection",
        sqlite_snapshot_workspace.recovery / "replay-inspection",
    }
    assert all(path.is_dir() for path in inspection_roots)
    assert sqlite_snapshot_workspace.sqlite_sidecars()
    assert all(
        path.is_relative_to(sqlite_snapshot_workspace.root)
        for path in sqlite_snapshot_workspace.sqlite_sidecars()
    )
    assert sqlite_snapshot_workspace.operational != retained.operational
    assert sqlite_snapshot_workspace.evidence != retained.evidence
    assert sqlite_snapshot_workspace.root.is_relative_to(retained.recovery_work)
