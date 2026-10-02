"""Focused offline tests for PUBLIC-STOREFRONT-V2-ACTIVATION-01."""

from datetime import datetime, timezone
import copy
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from core.shopping.public_storefront_v2_activation_03_final_authorization import validate_authorization
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    ARTIFACTS, AUTHORITY_ID, CADDYFILE_SHA256, ContractError,
    EXPECTED_PORTS, EXPECTED_RUNTIME_SEMANTIC_PROJECTION, MUTATION_ID,
    POLICY_VERSION, PROFILE, PROFILE_FILE,
    attest_runtime_profile, desired_runtime_projection, observed_runtime_projection,
    precondition_template, projection, validate_post_activation, validate_preconditions,
)
from ops.macos.shopping.issue_public_storefront_v2_activation_03_final_authorization import _authorization
from ops.macos.shopping.public_storefront_v2_activation_03_final_authorization_store import (
    PublicStorefrontV2ActivationAuthorizationStore,
)
from ops.macos.shopping.public_storefront_v2_activation_03_final_operator import (
    ActivationRunner, MacActivationPort,
)
from ops.macos.shopping import issue_public_storefront_v2_activation_03_final_authorization as issuer


ROOT = Path(__file__).resolve().parents[1]
TRUSTED_DEPLOYMENT_ROOT = Path("/Users/kyouhan/AIControlCenter")


def source():
    return {"head": "1" * 40, "clean": True, "artifacts": ARTIFACTS,
            "activation_bundle_sha256": "2" * 64}


def preconditions():
    return precondition_template(
        source=source(),
        colima={"profile": PROFILE, "profile_file": PROFILE_FILE,
                "semantic_projection": EXPECTED_RUNTIME_SEMANTIC_PROJECTION,
                "status": "Broken"},
        forwarding={"owner": "colima", "profile": PROFILE, "host": "127.0.0.1",
                     "port": 58082, "required_for_lifecycle": True},
        wordpress={"container_id": "43d8d4f9e370ac066a77cbf1b346002df6d11cff00e3212bc0a3c6b668745648",
                   "state": "created", "running": False, "published": "127.0.0.1:58082->80/tcp"},
        database={"container_id": "434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323",
                  "state": "running", "healthy": True, "published": False,
                  "volume": "ai-shopping-database"},
    )


def auth(pre):
    return _authorization(preconditions=pre, uid=os.getuid(), gid=os.getgid())


def post(*, empty=False):
    return {
        "public": {"https_success": True, "basic_auth": False, "storefront_rendered": True},
        "shopping_reads": {"categories": True, "search": True, "featured_products": True, "products": True},
        "product_catalog": "VALID_EMPTY" if empty else "VALID_NONEMPTY",
        "private_boundary": {"wordpress_paths_denied": True, "rest_routes_denied": True,
                              "management_paths_denied": True, "shopping_writes_not_proxied": True,
                              "order_payment_cart_checkout_not_proxied": True},
        "dev": {"https_success": False, "basic_auth_required": True,
                "production_never_uses_dev": True},
        "legacy": {"path": "/homepage/storefront", "status": 301, "location": "/"},
        "direct_browser_woo_denied": True,
        "wordpress_loopback": "127.0.0.1:58082", "server_side_api": "127.0.0.1:58081",
        "database_continuity": True, "effective_caddy_v2": True,
        "rest_route_live_proof": True, "product_detail_dynamic_id": not empty,
        "public_commerce_write_request": "NOT_PERFORMED", "caddy_reload_count": 1,
    }


def test_authority_is_distinct_and_hard_bound():
    value = auth(preconditions())
    assert value.authority_id == AUTHORITY_ID
    assert value.authoritative_work_item == AUTHORITY_ID
    assert value.mutation_id == MUTATION_ID
    assert value.maximum_uses == 1
    assert value.production_write_authority is False
    assert value.ubuntu_authority is False
    assert value.database_recreation_allowed is False
    assert value.volume_recreation_allowed is False
    assert value.dns_change_allowed is False
    assert value.woo_write_authority is False
    validate_authorization(value, now=datetime.now(timezone.utc), uid=os.getuid(), gid=os.getgid())


def test_phase_a_contract_is_host_only_and_binds_broken_profile():
    value = inspect.getsource(MacActivationPort.observe_preconditions)
    assert "_docker_inspect" not in value
    assert "Docker" in value and "never call Docker" in value
    bound = preconditions()
    validate_preconditions(bound)
    bound["colima"]["status"] = "Running"
    with pytest.raises(ContractError):
        validate_preconditions(bound)


