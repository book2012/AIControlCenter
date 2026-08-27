from pathlib import Path
from types import SimpleNamespace
import os

import pytest

from core.governance.control_plane.trust.models import PathPolicyError
from core.governance.control_plane.trust.path_policy import (
    MAX_REGISTRY_BYTES,
    REGISTRY_SUFFIX,
    _read_trust_registry,
    read_trust_registry,
)


def _call(home: Path, *, uid=None, gid=None, ruid=None, euid=None, platform="darwin"):
    actual_uid, actual_gid = os.getuid(), os.getgid()
    uid = actual_uid if uid is None else uid
    gid = actual_gid if gid is None else gid
    ruid = uid if ruid is None else ruid
    euid = ruid if euid is None else euid
    return _read_trust_registry(
        platform_source=lambda: platform,
        getuid=lambda: ruid,
        geteuid=lambda: euid,
        passwd_lookup=lambda _: SimpleNamespace(pw_uid=uid, pw_gid=gid, pw_dir=str(home)),
    )


def _registry(tmp_path: Path, data=b"{}"):
    path = tmp_path / REGISTRY_SUFFIX
    path.parent.mkdir(parents=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return path


def test_linux_cannot_supply_darwin_override():
    with pytest.raises(TypeError):
        read_trust_registry(platform="darwin")


def test_production_reader_accepts_no_identity_or_path_authority_arguments():
    with pytest.raises(TypeError):
        read_trust_registry(expected_uid=os.getuid(), expected_gid=os.getgid())


def test_linux_production_gate_rejected():
    with pytest.raises(PathPolicyError): _call(Path("/untrusted"), platform="linux")


def test_ruid_euid_mismatch_rejected(tmp_path):
    with pytest.raises(PathPolicyError): _call(tmp_path, ruid=501, euid=502, uid=501)


def test_root_rejected(tmp_path):
    with pytest.raises(PathPolicyError): _call(tmp_path, uid=0, gid=0, ruid=0, euid=0)


@pytest.mark.parametrize("passwd_home", [None, ""])
def test_ambiguous_passwd_home_rejected(passwd_home):
    with pytest.raises(PathPolicyError):
        _read_trust_registry(
            platform_source=lambda: "darwin",
            getuid=lambda: 501,
            geteuid=lambda: 501,
            passwd_lookup=lambda _: SimpleNamespace(
                pw_uid=501, pw_gid=20, pw_dir=passwd_home
            ),
        )


def test_missing_path_rejected(tmp_path):
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_symlink_path_rejected(tmp_path):
    real_home = tmp_path / "real"; real_home.mkdir()
    linked_home = tmp_path / "linked"; linked_home.symlink_to(real_home, target_is_directory=True)
    _registry(real_home)
    with pytest.raises(PathPolicyError): _call(linked_home)


def test_wrong_trust_directory_mode_rejected(tmp_path):
    path = _registry(tmp_path); os.chmod(path.parent, 0o755)
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_wrong_registry_file_mode_rejected(tmp_path):
    path = _registry(tmp_path); os.chmod(path, 0o644)
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_wrong_file_uid_gid_rejected(tmp_path, monkeypatch):
    _registry(tmp_path)
    original_fstat = os.fstat
    def wrong_owner(descriptor):
        result = original_fstat(descriptor)
        return SimpleNamespace(
            st_mode=result.st_mode, st_uid=result.st_uid, st_gid=result.st_gid + 1,
            st_size=result.st_size, st_dev=result.st_dev, st_ino=result.st_ino,
        )
    monkeypatch.setattr("core.governance.control_plane.trust.path_policy.os.fstat", wrong_owner)
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_oversized_registry_rejected(tmp_path):
    _registry(tmp_path, b"x" * (MAX_REGISTRY_BYTES + 1))
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_intermediate_component_replacement_with_symlink_fails_closed(tmp_path, monkeypatch):
    _registry(tmp_path)
    attacker = tmp_path / "attacker"; attacker.mkdir()
    original_open = os.open; replaced = False
    def replacing_open(path, flags, *args, **kwargs):
        nonlocal replaced
        if path == "Application Support" and not replaced:
            replaced = True
            component = tmp_path / "Library" / "Application Support"
            component.rename(tmp_path / "Library" / "original")
            component.symlink_to(attacker, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr("core.governance.control_plane.trust.path_policy.os.open", replacing_open)
    with pytest.raises(PathPolicyError): _call(tmp_path)


def test_final_leaf_replacement_during_read_fails_closed(tmp_path, monkeypatch):
    path = _registry(tmp_path, b'{"trusted":true}')
    original_read = os.read; replaced = False
    def replacing_read(descriptor, count):
        nonlocal replaced
        if not replaced:
            replaced = True
            path.unlink(); path.write_bytes(b'{"attacker":true}'); os.chmod(path, 0o600)
        return original_read(descriptor, count)
    monkeypatch.setattr("core.governance.control_plane.trust.path_policy.os.read", replacing_read)
    with pytest.raises(PathPolicyError): _call(tmp_path)
