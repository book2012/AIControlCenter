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
    return artifact_bytes(
        tmp_path, ("\n".join(records) + "\n").encode("utf-8"), mode=mode,
    )


def artifact_bytes(tmp_path: Path, payload: bytes, *, mode: int = 0o600) -> tuple[Path, ResolvedTrustedMacAccountHome, TrustedOwnershipExpectation]:
    home = tmp_path / "control-plane-home"
    target = home.joinpath(*source.SOURCE_COMPONENTS)
    target.parent.mkdir(parents=True)
    (home / "Library" / "Application Support" / "AIControlCenter").chmod(0o755)
    target.parent.chmod(0o700)
    target.write_bytes(payload)
    target.chmod(mode)
    resolved, ownership = trust(home)
    return target, resolved, ownership


def required_names() -> list[str]:
    contract = json.loads((ROOT / "deploy/shopping/config/secret-contract.json").read_text())
    return [item["name"] for item in contract["keys"] if item["required"]["runtime_cutover"]]


def observe(tmp_path: Path, records: list[str]):
    _target, home, ownership = artifact(tmp_path, records)
    return source._observe_runtime_cutover_source(resolved_home=home, ownership=ownership, repository_root=ROOT)


def observe_bytes(tmp_path: Path, payload: bytes):
    _target, home, ownership = artifact_bytes(tmp_path, payload)
    return source._observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=ROOT,
    )


def complete_records(*, port: str = "58082") -> list[str]:
    return [
        f"{name}={port if name == source.WORDPRESS_PORT_KEY else SECRET_MARKER}"
        for name in required_names()
    ]


def complete_payload_with_raw_value(key: str, raw_value: bytes) -> bytes:
    records = [
        name.encode("ascii") + b"=" + (
            raw_value if name == key
            else (b"58082" if name == source.WORDPRESS_PORT_KEY else SECRET_MARKER.encode())
        )
        for name in required_names()
    ]
    return b"\n".join(records) + b"\n"


def test_fixed_portable_path_and_no_caller_override(tmp_path: Path) -> None:
    target, home, ownership = artifact(tmp_path, complete_records())
    opened, descriptors = source._open_source(home, ownership, ROOT)
    try:
        assert opened.concrete_path == str(target)
        assert source.SOURCE_RELATIVE_PATH == "Library/Application Support/AIControlCenter/secrets/shopping-commerce.env"
    finally:
        for descriptor in reversed(descriptors): os.close(descriptor)
    assert tuple(inspect.signature(source.observe_runtime_cutover_source).parameters) == ()
    assert "path" not in inspect.signature(source._observe_runtime_cutover_source).parameters


def test_public_observer_derives_home_and_ownership_from_trusted_authorities(monkeypatch, tmp_path: Path) -> None:
    _target, home, ownership = artifact(tmp_path, complete_records())
    monkeypatch.setattr(source, "resolve_trusted_mac_account_home", lambda: home)
    monkeypatch.setattr(source, "issue_trusted_ownership_expectation", lambda resolved: ownership if resolved is home else None)
    result = source.observe_runtime_cutover_source()
    assert result.ready


def test_traversal_is_rejected() -> None:
    with pytest.raises(source.RuntimeCutoverSourceError) as error:
        source._validate_components(("Library", "..", "shopping-commerce.env"))
    assert error.value.reason is source.SourceReason.UNSAFE_PATH


def test_safe_complete_parent_chain_passes(tmp_path: Path) -> None:
    result = observe(tmp_path, complete_records())
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
    result = observe(tmp_path, complete_records())
    assert result.ready and result.reason_code is source.SourceReason.READY
    assert result.wordpress_port_expected == "58082"
    assert result.wordpress_port_value_valid is True
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


@pytest.mark.parametrize("port", ["58081", "59999", "not-a-port", "058082", "58082 ", "58082 # comment", "58082.0", "+58082"])
def test_noncanonical_wordpress_port_fails_closed(tmp_path: Path, port: str) -> None:
    result = observe(tmp_path, complete_records(port=port))
    assert not result.ready
    assert result.wordpress_port_value_valid is False
    assert result.reason_code is source.SourceReason.WORDPRESS_PORT_VALUE_INVALID


def test_missing_and_duplicate_wordpress_port_fail_closed(tmp_path: Path) -> None:
    without_port = [record for record in complete_records() if not record.startswith(f"{source.WORDPRESS_PORT_KEY}=")]
    missing = observe(tmp_path / "missing", without_port)
    assert missing.reason_code is source.SourceReason.MISSING_REQUIRED_KEY_NAMES
    duplicate_path = tmp_path / "duplicate"
    duplicate_path.mkdir()
    duplicate = observe(duplicate_path, complete_records() + [f"{source.WORDPRESS_PORT_KEY}=58082"])
    assert duplicate.reason_code is source.SourceReason.DUPLICATE_KEY_NAMES


def test_secret_assignment_values_are_never_emitted(tmp_path: Path) -> None:
    db_secret = "db-password-must-not-escape"
    root_secret = "root-password-must-not-escape"
    records = complete_records()
    records = [
        f"SHOPPING_DB_PASSWORD={db_secret}" if record.startswith("SHOPPING_DB_PASSWORD=")
        else f"SHOPPING_DB_ROOT_PASSWORD={root_secret}" if record.startswith("SHOPPING_DB_ROOT_PASSWORD=")
        else record
        for record in records
    ]
    result = observe(tmp_path, records)
    public_json = json.dumps(result.projection())
    assert result.ready and result.values_exposed is False
    assert db_secret not in public_json and root_secret not in public_json
    assert db_secret not in repr(result) and root_secret not in repr(result)


@pytest.mark.parametrize("key", ["SHOPPING_DB_PASSWORD", "SHOPPING_DB_ROOT_PASSWORD"])
def test_complete_source_invalid_utf8_secret_fails_for_unsafe_encoding(
    tmp_path: Path, key: str,
) -> None:
    sentinel = b"secret-sentinel-must-not-escape-\xff"
    result = observe_bytes(tmp_path, complete_payload_with_raw_value(key, sentinel))
    projection = json.dumps(result.projection())
    failure_text = result.reason_code.value
    assert result.ready is False
    assert result.reason_code is source.SourceReason.UNSAFE_RECORD_STRUCTURE
    assert result.reason_code is not source.SourceReason.MISSING_REQUIRED_KEY_NAMES
    assert "secret-sentinel-must-not-escape" not in projection
    assert "secret-sentinel-must-not-escape" not in repr(result)
    assert "secret-sentinel-must-not-escape" not in failure_text


def test_invalid_utf8_wordpress_port_record_fails_for_unsafe_encoding(tmp_path: Path) -> None:
    result = observe_bytes(
        tmp_path,
        complete_payload_with_raw_value(source.WORDPRESS_PORT_KEY, b"58082\xff"),
    )
    assert result.ready is False
    assert result.reason_code is source.SourceReason.UNSAFE_RECORD_STRUCTURE
    assert result.reason_code is not source.SourceReason.WORDPRESS_PORT_VALUE_INVALID


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
    result = observe(tmp_path, complete_records())
    assert result.mutation_performed is result.values_exposed is False
    text = Path(source.__file__).read_text()
    assert all(term not in text for term in ("Docker", "Colima", "MariaDB", "UbuntuWorkerClient", "Production"))
