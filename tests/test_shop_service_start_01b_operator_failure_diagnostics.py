"""Offline fault injection for value-free, one-shot operator diagnostics."""
import json
import sqlite3

import pytest

from core.shopping import wordpress_port_reconciliation as r
from ops.macos.shopping import wordpress_port_live_operator as cli
from ops.macos.shopping import storage_continuity_observer as observer
from test_shop_service_start_01b_wordpress_port_reconciliation import (
    facts, storage, source, OneShotAuthorization,
)
from test_shop_service_start_01b_wordpress_live_authority import store, authorization

RAW = 'secret-password /private/credential-path stderr Docker-output'


def fail(*args, **kwargs):
    raise RuntimeError(RAW)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(r, 'observe_runtime_cutover_source', source)
    monkeypatch.setattr(r, '_trusted_runtime_cutover_path', lambda: '/test/source')
    monkeypatch.setattr(r, '_sleep_between_post_observations', lambda: None)


@pytest.mark.parametrize('stage', [
    'INITIAL_RUNTIME_OBSERVATION', 'INITIAL_STORAGE_OBSERVATION',
    'INITIAL_SOURCE_OBSERVATION', 'INITIAL_FACT_BINDING', 'INITIAL_CLASSIFICATION',
    'AUTHORIZATION_PREPARATION',
])
def test_initial_failures_are_value_free_and_do_not_consume(monkeypatch, capsys, stage):
    auth = OneShotAuthorization()
    calls = []
    runtime, volumes = facts, storage
    if stage == 'INITIAL_RUNTIME_OBSERVATION': runtime = fail
    elif stage == 'INITIAL_STORAGE_OBSERVATION': volumes = fail
    else:
        target = {'INITIAL_SOURCE_OBSERVATION': 'observe_runtime_cutover_source',
                  'INITIAL_FACT_BINDING': '_with_storage',
                  'INITIAL_CLASSIFICATION': 'classify_reconciliation',
                  'AUTHORIZATION_PREPARATION': 'resolve_trusted_mac_account_home'}[stage]
        monkeypatch.setattr(r, target, fail)
    result = r.execute_reconciliation(observe_runtime=runtime, observe_storage=volumes,
                                      authorization=auth, runner=calls.append)
    assert auth.calls == calls == []
    assert result.authorization_consumption_state.value == 'NOT_CONSUMED'
    assert result.authorization_consumed is False
    monkeypatch.setattr(cli, 'run', lambda: result)
    assert cli.main() == 0
    output = capsys.readouterr()
    assert RAW not in output.out + output.err
    value = json.loads(output.out)
    assert value['failure_stage'] == stage
    assert value['reason_codes'] == [stage + '_FAILED']
    assert value['production_authority'] is value['ubuntu_authority'] is False


@pytest.mark.parametrize('stage,expected', [
    ('before_claim_commit', 'NOT_CONSUMED'),
    ('after_claim_commit', 'CONSUMED'),
    ('during_final_transaction', 'CONSUMED'),
    ('before_final_commit', 'CONSUMED'),
    ('after_final_commit', 'CONSUMED'),
])
def test_durable_progress_is_preserved(tmp_path, stage, expected):
    def fault(at, db):
        if at == stage: fail()
    auth = store(tmp_path, fault)
    auth._issue(authorization())
    calls = []
    result = r.execute_reconciliation(observe_runtime=facts, observe_storage=storage,
                                      authorization=auth, runner=calls.append)
    assert result.authorization_consumption_state.value == expected
    assert result.authorization_consumed is (expected == 'CONSUMED')
    assert calls == []
    with sqlite3.connect(auth._path) as db:
        state = db.execute('SELECT state FROM wordpress_mutation_authorizations').fetchone()[0]
    assert (state == 'AVAILABLE') is (expected == 'NOT_CONSUMED')
    assert RAW not in json.dumps(result.to_json_safe())


def test_unknown_consumer_failure_is_uncertain():
    class Unknown:
        consume = fail
    result = r.execute_reconciliation(observe_runtime=facts, observe_storage=storage,
                                      authorization=Unknown(), runner=fail)
    assert result.authorization_consumption_state.value == 'UNCERTAIN'
    assert result.authorization_consumed is None


@pytest.mark.parametrize('outcome', [r.ExecutionOutcome.FAILED, r.ExecutionOutcome.UNCERTAIN])
def test_committed_consumption_and_runner_never_retry(tmp_path, outcome):
    auth = store(tmp_path)
    auth._issue(authorization())
    calls = []
    def runner(invocation):
        calls.append(invocation)
        assert not {'down', 'rm', 'prune', 'build', 'pull', 'volume', 'database'} & set(invocation.argv)
        return outcome
    result = r.execute_reconciliation(observe_runtime=facts, observe_storage=storage,
                                      authorization=auth, runner=runner)
    assert len(calls) == 1
    assert result.outcome is outcome
    assert result.authorization_consumption_state.value == 'CONSUMED'
    assert result.authorization_consumed is True
    assert result.to_json_safe()['production_authority'] is False
    assert result.to_json_safe()['ubuntu_authority'] is False


@pytest.mark.parametrize('missing', ['Type', 'Name', 'Destination'])
def test_mount_missing_required_key_with_extra_keys_is_malformed(missing):
    def runner(argv):
        if 'volume' in argv:
            return observer.CommandResult(0, json.dumps(dict(Name=argv[-1], Driver='local', Scope='local', CreatedAt='test')))
        name = next(name for name, (_, container) in observer.CONTAINERS.items() if container == argv[-1])
        mount = dict(Type='volume', Name=name, Destination=observer.EXPECTED_DESTINATIONS[name], Extra='ignored')
        del mount[missing]
        return observer.CommandResult(0, json.dumps(dict(Mounts=[mount], Project=observer.COMPOSE_PROJECT, Service=observer.CONTAINERS[name][0])))
    evidence = observer.observe_storage_continuity(runner)
    assert all(row.completeness is observer.ContinuityCompleteness.MALFORMED for row in evidence.volumes)


def test_cli_generic_exception_is_value_free_and_uncertain(monkeypatch, capsys):
    monkeypatch.setattr(cli, 'run', fail)
    assert cli.main() == 1
    output = capsys.readouterr()
    assert RAW not in output.out + output.err
    assert json.loads(output.err)['authorization_consumption_state'] == 'UNCERTAIN'


def test_claim_commit_exception_is_uncertain_even_if_commit_happened(tmp_path, monkeypatch):
    auth = store(tmp_path)
    auth._issue(authorization())
    original = auth._write

    class AmbiguousCommit:
        def __init__(self): self.db = original()
        def __enter__(self):
            self.db.__enter__()
            return self
        def __exit__(self, *args): return self.db.__exit__(*args)
        def execute(self, *args): return self.db.execute(*args)
        def commit(self):
            self.db.commit()
            fail()

    monkeypatch.setattr(auth, '_write', AmbiguousCommit)
    calls = []
    result = r.execute_reconciliation(observe_runtime=facts, observe_storage=storage,
                                      authorization=auth, runner=calls.append)
    assert result.authorization_consumption_state.value == 'UNCERTAIN'
    assert result.authorization_consumed is None
    assert calls == []
    with sqlite3.connect(auth._path) as db:
        assert db.execute('SELECT state FROM wordpress_mutation_authorizations').fetchone()[0] == 'DURABLY_CLAIMED'
