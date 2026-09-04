from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

import pytest

from core.shopping import runtime_cutover_port_remediation as domain
from core.shopping import runtime_cutover_secret_source as source
from core.shopping import runtime_cutover_source_authorization as source_auth
from ops.macos.shopping import runtime_cutover_port_remediation_operator as operator
from ops.macos.shopping import runtime_cutover_source_authorization_store as auth_store
from tests.test_shop_service_start_01b_runtime_cutover_secret_source import (
    ROOT, SECRET_MARKER, artifact_bytes, complete_records, trust,
)


def observation(reason=source.SourceReason.WORDPRESS_PORT_VALUE_INVALID):
    ready = reason is source.SourceReason.READY
    return source.RuntimeCutoverSourceObservation(
        "1.0", source.SOURCE_AUTHORITY, source.SOURCE_ROLE, source.PATH_ROLE,
        True, (), (), (), (), ready, reason,
        wordpress_port_value_valid=ready,
    )


class Auth:
    def __init__(self, events, allowed=True): self.events, self.allowed = events, allowed
    def consume(self):
        self.events.append(("auth", domain.MUTATION_ID))
        allowed, self.allowed = self.allowed, False
        if not allowed:
            raise source_auth.AuthorizationError("spent")
        receipt = object.__new__(source_auth.SourceMutationConsumptionReceipt)
        values = {
            "authorization_id": "test", "issued_at": "2026-09-04T00:00:00+00:00",
            "expires_at": "2026-09-04T00:10:00+00:00", "trusted_uid": 501,
            "trusted_gid": 20, "authoritative_work_item": domain.AUTHORITATIVE_WORK_ITEM,
            "environment": domain.ENVIRONMENT, "mutation_id": domain.MUTATION_ID,
            "source_role": source.SOURCE_ROLE, "source_key": source.WORDPRESS_PORT_KEY,
            "desired_value": domain.DESIRED_VALUE, "maximum_uses": 1,
            "state": source_auth.ConsumptionState.COMMITTED,
            "production_authority": False, "ubuntu_authority": False,
        }
        for name, value in values.items(): object.__setattr__(receipt, name, value)
        result = object.__new__(source_auth.SourceMutationConsumptionResult)
        object.__setattr__(result, "receipt", receipt)
        return result


class Mutation:
    def __init__(self, events, outcome=domain.Outcome.SUCCEEDED): self.events, self.outcome = events, outcome
    def replace_wordpress_port(self): self.events.append(("mutation",)); return self.outcome


def test_pure_classifier_never_selects_and_accepts_no_authorization() -> None:
    decision = domain.classify_candidate(observation())
    assert decision.classification is domain.Classification.CANDIDATE
    assert decision.mutation_selected is False
    assert "authorization" not in inspect.signature(domain.classify_candidate).parameters


def test_no_authorization_means_no_mutation() -> None:
    events = []
    result = domain.execute_remediation(initial_observation=observation(),
        observe_source=lambda: observation(), authorization=None, mutation=Mutation(events))
    assert not result.mutation_executed and events == []


def test_authorization_precedes_fresh_observation_and_mutation() -> None:
    events = []
    states = iter((observation(), observation(source.SourceReason.READY)))
    def observe(): events.append(("observe",)); return next(states)
    result = domain.execute_remediation(initial_observation=observation(), observe_source=observe,
        authorization=Auth(events), mutation=Mutation(events))
    assert events == [("auth", domain.MUTATION_ID), ("observe",), ("mutation",), ("observe",)]
    assert result.outcome is domain.Outcome.SUCCEEDED


@pytest.mark.parametrize("reason", [source.SourceReason.MISSING_REQUIRED_KEY_NAMES,
    source.SourceReason.DUPLICATE_KEY_NAMES, source.SourceReason.UNKNOWN_KEY_NAMES,
    source.SourceReason.MALFORMED_ASSIGNMENT, source.SourceReason.UNSAFE_RECORD_STRUCTURE])
def test_wrong_fresh_reason_consumes_authorization_without_mutation(reason) -> None:
    events = []
    result = domain.execute_remediation(initial_observation=observation(),
        observe_source=lambda: observation(reason), authorization=Auth(events), mutation=Mutation(events))
    assert result.authorization_consumed and not result.mutation_executed
    assert events == [("auth", domain.MUTATION_ID)]


def test_already_desired_never_mutates() -> None:
    events = []
    result = domain.execute_remediation(initial_observation=observation(source.SourceReason.READY),
        observe_source=lambda: observation(), authorization=Auth(events), mutation=Mutation(events))
    assert result.classification is domain.Classification.ALREADY_DESIRED and events == []


def fixture(tmp_path: Path, payload: bytes):
    target, home, ownership = artifact_bytes(tmp_path, payload)
    class FixtureMutation:
        def replace_wordpress_port(self):
            return operator._replace_wordpress_port_at_trusted_source(
                resolved_home=home, ownership=ownership, repository_root=ROOT)
    return target, FixtureMutation()


