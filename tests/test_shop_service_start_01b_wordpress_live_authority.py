from __future__ import annotations
import builtins, inspect, os, sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from core.shopping import runtime_cutover_source_authorization as source_authority
from core.shopping import wordpress_port_authorization as domain
from ops.macos.shopping import issue_wordpress_port_authorization as issuer
from ops.macos.shopping import wordpress_port_live_operator as operator
from ops.macos.shopping.wordpress_port_authorization_store import WordPressAuthorizationStoreError, WordPressPortAuthorizationStore

def authorization(**changes):
    now=datetime.now(timezone.utc); values={**domain.immutable_contract(uid=os.getuid(),gid=os.getgid()),"authorization_id":"wp-auth","issued_at":(now-timedelta(seconds=1)).isoformat(),"expires_at":(now+timedelta(minutes=5)).isoformat()}; values.update(changes)
    value=object.__new__(domain.WordPressMutationAuthorization)
    for name in value.__dataclass_fields__: object.__setattr__(value,name,values[name])
    return value

def consumption_result(**changes):
    auth = authorization(**changes)
    receipt = object.__new__(domain.WordPressMutationConsumptionReceipt)
    for name in receipt.__dataclass_fields__:
        object.__setattr__(
            receipt, name,
            domain.ConsumptionState.COMMITTED if name == "state" else getattr(auth, name),
        )
    result = object.__new__(domain.WordPressMutationConsumptionResult)
    object.__setattr__(result, "receipt", receipt)
    return result

def source_domain_values():
    now = datetime.now(timezone.utc)
    values = {
        "authorization_id": "source-auth",
        "issued_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "trusted_uid": os.getuid(),
        "trusted_gid": os.getgid(),
        "authoritative_work_item": source_authority.AUTHORITATIVE_WORK_ITEM,
        "environment": source_authority.ENVIRONMENT,
        "mutation_id": source_authority.MUTATION_ID,
        "source_role": source_authority.SOURCE_ROLE,
        "source_key": source_authority.WORDPRESS_PORT_KEY,
        "desired_value": source_authority.DESIRED_VALUE,
        "maximum_uses": source_authority.MAXIMUM_USES,
        "production_authority": False,
        "ubuntu_authority": False,
    }
    authorization_value = object.__new__(source_authority.SourceMutationAuthorization)
    for name in authorization_value.__dataclass_fields__:
        object.__setattr__(authorization_value, name, values[name])
    receipt = object.__new__(source_authority.SourceMutationConsumptionReceipt)
    for name in receipt.__dataclass_fields__:
        object.__setattr__(
            receipt, name,
            source_authority.ConsumptionState.COMMITTED
            if name == "state" else values[name],
        )
    result = object.__new__(source_authority.SourceMutationConsumptionResult)
    object.__setattr__(result, "receipt", receipt)
    return authorization_value, result, receipt

def store(tmp_path,fault=None): return WordPressPortAuthorizationStore._for_test(tmp_path/"authority.sqlite3",uid=os.getuid(),gid=os.getgid(),fault=fault)
def tree(path): return tuple(sorted((str(p.relative_to(path)),p.stat().st_mode,p.stat().st_size,p.stat().st_mtime_ns) for p in path.rglob("*"))) if path.exists() else ()

def test_public_surfaces_are_zero_argument_and_operator_exports_only_run():
    assert tuple(inspect.signature(issuer.issue).parameters)==()
    assert tuple(inspect.signature(operator.run).parameters)==()
    assert operator.__all__ == ("run",)

def test_non_tty_denied(monkeypatch):
    monkeypatch.setattr(issuer.sys.stdin,"isatty",lambda:False); monkeypatch.setattr(issuer.sys.stdout,"isatty",lambda:True)
    with pytest.raises(RuntimeError,match="TTY"): issuer.issue()

def test_wrong_ack_does_not_create_store(monkeypatch):
    monkeypatch.setattr(issuer.sys.stdin,"isatty",lambda:True); monkeypatch.setattr(issuer.sys.stdout,"isatty",lambda:True)
    monkeypatch.setattr(builtins,"input",lambda _:"no"); monkeypatch.setattr(builtins,"print",lambda *a,**k:None)
    monkeypatch.setattr(issuer.WordPressPortAuthorizationStore,"_initialize_for_issuer",lambda:pytest.fail("created"))
    with pytest.raises(RuntimeError,match="acknowledgement"): issuer.issue()

