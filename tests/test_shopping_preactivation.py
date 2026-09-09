import inspect
import json
from types import SimpleNamespace

import pytest

from core.shopping.control_plane_read.preactivation import (
    EDGE_CHECKS, LOG_CHECKS, NAMESPACE, _evaluate,
)
from ops.macos.shopping import preactivation_observer as observer


def safe_facts():
    return dict(namespace=NAMESPACE, **{key: True for key, _ in EDGE_CHECKS + LOG_CHECKS})


def test_synthetic_safe_pass_is_not_live_authorization():
    result = _evaluate(safe_facts())
    assert result["status"] == "PASS"
    assert result["reason_codes"] == []
    for key in ("automatic_retry", "mutation_performed", "secret_values_exposed",
                "production_authority", "ubuntu_authority"):
        assert result[key] is False


@pytest.mark.parametrize("key,reason", EDGE_CHECKS + LOG_CHECKS)
@pytest.mark.parametrize("missing", [True, False])
def test_every_missing_or_negative_proof_blocks(key, reason, missing):
    facts = safe_facts()
    if missing:
        del facts[key]
    else:
        facts[key] = False
    result = _evaluate(facts)
    assert result["status"] == "BLOCKED"
    assert reason in result["reason_codes"]


@pytest.mark.parametrize("namespace", ["/wp-json/", NAMESPACE + "*", NAMESPACE[:-1], None])
def test_exact_namespace(namespace):
    assert _evaluate(dict(safe_facts(), namespace=namespace))["status"] == "BLOCKED"


def test_untrusted_values_never_project():
    facts = {key: "synthetic-sensitive-context" for key, _ in EDGE_CHECKS + LOG_CHECKS}
    facts.update(namespace="synthetic-sensitive-context", reason_codes=["synthetic-sensitive-context"])
    encoded = json.dumps(_evaluate(facts))
    assert "synthetic-sensitive-context" not in encoded
    assert len(encoded) < 3000
    assert _evaluate(dict(safe_facts(), repository_controls_verified=1))["status"] == "BLOCKED"


def install_metadata(monkeypatch, ip="127.0.0.1"):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        assert argv[:3] == [observer.DOCKER, "--host", observer._socket()]
        assert kwargs["stderr"] == observer.subprocess.DEVNULL
        assert kwargs["timeout"] == 5
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "HOME": "/var/empty",
                                 "DOCKER_CONFIG": "/var/empty/aicc-preactivation-no-config"}
        assert "Env" not in argv[5] and "LogConfig" not in argv[5]
        if argv[-1] == "ai-shopping-internal":
            return SimpleNamespace(returncode=0, stdout=b'{"internal":true,"name":"ai-shopping-internal","id":"synthetic-internal"}')
        networks = {"ai-shopping-internal": {"NetworkID": "synthetic-internal"}}
        if argv[-1] == "shopping-wordpress":
            networks["ai-shopping-network"] = {"NetworkID": "synthetic-external"}
        ports = {"80/tcp": [{"HostIp": ip, "HostPort": "58082"}]} if argv[-1] == "shopping-wordpress" else {"3306/tcp": None}
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(
            running=True, ports=ports, networks=networks, mode="ai-shopping-internal", project="ai-shopping")).encode())

    monkeypatch.setattr(observer, "_socket", lambda: "unix:///synthetic/commerce/docker.sock")
    monkeypatch.setattr(observer.sys, "platform", "darwin")
    monkeypatch.setattr(observer.subprocess, "run", run)
    return calls


@pytest.mark.parametrize("ip,expected", [("127.0.0.1", True), ("0.0.0.0", False), ("::1", False), ("localhost", False)])
def test_fixed_local_observation_cannot_infer_complete_safety(monkeypatch, ip, expected):
    calls = install_metadata(monkeypatch, ip)
    result = observer.observe()
    assert result["wordpress_loopback_only"] is expected
    assert result["mariadb_has_no_published_ports"] is True
    assert result["status"] == ("PASS" if expected else "BLOCKED")
    assert result["activation_status"] == "BLOCKED"
    assert not result["deployment_logging_safety_proven"]
    assert not result["public_edge_runtime_isolation_proven"]
    assert len(calls) == 3


