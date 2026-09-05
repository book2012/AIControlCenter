from __future__ import annotations

import inspect
import json
import os
import runpy
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.shopping import wordpress_port_authorization as domain
from ops.macos.shopping import wordpress_port_authorization_inspector as inspector
from ops.macos.shopping import wordpress_port_live_operator as operator
from ops.macos.shopping.wordpress_port_authorization_store import (
    WordPressAuthorizationStoreError,
    WordPressPortAuthorizationStore,
)


def _authorization(identifier: str, *, expired: bool = False):
    now = datetime.now(timezone.utc)
    values = {
        **domain.immutable_contract(uid=os.getuid(), gid=os.getgid()),
        "authorization_id": identifier,
        "issued_at": (now - timedelta(minutes=2)).isoformat(),
        "expires_at": (now - timedelta(minutes=1) if expired else now + timedelta(minutes=5)).isoformat(),
    }
    value = object.__new__(domain.WordPressMutationAuthorization)
    for name in value.__dataclass_fields__:
        object.__setattr__(value, name, values[name])
    return value


def _store(tmp_path: Path) -> WordPressPortAuthorizationStore:
    return WordPressPortAuthorizationStore._for_test(
        tmp_path / "authority.sqlite3", uid=os.getuid(), gid=os.getgid(),
    )


def _inspect(path: Path):
    return inspector._inspect_fixed_path(
        path, uid=os.getuid(), gid=os.getgid(), test=True,
    )


def _snapshot(path: Path):
    metadata = path.stat(follow_symlinks=False)
    return (path.read_bytes(), metadata.st_mode, metadata.st_uid, metadata.st_gid,
            metadata.st_size, metadata.st_mtime_ns)


def test_main_calls_run_exactly_once_and_emits_safe_json(monkeypatch, capsys):
    calls = []

    class Result:
        def to_json_safe(self):
            return {"production_authority": False, "ubuntu_authority": False}

    monkeypatch.setattr(operator, "run", lambda: calls.append(True) or Result())
    assert operator.main() == 0
    assert calls == [True]
    assert json.loads(capsys.readouterr().out) == {
        "production_authority": False, "ubuntu_authority": False,
    }


def test_python_module_path_calls_governed_run_once(monkeypatch, capsys):
    calls = []

    class Result:
        def to_json_safe(self):
            return {"module_invocation": True}

    monkeypatch.setattr(
        WordPressPortAuthorizationStore, "open_existing", lambda: None,
    )
    monkeypatch.setattr(
        "core.shopping.wordpress_port_reconciliation.execute_reconciliation",
        lambda **_kwargs: calls.append(True) or Result(),
    )
    with pytest.raises(SystemExit) as exited:
        runpy.run_path(operator.__file__, run_name="__main__")
    assert exited.value.code == 0
    assert calls == [True]
    assert json.loads(capsys.readouterr().out) == {"module_invocation": True}


def test_cli_has_no_caller_selectable_target_parameters():
    assert tuple(inspect.signature(operator.run).parameters) == ()
    assert tuple(inspect.signature(operator.main).parameters) == ()


def test_cli_exception_is_bounded_and_non_secret(monkeypatch, capsys):
    secret = "never-print-this-secret"
    monkeypatch.setattr(operator, "run", lambda: (_ for _ in ()).throw(RuntimeError(secret)))
    assert operator.main() != 0
    captured = capsys.readouterr()
    assert captured.out == "" and secret not in captured.err
    assert json.loads(captured.err) == {
        "error": "WORDPRESS_PORT_OPERATOR_CLI_FAILURE",
        "failure_stage": "OPERATOR_CLI",
        "reason_codes": ["WORDPRESS_PORT_OPERATOR_CLI_FAILURE"],
        "authorization_consumption_state": "UNCERTAIN",
        "authorization_consumed": None,
        "production_authority": False,
        "ubuntu_authority": False,
    }


def test_inspector_is_zero_argument_and_absent_store_creates_nothing(tmp_path):
    assert tuple(inspect.signature(inspector.inspect_authorizations).parameters) == ()
    missing = tmp_path / "absent" / "authority.sqlite3"
    before = tuple(tmp_path.rglob("*"))
    assert _inspect(missing) == {"authorizations": [], "state": "MISSING_STORE"}
    assert tuple(tmp_path.rglob("*")) == before