def test_contract_exact_and_identity_expiry_bool_foreign_rejected():
    value=authorization(); now=datetime.now(timezone.utc); domain.validate_authorization(value,now=now,uid=os.getuid(),gid=os.getgid())
    for bad in (True,object(),authorization(mutation_id=source_authority.MUTATION_ID),authorization(trusted_uid=os.getuid()+1),authorization(expires_at=(now-timedelta(seconds=2)).isoformat())):
        with pytest.raises(domain.AuthorizationError): domain.validate_authorization(bad,now=now,uid=os.getuid(),gid=os.getgid())
    for bad in (True,object()):
        with pytest.raises(domain.AuthorizationError): domain.validate_consumption_result(bad,now=now,uid=os.getuid(),gid=os.getgid())

@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("authorization_id", ""), ("authorization_id", 1),
        ("issued_at", 1), ("expires_at", 1),
        ("trusted_uid", True), ("trusted_gid", False),
        ("authoritative_work_item", object()), ("environment", object()),
        ("mutation_id", object()), ("target_context", object()),
        ("compose_project", object()), ("compose_file", object()),
        ("compose_service", object()), ("database_container", object()),
        ("wordpress_container", object()), ("expected_before_binding", object()),
        ("expected_after_binding", object()), ("maximum_uses", True),
        ("production_authority", 0), ("ubuntu_authority", 0),
    ],
)
def test_every_authorization_field_enforces_exact_type(field, bad_value):
    with pytest.raises(domain.AuthorizationError):
        domain.validate_authorization(
            authorization(**{field: bad_value}), now=datetime.now(timezone.utc),
            uid=os.getuid(), gid=os.getgid(),
        )

def test_consumption_validation_rejects_wrong_bindings_types_and_identity():
    now = datetime.now(timezone.utc)
    changes = (
        {"mutation_id": "wrong"}, {"environment": "wrong"},
        {"target_context": "wrong"}, {"compose_project": "wrong"},
        {"compose_file": "wrong"}, {"compose_service": "wrong"},
        {"expected_before_binding": "wrong"},
        {"expected_after_binding": "wrong"}, {"production_authority": 0},
        {"ubuntu_authority": 0}, {"maximum_uses": True},
        {"trusted_uid": os.getuid() + 1}, {"trusted_gid": os.getgid() + 1},
    )
    for change in changes:
        with pytest.raises(domain.AuthorizationError):
            domain.validate_consumption_result(
                consumption_result(**change), now=now, uid=os.getuid(), gid=os.getgid(),
            )

def test_source_authority_domain_types_never_satisfy_wordpress_validation():
    source_auth, source_result, source_receipt = source_domain_values()
    now = datetime.now(timezone.utc)
    with pytest.raises(domain.AuthorizationError):
        domain.validate_authorization(source_auth, now=now, uid=os.getuid(), gid=os.getgid())
    for value in (source_result, source_receipt):
        with pytest.raises(domain.AuthorizationError):
            domain.validate_consumption_result(value, now=now, uid=os.getuid(), gid=os.getgid())

def test_sqlite_row_reconstruction_validates_then_returns_exact_false():
    fields = list(domain.WordPressMutationAuthorization.__dataclass_fields__)
    row = [getattr(authorization(), name) for name in fields]
    row[fields.index("production_authority")] = 0
    row[fields.index("ubuntu_authority")] = 0
    row = tuple(row)
    rebuilt = WordPressPortAuthorizationStore._authorization(row)
    assert rebuilt.maximum_uses == 1 and type(rebuilt.maximum_uses) is int
    assert rebuilt.production_authority is False
    assert rebuilt.ubuntu_authority is False
    for field in ("production_authority", "ubuntu_authority"):
        values = list(row)
        values[fields.index(field)] = True
        with pytest.raises(WordPressAuthorizationStoreError):
            WordPressPortAuthorizationStore._authorization(tuple(values))

def test_absent_and_empty_operator_discovery_are_read_only(tmp_path):
    missing=tmp_path/"missing"/"authority.sqlite3"; before=tree(tmp_path)
    with pytest.raises(Exception): WordPressPortAuthorizationStore._open_existing_for_test(missing,uid=os.getuid(),gid=os.getgid())
    assert tree(tmp_path)==before

def test_public_operator_absent_store_has_no_write_or_compose_side_effect(monkeypatch):
    calls = []
    monkeypatch.setattr(
        operator.WordPressPortAuthorizationStore, "open_existing",
        lambda: (_ for _ in ()).throw(FileNotFoundError("absent")),
    )
    monkeypatch.setattr(
        operator.WordPressPortAuthorizationStore, "_initialize_for_issuer",
        lambda: pytest.fail("schema initialized"),
    )
    monkeypatch.setattr(operator, "_command", lambda _argv: pytest.fail("command executed"))
    monkeypatch.setattr(
        operator, "execute_reconciliation",
        lambda **kwargs: calls.append(kwargs) or "READ_ONLY",
    )
    assert operator.run() == "READ_ONLY"
    assert len(calls) == 1 and calls[0]["authorization"] is None

