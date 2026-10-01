"""Phase A security regressions and B1 repository-adapter integration."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, FrozenInstanceError
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import pytest

from core.deployment.adapters.macos.caddy_sites import (
    CaddySitePolicyError, classify_caddy_sites, load_site_policy,
)
from core.deployment.adapters.macos.ingress import CaddyIngressAdapter
from core.deployment.adapters.macos.repository import CaddyFileAdapter
from core.deployment.contracts import load_schema_registry, validate_contract_payload
from tests.support.caddy_site_fixtures import (
    AUTH, AUTH_VALUE, CADDY_PATH, CaddyFixtureFiles, GLOBALS, GUARDED, INGRESS,
    INGRESS_PATH, POLICY_PATH, POLICY_TEXT, PREVIEW, PRODUCTION, PRODUCTION_SITE,
    PROXY, UNGUARDED,
)


def classify(text, policy=None, ingress=None):
    return classify_caddy_sites(
        text, policy=load_site_policy(POLICY_TEXT) if policy is None else policy,
        ingress_contract=deepcopy(INGRESS) if ingress is None else ingress,
    )


def reject(text, code=None):
    # A failed expectation must not echo Caddy source or authentication fields.
    try:
        classify(text)
    except CaddySitePolicyError as error:
        if code is not None:
            assert error.code == code
        assert AUTH_VALUE not in str(error)
        return error
    pytest.fail("Unsafe desired-state fixture was accepted")


def test_production_only_compatibility():
    result = classify(PRODUCTION)
    assert asdict(result.production) == {
        "role": "production", "hostname": "bokstory.duckdns.org",
        "host": "127.0.0.1", "port": 58082, "authentication_required": False,
    }
    assert result.preview is None


@pytest.mark.parametrize("variant", ["normal", "reordered-sites", "crlf-comments"])
def test_fully_guarded_preview_classification(variant):
    text = GUARDED
    if variant == "reordered-sites":
        text = GLOBALS + PREVIEW + "\n" + PRODUCTION_SITE
    if variant == "crlf-comments":
        text = ("# fixture-only configuration\n\n" + text).replace("\n", "\r\n")
    result = classify(text)
    assert result.production.port == 58082
    assert asdict(result.preview) == {
        "role": "preview", "hostname": "dev.bokstory.duckdns.org",
        "host": "127.0.0.1", "port": 18080, "authentication_required": True,
    }
    assert set(asdict(result)) == {"production", "preview"}
    assert AUTH_VALUE not in repr(result)
    with pytest.raises(FrozenInstanceError):
        result.production.port = 18080


def test_policy_registry_and_input_immutability():
    policy, ingress = load_site_policy(POLICY_TEXT), deepcopy(INGRESS)
    before = deepcopy((policy, ingress))
    validate_contract_payload(registry=load_schema_registry(), contract_name="CaddySitePolicy", payload=policy)
    assert classify(GUARDED, policy, ingress) == classify(GUARDED, policy, ingress)
    assert (policy, ingress) == before


@pytest.mark.parametrize("case", [
    "missing-production", "preview-only", "duplicate-production", "duplicate-preview",
    "unknown-site", "wildcard", "fallback", "host-alias", "http-site", "second-global",
])
def test_missing_duplicate_unknown_and_fallback_sites_rejected(case):
    texts = {
        "missing-production": GLOBALS,
        "preview-only": GLOBALS + PREVIEW,
        "duplicate-production": PRODUCTION + PRODUCTION_SITE,
        "duplicate-preview": GUARDED + PREVIEW,
        "unknown-site": GUARDED + PREVIEW.replace("dev.bokstory.duckdns.org", "unknown.example.test"),
        "wildcard": GUARDED.replace("dev.bokstory.duckdns.org", "*.bokstory.duckdns.org"),
        "fallback": GUARDED.replace("dev.bokstory.duckdns.org", ":58443"),
        "host-alias": GUARDED.replace("dev.bokstory.duckdns.org", "dev.bokstory.duckdns.org, other.example.test"),
        "http-site": GUARDED.replace("dev.bokstory.duckdns.org", "http://dev.bokstory.duckdns.org"),
        "second-global": GUARDED + GLOBALS,
    }
    reject(texts[case])


@pytest.mark.parametrize("role", ["production", "preview"])
@pytest.mark.parametrize("target", [
    "127.0.0.1:58081", "127.0.0.1:0", "127.0.0.1:65536", "0.0.0.0:58082",
    "192.0.2.1:58082", "commerce.example.test:58082", "localhost:58082", "[::1]:58082",
    "127.0.0.1:58082 127.0.0.1:18080", "{http.request.host}:58082", "{$UPSTREAM}",
])
def test_unapproved_and_hidden_proxy_targets_rejected(role, target):
    old = "127.0.0.1:58082" if role == "production" else "127.0.0.1:18080"
    reject(GUARDED.replace("reverse_proxy " + old, "reverse_proxy " + target))


@pytest.mark.parametrize("case", [
    "duplicate-proxy", "proxy-block", "nested-handle", "named-matcher-proxy", "role-swap",
])
def test_alternate_proxy_routes_rejected(case):
    replacements = {
        "duplicate-proxy": PROXY + PROXY,
        "proxy-block": PROXY.rstrip() + " {\n            to 127.0.0.1:18081\n        }\n",
        "nested-handle": "        handle {\n" + PROXY + "        }\n",
        "named-matcher-proxy": PROXY.replace("reverse_proxy ", "reverse_proxy @public "),
        "role-swap": PROXY.replace(":18080", ":58082"),
    }
    reject(GUARDED.replace(PROXY, replacements[case]))


@pytest.mark.parametrize("role", ["production", "preview"])
@pytest.mark.parametrize("case", ["missing", "duplicate"])
def test_each_site_has_exactly_one_upstream(role, case):
    proxy = "        reverse_proxy 127.0.0.1:" + ("58082" if role == "production" else "18080") + "\n"
    reject(GUARDED.replace(proxy, "" if case == "missing" else proxy * 2))


@pytest.mark.parametrize("case", [
    "missing", "empty", "missing-password", "plaintext", "duplicate-user", "bad-hash",
    "path-limited", "matcher-limited", "after-proxy", "top-level", "early-response",
    "auth-subroute", "credential-placeholder", "unsupported-algorithm",
])
def test_preview_authentication_cannot_be_missing_partial_or_bypassed(case):
    replacement = {
        "missing": "",
        "empty": "        basic_auth {\n        }\n",
        "missing-password": "        basic_auth {\n            fixture_user\n        }\n",
        "plaintext": AUTH.replace(AUTH_VALUE, "synthetic-plaintext"),
        "duplicate-user": AUTH.replace("            fixture_user " + AUTH_VALUE + "\n", ("            fixture_user " + AUTH_VALUE + "\n") * 2),
        "bad-hash": AUTH.replace(AUTH_VALUE, "$2a$12$invalid"),
        "path-limited": AUTH.replace("basic_auth bcrypt", "basic_auth /private/* bcrypt"),
        "matcher-limited": AUTH.replace("basic_auth bcrypt", "basic_auth @restricted bcrypt"),
        "after-proxy": "",
        "top-level": "",
        "early-response": '        respond "ok" 200\n' + AUTH,
        "auth-subroute": "        route {\n" + AUTH + "        }\n",
        "credential-placeholder": AUTH.replace(AUTH_VALUE, "{$AUTH_VALUE}"),
        "unsupported-algorithm": AUTH.replace("bcrypt", "unsupported"),
    }[case]
    text = GUARDED.replace(AUTH, replacement)
    if case == "after-proxy":
        text = text.replace(PROXY, PROXY + AUTH)
    if case == "top-level":
        text = text.replace("dev.bokstory.duckdns.org {\n", "dev.bokstory.duckdns.org {\n" + AUTH)
    reject(text)


@pytest.mark.parametrize("role", ["production", "preview"])
@pytest.mark.parametrize("matcher", ["shopping_namespace", "shopping_rest_route", "shopping_rest_route_ambiguous"])
@pytest.mark.parametrize("case", ["missing-matcher", "missing-deny", "late-deny", "weakened-deny"])
def test_every_private_guard_is_required_and_ordered(role, matcher, case):
    site = PRODUCTION_SITE if role == "production" else PREVIEW
    deny = f'        respond @{matcher} "Forbidden" 403\n'
    if case == "missing-matcher":
        site = "\n".join(line for line in site.split("\n") if not line.lstrip().startswith("@" + matcher + " "))
    if case == "missing-deny":
        site = site.replace(deny, "")
    if case == "late-deny":
        site = site.replace(deny, "").replace("    }\n}\n", deny + "    }\n}\n")
    if case == "weakened-deny":
        site = site.replace(deny, deny.replace("403", "200"))
    reject(GLOBALS + (site + PREVIEW if role == "production" else PRODUCTION_SITE + site))


@pytest.mark.parametrize("case", ["path-subset", "query-subset", "regex-weakened", "route-matcher", "method-guard", "extra-route"])
def test_private_guard_bypasses_rejected(case):
    text = GUARDED
    if case == "path-subset":
        text = text.replace("path /wp-json/aicontrolcenter/v1/shopping ", "path ")
    if case == "query-subset":
        text = text.replace("query rest_route=/aicontrolcenter/v1/shopping ", "query ")
    if case == "regex-weakened":
        text = re.sub(r"vars_regexp .*", 'vars_regexp {http.request.uri.query} `.*`', text)
    if case == "route-matcher":
        text = text.replace("    route {", "    route /only-this-path {")
    if case == "method-guard":
        text = text.replace("@shopping_namespace path", "@shopping_namespace method GET path")
    if case == "extra-route":
        text = text.replace(PROXY, PROXY + "        handle /bypass {\n            respond ok 200\n        }\n")
    reject(text)


@pytest.mark.parametrize("case", [
    "import", "snippet", "inline-block", "quoted-brace", "unclosed-block", "unclosed-quote",
    "extra-close", "continuation", "inline-comment", "nul", "unicode", "bare-cr", "oversized",
])
def test_unsupported_or_ambiguous_syntax_rejected(case):
    text = {
        "import": PRODUCTION + "import external.caddy\n",
        "snippet": PRODUCTION + "(hidden) {\n reverse_proxy 127.0.0.1:18080\n}\n",
        "inline-block": PRODUCTION.replace("log {\n        output discard\n    }", "log { output discard }"),
        "quoted-brace": PRODUCTION.replace("{", '"{"', 1),
        "unclosed-block": PRODUCTION.rsplit("}", 1)[0],
        "unclosed-quote": PRODUCTION.replace('"Forbidden"', '"Forbidden'),
        "extra-close": PRODUCTION + "}\n",
        "continuation": PRODUCTION.replace("reverse_proxy ", "reverse_proxy \\\n"),
        "inline-comment": PRODUCTION.replace("reverse_proxy 127.0.0.1:58082", "reverse_proxy 127.0.0.1:58082 # ignored?"),
        "nul": PRODUCTION + "\x00",
        "unicode": PRODUCTION.replace("reverse_proxy", "reverse_prоxy"),
        "bare-cr": PRODUCTION.replace("\n", "\r", 1),
        "oversized": PRODUCTION + "#" * 32769,
    }[case]
    reject(text)


@pytest.mark.parametrize("case", ["file-sink", "stdout-sink", "credential-log", "log-format", "authorization-header", "header-up", "extra-global", "extra-listener"])
def test_unsafe_logging_and_credential_projection_rejected(case):
    replacements = {
        "file-sink": ("output discard", "output file /tmp/unsafe.log"),
        "stdout-sink": ("output discard", "output stdout"),
        "credential-log": ("output discard", "output discard\n        log_credentials"),
        "log-format": ("output discard", "output discard\n        format json"),
        "authorization-header": ("        -Server", "        Authorization {http.request.header.Authorization}\n        -Server"),
        "header-up": (PROXY, PROXY.rstrip() + " {\n            header_up Authorization synthetic\n        }\n"),
        "extra-global": ("    http_port 58080", "    debug\n    http_port 58080"),
        "extra-listener": ("    http_port 58080", "    http_port 58080\n    https_port 443"),
    }
    old, new = replacements[case]
    reject(GUARDED.replace(old, new))


@pytest.mark.parametrize("role", ["production", "preview"])
@pytest.mark.parametrize("case", ["sink", "credential-log", "header-projection"])
def test_site_safety_is_checked_independently_of_safe_global_logging(role, case):
    site = PRODUCTION_SITE if role == "production" else PREVIEW
    if case == "sink":
        site = site.replace("output discard", "output stdout")
    if case == "credential-log":
        site = site.replace("output discard", "output discard\n        log_credentials")
    if case == "header-projection":
        site = site.replace("        -Server", "        X-Leaked-Authorization {http.request.header.Authorization}\n        -Server")
    reject(GLOBALS + (site + PREVIEW if role == "production" else PRODUCTION_SITE + site))


@pytest.mark.parametrize("field,value", [
    ("policy_version", "dev-ingress/v2"), ("activation_allowed", True),
    ("logging", "file"), ("private_route_boundary", "application-only"),
    ("unexpected", True), ("password", "synthetic-must-not-escape"),
])
def test_invalid_policy_cannot_authorize_sites(field, value):
    policy = json.loads(POLICY_TEXT)
    policy[field] = value
    with pytest.raises(CaddySitePolicyError, match="^INVALID_SITE_POLICY$"):
        classify(GUARDED, policy)


@pytest.mark.parametrize("case", ["duplicate-key", "invalid-json", "float-port", "changed-preview", "shared-identity", "public-target"])
def test_policy_loading_rejects_ambiguous_and_changed_identities(case):
    policy = json.loads(POLICY_TEXT)
    text = POLICY_TEXT
    if case == "duplicate-key":
        text = text.replace('"activation_allowed": false', '"activation_allowed": false, "activation_allowed": false')
    if case == "invalid-json":
        text = '{"password":"synthetic-invalid-json"'
    if case == "float-port":
        policy["production"]["upstream"]["port"] = 58082.0
    if case == "changed-preview":
        policy["preview"]["upstream"]["port"] = 18081
    if case == "shared-identity":
        policy["preview"]["hostname"] = policy["production"]["hostname"]
    if case == "public-target":
        policy["preview"]["upstream"]["host"] = "0.0.0.0"
    if case not in {"duplicate-key", "invalid-json"}:
        text = json.dumps(policy)
    with pytest.raises(CaddySitePolicyError, match="^INVALID_SITE_POLICY$"):
        load_site_policy(text)


def test_production_contract_is_not_replaced_by_site_policy():
    ingress = deepcopy(INGRESS)
    ingress["upstream"]["port"] = 18080
    with pytest.raises(CaddySitePolicyError, match="^PRODUCTION_CONTRACT_MISMATCH$"):
        classify(GUARDED, ingress=ingress)


def test_unguarded_authenticated_dev_is_rejected(capsys):
    error = reject(UNGUARDED, "PRIVATE_GUARDS_REQUIRED")
    assert str(error) == "PRIVATE_GUARDS_REQUIRED"
    assert capsys.readouterr() == ("", "")


def test_ingress_adapter_still_rejects_unguarded_preview():
    with pytest.raises(CaddySitePolicyError, match="^PRIVATE_GUARDS_REQUIRED$"):
        CaddyIngressAdapter(CaddyFixtureFiles(UNGUARDED), CADDY_PATH).observe()


def adapter_observation(adapter, files, path=CADDY_PATH):
    instance = adapter(files, path)
    return (instance.observe() if adapter is CaddyIngressAdapter
            else instance.observe_caddy_desired_state())


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
@pytest.mark.parametrize("with_preview", [False, True], ids=["production-only", "guarded-preview"])
def test_adapters_report_explicit_roles_without_readiness_authority(adapter, with_preview):
    files = CaddyFixtureFiles(GUARDED if with_preview else PRODUCTION)
    result = adapter_observation(adapter, files)
    assert result["sites"]["production"] == {
        "role": "production", "hostname": "bokstory.duckdns.org",
        "host": "127.0.0.1", "port": 58082, "authentication_required": False,
    }
    assert result["canonical_production_upstream"] == "127.0.0.1:58082"
    assert result["upstreams"] == (["127.0.0.1:18080", "127.0.0.1:58082"] if with_preview
                                   else ["127.0.0.1:58082"])
    if with_preview:
        assert result["sites"]["preview"] == {
            "role": "preview", "hostname": "dev.bokstory.duckdns.org",
            "host": "127.0.0.1", "port": 18080, "authentication_required": True,
        }
    else:
        assert result["sites"]["preview"] is None
    assert result["evidence_scope"] == "repository-desired-state"
    assert result["site_policy_version"] == "public-storefront-migration/v2"
    for name in ("live_network_test_performed", "readiness_granted", "activation_authorized", "effective_runtime_attested"):
        assert result[name] is False
    assert "status" not in result and "overall_status" not in result
    assert {e["reference"] for e in result["evidence"]} == {CADDY_PATH, POLICY_PATH, INGRESS_PATH}
    assert set(files.reads) == {CADDY_PATH, POLICY_PATH, INGRESS_PATH}
    if adapter is CaddyIngressAdapter:
        assert (result["host"], result["port"], result["endpoint"]) == ("127.0.0.1", 58082, "127.0.0.1:58082")
    rendered = json.dumps(result)
    assert AUTH_VALUE not in rendered and "fixture_user" not in rendered and "basic_auth" not in rendered


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
@pytest.mark.parametrize("case", ["unguarded", "unknown", "duplicate", "extra-target", "public-target", "late-auth", "unsafe-log"])
def test_adapters_do_not_authorize_an_extra_upstream_by_loopback_alone(adapter, case):
    text = {
        "unguarded": UNGUARDED,
        "unknown": GUARDED + PREVIEW.replace("dev.bokstory.duckdns.org", "unknown.example.test"),
        "duplicate": GUARDED + PRODUCTION_SITE,
        "extra-target": GUARDED.replace(PROXY, PROXY.rstrip() + " 127.0.0.1:18081\n"),
        "public-target": GUARDED.replace("127.0.0.1:18080", "192.0.2.1:18080"),
        "late-auth": GUARDED.replace(AUTH + PROXY, PROXY + AUTH),
        "unsafe-log": GUARDED.replace("output discard", "output stdout"),
    }[case]
    with pytest.raises(CaddySitePolicyError) as caught:
        adapter_observation(adapter, CaddyFixtureFiles(text))
    assert AUTH_VALUE not in str(caught.value) and "fixture_user" not in str(caught.value)


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
@pytest.mark.parametrize("path", [CADDY_PATH, POLICY_PATH, INGRESS_PATH])
def test_adapter_read_failures_are_value_free(adapter, path):
    files = CaddyFixtureFiles(overrides={path: OSError("synthetic-private-read-error")})
    with pytest.raises(CaddySitePolicyError, match="^CADDY_EVIDENCE_UNAVAILABLE$") as caught:
        adapter_observation(adapter, files)
    assert "synthetic-private-read-error" not in str(caught.value)
    assert caught.value.__suppress_context__ is True


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
@pytest.mark.parametrize("case", ["invalid-policy", "missing-policy-key", "duplicate-policy-key", "invalid-contract", "duplicate-contract-key", "contract-mismatch"])
def test_adapters_fail_closed_on_invalid_or_ambiguous_policy_inputs(adapter, case):
    overrides = {}
    if case == "invalid-policy":
        overrides[POLICY_PATH] = '{"sensitive":"synthetic-private-value"'
    if case == "missing-policy-key":
        policy = json.loads(POLICY_TEXT)
        del policy["preview"]
        overrides[POLICY_PATH] = json.dumps(policy)
    if case == "duplicate-policy-key":
        overrides[POLICY_PATH] = POLICY_TEXT.replace('"activation_allowed": false', '"activation_allowed": false, "activation_allowed": false')
    if case == "invalid-contract":
        overrides[INGRESS_PATH] = '{"sensitive":"synthetic-private-value"'
    if case == "duplicate-contract-key":
        overrides[INGRESS_PATH] = json.dumps(INGRESS).replace('"port": 58082', '"port": 18080, "port": 58082')
    if case == "contract-mismatch":
        ingress = deepcopy(INGRESS)
        ingress["upstream"]["port"] = 18080
        overrides[INGRESS_PATH] = json.dumps(ingress)
    with pytest.raises(CaddySitePolicyError) as caught:
        adapter_observation(adapter, CaddyFixtureFiles(overrides=overrides))
    assert "synthetic-private-value" not in str(caught.value)


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
def test_adapters_bind_the_policy_entrypoint(adapter):
    with pytest.raises(CaddySitePolicyError, match="^CADDY_ENTRYPOINT_MISMATCH$"):
        adapter_observation(adapter, CaddyFixtureFiles(), "other.Caddyfile")


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
def test_adapters_reread_and_do_not_cache_a_previously_safe_result(adapter):
    files = CaddyFixtureFiles(GUARDED)
    instance = adapter(files, CADDY_PATH)
    observe = instance.observe if adapter is CaddyIngressAdapter else instance.observe_caddy_desired_state
    first = observe()
    first["sites"]["production"]["port"] = 18080
    assert observe()["sites"]["production"]["port"] == 58082
    files.overrides[CADDY_PATH] = UNGUARDED
    with pytest.raises(CaddySitePolicyError, match="^PRIVATE_GUARDS_REQUIRED$"):
        observe()


@pytest.mark.parametrize("adapter", [CaddyIngressAdapter, CaddyFileAdapter])
def test_both_adapters_obey_the_same_classifier_rejection(monkeypatch, adapter):
    from core.deployment.adapters.macos import caddy_sites
    def denied(*args, **kwargs):
        raise CaddySitePolicyError("PRIVATE_GUARDS_REQUIRED")
    monkeypatch.setattr(caddy_sites, "classify_caddy_sites", denied)
    with pytest.raises(CaddySitePolicyError, match="^PRIVATE_GUARDS_REQUIRED$"):
        adapter_observation(adapter, CaddyFixtureFiles(GUARDED))


@pytest.mark.parametrize("with_preview", [False, True], ids=["production-only", "guarded-preview"])
def test_accepted_fixtures_have_expected_offline_caddy_semantics(with_preview):
    """Independent Caddy adaptation validates our accepted subset, never runtime."""
    caddy = Path("/opt/homebrew/bin/caddy")
    if not caddy.is_file():
        pytest.skip("Offline Caddy binary unavailable")
    text = GUARDED if with_preview else PRODUCTION
    classify(text)
    # Use the canonical harness's isolated root, without visiting pytest's stale
    # machine-wide temporary directories. Only this test-owned file is adapted.
    with tempfile.TemporaryDirectory(dir=os.environ.get("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT")) as directory:
        path = Path(directory) / "fixture.Caddyfile"
        path.write_text(text)
        result = subprocess.run(
            [str(caddy), "adapt", "--config", str(path), "--adapter", "caddyfile"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={"PATH": "/usr/bin:/bin", "HOME": "/var/empty"}, timeout=5, check=False,
        )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    assert all(log["writer"]["output"] == "discard" for log in config["logging"]["logs"].values())
    routes = config["apps"]["http"]["servers"]["srv0"]["routes"]
    assert len(routes) == (2 if with_preview else 1)
    def handlers(value):
        found = []
        if isinstance(value, dict):
            if "handler" in value:
                found.append(value)
            for child in value.values():
                found.extend(handlers(child))
        elif isinstance(value, list):
            for child in value:
                found.extend(handlers(child))
        return found
    for route in routes:
        host = route["match"][0]["host"]
        preview = host == ["dev.bokstory.duckdns.org"]
        assert host in (["bokstory.duckdns.org"], ["dev.bokstory.duckdns.org"])
        chain = handlers(route)
        proxy_indices = [i for i, node in enumerate(chain) if node["handler"] == "reverse_proxy"]
        assert len(proxy_indices) == (1 if preview else 2)
        if preview:
            proxy = proxy_indices[0]
            assert chain[proxy]["upstreams"] == [{"dial": "127.0.0.1:18080"}]
        else:
            assert {chain[index]["upstreams"][0]["dial"] for index in proxy_indices} == {"127.0.0.1:58081", "127.0.0.1:58082"}
            proxy = max(proxy_indices)
        denies = [i for i, node in enumerate(chain) if node["handler"] == "static_response" and node.get("status_code") == 403]
        if preview:
            assert len(denies) == 3 and max(denies) < proxy
        auth = [i for i, node in enumerate(chain) if node["handler"] == "authentication"]
        if preview:
            assert len(auth) == 1 and max(denies) < auth[0] < proxy
        else:
            assert not auth
