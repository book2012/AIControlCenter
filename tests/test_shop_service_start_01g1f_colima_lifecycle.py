"""Synthetic only: no user Colima state, runtime command or live authority access."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from core.shopping import colima_lifecycle_reconciliation as c
from core.shopping import colima_lifecycle_authorization as a
from ops.macos.shopping import colima_lifecycle_operator as op
from ops.macos.shopping import issue_colima_lifecycle_authorization as issuer
from ops.macos.shopping.colima_lifecycle_authorization_store import ColimaLifecycleAuthorizationStore as Store


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('live IO forbidden')
    for module, name in [(op.subprocess, 'run'), (op, '_owner'), (op, '_executable'),
                         (op, '_environment'), (op.observation, '_snapshot'),
                         (op.observation, '_profile'), (Store, '_initialize_for_issuer'),
                         (Store, 'open_existing')]:
        monkeypatch.setattr(module, name, forbidden)


def snapshot():
    d = c.declared
    return dict(declared=dict(head='1'*40, clean=True, owner=dict(uid=os.getuid(), gid=os.getgid()),
        profile=c.PROFILE, profile_file=c.PROFILE_FILE, mountType='virtiofs', mounts=deepcopy(c.MOUNTS),
        profile_sha256=c.PROFILE_SHA256, desired_sha256=c.DESIRED_SHA256,
        wordpress=dict(id=c.FAILED_ID, status='created', running=False, pid=0, exit_code=127,
                       started='0001-01-01T00:00:00Z', restart_count=0),
        database=dict(id=c.DATABASE_ID, started=d.DATABASE_STARTED, restart_count=0, running=True, healthy='healthy'),
        artifacts={n:'b'*64 for n in d.ARTIFACTS}, production=False, ubuntu=False),
        runtime=dict(profile=c.PROFILE, running=True, runtime='docker', vm_type='vz'),
        storage=dict(c.VOLUME), attachment=dict(c.ATTACHMENT), wordpress_restart='no',
        lifecycle_authority=True, business_mutation_authority=False)


def auth(**changes):
    now=datetime.now(timezone.utc)
    values=dict(a.immutable_contract(uid=os.getuid(), gid=os.getgid()), authorization_id='test',
        issued_at=(now-timedelta(seconds=1)).isoformat(), expires_at=(now+timedelta(minutes=5)).isoformat(),
        precondition_json=c.canonical_snapshot(snapshot()))
    values.update(changes)
    value=object.__new__(a.ColimaLifecycleAuthorization)
    for key,item in values.items(): object.__setattr__(value,key,item)
    return value


def store(tmp_path, fault=None):
    value=Store._for_test(tmp_path/'authority.sqlite3',uid=os.getuid(),gid=os.getgid(),fault=fault)
    value._issue(auth())
    return value


def state(value):
    with sqlite3.connect(value._path) as db:
        return db.execute('SELECT state FROM colima_lifecycle_authorizations').fetchone()[0]


def change(value,path,replacement):
    parts=path.split('.')
    for part in parts[:-1]: value=value[part]
    value[parts[-1]]=replacement


DRIFTS=[('declared.head','2'*40),('declared.clean',False),('declared.profile','default'),
 ('declared.profile_file','/tmp/profile'),('declared.profile_sha256','f'*64),
 ('declared.desired_sha256','f'*64),('declared.mounts',c.MOUNTS[:1]),('declared.mountType','9p'),
 ('declared.production',True),('declared.ubuntu',True),('declared.owner.uid',999),
 ('declared.wordpress.id','f'*64),('declared.wordpress.status','running'),
 ('declared.wordpress.running',True),('declared.wordpress.pid',1),('declared.wordpress.exit_code',0),
 ('declared.wordpress.started','2026-09-09T00:00:00Z'),('declared.wordpress.restart_count',1),
 ('declared.database.id','f'*64),('declared.database.started','2026-09-09T00:00:00Z'),
 ('declared.database.restart_count',1),('declared.database.healthy','unhealthy'),
 ('declared.database.running',False),('runtime.profile','default'),('runtime.running',False),
 ('runtime.vm_type','qemu'),('runtime.runtime','containerd'),('storage.CreatedAt','new'),
 ('storage.Name','other'),('attachment.source','/tmp'),('attachment.rw',False),
 ('wordpress_restart','always'),('lifecycle_authority',False),('business_mutation_authority',True)]


@pytest.mark.parametrize('path,replacement',DRIFTS)
def test_drift_not_consumed(tmp_path,path,replacement):
    value=store(tmp_path); drift=snapshot(); change(drift,path,replacement)
    with pytest.raises(a.ConsumptionFailure) as error: value.consume(lambda:drift)
    assert error.value.state is c.AuthorizationConsumptionState.NOT_CONSUMED
    assert state(value)=='AVAILABLE'


def wire(monkeypatch,value,outcome=True):
    monkeypatch.setattr(op,'_owner',lambda:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    monkeypatch.setattr(op,'_executable',lambda:'/trusted/colima')
    monkeypatch.setattr(op,'_environment',lambda:{'HOME':c.HOME})
    monkeypatch.setattr(Store,'open_existing',lambda:value)
    monkeypatch.setattr(op,'observe_preconditions',snapshot)
    monkeypatch.setattr(op,'_snapshot',snapshot)
    monkeypatch.setattr(op,'_runtime',lambda *args:snapshot()['runtime'])
    monkeypatch.setattr(op,'_read',lambda *args:guest())
    calls=[]
    def mutate(*args):
        assert state(value)=='COMMITTED'
        calls.append('mutation')
        if isinstance(outcome,Exception): raise outcome
        return outcome
    monkeypatch.setattr(op,'_mutate',mutate)
    return calls


def guest():
    return ('1 0 8:1 / / rw,relatime - ext4 /dev/root rw\n'+''.join(
        f'{index} 1 0:{index} / {p} ro,relatime - virtiofs {c.mount_tag(p)} rw\n'
        for index,p in enumerate((c.STOREFRONT,c.CONFIG),2))).encode()
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

@pytest.mark.parametrize('stage', ['before_claim_commit','after_claim_commit','during_final_transaction','before_final_commit','after_final_commit'])
def test_faults_never_mutate(tmp_path, monkeypatch, stage):
    def fault(where, _):
        if where == stage: raise RuntimeError('secret-canary')
    value=store(tmp_path, fault); calls=wire(monkeypatch,value)
    result=op.run()
    assert not calls and result['status'] != 'RECONCILED'
    assert state(value) == ('AVAILABLE' if stage == 'before_claim_commit' else 'COMMITTED' if stage == 'after_final_commit' else 'DURABLY_CLAIMED')
    assert 'secret-canary' not in json.dumps(result)

@pytest.mark.parametrize('ack,head,drift,success', [(issuer.ACKNOWLEDGEMENT,'1'*40,False,True),
        ('AUTHORIZE historical','1'*40,False,False),(issuer.ACKNOWLEDGEMENT,'2'*40,False,False),
        (issuer.ACKNOWLEDGEMENT,'1'*40,True,False)])
def test_exact_interactive_ack(monkeypatch, ack,head,drift,success):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(issuer.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda _:None,flush=lambda:None))
    monkeypatch.setattr(issuer,'resolve_trusted_mac_account_home',lambda:object())
    monkeypatch.setattr(issuer,'issue_trusted_ownership_expectation',lambda _:SimpleNamespace(expected_uid=os.getuid(),expected_gid=os.getgid()))
    later=snapshot()
    if drift: later['declared']['head']='3'*40
    observations=iter([snapshot(),later]); answers=iter([head,ack]); issued=[]
    monkeypatch.setattr(issuer,'observe_preconditions',lambda:next(observations))
    monkeypatch.setattr('builtins.input',lambda _:next(answers))
    monkeypatch.setattr(Store,'_initialize_for_issuer',lambda:SimpleNamespace(_issue=issued.append))
    if success:
        assert issuer.issue()['status']=='AVAILABLE' and len(issued)==1
    else:
        with pytest.raises(RuntimeError): issuer.issue()
        assert not issued

def test_cli_overrides(monkeypatch,capsys):
    monkeypatch.setattr(op.sys,'argv',['operator','--profile','default'])
    monkeypatch.setattr(op,'run',lambda:pytest.fail('must not run'))
    monkeypatch.setattr(issuer,'issue',lambda:pytest.fail('must not issue'))
    assert op.main()==2 and issuer.main()==2
    assert 'CALLER_OVERRIDE_REJECTED' in capsys.readouterr().out

@pytest.mark.parametrize('outcome',[True,False,RuntimeError('secret-canary'),TimeoutError('secret-canary')])
def test_one_attempt_postobserve_even_on_error(tmp_path,monkeypatch,outcome):
    value=store(tmp_path); calls=wire(monkeypatch,value,outcome)
    result=op.run()
    assert result['status']==('RECONCILED' if outcome is True else 'UNCERTAIN')
    assert result['active_projection_proven'] and result['database_continuity_observed']
    assert result['profile_running_after'] is True
    assert result['lifecycle_mutation_attempted'] and result['authorization_consumed']
    for key in ('wordpress_generation_recovery_allowed','business_mutation_authority',
                'production_authority','ubuntu_authority','automatic_retry','automatic_rollback',
                'database_content_preservation_proven','backup_proven'):
        assert result[key] is False
    assert calls==['mutation'] and 'secret-canary' not in json.dumps(result)
    assert op.run()['status']=='BLOCKED' and calls==['mutation']


@pytest.mark.parametrize('kind',['missing','rw','wrong-source','opaque-tag','wrong-fs','duplicate',
 'overmount','parent','extra','subroot','malformed','empty','oversize','wrong-profile'])
def test_projection_fail_closed(kind):
    raw=guest(); profile=c.PROFILE
    if kind=='missing': raw=b'\n'.join(raw.splitlines()[:-1])
    elif kind=='rw': raw=raw.replace(b'ro,relatime',b'rw,relatime')
    elif kind=='wrong-source': raw=raw.replace(c.mount_tag(c.CONFIG).encode(),c.mount_tag(c.STOREFRONT).encode())
    elif kind=='opaque-tag': raw=raw.replace(c.mount_tag(c.CONFIG).encode(),b'mount1')
    elif kind=='wrong-fs': raw=raw.replace(b'virtiofs',b'ext4')
    elif kind=='duplicate': raw+=raw.splitlines()[-1]+b'\n'
    elif kind=='overmount': raw+=f'8 1 0:8 / {c.CONFIG}/child rw - tmpfs tmpfs rw\n'.encode()
    elif kind=='parent': raw+=f'8 1 0:8 / {c.REPOSITORY} rw - tmpfs tmpfs rw\n'.encode()
    elif kind=='extra': raw+=b'8 1 0:8 / /tmp ro - virtiofs other rw\n'
    elif kind=='subroot': raw=raw.replace(b' / '+c.CONFIG.encode(),b' /other '+c.CONFIG.encode())
    elif kind=='malformed': raw=b'garbage'
    elif kind=='empty': raw=b''
    elif kind=='oversize': raw=b'x'*65537
    else: profile='default'
    with pytest.raises((ValueError,IndexError)): c.prove_projection(raw,profile)


def test_projection_success_not_yaml():
    assert c.prove_projection(guest(),c.PROFILE)
    with pytest.raises(ValueError): c.prove_projection(json.dumps(c.MOUNTS).encode(),c.PROFILE)


@pytest.mark.parametrize('kind',['guest','snapshot','runtime','wordpress'])
def test_partial_postobservation(tmp_path,monkeypatch,kind):
    value=store(tmp_path); calls=wire(monkeypatch,value)
    def fail(*args): raise RuntimeError('secret-canary')
    if kind=='guest': monkeypatch.setattr(op,'_read',fail)
    elif kind=='snapshot': monkeypatch.setattr(op,'_snapshot',fail)
    elif kind=='runtime': monkeypatch.setattr(op,'_runtime',fail)
    else:
        after=snapshot(); after['declared']['wordpress']['running']=True
        monkeypatch.setattr(op,'_snapshot',lambda:after)
    result=op.run()
    assert result['status']=='UNCERTAIN' and calls==['mutation']
    assert 'secret-canary' not in json.dumps(result)
    if kind=='runtime': assert result['profile_running_after'] is None
    if kind=='snapshot': assert not result['database_continuity_observed']


@pytest.mark.parametrize('restart',[0,1,10])
def test_truthful_database_runtime_restart(restart):
    before=snapshot(); after=snapshot()
    after['declared']['database'].update(started='2026-09-09T00:00:00Z',restart_count=restart)
    assert c.database_continuity(before,after)
    c.validate_post(before,after)


@pytest.mark.parametrize('path,replacement',[
 ('declared.database.id','f'*64),('declared.database.started','2020-01-01T00:00:00Z'),
 ('declared.database.restart_count',-1),('declared.database.restart_count',True),
 ('declared.database.running',False),('declared.database.healthy','starting'),
 ('storage.CreatedAt','new'),('attachment.source','/other')])
def test_database_post_fail_closed(path,replacement):
    after=snapshot();change(after,path,replacement)
    with pytest.raises(ValueError): c.database_continuity(snapshot(),after)


@pytest.mark.parametrize('changes',[
 lambda now:dict(lifecycle_authority=False),lambda now:dict(lifecycle_authority=1),
 lambda now:dict(expires_at=(now+timedelta(minutes=11)).isoformat()),
 lambda now:dict(issued_at=(now+timedelta(minutes=1)).isoformat()),
 lambda now:dict(issued_at=now.replace(tzinfo=None).isoformat()),lambda now:dict(maximum_uses='1')])
def test_ttl_and_scope(changes):
    now=datetime(2026,9,9,tzinfo=timezone.utc)
    values=dict(issued_at=now.isoformat(),expires_at=(now+timedelta(minutes=5)).isoformat())
    values.update(changes(now))
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(auth(**values),now=now,uid=os.getuid(),gid=os.getgid())


def test_structure_isolation_01g1e(tmp_path):
    from core.shopping import colima_projection_authorization as old
    from ops.macos.shopping.colima_projection_authorization_store import ColimaProjectionAuthorizationStore
    with pytest.raises(TypeError): a.ColimaLifecycleAuthorization()
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization({},now=datetime.now(timezone.utc),uid=os.getuid(),gid=os.getgid())
    value=store(tmp_path); receipt=value.consume(snapshot)
    with pytest.raises(old.AuthorizationError):
        old.validate_consumption_result(receipt,now=datetime.now(timezone.utc),uid=os.getuid(),gid=os.getgid())
    with pytest.raises(Exception):
        ColimaProjectionAuthorizationStore._open_existing_for_test(value._path,uid=os.getuid(),gid=os.getgid())


def test_exact_mutation_argv_and_suppression(monkeypatch):
    calls=[]
    monkeypatch.setattr(op.subprocess,'run',lambda *args,**kw:calls.append((args,kw)) or SimpleNamespace(returncode=0))
    assert op._mutate('/trusted/colima',{'HOME':c.HOME})
    assert len(calls)==1
    args,kw=calls[0]
    assert args[0]==['/trusted/colima','restart','--profile',c.PROFILE]
    assert kw['stdout']==kw['stderr']==kw['stdin']==op.subprocess.DEVNULL
    assert kw['timeout']==180 and 'shell' not in kw


def test_fixed_runtime_and_guest_transport(monkeypatch):
    calls=[]
    def read(argv,env):
        calls.append(argv)
        if 'list' in argv: return json.dumps(dict(name=c.PROFILE,status='Running',runtime='docker')).encode()
        return guest()
    monkeypatch.setattr(op,'_read',read)
    monkeypatch.setattr(op,'_snapshot',snapshot)
    result=op._postobserve(snapshot(),'/trusted/colima',{})
    assert result['postconditions_valid'] and result['active_projection_proven']
    assert calls==[['/trusted/colima','list','--profile',c.PROFILE,'--json'],
                  ['/trusted/colima',*c.GUEST_ARGS],['/trusted/colima',*c.GUEST_ARGS]]


def test_no_application_mutation_entrypoint():
    source=Path(op.__file__).read_text()
    for forbidden in ('shell=True','Health.Log','.Config.Env','UbuntuWorkerClient','compose',
                      'docker start','docker stop','docker restart','volume create','network create',
                      'rollback(', 'retry('):
        assert forbidden not in source
    assert source.count('subprocess.run(')==1


def test_non_tty_denied(monkeypatch):
    monkeypatch.setattr(issuer.sys,'stdin',SimpleNamespace(isatty=lambda:False))
    with pytest.raises(RuntimeError,match='TTY_REQUIRED'): issuer.issue()


def test_pending_projection_supported_before_issuance():
    raw=b'\n'.join(guest().splitlines()[:-1])+b'\n'
    assert c.prove_projection(raw,c.PROFILE,pending=True)
    with pytest.raises(ValueError): c.prove_projection(raw,c.PROFILE)
    with pytest.raises(ValueError):
        c.prove_projection(raw.replace(c.mount_tag(c.STOREFRONT).encode(),b'mount0'),c.PROFILE,pending=True)


def test_observation_drift_and_pending_compatibility(monkeypatch):
    monkeypatch.setattr(op,'_read',lambda *args:guest())
    monkeypatch.setattr(op,'_executable',lambda:'/trusted/colima')
    monkeypatch.setattr(op,'_environment',lambda:{})
    later=snapshot();later['declared']['head']='2'*40
    observations=iter([snapshot(),later])
    monkeypatch.setattr(op,'_snapshot',lambda:next(observations))
    with pytest.raises(ValueError): op.observe_preconditions()
    monkeypatch.setattr(op,'_read',lambda *args:b'unknown')
    with pytest.raises(ValueError): op.observe_preconditions()


@pytest.mark.parametrize('kind',['valid','wrong-profile','multiple','unknown-state','wrong-runtime'])
def test_runtime_observation_closed(monkeypatch,kind):
    row=dict(name=c.PROFILE,status='Running',runtime='docker')
    if kind=='wrong-profile': row['name']='default'
    elif kind=='unknown-state': row['status']='Unknown'
    elif kind=='wrong-runtime': row['runtime']='containerd'
    raw=json.dumps(row).encode()
    if kind=='multiple': raw+=b'\n'+raw
    monkeypatch.setattr(op,'_read',lambda *args:raw)
    if kind=='valid': assert op._runtime('/trusted/colima',{})['running']
    else:
        with pytest.raises(ValueError): op._runtime('/trusted/colima',{})


@pytest.mark.parametrize('wrong_endpoint',[False,True])
def test_snapshot_only_fixed_read_commands(monkeypatch,wrong_endpoint):
    monkeypatch.setattr(op,'_startup_guard',lambda:None)
    monkeypatch.setattr(op,'_executable',lambda:'/trusted/colima')
    monkeypatch.setattr(op,'_environment',lambda:{})
    monkeypatch.setattr(op.observation,'_snapshot',lambda:snapshot()['declared'])
    monkeypatch.setattr(op.trusted,'_trusted_docker_executable',lambda:'/trusted/docker')
    calls=[]
    def read(argv,env):
        calls.append(argv)
        if argv[1]=='context':
            return json.dumps('ssh://worker' if wrong_endpoint else 'unix://'+c.HOME+'/.colima/'+c.PROFILE+'/docker.sock').encode()
        if argv[1]=='list': return json.dumps(dict(name=c.PROFILE,status='Running',runtime='docker')).encode()
        assert argv[1:3]==['--context','colima-aicontrolcenter-commerce']
        assert argv[3] in ('container','volume') and argv[4:6]==['inspect','--format']
        if argv[-1]==c.VOLUME['Name']: return json.dumps(c.VOLUME).encode()
        if argv[-1]==c.DATABASE_ID: return json.dumps(c.ATTACHMENT).encode()
        assert argv[-1]==c.FAILED_ID
        return b'"no"'
    monkeypatch.setattr(op,'_read',read)
    if wrong_endpoint:
        with pytest.raises(ValueError): op._snapshot()
        assert len(calls)==1
    else:
        c.validate_snapshot(op._snapshot())
        assert len(calls)==5


@pytest.mark.parametrize('field,value',[
 ('autoActivate',True),('autoActivate',None),('provision',[{'script':'secret-canary'}]),
 ('kubernetes',{'enabled':True}),('layer',True),('runtime','containerd'),('vmType','qemu'),
 ('mounts',c.MOUNTS[:1])])
def test_startup_guard_blocks_extra_authority(monkeypatch,field,value):
    profile=dict(vmType='vz',runtime='docker',mountType='virtiofs',mounts=c.MOUNTS,
                 provision=[],autoActivate=False,kubernetes={'enabled':False})
    profile[field]=value
    monkeypatch.setattr(op,'_owner',lambda:object())
    monkeypatch.setattr(op.observation,'_profile',lambda _: (b'fixture',None))
    monkeypatch.setattr(c,'digest',lambda _:c.PROFILE_SHA256)
    monkeypatch.setattr(c.declared,'_parse',lambda _:('',None,profile))
    with pytest.raises(ValueError): op._startup_guard()


def test_override_existence_blocks_without_read(monkeypatch):
    profile=dict(vmType='vz',runtime='docker',mounts=c.MOUNTS,autoActivate=False)
    monkeypatch.setattr(op,'_owner',lambda:object())
    monkeypatch.setattr(op.observation,'_profile',lambda _: (b'fixture',None))
    monkeypatch.setattr(c,'digest',lambda _:c.PROFILE_SHA256)
    monkeypatch.setattr(c.declared,'_parse',lambda _:('',None,profile))
    monkeypatch.setattr(op.os.path,'lexists',lambda _:True)
    with pytest.raises(ValueError): op._startup_guard()


def test_authorization_exact_expiry_boundary():
    value=auth()
    with pytest.raises(a.AuthorizationError):
        a.validate_authorization(value,now=datetime.fromisoformat(value.expires_at),uid=os.getuid(),gid=os.getgid())