def test_contract_rejects_drift_and_requires_dynamic_detail_contract():
    value = preconditions()
    value["desired"]["policy_version"] = "old"
    with pytest.raises(ContractError):
        validate_preconditions(value)
    assert CADDYFILE_SHA256 == ARTIFACTS["ops/macos/caddy/Caddyfile"]
    assert EXPECTED_PORTS == {"control_plane": 58081, "wordpress": 58082, "dev": 18080}
    assert POLICY_VERSION == "public-storefront-migration/v2"
    validate_post_activation(post(empty=True))
    with pytest.raises(ContractError):
        validate_post_activation({**post(), "product_detail_dynamic_id": False})


def test_store_is_durable_one_shot_and_does_not_reissue(tmp_path):
    path = tmp_path / "public-storefront-v2-activation-01.sqlite3"
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(path, uid=os.getuid(), gid=os.getgid())
    store._issue(auth(preconditions()))
    result = store.consume(lambda: preconditions())
    assert result.receipt.state == "COMMITTED"
    with pytest.raises(Exception):
        PublicStorefrontV2ActivationAuthorizationStore._open_existing_for_test(path, uid=os.getuid(), gid=os.getgid())
    with pytest.raises(Exception):
        store._issue(auth(preconditions()))


class FakePort:
    def __init__(self, before):
        self.before = before
        self.calls = []

    def observe_preconditions(self):
        self.calls.append("phase_a")
        return self.before

    def reconcile_colima(self):
        self.calls.append("colima_repair")
        return True

    def validate_existing_generations(self):
        self.calls.append("phase_b")
        return True

    def start_existing_wordpress(self):
        self.calls.append("wordpress_start")
        return True

    def wordpress_healthy(self):
        self.calls.append("wordpress_health")
        return True

    def server_side_api_connectivity(self):
        self.calls.append("server_side_api")
        return True

    def validate_caddy_offline(self):
        self.calls.append("caddy_validate")
        return True

    def reload_caddy_once(self):
        self.calls.append("caddy_reload")
        return True

    def effective_caddy_v2(self):
        self.calls.append("effective_caddy_v2")
        return True

    def post_activation(self):
        self.calls.append("post")
        return post()


def test_runner_has_two_phase_order_and_one_mutation_each(tmp_path):
    before = preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "a.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(auth(before))
    port = FakePort(before)
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "ACTIVATED"
    assert port.calls == ["phase_a", "phase_a", "colima_repair", "phase_b", "wordpress_start",
                          "wordpress_health", "server_side_api", "caddy_validate", "caddy_reload",
                          "effective_caddy_v2", "post"]
    assert result["colima_repair_attempted"] is True
    assert result["wordpress_start_attempted"] is True
    assert result["caddy_reload_attempted"] is True
    assert result["caddy_reload_count"] == 1
    assert result["colima_retry"] is False


def test_phase_b_identity_failure_never_starts_wordpress(tmp_path):
    before = preconditions()
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(tmp_path / "b.sqlite3", uid=os.getuid(), gid=os.getgid())
    store._issue(auth(before))
    port = FakePort(before)
    port.validate_existing_generations = lambda: port.calls.append("phase_b") or False
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "UNCERTAIN"
    assert result["colima_repair_attempted"] is True
    assert result["wordpress_start_attempted"] is False
    assert "wordpress_start" not in port.calls
    assert "caddy_reload" not in port.calls


def test_semantic_profile_drift_after_claim_stops_before_mutation(tmp_path):
    before = preconditions()
    drifted = copy.deepcopy(before)
    drifted["colima"]["semantic_projection"]["cpus"] = 8
    store = PublicStorefrontV2ActivationAuthorizationStore._for_test(
        tmp_path / "semantic-drift.sqlite3", uid=os.getuid(), gid=os.getgid(),
    )
    store._issue(auth(before))

    class DriftPort(FakePort):
        def observe_preconditions(self):
            self.calls.append("phase_a")
            return before if self.calls.count("phase_a") == 1 else drifted

    port = DriftPort(before)
    result = ActivationRunner(store, port, os.getuid(), os.getgid()).run()
    assert result["status"] == "UNCERTAIN"
    assert result["authorization_consumed"] is True
    assert port.calls == ["phase_a", "phase_a"]


