"""Fixed profile-only operator. No lifecycle, guest transport or container mutation."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping import colima_projection_reconciliation as c
from core.shopping.colima_projection_authorization import ConsumptionFailure, validate_consumption_result
from ops.macos.shopping.colima_projection_authorization_store import ColimaProjectionAuthorizationStore
from ops.macos.shopping import wordpress_port_live_operator as trusted

WP_FORMAT = ('{"id":{{json .Id}},"status":{{json .State.Status}},"running":{{json .State.Running}},'
             '"pid":{{json .State.Pid}},"exit_code":{{json .State.ExitCode}},'
             '"started":{{json .State.StartedAt}},"restart_count":{{json .RestartCount}}}')
DB_FORMAT = ('{"id":{{json .Id}},"started":{{json .State.StartedAt}},"restart_count":{{json .RestartCount}},'
             '"running":{{json .State.Running}},"healthy":{{with (index .State "Health")}}{{json .Status}}{{else}}null{{end}}}')


def _owner():
    home = resolve_trusted_mac_account_home()
    c.require(home.passwd_home == c.HOME and str(c.ROOT) == c.REPOSITORY)
    return issue_trusted_ownership_expectation(home)


def _safe_file(path, owner):
    c.require(path.is_absolute() and path.resolve(strict=True) == path)
    meta = path.lstat()
    c.require(stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1 and meta.st_size <= 65536)
    c.require((meta.st_uid, meta.st_gid) == (owner.expected_uid, owner.expected_gid))
    c.require(stat.S_IMODE(meta.st_mode) & 0o022 == 0)
    for parent in path.parents:
        info = parent.lstat()
        c.require(stat.S_ISDIR(info.st_mode) and info.st_uid in (0, owner.expected_uid))
        c.require(stat.S_IMODE(info.st_mode) & 0o022 == 0)
    return meta


def _identity(meta):
    # Reads may advance atime; bind only identity and mutation-sensitive metadata.
    return tuple(getattr(meta, name) for name in (
        'st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
        'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def _profile(owner):
    path = Path(c.PROFILE_FILE)
    meta = _safe_file(path, owner)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        c.require(_identity(os.fstat(stream.fileno())) == _identity(meta))
        raw = stream.read(65537)
    c._parse(raw)
    return raw, meta


def _read(argv, environment):
    result = subprocess.run(argv, cwd=c.ROOT, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
    c.require(result.returncode == 0 and len(result.stdout) <= 65536)
    return result.stdout


def _snapshot():
    owner = _owner()
    raw, _ = _profile(owner)
    _, _, profile = c._parse(raw)
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/var/empty', 'GIT_CONFIG_NOSYSTEM': '1'}
    head = _read(['/usr/bin/git', 'rev-parse', 'HEAD'], env).decode('ascii').strip()
    c.require(not _read(['/usr/bin/git', 'status', '--porcelain=v1', '--untracked-files=all'], env).strip())
    desired_path = c.ROOT / 'deploy/shopping/colima-mounts.json'
    _safe_file(desired_path, owner)
    desired = desired_path.read_bytes()
    c.require(json.loads(desired) == c.DESIRED)
    artifacts = {}
    for name in c.ARTIFACTS:
        path = Path(c.CONFIG) / name
        _safe_file(path, owner)
        artifacts[name] = c.digest(path.read_bytes())
    def container(identity, format_):
        return json.loads(_read([trusted._trusted_docker_executable(), '--context',
            'colima-aicontrolcenter-commerce', 'container', 'inspect', '--format', format_, identity], trusted._fixed_environment()))
    return dict(head=head, clean=True, owner=dict(uid=owner.expected_uid, gid=owner.expected_gid),
                profile=c.PROFILE, profile_file=c.PROFILE_FILE, mountType=profile['mountType'],
                mounts=profile['mounts'], profile_sha256=c.digest(raw), desired_sha256=c.digest(desired),
                wordpress=container(c.FAILED_ID, WP_FORMAT), database=container(c.DATABASE_ID, DB_FORMAT),
                artifacts=artifacts, production=False, ubuntu=False)


def observe_preconditions():
    first, second = _snapshot(), _snapshot()
    c.validate_snapshot(first)
    c.require(first == second)
    return first


def _prepare_mutation():
    owner = _owner()
    raw, meta = _profile(owner)
    replacement = c.reconcile_bytes(raw)
    def mutate():
        # Recheck after claim: any failure remains consumed; no retry or rollback.
        current, current_meta = _profile(owner)
        c.require(current == raw and _identity(current_meta) == _identity(meta))
        path = Path(c.PROFILE_FILE)
        fd, temporary = tempfile.mkstemp(prefix='.01g1e-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), stat.S_IMODE(meta.st_mode))
                os.fchown(stream.fileno(), meta.st_uid, meta.st_gid)
                stream.write(replacement)
                stream.flush()
                os.fsync(stream.fileno())
            current, current_meta = _profile(owner)
            c.require(current == raw and _identity(current_meta) == _identity(meta))
            os.replace(temporary, path)  # the sole profile reconciliation attempt
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)  # unused staging file only, never rollback
    return c.digest(raw), c.digest(replacement), mutate


def run():
    consumed, attempted = False, False
    try:
        owner = _owner()
        store = ColimaProjectionAuthorizationStore.open_existing()
        original_hash, replacement_hash, mutate = _prepare_mutation()
        def observe():
            value = observe_preconditions()
            c.require(value['profile_sha256'] == original_hash)
            return value
        consumed = None
        receipt = validate_consumption_result(store.consume(observe), now=datetime.now(timezone.utc),
                                              uid=owner.expected_uid, gid=owner.expected_gid)
        consumed = True
        before = c.parse_binding(receipt.precondition_json)
        attempted = True
        mutate()
        first, after = _snapshot(), _snapshot()
        c.require(first == after and after['profile_sha256'] == replacement_hash)
        c.validate_declared(before, after)
        return c.projection('DECLARED_PENDING_LIFECYCLE', consumed=True, attempted=True)
    except ConsumptionFailure as error:
        consumed = {c.AuthorizationConsumptionState.NOT_CONSUMED: False,
                    c.AuthorizationConsumptionState.CONSUMED: True}.get(error.state)
    except Exception:
        pass
    return c.projection('BLOCKED' if consumed is False else 'UNCERTAIN', consumed=consumed, attempted=attempted)


def main():
    result = c.projection('CALLER_OVERRIDE_REJECTED') if len(sys.argv) != 1 else run()
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'DECLARED_PENDING_LIFECYCLE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