def test_exception_context_suppressed_and_no_retry(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("synthetic-sensitive-context")

    monkeypatch.setattr(observer, "_socket", lambda: "unix:///synthetic/commerce/docker.sock")
    monkeypatch.setattr(observer.sys, "platform", "darwin")
    monkeypatch.setattr(observer.subprocess, "run", fail)
    result = observer.observe()
    assert result["status"] == "BLOCKED"
    assert len(calls) == 3
    assert "synthetic-sensitive-context" not in json.dumps(result)


def test_zero_override(monkeypatch, capsys):
    assert not inspect.signature(observer.observe).parameters
    monkeypatch.setattr(observer.sys, "argv", ["observer", "synthetic-sensitive-context"])
    monkeypatch.setattr(observer, "observe", lambda: pytest.fail("must reject before observation"))
    assert observer.main() == 2
    result = capsys.readouterr().out
    assert "synthetic-sensitive-context" not in result
    assert json.loads(result)["reason_codes"] == ["CALLER_OVERRIDE_REJECTED"]


def test_non_mac_never_runs_commands(monkeypatch):
    monkeypatch.setattr(observer.sys, "platform", "linux")
    monkeypatch.setattr(observer.subprocess, "run", lambda *a, **k: pytest.fail("not local Mac"))
    assert observer.observe()["status"] == "BLOCKED"


@pytest.mark.parametrize("payload", [b"not-json", b"[]", b"{}", b"x" * 8193])
def test_malformed_runtime_is_not_proof(monkeypatch, payload):
    monkeypatch.setattr(observer.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=payload))
    assert observer._metadata("shopping-wordpress") is None


def test_repository_controls_and_no_machine_identity():
    assert observer._repository_facts() is True
    for relative in ("ops/macos/shopping/preactivation_observer.py",
                     "core/shopping/control_plane_read/preactivation.py"):
        assert "/Users/" not in (observer.ROOT / relative).read_text()
    assert not (observer.ROOT / "ops/macos/shopping/shop_service_start_01f_evidence.json").exists()


def test_current_compose_review_preserves_historical_01g1c_contract():
    import hashlib
    from core.shopping import wordpress_generation_reconciliation as historical
    from core.shopping import wordpress_recovery_reconciliation as recovery

    relative = "deploy/shopping/compose.yaml"
    compose = (observer.ROOT / relative).read_bytes()
    policy = json.loads((observer.ROOT / "config/deployment/shopping-logging-policy.json").read_text())
    actual = hashlib.sha256(compose).hexdigest()
    assert actual == "0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c"
    assert policy["reviewed_repository_artifacts"][relative] == actual
    assert recovery.ARTIFACTS[relative] == "e90b116f9683d3ece0abc0111865ea41d9129a835070232e3a823c5c2e7e85ac"
    assert recovery.ARTIFACTS[relative] != actual
    assert historical.ARTIFACTS[relative] == "341c9dfcd69cb001bc9514d34427335a47b1b4dcad6d95cb40072752a1643f8b"
    assert historical.ARTIFACTS[relative] != actual
    assert b"./config/shopping-apache-safety.conf:/etc/apache2/sites-available/000-default.conf:ro" in compose
    assert b"/etc/apache2/sites-enabled/000-default.conf" not in compose


@pytest.mark.parametrize("field", observer.FALSE_POLICY_FIELDS)
def test_policy_rejects_capture_debug_and_authority(monkeypatch, tmp_path, field):
    path = tmp_path / "config/deployment/shopping-logging-policy.json"
    path.parent.mkdir(parents=True)
    policy = json.loads((observer.ROOT / "config/deployment/shopping-logging-policy.json").read_text())
    policy[field] = True
    path.write_text(json.dumps(policy))
    monkeypatch.setattr(observer, "ROOT", tmp_path)
    assert observer._repository_facts() is False


