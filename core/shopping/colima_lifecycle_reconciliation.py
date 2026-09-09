"""Pure 01G1F lifecycle contract; no declaration or application mutation authority."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json

# Reuse only immutable facts and read-only validation, never historical authority.
from core.shopping import colima_projection_reconciliation as declared
from core.shopping.wordpress_port_reconciliation import AuthorizationConsumptionState

ROOT, HOME, REPOSITORY = declared.ROOT, declared.HOME, declared.REPOSITORY
PROFILE, PROFILE_FILE = declared.PROFILE, declared.PROFILE_FILE
MOUNTS, STOREFRONT, CONFIG = declared.MOUNTS, declared.STOREFRONT, declared.CONFIG
FAILED_ID, DATABASE_ID = declared.FAILED_ID, declared.DATABASE_ID
AUTHORITATIVE_WORK_ITEM = 'SHOP-SERVICE-START-01G1F'
MUTATION_ID = AUTHORITATIVE_WORK_ITEM + ':COLIMA_RUNTIME_LIFECYCLE_RECONCILIATION'
PROFILE_SHA256 = '35dc5344e8072f7d787b801b18dec65bf499b93859ec71e7595526a3f7074dce'
DESIRED_SHA256 = '3074cf3a5fd4a2a24fcfd396b86ceab4380d85e388dc054e8639539e1281d4fe'
LIFECYCLE_ARGS = ('restart', '--profile', PROFILE)
GUEST_ARGS = ('ssh', '--profile', PROFILE, '--', '/bin/cat', '/proc/self/mountinfo')
VOLUME = dict(Name='ai-shopping-database', Driver='local', Scope='local',
              CreatedAt='2026-07-27T22:18:53+09:00')
ATTACHMENT = dict(type='volume', name='ai-shopping-database', destination='/var/lib/mysql',
                  source='/var/lib/docker/volumes/ai-shopping-database/_data', rw=True)
require, keys, digest = declared.require, declared.keys, declared.digest


def validate_snapshot(value):
    keys(value, 'declared runtime storage attachment wordpress_restart lifecycle_authority business_mutation_authority')
    declared.validate_snapshot(value['declared'], post=True)
    require(value['declared']['profile_sha256'] == PROFILE_SHA256)
    require(value['declared']['desired_sha256'] == DESIRED_SHA256)
    require(value['runtime'] == dict(profile=PROFILE, running=True, runtime='docker', vm_type='vz'))
    require(type(value['runtime']['running']) is bool)
    require(value['storage'] == VOLUME and value['attachment'] == ATTACHMENT)
    require(value['attachment']['rw'] is True)
    require(value['wordpress_restart'] == 'no')
    require(value['lifecycle_authority'] is True and value['business_mutation_authority'] is False)


def canonical_snapshot(value):
    validate_snapshot(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def parse_binding(raw):
    require(type(raw) is str and len(raw) <= 16384)
    value = json.loads(raw)
    require(canonical_snapshot(value) == raw)
    return value


def mount_tag(path):
    # Lima's stable source+target tag. Legacy positional tags cannot prove source identity.
    return 'lima-' + hashlib.sha256((path + ':' + path).encode()).hexdigest()[:16]


def prove_projection(raw, profile, *, pending=False):
    """Kernel mountinfo evidence, not YAML. Unknown tag/format/overmount fails closed.

    Read-only VFS mount flags prove effective read-only semantics for this guest
    mount namespace, without attempting a write. No claim about future remounts.
    """
    require(profile == PROFILE and type(raw) is bytes and 0 < len(raw) <= 65536)
    mounts = []
    ids = set()
    for line in raw.decode('ascii').splitlines():
        fields = line.split()
        separator = fields.index('-')
        require(separator >= 6 and len(fields) == separator + 4)
        require(fields[0].isdigit() and fields[0] not in ids)
        ids.add(fields[0])
        target = fields[4]
        require(target.startswith('/') and '\\' not in target)
        require(not any(part in ('.', '..') for part in target.split('/')))
        mounts.append((target, fields[3], fields[5].split(','), fields[separator+1], fields[separator+2]))
    expected = {STOREFRONT, CONFIG}
    # Accept exactly these host projections; reject extra virtiofs, duplicate mounts,
    # shopping ancestors/children, bind overlays and ambiguous roots.
    require(sum(m[0] == '/' for m in mounts) == 1)
    active = {m[0] for m in mounts if m[3] == 'virtiofs'}
    if pending:
        require(active in ({STOREFRONT}, expected))
        expected = active
    else:
        require(active == expected)
    for path in expected:
        rows = [m for m in mounts if m[0] == path]
        require(len(rows) == 1)
        target, root, options, fstype, source = rows[0]
        require(root == '/' and fstype == 'virtiofs' and source == mount_tag(path))
        require('ro' in options and 'rw' not in options)
        for other in mounts:
            if other is rows[0]:
                continue
            require(not other[0].startswith(path + '/'))
            require(other[0] == '/' or not path.startswith(other[0] + '/'))
    return True


def database_continuity(before, after):
    """Metadata continuity only: never a backup, integrity or data-preservation claim."""
    prior = before['declared']['database']
    current = after['declared']['database']
    keys(current, 'id started restart_count running healthy')
    require(current['id'] == prior['id'] == DATABASE_ID)
    require(current['running'] is True and current['healthy'] == 'healthy')
    require(type(current['restart_count']) is int and current['restart_count'] >= 0)
    require(type(current['started']) is str and current['started'].endswith('Z'))
    # Runtime restart can change StartedAt and reset/increment RestartCount.
    require(datetime.fromisoformat(current['started']) >= datetime.fromisoformat(prior['started']))
    require(after['storage'] == before['storage'] == VOLUME)
    require(after['attachment'] == before['attachment'] == ATTACHMENT and after['attachment']['rw'] is True)
    return True


def validate_post(before, after):
    # Preserve all preconditions except the truthful runtime lifecycle fields.
    normalized = json.loads(json.dumps(after))
    database_continuity(before, after)
    normalized['declared']['database'] = before['declared']['database']
    require(canonical_snapshot(normalized) == canonical_snapshot(before))


def projection(status, *, consumed=False, attempted=False):
    return dict(status=status, mutation_id=MUTATION_ID, authorization_consumed=consumed,
                lifecycle_mutation_attempted=attempted, mutation_attempted=attempted,
                maximum_uses=1, lifecycle_authority=True, production_authority=False,
                ubuntu_authority=False, business_mutation_authority=False,
                wordpress_generation_recovery_allowed=False, automatic_retry=False,
                automatic_rollback=False, active_projection_proven=False,
                profile_running_after=None, database_continuity_observed=False,
                database_content_preservation_proven=False, backup_proven=False)
