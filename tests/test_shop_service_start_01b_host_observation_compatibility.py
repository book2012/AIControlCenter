"""Synthetic host metadata and mount evidence; never invoke a live runtime."""
import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ops.macos.shopping import wordpress_port_live_operator as operator
from ops.macos.shopping import storage_continuity_observer as observer
from core.shopping.observability.storage_continuity import ContinuityCompleteness, ContinuityReason


@pytest.fixture(params=['docker', 'docker-compose'])
def host(request, monkeypatch):
    formula = request.param
    root = Path('/opt/homebrew')
    entry = root / 'bin' / formula
    target = root / 'Cellar' / formula / '29.6.2' / 'bin' / formula
    metadata = {p: SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=501, st_gid=80)
                for p in (root, entry.parent, *list(target.parents)[:4])}
    metadata[target] = SimpleNamespace(st_mode=stat.S_IFREG | 0o555, st_uid=501, st_gid=80)
    for p in (entry.parent, root / 'Cellar'):
        metadata[p].st_mode = stat.S_IFDIR | 0o775
    monkeypatch.setattr(operator.os, 'getuid', lambda: 501)
    monkeypatch.setattr(operator.pwd, 'getpwuid', lambda uid: SimpleNamespace(pw_uid=501, pw_dir='/trusted', pw_name='trusted'))
    def resolve(path, strict=False):
        assert strict is True
        return target if path == entry else path
    monkeypatch.setattr(Path, 'resolve', resolve)
    monkeypatch.setattr(Path, 'stat', lambda path: metadata[path])
    monkeypatch.setattr(Path, 'is_symlink', lambda path: False)
    check = operator._trusted_docker_executable if formula == 'docker' else operator._trusted_compose_executable
    return root, entry, target, metadata, check


def test_shared_admin_ancestors_accepted(host):
    root, _, target, metadata, check = host
    metadata[root].st_mode = stat.S_IFDIR | 0o775
    assert check() == str(target)


@pytest.mark.parametrize('location,mode,gid,uid', [
    ('bin', 0o777, 80, 501), ('Cellar', 0o777, 80, 501),
    ('bin', 0o775, 20, 501), ('bin', 0o775, 80, 502),
    ('rack', 0o775, 80, 501), ('version', 0o775, 80, 501),
    ('formula_bin', 0o775, 80, 501),
    ('target', 0o575, 80, 501), ('target', 0o557, 80, 501),
    ('target', 0o444, 80, 501), ('target', 0o555, 80, 502),
])
def test_unsafe_writer_or_target_rejected(host, location, mode, gid, uid):
    root, _, target, metadata, check = host
    path = {'rack': target.parents[2], 'version': target.parents[1],
            'formula_bin': target.parent, 'target': target}.get(location, root / location)
    metadata[path] = SimpleNamespace(st_mode=(stat.S_IFREG if path == target else stat.S_IFDIR) | mode, st_uid=uid, st_gid=gid)
    with pytest.raises(RuntimeError, match='unsafe'):
        check()


@pytest.mark.parametrize('suffix', ['../outside/bin/docker', 'Cellar/other/1/bin/docker', 'Cellar/docker/1/libexec/docker', 'Cellar/docker/1/extra/bin/docker'])
def test_unexpected_resolution(host, monkeypatch, suffix):
    root, _, _, metadata, check = host
    target = Path('/outside/docker') if suffix.startswith('..') else root / suffix
    metadata[target] = SimpleNamespace(st_mode=stat.S_IFREG | 0o555, st_uid=501, st_gid=80)
    monkeypatch.setattr(Path, 'resolve', lambda *a, **k: target)
    with pytest.raises(RuntimeError, match='unexpected'):
        check()


@pytest.mark.parametrize('error', [FileNotFoundError(), RuntimeError('symlink loop')])
def test_missing_broken_resolution(host, monkeypatch, error):
    def broken(*a, **k):
        raise error
    monkeypatch.setattr(Path, 'resolve', broken)
    with pytest.raises(RuntimeError, match='unavailable'):
        host[-1]()


def test_exact_docker_command(host, monkeypatch):
    if host[1].name != 'docker':
        return
    calls = []
    monkeypatch.setenv('PATH', '/attacker')
    monkeypatch.setenv('DOCKER_HOST', 'attacker')
    monkeypatch.setattr(operator.subprocess, 'run', lambda *a, **k: calls.append((a, k)))
    argv = ('docker', '--context', operator.TARGET_CONTEXT, 'info')
    operator._command(argv)
    args, kwargs = calls[0]
    assert args == ([str(host[2]), '--context', 'colima-aicontrolcenter-commerce', 'info'],)
    assert kwargs['cwd'] == operator._REPOSITORY_ROOT
    expected = {'HOME': '/trusted', 'USER': 'trusted', 'LOGNAME': 'trusted', 'PATH': operator._FIXED_PATH, 'DOCKER_CONFIG': '/trusted/.docker'}
    expected.update({key: operator.os.environ[key] for key in ('LANG', 'LC_ALL', 'TMPDIR') if key in operator.os.environ})
    assert kwargs['env'] == expected


