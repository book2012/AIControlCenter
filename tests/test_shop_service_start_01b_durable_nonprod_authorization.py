from __future__ import annotations

import inspect
import os
import builtins
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.shopping import runtime_cutover_port_remediation as remediation
from core.shopping import runtime_cutover_source_authorization as domain
from core.shopping.runtime_cutover_secret_source import SOURCE_ROLE, WORDPRESS_PORT_KEY
from ops.macos.shopping import issue_runtime_cutover_source_authorization as issuer
from ops.macos.shopping.runtime_cutover_source_authorization_store import (
    RuntimeCutoverSourceAuthorizationStore, SourceAuthorizationStoreError,
)


def authorization(*, expires_delta=timedelta(minutes=5), **changes):
    now = datetime.now(timezone.utc)
    values = {
        "authorization_id": "auth-01", "issued_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + expires_delta).isoformat(), "trusted_uid": os.getuid(), "trusted_gid": os.getgid(),
        "authoritative_work_item": domain.AUTHORITATIVE_WORK_ITEM,
        "environment": domain.ENVIRONMENT, "mutation_id": domain.MUTATION_ID,
        "source_role": SOURCE_ROLE, "source_key": WORDPRESS_PORT_KEY,
        "desired_value": domain.DESIRED_VALUE, "maximum_uses": 1,
        "production_authority": False, "ubuntu_authority": False,
    }
    values.update(changes)
    value = object.__new__(domain.SourceMutationAuthorization)
    for name in domain.SourceMutationAuthorization.__dataclass_fields__:
        object.__setattr__(value, name, values[name])
    return value


def store(tmp_path: Path, fault=None):
    return RuntimeCutoverSourceAuthorizationStore._for_test(
        tmp_path / "authority.sqlite3", uid=os.getuid(), gid=os.getgid(), fault=fault)


def tree_state(path: Path):
    return tuple(sorted((str(value.relative_to(path)), value.stat().st_mode,
                         value.stat().st_size, value.stat().st_mtime_ns)
                        for value in path.rglob("*"))) if path.exists() else ()


def test_live_surfaces_are_caller_unconfigurable() -> None:
    assert tuple(inspect.signature(issuer.issue).parameters) == ()
    assert tuple(inspect.signature(RuntimeCutoverSourceAuthorizationStore).parameters) == ()
    assert tuple(inspect.signature(RuntimeCutoverSourceAuthorizationStore.open_existing).parameters) == ()
    assert tuple(inspect.signature(RuntimeCutoverSourceAuthorizationStore.consume).parameters) == ("self",)
    assert tuple(inspect.signature(remediation.execute_remediation).parameters) == (
        "initial_observation", "observe_source", "authorization", "mutation")


def test_non_tty_and_exact_acknowledgement_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(issuer.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(issuer.sys.stdout, "isatty", lambda: True)
    with pytest.raises(RuntimeError, match="TTY"):
        issuer.issue()


def test_interactive_contract_and_repository_identity(monkeypatch) -> None:
    class TTY:
        def isatty(self): return True
    class Home: bound_uid = 501; passwd_home = "/trusted/passwd/home"
    class Ownership: expected_uid = 501; expected_gid = 20
    captured = {}
    class Store:
        @classmethod
        def _initialize_for_issuer(cls):
            captured["initialized"] = True
            return cls()
        def _issue(self, value): captured["authorization"] = value
    monkeypatch.setattr(issuer.sys, "stdin", TTY())
    monkeypatch.setattr(issuer.sys, "stdout", TTY())
    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: captured.setdefault("printed", []).append(args))
    monkeypatch.setattr(builtins, "input", lambda _prompt: issuer.ACKNOWLEDGEMENT)
    monkeypatch.setattr(issuer, "resolve_trusted_mac_account_home", lambda: Home())
    monkeypatch.setattr(issuer, "issue_trusted_ownership_expectation", lambda home: Ownership())
    monkeypatch.setattr(issuer, "RuntimeCutoverSourceAuthorizationStore", Store)
    receipt = issuer.issue()
    auth = captured["authorization"]
    assert (auth.trusted_uid, auth.trusted_gid) == (501, 20)
    assert receipt["state"] == "AVAILABLE"
    assert captured["initialized"] is True
    assert receipt["production_authority"] is receipt["ubuntu_authority"] is False


def test_wrong_acknowledgement_does_not_issue(monkeypatch) -> None:
    monkeypatch.setattr(issuer.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(issuer.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _prompt: "yes")
    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: None)
    monkeypatch.setattr(issuer.RuntimeCutoverSourceAuthorizationStore, "_initialize_for_issuer",
                        lambda: pytest.fail("store initialized"))
    with pytest.raises(RuntimeError, match="acknowledgement"):
        issuer.issue()


def test_open_existing_absent_store_creates_nothing(tmp_path) -> None:
    path = tmp_path / "missing" / "authority.sqlite3"
    before = tree_state(tmp_path)
    with pytest.raises(SourceAuthorizationStoreError):
        RuntimeCutoverSourceAuthorizationStore._open_existing_for_test(
            path, uid=os.getuid(), gid=os.getgid())
    assert tree_state(tmp_path) == before


