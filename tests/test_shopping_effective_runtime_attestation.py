"""Synthetic only: no runtime commands, WordPress bootstrap or bearer secrets."""
import copy
import inspect
import json
from pathlib import Path
import sys
import time

import pytest

from core.shopping.control_plane_read.effective_runtime import CHECKS, FALSE_FIELDS, reduce_evidence
from ops.macos.shopping import effective_runtime_attestor as attestor


from tests.test_shopping_runtime_components import reviewed_fixture


def reduce_evidence(facts, errors=()):
    from core.shopping.control_plane_read.effective_runtime import reduce_evidence as reduce
    manifest, observed = reviewed_fixture()
    return reduce(facts, errors, manifest=manifest, observed_components=observed)


def complete():
    return {group: dict.fromkeys(keys, True) for group, keys in CHECKS.items()}


def test_complete_synthetic_evidence_passes_without_authority():
    result = reduce_evidence(complete())
    assert result["status"] == "PASS"
    assert result["activation_status"] == "BLOCKED"
    assert result["reason_codes"] == []
    assert result["public_edge_runtime_isolation_proven"]
    assert result["deployment_logging_safety_proven"]
    assert all(result[key] is False for key in FALSE_FIELDS)


@pytest.mark.parametrize("group,key", [(g, k) for g, keys in CHECKS.items() for k in keys])
@pytest.mark.parametrize("value", [None, False, 1, "secret-looking-value"])
def test_every_missing_unsafe_or_ambiguous_control_blocks(group, key, value):
    facts = complete()
    if value is None:
        del facts[group][key]
    else:
        facts[group][key] = value
    result = reduce_evidence(facts)
    assert result["status"] == "BLOCKED"
    assert group.upper() + "_" + key.upper() in result["reason_codes"]
    assert "secret-looking-value" not in json.dumps(result)


@pytest.mark.parametrize("facts", [None, [], {"unexpected": "Bearer synthetic-only"},
                                    {"caddy_effective": {"unknown": True}}])
def test_unexpected_evidence_never_projects(facts):
    result = reduce_evidence(facts, ["Bearer synthetic-only"])
    assert result["status"] == "BLOCKED"
    assert "Bearer synthetic-only" not in json.dumps(result)
    assert "UNEXPECTED_EVIDENCE" in result["reason_codes"]


@pytest.mark.parametrize("raw,code", [
    (b"bad", "MALFORMED_JSON"), (b"[]", "MALFORMED_JSON"),
    (b'{"a":NaN}', "MALFORMED_JSON"),
    (b'{"a":{"b":false,"b":true}}', "DUPLICATE_JSON_KEYS"),
    (b"x" * (attestor.LIMIT + 1), "STDOUT_OVERSIZED"),
])
def test_json_is_strict(raw, code):
    with pytest.raises(attestor.EvidenceError, match=code):
        attestor._json(raw)


@pytest.mark.parametrize("status", [b"301", b"302", b"401", b"500", b"", b"200\n"])
def test_admin_requires_exact_http_200(status):
    with pytest.raises(attestor.EvidenceError):
        attestor._admin_json(b'{}\n' + status)


def test_admin_duplicate_keys_rejected():
    with pytest.raises(attestor.EvidenceError, match="DUPLICATE_JSON_KEYS"):
        attestor._admin_json(b'{"apps":{},"apps":{}}\n200')


@pytest.mark.parametrize("script,code", [
    ("import sys; sys.exit(7)", "SUBPROCESS_NONZERO"),
    ("import sys; sys.stdout.write('x'*200000)", "STDOUT_OVERSIZED"),
    ("import time; time.sleep(2)", "SUBPROCESS_TIMEOUT"),
])
def test_bounded_subprocess(script, code):
    # Only isolated synthetic Python children; never Docker/Caddy/PHP.
    with pytest.raises(attestor.EvidenceError, match=code):
        attestor._run([sys.executable, "-I", "-c", script], time.monotonic() + 0.5)


def test_expired_total_deadline_spawns_nothing(monkeypatch):
    monkeypatch.setattr(attestor.subprocess, "Popen", lambda *a, **k: pytest.fail("expired"))
    with pytest.raises(attestor.EvidenceError, match="TOTAL_DEADLINE_EXCEEDED"):
        attestor._run([], time.monotonic() - 1)


