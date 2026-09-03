from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import ResolvedTrustedMacAccountHome
from core.secrets.mariadb_continuity_trusted_ownership_expectation import TrustedOwnershipExpectation
from core.shopping import runtime_cutover_secret_source as source


ROOT = Path(__file__).resolve().parents[1]
SECRET_MARKER = "do-not-emit-this-secret"


def trust(home: Path) -> tuple[ResolvedTrustedMacAccountHome, TrustedOwnershipExpectation]:
    resolved = object.__new__(ResolvedTrustedMacAccountHome)
    object.__setattr__(resolved, "bound_uid", os.getuid())
    object.__setattr__(resolved, "passwd_home", str(home))
    ownership = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(ownership, "expected_uid", os.getuid())
    object.__setattr__(ownership, "expected_gid", os.getgid())
    return resolved, ownership


def artifact(tmp_path: Path, records: list[str], *, mode: int = 0o600) -> tuple[Path, ResolvedTrustedMacAccountHome, TrustedOwnershipExpectation]:
    home = tmp_path / "control-plane-home"
    target = home.joinpath(*source.SOURCE_COMPONENTS)
    target.parent.mkdir(parents=True)
    (home / "Library" / "Application Support" / "AIControlCenter").chmod(0o755)
    target.parent.chmod(0o700)
    target.write_text("\n".join(records) + "\n", encoding="utf-8")
    target.chmod(mode)
    resolved, ownership = trust(home)
    return target, resolved, ownership


def required_names() -> list[str]:
    contract = json.loads((ROOT / "deploy/shopping/config/secret-contract.json").read_text())
    return [item["name"] for item in contract["keys"] if item["required"]["runtime_cutover"]]


def observe(tmp_path: Path, records: list[str]):
    _target, home, ownership = artifact(tmp_path, records)
    return source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT)


def test_fixed_portable_path_and_no_caller_override(tmp_path: Path) -> None:
    target, home, ownership = artifact(tmp_path, [f"{name}=x" for name in required_names()])
    opened, descriptors = source._open_source(home, ownership, ROOT)
    try:
        assert opened.concrete_path == str(target)
        assert source.SOURCE_RELATIVE_PATH == "Library/Application Support/AIControlCenter/secrets/shopping-commerce.env"
    finally:
        for descriptor in reversed(descriptors): os.close(descriptor)
    assert tuple(inspect.signature(source.observe_runtime_cutover_source).parameters) == ()
    assert "path" not in inspect.signature(source._observe_runtime_cutover_source).parameters


def test_public_observer_derives_home_and_ownership_from_trusted_authorities(monkeypatch, tmp_path: Path) -> None:
    _target, home, ownership = artifact(tmp_path, [f"{name}=x" for name in required_names()])
    monkeypatch.setattr(source, "resolve_trusted_mac_account_home", lambda: home)
    monkeypatch.setattr(source, "issue_trusted_ownership_expectation", lambda resolved: ownership if resolved is home else None)
    result = source.observe_runtime_cutover_source()
    assert result.ready


def test_traversal_is_rejected() -> None:
    with pytest.raises(source.RuntimeCutoverSourceError) as error:
        source._validate_components(("Library", "..", "shopping-commerce.env"))
    assert error.value.reason is source.SourceReason.UNSAFE_PATH


def test_safe_complete_parent_chain_passes(tmp_path: Path) -> None:
    result = observe(tmp_path, [f"{name}=x" for name in required_names()])
    assert result.ready


def test_parent_symlink_and_non_directory_fail_closed(tmp_path: Path) -> None:
    target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    application_support = Path(home.passwd_home) / "Library" / "Application Support"
    target.unlink()
    target.parent.rmdir()
    (application_support / "real-control-plane").mkdir()
    (application_support / "AIControlCenter").rmdir()
    (application_support / "AIControlCenter").symlink_to(application_support / "real-control-plane")
    result = source._observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=ROOT,
    )
    assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA

    (application_support / "AIControlCenter").unlink()
    (application_support / "AIControlCenter").write_text("not a directory")
    result = source._observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=ROOT,
    )
    assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA


@pytest.mark.parametrize("mode", [0o775, 0o757])
def test_group_or_world_writable_passwd_home_parent_fails_closed(tmp_path: Path, mode: int) -> None:
    _target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    library = Path(home.passwd_home) / "Library"
    library.chmod(mode)
    result = source._observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=ROOT,
    )
    assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA


def test_wrong_parent_ownership_fails_closed(tmp_path: Path) -> None:
    _target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    wrong = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(wrong, "expected_uid", ownership.expected_uid + 1)
    object.__setattr__(wrong, "expected_gid", ownership.expected_gid)
    result = source._observe_runtime_cutover_source(
        resolved_home=home, ownership=wrong, repository_root=ROOT,
    )
    assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA


