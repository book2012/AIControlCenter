"""Offline synthetic checks only: sockets and trust identity are substituted."""
import hashlib
import inspect
import json
import logging
import os
import pickle
import stat
from pathlib import Path

import pytest

from core.shopping.control_plane_read import capability as c, provider as p, transport as t, contracts as k

TOKEN = 'ab' * 32  # synthetic fixture, never a provisioned credential


def cap():
    return c.ControlPlaneShoppingReadCapability(TOKEN)


def test_entropy(monkeypatch):
    seen = []
    def entropy(n):
        seen.append(n)
        return bytes(range(n))
    monkeypatch.setattr(c.secrets, 'token_bytes', entropy)
    value = c.generate_control_plane_shopping_read_capability()
    assert seen == [32]
    assert value._request_ascii() == bytes(range(32)).hex()
    assert c._generate_with_entropy_for_tests(entropy)._request_ascii() == value._request_ascii()
    assert len(value._request_ascii().encode('ascii')) == 64
    with pytest.raises(c.CapabilityError):
        c._generate_with_entropy_for_tests(lambda n: b'x' * 31)


@pytest.mark.parametrize('value', [TOKEN.upper(), TOKEN[:-1], TOKEN+'0', 'g'*64, '０'*64, TOKEN+'\n', None, b'a'*64])
def test_canonical(value):
    with pytest.raises(c.CapabilityError):
        c.ControlPlaneShoppingReadCapability(value)
    with pytest.raises(c.CapabilityError):
        c.ShoppingReadVerifier(value)


def test_verifier_and_safe_values(caplog):
    value = cap()
    verifier = c.derive_verifier(value)
    digest = hashlib.sha256(TOKEN.encode('ascii')).hexdigest()
    assert verifier._provisioning_digest() == digest
    assert hashlib.sha256(digest.encode('ascii')).hexdigest() != digest
    with caplog.at_level(logging.INFO):
        logging.info('%s %r', value, verifier)
    for obj in (value, verifier, k.VerifierCASContract(None, verifier)):
        assert TOKEN not in repr(obj) + str(obj)
        assert digest not in repr(obj) + str(obj)
        with pytest.raises((TypeError, c.CapabilityError)) as error:
            json.dumps(obj)
        assert TOKEN not in str(error.value)
    for obj in (value, verifier):
        with pytest.raises(c.CapabilityError):
            pickle.dumps(obj)
    assert TOKEN not in caplog.text and digest not in caplog.text