@pytest.mark.parametrize("expired", [False, True])
def test_public_operator_empty_or_expired_store_is_read_only(
    monkeypatch, tmp_path, expired,
):
    value = store(tmp_path)
    if expired:
        value._issue(authorization())
        with sqlite3.connect(value._path) as db:
            db.execute(
                "UPDATE wordpress_mutation_authorizations SET expires_at=?",
                ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),),
            )
    before = tree(tmp_path)
    monkeypatch.setattr(
        operator.WordPressPortAuthorizationStore, "open_existing",
        lambda: WordPressPortAuthorizationStore._open_existing_for_test(
            value._path, uid=os.getuid(), gid=os.getgid(),
        ),
    )
    monkeypatch.setattr(operator, "_command", lambda _argv: pytest.fail("command executed"))
    captured = []
    monkeypatch.setattr(
        operator, "execute_reconciliation",
        lambda **kwargs: captured.append(kwargs) or "READ_ONLY",
    )
    assert operator.run() == "READ_ONLY"
    assert tree(tmp_path) == before
    assert len(captured) == 1 and captured[0]["authorization"] is None
    value=store(tmp_path); before=tree(tmp_path)
    with pytest.raises(domain.AuthorizationError): WordPressPortAuthorizationStore._open_existing_for_test(value._path,uid=os.getuid(),gid=os.getgid())
    assert tree(tmp_path)==before

def test_store_security_schema_and_single_outstanding(tmp_path):
    value=store(tmp_path); value._issue(authorization())
    with pytest.raises(domain.AuthorizationError): value._issue(authorization(authorization_id="two"))
    value._path.chmod(0o644)
    with pytest.raises(WordPressAuthorizationStoreError): WordPressPortAuthorizationStore._open_existing_for_test(value._path,uid=os.getuid(),gid=os.getgid())

def test_foreign_schema_and_symlink_fail_closed(tmp_path):
    path=tmp_path/"authority.sqlite3"
    with sqlite3.connect(path) as db: db.execute("CREATE TABLE foreign_data(x)")
    path.chmod(0o600)
    with pytest.raises(WordPressAuthorizationStoreError): store(tmp_path)
    path.unlink(); target=tmp_path/"target"; target.write_text(""); target.chmod(0o600); path.symlink_to(target)
    with pytest.raises(WordPressAuthorizationStoreError): store(tmp_path)

def test_durable_replay_restart_and_concurrency(tmp_path):
    value=store(tmp_path); value._issue(authorization()); result=value.consume()
    assert result.receipt.state is domain.ConsumptionState.COMMITTED
    with pytest.raises(domain.AuthorizationError): store(tmp_path).consume()
    other=tmp_path/"other"; other.mkdir(); first=store(other); first._issue(authorization(authorization_id="concurrent")); second=store(other)
    def consume(s):
        try: s.consume(); return "OK"
        except Exception: return "DENIED"
    with ThreadPoolExecutor(max_workers=2) as pool: assert sorted(pool.map(consume,(first,second)))==["DENIED","OK"]

def test_stranded_claim_and_ambiguous_commit(tmp_path):
    def strand(stage,_db):
        if stage=="after_claim_commit": raise RuntimeError("stop")
    value=store(tmp_path,strand); value._issue(authorization())
    with pytest.raises(RuntimeError): value.consume()
    with pytest.raises(domain.AuthorizationError): store(tmp_path).consume()
    other=tmp_path/"other"; other.mkdir()
    def ambiguous(stage,_db):
        if stage=="after_final_commit": raise sqlite3.OperationalError("ambiguous")
    value=store(other,ambiguous); value._issue(authorization(authorization_id="ambiguous")); assert value.consume().receipt.state is domain.ConsumptionState.COMMITTED

def test_runner_accepts_only_exact_invocation(monkeypatch):
    class Completed: returncode=0
    monkeypatch.setattr(operator,"_command",lambda argv:Completed())
    from core.shopping.wordpress_port_reconciliation import MutationInvocation, ExecutionOutcome, build_mutation_invocation
    assert operator._run_compose(build_mutation_invocation()) is ExecutionOutcome.SUCCEEDED
    with pytest.raises(ValueError): operator._run_compose(MutationInvocation(("docker","compose","down")))

