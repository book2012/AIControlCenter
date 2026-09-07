import inspect
import json
from types import SimpleNamespace

import pytest
import requests

from ops.macos.shopping import woocommerce_authenticated_read_validator as validator


KEY = 'fake-key-never-project'
SECRET = 'fake-secret-never-project'
CANONICAL = 'https://catalog.invalid'


@pytest.fixture(autouse=True)
def repository_facts(monkeypatch):
    facts = dict(runtime_owner='mac', ubuntu_dependency=False,
                 mariadb_host_published_port=False, wordpress_bind_host='127.0.0.1',
                 wordpress_port=58082, woocommerce_host_service_id='shopping-runtime',
                 woocommerce_kind='wordpress-plugin-commerce-engine')
    monkeypatch.setattr(validator, 'load_shopping_repository_facts', lambda paths: facts)
    # No test may reach the real network, including through an unexpected method.
    monkeypatch.setattr(requests.Session, 'send', lambda *a, **k: pytest.fail('live network'))
    return facts


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    path = tmp_path / 'read.env'
    path.write_text(
        'SHOPPING_WOOCOMMERCE_BASE_URL=https://catalog.invalid\n'
        f'SHOPPING_WOOCOMMERCE_CONSUMER_KEY={KEY}\n'
        f'SHOPPING_WOOCOMMERCE_CONSUMER_SECRET={SECRET}\n'
        'SHOPPING_WOOCOMMERCE_API_KEY_PERMISSION=read\n'
    )
    path.chmod(0o600)
    monkeypatch.setattr(validator, 'DEFAULT_WOOCOMMERCE_READ_SECRET_PATH', path)
    return path


@pytest.fixture
def wire(boundary, monkeypatch):
    state = SimpleNamespace(status=200, payload=[{'id': 1}], total='1', calls=[], failure=None)

    def get(_session, url, **kwargs):
        state.calls.append((url, kwargs))
        if state.failure:
            raise state.failure
        def body():
            assert state.status == 200, 'error body must not be read'
            return state.payload
        return SimpleNamespace(status_code=state.status, json=body,
                               headers={'X-WP-Total': state.total}, close=lambda: None)

    monkeypatch.setattr(requests.Session, 'get', get)
    for method in ('post', 'put', 'patch', 'delete', 'head', 'options'):
        monkeypatch.setattr(requests.Session, method, lambda *a, **k: pytest.fail('mutation'))
    return state


def safe(result):
    serialized = json.dumps(result, allow_nan=False)
    assert all(value not in serialized for value in (KEY, SECRET, CANONICAL, 'oauth_', 'Authorization'))
    for key in ('production_authority', 'ubuntu_authority', 'automatic_retry',
                'mutation_performed', 'secret_values_exposed'):
        assert result[key] is False


@pytest.mark.parametrize('payload,total,empty', [([{'id': 1}], '9', False), ([], '0', True)])
def test_success(wire, payload, total, empty):
    wire.payload, wire.total = payload, total
    result = validator.validate_once()
    safe(result)
    assert result['status'] == 'READY'
    assert result['credential_boundary_valid'] is True
    assert result['authentication_accepted'] is True
    assert result['api_readable'] is result['catalog_readable'] is True
    assert result['catalog_total'] == int(total)
    assert result['catalog_empty'] is empty
    assert len(wire.calls) == 1
    url, kwargs = wire.calls[0]
    assert url == 'http://127.0.0.1:58082/wp-json/wc/v3/products'
    assert kwargs['headers'] == {'Host': 'catalog.invalid'}
    assert kwargs['auth'] == (KEY, SECRET)
    assert result['connect_target_source'] == 'repository_service_start'
    assert result['connect_target_loopback'] is True
    assert kwargs['allow_redirects'] is False
    assert kwargs['timeout'] == (5.0, 15.0)
    assert 'verify' not in kwargs
    assert kwargs['params'] == {'context': 'view', 'status': 'publish', 'page': '1', 'per_page': '1'}


