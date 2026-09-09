"""Pure, isolated 01G1F0 restart-policy contract; metadata continuity only."""
import json
import re
from core.shopping.colima_projection_reconciliation import (
    ROOT, HOME, REPOSITORY, PROFILE, PROFILE_FILE, FAILED_ID, DATABASE_ID,
    require, keys, digest,
)
from core.shopping.colima_lifecycle_reconciliation import VOLUME, ATTACHMENT
from core.shopping.wordpress_port_reconciliation import AuthorizationConsumptionState

AUTHORITATIVE_WORK_ITEM = 'SHOP-SERVICE-START-01G1F0'
MUTATION_ID = AUTHORITATIVE_WORK_ITEM + ':WORDPRESS_RESTART_POLICY_RECONCILIATION'
COMPOSE_SHA256 = '0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c'
CONTEXT = 'colima-aicontrolcenter-commerce'
SOCKET = HOME + '/.colima/' + PROFILE + '/docker.sock'
MUTATION_ARGS = ('--context', CONTEXT, 'update', '--restart=no', FAILED_ID)
DENIED = ('production_authority', 'ubuntu_authority', 'business_mutation_authority',
          'lifecycle_authority', 'wordpress_generation_recovery_allowed',
          'capability_authority', 'verifier_authority')


def validate_snapshot(v, *, post=False):
    keys(v, 'head clean owner compose_sha256 desired_restart context endpoint socket wordpress database storage attachment')
    require(type(v['head']) is str and re.fullmatch('[0-9a-f]{40}', v['head']))
    require(v['clean'] is True and v['compose_sha256'] == COMPOSE_SHA256 and v['desired_restart'] == 'no')
    keys(v['owner'], 'uid gid')
    require(type(v['owner']['uid']) is int and v['owner']['uid'] > 0)
    require(type(v['owner']['gid']) is int and v['owner']['gid'] >= 0)
    require(v['context'] == CONTEXT and v['endpoint'] == 'unix://' + SOCKET)
    keys(v['socket'], 'dev ino mode uid gid')
    require(all(type(n) is int and n >= 0 for n in v['socket'].values()))
    import stat
    require(stat.S_ISSOCK(v['socket']['mode']) and v['socket']['uid'] == v['owner']['uid'])
    keys(v['wordpress'], 'id status running restart_count restart maximum_retry_count')
    require(v['wordpress'] == dict(id=FAILED_ID, status='created', running=False,
        restart_count=0, restart='no' if post else 'unless-stopped', maximum_retry_count=0))
    require(v['wordpress']['running'] is False)
    for field in ('restart_count', 'maximum_retry_count'):
        require(type(v['wordpress'][field]) is int)
    keys(v['database'], 'id started restart_count running healthy')
    db = v['database']
    require(db['id'] == DATABASE_ID and db['running'] is True and db['healthy'] == 'healthy')
    require(type(db['restart_count']) is int and db['restart_count'] >= 0)
    require(type(db['started']) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z', db['started']))
    require(v['storage'] == VOLUME and v['attachment'] == ATTACHMENT and v['attachment']['rw'] is True)


def canonical_snapshot(v):
    validate_snapshot(v)
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def parse_binding(raw):
    require(type(raw) is str and len(raw) <= 16384)
    value = json.loads(raw)
    require(canonical_snapshot(value) == raw)
    return value


def validate_post(before, after):
    validate_snapshot(before)
    validate_snapshot(after, post=True)
    normalized = json.loads(json.dumps(after))
    normalized['wordpress']['restart'] = 'unless-stopped'
    require(canonical_snapshot(normalized) == canonical_snapshot(before))


def projection(status, *, consumed=False, attempted=False):
    return dict(status=status, mutation_id=MUTATION_ID, authorization_consumed=consumed,
        mutation_attempted=attempted, maximum_uses=1, **dict.fromkeys(DENIED, False),
        automatic_retry=False, automatic_rollback=False, backup_proven=False,
        database_content_preservation_proven=False, database_continuity_observed=False)