def metadata():
    internal = dict(internal=True, name="ai-shopping-internal", id="internal-id", project="ai-shopping")
    external = dict(internal=False, name="ai-shopping-network", id="external-id", project="ai-shopping")
    db = dict(id="db-id", started="fixed-start", running=True, project="ai-shopping", service="database",
              mode="ai-shopping-internal", networks={"ai-shopping-internal": {"NetworkID": "internal-id"}},
              ports={"3306/tcp": None})
    wp = dict(id="wp-id", started="fixed-start", running=True, project="ai-shopping", service="wordpress",
              mode="ai-shopping-network", networks={"ai-shopping-internal": {"NetworkID": "internal-id"},
              "ai-shopping-network": {"NetworkID": "external-id"}},
              ports={"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]})
    return [wp, db, internal, external]


def test_expected_topology():
    assert all(attestor._topology(*metadata()).values())


@pytest.mark.parametrize("index,key,value", [
    (0, "project", "other"), (0, "service", "other"), (0, "running", False),
    (0, "ports", {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58081"}]}),
    (0, "ports", {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "58082"}]}),
    (0, "ports", {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}] * 2}),
    (0, "mode", "host"), (0, "networks", {}), (0, "unexpected", True),
    (1, "project", "other"), (1, "running", False), (1, "networks", {}),
    (1, "ports", {"3306/tcp": [{"HostIp": "127.0.0.1", "HostPort": "3306"}]}),
    (2, "internal", False), (2, "internal", 1), (2, "id", "other"),
    (2, "name", "other"), (2, "project", "other"), (3, "id", "other"),
])
def test_unexpected_container_project_network_and_publish_block(index, key, value):
    values = metadata()
    values[index][key] = value
    topology = attestor._topology(*values)
    assert not all(topology.values())
    facts = complete()
    facts["topology"] = topology
    assert reduce_evidence(facts)["status"] == "BLOCKED"


def caddy():
    # Reviewed adaptation stand-in. The collector requires full document equality,
    # not loose searches for a deny somewhere in the document.
    return {"apps": {"http": {"servers": {"srv0": {"routes": [
        {"deny": "namespace"}, {"deny": "rest_route"}, {"deny": "ambiguous_rest_route"},
        {"reverse_proxy": "127.0.0.1:58082"},
    ]}}}}, "logging": {"logs": {"default": {"writer": {"output": "discard"}}}}}


@pytest.mark.parametrize("change", ["namespace_missing", "rest_route_missing", "deny_after_proxy",
                                    "stale_port", "unsafe_sink", "authorization", "alternate_handler"])
def test_loaded_caddy_divergence_blocks(change):
    adapted = caddy()
    loaded = copy.deepcopy(adapted)
    routes = loaded["apps"]["http"]["servers"]["srv0"]["routes"]
    if change == "namespace_missing": del routes[0]
    if change == "rest_route_missing": del routes[1]
    if change == "deny_after_proxy": routes.reverse()
    if change == "stale_port": routes[-1]["reverse_proxy"] = "127.0.0.1:58081"
    if change == "unsafe_sink": loaded["logging"]["logs"]["default"]["writer"]["output"] = "file"
    if change == "authorization": loaded["logging"]["authorization"] = "synthetic-secret"
    if change == "alternate_handler": loaded["apps"]["http"]["servers"]["other"] = {"routes": [{}]}
    proofs = attestor._caddy_proofs(loaded, adapted, True, True)
    assert proofs["loaded_config_proven"]
    assert not proofs["namespace_deny_proven"]
    assert not proofs["safe_sink_proven"]
    assert "synthetic-secret" not in json.dumps(proofs)


@pytest.mark.parametrize("loaded,identity,policy", [(None, True, True), ({}, True, True),
                                                   (caddy(), False, True), (caddy(), True, False)])
def test_adaptation_alone_never_proves_runtime(loaded, identity, policy):
    assert not all(attestor._caddy_proofs(loaded, caddy(), identity, policy).values())


LISTENERS = b"p123\nccaddy\nf10\nn127.0.0.1:2019\nf11\nn*:58080\nf12\nn*:58443\n"


def test_caddy_host_listener_identity():
    assert attestor._host_pid(LISTENERS) == "123"


@pytest.mark.parametrize("raw", [LISTENERS.replace(b"127.0.0.1", b"*"),
                                 LISTENERS.replace(b"ccaddy", b"cother"),
                                 LISTENERS + b"p124\nccaddy\nn*:58080\n",
                                 LISTENERS.replace(b"58443", b"58081"), b"synthetic-secret"])
def test_ambiguous_or_wrong_host_listeners_block(raw):
    assert attestor._host_pid(raw) is None


