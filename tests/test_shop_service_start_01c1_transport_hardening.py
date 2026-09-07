"""Offline wire-boundary regressions; no runtime or credential access."""
import json
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
import requests

from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter
from core.shopping.adapters.woocommerce_read_transport import WooCommerceReadTransportSession
from core.shopping.secure_runtime import WooCommerceReadSecret
from tests.test_shop_service_start_01b_authenticated_woocommerce_read_validator import (
    boundary, repository_facts, KEY, SECRET,
)
from ops.macos.shopping import woocommerce_authenticated_read_validator as validator


@pytest.mark.parametrize('status,payload,total,reason', [
    (200, [{'id': 1}], '1', 'READY'), (200, [], '0', 'READY'),
    (401, {}, '0', 'AUTHENTICATION_REJECTED'),
    (403, {}, '0', 'AUTHENTICATION_REJECTED'),
    (503, {}, '0', 'API_UNAVAILABLE'), (302, {}, '0', 'API_UNAVAILABLE'),
    (200, {}, '0', 'MALFORMED_EVIDENCE'),
    (200, [], 'bad', 'MALFORMED_EVIDENCE'),
    ('timeout', {}, '0', 'API_UNAVAILABLE'),
])
def test_prepared_wire_and_diagnostics(boundary, monkeypatch, capsys, status, payload, total, reason):
    calls = []
    retained = []
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        monkeypatch.setenv(name, 'http://outside.invalid:9999')
    monkeypatch.setenv('NO_PROXY', '')

    def send(session, request, **kwargs):
        calls.append(request.url)
        assert session.trust_env is False
        assert kwargs['proxies'] == {}
        assert kwargs['allow_redirects'] is False
        assert kwargs['timeout'] == (5.0, 15.0)
        assert request.method == 'GET'
        assert request.url.startswith('http://127.0.0.1:58082/wp-json/wc/v3/products?')
        assert request.headers['Host'] == 'catalog.invalid'
        header = request.headers['Authorization']
        assert header.startswith('OAuth ')
        oauth = dict((k, unquote(v.strip('"'))) for k, v in
                     (part.split('=', 1) for part in header[6:].split(', ')))
        assert oauth['oauth_consumer_key'] == KEY
        assert oauth['oauth_signature_method'] == 'HMAC-SHA256'
        assert SECRET not in header
        query = parse_qs(urlsplit(request.url).query)
        assert set(query) == {'context', 'status', 'page', 'per_page'}
        assert all(value not in request.url for value in (KEY, SECRET, oauth['oauth_signature']))
        retained.append(request)
        if status == 'timeout':
            raise requests.Timeout(KEY + SECRET + header, request=request)
        response = requests.Response()
        response.status_code = status
        response.request = request
        response._content = json.dumps(payload).encode()
        response._content_consumed = True
        response.headers['X-WP-Total'] = total
        return response

    monkeypatch.setattr(requests.Session, 'send', send)
    monkeypatch.setattr(validator.sys, 'argv', ['validator'])
    validator.main()
    output = capsys.readouterr()
    evidence = json.loads(output.out)
    assert reason in evidence['reason_codes']
    assert len(calls) == 1
    assert output.err == ''
    secret = WooCommerceReadSecret('https://catalog.invalid', KEY, SECRET, 'READ_ONLY')
    diagnostic = output.out + output.err + repr(secret) + str(secret)
    for request in retained:
        diagnostic += repr(vars(request)) + str(request)
        assert 'Authorization' not in request.headers
    assert all(value not in diagnostic for value in (KEY, SECRET, 'oauth_signature'))


def test_transport_exception_has_no_raw_context(monkeypatch):
    def get(*args, **kwargs):
        raise requests.Timeout(KEY + SECRET)
    monkeypatch.setattr(requests.Session, 'get', get)
    transport = WooCommerceReadTransportSession()
    with pytest.raises(requests.Timeout) as caught:
        transport.get('http://127.0.0.1:58082')
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert KEY not in repr(caught.value) + str(caught.value)


@pytest.mark.parametrize('base', ['http://user:pass@host', 'http://host?consumer_key=key', 'http://host#secret', 'http://host\n'])
def test_unsafe_identity_rejected(base):
    with pytest.raises(RuntimeError, match='Invalid WooCommerce identity'):
        WooCommerceRESTAdapter(base, KEY, SECRET)
