from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from core.deployment.operational_bootstrap_execution import (
    OperationalBootstrapExecutionError,
    TestOnlyOperationalBootstrapRuntimeAdapter,
)
from tests.deployment.test_m3_a4b2b2a_operational_bootstrap_execution import (
    roots,
    setup_execution,
)


def _shared_parent(home: Path) -> Path:
    return home / "Library" / "Application Support" / "AIControlCenter"


@pytest.mark.parametrize(("mode", "restricted"), [(0o755, True), (0o700, False)])
def test_existing_safe_parent_is_accepted_without_metadata_change(roots, mode, restricted):
    _, home = roots
    parent = _shared_parent(home)
    parent.mkdir(parents=True)
    parent.chmod(mode)
    sibling = parent / "runtime"
    sibling.mkdir(mode=0o751)
    content = sibling / "state.txt"
    content.write_text("preexisting\n", encoding="utf-8")
    before = (parent.stat().st_mode, sibling.stat().st_mode, content.read_bytes())

    coordinator, request, host, target, paths = setup_execution(roots)
    evidence = paths.shared_parent_evidence
    assert evidence.application_state_parent_preexisting
    assert not evidence.application_state_parent_owned_by_bootstrap
    assert evidence.application_state_parent_mode == mode
    assert evidence.application_state_parent_owner_uid == os.getuid()
    assert evidence.existing_unmanaged_sibling_count == 1
    assert bool(evidence.shared_parent_restrictions) is restricted
    coordinator.execute(request=request, host=host, target=target)

    assert (parent.stat().st_mode, sibling.stat().st_mode, content.read_bytes()) == before
    assert stat.S_IMODE(paths.audit_database.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.replay_database.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.monitoring.stat().st_mode) == 0o700
    for file_path in (
        paths.audit_database, paths.replay_database,
        paths.audit_backups / "baseline.sqlite3",
        paths.audit_backups / "baseline.manifest.json",
        paths.replay_backups / "baseline.sqlite3",
        paths.replay_backups / "baseline.manifest.json",
    ):
        assert stat.S_IMODE(file_path.stat().st_mode) == 0o600


def test_absent_parent_is_created_0700(roots):
    coordinator, request, host, target, paths = setup_execution(roots)
    assert not paths.shared_parent_evidence.application_state_parent_preexisting
    assert paths.shared_parent_evidence.application_state_parent_owned_by_bootstrap
    coordinator.execute(request=request, host=host, target=target)
    assert stat.S_IMODE(paths.root.stat().st_mode) == 0o700


@pytest.mark.parametrize("mode", [0o720, 0o702, 0o777])
def test_group_or_world_writable_shared_parent_is_rejected(roots, mode):
    _, home = roots
    parent = _shared_parent(home)
    parent.mkdir(parents=True)
    parent.chmod(mode)
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        setup_execution(roots)
    assert caught.value.code == "SHARED_PARENT_GROUP_WORLD_WRITABLE"


def test_wrong_owner_shared_parent_is_rejected(roots, monkeypatch):
    _, home = roots
    _shared_parent(home).mkdir(parents=True)
    current_uid = os.getuid()
    monkeypatch.setattr(
        "core.deployment.operational_bootstrap_execution.path_policy.os.getuid",
        lambda: current_uid + 1,
    )
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        setup_execution(roots)
    assert caught.value.code == "SHARED_PARENT_OWNER_INVALID"


def test_shared_parent_symlink_is_rejected(roots):
    execution, home = roots
    target = execution / "linked-parent"
    target.mkdir()
    parent = _shared_parent(home)
    parent.parent.mkdir(parents=True)
    parent.symlink_to(target, target_is_directory=True)
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        setup_execution(roots)
    assert caught.value.code == "SYMLINK_PATH_REJECTED"


@pytest.mark.parametrize("managed", ["audit", "security", "monitoring"])
def test_any_existing_managed_subtree_is_rejected(roots, managed):
    _, home = roots
    parent = _shared_parent(home)
    parent.mkdir(parents=True)
    (parent / managed).mkdir()
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        setup_execution(roots)
    assert caught.value.code == "MANAGED_TARGET_ALREADY_EXISTS"


@pytest.mark.parametrize("partial", [
    "audit/audit-ledger.sqlite3",
    "audit/backups/baseline.sqlite3",
    "audit/backups/baseline.manifest.json",
    "security/permit-replay.sqlite3",
    "security/backups/baseline.sqlite3",
])
def test_partial_prior_bootstrap_state_is_rejected(roots, partial):
    _, home = roots
    target = _shared_parent(home) / partial
    target.parent.mkdir(parents=True)
    target.write_text("unknown", encoding="utf-8")
    with pytest.raises(OperationalBootstrapExecutionError) as caught:
        setup_execution(roots)
    assert caught.value.code == "MANAGED_TARGET_ALREADY_EXISTS"


def test_post_claim_cleanup_preserves_shared_parent_and_sibling(roots):
    _, home = roots
    parent = _shared_parent(home)
    parent.mkdir(parents=True)
    sibling = parent / "data"
    sibling.mkdir(mode=0o750)
    marker = sibling / "marker"
    marker.write_bytes(b"unchanged")
    before = (stat.S_IMODE(parent.stat().st_mode),
              stat.S_IMODE(sibling.stat().st_mode), marker.read_bytes())
    adapter = TestOnlyOperationalBootstrapRuntimeAdapter(
        failure_step="BOOTSTRAP_REPLAY_SQLITE_DATABASE")
    coordinator, request, host, target, paths = setup_execution(roots, adapter=adapter)
    with pytest.raises(OperationalBootstrapExecutionError):
        coordinator.execute(request=request, host=host, target=target)
    assert request.permit_path.with_name("permit.json.claim.json").exists()
    assert parent.exists()
    assert not any(path.exists() for path in paths.managed_roots)
    assert (stat.S_IMODE(parent.stat().st_mode),
            stat.S_IMODE(sibling.stat().st_mode), marker.read_bytes()) == before
