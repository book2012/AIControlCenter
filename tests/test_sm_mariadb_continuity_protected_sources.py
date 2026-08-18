import ast
import os
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_protected_sources import (
    ProtectedSourceObservation,
    ProtectedSourceReason,
    observe_fixed_protected_source,
)


PRODUCTION = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_protected_sources.py"


def make_slot(tmp_path: Path, *, parent_mode: int = 0o700, leaf_mode: int = 0o600, data: bytes = b"x") -> Path:
    parent = tmp_path / "protected"
    parent.mkdir()
    leaf = parent / "fixed-slot"
    leaf.write_bytes(data)
    leaf.chmod(leaf_mode)
    parent.chmod(parent_mode)
    return leaf


def observe(slot: Path, *, uid: int | None = None, gid: int | None = None):
    return observe_fixed_protected_source(
        slot,
        expected_uid=os.getuid() if uid is None else uid,
        expected_gid=os.getgid() if gid is None else gid,
    )


def test_accepts_deterministic_safe_metadata(tmp_path: Path) -> None:
    slot = make_slot(tmp_path)
    assert oct(slot.parent.stat().st_mode & 0o777) == "0o700"
    assert oct(slot.stat().st_mode & 0o777) == "0o600"
    assert observe(slot).acceptable is True


@pytest.mark.parametrize("mode", [0o600, 0o710, 0o755])
def test_parent_requires_exact_0700(tmp_path: Path, mode: int) -> None:
    slot = make_slot(tmp_path, parent_mode=mode)
    assert observe(slot).reason is ProtectedSourceReason.PROTECTED_PARENT_UNSAFE


@pytest.mark.parametrize("mode", [0o601, 0o640, 0o666])
def test_leaf_rejects_permissions_exceeding_0600(tmp_path: Path, mode: int) -> None:
    slot = make_slot(tmp_path, leaf_mode=mode)
    assert observe(slot).reason is ProtectedSourceReason.LEAF_UNSAFE


def test_parent_and_leaf_symlinks_are_rejected(tmp_path: Path) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    real_parent.chmod(0o700)
    real_leaf = real_parent / "fixed-slot"
    real_leaf.write_bytes(b"x")
    real_leaf.chmod(0o600)
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    assert observe_fixed_protected_source(linked_parent / "fixed-slot", expected_uid=os.getuid(), expected_gid=os.getgid()).reason is ProtectedSourceReason.PROTECTED_PARENT_UNSAFE
    linked_leaf = real_parent / "linked-slot"
    linked_leaf.symlink_to(real_leaf)
    assert observe_fixed_protected_source(linked_leaf, expected_uid=os.getuid(), expected_gid=os.getgid()).reason is ProtectedSourceReason.LEAF_UNSAFE


def test_leaf_wrong_ownership_missing_and_empty_are_rejected(tmp_path: Path) -> None:
    slot = make_slot(tmp_path)
    metadata = os.lstat(slot)
    assert observe(slot, uid=metadata.st_uid + 1).reason is ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH
    assert observe(slot, gid=metadata.st_gid + 1).reason is ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH
    missing = slot.parent / "missing"
    assert observe_fixed_protected_source(missing, expected_uid=os.getuid(), expected_gid=os.getgid()).reason is ProtectedSourceReason.LEAF_MISSING
    slot.write_bytes(b"")
    slot.chmod(0o600)
    assert observe(slot).reason is ProtectedSourceReason.LEAF_EMPTY


def test_missing_parent_and_parent_ownership_are_rejected(tmp_path: Path) -> None:
    missing = tmp_path / "missing-parent" / "fixed-slot"
    assert observe(missing).reason is ProtectedSourceReason.PROTECTED_PARENT_MISSING
    slot = make_slot(tmp_path)
    parent = os.lstat(slot.parent)
    assert observe(slot, uid=parent.st_uid + 1).reason is ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH
    assert observe(slot, gid=parent.st_gid + 1).reason is ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH


def test_leaf_uid_and_gid_mismatch_after_valid_parent_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slot = make_slot(tmp_path)
    real_lstat = os.lstat

    def mismatched_uid(path: object):
        result = real_lstat(path)
        if Path(path) == slot:
            values = list(result)
            values[4] += 1
            return os.stat_result(values)
        return result

    monkeypatch.setattr(os, "lstat", mismatched_uid)
    assert observe(slot).reason is ProtectedSourceReason.LEAF_OWNERSHIP_MISMATCH

    def mismatched_gid(path: object):
        result = real_lstat(path)
        if Path(path) == slot:
            values = list(result)
            values[5] += 1
            return os.stat_result(values)
        return result

    monkeypatch.setattr(os, "lstat", mismatched_gid)
    assert observe(slot).reason is ProtectedSourceReason.LEAF_OWNERSHIP_MISMATCH


def test_closed_reason_and_contradictory_direct_construction_are_rejected() -> None:
    assert tuple(reason.value for reason in ProtectedSourceReason) == (
        "PROTECTED_PARENT_MISSING", "PROTECTED_PARENT_UNSAFE",
        "PROTECTED_PARENT_OWNERSHIP_MISMATCH", "LEAF_MISSING", "LEAF_UNSAFE",
        "LEAF_OWNERSHIP_MISMATCH", "LEAF_EMPTY", "ACCEPTABLE",
    )
    with pytest.raises(TypeError):
        ProtectedSourceObservation("ACCEPTABLE", True, True, True, True, True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ProtectedSourceObservation(ProtectedSourceReason.ACCEPTABLE, True, False, True, True, True)
    with pytest.raises(ValueError):
        ProtectedSourceObservation(ProtectedSourceReason.ACCEPTABLE, True, True, False, True, True)
    with pytest.raises(ValueError):
        ProtectedSourceObservation(ProtectedSourceReason.LEAF_EMPTY, True, True, True, True, True)


def test_acceptable_is_derived_and_projection_is_zero_authority(tmp_path: Path) -> None:
    observation = observe(make_slot(tmp_path))
    assert "acceptable" not in __import__("inspect").signature(ProtectedSourceObservation).parameters
    assert observation.acceptable is True
    projection = observation.to_projection()
    assert projection["value_free"] is True
    for name in (
        "authorization_authority", "capability_authority", "execution_authority",
        "mutation_authority", "retry_authority", "reconnect_authority",
        "rollback_authority",
    ):
        assert projection[name] is False


def test_implementation_is_metadata_only_and_has_no_discovery_or_fallback() -> None:
    tree = ast.parse(PRODUCTION.read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    called_attributes = {node.func.attr for node in calls if isinstance(node.func, ast.Attribute)}
    called_names = {node.func.id for node in calls if isinstance(node.func, ast.Name)}
    assert not ({"open", "read_text", "read_bytes", "iterdir", "glob", "rglob", "walk", "listdir", "scandir"} & (called_attributes | called_names))
    assert "fallback" not in PRODUCTION.read_text().lower()
    assert "candidate" not in PRODUCTION.read_text().lower()