def payload(port=b"58081", final=b"\n"):
    entries = json.loads((ROOT / "deploy/shopping/config/secret-contract.json").read_text())["keys"]
    return b"# comment\n" + b"\n".join(
        entry["name"].encode() + b"=" + (
            port if entry["name"] == source.WORDPRESS_PORT_KEY else SECRET_MARKER.encode()
        )
        for entry in entries if entry["required"]["runtime_cutover"]
    ) + final


def test_only_exact_port_bytes_change_preserving_everything_else(tmp_path: Path) -> None:
    before = payload(final=b"")
    target, capability = fixture(tmp_path, before)
    metadata = target.stat()
    assert capability.replace_wordpress_port() is domain.Outcome.SUCCEEDED
    after = target.read_bytes()
    assert after == before.replace(b"SHOPPING_WORDPRESS_PORT=58081", b"SHOPPING_WORDPRESS_PORT=58082")
    assert after.endswith(b"\n") is False
    current = target.stat()
    assert (current.st_uid, current.st_gid, current.st_mode & 0o777) == (
        metadata.st_uid, metadata.st_gid, metadata.st_mode & 0o777)


@pytest.mark.parametrize("raw", [b"SHOPPING_DB_PASSWORD=bad\xff\n", b"BROKEN\n",
    b"SHOPPING_UNKNOWN=x\n", b"SHOPPING_DB_NAME=x\nSHOPPING_DB_NAME=y\n"])
def test_invalid_source_fails_without_publication(tmp_path: Path, raw: bytes) -> None:
    before = payload() + raw
    target, capability = fixture(tmp_path, before)
    assert capability.replace_wordpress_port() is domain.Outcome.FAILED
    assert target.read_bytes() == before


def test_already_desired_capability_does_not_publish(tmp_path: Path, monkeypatch) -> None:
    target, capability = fixture(tmp_path, payload(b"58082"))
    monkeypatch.setattr(operator.os, "replace", lambda *_a, **_k: pytest.fail("published"))
    assert capability.replace_wordpress_port() is domain.Outcome.FAILED
    assert b"58082" in target.read_bytes()


def test_short_writes_exclusive_temp_fsync_and_parent_fsync(tmp_path: Path, monkeypatch) -> None:
    target, capability = fixture(tmp_path, payload())
    real_fsync = os.fsync
    fsyncs = []
    def synced(fd): fsyncs.append(fd); return real_fsync(fd)
    monkeypatch.setattr(operator.os, "fsync", synced)
    assert capability.replace_wordpress_port() is domain.Outcome.SUCCEEDED
    assert len(fsyncs) == 2
    assert "os.O_EXCL" in Path(operator.__file__).read_text()
    assert b"SHOPPING_WORDPRESS_PORT=58082" in target.read_bytes()


