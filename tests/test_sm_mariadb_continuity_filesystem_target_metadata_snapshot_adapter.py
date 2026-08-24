import ast
import inspect
import stat
from types import SimpleNamespace

import pytest

from core.secrets import mariadb_continuity_filesystem_target_metadata_snapshot as contract
from core.secrets.mariadb_continuity_concrete_protected_evidence_path import ConcreteProtectedEvidencePath
from core.secrets.mariadb_continuity_trusted_ownership_expectation import TrustedOwnershipExpectation
from ops.macos.shopping import mariadb_continuity_filesystem_target_metadata_snapshot_adapter as adapter_module


Outcome = contract.FilesystemTargetMetadataSnapshotOutcome
Reason = contract.FilesystemTargetMetadataSnapshotReason
Classification = contract.FilesystemTargetClassification


def request(path="/exact/../unchanged", uid=501, gid=20):
    concrete = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(concrete, "concrete_path", path)
    ownership = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(ownership, "expected_uid", uid)
    object.__setattr__(ownership, "expected_gid", gid)
    return contract.create_filesystem_target_metadata_snapshot_request(concrete, ownership)


def invoke(monkeypatch, observation, value=None):
    calls = []
    def fake_lstat(path):
        calls.append(path)
        if isinstance(observation, BaseException):
            raise observation
        return observation
    monkeypatch.setattr(adapter_module.os, "lstat", fake_lstat)
    result = adapter_module.MacFilesystemTargetMetadataSnapshotAdapter().observe_once(value or request())
    return result, calls


@pytest.mark.parametrize("bad", [object(), None])
def test_malformed_request_is_rejected_before_lstat(monkeypatch, bad):
    calls = []
    monkeypatch.setattr(adapter_module.os, "lstat", lambda path: calls.append(path))
    with pytest.raises(TypeError):
        adapter_module.MacFilesystemTargetMetadataSnapshotAdapter().observe_once(bad)
    assert calls == []


@pytest.mark.parametrize("field,value", [("concrete_path", object()), ("expected_uid", True), ("expected_uid", -1), ("expected_gid", False), ("expected_gid", -1)])
def test_malformed_nested_fact_is_rejected_before_lstat(monkeypatch, field, value):
    value_request = request()
    target = value_request.concrete_path if field == "concrete_path" else value_request.ownership_expectation
    object.__setattr__(target, field, value)
    calls = []
    monkeypatch.setattr(adapter_module.os, "lstat", lambda path: calls.append(path))
    with pytest.raises(TypeError):
        adapter_module.MacFilesystemTargetMetadataSnapshotAdapter().observe_once(value_request)
    assert calls == []


@pytest.mark.parametrize("error,expected", [(FileNotFoundError(), (Outcome.ABSENT, Reason.SOURCE_ABSENT, Classification.UNOBSERVED)), (PermissionError(), (Outcome.UNAVAILABLE, Reason.METADATA_ACCESS_FAILURE, Classification.UNOBSERVED))])
def test_failure_mapping_single_call_and_all_observed_none(monkeypatch, error, expected):
    result, calls = invoke(monkeypatch, error)
    assert (result.outcome, result.reason, result.target_classification) == expected
    assert (result.observed_mode, result.observed_uid, result.observed_gid) == (None, None, None)
    assert calls == ["/exact/../unchanged"]


class IntSubclass(int): pass


@pytest.mark.parametrize("observation", [object(), SimpleNamespace(st_mode=True, st_uid=501, st_gid=20), SimpleNamespace(st_mode=IntSubclass(stat.S_IFDIR | 0o700), st_uid=501, st_gid=20), SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=False, st_gid=20), SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=IntSubclass(501), st_gid=20), SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=501, st_gid=True), SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=501, st_gid=IntSubclass(20)), SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=501, st_gid=-1)])
def test_malformed_metadata_is_uncertain_and_discards_all_values(monkeypatch, observation):
    result, calls = invoke(monkeypatch, observation)
    assert (result.outcome, result.reason, result.target_classification) == (Outcome.UNCERTAIN, Reason.AMBIGUOUS_METADATA_RESULT, Classification.AMBIGUOUS)
    assert (result.observed_mode, result.observed_uid, result.observed_gid) == (None, None, None)
    assert len(calls) == 1


@pytest.mark.parametrize("mode,uid,gid,reason,classification,outcome", [
    (stat.S_IFLNK | 0o700, 999, 999, Reason.SYMLINK_REJECTED, Classification.SYMLINK, Outcome.UNSAFE),
    (stat.S_IFREG | 0o700, 999, 999, Reason.WRONG_FILE_TYPE, Classification.OTHER, Outcome.UNSAFE),
    (stat.S_IFDIR | 0o755, 999, 999, Reason.TARGET_MODE_MISMATCH, Classification.DIRECTORY, Outcome.UNSAFE),
    (stat.S_IFDIR | 0o700, 999, 999, Reason.TARGET_UID_MISMATCH, Classification.DIRECTORY, Outcome.UNSAFE),
    (stat.S_IFDIR | 0o700, 501, 999, Reason.TARGET_GID_MISMATCH, Classification.DIRECTORY, Outcome.UNSAFE),
    (stat.S_IFDIR | 0o700, 501, 20, Reason.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE, Classification.DIRECTORY, Outcome.DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE),
])
def test_deterministic_classification_precedence_and_exact_preservation(monkeypatch, mode, uid, gid, reason, classification, outcome):
    result, calls = invoke(monkeypatch, SimpleNamespace(st_mode=mode, st_uid=uid, st_gid=gid))
    assert (result.outcome, result.reason, result.target_classification) == (outcome, reason, classification)
    assert (result.observed_mode, result.observed_uid, result.observed_gid) == (mode, uid, gid)
    assert calls == ["/exact/../unchanged"]
    assert (result.stable_handle_bound, result.toctou_closed, result.fd_inode_device_bound) == (False, False, False)


def test_source_has_exact_single_lstat_and_no_scope_creep():
    source = inspect.getsource(adapter_module)
    tree = ast.parse(source)
    calls = [node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))]
    assert calls.count("lstat") == 1
    assert set(calls).isdisjoint({"stat", "Path", "exists", "lexists", "is_dir", "is_file", "is_symlink", "open", "read", "digest", "listdir", "scandir", "walk", "getuid", "geteuid", "getgid", "getegid", "issue_trusted_ownership_expectation", "RuntimeHomeResolver"})
