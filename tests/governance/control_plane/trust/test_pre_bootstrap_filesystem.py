from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import inspect

import pytest

from core.governance.control_plane.trust.pre_bootstrap_filesystem import (
    ExistingObjectKind, FilesystemClassification as C, FilesystemContractError,
    FilesystemObservation as O, GovernedPath as P, TrustedFilesystemIdentity as I,
    _plan_pre_bootstrap_filesystem, classify_governed_directory,
    observe_pre_bootstrap_filesystem, plan_pre_bootstrap_filesystem,
)
import core.governance.control_plane.trust.pre_bootstrap_filesystem as filesystem


IDENTITY = I(501, 20, "/Users/operator")


def observation(**overrides):
    values = dict(path=P.GOVERNANCE, object_kind=ExistingObjectKind.DIRECTORY,
                  uid=501, gid=20, mode=0o700, descriptor_identity_proven=True)
    values.update(overrides)
    return O(**values)


def test_public_planner_accepts_no_caller_path_home_or_identity():
    assert not inspect.signature(plan_pre_bootstrap_filesystem).parameters
    assert not inspect.signature(observe_pre_bootstrap_filesystem).parameters
    with pytest.raises(TypeError): plan_pre_bootstrap_filesystem(home="/tmp", uid=501, gid=20)


def test_plan_uses_exact_passwd_identity_and_fixed_paths():
    plan = _plan_pre_bootstrap_filesystem(
        platform_source=lambda: "darwin", getuid=lambda: 501, geteuid=lambda: 501,
        passwd_lookup=lambda uid: SimpleNamespace(pw_uid=uid, pw_gid=20, pw_dir="/Users/operator"),
    )
    assert plan.governance_path == "/Users/operator/Library/Application Support/AIControlCenter/governance"
    assert plan.trust_path == plan.governance_path + "/trust"
    with pytest.raises(FrozenInstanceError): plan.governance_path = "/tmp"


@pytest.mark.parametrize("ruid,euid", [(0, 0), (501, 502), (True, True)])
def test_invalid_process_identity_denied(ruid, euid):
    with pytest.raises(FilesystemContractError):
        _plan_pre_bootstrap_filesystem(
            platform_source=lambda: "darwin", getuid=lambda: ruid, geteuid=lambda: euid,
            passwd_lookup=lambda _: SimpleNamespace(pw_uid=ruid, pw_gid=20, pw_dir="/Users/operator"),
        )


@pytest.mark.parametrize("uid,gid", [(502, 20), (501, True), (True, 20)])
def test_caller_uid_gid_cannot_replace_passwd_binding(uid, gid):
    with pytest.raises(FilesystemContractError):
        _plan_pre_bootstrap_filesystem(
            platform_source=lambda: "darwin", getuid=lambda: 501, geteuid=lambda: 501,
            passwd_lookup=lambda _: SimpleNamespace(pw_uid=uid, pw_gid=gid, pw_dir="/Users/operator"),
        )


def test_closed_classifications():
    assert classify_governed_directory(O(P.GOVERNANCE, proven_absent=True), IDENTITY) is C.ABSENT
    assert classify_governed_directory(observation(), IDENTITY) is C.SAFE_EXISTING
    assert classify_governed_directory(observation(mode=0o755), IDENTITY) is C.UNSAFE_EXISTING
    assert classify_governed_directory(observation(uid=502), IDENTITY) is C.UNSAFE_EXISTING
    assert classify_governed_directory(observation(gid=21), IDENTITY) is C.UNSAFE_EXISTING
    assert classify_governed_directory(observation(object_kind=ExistingObjectKind.SYMLINK), IDENTITY) is C.UNSAFE_EXISTING
    assert classify_governed_directory(observation(object_kind=ExistingObjectKind.OTHER), IDENTITY) is C.UNSAFE_EXISTING
    assert classify_governed_directory(observation(observation_complete=False), IDENTITY) is C.AMBIGUOUS
    assert classify_governed_directory(observation(descriptor_identity_proven=False), IDENTITY) is C.AMBIGUOUS


def test_failure_to_observe_never_becomes_absent_and_bool_metadata_is_ambiguous():
    assert classify_governed_directory(O(P.GOVERNANCE), IDENTITY) is C.AMBIGUOUS
    assert classify_governed_directory(observation(mode=True), IDENTITY) is C.AMBIGUOUS
    assert classify_governed_directory(observation(uid=True), IDENTITY) is C.AMBIGUOUS