@pytest.mark.parametrize('kind', ['file_mode', 'parent_mode', 'permission', 'symlink', 'owner', 'parent_owner'])
def test_invalid_boundary(boundary, wire, monkeypatch, kind):
    if kind == 'file_mode':
        boundary.chmod(0o644)
    elif kind == 'parent_mode':
        boundary.parent.chmod(0o755)
    elif kind == 'permission':
        boundary.write_text(boundary.read_text().replace('=read\n', '=write\n'))
    elif kind == 'symlink':
        link = boundary.parent / 'link'
        link.symlink_to(boundary)
        monkeypatch.setattr(validator, 'DEFAULT_WOOCOMMERCE_READ_SECRET_PATH', link)
    else:
        from pathlib import Path
        original = Path.lstat
        target = boundary if kind == 'owner' else boundary.parent
        def metadata(path):
            value = original(path)
            if path == target:
                return SimpleNamespace(st_uid=value.st_uid + 1, st_mode=value.st_mode)
            return value
        monkeypatch.setattr(Path, 'lstat', metadata)
    result = validator.validate_once()
    safe(result)
    assert result['reason_codes'] == ['CREDENTIAL_BOUNDARY_INVALID']
    assert wire.calls == []


@pytest.mark.parametrize('status,reason,accepted', [(401, 'AUTHENTICATION_REJECTED', False),
    (403, 'AUTHENTICATION_REJECTED', False), (500, 'API_UNAVAILABLE', None),
    (302, 'API_UNAVAILABLE', None), ('200', 'MALFORMED_EVIDENCE', None)])
def test_http_failure(wire, status, reason, accepted):
    wire.status = status
    result = validator.validate_once()
    safe(result)
    assert result['reason_codes'] == [reason]
    assert result['authentication_accepted'] is accepted
    assert len(wire.calls) == 1


@pytest.mark.parametrize('payload,total', [({}, '1'), ([{}], '1'), ([{'id': True}], '1'),
    ([], '1'), ([{'id': 1}], '0'), ([], '-1'), ([], None), ([], '1.0'),
    ([{'id': 1}, {'id': 2}], '2')])
def test_malformed_catalog(wire, payload, total):
    wire.payload, wire.total = payload, total
    result = validator.validate_once()
    safe(result)
    assert result['status'] == 'BLOCKED'
    assert result['reason_codes'] == ['CATALOG_UNREADABLE', 'MALFORMED_EVIDENCE']
    assert result['authentication_accepted'] is True


def test_transport_failure_no_retry_or_exception_projection(wire, capsys, monkeypatch):
    wire.failure = requests.Timeout(KEY + SECRET)
    monkeypatch.setattr(validator.sys, 'argv', ['validator'])
    assert validator.main() == 1
    output = capsys.readouterr()
    assert KEY not in output.out + output.err and SECRET not in output.out + output.err
    assert json.loads(output.out)['authentication_accepted'] is None
    assert len(wire.calls) == 1


def test_no_caller_target_or_argument_echo(wire, monkeypatch, capsys):
    assert not inspect.signature(validator.validate_once).parameters
    monkeypatch.setattr(validator.sys, 'argv', ['validator', '--url', SECRET])
    assert validator.main() == 2
    assert SECRET not in str(capsys.readouterr())
    assert wire.calls == []
    monkeypatch.setenv('WOOCOMMERCE_INTERNAL_BASE_URL', 'http://untrusted.invalid')
    monkeypatch.setenv('WOOCOMMERCE_BASE_URL', 'http://untrusted.invalid')
    assert validator.validate_once()['status'] == 'READY'
    assert wire.calls[0][0] == 'http://127.0.0.1:58082/wp-json/wc/v3/products'


def test_policy_denial_prevents_network(wire, monkeypatch):
    monkeypatch.setattr(validator, 'evaluate_external_read', lambda **k: SimpleNamespace(allowed=False))
    assert validator.validate_once()['reason_codes'] == ['EXTERNAL_READ_POLICY_DENIED']
    assert wire.calls == []


def test_transport_has_only_get_capability():
    for cls in (validator._StatusCheckedReadTransport, validator.WooCommerceReadTransportSession):
        assert not any(hasattr(cls, method) for method in ('post', 'put', 'patch', 'delete'))


