"""Synthetic G tests: all live boundaries disabled."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import stat
from types import SimpleNamespace

import pytest
from core.shopping import wordpress_existing_generation_start_reconciliation as c
from core.shopping import wordpress_existing_generation_start_authorization as a
from ops.macos.shopping import wordpress_existing_generation_start_operator as op
from ops.macos.shopping import issue_wordpress_existing_generation_start_authorization as issuer
from ops.macos.shopping.wordpress_existing_generation_start_authorization_store import WordPressExistingGenerationStartAuthorizationStore as Store


_original_environment = op._environment
_original_repository = op._repository


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('live IO forbidden')
    for module, name in [(op.subprocess, 'run'), (op, '_owner'), (op, '_executable'),
        (op, '_environment'), (op, '_socket'), (op, '_repository'),
        (Store, '_initialize_for_issuer'), (Store, 'open_existing')]:
        monkeypatch.setattr(module, name, forbidden)


def snapshot():
    return dict(head='f4d50eae4e452434922013463a3a486a2bbd8c52', clean=True, reviewed_artifact='a'*64,
        owner=dict(uid=os.getuid(),gid=os.getgid()), compose_sha256=c.COMPOSE_SHA256,
        desired_restart='no', context=c.CONTEXT, endpoint='unix://'+c.SOCKET,
        socket=dict(dev=1,ino=2,mode=stat.S_IFSOCK|0o600,uid=os.getuid(),gid=os.getgid()),
        wordpress=dict(id=c.FAILED_ID,status='created',running=False,restart_count=0,
            restart='no',maximum_retry_count=0,healthy='starting'),
        database=dict(id=c.DATABASE_ID,started='2026-09-03T03:10:22.559242003Z',
            restart_count=0,running=True,healthy='healthy'),
        storage=dict(c.VOLUME),attachment=dict(c.ATTACHMENT))


def post():
    v=snapshot();v['wordpress'].update(status='running',running=True,healthy='healthy');return v


def auth(**changes):
    now=datetime.now(timezone.utc)
    values=dict(a.immutable_contract(uid=os.getuid(),gid=os.getgid()),authorization_id='test',
        issued_at=(now-timedelta(seconds=1)).isoformat(),expires_at=(now+timedelta(minutes=5)).isoformat(),
        precondition_json=c.canonical_snapshot(snapshot()))
    values.update(changes)
    v=object.__new__(a.WordPressExistingGenerationStartAuthorization)
    for k,item in values.items():object.__setattr__(v,k,item)
    return v


def store(tmp_path,fault=None):
    v=Store._for_test(tmp_path/'authority.sqlite3',uid=os.getuid(),gid=os.getgid(),fault=fault)
    v._issue(auth());return v


def state(v):
    with sqlite3.connect(v._path) as db:
        return db.execute('SELECT state FROM wordpress_existing_generation_start_authorizations').fetchone()[0]


def change(v,path,value):
    parts=path.split('.')
    for p in parts[:-1]:v=v[p]
    v[parts[-1]]=value


DRIFTS=[('reviewed_artifact','b'*64),('head','2'*40),('clean',False),('compose_sha256','f'*64),('desired_restart','unless-stopped'),
 ('context','default'),('endpoint','ssh://worker'),('socket.ino',3),('socket.uid',999),
 ('wordpress.id','f'*64),('wordpress.status','exited'),('wordpress.running',True),
 ('wordpress.restart_count',1),('wordpress.restart_count',False),('wordpress.restart','unless-stopped'),
 ('wordpress.maximum_retry_count',1),('database.id','f'*64),('database.started','2026-09-09T00:00:00Z'),
 ('database.restart_count',1),('database.running',False),('database.healthy','unhealthy'),
 ('storage.CreatedAt','new'),('attachment.source','/other'),('attachment.rw',False)]


@pytest.mark.parametrize('path,replacement',DRIFTS)
def test_drift_not_consumed(tmp_path,path,replacement):
    v=store(tmp_path);drift=snapshot();change(drift,path,replacement)
    with pytest.raises(a.ConsumptionFailure) as error:v.consume(lambda:drift)
    assert error.value.state is c.AuthorizationConsumptionState.NOT_CONSUMED
    assert state(v)=='AVAILABLE'


def wire(monkeypatch,v,outcome=0):
    monkeypatch.setattr(op,'_owner',lambda:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    monkeypatch.setattr(op,'_executable',lambda:'/trusted/docker')
    monkeypatch.setattr(op,'_environment',lambda:{'HOME':c.HOME})
    monkeypatch.setattr(Store,'open_existing',lambda:v)
    monkeypatch.setattr(op,'observe_preconditions',snapshot)
    monkeypatch.setattr(op,'_snapshot',post)
    calls=[]
    def run(argv,**kw):
        assert state(v)=='COMMITTED'
        calls.append((argv,kw))
        if isinstance(outcome,Exception):raise outcome
        return SimpleNamespace(returncode=outcome)
    monkeypatch.setattr(op.subprocess,'run',run)
    return calls


@pytest.mark.parametrize('outcome',[0,1,op.subprocess.TimeoutExpired('canary',30),RuntimeError('canary')])
def test_single_exact_update_consumed_first(tmp_path,monkeypatch,outcome):
    v=store(tmp_path);calls=wire(monkeypatch,v,outcome)
    result=op.run()
    assert result['status']==('ACCEPTED' if outcome==0 else 'UNCERTAIN')
    assert result['authorization_consumed'] and result['database_continuity_observed']
    assert len(calls)==1
    argv,kw=calls[0]
    assert argv==['/trusted/docker','--context',c.CONTEXT,'start',c.FAILED_ID]
    assert kw['stdin']==kw['stdout']==kw['stderr']==op.subprocess.DEVNULL
    assert kw['timeout']==30 and 'shell' not in kw
    assert all(result[n] is False for n in c.DENIED)
    assert not result['backup_proven'] and not result['database_content_preservation_proven']
    assert 'canary' not in json.dumps(result)
    assert op.run()['status']=='BLOCKED' and len(calls)==1


@pytest.mark.parametrize('path,replacement',[(p, v) for p, v in DRIFTS if p not in ("wordpress.restart", "wordpress.running")]+ [('wordpress.restart','unless-stopped')])
def test_post_mismatch_uncertain(tmp_path,monkeypatch,path,replacement):
    v=store(tmp_path);calls=wire(monkeypatch,v)
    after=post();change(after,path,replacement)
    monkeypatch.setattr(op,'_snapshot',lambda:after)
    assert op.run()['status']=='UNCERTAIN' and len(calls)==1


@pytest.mark.parametrize('stage',['before_claim_commit','after_claim_commit','during_final_transaction','before_final_commit','after_final_commit'])
def test_store_faults_no_mutation(tmp_path,monkeypatch,stage):
    def fault(where,db):
        if where==stage:raise RuntimeError('canary')
    v=store(tmp_path,fault);calls=wire(monkeypatch,v)
    result=op.run()
    assert not calls and result['status']!='ACCEPTED'
    assert 'canary' not in json.dumps(result)


def test_consumed_then_drift_no_attempt(tmp_path,monkeypatch):
    v=store(tmp_path);calls=wire(monkeypatch,v)
    after=snapshot();after['wordpress']['id']='f'*64
    observations=iter([snapshot(),after])
    monkeypatch.setattr(op,'observe_preconditions',lambda:next(observations))
    assert op.run()['status']=='BLOCKED' and not calls and state(v)=='COMMITTED'


@pytest.mark.parametrize('previous',['available','expired','consumed'])
def test_reissuance_refused(tmp_path,previous):
    v=store(tmp_path)
    if previous=='consumed':v.consume(snapshot)
    if previous=='expired':
        with sqlite3.connect(v._path) as db:
            db.execute("UPDATE wordpress_existing_generation_start_authorizations SET expires_at=?",((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),))
    with pytest.raises(a.AuthorizationError):v._issue(auth(authorization_id='second'))


def test_concurrent_one_winner(tmp_path):
    v=store(tmp_path)
    def consume(_):
        try:v.consume(snapshot);return True
        except a.ConsumptionFailure:return False
    with ThreadPoolExecutor(max_workers=2) as pool:assert sum(pool.map(consume,range(2)))==1


@pytest.mark.parametrize('changes',[lambda now,n=n:{n:True} for n in c.DENIED]+[
 lambda now:{'maximum_uses':2},lambda now:{'maximum_uses':True},lambda now:{'mutation_id':'historical'},
 lambda now:{'expires_at':(now+timedelta(minutes=11)).isoformat()},
 lambda now:{'issued_at':now.replace(tzinfo=None).isoformat()},lambda now:{'trusted_uid':999}])
def test_bad_authority(changes):
    now=datetime(2026,9,9,tzinfo=timezone.utc)
    values=dict(issued_at=now.isoformat(),expires_at=(now+timedelta(minutes=5)).isoformat())
    values.update(changes(now))
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(auth(**values),now=now,uid=os.getuid(),gid=os.getgid())


def test_expiry_boundary():
    v=auth()
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(v,now=datetime.fromisoformat(v.expires_at),uid=os.getuid(),gid=os.getgid())


@pytest.mark.parametrize('ack,head,success',[(issuer.ACKNOWLEDGEMENT,snapshot()['head'],True),
 ('AUTHORIZE historical',snapshot()['head'],False),(issuer.ACKNOWLEDGEMENT,'2'*40,False)])
def test_exact_ack(monkeypatch,ack,head,success):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda _:None,flush=lambda:None))
    monkeypatch.setattr(issuer,'resolve_trusted_mac_account_home',lambda:object())
    monkeypatch.setattr(issuer,'issue_trusted_ownership_expectation',lambda _:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    monkeypatch.setattr(issuer,'observe_preconditions',snapshot)
    answers=iter([head,snapshot()['reviewed_artifact'],ack]);issued=[]
    monkeypatch.setattr('builtins.input',lambda _:next(answers))
    monkeypatch.setattr(Store,'_initialize_for_issuer',lambda:SimpleNamespace(_issue=issued.append))
    if success:
        assert issuer.issue()['status']=='AVAILABLE' and len(issued)==1
        assert json.loads(issued[0].precondition_json)['head']==head
        assert json.loads(issued[0].precondition_json)['reviewed_artifact']==snapshot()['reviewed_artifact']
    else:
        with pytest.raises(RuntimeError):issuer.issue()
        assert not issued


def test_non_tty_and_overrides(monkeypatch):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:False))
    with pytest.raises(RuntimeError):issuer.issue()
    monkeypatch.setattr(op.sys,'argv',['operator','--override'])
    assert op.main()==issuer.main()==2


def test_strict_parent_not_repaired(tmp_path):
    tmp_path.chmod(0o755)
    with pytest.raises(Exception):Store._for_test(tmp_path/'bad.sqlite3',uid=os.getuid(),gid=os.getgid())
    assert stat.S_IMODE(tmp_path.stat().st_mode)==0o755
    tmp_path.chmod(0o700)


def test_historical_isolation(tmp_path):
    from core.shopping import colima_lifecycle_authorization as old
    from ops.macos.shopping.colima_lifecycle_authorization_store import ColimaLifecycleAuthorizationStore
    v=store(tmp_path);result=v.consume(snapshot)
    with pytest.raises(old.AuthorizationError):old.validate_consumption_result(result,now=datetime.now(timezone.utc),uid=os.getuid(),gid=os.getgid())
    with pytest.raises(Exception):ColimaLifecycleAuthorizationStore._open_existing_for_test(v._path,uid=os.getuid(),gid=os.getgid())


def test_snapshot_read_allowlist(monkeypatch):
    before=snapshot()
    monkeypatch.setattr(op,'_owner',lambda:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    monkeypatch.setattr(op,'_repository',lambda _: {n:before[n] for n in ('head','reviewed_artifact','clean','compose_sha256','desired_restart')})
    monkeypatch.setattr(op,'_socket',lambda _:before['socket'])
    monkeypatch.setattr(op,'_executable',lambda:'/trusted/docker')
    monkeypatch.setattr(op,'_environment',lambda:{})
    calls=[]
    values=iter([before['endpoint'],before['wordpress'],before['database'],before['storage'],before['attachment']])
    def read(argv,env):calls.append(argv);return json.dumps(next(values)).encode()
    monkeypatch.setattr(op,'_read',read)
    assert op._snapshot()==before
    assert calls==[
        ['/trusted/docker','context','inspect','--format','{{json .Endpoints.docker.Host}}',c.CONTEXT],
        *[['/trusted/docker','--context',c.CONTEXT,kind,'inspect','--format',fmt,identity]
          for kind,fmt,identity in [('container',op.WP_FORMAT,c.FAILED_ID),
          ('container',op.observation.DB_FORMAT,c.DATABASE_ID),('volume',op.VOLUME_FORMAT,c.VOLUME['Name']),
          ('container',op.ATTACHMENT_FORMAT,c.DATABASE_ID)]]]


def test_no_broader_mutation():
    source=Path(op.__file__).read_text()
    assert source.count('subprocess.run(')==1
    for forbidden in ('shell=True','Health.Log','.Config.Env','UbuntuWorkerClient','LIFECYCLE_ARGS','GUEST_ARGS',
                      "'stop'","'rm'","'exec'",'docker compose'):
        assert forbidden not in source
    assert c.MUTATION_ARGS[-1]!=c.DATABASE_ID
    assert c.digest((c.ROOT/'deploy/shopping/compose.yaml').read_bytes())==c.COMPOSE_SHA256


def test_observation_requires_two_equal_samples(monkeypatch):
    later=snapshot();later['socket']['ino']=99
    values=iter([snapshot(),later])
    monkeypatch.setattr(op,'_snapshot',lambda:next(values))
    with pytest.raises(ValueError):op.observe_preconditions()
    monkeypatch.setattr(op,'_snapshot',snapshot)
    assert op.observe_preconditions()==snapshot()


def test_post_observation_failure_uncertain(tmp_path,monkeypatch):
    v=store(tmp_path);calls=wire(monkeypatch,v)
    def fail():raise RuntimeError('secret-canary')
    monkeypatch.setattr(op,'_snapshot',fail)
    result=op.run()
    assert result['status']=='UNCERTAIN' and len(calls)==1
    assert 'secret-canary' not in json.dumps(result)


def test_hardlinked_store_rejected(tmp_path):
    v=store(tmp_path);os.link(v._path,tmp_path/'link')
    with pytest.raises(Exception):v._issue(auth(authorization_id='second'))


def test_issuer_drift_after_ack(monkeypatch):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda _:None,flush=lambda:None))
    monkeypatch.setattr(issuer,'resolve_trusted_mac_account_home',lambda:object())
    monkeypatch.setattr(issuer,'issue_trusted_ownership_expectation',lambda _:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    later=snapshot();later['socket']['ino']=5
    observations=iter([snapshot(),later]);answers=iter([snapshot()['head'],snapshot()['reviewed_artifact'],issuer.ACKNOWLEDGEMENT])
    monkeypatch.setattr(issuer,'observe_preconditions',lambda:next(observations))
    monkeypatch.setattr('builtins.input',lambda _:next(answers))
    with pytest.raises(RuntimeError,match='PRECONDITION_DRIFT'):issuer.issue()


def test_environment_filters_ambient(monkeypatch):
    monkeypatch.setattr(op.trusted,'_fixed_environment',lambda:dict(HOME=c.HOME,USER='u',LOGNAME='u',
        PATH='/fixed',DOCKER_CONFIG='/fixed/config',DOCKER_HOST='ssh://worker',TMPDIR='/tmp',LC_ALL='bad'))
    assert set(_original_environment())=={'HOME','USER','LOGNAME','PATH','DOCKER_CONFIG'}


@pytest.mark.parametrize('reviewed', ['', 'b'*64])
def test_later_clean_head_without_reviewed_artifact_denied(monkeypatch, reviewed):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer.sys,'stdout',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer,'resolve_trusted_mac_account_home',lambda:object())
    monkeypatch.setattr(issuer,'issue_trusted_ownership_expectation',lambda _:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    later=snapshot();later['head']='2'*40
    monkeypatch.setattr(issuer,'observe_preconditions',lambda:later)
    answers=iter([later['head'],reviewed])
    monkeypatch.setattr('builtins.input',lambda _:next(answers))
    with pytest.raises(RuntimeError,match='REVIEWED_ARTIFACT_REQUIRED'):
        issuer.issue()


@pytest.mark.parametrize('changed', [
    'core/shopping/wordpress_existing_generation_start_artifact.py',
    'core/shopping/wordpress_existing_generation_start_authorization.py',
    'core/shopping/wordpress_existing_generation_start_reconciliation.py',
    'ops/macos/shopping/issue_wordpress_existing_generation_start_authorization.py',
    'ops/macos/shopping/wordpress_existing_generation_start_authorization_store.py',
    'ops/macos/shopping/wordpress_existing_generation_start_operator.py',
    'core/secrets/mariadb_continuity_trusted_ownership_expectation.py',
    'ops/macos/shopping/wordpress_port_live_operator.py',
    'deploy/shopping/compose.yaml', 'requirements.txt',
])
def test_authority_bytes_change_identity(tmp_path, changed):
    from core.shopping.wordpress_existing_generation_start_artifact import artifact_identity
    file=tmp_path/changed;file.parent.mkdir(parents=True,exist_ok=True)
    file.write_bytes(b'reviewed implementation')
    reviewed=artifact_identity(tmp_path,[changed],lambda _:None)
    file.write_bytes(b'modified implementation')
    assert artifact_identity(tmp_path,[changed],lambda _:None)!=reviewed
    file.unlink()
    with pytest.raises(FileNotFoundError):artifact_identity(tmp_path,[changed],lambda _:None)


@pytest.mark.parametrize('head', ['1'*40, '2'*40])
def test_same_artifact_on_clean_committed_head_observed(monkeypatch,tmp_path,head):
    from core.shopping.wordpress_existing_generation_start_artifact import artifact_identity, ARTIFACT_PATHS
    compose=tmp_path/'deploy/shopping/compose.yaml';compose.parent.mkdir(parents=True)
    compose.write_bytes((c.ROOT/'deploy/shopping/compose.yaml').read_bytes())
    implementation=tmp_path/'core/authority.py';implementation.parent.mkdir()
    implementation.write_bytes(b'immutable implementation')
    paths=['core/authority.py','deploy/shopping/compose.yaml']
    reviewed=artifact_identity(tmp_path,paths,lambda _:None)
    monkeypatch.setattr(c,'ROOT',tmp_path)
    monkeypatch.setattr(op.observation,'_safe_file',lambda *_:None)
    calls=[]
    def read(argv,env):
        calls.append(argv)
        if argv==['/usr/bin/git','rev-parse','HEAD']:return head.encode()+b'\n'
        if argv==['/usr/bin/git','status','--porcelain=v1','--untracked-files=all']:return b''
        assert argv==['/usr/bin/git','ls-files','-z','--',*ARTIFACT_PATHS]
        return ('\0'.join(paths)+'\0').encode()
    monkeypatch.setattr(op,'_read',read)
    observed=_original_repository(object())
    assert observed['head']==head and observed['clean'] is True
    assert observed['reviewed_artifact']==reviewed
    bound=snapshot();bound.update(observed)
    authorization=auth(precondition_json=c.canonical_snapshot(bound))
    a.validate_authorization(authorization,now=datetime.now(timezone.utc),uid=os.getuid(),gid=os.getgid())
    assert json.loads(authorization.precondition_json)['head']==head
    implementation.write_bytes(b'changed authority')
    assert _original_repository(object())['reviewed_artifact']!=reviewed
    monkeypatch.setattr(op,'_read',lambda argv,env:head.encode() if 'rev-parse' in argv else b' M core/authority.py\n')
    with pytest.raises(ValueError):_original_repository(object())


def test_artifact_inventory_and_historical_binding_fail_closed(tmp_path):
    from core.shopping.wordpress_existing_generation_start_artifact import artifact_identity
    file=tmp_path/'authority.py';file.write_bytes(b'authority')
    first=artifact_identity(tmp_path,['authority.py'],lambda _:None)
    extra=tmp_path/'added.py';extra.write_bytes(b'new authority')
    assert artifact_identity(tmp_path,['added.py','authority.py'],lambda _:None)!=first
    for names in ([],['authority.py','authority.py'],['../authority.py']):
        with pytest.raises(ValueError):artifact_identity(tmp_path,names,lambda _:None)
    historical=snapshot();historical.pop('reviewed_artifact')
    with pytest.raises(ValueError):c.canonical_snapshot(historical)


def test_loaded_local_authority_dependencies_are_in_artifact_scope():
    import sys
    from core.shopping.wordpress_existing_generation_start_artifact import ARTIFACT_PATHS
    root=Path(__file__).resolve().parents[1]
    for name,module in tuple(sys.modules.items()):
        if not name.startswith(('core.', 'ops.', 'integrations.')) or not getattr(module,'__file__',None):
            continue
        relative=Path(module.__file__).resolve().relative_to(root).as_posix()
        assert any(relative==scope or relative.startswith(scope+'/') for scope in ARTIFACT_PATHS)


def test_artifact_mode_and_unsafe_files(tmp_path):
    from core.shopping.wordpress_existing_generation_start_artifact import artifact_identity
    file=tmp_path/'authority.py';file.write_bytes(b'authority');file.chmod(0o600)
    before=artifact_identity(tmp_path,['authority.py'],lambda _:None)
    file.chmod(0o700)
    assert artifact_identity(tmp_path,['authority.py'],lambda _:None)!=before
    file.write_bytes(b'x'*65537)
    with pytest.raises(ValueError):artifact_identity(tmp_path,['authority.py'],lambda _:None)
    file.unlink();file.symlink_to(tmp_path/'missing')
    with pytest.raises(OSError):artifact_identity(tmp_path,['authority.py'],lambda _:None)


def test_artifact_safe_file_validation_cannot_be_bypassed(tmp_path):
    from core.shopping.wordpress_existing_generation_start_artifact import artifact_identity
    file=tmp_path/'authority.py';file.write_bytes(b'authority')
    def reject(_):raise ValueError('unsafe ownership or mode')
    with pytest.raises(ValueError,match='unsafe ownership or mode'):
        artifact_identity(tmp_path,['authority.py'],reject)


def test_created_without_health_state():
    before = snapshot()
    before['wordpress']['healthy'] = None
    c.validate_snapshot(before)
    c.validate_post(before, post())


@pytest.mark.parametrize('converges', [True, False])
def test_health_horizon_single_start(tmp_path, monkeypatch, converges):
    v = store(tmp_path)
    calls = wire(monkeypatch, v)
    clock = [0]
    monkeypatch.setattr(op.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(op.time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    def observe():
        after = post()
        after['wordpress']['healthy'] = 'healthy' if converges and clock[0] >= 400 else 'starting'
        return after
    monkeypatch.setattr(op, '_snapshot', observe)
    assert op.run()['status'] == ('ACCEPTED' if converges else 'UNCERTAIN')
    assert len(calls) == 1
    assert clock[0] == (400 if converges else 460)


def test_database_restart_zero_required_before_issuance():
    before = snapshot()
    before['database']['restart_count'] = 1
    with pytest.raises(ValueError): c.canonical_snapshot(before)


def test_f0_authority_and_store_rejected(tmp_path):
    from core.shopping import wordpress_restart_policy_authorization as f0
    from ops.macos.shopping.wordpress_restart_policy_authorization_store import WordPressRestartPolicyAuthorizationStore
    v = store(tmp_path)
    with pytest.raises(f0.AuthorizationError):
        f0.validate_consumption_result(v.consume(snapshot), now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        WordPressRestartPolicyAuthorizationStore._open_existing_for_test(v._path, uid=os.getuid(), gid=os.getgid())


def test_non_mac_blocked_before_store_or_docker(monkeypatch):
    def reject(): raise RuntimeError('Darwin is required')
    monkeypatch.setattr(op, '_owner', reject)
    assert op.run() == c.projection('BLOCKED')