@pytest.mark.parametrize("artifact", sorted(observer.ARTIFACTS))
def test_missing_or_modified_artifact_blocks(monkeypatch, tmp_path, artifact):
    import shutil
    for relative in observer.ARTIFACTS | {"config/deployment/shopping-logging-policy.json"}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(observer.ROOT / relative, target)
    monkeypatch.setattr(observer, "ROOT", tmp_path)
    assert observer._repository_facts()
    target = tmp_path / artifact
    target.write_text(target.read_text() + "\nambiguous unreviewed configuration\n")
    assert not observer._repository_facts()
    target.unlink()
    assert not observer._repository_facts()


def test_caddy_ordered_private_rules():
    text = (observer.ROOT / "ops/macos/caddy/Caddyfile").read_text()
    assert 'path /wp-json/aicontrolcenter/v1/shopping /wp-json/aicontrolcenter/v1/shopping/*' in text
    route = text.split('    route {', 1)[1]
    assert route.count('reverse_proxy') == text.count('reverse_proxy') == 1
    for matcher in ('shopping_namespace', 'shopping_rest_route', 'shopping_rest_route_ambiguous'):
        assert route.index(f'respond @{matcher} "Forbidden" 403') < route.index('reverse_proxy')
    for forbidden in ('@query_present', '@encoded_uri', '@unsafe_method', '@shopping_alias', 'not method'):
        assert forbidden not in text
    assert text.count('output discard') == 2
    assert 'log_credentials' not in text


def test_active_upstreams_and_explicit_debug_controls():
    import yaml
    compose = yaml.safe_load((observer.ROOT / 'deploy/shopping/compose.yaml').read_text())
    wp = compose['services']['wordpress']
    assert wp['ports'] == ['127.0.0.1:58082:80']
    assert 'ports' not in compose['services']['database']
    assert wp['environment']['WORDPRESS_DEBUG'] == ''
    for constant in ('WP_DEBUG', 'WP_DEBUG_LOG', 'WP_DEBUG_DISPLAY'):
        assert f"define('{constant}', false);" in wp['environment']['WORDPRESS_CONFIG_EXTRA']
    assert '58081' not in (observer.ROOT / 'ops/macos/caddy/Caddyfile').read_text()
    ingress = json.loads((observer.ROOT / 'config/deployment/ingress.json').read_text())
    assert ingress['upstream']['port'] == 58082
    colima = json.loads((observer.ROOT / 'ops/macos/colima/commerce-runtime.json').read_text())
    assert colima['wordpress_host_binding'] == '127.0.0.1:58082:80'
    for name in ('shopping-apache-safety.conf', 'shopping-php-safety.ini'):
        assert any('./config/' + name + ':' in v and v.endswith(':ro') for v in wp['volumes'])
        assert {'path': 'deploy/shopping/config/' + name, 'writable': False} in colima['mounts']


def test_plugin_and_exception_projection_remain_value_free():
    import re
    plugin = next(p for p in observer.ARTIFACTS if p.endswith('.php'))
    text = (observer.ROOT / plugin).read_text()
    assert not re.search(r'\b(error_log|syslog|var_dump|print_r|trigger_error|wc_get_logger)\s*\(', text)
    assert 'catch (Throwable $ignored)' in text
    assert '$ignored->' not in text
    assert "new WP_Error('aicc_engine_unavailable', 'Shopping read unavailable.'" in text