def test_issuance_denied_on_semantic_profile_drift(monkeypatch):
    before = preconditions()
    drifted = copy.deepcopy(before)
    drifted["colima"]["semantic_projection"]["network_address"] = True

    class TTY:
        def isatty(self):
            return True

        def write(self, value):
            return len(value)

        def flush(self):
            pass

    monkeypatch.setattr(issuer, "sys", SimpleNamespace(stdin=TTY(), stdout=TTY()))
    monkeypatch.setattr(issuer, "source_identity", lambda *args, **kwargs: source())
    monkeypatch.setattr(
        issuer, "resolve_trusted_mac_account_home",
        lambda: SimpleNamespace(passwd_home=str(ROOT)),
    )
    monkeypatch.setattr(
        issuer, "issue_trusted_ownership_expectation",
        lambda home: SimpleNamespace(expected_uid=os.getuid(), expected_gid=os.getgid()),
    )

    class DriftPort:
        def __init__(self, **kwargs):
            self.calls = 0

        def observe_preconditions(self):
            self.calls += 1
            return before if self.calls == 1 else drifted

    monkeypatch.setattr(issuer, "MacActivationPort", DriftPort)
    responses = iter([source()["head"], source()["activation_bundle_sha256"], issuer.ACKNOWLEDGEMENT])
    monkeypatch.setattr("builtins.input", lambda *args: next(responses))
    result = issuer.issue_and_run(candidate_root=ROOT, runtime_root=ROOT)
    assert result["status"] == "PRECONDITION_DRIFT"


def test_static_mutation_surface_is_closed():
    source_text = inspect.getsource(MacActivationPort)
    for forbidden in ("[\"compose\"", " compose up", "container create", "container rm", "volume create", "volume rm"):
        assert forbidden not in source_text.lower()
    assert '"container", "start"' in source_text
    assert "WORDPRESS_CONTAINER_ID" in source_text
    assert "UbuntuWorkerClient" not in source_text


def test_post_result_is_value_free():
    result = projection("BLOCKED", authorization_consumed=False)
    assert "secret" not in json.dumps(result)


def _profile_yaml(*, mounts=None):
    return {
        "cpu": 4,
        "disk": 80,
        "memory": 6,
        "arch": "aarch64",
        "runtime": "docker",
        "kubernetes": {"enabled": False},
        "autoActivate": False,
        "network": {
            "address": False,
            "mode": "shared",
            "dns": None,
            "dnsHosts": {},
            "hostAddresses": False,
        },
        "forwardAgent": False,
        "vmType": "vz",
        "portForwarder": "ssh",
        "mountType": "virtiofs",
        "mounts": copy.deepcopy(
            _absolute_mounts(TRUSTED_DEPLOYMENT_ROOT)
            if mounts is None else mounts
        ),
    }


def _absolute_mounts(root):
    return [
        {"location": str(root / mount["location"]), "writable": mount["writable"]}
        for mount in EXPECTED_RUNTIME_SEMANTIC_PROJECTION["mounts"]
    ]


def _valid_profile_bytes():
    return yaml.safe_dump(_profile_yaml(), sort_keys=True).encode()


def _assert_rejected(raw):
    with pytest.raises(ContractError):
        attest_runtime_profile(
            raw, contract=json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text()),
            trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT,
        )


def test_semantically_equivalent_yaml_formatting_and_order_passes():
    first = yaml.safe_dump(_profile_yaml(), sort_keys=True).encode()
    value = _profile_yaml()
    reordered = {key: value[key] for key in reversed(list(value))}
    second = ("# formatting and order are not semantics\n" +
              yaml.safe_dump(reordered, sort_keys=False)).encode()
    contract = json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text())
    assert attest_runtime_profile(first, contract=contract,
                                  trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT) == \
        attest_runtime_profile(second, contract=contract,
                               trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT)


@pytest.mark.parametrize(("field", "value"), [("cpu", 8), ("memory", 8)])
def test_cpu_and_memory_drift_fail(field, value):
    profile = _profile_yaml()
    profile[field] = value
    _assert_rejected(yaml.safe_dump(profile).encode())


@pytest.mark.parametrize(("field", "value"), [("arch", "x86_64"), ("runtime", "containerd")])
def test_architecture_and_runtime_drift_fail(field, value):
    profile = _profile_yaml()
    profile[field] = value
    _assert_rejected(yaml.safe_dump(profile).encode())