def test_open_existing_empty_store_changes_no_durable_state(tmp_path) -> None:
    value = store(tmp_path)
    before = tree_state(tmp_path)
    with pytest.raises(domain.AuthorizationError):
        RuntimeCutoverSourceAuthorizationStore._open_existing_for_test(
            value._path, uid=os.getuid(), gid=os.getgid())
    assert tree_state(tmp_path) == before


@pytest.mark.parametrize("field,replacement", (
    ("expires_at", "2000-01-01T00:00:00+00:00"),
    ("trusted_uid", os.getuid() + 1),
))
def test_open_existing_expired_or_invalid_authorization_changes_nothing(
        tmp_path, field, replacement) -> None:
    store_value = store(tmp_path)
    store_value._issue(authorization())
    with store_value._connect_write() as connection:
        connection.execute(f"UPDATE source_mutation_authorizations SET {field}=?", (replacement,))
    before = tree_state(tmp_path)
    with pytest.raises(domain.AuthorizationError):
        RuntimeCutoverSourceAuthorizationStore._open_existing_for_test(
            store_value._path, uid=os.getuid(), gid=os.getgid())
    assert tree_state(tmp_path) == before


def test_store_creation_is_issuer_initialization_only(tmp_path) -> None:
    path = tmp_path / "authority.sqlite3"
    with pytest.raises(TypeError): RuntimeCutoverSourceAuthorizationStore()
    assert not path.exists()
    created = RuntimeCutoverSourceAuthorizationStore._for_test(
        path, uid=os.getuid(), gid=os.getgid())
    assert created._path == path and path.is_file()


def test_expiry_and_exact_binding_validation() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(domain.AuthorizationError):
        domain.validate_authorization(authorization(expires_delta=timedelta(seconds=-2)), now=now, uid=os.getuid(), gid=os.getgid())
    with pytest.raises(domain.AuthorizationError):
        domain.validate_authorization(authorization(mutation_id="SHOP-SERVICE-START-01B:WORDPRESS_PORT_58081_TO_58082"), now=now, uid=os.getuid(), gid=os.getgid())
    with pytest.raises(domain.AuthorizationError):
        domain.validate_authorization(True, now=now, uid=os.getuid(), gid=os.getgid())


def test_durable_claim_replay_restart_and_structured_receipt(tmp_path) -> None:
    issuer_store = store(tmp_path); issuer_store._issue(authorization())
    first = RuntimeCutoverSourceAuthorizationStore._open_existing_for_test(
        issuer_store._path, uid=os.getuid(), gid=os.getgid())
    result = first.consume()
    assert type(result) is domain.SourceMutationConsumptionResult
    assert result.receipt.state is domain.ConsumptionState.COMMITTED
    restarted = store(tmp_path)
    with pytest.raises(domain.AuthorizationError): restarted.consume()


def test_concurrent_double_consume_denied(tmp_path) -> None:
    first = store(tmp_path); first._issue(authorization())
    second = store(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda s: _consume_outcome(s), (first, second)))
    assert sorted(outcomes) == ["DENIED", "OK"]


def _consume_outcome(value):
    try: value.consume(); return "OK"
    except Exception: return "DENIED"


def test_stranded_claim_is_permanently_spent(tmp_path) -> None:
    def strand(stage, _connection):
        if stage == "after_claim_commit": raise RuntimeError("process stopped")
    claimed = store(tmp_path, strand); claimed._issue(authorization())
    with pytest.raises(RuntimeError): claimed.consume()
    with pytest.raises(domain.AuthorizationError): store(tmp_path).consume()


def test_ambiguous_final_commit_reconciles_only_same_call(tmp_path) -> None:
    def ambiguous(stage, _connection):
        if stage == "after_final_commit": raise sqlite3.OperationalError("ambiguous")
    value = store(tmp_path, ambiguous); value._issue(authorization())
    assert value.consume().receipt.state is domain.ConsumptionState.COMMITTED
    with pytest.raises(domain.AuthorizationError): store(tmp_path).consume()


def test_foreign_schema_symlink_and_mode_fail_closed(tmp_path) -> None:
    path = tmp_path / "authority.sqlite3"
    with sqlite3.connect(path) as connection: connection.execute("CREATE TABLE foreign_data(x)")
    path.chmod(0o600)
    with pytest.raises(SourceAuthorizationStoreError): store(tmp_path)
    path.unlink(); target = tmp_path / "target"; target.write_text(""); target.chmod(0o600)
    path.symlink_to(target)
    with pytest.raises(SourceAuthorizationStoreError): store(tmp_path)


def test_bool_and_foreign_receipts_never_authorize() -> None:
    for value in (True, object()):
        with pytest.raises(domain.AuthorizationError): domain.validate_consumption_result(value)


def test_wordpress_authorization_is_separate() -> None:
    receipt = RuntimeCutoverSourceAuthorizationStore._result(authorization()).receipt
    object.__setattr__(receipt, "mutation_id", "SHOP-SERVICE-START-01B:WORDPRESS_PORT_58081_TO_58082")
    result = object.__new__(domain.SourceMutationConsumptionResult); object.__setattr__(result, "receipt", receipt)
    with pytest.raises(domain.AuthorizationError): domain.validate_consumption_result(result)


def test_contract_grants_no_other_mutation_authority() -> None:
    value = authorization()
    assert value.production_authority is value.ubuntu_authority is False
    assert not hasattr(value, "database_mutation_allowed")
    assert not hasattr(value, "wordpress_runtime_mutation_allowed")