def test_write_all_handles_short_writes(tmp_path: Path, monkeypatch) -> None:
    destination = tmp_path / "short-write"
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    real_write, calls = os.write, []
    def short(target_fd, data):
        calls.append(len(data))
        return real_write(target_fd, data[:max(1, len(data) // 2)])
    monkeypatch.setattr(operator.os, "write", short)
    try:
        operator._write_all(fd, b"exact transformed bytes")
    finally:
        os.close(fd)
    assert destination.read_bytes() == b"exact transformed bytes" and len(calls) > 1


def test_identity_drift_before_replace_fails_and_cleans_temp(tmp_path: Path, monkeypatch) -> None:
    target, capability = fixture(tmp_path, payload())
    real_stat, count = operator.os.stat, {"n": 0}
    def drift(*args, **kwargs):
        value = real_stat(*args, **kwargs)
        if kwargs.get("dir_fd") is not None and args[0] == source.SOURCE_COMPONENTS[-1]:
            target.write_bytes(target.read_bytes() + b"# drift\n")
        return value
    monkeypatch.setattr(operator.os, "stat", drift)
    assert capability.replace_wordpress_port() is domain.Outcome.FAILED
    assert not list(target.parent.glob("*.tmp-*"))


def test_publish_exception_uncertain_and_at_most_once(tmp_path: Path, monkeypatch) -> None:
    _target, capability = fixture(tmp_path, payload())
    calls = []
    def fail(*args, **kwargs): calls.append((args, kwargs)); raise OSError("opaque")
    monkeypatch.setattr(operator.os, "replace", fail)
    assert capability.replace_wordpress_port() is domain.Outcome.UNCERTAIN
    assert len(calls) == 1


def test_one_authorization_cannot_execute_twice() -> None:
    events, auth = [], Auth([])
    for _ in range(2):
        domain.execute_remediation(initial_observation=observation(),
            observe_source=lambda: observation(), authorization=auth, mutation=Mutation(events, domain.Outcome.FAILED))
    assert events == [("mutation",)]


def test_json_is_value_free_and_authority_fixed() -> None:
    result = domain.execute_remediation(initial_observation=observation(),
        observe_source=lambda: observation(), authorization=None, mutation=Mutation([]))
    projection = result.to_json_safe(); encoded = json.dumps(projection)
    assert projection["expected_key"] == source.WORDPRESS_PORT_KEY
    assert projection["expected_value"] == "58082"
    assert projection["production_authority"] is projection["ubuntu_authority"] is False
    assert projection["automatic_retry"] is False
    assert projection["database_mutation_allowed"] is False
    assert projection["wordpress_runtime_mutation_allowed"] is False
    assert all(projection[key] is False for key in ("secret_values_retained", "secret_values_emitted",
        "secret_values_logged", "secret_values_hashed", "secret_values_semantically_compared"))
    assert "58081" not in encoded and SECRET_MARKER not in encoded
    assert tuple(inspect.signature(operator.run).parameters) == ()


def test_public_operator_fails_closed_and_rejects_caller_authorization(monkeypatch) -> None:
    monkeypatch.setattr(operator, "_replace_wordpress_port_at_trusted_source",
                        lambda **_kwargs: pytest.fail("mutation executed"))
    class AbsentStore:
        @classmethod
        def open_existing(cls): raise RuntimeError("unavailable")
    monkeypatch.setattr(operator, "RuntimeCutoverSourceAuthorizationStore", AbsentStore)
    monkeypatch.setattr(operator, "observe_runtime_cutover_source", observation)
    result = operator.run()
    assert result.classification is domain.Classification.CANDIDATE
    assert not result.authorization_consumed and not result.mutation_executed
    with pytest.raises(TypeError):
        operator.run(authorization=Auth([], allowed=True))


def test_public_operator_absent_store_has_zero_filesystem_mutation(monkeypatch, tmp_path) -> None:
    class Home: passwd_home = str(tmp_path); bound_uid = os.getuid()
    class Ownership: expected_uid = os.getuid(); expected_gid = os.getgid()
    monkeypatch.setattr(auth_store, "resolve_trusted_mac_account_home", lambda: Home())
    monkeypatch.setattr(auth_store, "issue_trusted_ownership_expectation", lambda _home: Ownership())
    monkeypatch.setattr(operator, "observe_runtime_cutover_source", observation)
    before = tuple(tmp_path.rglob("*"))
    result = operator.run()
    assert tuple(tmp_path.rglob("*")) == before
    assert not result.authorization_consumed and not result.mutation_executed


def test_public_operator_empty_store_changes_no_durable_state(monkeypatch, tmp_path) -> None:
    class Home: passwd_home = str(tmp_path); bound_uid = os.getuid()
    class Ownership: expected_uid = os.getuid(); expected_gid = os.getgid()
    path = tmp_path.joinpath(*auth_store._COMPONENTS)
    auth_store.RuntimeCutoverSourceAuthorizationStore._for_test(
        path, uid=os.getuid(), gid=os.getgid())
    monkeypatch.setattr(auth_store, "resolve_trusted_mac_account_home", lambda: Home())
    monkeypatch.setattr(auth_store, "issue_trusted_ownership_expectation", lambda _home: Ownership())
    monkeypatch.setattr(operator, "observe_runtime_cutover_source", observation)
    before = path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns
    result = operator.run()
    assert (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns) == before
    assert not result.authorization_consumed and not result.mutation_executed


def test_operator_exports_only_inert_run_and_no_public_mutation_api() -> None:
    assert operator.__all__ == ("run",)
    assert not hasattr(operator, "AtomicRuntimeCutoverPortMutation")
    exported = {name: getattr(operator, name) for name in operator.__all__}
    assert exported == {"run": operator.run}
    assert all("mutation" not in name.lower() for name in exported)


def test_private_capability_resolves_trust_internally(monkeypatch) -> None:
    sentinel_home, sentinel_ownership, calls = object(), object(), []
    monkeypatch.setattr(operator, "resolve_trusted_mac_account_home",
                        lambda: calls.append("home") or sentinel_home)
    monkeypatch.setattr(operator, "issue_trusted_ownership_expectation",
                        lambda home: calls.append(("ownership", home)) or sentinel_ownership)
    def replace(**kwargs):
        calls.append(("replace", kwargs))
        return domain.Outcome.SUCCEEDED
    monkeypatch.setattr(operator, "_replace_wordpress_port_at_trusted_source", replace)
    assert operator._AtomicRuntimeCutoverPortMutation().replace_wordpress_port() is domain.Outcome.SUCCEEDED
    assert calls[:2] == ["home", ("ownership", sentinel_home)]
    assert calls[2][1] == {"resolved_home": sentinel_home,
                           "ownership": sentinel_ownership, "repository_root": operator._ROOT}
    assert source.SOURCE_COMPONENTS == ("Library", "Application Support", "AIControlCenter",
                                        "secrets", "shopping-commerce.env")
    assert source.WORDPRESS_PORT_KEY == "SHOPPING_WORDPRESS_PORT"
    assert domain.DESIRED_VALUE == "58082"


def test_classifier_rejects_observation_subclass_and_foreign_object() -> None:
    class ObservationSubclass(source.RuntimeCutoverSourceObservation):
        pass
    subclass = ObservationSubclass(**{
        field: getattr(observation(), field)
        for field in source.RuntimeCutoverSourceObservation.__dataclass_fields__
    })
    for invalid in (subclass, object()):
        decision = domain.classify_candidate(invalid)
        assert decision.classification is domain.Classification.BLOCKED
        assert decision.reason_codes == ("SOURCE_OBSERVATION_INVALID",)