class FakeFilesystem:
    components = ("Users", "operator", "Library", "Application Support", "AIControlCenter", "governance", "trust")

    def __init__(self, *, changes=None, missing=None, symlink=None, mismatch=None, failure=None):
        self.changes = changes or {}
        self.missing = missing
        self.symlink = symlink
        self.mismatch = mismatch
        self.failure = failure
        self.next_fd = 10
        self.names = {10: "/"}

    def metadata(self, name, *, opened=False):
        defaults = {
            "/": (0, 0, 0o755), "Users": (0, 80, 0o755),
            "operator": (501, 20, 0o755), "Library": (501, 20, 0o755),
            "Application Support": (501, 20, 0o755), "AIControlCenter": (501, 20, 0o755),
            "governance": (501, 20, 0o700), "trust": (501, 20, 0o700),
        }
        uid, gid, mode = self.changes.get(name, defaults[name])
        kind = filesystem.stat.S_IFLNK if name == self.symlink else filesystem.stat.S_IFDIR
        inode = self.components.index(name) + 2 if name in self.components else 1
        if opened and name == self.mismatch:
            inode += 100
        return SimpleNamespace(st_mode=kind | mode, st_uid=uid, st_gid=gid, st_dev=1, st_ino=inode)

    def open(self, name, flags, dir_fd=None):
        if self.failure == ("open", name):
            raise OSError("uncertain open")
        if name == "/":
            return 10
        if name == self.missing:
            raise FileNotFoundError(name)
        self.next_fd += 1
        self.names[self.next_fd] = name
        return self.next_fd

    def stat(self, name, *, dir_fd, follow_symlinks):
        assert follow_symlinks is False
        if self.failure == ("stat", name):
            raise OSError("uncertain stat")
        if name == self.missing:
            raise FileNotFoundError(name)
        return self.metadata(name)

    def fstat(self, descriptor):
        name = self.names[descriptor]
        if self.failure == ("fstat", name):
            raise OSError("uncertain fstat")
        return self.metadata(name, opened=True)


def observe_fake(monkeypatch, **kwargs):
    fake = FakeFilesystem(**kwargs)
    monkeypatch.setattr(filesystem.os, "open", fake.open)
    monkeypatch.setattr(filesystem.os, "stat", fake.stat)
    monkeypatch.setattr(filesystem.os, "fstat", fake.fstat)
    monkeypatch.setattr(filesystem.os, "close", lambda descriptor: None)
    plan = filesystem.PreBootstrapFilesystemPlan(
        IDENTITY,
        "/Users/operator/Library/Application Support/AIControlCenter/governance",
        "/Users/operator/Library/Application Support/AIControlCenter/governance/trust",
    )
    return filesystem._observe_pre_bootstrap_filesystem(plan)


def assert_ambiguous(observations):
    assert tuple(classify_governed_directory(item, IDENTITY) for item in observations) == (C.AMBIGUOUS, C.AMBIGUOUS)


def test_safe_full_ancestor_chain_reaches_governed_observation(monkeypatch):
    governance, trust = observe_fake(monkeypatch)
    assert classify_governed_directory(governance, IDENTITY) is C.SAFE_EXISTING
    assert classify_governed_directory(trust, IDENTITY) is C.SAFE_EXISTING


def test_system_ancestor_does_not_require_passwd_ownership(monkeypatch):
    governance, _ = observe_fake(monkeypatch, changes={"Users": (999, 999, 0o755)})
    assert classify_governed_directory(governance, IDENTITY) is C.SAFE_EXISTING


@pytest.mark.parametrize("component,mode", [("/", 0o775), ("/", 0o757), ("Users", 0o775), ("Users", 0o757)])
def test_system_ancestor_writable_modes_fail_closed(monkeypatch, component, mode):
    assert_ambiguous(observe_fake(monkeypatch, changes={component: (0, 80, mode)}))


@pytest.mark.parametrize("component,identity", [
    ("operator", (502, 20)), ("operator", (501, 21)),
    ("Library", (502, 20)), ("Library", (501, 21)),
])
def test_passwd_owned_ancestor_wrong_identity_fails_closed(monkeypatch, component, identity):
    assert_ambiguous(observe_fake(monkeypatch, changes={component: (*identity, 0o755)}))


@pytest.mark.parametrize("component,mode", [
    ("operator", 0o775), ("operator", 0o757), ("Application Support", 0o775),
])
def test_passwd_owned_ancestor_writable_mode_fails_closed(monkeypatch, component, mode):
    assert_ambiguous(observe_fake(monkeypatch, changes={component: (501, 20, mode)}))


def test_exact_shared_parent_is_accepted(monkeypatch):
    governance, _ = observe_fake(monkeypatch, changes={"AIControlCenter": (501, 20, 0o755)})
    assert classify_governed_directory(governance, IDENTITY) is C.SAFE_EXISTING


@pytest.mark.parametrize("identity", [(502, 20), (501, 21)])
def test_shared_parent_requires_exact_passwd_identity(monkeypatch, identity):
    assert_ambiguous(observe_fake(monkeypatch, changes={"AIControlCenter": (*identity, 0o755)}))


@pytest.mark.parametrize("mode", [0o700, 0o775])
def test_shared_parent_requires_exact_0755(monkeypatch, mode):
    assert_ambiguous(observe_fake(monkeypatch, changes={"AIControlCenter": (501, 20, mode)}))


@pytest.mark.parametrize("condition", [
    {"symlink": "Library"}, {"missing": "Application Support"}, {"mismatch": "AIControlCenter"},
    {"failure": ("stat", "Library")}, {"failure": ("open", "Library")},
    {"failure": ("fstat", "Library")},
])
def test_prerequisite_symlink_missing_race_and_io_uncertainty_fail_closed(monkeypatch, condition):
    assert_ambiguous(observe_fake(monkeypatch, **condition))


@pytest.mark.parametrize("mode,expected", [(0o755, C.UNSAFE_EXISTING), (0o700, C.SAFE_EXISTING)])
def test_governed_exact_mode_semantics_are_preserved(monkeypatch, mode, expected):
    governance, _ = observe_fake(monkeypatch, changes={"governance": (501, 20, mode)})
    assert classify_governed_directory(governance, IDENTITY) is expected
