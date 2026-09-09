"""Fixed Mac-local Docker metadata observation and one existing generation start."""
from datetime import datetime, timezone
import json
from pathlib import Path
import stat
import subprocess
import sys
import time
import yaml

from core.shopping import wordpress_existing_generation_start_reconciliation as c
from core.shopping.wordpress_existing_generation_start_artifact import ARTIFACT_PATHS, artifact_identity
from core.shopping.wordpress_existing_generation_start_authorization import ConsumptionFailure, validate_consumption_result
from ops.macos.shopping.wordpress_existing_generation_start_authorization_store import WordPressExistingGenerationStartAuthorizationStore
from ops.macos.shopping import colima_projection_operator as observation
from ops.macos.shopping import wordpress_port_live_operator as trusted
from ops.macos.shopping.colima_lifecycle_operator import ATTACHMENT_FORMAT
from ops.macos.shopping.storage_continuity_observer import VOLUME_FORMAT

_owner = observation._owner
_read = observation._read
WP_FORMAT = ('{"id":{{json .Id}},"status":{{json .State.Status}},"running":{{json .State.Running}},'
    '"restart_count":{{json .RestartCount}},"restart":{{json .HostConfig.RestartPolicy.Name}},'
    '"maximum_retry_count":{{json .HostConfig.RestartPolicy.MaximumRetryCount}},'
    '"healthy":{{with (index .State "Health")}}{{json .Status}}{{else}}null{{end}}}')


def _environment():
    env = trusted._fixed_environment()
    return {key: env[key] for key in ('HOME', 'USER', 'LOGNAME', 'PATH', 'DOCKER_CONFIG')}


def _executable():
    return trusted._trusted_docker_executable()


def _socket(owner):
    path = Path(c.SOCKET)
    c.require(path.resolve(strict=True) == path)
    for parent in path.parents:
        meta = parent.lstat()
        c.require(stat.S_ISDIR(meta.st_mode) and meta.st_uid in (0, owner.expected_uid))
        c.require(meta.st_mode & 0o022 == 0)
    meta = path.lstat()
    c.require(stat.S_ISSOCK(meta.st_mode) and meta.st_uid == owner.expected_uid)
    return dict(dev=meta.st_dev, ino=meta.st_ino, mode=meta.st_mode, uid=meta.st_uid, gid=meta.st_gid)


def _repository(owner):
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/var/empty', 'GIT_CONFIG_NOSYSTEM': '1'}
    head = _read(['/usr/bin/git', 'rev-parse', 'HEAD'], env).decode('ascii').strip()
    c.require(not _read(['/usr/bin/git', 'status', '--porcelain=v1', '--untracked-files=all'], env).strip())
    tracked = _read(['/usr/bin/git', 'ls-files', '-z', '--', *ARTIFACT_PATHS], env).decode('utf-8').split('\0')
    c.require(tracked[-1] == '')
    reviewed_artifact = artifact_identity(c.ROOT, tracked[:-1],
        lambda file: observation._safe_file(file, owner))
    path = c.ROOT / 'deploy/shopping/compose.yaml'
    observation._safe_file(path, owner)
    raw = path.read_bytes()
    c.require(c.digest(raw) == c.COMPOSE_SHA256)
    desired = yaml.safe_load(raw)['services']['wordpress']['restart']
    c.require(desired == 'no')
    return dict(head=head, reviewed_artifact=reviewed_artifact, clean=True, compose_sha256=c.digest(raw), desired_restart=desired)


def _snapshot():
    owner = _owner()
    repo = _repository(owner)
    executable, env = _executable(), _environment()
    socket = _socket(owner)
    endpoint = json.loads(_read([executable, 'context', 'inspect', '--format',
        '{{json .Endpoints.docker.Host}}', c.CONTEXT], env))
    c.require(endpoint == 'unix://' + c.SOCKET)
    def inspect(kind, format_, identity):
        return json.loads(_read([executable, '--context', c.CONTEXT, kind, 'inspect',
            '--format', format_, identity], env))
    result = dict(**repo, owner=dict(uid=owner.expected_uid, gid=owner.expected_gid),
        context=c.CONTEXT, endpoint=endpoint, socket=socket,
        wordpress=inspect('container', WP_FORMAT, c.FAILED_ID),
        database=inspect('container', observation.DB_FORMAT, c.DATABASE_ID),
        storage=inspect('volume', VOLUME_FORMAT, c.VOLUME['Name']),
        attachment=inspect('container', ATTACHMENT_FORMAT, c.DATABASE_ID))
    c.require(_socket(owner) == socket and _repository(owner) == repo)
    return result


def observe_preconditions():
    first, second = _snapshot(), _snapshot()
    c.require(c.canonical_snapshot(first) == c.canonical_snapshot(second))
    return first


def _mutate(executable, env):
    result = subprocess.run([executable, *c.MUTATION_ARGS], cwd=c.ROOT, env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=30, check=False)
    return type(result.returncode) is int and result.returncode == 0


# Reviewed compose: 60s start period + 20 * (15s interval + 5s timeout).
HEALTH_CONVERGENCE_SECONDS = 460
POLL_SECONDS = 5


def _postconditions(before):
    deadline = time.monotonic() + HEALTH_CONVERGENCE_SECONDS
    while True:
        after = _snapshot()
        # Identity, restart and storage drift fail immediately, even during startup.
        c.validate_post(before, after)
        if time.monotonic() >= deadline:
            raise ValueError('HEALTH_CONVERGENCE_TIMEOUT')
        if after['wordpress']['healthy'] == 'healthy':
            return after
        time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))


def run():
    consumed, attempted = False, False
    result = c.projection('BLOCKED')
    try:
        owner = _owner()
        executable, env = _executable(), _environment()
        store = WordPressExistingGenerationStartAuthorizationStore.open_existing()
        def observe():
            c.require(_executable() == executable and _environment() == env)
            return observe_preconditions()
        consumed = None
        consumption = store.consume(observe)
        receipt = validate_consumption_result(consumption, now=datetime.now(timezone.utc),
            uid=owner.expected_uid, gid=owner.expected_gid)
        consumed = True
        before = c.parse_binding(receipt.precondition_json)
        # Freshly recheck after durable consumption. Drift burns authority without mutation.
        c.require(c.canonical_snapshot(observe()) == receipt.precondition_json)
        validate_consumption_result(consumption, now=datetime.now(timezone.utc),
            uid=owner.expected_uid, gid=owner.expected_gid)
        attempted = True
        succeeded = False
        try:
            succeeded = _mutate(executable, env)
        except Exception:
            pass
        # A failed/ambiguous invocation still gets only read-only post-observation.
        _postconditions(before)
        result['database_continuity_observed'] = True
        result['status'] = 'ACCEPTED' if succeeded else 'UNCERTAIN'
    except ConsumptionFailure as error:
        consumed = {c.AuthorizationConsumptionState.NOT_CONSUMED: False,
                    c.AuthorizationConsumptionState.CONSUMED: True}.get(error.state)
        if consumed is not False:
            result['status'] = 'UNCERTAIN'
    except Exception:
        pass
    result.update(authorization_consumed=consumed, mutation_attempted=attempted)
    if result['status'] == 'BLOCKED' and (attempted or consumed is None):
        result['status'] = 'UNCERTAIN'
    return result


def main():
    result = c.projection('CALLER_OVERRIDE_REJECTED') if len(sys.argv) != 1 else run()
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'ACCEPTED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