def _trusted_execution_boundary(monkeypatch, tmp_path):
    repository = tmp_path / "repository"
    compose = repository / "deploy/shopping/compose.yaml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services: {}\n")
    prefix = tmp_path / "homebrew"
    executable = prefix / "Cellar/docker/1/bin/docker"
    executable.parent.mkdir(parents=True)
    executable.write_text("binary")
    executable.chmod(0o755)
    entrypoint = prefix / "bin/docker"
    entrypoint.parent.mkdir()
    entrypoint.symlink_to(executable)
    monkeypatch.setattr(operator, "_REPOSITORY_ROOT", repository)
    monkeypatch.setattr(operator, "_TRUSTED_EXECUTABLE_ROOT", prefix)
    monkeypatch.setattr(operator, "_TRUSTED_DOCKER_ENTRYPOINT", entrypoint)
    return repository, executable

def test_mutation_anchors_compose_and_subprocess_to_repository(monkeypatch, tmp_path):
    repository, executable = _trusted_execution_boundary(monkeypatch, tmp_path)
    caller = tmp_path / "caller"
    fake_compose = caller / "deploy/shopping/compose.yaml"
    fake_compose.parent.mkdir(parents=True)
    fake_compose.write_text("attacker-controlled")
    calls = []
    class Completed: returncode = 0
    monkeypatch.setattr(operator.subprocess, "run", lambda argv, **kwargs: calls.append((argv, kwargs)) or Completed())
    previous = Path.cwd()
    try:
        os.chdir(caller)
        assert operator._run_compose(domain_invocation()) is operator.ExecutionOutcome.SUCCEEDED
    finally:
        os.chdir(previous)
    argv, kwargs = calls[0]
    assert argv[0] == str(executable.resolve())
    assert argv[7] == "deploy/shopping/compose.yaml"
    assert kwargs["cwd"] == repository
    assert (kwargs["cwd"] / argv[7]).read_text() == "services: {}\n"

def domain_invocation():
    from core.shopping.wordpress_port_reconciliation import build_mutation_invocation
    return build_mutation_invocation()

def test_caller_path_and_docker_compose_selectors_are_not_authoritative(monkeypatch, tmp_path):
    _, executable = _trusted_execution_boundary(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "attacker"))
    for name in operator._DOCKER_SELECTION_VARIABLES:
        monkeypatch.setenv(name, "attacker-selected")
    calls = []
    class Completed: returncode = 0
    monkeypatch.setattr(operator.subprocess, "run", lambda argv, **kwargs: calls.append((argv, kwargs)) or Completed())
    assert operator._run_compose(domain_invocation()) is operator.ExecutionOutcome.SUCCEEDED
    argv, kwargs = calls[0]
    assert argv[0] == str(executable.resolve())
    assert kwargs["env"]["PATH"] == operator._FIXED_PATH
    assert kwargs["env"]["DOCKER_CONFIG"].endswith("/.docker")
    assert all(kwargs["env"].get(name) != "attacker-selected" for name in operator._DOCKER_SELECTION_VARIABLES)

def test_trusted_docker_resolution_failure_fails_before_mutation(monkeypatch, tmp_path):
    repository = tmp_path / "repository"
    compose = repository / "deploy/shopping/compose.yaml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services: {}\n")
    monkeypatch.setattr(operator, "_REPOSITORY_ROOT", repository)
    monkeypatch.setattr(operator, "_TRUSTED_DOCKER_ENTRYPOINT", tmp_path / "missing/docker")
    monkeypatch.setattr(operator, "_TRUSTED_EXECUTABLE_ROOT", tmp_path / "trusted")
    monkeypatch.setattr(operator.subprocess, "run", lambda *_a, **_k: pytest.fail("mutation executed"))
    assert operator._run_compose(domain_invocation()) is operator.ExecutionOutcome.UNCERTAIN

def test_unsafe_or_unexpected_docker_resolution_is_rejected(monkeypatch, tmp_path):
    _, executable = _trusted_execution_boundary(monkeypatch, tmp_path)
    executable.chmod(0o777)
    with pytest.raises(RuntimeError, match="unsafe"):
        operator._trusted_docker_executable()
    outside = tmp_path / "outside/docker"
    outside.parent.mkdir()
    outside.write_text("binary")
    outside.chmod(0o755)
    operator._TRUSTED_DOCKER_ENTRYPOINT.unlink()
    operator._TRUSTED_DOCKER_ENTRYPOINT.symlink_to(outside)
    with pytest.raises(RuntimeError, match="unexpected"):
        operator._trusted_docker_executable()