@pytest.mark.parametrize('failure', ['project', 'running', 'host_port', 'network', 'internal', 'ambiguous'])
def test_bad_runtime_topology_blocks(monkeypatch, failure):
    install_metadata(monkeypatch)
    original = observer._read_metadata
    def read(target):
        value = original(target)
        if target == 'shopping-wordpress':
            if failure == 'project': value['project'] = 'other'
            if failure == 'running': value['running'] = False
            if failure == 'network': value['networks'] = {}
            if failure == 'ambiguous': value['unexpected'] = True
        if target == 'shopping-db' and failure == 'host_port':
            value['ports'] = {'3306/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '3306'}]}
        if target == 'ai-shopping-internal' and failure == 'internal': value['internal'] = False
        return value
    monkeypatch.setattr(observer, '_read_metadata', read)
    assert observer.observe()['status'] == 'BLOCKED'


def test_stale_port_even_with_updated_digest_rejected(monkeypatch, tmp_path):
    import hashlib
    import shutil
    for relative in observer.ARTIFACTS | {'config/deployment/shopping-logging-policy.json'}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(observer.ROOT / relative, target)
    relative = 'config/deployment/ingress.json'
    target = tmp_path / relative
    target.write_text(target.read_text().replace('58082', '58081'))
    policy_path = tmp_path / 'config/deployment/shopping-logging-policy.json'
    policy = json.loads(policy_path.read_text())
    policy['reviewed_repository_artifacts'][relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    policy_path.write_text(json.dumps(policy))
    monkeypatch.setattr(observer, 'ROOT', tmp_path)
    assert not observer._repository_facts()


@pytest.fixture(scope="module")
def adapted_caddy():
    from pathlib import Path
    import subprocess
    caddy = Path('/opt/homebrew/bin/caddy')
    if not caddy.exists():
        pytest.skip('local Caddy adapter unavailable; static assertions still run')
    result = subprocess.run([str(caddy), 'adapt', '--config', str(observer.ROOT / 'ops/macos/caddy/Caddyfile'),
                             '--adapter', 'caddyfile'], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=5, check=False)
    assert result.returncode == 0
    config = json.loads(result.stdout)
    return config


def test_caddy_adapter_preserves_deny_order_and_sinks(adapted_caddy):
    config = adapted_caddy
    handlers = []
    def walk(value):
        if isinstance(value, dict):
            if 'handler' in value: handlers.append(value)
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(config)
    proxy_index = next(i for i, v in enumerate(handlers) if v['handler'] == 'reverse_proxy')
    denied = [i for i, v in enumerate(handlers) if v['handler'] == 'static_response' and v.get('status_code') == 403]
    assert len(denied) == 3 and all(i < proxy_index for i in denied)
    assert handlers[proxy_index]['upstreams'] == [{'dial': '127.0.0.1:58082'}]
    assert all(v['writer']['output'] == 'discard' for v in config['logging']['logs'].values())


def test_logging_sink_configuration_has_no_header_projection():
    apache = (observer.ROOT / 'deploy/shopping/config/shopping-apache-safety.conf').read_text()
    assert 'CustomLog /dev/null common' in apache
    assert apache.count('ErrorLog /dev/null') == 2
    assert 'AllowOverride None' in apache
    assert '%{Authorization}' not in apache
    php = (observer.ROOT / 'deploy/shopping/config/shopping-php-safety.ini').read_text()
    for line in ('log_errors = Off', 'display_errors = Off', 'display_startup_errors = Off',
                 'zend.exception_ignore_args = On', 'error_log = /dev/null'):
        assert line in php


def test_duplicate_evidence_keys_rejected():
    with pytest.raises(ValueError):
        observer._json('{"internal":false,"internal":true}')


def test_trusted_home_resolver_ignores_environment(monkeypatch):
    monkeypatch.setenv('HOME', '/untrusted')
    monkeypatch.setenv('DOCKER_HOST', 'tcp://untrusted')
    monkeypatch.setattr(observer, 'resolve_trusted_mac_account_home',
                        lambda: SimpleNamespace(passwd_home='/trusted-account'))
    assert observer._socket() == 'unix:///trusted-account/.colima/aicontrolcenter-commerce/docker.sock'


def private_policy_routes(config):
    """Find the ordered route itself; fail on unexpected nesting or matchers."""
    found = []
    def walk(value):
        if isinstance(value, dict):
            routes = value.get('routes', [])
            if any(h.get('handler') == 'reverse_proxy'
                   for route in routes for h in route.get('handle', [])):
                found.append(routes)
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(config)
    assert len(found) == 1
    routes = found[0]
    assert len(routes) == 6
    assert [set(r['match'][0]) for r in routes[:5]] == [
        {'path'}, {'query'}, {'vars_regexp'}, {'path'}, {'path'}]
    assert all(len(r['match']) == 1 for r in routes[:5])
    assert all(len(r['handle']) == 1 for r in routes)
    assert 'match' not in routes[-1]
    return routes


def synthetic_edge_policy(config, method, uri):
    """Offline subset of documented Caddy semantics, not a runtime attestation.

    Path: one decode, case folding, slash merging and dot cleaning.
    Query: decoded keys and ANY repeated value; Go discards malformed pairs.
    The raw-query guard is evaluated separately using its adapted RE2-compatible
    regex. No method matcher is allowed in this policy. No HTTP is performed.
    """
    import posixpath
    import re
    from urllib.parse import parse_qs, unquote, urlsplit
    assert method
    parsed = urlsplit(uri)
    path = posixpath.normpath(re.sub('/+', '/', unquote(parsed.path).lower()))
    if parsed.path.endswith('/') and path != '/': path += '/'
    query = {}
    for pair in parsed.query.split('&'):
        if ';' in pair or re.search(r'%(?![0-9a-fA-F]{2})', pair): continue
        for key, values in parse_qs(pair, keep_blank_values=True).items():
            query.setdefault(key, []).extend(values)
    def pattern_matches(value, pattern):
        return value.startswith(pattern[:-1]) if pattern.endswith('*') else value == pattern
    for route in private_policy_routes(config):
        match = route.get('match', [{}])[0]
        if 'path' in match:
            matched = any(pattern_matches(path, p) for p in match['path'])
        elif 'query' in match:
            matched = all(any(pattern_matches(v, p) for v in query.get(k, []) for p in patterns)
                          for k, patterns in match['query'].items())
        elif 'vars_regexp' in match:
            assert set(match['vars_regexp']) == {'{http.request.uri.query}'}
            matched = re.search(match['vars_regexp']['{http.request.uri.query}']['pattern'], parsed.query) is not None
        else:
            assert match == {}
            matched = True
        if matched:
            handler = route['handle'][0]
            return handler.get('status_code', handler['handler'])
    pytest.fail('no terminal policy handler')


@pytest.mark.parametrize('method', ['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
@pytest.mark.parametrize('uri', [
    '/?s=shirt', '/shop/?orderby=price', '/product/example/?attribute_color=black',
    '/cart/', '/checkout/', '/?wc-ajax=add_to_cart', '/product/caf%C3%A9/',
    '/shop/?s=100%25+cotton', '/wp-json/wc/store/v1/cart',
    '/?rest_route=/wc/store/v1/cart', '/?rest_route=/wp/v2/posts&rest_route=/wc/store/v1/cart',
    '/?rest_route=/aicontrolcenter/v1/shopping-list',
    '/wp-json/aicontrolcenter/v1/shopping-list',
    '/?s=/aicontrolcenter/v1/shopping/products', '/about/aicontrolcenter/',
])
def test_storefront_remains_proxy_eligible(adapted_caddy, method, uri):
    assert synthetic_edge_policy(adapted_caddy, method, uri) == 'reverse_proxy'


@pytest.mark.parametrize('method', ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@pytest.mark.parametrize('uri', [
    '/wp-json/aicontrolcenter/v1/shopping', '/wp-json/aicontrolcenter/v1/shopping/',
    '/wp-json/aicontrolcenter/v1/shopping/products',
    '/WP-JSON/AICONTROLCENTER/v1/SHOPPING/products',
    '/wp-json%2faicontrolcenter/v1/%73hopping/products',
    '/wp-json//aicontrolcenter/v1/other/../shopping/products',
    '/?rest_route=/aicontrolcenter/v1/shopping',
    '/?rest_route=/aicontrolcenter/v1/shopping/products',
    '/?rest_route=/wp/v2/posts&rest_route=/aicontrolcenter/v1/shopping/products',
    '/?rest_route=/aicontrolcenter/v1/shopping/products&rest_route=/wp/v2/posts',
    '/?r%65st_route=%2Faicontrolcenter%2Fv1%2Fshopping%2Fproducts',
    '/?rest_route=/AICONTROLCENTER/v1/SHOPPING/products',
    '/?rest_route=aicontrolcenter/v1/shopping/products',
    '/?rest.route=/aicontrolcenter/v1/shopping/products',
    '/?rest+route=/aicontrolcenter/v1/shopping/products',
    '/?rest_route=/aicontrolcenter/v1/shopping/products;unused=1',
    '/?rest_route=/aicontrolcenter/v1/shopping/products&bad=%zz',
    '/?rest_route=/aicontrolcenter/v1/shopping/products%zz',
])
def test_private_routes_explicitly_denied(adapted_caddy, method, uri):
    assert synthetic_edge_policy(adapted_caddy, method, uri) == 403


def test_encoded_private_query_spellings(adapted_caddy):
    # Vary each key/value character independently and fully encode both, including
    # nested escapes. These are namespace-only conservative denial cases.
    key, value = 'rest_route', '/aicontrolcenter/v1/shopping/products'
    for depth in (1, 2, 3):
        def encode(char): return '%' + '25' * (depth - 1) + format(ord(char), '02X')
        cases = [(''.join(map(encode, key)), ''.join(map(encode, value)))]
        cases += [(key[:i] + encode(c) + key[i+1:], value) for i, c in enumerate(key)]
        cases += [(key, value[:i] + encode(c) + value[i+1:]) for i, c in enumerate(value)]
        for k, v in cases:
            assert synthetic_edge_policy(adapted_caddy, 'POST', '/?' + k + '=' + v) == 403


def test_registered_product_route_is_covered(adapted_caddy):
    plugin = next(p for p in observer.ARTIFACTS if p.endswith('.php'))
    source = (observer.ROOT / plugin).read_text()
    assert "register_rest_route('aicontrolcenter/v1', '/shopping/products'" in source
    assert synthetic_edge_policy(adapted_caddy, 'GET', '/wp-json/aicontrolcenter/v1/shopping/products') == 403
    assert synthetic_edge_policy(adapted_caddy, 'GET', '/?rest_route=/aicontrolcenter/v1/shopping/products') == 403


def test_private_query_guard_has_reviewable_construction(adapted_caddy):
    """Keep the expanded Caddy regex reproducible from a small namespace grammar."""
    import re
    def spelling(word):
        parts = []
        for char in word:
            codes = sorted({format(ord(c), '02x') for c in (char.lower(), char.upper())})
            parts.append('(?:' + re.escape(char) + '|%(?:25)*(?:' + '|'.join(codes) + '))')
        return ''.join(parts)
    slash = '(?:/|%(?:25)*2f)'
    key = spelling('rest') + '(?:_|[.+]|%(?:25)*(?:5f|20|2e))' + spelling('route')
    namespace = slash.join(map(spelling, ('aicontrolcenter', 'v1', 'shopping')))
    expected = '(?i)(^|[&;])' + key + '=' + slash + '*' + namespace + '(' + slash + '|[&;]|$)'
    routes = private_policy_routes(adapted_caddy)
    assert routes[1]['match'] == [{'query': {'rest_route': [
        '/aicontrolcenter/v1/shopping', '/aicontrolcenter/v1/shopping/*']}}]
    guard = routes[2]['match'][0]['vars_regexp']['{http.request.uri.query}']
    assert guard['pattern'] == expected
