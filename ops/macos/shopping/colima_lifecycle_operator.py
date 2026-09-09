"""Fixed Mac-local lifecycle boundary and read-only guest/storage observations."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from core.shopping import colima_lifecycle_reconciliation as c
from core.shopping.colima_lifecycle_authorization import ConsumptionFailure, validate_consumption_result
from ops.macos.shopping.colima_lifecycle_authorization_store import ColimaLifecycleAuthorizationStore
from ops.macos.shopping import colima_projection_operator as observation
from ops.macos.shopping import wordpress_port_live_operator as trusted
from ops.macos.shopping.storage_continuity_observer import VOLUME_FORMAT

_owner = observation._owner
_read = observation._read
ATTACHMENT_FORMAT = ('{{range .Mounts}}{{if eq .Destination "/var/lib/mysql"}}'
    '{"type":{{json .Type}},"name":{{json .Name}},"destination":{{json .Destination}},'
    '"source":{{json .Source}},"rw":{{json .RW}}}{{end}}{{end}}')
RESTART_FORMAT = '{{json .HostConfig.RestartPolicy.Name}}'


def _environment():
    env = trusted._fixed_environment()
    # No caller Colima/Lima selectors, XDG overrides, locale or temporary directory.
    return {key: env[key] for key in ('HOME', 'USER', 'LOGNAME', 'PATH', 'DOCKER_CONFIG')}


def _executable():
    return trusted._trusted_homebrew_executable(Path('/opt/homebrew/bin/colima'), 'colima', 'Colima')


def _startup_guard():
    owner = _owner()
    raw, _ = observation._profile(owner)
    c.require(c.digest(raw) == c.PROFILE_SHA256)
    profile = c.declared._parse(raw)[2]
    c.require(profile.get('vmType') == 'vz' and profile.get('runtime') == 'docker')
    c.require(profile.get('mounts') == c.MOUNTS)
    c.require(profile.get('provision', []) == [])
    c.require(profile.get('kubernetes', {}).get('enabled', False) is False)
    c.require(profile.get('layer', False) is False)
    # Default is true: absence cannot establish no context mutation.
    c.require(profile.get('autoActivate') is False)
    # Do not read potential scripts or secrets in override files. Their existence blocks.
    for name in ('default.yaml', 'override.yaml'):
        path = Path(c.HOME) / '.colima/_lima/_config' / name
        c.require(not os.path.lexists(path))
        parent = path.parent
        while not parent.exists():
            c.require(not parent.is_symlink())
            parent = parent.parent
        c.require(parent.resolve(strict=True) == parent)
    return profile


def _runtime(executable, env):
    rows = [json.loads(line) for line in _read(
        [executable, 'list', '--profile', c.PROFILE, '--json'], env).splitlines() if line.strip()]
    c.require(len(rows) == 1 and rows[0]['name'] == c.PROFILE)
    c.require(rows[0]['status'] in ('Running', 'Stopped'))
    c.require(rows[0]['runtime'] == 'docker')
    return dict(profile=c.PROFILE, running=rows[0]['status'] == 'Running', runtime='docker', vm_type='vz')


def _snapshot():
    _startup_guard()
    executable, env = _executable(), _environment()
    endpoint = json.loads(_read([trusted._trusted_docker_executable(), 'context', 'inspect',
        '--format', '{{json .Endpoints.docker.Host}}', 'colima-aicontrolcenter-commerce'], env))
    c.require(endpoint == 'unix://' + c.HOME + '/.colima/' + c.PROFILE + '/docker.sock')
    def docker(kind, format_, identity):
        return json.loads(_read([trusted._trusted_docker_executable(), '--context',
            'colima-aicontrolcenter-commerce', kind, 'inspect', '--format', format_, identity], env))
    return dict(declared=observation._snapshot(), runtime=_runtime(executable, env),
                storage=docker('volume', VOLUME_FORMAT, c.VOLUME['Name']),
                attachment=docker('container', ATTACHMENT_FORMAT, c.DATABASE_ID),
                wordpress_restart=docker('container', RESTART_FORMAT, c.FAILED_ID),
                lifecycle_authority=True, business_mutation_authority=False)


def observe_preconditions():
    # Reject unsupported source tags before spending one-shot authority. The second
    # mount may still be pending, but the existing projection must be provable.
    c.prove_projection(_read([_executable(), *c.GUEST_ARGS], _environment()), c.PROFILE, pending=True)
    first, second = _snapshot(), _snapshot()
    c.require(c.canonical_snapshot(first) == c.canonical_snapshot(second))
    return first


def _mutate(executable, env):
    # Only one graceful restart. Output is discarded, including failures/timeouts.
    result = subprocess.run([executable, *c.LIFECYCLE_ARGS], cwd=c.ROOT, env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=180, check=False)
    return result.returncode == 0


def _postobserve(before, executable, env):
    result = dict(profile_running_after=None, active_projection_proven=False,
                  database_continuity_observed=False, postconditions_valid=False)
    try:
        result['profile_running_after'] = _runtime(executable, env)['running']
    except Exception:
        pass
    try:
        first = _read([executable, *c.GUEST_ARGS], env)
        second = _read([executable, *c.GUEST_ARGS], env)
        c.require(first == second and result['profile_running_after'] is True)
        result['active_projection_proven'] = c.prove_projection(first, c.PROFILE)
    except Exception:
        pass
    try:
        first, after = _snapshot(), _snapshot()
        c.require(first == after)
        result['database_continuity_observed'] = c.database_continuity(before, after)
        c.validate_post(before, after)
        result['postconditions_valid'] = True
    except Exception:
        pass
    return result


def run():
    consumed, attempted = False, False
    result = c.projection('BLOCKED')
    try:
        owner = _owner()
        executable, env = _executable(), _environment()
        store = ColimaLifecycleAuthorizationStore.open_existing()
        def observe():
            # Resolve again inside the claim transaction; package replacement blocks.
            c.require(_executable() == executable and _environment() == env)
            return observe_preconditions()
        consumed = None
        receipt = validate_consumption_result(store.consume(observe), now=datetime.now(timezone.utc),
            uid=owner.expected_uid, gid=owner.expected_gid)
        consumed = True
        before = c.parse_binding(receipt.precondition_json)
        attempted = True
        succeeded = False
        try:
            succeeded = _mutate(executable, env)
        except Exception:
            pass
        # Even nonzero/timeout outcomes receive read-only forensic observation.
        post = _postobserve(before, executable, env)
        valid = post.pop('postconditions_valid')
        result.update(post)
        result['status'] = ('RECONCILED' if succeeded and valid and
            post['profile_running_after'] is True and post['active_projection_proven'] and
            post['database_continuity_observed'] else 'UNCERTAIN')
    except ConsumptionFailure as error:
        consumed = {c.AuthorizationConsumptionState.NOT_CONSUMED: False,
                    c.AuthorizationConsumptionState.CONSUMED: True}.get(error.state)
    except Exception:
        pass
    result.update(authorization_consumed=consumed, mutation_attempted=attempted,
                  lifecycle_mutation_attempted=attempted)
    if result['status'] == 'BLOCKED' and consumed is not False:
        result['status'] = 'UNCERTAIN'
    return result


def main():
    result = c.projection('CALLER_OVERRIDE_REJECTED') if len(sys.argv) != 1 else run()
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'RECONCILED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