@pytest.fixture
def source(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    leaf = home.joinpath(*p.COMPONENTS)
    leaf.parent.mkdir(parents=True, mode=0o700)
    leaf.parent.chmod(0o700)
    leaf.write_bytes(p.KEY + b'=' + TOKEN.encode() + b'\n')
    leaf.chmod(0o600)
    # Model trusted root-owned non-writable ancestors above the synthetic home.
    # Actual opens/stat identities/symlinks and home subtree metadata remain real.
    real_stat, real_fstat = os.stat, os.fstat
    ancestors = {real_stat(path).st_ino for path in home.parents}
    def trusted(s):
        if s.st_ino not in ancestors:
            return s
        class Meta:
            def __getattr__(self, key): return getattr(s, key)
            st_uid = 0
            st_mode = s.st_mode & ~0o022
        return Meta()
    monkeypatch.setattr(p.os, 'stat', lambda *a, **kw: trusted(real_stat(*a, **kw)))
    monkeypatch.setattr(p.os, 'fstat', lambda *a: trusted(real_fstat(*a)))
    return home, leaf


def load(source):
    return p._read_fixed(str(source[0]), os.getuid(), os.getgid())


def test_provider_reads(source):
    assert load(source)._request_ascii() == TOKEN
    assert list(inspect.signature(p.ControlPlaneShoppingReadCapabilityFileProvider).parameters) == []


@pytest.mark.parametrize('kind', ['parent_mode', 'leaf_mode', 'uid', 'gid', 'leaf_symlink', 'parent_symlink', 'hardlink', 'oversized', 'duplicate', 'unknown', 'malformed', 'fifo'])
def test_provider_denials(source, kind):
    home, leaf = source
    if kind == 'parent_mode': leaf.parent.chmod(0o750)
    elif kind == 'leaf_mode': leaf.chmod(0o400)
    elif kind in ('uid', 'gid'):
        with pytest.raises(c.CapabilityError):
            p._read_fixed(str(home), os.getuid() + (kind == 'uid'), os.getgid() + (kind == 'gid'))
        return
    elif kind == 'leaf_symlink':
        other = leaf.with_suffix('.other'); leaf.rename(other); leaf.symlink_to(other)
    elif kind == 'parent_symlink':
        other = leaf.parent.with_name('other'); leaf.parent.rename(other); leaf.parent.symlink_to(other)
    elif kind == 'hardlink': os.link(leaf, leaf.with_suffix('.hard'))
    elif kind == 'oversized': leaf.write_bytes(b'x' * (p.MAX_SOURCE_BYTES+1))
    elif kind == 'duplicate': leaf.write_bytes(leaf.read_bytes()*2)
    elif kind == 'unknown': leaf.write_bytes(b'UNKNOWN='+TOKEN.encode())
    elif kind == 'malformed': leaf.write_bytes(p.KEY+b'='+TOKEN.upper().encode())
    elif kind == 'fifo': leaf.unlink(); os.mkfifo(leaf, 0o600)
    with pytest.raises(c.CapabilityError) as error:
        load(source)
    assert error.value.__context__ is None
    assert TOKEN not in repr(error.value)


class FakeSocket:
    def __init__(self, response, clock=None, tick=0):
        self.response = response; self.clock = clock; self.tick = tick
        self.timeouts = []; self.sent = b''; self.closed = False
    def __enter__(self): return self
    def __exit__(self, *args): self.closed = True
    def settimeout(self, value): self.timeout = value; self.timeouts.append(value)
    def connect(self, target): self.target = target
    def send(self, data): self.sent += data; return len(data)
    def recv(self, count):
        if self.clock is not None:
            self.clock[0] += min(self.tick, self.timeout)
            if self.tick >= self.timeout: raise TimeoutError(TOKEN)
            count = min(count, 1)
        data, self.response = self.response[:count], self.response[count:]
        return data


def response(payload=None, status=b'200 OK', extra=b''):
    body = json.dumps(payload or {'items': [], 'page': 1, 'page_size': 20, 'has_more': False}).encode()
    return b'HTTP/1.1 '+status+b'\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body)).encode()+b'\r\n'+extra+b'\r\n'+body


def wire(monkeypatch, raw, **kw):
    sock = FakeSocket(raw, **kw)
    monkeypatch.setattr(t.socket, 'socket', lambda *args: sock)
    return sock


def test_fixed_transport(monkeypatch):
    sock = wire(monkeypatch, response())
    adapter = t.ControlPlaneShoppingReadAdapter()
    assert adapter.products(cap()) == {'items': [], 'page': 1, 'page_size': 20, 'has_more': False}
    assert sock.target == ('127.0.0.1', int(t.WORDPRESS_PORT_EXPECTED))
    assert sock.sent.startswith(b'GET '+t.REST_PATH.encode())
    assert b'Authorization: Bearer '+TOKEN.encode() in sock.sent
    assert sock.closed and all(0 < x <= 2 for x in sock.timeouts)
    assert not adapter.trust_env and not adapter.proxies and not adapter.redirects and adapter.max_retries == 0
    assert list(inspect.signature(adapter.products).parameters) == ['capability', 'page', 'page_size']
    with pytest.raises(TypeError): adapter.products(cap(), url='http://example.invalid')
    with pytest.raises(t.ShoppingReadError): adapter.products(c.derive_verifier(cap()))


@pytest.mark.parametrize('page,size', [(0,20),(10001,20),(True,20),('1',20),(1,0),(1,21),(1,False)])
def test_page_bounds(page, size):
    with pytest.raises(t.ShoppingReadError): t.validate_page(page,size)


def test_valid_bounds():
    for page in (1,10000):
        for size in (1,20): t.validate_page(page,size)


@pytest.mark.parametrize('raw', [response(status=b'302 Found'), response(extra=b'Transfer-Encoding: chunked\r\n'),
    b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 99999\r\n\r\n',
    b'x'*8193, response({'items':[{'id':1,'name':TOKEN}], 'page':1,'page_size':20,'has_more':False}),
    response({'items':[{'id':1,'name':'x'*201}], 'page':1,'page_size':20,'has_more':False}),
    response({'items':[{'id':2,'name':'two'},{'id':1,'name':'one'}], 'page':1,'page_size':20,'has_more':False}),
    response({'items':[], 'page':True,'page_size':20,'has_more':False}),
    response({'items':[], 'page':1,'page_size':20,'has_more':False,'orders':[]})])
def test_bad_responses(monkeypatch, raw, caplog):
    sock = wire(monkeypatch, raw)
    with pytest.raises(t.ShoppingReadError) as error: t.ControlPlaneShoppingReadAdapter().products(cap())
    assert error.value.__context__ is None
    assert TOKEN not in str(error.value) + repr(error.value) + caplog.text
    assert sock.closed


def test_absolute_deadline(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(t.time, 'monotonic', lambda: clock[0])
    sock = wire(monkeypatch, response(), clock=clock, tick=0.75)
    with pytest.raises(t.ShoppingReadError): t.ControlPlaneShoppingReadAdapter().products(cap())
    assert clock[0] == t.TOTAL_TIMEOUT
    assert sock.closed and sock.timeouts[-1] < t.READ_TIMEOUT


def test_synthetic_contracts():
    verifier = c.derive_verifier(cap())
    contract = k.VerifierCASContract(None, verifier)
    payload = contract.boundary_payload()
    assert TOKEN not in json.dumps(payload)
    assert payload['pending_verifier'] == verifier._provisioning_digest()
    assert payload['maximum_uses'] == 1 and payload['automatic_retry'] is False
    assert payload['autoload'] is False
    assert payload['container'] == 'shopping-wordpress' and payload['project'] == 'ai-shopping'
    assert not k.LIVE_OPERATOR_AVAILABLE
    assert not k.PUBLIC_EDGE_RUNTIME_ISOLATION_PROVEN and not k.DEPLOYMENT_LOGGING_SAFETY_PROVEN
    assert k.PUBLIC_EDGE_DENY_PREFIX == '/wp-json/aicontrolcenter/v1/shopping/'
    with pytest.raises(c.CapabilityError): k.VerifierCASContract(None, cap())
    rotation = k.SyntheticRotation()
    with pytest.raises(c.CapabilityError): rotation.advance('separately_authorized_verifier_cas_confirmed')
    rotation = rotation.advance('pending_generated_locally')
    with pytest.raises(c.CapabilityError): rotation.advance('separately_authorized_verifier_cas_confirmed')
    for event in ('pending_persisted_locally', 'separately_authorized_verifier_cas_confirmed',
                  'pending_authenticated_and_locally_promoted', 'old_local_capability_retired'):
        rotation = rotation.advance(event)
    assert rotation.state == k.RotationState.PROMOTED and rotation.old_retired
    failed = k.SyntheticRotation().advance('failed_or_uncertain')
    with pytest.raises(c.CapabilityError): failed.advance('pending_generated_locally')


PLUGIN = Path('deploy/shopping/wordpress/plugins/ai-controlcenter-shopping-read/ai-controlcenter-shopping-read.php')


def test_plugin_source_contract():
    source = PLUGIN.read_text()
    for required in ("'methods' => 'GET'", "get_header_as_array('authorization')", 'count($headers) !== 1',
        "hash('sha256', $matches[1])", 'hash_equals($verifier, $matches[1])',
        "array_diff(array_keys($query), array('page', 'page_size'))", "'status' => 'publish'",
        "'orderby' => 'ID', 'order' => 'ASC'", "'has_password'] = false", "get_post_field('post_password'",
        "function_exists('wc_get_products')", 'aicc_shopping_read_integer($page, 10000)',
        'aicc_shopping_read_integer($page_size, 20)', "'/\\A.{0,200}/us'", "'Cache-Control' => 'no-store'"):
        assert required in source
    for prohibited in ('$wpdb', 'wc_get_orders(', 'get_users(', 'wp_remote_', 'update_option(', 'add_option(',
                       'error_log(', 'var_dump(', 'print_r(', 'register_setting(', 'get_meta('):
        assert prohibited not in source
    assert source.count('register_rest_route(') == 1


@pytest.mark.parametrize('kind', ['parent_mode', 'parent_replacement', 'leaf_replacement'])
def test_provider_rejects_changes_during_read(source, monkeypatch, kind):
    _, leaf = source
    real_read = os.read
    changed = False
    def racing_read(fd, count):
        nonlocal changed
        block = real_read(fd, count)
        if not changed:
            changed = True
            if kind == 'parent_mode':
                leaf.parent.chmod(0o750)
            elif kind == 'parent_replacement':
                leaf.parent.rename(leaf.parent.with_name('moved'))
                leaf.parent.mkdir(mode=0o700)
            else:
                leaf.rename(leaf.with_suffix('.moved'))
                leaf.write_bytes(p.KEY + b'=' + TOKEN.encode())
                leaf.chmod(0o600)
        return block
    monkeypatch.setattr(p.os, 'read', racing_read)
    with pytest.raises(c.CapabilityError) as error:
        load(source)
    assert error.value.__context__ is None


def test_provider_partial_reads(source, monkeypatch):
    real_read = os.read
    monkeypatch.setattr(p.os, 'read', lambda fd, count: real_read(fd, min(count, 3)))
    assert load(source)._request_ascii() == TOKEN


def test_provider_premature_eof(source, monkeypatch):
    monkeypatch.setattr(p.os, 'read', lambda fd, count: b'')
    with pytest.raises(c.CapabilityError):
        load(source)