def install_collector(monkeypatch):
    monkeypatch.setattr(attestor.sys, "platform", "darwin")
    monkeypatch.setattr(attestor.repository, "_socket", lambda: "unix:///trusted/.colima/aicontrolcenter-commerce/docker.sock")
    monkeypatch.setattr(attestor, "CADDY", sys.executable)
    calls = []
    values = dict(zip(("shopping-wordpress", "shopping-db", "ai-shopping-internal", "ai-shopping-network"), metadata()))
    def run(argv, deadline):
        calls.append(argv)
        assert deadline > 0
        if argv[0] == attestor.repository.DOCKER:
            assert argv[1:3] == ["--host", "unix:///trusted/.colima/aicontrolcenter-commerce/docker.sock"]
            assert "Env" not in argv[-2]
            return json.dumps(values[argv[-1]]).encode()
        if argv[0] == "/usr/sbin/lsof":
            return ("n" + str(Path(sys.executable).resolve()) + "\n").encode() if "-a" in argv else LISTENERS
        if argv[0] == "/usr/bin/curl":
            assert argv[-1] == "http://127.0.0.1:2019/config/"
            assert "--location" not in argv and "-H" not in argv
            return json.dumps(caddy()).encode() + b"\n200"
        assert argv[1] == "adapt"
        return json.dumps(caddy()).encode()
    monkeypatch.setattr(attestor, "_run", run)
    return calls


def test_safe_files_and_cli_never_become_loaded_runtime_proof(monkeypatch):
    calls = install_collector(monkeypatch)
    result = attestor.observe()
    assert result["status"] == "BLOCKED"
    assert not result["public_edge_runtime_isolation_proven"]
    assert not result["deployment_logging_safety_proven"]
    assert not result["controlled_nonprod_soft_launch_ready"]
    for reason in ("RUNTIME_BINDING_UNPROVEN", "SERVING_GENERATION_PROVENANCE_UNPROVEN"):
        assert reason in result["reason_codes"]
    assert all(result[key] is False for key in FALSE_FIELDS)
    assert len(calls) == 14


def test_environment_poisoning_is_ignored(monkeypatch):
    install_collector(monkeypatch)
    before = attestor.observe()
    for key in ("HOME", "DOCKER_HOST", "DOCKER_CONTEXT", "HTTP_PROXY", "HTTPS_PROXY", "CURL_HOME", "PHPRC", "PHP_INI_SCAN_DIR"):
        monkeypatch.setenv(key, "synthetic-secret")
    assert attestor.observe() == before
    assert "synthetic-secret" not in json.dumps(attestor.ENV)


def test_trusted_home_binding_ignores_ambient_home(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setenv("HOME", "/synthetic-untrusted")
    monkeypatch.setattr(attestor.repository, "resolve_trusted_mac_account_home",
                        lambda: SimpleNamespace(passwd_home="/trusted"))
    assert attestor.repository._socket() == "unix:///trusted/.colima/aicontrolcenter-commerce/docker.sock"


def test_caller_override_rejected_before_observation(monkeypatch, capsys):
    assert not inspect.signature(attestor.observe).parameters
    monkeypatch.setattr(attestor.sys, "argv", ["attestor", "synthetic-secret"])
    monkeypatch.setattr(attestor, "observe", lambda: pytest.fail("caller override"))
    assert attestor.main() == 2
    output = capsys.readouterr()
    assert output.err == "" and "synthetic-secret" not in output.out
    assert "CALLER_OVERRIDE_REJECTED" in json.loads(output.out)["reason_codes"]


def test_non_mac_spawns_nothing(monkeypatch):
    monkeypatch.setattr(attestor.sys, "platform", "linux")
    monkeypatch.setattr(attestor, "_run", lambda *a: pytest.fail("not Mac"))
    assert attestor.observe()["status"] == "BLOCKED"


def test_collector_failure_never_emits_exception(monkeypatch, capsys):
    monkeypatch.setattr(attestor.sys, "argv", ["attestor"])
    def fail():
        raise RuntimeError("synthetic-secret")
    monkeypatch.setattr(attestor, "observe", fail)
    assert attestor.main() == 2
    output = capsys.readouterr()
    assert output.err == "" and "synthetic-secret" not in output.out
    assert json.loads(output.out)["status"] == "BLOCKED"


def test_no_application_execution_or_mutation_commands(monkeypatch):
    calls = install_collector(monkeypatch)
    attestor.observe()
    for argv in calls:
        assert not set(argv) & {"up", "down", "restart", "recreate", "reload", "start", "stop", "ssh", "wp", "--env", "-e"}
        assert not any("Authorization:" in word for word in argv)
    assert "shell=True" not in inspect.getsource(attestor)
    assert not hasattr(attestor, "FILES_PROBE")
    assert not any("exec" in argv for argv in calls)
    assert "wp-load.php" not in inspect.getsource(attestor)


def test_repository_safety_does_not_establish_route_absence(monkeypatch):
    install_collector(monkeypatch)
    monkeypatch.setattr(attestor.repository, '_repository_facts', lambda: True)
    result = attestor.observe()
    invariants = result['repository_invariants']
    assert invariants['reviewed_edge_policy_valid']
    assert invariants['reviewed_safety_controls_valid']
    assert invariants['no_generic_proxy_or_caller_target'] is False
    assert invariants['no_public_observation_endpoint'] is False
    assert not result['public_edge_runtime_isolation_proven']