@pytest.mark.parametrize("mode", [0o755, 0o750, 0o770])
def test_secrets_directory_requires_exact_0700(tmp_path: Path, mode: int) -> None:
    target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    target.parent.chmod(mode)
    result = source._observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=ROOT,
    )
    assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA


def test_symlink_directory_and_empty_are_rejected(tmp_path: Path) -> None:
    target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    target.unlink(); target.symlink_to(tmp_path / "elsewhere")
    assert source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT).reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA
    target.unlink(); target.mkdir()
    assert source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT).reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA
    target.rmdir(); target.write_bytes(b""); target.chmod(0o600)
    assert source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT).reason_code is source.SourceReason.EMPTY_SOURCE


def test_wrong_owner_group_and_unsafe_mode_fail_closed(tmp_path: Path) -> None:
    _target, home, ownership = artifact(tmp_path, ["SHOPPING_DB_NAME=x"])
    wrong_uid = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(wrong_uid, "expected_uid", os.getuid() + 1); object.__setattr__(wrong_uid, "expected_gid", os.getgid())
    wrong_gid = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(wrong_gid, "expected_uid", os.getuid()); object.__setattr__(wrong_gid, "expected_gid", os.getgid() + 1)
    for expectation in (wrong_uid, wrong_gid):
        result = source._observe_runtime_cutover_source(resolved_home=home, ownership=expectation, repository_root=ROOT)
        assert result.reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA
    target = Path(home.passwd_home).joinpath(*source.SOURCE_COMPONENTS); target.chmod(0o640)
    assert source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT).reason_code is source.SourceReason.UNSAFE_FILESYSTEM_METADATA


def test_source_must_be_outside_repository() -> None:
    home, ownership = trust(ROOT)
    result = source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT)
    assert result.reason_code is source.SourceReason.UNSAFE_PATH


def test_required_names_are_canonical_and_complete_is_ready(tmp_path: Path) -> None:
    result = observe(tmp_path, [f"{name}={SECRET_MARKER}" for name in required_names()])
    assert result.ready and result.reason_code is source.SourceReason.READY
    assert list(result.required_key_names_present) == required_names()
    assert SECRET_MARKER not in json.dumps(result.projection())


def test_missing_duplicate_unknown_and_malformed_fail_closed(tmp_path: Path) -> None:
    names = required_names()
    cases = [
        ([f"{name}=x" for name in names[:-1]], source.SourceReason.MISSING_REQUIRED_KEY_NAMES),
        ([f"{name}=x" for name in names] + [f"{names[0]}=again"], source.SourceReason.DUPLICATE_KEY_NAMES),
        ([f"{name}=x" for name in names] + ["SHOPPING_UNKNOWN=x"], source.SourceReason.UNKNOWN_KEY_NAMES),
        ([f"{name}=x" for name in names] + [f"broken {SECRET_MARKER}"], source.SourceReason.MALFORMED_ASSIGNMENT),
    ]
    for index, (records, reason) in enumerate(cases):
        case = tmp_path / str(index); case.mkdir()
        result = observe(case, records)
        assert not result.ready and result.reason_code is reason
        assert SECRET_MARKER not in json.dumps(result.projection())


@pytest.mark.parametrize("payload", [b"A" * (source.MAX_SOURCE_BYTES + 1), b"SHOPPING_DB_NAME=" + b"x" * source.MAX_RECORD_BYTES, b"SHOPPING_DB_NAME=x\0y", b"SHOPPING_DB_NAME=\xff"])
def test_oversized_nul_and_encoding_fail_value_free(tmp_path: Path, payload: bytes) -> None:
    target, home, ownership = artifact(tmp_path, ["placeholder=x"])
    target.write_bytes(payload); target.chmod(0o600)
    result = source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT)
    assert not result.ready and SECRET_MARKER not in str(result) and "=" not in result.reason_code.value


def test_no_runtime_or_mutation_surface(monkeypatch, tmp_path: Path) -> None:
    import socket, subprocess, urllib.request
    def blocked(*_args, **_kwargs): raise AssertionError("external call attempted")
    monkeypatch.setattr(subprocess, "run", blocked); monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked); monkeypatch.setattr(urllib.request, "urlopen", blocked)
    result = observe(tmp_path, [f"{name}=x" for name in required_names()])
    assert result.mutation_performed is result.values_exposed is False
    text = Path(source.__file__).read_text()
    assert all(term not in text for term in ("Docker", "Colima", "MariaDB", "UbuntuWorkerClient", "Production"))
