"""Fixture-only 01G1D tests: no Docker, live issuer or live authority store."""
from datetime import datetime, timedelta, timezone
import inspect
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

import pytest

from core.shopping import wordpress_recovery_reconciliation as c
from core.shopping import wordpress_recovery_authorization as a
from core.shopping import wordpress_port_authorization as old
from ops.macos.shopping import wordpress_recovery_operator as op
from ops.macos.shopping import issue_wordpress_recovery_authorization as issuer
from ops.macos.shopping.wordpress_recovery_authorization_store import WordPressRecoveryAuthorizationStore as Store
from ops.macos.shopping.wordpress_port_authorization_store import WordPressPortAuthorizationStore as OldStore


def snapshot(post=False):
    networks = {name: dict(id=c.NETWORK_IDS[name], internal=(name == c.NETWORKS[0])) for name, char in zip(c.NETWORKS, 'ab')}
    containers = {}
    for service, char in [('wordpress', 'c' if not post else 'd'), ('database', 'e')]:
        containers[service] = dict(id=(c.DATABASE_ID if service == 'database' else ('d'*64 if post else c.FAILED_ID)), started=('2026-09-03T03:10:22.559242003Z' if service == 'database' else ('2026-09-08T01:00:00.123Z' if post else '0001-01-01T00:00:00Z')), restart_count=0,
            status='created' if service == 'wordpress' and not post else 'running',
            pid=0 if service == 'wordpress' and not post else 123, exit_code=127 if service == 'wordpress' and not post else 0,
            running=service == 'database' or post, healthy=service == 'database' or post, paused=False, restarting=False, image='sha256:' + 'f' * 64,
            configured_image=c.WORDPRESS_IMAGE if service == 'wordpress' else 'mariadb:11.4.12@sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7',
            project=c.COMPOSE_PROJECT, service=service, network_mode=c.NETWORKS[0],
            host_ports={'80/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '58082'}]} if service == 'wordpress' else {},
            ports={'80/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '58082'}]} if service == 'wordpress' else {'3306/tcp': None},
            networks={name: networks[name]['id'] for name in (c.NETWORKS if service == 'wordpress' else c.NETWORKS[:1])},
            mounts=c.expected_mounts(post) if service == 'wordpress' else [c.volume_mount(c.VOLUMES[1], '/var/lib/mysql')])
    return dict(head='1' * 40, clean=True, artifacts=dict(c.ARTIFACTS), **containers,
                image=dict(id='sha256:'+'f'*64, digest='wordpress@'+c.WORDPRESS_IMAGE.split('@')[1]),
                volumes={name: dict(Name=name, Driver='local', Scope='local', CreatedAt=c.VOLUME_CREATED[name]) for name in c.VOLUMES},
                networks=networks, source_metadata=dict(st_dev=1, st_ino=2, st_mode=33152, st_uid=os.getuid(), st_gid=os.getgid(), st_size=20, st_nlink=1, st_mtime_ns=1, st_ctime_ns=1),
                production=False, ubuntu=False)


def auth(**changes):
    now = datetime.now(timezone.utc)
    values = dict(a.immutable_contract(uid=os.getuid(), gid=os.getgid()),
                  authorization_id='fc29348b-dfde-4ba3-89f3-93a32a12b857', issued_at=(now-timedelta(seconds=1)).isoformat(),
                  expires_at=(now+timedelta(minutes=5)).isoformat(), precondition_json=c.canonical_snapshot(snapshot()))
    values.update(changes)
    result = object.__new__(a.WordPressMutationAuthorization)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def store(tmp_path, fault=None):
    value = Store._for_test(tmp_path / 'authority.sqlite3', uid=os.getuid(), gid=os.getgid(), fault=fault)
    value._issue(auth())
    return value


def state(value):
    with sqlite3.connect(value._path) as db:
        return db.execute('SELECT state FROM wordpress_mutation_authorizations').fetchone()[0]


def test_distinct_one_shot(tmp_path):
    value = store(tmp_path)
    receipt = value.consume(snapshot)
    assert a.validate_consumption_result(receipt, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid()).mutation_id == 'SHOP-SERVICE-START-01G1D:WORDPRESS_RUNTIME_GENERATION_RECOVERY'
    assert state(value) == 'COMMITTED'
    with pytest.raises(a.ConsumptionFailure):
        value.consume(snapshot)
    with pytest.raises(old.AuthorizationError):
        old.validate_consumption_result(receipt, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        OldStore._open_existing_for_test(value._path, uid=os.getuid(), gid=os.getgid())


@pytest.mark.parametrize('changes', [dict(mutation_id=old.MUTATION_ID), dict(authoritative_work_item='SHOP-SERVICE-START-01B'),
    dict(compose_service='database'), dict(compose_service='wordpress-cli'), dict(target_context='other'), dict(compose_project='other'),
    dict(compose_file='elsewhere'), dict(maximum_uses=2), dict(production_authority=True), dict(ubuntu_authority=True)])
def test_authorization_rejects_scope_changes(changes):
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(auth(**changes), now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())


DRIFTS = [
    ('head', '2'*40), ('clean', False), ('artifacts', {}), ('production', True), ('ubuntu', True),
    ('wordpress.id', '9'*64), ('wordpress.started', '2026-09-08T02:00:00Z'), ('wordpress.restart_count', 1),
    ('wordpress.image', 'sha256:'+'9'*64), ('wordpress.healthy', True), ('wordpress.mounts', []),
    ('database.id', '9'*64), ('database.started', '2026-09-08T02:00:00Z'), ('database.restart_count', 1),
    ('database.healthy', False), ('database.ports', {'3306/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '3306'}]}),
    ('wordpress.ports', {'80/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '58082'}]}),
    ('wordpress.networks', {}), ('database.networks', {}), ('networks.ai-shopping-internal.id', '9'*64),
    ('networks.ai-shopping-network.id', '9'*64), ('networks.ai-shopping-internal.internal', False),
    ('volumes.ai-shopping-wordpress.CreatedAt', '2026-09-01T01:00:00Z'),
    ('volumes.ai-shopping-database.CreatedAt', '2026-09-01T01:00:00Z'),
    ('volumes.ai-shopping-wordpress.Driver', 'other'), ('volumes.ai-shopping-database.Scope', 'global'),
    ('source_metadata.st_ino', 999), ('source_metadata.st_mtime_ns', 999),
]


def change(value, path, replacement):
    parts = path.split('.')
    for part in parts[:-1]:
        value = value[part]
    value[parts[-1]] = replacement


@pytest.mark.parametrize('path,replacement', DRIFTS)
def test_bound_drift_before_consumption(tmp_path, path, replacement):
    value = store(tmp_path)
    drift = snapshot()
    change(drift, path, replacement)
    with pytest.raises(a.ConsumptionFailure) as error:
        value.consume(lambda: drift)
    assert error.value.state is c.AuthorizationConsumptionState.NOT_CONSUMED
    assert state(value) == 'AVAILABLE'


@pytest.mark.parametrize('path,replacement', [x for x in DRIFTS if x[0] not in {'wordpress.id', 'wordpress.started', 'wordpress.restart_count'}])
def test_postconditions_reject_drift(path, replacement):
    after = snapshot(True)
    change(after, path, False if path == 'wordpress.healthy' else replacement)
    with pytest.raises(ValueError):
        c.validate_post(snapshot(), after)


def test_generation_must_change_and_four_mounts():
    c.validate_post(snapshot(), snapshot(True))
    after = snapshot(True)
    after['wordpress']['id'] = snapshot()['wordpress']['id']
    with pytest.raises(ValueError): c.validate_post(snapshot(), after)
    for mutate in [lambda m: m.pop(), lambda m: m.append(m[0]), lambda m: m[1].update(rw=True),
                   lambda m: m[1].update(destination=m[0]['destination']), lambda m: m[0].update(name='other')]:
        after = snapshot(True)
        mutate(after['wordpress']['mounts'])
        with pytest.raises(ValueError): c.validate_post(snapshot(), after)


def test_fixed_execution_no_target_or_removal(monkeypatch):
    from core.shopping import wordpress_port_reconciliation as port
    monkeypatch.setattr(port, '_trusted_runtime_cutover_path', lambda: '/trusted/source.env')
    monkeypatch.setattr(op.trusted, '_trusted_compose_executable', lambda: '/trusted/docker-compose')
    monkeypatch.setattr(op.trusted, '_trusted_docker_executable', lambda: '/trusted/docker')
    monkeypatch.setattr(op.trusted, '_fixed_environment', lambda: {'PATH': '/fixed'})
    calls = []
    monkeypatch.setattr(op.subprocess, 'run', lambda *args, **kw: calls.append((args, kw)) or SimpleNamespace(returncode=0))
    mutate = op._prepare_mutation()
    assert not inspect.signature(op.run).parameters
    assert not inspect.signature(op._prepare_mutation).parameters
    assert not inspect.signature(mutate).parameters
    assert not inspect.signature(c.build_mutation_invocation).parameters
    assert mutate() is c.ExecutionOutcome.SUCCEEDED
    assert calls[0][0][0] == ('/trusted/docker', '--context', 'colima-aicontrolcenter-commerce', 'compose', '--project-name', 'ai-shopping', '--file', 'deploy/shopping/compose.yaml', '--env-file', '/trusted/source.env', 'up', '-d', '--no-deps', '--pull', 'never', '--force-recreate', 'wordpress')
    assert calls[0][1]['stdout'] == op.subprocess.DEVNULL
    assert len(calls) == 1


def wire(monkeypatch, value, outcome):
    monkeypatch.setattr(op, 'resolve_trusted_mac_account_home', lambda: object())
    monkeypatch.setattr(op, 'issue_trusted_ownership_expectation', lambda _: SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid()))
    monkeypatch.setattr(op.WordPressRecoveryAuthorizationStore, 'open_existing', lambda: value)
    monkeypatch.setattr(op, 'observe_preconditions', snapshot)
    calls = []
    def mutate():
        calls.append('mutation')
        if isinstance(outcome, Exception): raise outcome
        return outcome
    monkeypatch.setattr(op, '_prepare_mutation', lambda: mutate)
    monkeypatch.setattr(op, '_validate_post', lambda _: True)
    return calls


@pytest.mark.parametrize('outcome,expected', [(c.ExecutionOutcome.SUCCEEDED, 'ACCEPTED'), (c.ExecutionOutcome.FAILED, 'UNCERTAIN'), (c.ExecutionOutcome.UNCERTAIN, 'UNCERTAIN'), (True, 'UNCERTAIN'), (RuntimeError('secret-canary'), 'UNCERTAIN')])
def test_no_retry_rollback_or_uncertain_acceptance(tmp_path, monkeypatch, outcome, expected):
    value = store(tmp_path)
    calls = wire(monkeypatch, value, outcome)
    result = op.run()
    assert result['status'] == expected
    assert calls == ['mutation'] and state(value) == 'COMMITTED'
    assert 'secret-canary' not in json.dumps(result)
    assert op.run()['status'] == 'BLOCKED'
    assert calls == ['mutation']


def test_operator_drift_never_mutates(tmp_path, monkeypatch):
    value = store(tmp_path)
    calls = wire(monkeypatch, value, c.ExecutionOutcome.SUCCEEDED)
    drift = snapshot(); drift['head'] = '2'*40
    monkeypatch.setattr(op, 'observe_preconditions', lambda: drift)
    assert op.run()['status'] == 'BLOCKED'
    assert state(value) == 'AVAILABLE' and calls == []


@pytest.mark.parametrize('stage', ['before_claim_commit', 'after_claim_commit', 'during_final_transaction', 'before_final_commit'])
def test_store_faults_fail_closed(tmp_path, monkeypatch, stage):
    def fault(where, _):
        if where == stage: raise RuntimeError('secret-canary')
    value = store(tmp_path, fault)
    calls = wire(monkeypatch, value, c.ExecutionOutcome.SUCCEEDED)
    result = op.run()
    assert result['status'] != 'ACCEPTED' and calls == []
    assert state(value) == ('AVAILABLE' if stage == 'before_claim_commit' else 'DURABLY_CLAIMED')
    assert 'secret-canary' not in json.dumps(result)


def test_concurrent_consumption_one_winner(tmp_path):
    value = store(tmp_path)
    def consume():
        try: value.consume(snapshot); return True
        except a.ConsumptionFailure: return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _: consume(), range(2))) == 1


def test_no_secret_or_authenticated_path():
    for payload in [snapshot(), snapshot(True)]:
        payload['capability'] = 'secret-canary'
        with pytest.raises(ValueError): c.validate_snapshot(payload)
    raw = json.dumps(c.projection('BLOCKED'))
    assert 'secret-canary' not in raw
    for path in [Path(op.__file__), Path(issuer.__file__)]:
        code = path.read_text()
        for forbidden in ['observe_runtime_cutover_source(', '_observe_records(', '.Config.Env', 'Health.Log', 'transport.', 'urllib', 'requests.', 'UbuntuWorkerClient', 'ssh']:
            assert forbidden not in code
    assert 'wordpress_port_authorization' not in Path(op.__file__).read_text()
    assert c.projection('BLOCKED')['production_authority'] is False
    assert c.projection('BLOCKED')['ubuntu_authority'] is False


def test_source_metadata_never_reads(monkeypatch):
    read = []
    metadata = SimpleNamespace(**snapshot()['source_metadata'])
    monkeypatch.setattr(op, 'resolve_trusted_mac_account_home', lambda: object())
    monkeypatch.setattr(op, 'issue_trusted_ownership_expectation', lambda _: object())
    monkeypatch.setattr(op, '_open_source', lambda *args: (SimpleNamespace(metadata=metadata), [99]))
    monkeypatch.setattr(op.os, 'close', lambda fd: read.append(('close', fd)))
    monkeypatch.setattr(op.os, 'read', lambda *args: pytest.fail('env content read'))
    assert op._source_metadata() == snapshot()['source_metadata']
    assert read == [('close', 99)]


def test_stable_observation_required(monkeypatch):
    first = snapshot(); second = snapshot(); second['wordpress']['restart_count'] = 1
    values = iter([first, second])
    monkeypatch.setattr(op, '_snapshot', lambda: next(values))
    with pytest.raises(ValueError): op.observe_preconditions()


def test_post_convergence_is_read_only_and_bounded(monkeypatch):
    calls = []
    monkeypatch.setattr(op, '_snapshot', lambda: calls.append(1) or snapshot())
    monkeypatch.setattr(op.time, 'sleep', lambda _: None)
    assert not op._validate_post(snapshot())
    assert len(calls) == 50
    monkeypatch.setattr(op, '_snapshot', lambda: snapshot(True))
    assert op._validate_post(snapshot())


def test_cli_rejects_overrides(monkeypatch, capsys):
    monkeypatch.setattr(op.sys, 'argv', ['operator', '--service', 'database'])
    monkeypatch.setattr(op, 'run', lambda: pytest.fail('must not run'))
    assert op.main() == 2
    monkeypatch.setattr(issuer, 'issue', lambda: pytest.fail('must not issue'))
    assert issuer.main() == 2
    assert 'CALLER_OVERRIDE_REJECTED' in capsys.readouterr().out


def test_01b_type_and_store_cannot_supply_authority(tmp_path):
    legacy = object.__new__(old.WordPressMutationAuthorization)
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(legacy, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    legacy_store = OldStore._for_test(tmp_path / 'old.sqlite3', uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        Store._open_existing_for_test(legacy_store._path, uid=os.getuid(), gid=os.getgid())


def test_successful_command_bad_post_not_accepted(tmp_path, monkeypatch):
    value = store(tmp_path)
    calls = wire(monkeypatch, value, c.ExecutionOutcome.SUCCEEDED)
    monkeypatch.setattr(op, '_validate_post', lambda _: False)
    assert op.run()['status'] == 'UNCERTAIN'
    assert calls == ['mutation']


def test_observation_error_before_claim_is_value_free(tmp_path, monkeypatch):
    value = store(tmp_path)
    calls = wire(monkeypatch, value, c.ExecutionOutcome.SUCCEEDED)
    def fail(): raise RuntimeError('secret-canary')
    monkeypatch.setattr(op, 'observe_preconditions', fail)
    result = op.run()
    assert result['authorization_consumed'] is False and not calls
    assert state(value) == 'AVAILABLE' and 'secret-canary' not in json.dumps(result)


@pytest.mark.parametrize('ack,drift,expected', [(issuer.ACKNOWLEDGEMENT, False, True), ('AUTHORIZE '+old.MUTATION_ID, False, False), (issuer.ACKNOWLEDGEMENT, True, False)])
def test_fixture_issuer_requires_exact_ack_and_stability(monkeypatch, capsys, ack, drift, expected):
    monkeypatch.setattr(issuer.sys, 'stdin', SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(issuer.sys, 'stdout', SimpleNamespace(isatty=lambda: True, write=lambda _: None, flush=lambda: None))
    monkeypatch.setattr(issuer, 'resolve_trusted_mac_account_home', lambda: object())
    monkeypatch.setattr(issuer, 'issue_trusted_ownership_expectation', lambda _: SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid()))
    later = snapshot()
    if drift: later['head'] = '2'*40
    observations = iter([snapshot(), later])
    monkeypatch.setattr(issuer, 'observe_preconditions', lambda: next(observations))
    monkeypatch.setattr('builtins.input', lambda _: ack)
    issued = []
    monkeypatch.setattr(issuer.WordPressRecoveryAuthorizationStore, '_initialize_for_issuer', lambda: SimpleNamespace(_issue=issued.append))
    if expected:
        assert issuer.issue()['status'] == 'AVAILABLE'
        assert len(issued) == 1
        a.validate_authorization(issued[0], now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    else:
        with pytest.raises(RuntimeError): issuer.issue()
        assert not issued


def test_inspection_commands_are_fixed_and_only_read_metadata(monkeypatch):
    monkeypatch.setattr(op.sys, 'platform', 'darwin')
    monkeypatch.setattr(op, '_source_metadata', lambda: snapshot()['source_metadata'])
    monkeypatch.setattr(op, '_repository', lambda: ('1'*40, dict(c.ARTIFACTS)))
    commands = []
    def read(args):
        commands.append(args)
        name = args[-1]
        if args[0] == 'image': return dict(id=snapshot()['image']['id'], digests=[snapshot()['image']['digest']])
        if args[0] == 'network': return snapshot()['networks'][name]
        if args[0] == 'volume': return snapshot()['volumes'][name]
        value = snapshot()['wordpress' if name == c.WORDPRESS_CONTAINER else 'database']
        value['healthy'] = 'healthy' if value['healthy'] else None
        value['networks'] = {k: {'NetworkID': v} for k, v in value['networks'].items()}
        value['mounts'] = [{k.title() if k != 'rw' else 'RW': v for k, v in m.items()} for m in value['mounts']]
        return value
    monkeypatch.setattr(op, '_read', read)
    result = op.observe_preconditions()
    c.validate_snapshot(result)
    assert len(commands) == 14
    assert all(command[1] == 'inspect' and command[2] == '--format' for command in commands)
    assert set(command[-1] for command in commands) == {c.WORDPRESS_IMAGE, c.WORDPRESS_CONTAINER, c.DATABASE_CONTAINER, *c.NETWORKS, *c.VOLUMES}


def test_repository_digest_and_clean_contract(monkeypatch):
    commands = []
    def git(args, **kwargs):
        commands.append(args)
        return SimpleNamespace(returncode=0, stdout=b'1'*40 if args[1] == 'rev-parse' else b'')
    monkeypatch.setattr(op.subprocess, 'run', git)
    import hashlib
    compose = c.ROOT / c.COMPOSE_FILE
    assert hashlib.sha256(compose.read_bytes()).hexdigest() == '0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c'
    assert c.ARTIFACTS[c.COMPOSE_FILE] == 'e90b116f9683d3ece0abc0111865ea41d9129a835070232e3a823c5c2e7e85ac'
    # Even a clean evolved repository cannot satisfy the consumed 01G1D contract.
    with pytest.raises(ValueError, match='GENERATION_IDENTITY_REJECTED'):
        op._repository()
    assert commands[-1][-1] == '--untracked-files=all'
    monkeypatch.setattr(op.subprocess, 'run', lambda *args, **kw: SimpleNamespace(returncode=0, stdout=b'dirty'))
    with pytest.raises(ValueError): op._repository()


@pytest.mark.parametrize('where', ['top', 'container', 'mount', 'image', 'volume', 'network', 'metadata'])
def test_secret_canary_rejected_from_persisted_schema(where):
    value = snapshot()
    target = {'top': value, 'container': value['wordpress'], 'mount': value['wordpress']['mounts'][0],
              'image': value['image'], 'volume': value['volumes'][c.VOLUMES[0]],
              'network': value['networks'][c.NETWORKS[0]], 'metadata': value['source_metadata']}[where]
    target['secret-canary'] = 'secret-canary'
    with pytest.raises(ValueError): c.canonical_snapshot(value)


def test_current_destination_and_historical_distinction():
    from core.shopping import wordpress_generation_reconciliation as historical
    current = c.expected_mounts(True)
    assert len(current) == 4
    assert '/etc/apache2/sites-available/000-default.conf' in {m['destination'] for m in current}
    assert '/etc/apache2/sites-enabled/000-default.conf' in {m['destination'] for m in historical.expected_mounts(True)}
    after = snapshot(True)
    after['wordpress']['mounts'] = c.expected_mounts(False)
    with pytest.raises(ValueError): c.validate_post(snapshot(), after)
    compose = (c.ROOT / c.COMPOSE_FILE).read_text()
    assert './config/shopping-apache-safety.conf:/etc/apache2/sites-available/000-default.conf:ro' in compose
    assert '/etc/apache2/sites-enabled/000-default.conf' not in compose


def test_recovery_cannot_reissue_or_use_historical_authority(tmp_path):
    from core.shopping import wordpress_generation_authorization as historical
    from ops.macos.shopping.wordpress_generation_authorization_store import WordPressGenerationAuthorizationStore
    value = store(tmp_path)
    receipt = value.consume(snapshot)
    with pytest.raises(a.AuthorizationError): value._issue(auth(authorization_id='another'))
    with pytest.raises(historical.AuthorizationError):
        historical.validate_consumption_result(receipt, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        WordPressGenerationAuthorizationStore._open_existing_for_test(value._path, uid=os.getuid(), gid=os.getgid())


@pytest.mark.parametrize('field,value', [('status','exited'), ('pid',1), ('exit_code',0), ('running',True), ('started','2026-09-08T00:00:00Z')])
def test_exact_failed_created_state(field, value):
    before = snapshot()
    c.validate_snapshot(before)
    before['wordpress'][field] = value
    with pytest.raises(ValueError): c.validate_snapshot(before)


@pytest.mark.parametrize('field,value', [('started','0001-01-01T00:00:00Z'), ('started','2026-99-99T00:00:00Z'), ('healthy',False), ('running',False), ('pid',0)])
def test_post_requires_valid_running_generation(field, value):
    after = snapshot(True)
    after['wordpress'][field] = value
    with pytest.raises(ValueError): c.validate_post(snapshot(), after)


def test_created_unattached_network_and_port_metadata_is_bound(tmp_path):
    before = snapshot()
    before['wordpress']['ports'] = {}
    before['wordpress']['networks'] = {name: '' for name in c.NETWORKS}
    c.validate_snapshot(before)
    value = Store._for_test(tmp_path / 'created.sqlite3', uid=os.getuid(), gid=os.getgid())
    value._issue(auth(precondition_json=c.canonical_snapshot(before)))
    drift = json.loads(json.dumps(before))
    drift['wordpress']['networks'][c.NETWORKS[0]] = c.NETWORK_IDS[c.NETWORKS[0]]
    with pytest.raises(a.ConsumptionFailure): value.consume(lambda: drift)
    assert state(value) == 'AVAILABLE'
    c.validate_post(before, snapshot(True))


def test_container_format_uses_optional_health_lookup():
    assert ".State.Health" not in op.CONTAINER_FORMAT
    assert 'index .State "Health"' in op.CONTAINER_FORMAT