def observe(extra=(), change=None, label=None):
    def runner(argv):
        if 'volume' in argv:
            return observer.CommandResult(0, json.dumps(dict(Name=argv[-1], Driver='local', Scope='local', CreatedAt='fixed')))
        name = next(n for n, (_, container) in observer.CONTAINERS.items() if container == argv[-1])
        mount = dict(Type='volume', Name=name, Destination=observer.EXPECTED_DESTINATIONS[name])
        mounts = [mount, *extra]
        if change:
            change(mounts)
        row = dict(Mounts=mounts, Project=observer.COMPOSE_PROJECT, Service=observer.CONTAINERS[name][0])
        if label:
            row[label] = 'wrong'
        return observer.CommandResult(0, json.dumps(row))
    return observer.observe_storage_continuity(runner)


@pytest.mark.parametrize('kind', ['bind', 'tmpfs', 'other'])
def test_mixed_mounts_preserve_complete_volume_identities(kind):
    result = observe([dict(Type=kind, Destination='/extra', Source='/not/projected', Name='ai-shopping-wordpress')] if kind == 'other' else [dict(Type=kind, Destination='/extra')])
    for row in result.volumes:
        assert row.completeness is ContinuityCompleteness.COMPLETE
        assert row.driver == row.scope == 'local'
        assert row.created_at == 'fixed'
        assert row.observed_destination == observer.EXPECTED_DESTINATIONS[row.volume_name]
    assert '/not/projected' not in json.dumps(result.to_json_safe())


@pytest.mark.parametrize('extra', [None, {}, {'Type': 'bind'}, {'Type': '', 'Destination': '/x'}, {'Type': 1, 'Destination': '/x'}, {'Type': 'bind', 'Destination': ''}, {'Type': 'volume', 'Destination': '/x'}, {'Type': 'volume', 'Name': 1, 'Destination': '/x'}])
def test_malformed_arbitrary_mounts(extra):
    assert all(row.completeness is ContinuityCompleteness.MALFORMED for row in observe([extra]).volumes)


def test_missing_canonical_volume_name():
    assert all(row.completeness is ContinuityCompleteness.MALFORMED for row in observe(change=lambda m: m[0].pop('Name')).volumes)


@pytest.mark.parametrize('label', ['Project', 'Service'])
def test_wrong_labels(label):
    assert all(row.completeness is ContinuityCompleteness.MALFORMED for row in observe(label=label).volumes)


def test_duplicate_and_wrong_destination():
    duplicate = observe(change=lambda m: m.append(dict(m[0])))
    wrong = observe(change=lambda m: m[0].update(Destination='/wrong'))
    assert all(row.reason is ContinuityReason.AMBIGUOUS_ATTACHMENT for row in duplicate.volumes)
    assert all(row.reason is ContinuityReason.ATTACHMENT_DESTINATION_MISMATCH for row in wrong.volumes)


def test_nonregular_executable_rejected(host):
    host[3][host[2]].st_mode = stat.S_IFDIR | 0o555
    with pytest.raises(RuntimeError, match='unsafe'):
        host[-1]()


def test_shared_symlink_rejected(host, monkeypatch):
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path == host[0] / 'bin')
    with pytest.raises(RuntimeError, match='unsafe'):
        host[-1]()


@pytest.mark.parametrize('invalid', ['missing', 'symlink', 'directory'])
def test_compose_file_identity_rejected_before_execution(tmp_path, monkeypatch, invalid):
    monkeypatch.setattr(operator, '_REPOSITORY_ROOT', tmp_path)
    path = tmp_path / 'deploy/shopping/compose.yaml'
    path.parent.mkdir(parents=True)
    if invalid == 'symlink':
        target = tmp_path / 'other.yaml'
        target.write_text('services: {}\n')
        path.symlink_to(target)
    elif invalid == 'directory':
        path.mkdir()
    monkeypatch.setattr(operator.subprocess, 'run', lambda *a, **k: pytest.fail('execution attempted'))
    with pytest.raises(RuntimeError, match='Compose file identity'):
        operator._run_compose(operator.build_mutation_invocation())
