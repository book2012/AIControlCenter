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
            return json.dumps(values.get(argv[-1], {})).encode()
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
    assert len(calls) == 18


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


def binding_fixture():
    mounts = [dict(Type="volume", Name="ai-shopping-wordpress", Source="/fixed/volume",
                   Destination="/var/www/html", RW=True)]
    for source, destination in (
        ("config/shopping-apache-safety.conf", "/etc/apache2/sites-available/000-default.conf"),
        ("config/shopping-php-safety.ini", "/usr/local/etc/php/conf.d/zz-shopping-safety.ini"),
        ("wordpress/plugins/ai-shopping-storefront", "/var/www/html/wp-content/plugins/ai-shopping-storefront"),
    ):
        mounts.append(dict(Type="bind", Name="", Source=str(attestor.repository.ROOT / "deploy/shopping" / source),
                           Destination=destination, RW=False))
    binding = dict(id="a" * 64, image="sha256:" + "b" * 64,
                   configured_image=attestor.WORDPRESS_IMAGE, started="2026-09-08T01:02:03.000000001Z",
                   running=True, paused=False, restarting=False, pid=42, restart_count=0, mounts=mounts)
    image = dict(id=binding["image"], digests=["wordpress@" + attestor.WORDPRESS_IMAGE.split("@")[1]])
    return binding, image


def binding_proofs(binding, image, after=None):
    return attestor._deployment_binding(binding, binding if after is None else after,
                                        image, image, attestor._topology(*metadata()), True)


def test_stable_binding_does_not_invent_loaded_state_or_freshness():
    binding, image = binding_fixture()
    result = binding_proofs(binding, image)
    for key in ("actual_runtime_image_matches", "container_identity_bound",
                "runtime_generation_identity_bound", "expected_mounts_config_bound"):
        assert result[key] is True
    for key in ("runtime_generation_fresh", "serving_generation_provenance_bound",
                "mount_artifact_integrity_proven", "no_unexpected_mutable_executable_config"):
        assert result[key] is False


@pytest.mark.parametrize("key,value", [("id", "c" * 64), ("pid", 43), ("restart_count", 1),
                                        ("started", "2026-09-08T01:02:04.000000001Z"),
                                        ("paused", True), ("running", False)])
def test_generation_change_invalidates_binding(key, value):
    binding, image = binding_fixture()
    after = copy.deepcopy(binding)
    after[key] = value
    result = binding_proofs(binding, image, after)
    assert not result["runtime_generation_identity_bound"]
    assert not result["actual_runtime_image_matches"]


@pytest.mark.parametrize("change", ["image", "digest", "rw", "source", "extra", "duplicate"])
def test_wrong_image_or_mount_binding_fails_closed(change):
    binding, image = binding_fixture()
    if change == "image": image["id"] = "sha256:" + "c" * 64
    elif change == "digest": image["digests"] = []
    elif change == "rw": binding["mounts"][1]["RW"] = True
    elif change == "source": binding["mounts"][1]["Source"] = "/other"
    elif change == "extra": binding["mounts"].append(copy.deepcopy(binding["mounts"][1]))
    else: binding["mounts"][2] = copy.deepcopy(binding["mounts"][1])
    result = binding_proofs(binding, image)
    assert not result["actual_runtime_image_matches" if change in ("image", "digest")
                      else "expected_mounts_config_bound"]


def test_collector_passes_manifest_and_unknown_identity_categories(monkeypatch):
    install_collector(monkeypatch)
    original = attestor.reduce_evidence
    seen = {}
    def reduce(facts, errors, **kwargs):
        seen.update(kwargs)
        return original(facts, errors, **kwargs)
    monkeypatch.setattr(attestor, "reduce_evidence", reduce)
    result = attestor.observe()
    assert seen["manifest"] == json.loads((attestor.repository.ROOT /
        "config/deployment/shopping-runtime-component-manifest.json").read_text())
    assert seen["observed_components"] == dict.fromkeys(attestor.CATEGORIES, None)
    assert result["complete_component_identity_proven"] is False


def test_binding_format_uses_native_mount_json():
    assert '"mounts":{{json .Mounts}}' in attestor.BINDING_FORMAT
    assert "range" not in attestor.BINDING_FORMAT
    assert "index" not in attestor.BINDING_FORMAT


def test_raw_docker_mount_projection_ignores_metadata_policy():
    binding, image = binding_fixture()
    raw = binding["mounts"]
    raw[1].update(Mode="ro", Propagation="rprivate", Driver="local",
                  rw=True, runtime_generation_fresh=True,
                  mount_artifact_integrity_proven=True)
    original = copy.deepcopy(raw)
    projected = attestor._normalize_mounts(raw)
    assert projected == [dict(type=m["Type"], name=m["Name"], source=m["Source"],
                              destination=m["Destination"], rw=m["RW"]) for m in raw]
    assert raw == original
    assert binding_proofs(binding, image)["expected_mounts_config_bound"]
    assert not binding_proofs(binding, image)["runtime_generation_fresh"]
    assert not binding_proofs(binding, image)["mount_artifact_integrity_proven"]


@pytest.mark.parametrize("mount_index,field,change", [
    (index, field, change)
    for index in (0, 1)
    for field in ("Type", "Name", "Source", "Destination", "RW")
    for change in ("missing", "null", "integer", "list", "dict")
    if (index, field, change) != (1, "Name", "missing")
])
def test_malformed_docker_mount_field_blocks(field, change, mount_index):
    binding, image = binding_fixture()
    mount = binding["mounts"][mount_index]
    if change == "missing":
        del mount[field]
    else:
        mount[field] = {"null": None, "integer": 1, "list": [], "dict": {}}[change]
    assert attestor._normalize_mounts(binding["mounts"]) is None
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