@pytest.mark.parametrize(("field", "value"), [
    (("network", "address"), True),
    (("network", "mode"), "bridged"),
    (("network", "dns"), ["1.1.1.1"]),
    (("network", "hostAddresses"), True),
    (("portForwarder",), "none"),
    (("autoActivate",), True),
    (("kubernetes", "enabled"), True),
    (("forwardAgent",), True),
])
def test_network_and_security_drift_fail(field, value):
    profile = _profile_yaml()
    target = profile
    for part in field[:-1]:
        target = target[part]
    target[field[-1]] = value
    _assert_rejected(yaml.safe_dump(profile).encode())


def test_missing_required_mount_fails():
    mounts = _absolute_mounts(TRUSTED_DEPLOYMENT_ROOT)[:-1]
    _assert_rejected(yaml.safe_dump(_profile_yaml(mounts=mounts)).encode())


def test_writable_required_mount_fails():
    mounts = _absolute_mounts(TRUSTED_DEPLOYMENT_ROOT)
    mounts[1]["writable"] = True
    _assert_rejected(yaml.safe_dump(_profile_yaml(mounts=mounts)).encode())


def test_extra_mount_fails():
    mounts = _absolute_mounts(TRUSTED_DEPLOYMENT_ROOT)
    mounts.append({"location": "/Users/kyouhan/AIControlCenter/deploy/shopping", "writable": False})
    _assert_rejected(yaml.safe_dump(_profile_yaml(mounts=mounts)).encode())


def test_broad_config_directory_mount_fails():
    mounts = [_absolute_mounts(TRUSTED_DEPLOYMENT_ROOT)[0], {
        "location": "/Users/kyouhan/AIControlCenter/deploy/shopping/config", "writable": False,
    }]
    _assert_rejected(yaml.safe_dump(_profile_yaml(mounts=mounts)).encode())


def test_exact_required_three_entry_mount_contract_passes():
    contract = json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text())
    assert attest_runtime_profile(
        _valid_profile_bytes(), contract=contract,
        trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT,
    )


def test_desired_projection_is_root_independent(tmp_path):
    contract_text = (ROOT / "ops/macos/colima/commerce-runtime.json").read_text()
    contracts = []
    for name in ("candidate-a", "candidate-b"):
        path = tmp_path / name / "ops/macos/colima/commerce-runtime.json"
        path.parent.mkdir(parents=True)
        path.write_text(contract_text)
        contracts.append(json.loads(path.read_text()))
    assert desired_runtime_projection(contracts[0]) == desired_runtime_projection(contracts[1])
    assert desired_runtime_projection(contracts[0]) == EXPECTED_RUNTIME_SEMANTIC_PROJECTION
    assert all(not mount["location"].startswith("/")
               for mount in EXPECTED_RUNTIME_SEMANTIC_PROJECTION["mounts"])


def test_candidate_checkout_mounts_are_rejected_by_production_root():
    contract = json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text())
    raw = yaml.safe_dump(_profile_yaml(mounts=_absolute_mounts(ROOT))).encode()
    with pytest.raises(ContractError):
        attest_runtime_profile(
            raw, contract=contract,
            trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT,
        )


def test_raw_live_yaml_sha_is_not_compared_to_json_contract_sha():
    source = inspect.getsource(MacActivationPort._observe_profile_config)
    assert "digest_bytes" not in source
    assert "PROFILE_SHA256" not in source
    assert "attest_runtime_profile" in source


def test_live_broad_mount_profile_is_rejected_read_only():
    raw = Path("/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml")
    if raw.is_file():
        contract = json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text())
        observed = observed_runtime_projection(
            raw.read_bytes(), trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT,
        )
        assert observed["mounts"] != desired_runtime_projection(contract)["mounts"]
        _assert_rejected(raw.read_bytes())


def test_tilde_mounts_fail_closed_without_trusted_home_abstraction():
    contract = json.loads((ROOT / "ops/macos/colima/commerce-runtime.json").read_text())
    profile = _profile_yaml()
    profile["mounts"][0]["location"] = "~/deploy/shopping/wordpress/plugins/ai-shopping-storefront"
    with pytest.raises(ContractError):
        attest_runtime_profile(
            yaml.safe_dump(profile).encode(), contract=contract,
            trusted_deployment_root=TRUSTED_DEPLOYMENT_ROOT,
        )


def test_mount_normalization_has_no_hardcoded_user_home():
    from core.shopping import public_storefront_v2_activation_03_final_reconciliation as reconciliation
    assert "/Users/kyouhan/" not in inspect.getsource(reconciliation._canonical_mount_location)
