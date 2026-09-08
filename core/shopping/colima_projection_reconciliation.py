"""Pure 01G1E contract, conservative YAML surgery and read-only validation."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode
from core.shopping.wordpress_port_reconciliation import AuthorizationConsumptionState

ROOT = Path(__file__).resolve().parents[2]
AUTHORITATIVE_WORK_ITEM = 'SHOP-SERVICE-START-01G1E'
MUTATION_ID = AUTHORITATIVE_WORK_ITEM + ':COLIMA_BIND_SOURCE_PROJECTION_RECOVERY'
PROFILE = 'aicontrolcenter-commerce'
PROFILE_FILE = '/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml'
HOME = '/Users/kyouhan'
REPOSITORY = HOME + '/AIControlCenter'
STOREFRONT = REPOSITORY + '/deploy/shopping/wordpress/plugins/ai-shopping-storefront'
CONFIG = REPOSITORY + '/deploy/shopping/config'
MOUNTS = [{'location': p, 'writable': False} for p in (STOREFRONT, CONFIG)]
FAILED_ID = '0636d4cad86d31f0119ccadb1c83ef59ea4b2192bdd74b3f459c2947d24f2a0e'
DATABASE_ID = '434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323'
DATABASE_STARTED = '2026-09-03T03:10:22.559242003Z'
ARTIFACTS = ('shopping-apache-safety.conf', 'shopping-php-safety.ini')
DESIRED = dict(work_item=AUTHORITATIVE_WORK_ITEM, profile=PROFILE, profile_file=PROFILE_FILE,
               mountType='virtiofs', mounts=MOUNTS, production_authority=False,
               ubuntu_authority=False, lifecycle_authority=False)


def require(condition):
    if not condition:
        raise ValueError('COLIMA_PROJECTION_REJECTED')


def keys(value, names):
    require(type(value) is dict and set(value) == set(names.split()))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _parse(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 65536)
    text = raw.decode('utf-8')
    # Aliases, anchors, tags and duplicate keys are rejected, including unrelated fields.
    for token in yaml.scan(text):
        require(not isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken, yaml.tokens.TagToken)))
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    def unique(n):
        if isinstance(n, MappingNode):
            seen = set()
            for key, value in n.value:
                require(isinstance(key, ScalarNode) and key.tag == 'tag:yaml.org,2002:str')
                require(key.value not in seen and key.value != '<<')
                seen.add(key.value)
                unique(value)
        elif isinstance(n, SequenceNode):
            for item in n.value:
                unique(item)
    unique(node)
    require(isinstance(node, MappingNode) and not node.flow_style)
    value = yaml.safe_load(text)
    require(type(value) is dict and value.get('mountType') == 'virtiofs')
    mounts = value.get('mounts')
    require(type(mounts) is list and len(mounts) in (1, 2))
    for mount in mounts:
        keys(mount, 'location writable')
        require(type(mount['location']) is str and mount['writable'] is False)
    require(mounts == MOUNTS[:1] or (len(mounts) == 2 and all(mounts.count(m) == 1 for m in MOUNTS)))
    return text, node, value


def reconcile_bytes(raw):
    """Only append the missing exact mount; all existing bytes are retained."""
    text, node, value = _parse(raw)
    require(value['mounts'] == MOUNTS[:1])  # already reconciled is drift, not retry
    mount_node = next(v for k, v in node.value if k.value == 'mounts')
    require(isinstance(mount_node, SequenceNode) and not mount_node.flow_style)
    # Insert after the last mount, before the next top-level field or trailing comments.
    end = mount_node.value[-1].end_mark.index
    require(end == 0 or text[end-1] == '\n')
    indent = ' ' * mount_node.start_mark.column
    addition = f'{indent}- location: {CONFIG}\n{indent}  writable: false\n'
    result = (text[:end] + addition + text[end:]).encode('utf-8')
    _, _, after = _parse(result)
    require(after == {**value, 'mounts': MOUNTS})
    return result


def validate_snapshot(v, *, post=False):
    keys(v, 'head clean owner profile profile_file mountType mounts profile_sha256 desired_sha256 wordpress database artifacts production ubuntu')
    require(type(v['head']) is str and re.fullmatch('[0-9a-f]{40}', v['head']))
    require(v['clean'] is True and v['production'] is False and v['ubuntu'] is False)
    keys(v['owner'], 'uid gid')
    require(type(v['owner']['uid']) is int and v['owner']['uid'] > 0)
    require(type(v['owner']['gid']) is int and v['owner']['gid'] >= 0)
    require(v['profile'] == PROFILE and v['profile_file'] == PROFILE_FILE and v['mountType'] == 'virtiofs')
    require(type(v['mounts']) is list)
    for mount in v['mounts']:
        keys(mount, 'location writable')
        require(type(mount['location']) is str and mount['writable'] is False)
    require(v['mounts'] == (MOUNTS if post else MOUNTS[:1]))
    for field in ('profile_sha256', 'desired_sha256'):
        require(type(v[field]) is str and re.fullmatch('[0-9a-f]{64}', v[field]))
    keys(v['wordpress'], 'id status running pid exit_code started restart_count')
    require(v['wordpress'] == dict(id=FAILED_ID, status='created', running=False, pid=0,
                                  exit_code=127, started='0001-01-01T00:00:00Z', restart_count=0))
    keys(v['database'], 'id started restart_count running healthy')
    require(v['database'] == dict(id=DATABASE_ID, started=DATABASE_STARTED, restart_count=0, running=True, healthy='healthy'))
    for name in ('wordpress', 'database'):
        require(type(v[name]['restart_count']) is int and type(v[name]['running']) is bool)
    require(type(v['wordpress']['pid']) is int and type(v['wordpress']['exit_code']) is int)
    require(type(v['artifacts']) is dict and set(v['artifacts']) == set(ARTIFACTS))
    for d in v['artifacts'].values():
        require(type(d) is str and re.fullmatch('[0-9a-f]{64}', d))


def canonical_snapshot(value):
    validate_snapshot(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def parse_binding(raw):
    require(type(raw) is str and len(raw) <= 16384)
    value = json.loads(raw)
    require(canonical_snapshot(value) == raw)
    return value


def validate_declared(before, after):
    validate_snapshot(before)
    validate_snapshot(after, post=True)
    for name in before.keys() - {'mounts', 'profile_sha256'}:
        require(before[name] == after[name])
    require(before['profile_sha256'] != after['profile_sha256'])


def validate_post(before, after, guest):
    """Pure validator for trusted read-only guest evidence; does not collect it."""
    validate_declared(before, after)
    keys(guest, 'config storefront artifacts production ubuntu')
    require(guest['production'] is False and guest['ubuntu'] is False)
    for name in ('config', 'storefront'):
        keys(guest[name], 'fstype readonly')
        require(guest[name]['fstype'] == 'virtiofs' and guest[name]['readonly'] is True)
    require(guest['artifacts'] == {name: 'regular file' for name in ARTIFACTS})


def projection(status, *, consumed=False, attempted=False):
    return dict(status=status, mutation_id=MUTATION_ID, authorization_consumed=consumed,
                mutation_attempted=attempted, maximum_uses=1, production_authority=False,
                ubuntu_authority=False, business_mutation_authority=False, lifecycle_authority=False,
                wordpress_generation_recovery_allowed=False, automatic_retry=False,
                automatic_rollback=False, active_projection_proven=False)