def test_inspector_preserves_store_bytes_and_metadata_and_never_consumes(monkeypatch, tmp_path):
    value = _store(tmp_path)
    value._issue(_authorization("available"))
    before = _snapshot(value._path)
    monkeypatch.setattr(
        WordPressPortAuthorizationStore, "consume", lambda _self: pytest.fail("consumed"),
    )
    monkeypatch.setattr(
        WordPressPortAuthorizationStore, "_initialize_for_issuer",
        lambda: pytest.fail("issuer initialized"),
    )
    result = _inspect(value._path)
    assert result["authorizations"][0]["state"] == "AVAILABLE"
    assert _snapshot(value._path) == before


def test_inspector_distinguishes_all_durable_states(tmp_path):
    value = _store(tmp_path)
    value._issue(_authorization("available"))
    with sqlite3.connect(value._path) as db:
        columns = tuple(domain.WordPressMutationAuthorization.__dataclass_fields__)
        expired = _authorization("expired", expired=True)
        db.execute(
            "INSERT INTO wordpress_mutation_authorizations (" + ",".join(columns)
            + ",state,claimed_at,committed_at) VALUES (" + ",".join("?" for _ in columns)
            + ",'AVAILABLE',NULL,NULL)", tuple(getattr(expired, name) for name in columns),
        )
        claimed = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE wordpress_mutation_authorizations SET state='DURABLY_CLAIMED',claimed_at=? WHERE authorization_id='available'",
            (claimed,),
        )
        committed = _authorization("committed")
        db.execute(
            "INSERT INTO wordpress_mutation_authorizations (" + ",".join(columns)
            + ",state,claimed_at,committed_at) VALUES (" + ",".join("?" for _ in columns)
            + ",'COMMITTED',?,?)",
            (*tuple(getattr(committed, name) for name in columns), claimed, claimed),
        )
    rows = {row["authorization_id"]: row for row in _inspect(value._path)["authorizations"]}
    assert rows["available"]["state"] == "DURABLY_CLAIMED"
    assert rows["expired"]["state"] == "EXPIRED_AVAILABLE" and rows["expired"]["expired"]
    assert rows["committed"]["state"] == "COMMITTED"
    assert all(row["production_authority"] is False for row in rows.values())
    assert all(row["ubuntu_authority"] is False for row in rows.values())


def test_inspector_rejects_mode_symlink_and_schema(tmp_path):
    value = _store(tmp_path)
    with pytest.raises(WordPressAuthorizationStoreError):
        inspector._inspect_fixed_path(
            value._path, uid=os.getuid() + 1, gid=os.getgid(), test=True,
        )
    value._path.chmod(0o644)
    with pytest.raises(WordPressAuthorizationStoreError):
        _inspect(value._path)
    value._path.chmod(0o600)
    link = tmp_path / "link.sqlite3"
    link.symlink_to(value._path)
    with pytest.raises(WordPressAuthorizationStoreError):
        _inspect(link)
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir(mode=0o700)
    foreign = foreign_dir / "authority.sqlite3"
    with sqlite3.connect(foreign) as db:
        db.execute("CREATE TABLE credentials(secret TEXT)")
    foreign.chmod(0o600)
    with pytest.raises(WordPressAuthorizationStoreError):
        _inspect(foreign)


def test_inspector_exposes_only_allowlisted_metadata(tmp_path):
    value = _store(tmp_path)
    value._issue(_authorization("safe-id"))
    row = _inspect(value._path)["authorizations"][0]
    assert set(row) == {
        "authorization_id", "state", "issued_at", "expires_at", "expired",
        "mutation_id", "production_authority", "ubuntu_authority",
    }
    serialized = json.dumps(row)
    for forbidden in ("compose_file", "target_context", "expected_before_binding", "trusted_uid"):
        assert forbidden not in serialized


def test_inspector_main_emits_deterministic_json(monkeypatch, capsys):
    observation = {"authorizations": [], "state": "NO_ROWS"}
    monkeypatch.setattr(inspector, "inspect_authorizations", lambda: observation)
    assert inspector.main() == 0
    assert capsys.readouterr().out == json.dumps(
        observation, sort_keys=True, separators=(",", ":"),
    ) + "\n"
