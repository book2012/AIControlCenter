"""All IO uses fixtures/mocks/temp files. Never access the user's Colima state."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from core.shopping import colima_projection_reconciliation as c
from core.shopping import colima_projection_authorization as a
from ops.macos.shopping import colima_projection_operator as op
from ops.macos.shopping import issue_colima_projection_authorization as issuer
from ops.macos.shopping.colima_projection_authorization_store import ColimaProjectionAuthorizationStore as Store

RAW = ('# retained\ncpu: 4\nmountType: virtiofs\nmounts:\n  - location: ' + c.STOREFRONT +
       '\n    writable: false\n# unchanged\nmemory: 8\n').encode()


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    monkeypatch.setattr(op.subprocess, 'run', lambda *a, **k: pytest.fail('live process forbidden'))
    monkeypatch.setattr(op, '_owner', lambda: pytest.fail('live ownership resolution forbidden'))
    monkeypatch.setattr(Store, '_initialize_for_issuer', lambda: pytest.fail('live issuance forbidden'))
    monkeypatch.setattr(Store, 'open_existing', lambda: pytest.fail('live store forbidden'))


def snapshot(post=False):
    return dict(head='1'*40, clean=True, owner=dict(uid=os.getuid(), gid=os.getgid()),
                profile=c.PROFILE, profile_file=c.PROFILE_FILE, mountType='virtiofs',
                mounts=c.MOUNTS if post else c.MOUNTS[:1], profile_sha256=c.digest(c.reconcile_bytes(RAW) if post else RAW),
                desired_sha256='a'*64, wordpress=dict(id=c.FAILED_ID, status='created', running=False, pid=0,
                exit_code=127, started='0001-01-01T00:00:00Z', restart_count=0),
                database=dict(id=c.DATABASE_ID, started=c.DATABASE_STARTED, restart_count=0, running=True, healthy='healthy'),
                artifacts={n:'b'*64 for n in c.ARTIFACTS}, production=False, ubuntu=False)


def auth(**changes):
    now = datetime.now(timezone.utc)
    values = dict(a.immutable_contract(uid=os.getuid(), gid=os.getgid()), authorization_id='test',
                  issued_at=(now-timedelta(seconds=1)).isoformat(), expires_at=(now+timedelta(minutes=5)).isoformat(),
                  precondition_json=c.canonical_snapshot(snapshot()))
    values.update(changes)
    value = object.__new__(a.ColimaProjectionAuthorization)
    for key, item in values.items(): object.__setattr__(value, key, item)
    return value


def store(tmp_path, fault=None):
    value = Store._for_test(tmp_path/'authority.sqlite3', uid=os.getuid(), gid=os.getgid(), fault=fault)
    value._issue(auth())
    return value


def state(value):
    with sqlite3.connect(value._path) as db:
        return db.execute('SELECT state FROM colima_projection_authorizations').fetchone()[0]


def test_contract_and_preservation():
    assert json.loads((c.ROOT/'deploy/shopping/colima-mounts.json').read_bytes()) == c.DESIRED
    result = c.reconcile_bytes(RAW)
    addition = f'  - location: {c.CONFIG}\n    writable: false\n'.encode()
    assert result.replace(addition, b'') == RAW
    assert c._parse(result)[2]['mounts'] == c.MOUNTS
    with pytest.raises(ValueError): c.reconcile_bytes(result)


@pytest.mark.parametrize('raw', [
    RAW.replace(b'virtiofs', b'9p'), RAW.replace(b'writable: false', b'writable: true'),
    RAW.replace(b'writable: false', b'writable: "false"'), RAW.replace(c.STOREFRONT.encode(), c.HOME.encode()),
    RAW.replace(c.STOREFRONT.encode(), c.REPOSITORY.encode()), RAW.replace(c.STOREFRONT.encode(), b'~'),
    RAW.replace(c.STOREFRONT.encode(), b'/tmp'), RAW + b'mountType: virtiofs\n',
    RAW.replace(b'writable: false', b'writable: false\n    writable: false'),
    RAW.replace(b'memory: 8', b'memory: &a 8\nother: *a'),
    RAW.replace(b'writable: false', b'writable: false\n    extra: true'),
    RAW.replace(b'memory: 8', b'memory: {a: 1, a: 2}'),
    RAW.replace(b'memory: 8', b'memory: !!int 8'),
    RAW.replace(b'  - location:', b'  - location: /tmp\n    writable: false\n  - location:'),
])
def test_ambiguous_or_broad_yaml_rejected(raw):
    with pytest.raises((ValueError, c.yaml.YAMLError)): c.reconcile_bytes(raw)


DRIFTS = [('head', '2'*40), ('clean', False), ('profile', 'default'), ('profile_file', '/tmp/colima.yaml'),
          ('mountType', '9p'), ('mounts', c.MOUNTS), ('profile_sha256', 'e'*64), ('desired_sha256', 'e'*64),
          ('owner.uid', 999), ('production', True), ('ubuntu', True), ('wordpress.id', 'f'*64),
          ('wordpress.status', 'running'), ('wordpress.running', True), ('wordpress.pid', 1),
          ('wordpress.exit_code', 0), ('wordpress.restart_count', 1), ('database.id', 'e'*64),
          ('database.started', '2026-09-09T00:00:00Z'), ('database.restart_count', 1),
          ('database.healthy', 'unhealthy'), ('database.running', False)]


def change(value, path, replacement):
    parts = path.split('.')
    for key in parts[:-1]: value = value[key]
    value[parts[-1]] = replacement


@pytest.mark.parametrize('path,replacement', DRIFTS)
def test_drift_not_consumed(tmp_path, path, replacement):
    value = store(tmp_path)
    drift = snapshot(); change(drift, path, replacement)
    with pytest.raises(a.ConsumptionFailure) as error: value.consume(lambda: drift)
    assert error.value.state is c.AuthorizationConsumptionState.NOT_CONSUMED
    assert state(value) == 'AVAILABLE'


@pytest.mark.parametrize('changes', [dict(maximum_uses=2), dict(maximum_uses=True), dict(production_authority=True),
    dict(ubuntu_authority=True), dict(mutation_id='SHOP-SERVICE-START-01G1D:WORDPRESS_RUNTIME_GENERATION_RECOVERY'),
    dict(profile='default'), dict(profile_file='/tmp/colima.yaml'), dict(trusted_uid=0),
    dict(expires_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat())])
def test_bad_authority(changes):
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(auth(**changes), now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())


def test_one_shot_and_historical_isolation(tmp_path):
    from core.shopping import wordpress_recovery_authorization as old
    from ops.macos.shopping.wordpress_recovery_authorization_store import WordPressRecoveryAuthorizationStore
    value = store(tmp_path)
    result = value.consume(snapshot)
    a.validate_consumption_result(result, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    assert state(value) == 'COMMITTED'
    with pytest.raises(a.ConsumptionFailure): value.consume(snapshot)
    with pytest.raises(a.AuthorizationError): value._issue(auth(authorization_id='another'))
    with pytest.raises(old.AuthorizationError): old.validate_consumption_result(result, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception): WordPressRecoveryAuthorizationStore._open_existing_for_test(value._path, uid=os.getuid(), gid=os.getgid())


def test_concurrent_single_winner(tmp_path):
    value = store(tmp_path)
    def consume(_):
        try: value.consume(snapshot); return True
        except a.ConsumptionFailure: return False
    with ThreadPoolExecutor(max_workers=2) as pool: assert sum(pool.map(consume, range(2))) == 1


def wire(monkeypatch, value, outcome=None):
    monkeypatch.setattr(op, '_owner', lambda: SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid()))
    monkeypatch.setattr(Store, 'open_existing', lambda: value)
    monkeypatch.setattr(op, 'observe_preconditions', snapshot)
    monkeypatch.setattr(op, '_snapshot', lambda: snapshot(True))
    calls=[]
    def mutate():
        assert state(value) == 'COMMITTED'
        calls.append('mutation')
        if outcome: raise outcome
    monkeypatch.setattr(op, '_prepare_mutation', lambda: (snapshot()['profile_sha256'],snapshot(True)['profile_sha256'],mutate))
    return calls


@pytest.mark.parametrize('stage', ['before_claim_commit','after_claim_commit','during_final_transaction','before_final_commit','after_final_commit'])
def test_faults_never_mutate(tmp_path, monkeypatch, stage):
    def fault(where, _):
        if where == stage: raise RuntimeError('secret-canary')
    value=store(tmp_path, fault); calls=wire(monkeypatch,value)
    result=op.run()
    assert not calls and result['status'] != 'DECLARED_PENDING_LIFECYCLE'
    assert state(value) == ('AVAILABLE' if stage == 'before_claim_commit' else 'COMMITTED' if stage == 'after_final_commit' else 'DURABLY_CLAIMED')
    assert 'secret-canary' not in json.dumps(result)


@pytest.mark.parametrize('error', [None, RuntimeError('secret-canary')])
def test_operator_no_retry_or_activation_claim(tmp_path, monkeypatch, error):
    value=store(tmp_path); calls=wire(monkeypatch,value,error)
    result=op.run()
    assert result['status'] == ('UNCERTAIN' if error else 'DECLARED_PENDING_LIFECYCLE')
    assert result['active_projection_proven'] is False
    assert calls == ['mutation'] and state(value) == 'COMMITTED'
    assert 'secret-canary' not in json.dumps(result)
    op.run()
    assert calls == ['mutation']


def test_operator_post_failure_consumed(tmp_path, monkeypatch):
    value=store(tmp_path); calls=wire(monkeypatch,value)
    monkeypatch.setattr(op, '_snapshot', snapshot)
    assert op.run()['status'] == 'UNCERTAIN'
    assert calls == ['mutation'] and state(value) == 'COMMITTED'


def test_temp_profile_only(monkeypatch, tmp_path):
    path=tmp_path/'colima.yaml'; path.write_bytes(RAW); path.chmod(0o600)
    monkeypatch.setattr(c, 'PROFILE_FILE', str(path))
    monkeypatch.setattr(op, '_owner', lambda: SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid()))
    # Temp ancestors may be world-writable; live path checks are tested separately.
    monkeypatch.setattr(op, '_safe_file', lambda p, _: p.lstat())
    original, replacement, mutate=op._prepare_mutation()
    assert original == c.digest(RAW) and path.read_bytes() == RAW
    mutate()
    assert c.digest(path.read_bytes()) == replacement
    assert path.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.iterdir()) == [path]
    with pytest.raises(ValueError): mutate()


def guest():
    return dict(config=dict(fstype='virtiofs', readonly=True), storefront=dict(fstype='virtiofs',readonly=True),
                artifacts={n:'regular file' for n in c.ARTIFACTS}, production=False, ubuntu=False)


@pytest.mark.parametrize('path,replacement', [('config.fstype','ext4'),('config.readonly',False),('storefront.fstype','ext4'),
        ('storefront.readonly',False),('artifacts',{}),('production',True),('ubuntu',True)])
def test_guest_post_fail_closed(path,replacement):
    c.validate_post(snapshot(),snapshot(True),guest())
    evidence=guest(); change(evidence,path,replacement)
    with pytest.raises(ValueError): c.validate_post(snapshot(),snapshot(True),evidence)


@pytest.mark.parametrize('path,replacement', [d for d in DRIFTS if d[0] not in ('mounts','profile_sha256')])
def test_post_continuity(path,replacement):
    after=snapshot(True); change(after,path,replacement)
    with pytest.raises(ValueError): c.validate_post(snapshot(),after,guest())


@pytest.mark.parametrize('ack,head,drift,success', [(issuer.ACKNOWLEDGEMENT,'1'*40,False,True),
        ('AUTHORIZE historical','1'*40,False,False),(issuer.ACKNOWLEDGEMENT,'2'*40,False,False),
        (issuer.ACKNOWLEDGEMENT,'1'*40,True,False)])
def test_exact_interactive_ack(monkeypatch, ack,head,drift,success):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda _:None,flush=lambda:None))
    monkeypatch.setattr(issuer,'resolve_trusted_mac_account_home',lambda:object())
    monkeypatch.setattr(issuer,'issue_trusted_ownership_expectation',lambda _:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    later=snapshot()
    if drift: later['head']='3'*40
    observations=iter([snapshot(),later]); answers=iter([head,ack]); issued=[]
    monkeypatch.setattr(issuer,'observe_preconditions',lambda:next(observations))
    monkeypatch.setattr('builtins.input',lambda _:next(answers))
    monkeypatch.setattr(Store,'_initialize_for_issuer',lambda:SimpleNamespace(_issue=issued.append))
    if success:
        assert issuer.issue()['status']=='AVAILABLE' and len(issued)==1
    else:
        with pytest.raises(RuntimeError): issuer.issue()
        assert not issued


def test_stable_observation_and_closed_output(monkeypatch):
    later=snapshot(); later['head']='2'*40
    observations=iter([snapshot(),later])
    monkeypatch.setattr(op,'_snapshot',lambda:next(observations))
    with pytest.raises(ValueError): op.observe_preconditions()
    value=snapshot(); value['secret-canary']='secret-canary'
    with pytest.raises(ValueError): c.canonical_snapshot(value)


def test_cli_overrides(monkeypatch,capsys):
    monkeypatch.setattr(op.sys,'argv',['operator','--profile','default'])
    monkeypatch.setattr(op,'run',lambda:pytest.fail('must not run'))
    monkeypatch.setattr(issuer,'issue',lambda:pytest.fail('must not issue'))
    assert op.main()==2 and issuer.main()==2
    assert 'CALLER_OVERRIDE_REJECTED' in capsys.readouterr().out


def test_no_mutation_process_or_secret_fields():
    source=Path(op.__file__).read_text()
    for forbidden in ['shell=True','Health.Log','.Config.Env','colima stop','colima start','colima restart','compose', 'ssh', 'UbuntuWorkerClient']:
        assert forbidden not in source
    assert 'stderr=subprocess.DEVNULL' in source


def test_readonly_observer_fixed_commands(monkeypatch):
    owner=SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid())
    monkeypatch.setattr(op,'_owner',lambda:owner)
    monkeypatch.setattr(op,'_profile',lambda _:(RAW,None))
    monkeypatch.setattr(op,'_safe_file',lambda *a:None)
    monkeypatch.setattr(op.trusted,'_trusted_docker_executable',lambda:'/trusted/docker')
    monkeypatch.setattr(op.trusted,'_fixed_environment',lambda:{'PATH':'/fixed'})
    calls=[]
    def read(argv, env):
        calls.append(argv)
        if argv[0]=='/usr/bin/git': return b'1'*40 if argv[1]=='rev-parse' else b''
        return json.dumps(snapshot()['wordpress' if argv[-1]==c.FAILED_ID else 'database']).encode()
    monkeypatch.setattr(op,'_read',read)
    observed=op.observe_preconditions()
    c.validate_snapshot(observed)
    assert len(calls)==8
    for command in [v for v in calls if v[0]=='/trusted/docker']:
        assert command[1:6]==['--context','colima-aicontrolcenter-commerce','container','inspect','--format']
        assert command[-1] in (c.FAILED_ID,c.DATABASE_ID)


def test_read_process_output_suppressed(monkeypatch):
    calls=[]
    monkeypatch.setattr(op.subprocess,'run',lambda *a,**kw:calls.append((a,kw)) or SimpleNamespace(returncode=0,stdout=b'{}'))
    assert op._read(['/fixed/read'],{})==b'{}'
    assert calls[0][1]['stderr']==op.subprocess.DEVNULL
    assert calls[0][1]['stdout']==op.subprocess.PIPE
    assert calls[0][1]['stdin']==op.subprocess.DEVNULL
    assert calls[0][1]['timeout']==10 and 'shell' not in calls[0][1]


@pytest.mark.parametrize('kind',['symlink','directory','wrong_owner','writable'])
def test_unsafe_profile_rejected(tmp_path,kind):
    path=tmp_path/'profile'; path.write_bytes(RAW); path.chmod(0o600)
    owner=SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid())
    if kind=='symlink':
        link=tmp_path/'link'; link.symlink_to(path); path=link
    elif kind=='directory': path=tmp_path
    elif kind=='wrong_owner': owner.expected_uid+=1
    else: path.chmod(0o666)
    with pytest.raises(ValueError): op._safe_file(path,owner)


def test_mount_boolean_not_integer():
    value=snapshot(); value['mounts']=[dict(location=c.STOREFRONT,writable=0)]
    with pytest.raises(ValueError): c.canonical_snapshot(value)


def test_prepare_drift_keeps_authority_available(tmp_path,monkeypatch):
    value=store(tmp_path); calls=wire(monkeypatch,value)
    monkeypatch.setattr(op,'_prepare_mutation',lambda:('f'*64,'e'*64,lambda:calls.append('wrong')))
    assert op.run()['status']=='BLOCKED'
    assert state(value)=='AVAILABLE' and not calls


def test_mutation_drift_does_not_write(monkeypatch,tmp_path):
    path=tmp_path/'colima.yaml'; path.write_bytes(RAW)
    monkeypatch.setattr(c,'PROFILE_FILE',str(path))
    monkeypatch.setattr(op,'_owner',lambda:object())
    monkeypatch.setattr(op,'_safe_file',lambda p,_:p.lstat())
    _,_,mutate=op._prepare_mutation()
    drift=RAW+b'# drift\n'; path.write_bytes(drift)
    with pytest.raises(ValueError): mutate()
    assert path.read_bytes()==drift


def test_read_atime_does_not_cause_false_drift(tmp_path):
    path=tmp_path/'fixture'; path.write_bytes(RAW)
    before=path.stat()
    os.utime(path,ns=(before.st_atime_ns+1000,before.st_mtime_ns))
    # Explicit utime also changes ctime, so model only a filesystem read's atime.
    values={name:getattr(before,name) for name in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')}
    after=SimpleNamespace(**values,st_atime_ns=before.st_atime_ns+1000)
    assert op._identity(before)==op._identity(after)