@pytest.mark.parametrize('field,value', [
    ('wordpress_port', '58082'), ('wordpress_port', True), ('wordpress_port', False),
    ('wordpress_port', 0), ('wordpress_port', 65536), ('wordpress_port', None),
    ('wordpress_port', 58082.0), ('wordpress_port', -1),
    ('wordpress_bind_host', '0.0.0.0'), ('ubuntu_dependency', True),
    ('ubuntu_dependency', 0), ('runtime_owner', 'ubuntu'),
    ('mariadb_host_published_port', True), ('mariadb_host_published_port', 0),
    ('woocommerce_host_service_id', 'other'), ('woocommerce_kind', 'other'),
])
def test_invalid_target_pre_network(wire, repository_facts, monkeypatch, field, value):
    repository_facts[field] = value
    monkeypatch.setattr(validator, '_StatusCheckedReadTransport',
                        lambda: pytest.fail('transport constructed for invalid target'))
    result = validator.validate_once()
    safe(result)
    assert result['status'] == 'BLOCKED'
    assert result['reason_codes'] == ['RUNTIME_TARGET_INVALID']
    assert wire.calls == []


@pytest.mark.parametrize('field', [
    'runtime_owner', 'ubuntu_dependency', 'mariadb_host_published_port',
    'wordpress_bind_host', 'wordpress_port', 'woocommerce_host_service_id', 'woocommerce_kind',
])
def test_missing_target_fact(wire, repository_facts, field):
    del repository_facts[field]
    assert validator.validate_once()['reason_codes'] == ['RUNTIME_TARGET_INVALID']
    assert wire.calls == []


def test_loader_failure_safe_projection(wire, monkeypatch, capsys):
    def unavailable(paths):
        raise RuntimeError(KEY + SECRET + CANONICAL + 'oauth_signature Authorization')
    monkeypatch.setattr(validator, 'load_shopping_repository_facts', unavailable)
    monkeypatch.setattr(validator.sys, 'argv', ['validator'])
    assert validator.main() == 1
    output = capsys.readouterr()
    safe(json.loads(output.out))
    assert output.err == ''
    assert json.loads(output.out)['reason_codes'] == ['RUNTIME_TARGET_INVALID']
    assert wire.calls == []


@pytest.mark.parametrize('port', [1, 58082, 65535])
def test_repository_target_and_canonical_adapter_identity(wire, repository_facts, monkeypatch, port):
    from pathlib import Path
    repository_facts['wordpress_port'] = port
    original = validator.WooCommerceRESTAdapter
    captured = {}
    def adapter(**kwargs):
        captured.update(kwargs)
        return original(**kwargs)
    def load(paths):
        assert paths == validator.ShoppingRepositoryPaths.canonical(
            Path(validator.__file__).resolve().parents[3])
        return repository_facts
    monkeypatch.setattr(validator, 'WooCommerceRESTAdapter', adapter)
    monkeypatch.setattr(validator, 'load_shopping_repository_facts', load)
    monkeypatch.setenv('SHOPPING_WORDPRESS_PORT', '1234')
    monkeypatch.setenv('SHOPPING_WOOCOMMERCE_BASE_URL', 'http://untrusted.invalid')
    assert validator.validate_once()['status'] == 'READY'
    assert captured['base_url'] == CANONICAL
    assert captured['connect_base_url'] == f'http://127.0.0.1:{port}'
    assert len(wire.calls) == 1


def test_oauth_signature_uses_canonical_identity(boundary, wire, monkeypatch):
    boundary.write_text(boundary.read_text().replace('https://catalog.invalid', 'http://catalog.invalid'))
    original = validator.WooCommerceRESTAdapter._oauth_params
    signed = []
    def oauth(self, method, url, params):
        signed.append((method, url))
        return original(self, method, url, params)
    monkeypatch.setattr(validator.WooCommerceRESTAdapter, '_oauth_params', oauth)
    result = validator.validate_once()
    safe(result)
    assert result['status'] == 'READY'
    assert signed == [('GET', 'http://catalog.invalid/wp-json/wc/v3/products')]
    assert len(wire.calls) == 1
    assert wire.calls[0][1]['headers'] == {'Host': 'catalog.invalid'}
    assert 'oauth_signature' in wire.calls[0][1]['params']


def test_retries_disabled():
    transport = validator.WooCommerceReadTransportSession(max_retries=99)
    assert transport.max_retries == 0
    assert transport.retry_after_max_seconds == 0
    assert all(adapter.max_retries.total == 0
               for adapter in transport._session.adapters.values())