@pytest.mark.parametrize("omit_bind_name", [False, True])
def test_type_aware_mount_names_normalize(omit_bind_name):
    binding, image = binding_fixture()
    if omit_bind_name:
        for mount in binding["mounts"][1:]:
            del mount["Name"]
    original = copy.deepcopy(binding["mounts"])
    normalized = attestor._normalize_mounts(binding["mounts"])
    assert normalized[0] == dict(type="volume", name="ai-shopping-wordpress",
        source="/fixed/volume", destination="/var/www/html", rw=True)
    assert all(m["name"] == "" for m in normalized[1:])
    assert all(set(m) == {"type", "name", "source", "destination", "rw"} for m in normalized)
    assert binding["mounts"] == original
    proofs = binding_proofs(binding, image)
    assert {key for key, value in proofs.items() if value} == {
        "reviewed_pinned_identity_contract", "expected_immutable_wordpress_image",
        "actual_runtime_image_matches", "container_identity_bound",
        "runtime_generation_identity_bound", "expected_mounts_config_bound"}
    result = attestor.reduce_evidence({"deployment_identity": proofs})
    assert not any(result["closed_controls"].values())
    assert not any(result["repository_invariants"].values())
    assert all(result[key] is False for key in FALSE_FIELDS)
    assert not result["complete_component_identity_proven"]


@pytest.mark.parametrize("mount_index,field,value", [
    (0, "Name", ""), (0, "Type", "tmpfs"), (1, "Type", "tmpfs"),
])
def test_empty_volume_name_and_unknown_mount_type_block(mount_index, field, value):
    binding, image = binding_fixture()
    binding["mounts"][mount_index][field] = value
    assert attestor._normalize_mounts(binding["mounts"]) is None
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


@pytest.mark.parametrize("mount_index", [1, 2, 3])
@pytest.mark.parametrize("field,value", [("Source", "/unexpected"),
    ("Destination", "/unexpected"), ("RW", True), ("Name", "unexpected")])
def test_each_safety_bind_enforces_expected_binding(mount_index, field, value):
    binding, image = binding_fixture()
    binding["mounts"][mount_index][field] = value
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


@pytest.mark.parametrize("field,value", [("Type", ""), ("Source", ""),
    ("Destination", ""), ("RW", "false"), ("Type", True), ("Name", False),
    ("Source", True), ("Destination", True)])
def test_invalid_mount_primitives_block(field, value):
    binding, image = binding_fixture()
    binding["mounts"][1][field] = value
    assert attestor._normalize_mounts(binding["mounts"]) is None
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


@pytest.mark.parametrize("mounts", [None, {}, "mounts", [None], [[]], ["mount"]])
def test_invalid_mount_collection_blocks(mounts):
    binding, image = binding_fixture()
    binding["mounts"] = mounts
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


@pytest.mark.parametrize("change", ["destination", "duplicate_destination", "extra", "name", "type"])
def test_closed_expected_mount_set_blocks(change):
    binding, image = binding_fixture()
    mounts = binding["mounts"]
    if change == "destination":
        mounts[1]["Destination"] = "/etc/apache2/other.conf"
    elif change == "duplicate_destination":
        mounts[2]["Destination"] = mounts[1]["Destination"]
        assert attestor._normalize_mounts(mounts) is None
    elif change == "extra":
        mounts.append(dict(Type="bind", Name="", Source="/extra/config",
                           Destination="/usr/local/etc/php/conf.d/extra.ini", RW=False))
    elif change == "name":
        mounts[0]["Name"] = "other-volume"
    else:
        mounts[1]["Type"] = "volume"
    assert not binding_proofs(binding, image)["expected_mounts_config_bound"]


def test_stable_mounts_leave_loaded_controls_and_inventory_unproven():
    binding, image = binding_fixture()
    result = attestor.reduce_evidence({"deployment_identity": binding_proofs(binding, image)})
    assert result["deployment_identity"]["expected_mounts_config_bound"]
    assert not any(result["closed_controls"].values())
    assert not any(result["repository_invariants"].values())
    assert not result["complete_component_identity_proven"]
    assert not result["public_edge_runtime_isolation_proven"]
    assert not result["deployment_logging_safety_proven"]
    assert all(result[key] is False for key in FALSE_FIELDS)


def test_collector_commands_remain_fixed_read_only_arrays(monkeypatch):
    calls = install_collector(monkeypatch)
    attestor.observe()
    docker_calls = [argv for argv in calls if argv[0] == attestor.repository.DOCKER]
    prefix = [attestor.repository.DOCKER, "--host",
              "unix:///trusted/.colima/aicontrolcenter-commerce/docker.sock"]
    expected = [prefix + ["inspect", "--format", attestor.BINDING_FORMAT, "shopping-wordpress"],
                prefix + ["image", "inspect", "--format", attestor.IMAGE_FORMAT, attestor.WORDPRESS_IMAGE]]
    expected += [prefix + ["inspect", "--format", attestor.CONTAINER_FORMAT, name]
                 for name in ("shopping-wordpress", "shopping-db")]
    expected += [prefix + ["network", "inspect", "--format", attestor.NETWORK_FORMAT, name]
                 for name in ("ai-shopping-internal", "ai-shopping-network")]
    assert len(docker_calls) == 2 * len(expected)
    assert all(docker_calls.count(command) == 2 for command in expected)
    assert all(type(argv) is list for argv in calls)
    assert not any(token in {"exec", "php", "ssh", "compose", "restart", "reload"}
                   for argv in calls for token in argv)
    assert "shell=True" not in inspect.getsource(attestor)
