"""Pure contract for PUBLIC-STOREFRONT-V2-ACTIVATION-01.

This module contains identities and validators only.  It deliberately has no
process, filesystem, network, Docker, Colima, Caddy, or authorization-store
side effects.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode


AUTHORITY_ID = "PUBLIC-STOREFRONT-V2-ACTIVATION-01"
AUTHORITATIVE_WORK_ITEM = AUTHORITY_ID
MUTATION_ID = AUTHORITY_ID + ":ONE_SHOT_PUBLIC_RUNTIME_AND_CADDY_ACTIVATION"

# This is intentionally closed and excludes the digest-bearing contract value
# itself.  The source HEAD is obtained from Git at issuance time; the bundle
# digest therefore remains valid after the activation mechanism is committed.
ACTIVATION_BUNDLE_FILES = (
    "core/shopping/public_storefront_v2_activation_03_final_authorization.py",
    "core/shopping/public_storefront_v2_activation_03_final_reconciliation.py",
    "ops/macos/shopping/PUBLIC_STOREFRONT_V2_ACTIVATION_03_FINAL.md",
    "ops/macos/shopping/issue_public_storefront_v2_activation_03_final_authorization.py",
    "ops/macos/shopping/public_storefront_v2_activation_03_final_authorization_store.py",
    "ops/macos/shopping/public_storefront_v2_activation_03_final_operator.py",
    "ops/macos/shopping/public_storefront_v2_effective_caddy_observer.py",
)

PROFILE = "aicontrolcenter-commerce"
PROFILE_FILE = "/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml"
PROFILE_ARTIFACT = "ops/macos/colima/commerce-runtime.json"
PROFILE_SHA256 = "61a9194ab22dfff9515d44d3d41af9eafdf3647e8ee5d6f0cb6fe92f77f473ea"

CADDYFILE = "ops/macos/caddy/Caddyfile"
CADDYFILE_SHA256 = "78515f55e58bc2ad159d7cbdcf329bee975b73b05ac540857ae251bd9d725882"
CADDY_POLICY = "config/deployment/caddy-site-policy.json"
CADDY_POLICY_SHA256 = "c6fe2d3f0d34236d073ea1120c47b5d06c723f6068e7986f55f362a5f97ebfbd"
INGRESS = "config/deployment/ingress.json"
INGRESS_SHA256 = "a6da9a7dfa8bce1aa9f73aa255c1dfd3d24aa089ba13914deaea142c9182fe35"
COMPOSE = "deploy/shopping/compose.yaml"
COMPOSE_SHA256 = "0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c"
STOREFRONT_PLUGIN = "deploy/shopping/wordpress/plugins/ai-shopping-storefront/ai-shopping-storefront.php"
STOREFRONT_PLUGIN_SHA256 = "6367e13a2fa20c848976c17091cc6d0e956cc1f01f2315680d8d36c45f3383a5"
API_CLIENT = "deploy/shopping/wordpress/plugins/ai-shopping-storefront/includes/class-api-client.php"
API_CLIENT_SHA256 = "f409aa3df07a72055ea4790dcff47fe0112fba72567dd11f780cb8de895500e7"
BROWSER_STOREFRONT = "core/homepage/ui/storefront.js"
BROWSER_STOREFRONT_SHA256 = "0f7c425bbb366f0597db9b74f6bfb09ebc5c02b119379019825f6f2adb30f08b"
WORDPRESS_STOREFRONT_UI = "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-ui.js"
WORDPRESS_STOREFRONT_UI_SHA256 = "ca0df28ac5dfc92cedc6e79b91af587f6e1b3ee7cfbbfbb49b004c9facf50491"

ARTIFACTS = {
    CADDYFILE: CADDYFILE_SHA256,
    CADDY_POLICY: CADDY_POLICY_SHA256,
    INGRESS: INGRESS_SHA256,
    COMPOSE: COMPOSE_SHA256,
    STOREFRONT_PLUGIN: STOREFRONT_PLUGIN_SHA256,
    API_CLIENT: API_CLIENT_SHA256,
    BROWSER_STOREFRONT: BROWSER_STOREFRONT_SHA256,
    WORDPRESS_STOREFRONT_UI: WORDPRESS_STOREFRONT_UI_SHA256,
    PROFILE_ARTIFACT: PROFILE_SHA256,
}

PUBLIC_HOST = "bokstory.duckdns.org"
DEV_HOST = "dev.bokstory.duckdns.org"
PUBLIC_PORT = 58082
CONTROL_PLANE_PORT = 58081
DEV_PORT = 18080
EXPECTED_PORTS = {
    "control_plane": CONTROL_PLANE_PORT,
    "wordpress": PUBLIC_PORT,
    "dev": DEV_PORT,
}
POLICY_VERSION = "public-storefront-migration/v2"
EFFECTIVE_CADDY_STATE = "PRE_V2"

CONTEXT = "colima-aicontrolcenter-commerce"
WORDPRESS_CONTAINER_ID = "43d8d4f9e370ac066a77cbf1b346002df6d11cff00e3212bc0a3c6b668745648"
DATABASE_CONTAINER_ID = "434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323"
WORDPRESS_VOLUME = "ai-shopping-wordpress"
DATABASE_VOLUME = "ai-shopping-database"

# These are reviewed/durable generation identities.  They are deliberately
# not obtained from Docker in Phase A: a Broken Colima profile has no usable
# Docker endpoint.  Phase B re-reads the live identities and compares them to
# these bindings before any WordPress start is permitted.
EXPECTED_VOLUME_NAMES = {
    "wordpress": WORDPRESS_VOLUME,
    "database": DATABASE_VOLUME,
}

MAXIMUM_USES = 1
MAXIMUM_LIFETIME_SECONDS = 600

_RUNTIME_CONTRACT_KEYS = (
    "ai_workloads_allowed", "allowed_workloads", "architecture", "auto_activate",
    "cpus", "disk_gib", "docker_context", "kubernetes", "memory_gib",
    "mount_policy", "mount_type", "mounts", "network_address", "network_mode",
    "port_forwarder", "profile", "public_ingress_owner", "purpose", "runtime",
    "schema_version", "ssh_agent", "ubuntu_runtime_allowed", "vm_type",
    "wordpress_host_binding",
)
_COLIMA_ROOT_KEYS = frozenset({
    "arch", "autoActivate", "binfmt", "cpu", "cpuType", "disk", "diskImage", "memory",
    "docker", "env", "forceDiskImage", "forwardAgent", "hostname", "kubernetes",
    "mountInotify", "mountType", "mounts", "nestedVirtualization", "network",
    "portForwarder", "provision", "rosetta", "rootDisk", "runtime", "sshConfig",
    "sshPort", "vmType", "modelRunner",
})
_NETWORK_KEYS = frozenset({
    "address", "dns", "dnsHosts", "gatewayAddress", "hostAddresses", "interface",
    "mode", "preferredRoute",
})
_KUBERNETES_KEYS = frozenset({"enabled", "k3sArgs", "port", "version"})
_SEMANTIC_REQUIRED_ROOT_KEYS = frozenset({
    "arch", "autoActivate", "cpu", "disk", "forwardAgent", "kubernetes", "memory",
    "mountType", "mounts", "network", "portForwarder", "runtime", "vmType",
})
_SECURITY_DEFAULTS = {
    "binfmt": True,
    "cpuType": "",
    "diskImage": "",
    "docker": {},
    "env": {},
    "forceDiskImage": False,
    "mountInotify": False,
    "modelRunner": "docker",
    "nestedVirtualization": False,
    "provision": None,
    "rosetta": False,
    "rootDisk": 20,
    "sshConfig": True,
    "sshPort": 0,
}


class ContractError(ValueError):
    """The value-free contract failure crossing this boundary."""


def require(condition: bool) -> None:
    if not condition:
        raise ContractError("PUBLIC_STOREFRONT_V2_CONTRACT_REJECTED")


def _keys(value: Any, expected: tuple[str, ...]) -> None:
    require(type(value) is dict and tuple(sorted(value)) == tuple(sorted(expected)))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_bytes(raw: bytes) -> str:
    require(type(raw) is bytes and len(raw) <= 262144)
    return hashlib.sha256(raw).hexdigest()


def _strict_yaml(raw: bytes) -> dict[str, Any]:
    """Parse Colima YAML without allowing syntax to hide semantic drift."""
    require(type(raw) is bytes and 0 < len(raw) <= 262144)
    try:
        text = raw.decode("utf-8")
        for token in yaml.scan(text):
            require(not isinstance(token, (yaml.tokens.AliasToken,
                                           yaml.tokens.AnchorToken,
                                           yaml.tokens.TagToken)))
        node = yaml.compose(text, Loader=yaml.SafeLoader)

        def unique(value: Any) -> None:
            if isinstance(value, MappingNode):
                seen: set[str] = set()
                for key, child in value.value:
                    require(isinstance(key, ScalarNode) and
                            key.tag == "tag:yaml.org,2002:str" and
                            key.value not in seen and key.value != "<<")
                    seen.add(key.value)
                    unique(child)
            elif isinstance(value, SequenceNode):
                for child in value.value:
                    unique(child)

        require(isinstance(node, MappingNode))
        unique(node)
        value = yaml.safe_load(text)
    except Exception:
        raise ContractError("PUBLIC_STOREFRONT_V2_PROFILE_REJECTED") from None
    require(type(value) is dict and all(type(key) is str for key in value))
    return value


def _require_exact_mapping(value: Any, keys: frozenset[str]) -> dict[str, Any]:
    require(type(value) is dict and set(value) == keys)
    return value


def _require_mapping_subset(value: Any, allowed: frozenset[str], required: frozenset[str]) -> dict[str, Any]:
    require(type(value) is dict and set(value) <= allowed and required <= set(value))
    return value


def _canonical_mount_location(value: Any) -> str:
    require(type(value) is str and value and "\\" not in value)
    path = Path(value)
    require(path.is_absolute() and not any(part in ("", ".", "..") for part in path.parts))
    return str(path)


def _trusted_deployment_root(value: Any) -> Path:
    """Validate the explicit root used to interpret live absolute mounts."""
    require(isinstance(value, Path))
    root = Path(_canonical_mount_location(str(value)))
    require(root != Path("/"))
    return root


def _project_live_mount_location(value: Any, *, trusted_deployment_root: Path) -> str:
    location = Path(_canonical_mount_location(value))
    root = _trusted_deployment_root(trusted_deployment_root)
    try:
        logical = location.relative_to(root)
    except ValueError:
        raise ContractError("PUBLIC_STOREFRONT_V2_MOUNT_ROOT_REJECTED") from None
    require(logical != Path("."))
    require(not any(part in ("", ".", "..") for part in logical.parts))
    return logical.as_posix()


def _contract_mounts(contract: dict[str, Any]) -> list[dict[str, Any]]:
    mounts = contract["mounts"]
    require(type(mounts) is list and mounts)
    result: list[dict[str, Any]] = []
    for mount in mounts:
        mount_value = _require_exact_mapping(mount, frozenset({"path", "writable"}))
        path = mount_value["path"]
        require(type(path) is str and path and "\\" not in path and not Path(path).is_absolute())
        require(not any(part in ("", ".", "..") for part in Path(path).parts))
        require(type(mount_value["writable"]) is bool and mount_value["writable"] is False)
        result.append({
            # Durable semantic identity is contract-relative.  A checkout or
            # deployment root is bound only while interpreting live YAML.
            "location": Path(path).as_posix(),
            "writable": False,
        })
    require(len({mount["location"] for mount in result}) == len(result))
    return result


def desired_runtime_projection(contract: Any) -> dict[str, Any]:
    """Project the JSON-first runtime contract into activation semantics."""
    contract = _require_exact_mapping(contract, frozenset(_RUNTIME_CONTRACT_KEYS))
    require(contract["schema_version"] == 1)
    require(contract["profile"] == PROFILE and contract["runtime"] == "docker")
    require(contract["architecture"] == "aarch64" and contract["vm_type"] == "vz")
    require(contract["mount_type"] == "virtiofs" and
            contract["mount_policy"] == "explicit-compose-bind-allowlist")
    require(contract["cpus"] == 4 and contract["memory_gib"] == 6 and contract["disk_gib"] == 80)
    require(contract["network_address"] is False and contract["network_mode"] == "shared")
    require(contract["port_forwarder"] == "ssh" and contract["auto_activate"] is False)
    require(contract["kubernetes"] is False and contract["ssh_agent"] is False)
    require(contract["ai_workloads_allowed"] is False and contract["ubuntu_runtime_allowed"] is False)
    require(contract["public_ingress_owner"] == "host-caddy")
    require(contract["allowed_workloads"] == ["wordpress", "woocommerce", "database", "wordpress-cli"])
    require(contract["wordpress_host_binding"] == "127.0.0.1:58082:80")
    return {
        "cpus": contract["cpus"],
        "memory_gib": contract["memory_gib"],
        "disk_gib": contract["disk_gib"],
        "architecture": contract["architecture"],
        "runtime": contract["runtime"],
        "vm_type": contract["vm_type"],
        "mount_type": contract["mount_type"],
        "network_address": contract["network_address"],
        "network_mode": contract["network_mode"],
        "network_host_addresses": False,
        "network_preferred_route": False,
        # The JSON contract has no custom DNS fields.  The safe semantic value
        # is therefore Colima's explicit no-custom-DNS form, not an omitted
        # comparison against arbitrary live resolver settings.
        "dns": None,
        "dns_hosts": {},
        "port_forwarder": contract["port_forwarder"],
        "auto_activate": contract["auto_activate"],
        "kubernetes": contract["kubernetes"],
        "ssh_agent": contract["ssh_agent"],
        "mounts": _contract_mounts(contract),
    }


def observed_runtime_projection(raw: bytes, *, trusted_deployment_root: Path) -> dict[str, Any]:
    """Project live semantics, binding absolute mounts to the trusted root."""
    value = _strict_yaml(raw)
    require(set(value) <= _COLIMA_ROOT_KEYS and _SEMANTIC_REQUIRED_ROOT_KEYS <= set(value))
    for name, expected in _SECURITY_DEFAULTS.items():
        if name in value:
            require(value[name] == expected)

    network = _require_mapping_subset(
        value["network"], _NETWORK_KEYS,
        frozenset({"address", "dns", "dnsHosts", "hostAddresses", "mode"}),
    )
    require(type(network["address"]) is bool and type(network["hostAddresses"]) is bool)
    require(type(network["mode"]) is str)
    require(type(network.get("preferredRoute", False)) is bool and
            network.get("preferredRoute", False) is False)
    require(network["dns"] is None or (type(network["dns"]) is list and
                                        all(type(item) is str for item in network["dns"])))
    require(type(network["dnsHosts"]) is dict and
            all(type(key) is str and type(item) is str for key, item in network["dnsHosts"].items()))
    kubernetes = _require_mapping_subset(value["kubernetes"], _KUBERNETES_KEYS,
                                         frozenset({"enabled"}))
    require(type(kubernetes["enabled"]) is bool)
    mounts = value["mounts"]
    require(type(mounts) is list)
    observed_mounts: list[dict[str, Any]] = []
    for mount in mounts:
        mount_value = _require_exact_mapping(mount, frozenset({"location", "writable"}))
        require(type(mount_value["writable"]) is bool)
        observed_mounts.append({
            "location": _project_live_mount_location(
                mount_value["location"], trusted_deployment_root=trusted_deployment_root,
            ),
            "writable": mount_value["writable"],
        })
    require(len({mount["location"] for mount in observed_mounts}) == len(observed_mounts))
    require(type(value["cpu"]) is int and type(value["memory"]) is int and type(value["disk"]) is int)
    require(type(value["arch"]) is str and type(value["runtime"]) is str and
            type(value["vmType"]) is str and type(value["mountType"]) is str and
            type(value["portForwarder"]) is str)
    for name in ("autoActivate", "forwardAgent"):
        require(type(value[name]) is bool)
    return {
        "cpus": value["cpu"],
        "memory_gib": value["memory"],
        "disk_gib": value["disk"],
        "architecture": value["arch"],
        "runtime": value["runtime"],
        "vm_type": value["vmType"],
        "mount_type": value["mountType"],
        "network_address": network["address"],
        "network_mode": network["mode"],
        "network_host_addresses": network["hostAddresses"],
        "network_preferred_route": network.get("preferredRoute", False),
        "dns": network["dns"],
        "dns_hosts": network["dnsHosts"],
        "port_forwarder": value["portForwarder"],
        "auto_activate": value["autoActivate"],
        "kubernetes": kubernetes["enabled"],
        "ssh_agent": value["forwardAgent"],
        "mounts": observed_mounts,
    }


def attest_runtime_profile(raw: bytes, *, contract: Any,
                           trusted_deployment_root: Path) -> dict[str, Any]:
    """Return the observed projection only when it exactly matches desired semantics."""
    desired = desired_runtime_projection(contract)
    observed = observed_runtime_projection(raw, trusted_deployment_root=trusted_deployment_root)
    require(observed == desired)
    return observed


_CONTRACT_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT_DATA = json.loads((_CONTRACT_ROOT / PROFILE_ARTIFACT).read_text(encoding="utf-8"))
EXPECTED_RUNTIME_SEMANTIC_PROJECTION = desired_runtime_projection(
    _CONTRACT_DATA,
)


def validate_source_identity(value: Any, *, clean_required: bool = True) -> None:
    _keys(value, ("head", "clean", "artifacts", "activation_bundle_sha256"))
    require(type(value["head"]) is str and re.fullmatch(r"[0-9a-f]{40}", value["head"]))
    require(type(value["activation_bundle_sha256"]) is str and
            re.fullmatch(r"[0-9a-f]{64}", value["activation_bundle_sha256"]))
    require(type(value["clean"]) is bool and (value["clean"] is clean_required or not clean_required))
    _keys(value["artifacts"], tuple(ARTIFACTS))
    require(value["artifacts"] == ARTIFACTS)


def precondition_template(*, source: dict[str, Any], colima: dict[str, Any],
                          forwarding: dict[str, Any], wordpress: dict[str, Any],
                          database: dict[str, Any]) -> dict[str, Any]:
    """Build the closed precondition shape used by issuers and test seams."""
    value = {
        "source": source,
        "desired": {
            "policy_version": POLICY_VERSION,
            "public_host": PUBLIC_HOST,
            "dev_host": DEV_HOST,
            "public_upstream": "127.0.0.1:58082",
            "shopping_api_upstream": "127.0.0.1:58081",
            "dev_upstream": "127.0.0.1:18080",
        },
        "effective": {"caddy_state": EFFECTIVE_CADDY_STATE},
        "colima": colima,
        "forwarding": forwarding,
        "wordpress": wordpress,
        "database": database,
        "volumes": {"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME},
        "ports": EXPECTED_PORTS,
        "authority": {
            "ubuntu_authority": False,
            "business_mutation_authority": False,
            "database_recreation_allowed": False,
            "volume_recreation_allowed": False,
            "woo_write_authority": False,
        },
    }
    validate_preconditions(value)
    return value


def validate_preconditions(value: Any) -> None:
    _keys(value, ("source", "desired", "effective", "colima", "forwarding",
                  "wordpress", "database", "volumes", "ports", "authority"))
    validate_source_identity(value["source"])
    _keys(value["desired"], ("policy_version", "public_host", "dev_host",
                               "public_upstream", "shopping_api_upstream", "dev_upstream"))
    require(value["desired"] == {
        "policy_version": POLICY_VERSION,
        "public_host": PUBLIC_HOST,
        "dev_host": DEV_HOST,
        "public_upstream": "127.0.0.1:58082",
        "shopping_api_upstream": "127.0.0.1:58081",
        "dev_upstream": "127.0.0.1:18080",
    })
    _keys(value["effective"], ("caddy_state",))
    require(value["effective"]["caddy_state"] == EFFECTIVE_CADDY_STATE)
    _keys(value["colima"], ("profile", "profile_file", "semantic_projection", "status"))
    require(value["colima"] == {
        "profile": PROFILE, "profile_file": PROFILE_FILE,
        "semantic_projection": EXPECTED_RUNTIME_SEMANTIC_PROJECTION, "status": "Broken",
    })
    _keys(value["forwarding"], ("owner", "profile", "host", "port", "required_for_lifecycle"))
    require(value["forwarding"] == {
        "owner": "colima", "profile": PROFILE, "host": "127.0.0.1",
        "port": PUBLIC_PORT, "required_for_lifecycle": True,
    })
    _keys(value["wordpress"], ("container_id", "state", "running", "published"))
    require(value["wordpress"] == {
        "container_id": WORDPRESS_CONTAINER_ID, "state": "created",
        "running": False, "published": "127.0.0.1:58082->80/tcp",
    })
    _keys(value["database"], ("container_id", "state", "healthy", "published", "volume"))
    require(value["database"] == {
        "container_id": DATABASE_CONTAINER_ID, "state": "running",
        "healthy": True, "published": False, "volume": DATABASE_VOLUME,
    })
    require(value["volumes"] == {"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME})
    require(value["ports"] == EXPECTED_PORTS)
    require(value["authority"] == {
        "ubuntu_authority": False, "business_mutation_authority": False,
        "database_recreation_allowed": False, "volume_recreation_allowed": False,
        "woo_write_authority": False,
    })


def parse_preconditions(raw: str) -> dict[str, Any]:
    require(type(raw) is str and len(raw) <= 32768)
    try:
        value = json.loads(raw)
    except Exception:
        raise ContractError("PUBLIC_STOREFRONT_V2_CONTRACT_REJECTED") from None
    validate_preconditions(value)
    require(canonical_json(value) == raw)
    return value


def validate_post_activation(value: Any) -> None:
    _keys(value, ("public", "shopping_reads", "product_catalog", "private_boundary", "dev",
                  "legacy", "direct_browser_woo_denied", "wordpress_loopback",
                  "server_side_api", "database_continuity", "effective_caddy_v2",
                  "rest_route_live_proof", "product_detail_dynamic_id",
                  "public_commerce_write_request", "caddy_reload_count"))
    require(value["public"] == {"https_success": True, "basic_auth": False,
                                 "storefront_rendered": True})
    _keys(value["shopping_reads"], ("categories", "search", "featured_products", "products"))
    require(value["shopping_reads"] == {
        "categories": True, "search": True, "featured_products": True,
        "products": True,
    })
    require(value["product_catalog"] in ("VALID_NONEMPTY", "VALID_EMPTY"))
    require(value["private_boundary"] == {
        "wordpress_paths_denied": True, "rest_routes_denied": True,
        "management_paths_denied": True, "shopping_writes_not_proxied": True,
        "order_payment_cart_checkout_not_proxied": True,
    })
    require(value["dev"] == {"https_success": False, "basic_auth_required": True,
                               "production_never_uses_dev": True})
    require(value["legacy"] == {"path": "/homepage/storefront", "status": 301,
                                 "location": "/"})
    require(value["direct_browser_woo_denied"] is True)
    require(value["wordpress_loopback"] == "127.0.0.1:58082")
    require(value["server_side_api"] == "127.0.0.1:58081")
    require(value["database_continuity"] is True)
    require(value["effective_caddy_v2"] is True)
    require(value["rest_route_live_proof"] is True)
    require(value["product_detail_dynamic_id"] is (value["product_catalog"] == "VALID_NONEMPTY"))
    require(value["public_commerce_write_request"] == "NOT_PERFORMED")
    require(value["caddy_reload_count"] == 1)


def projection(status: str, *, authorization_consumed: bool | None = False,
               mutation_attempted: bool = False, **facts: Any) -> dict[str, Any]:
    """Safe result projection: no command output, credentials, or response bodies."""
    result = {
        "status": status,
        "authority_id": AUTHORITY_ID,
        "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
        "mutation_id": MUTATION_ID,
        "authorization_consumed": authorization_consumed,
        "mutation_attempted": mutation_attempted,
        "maximum_uses": MAXIMUM_USES,
        "activation_authority": True,
        "lifecycle_authority": True,
        "caddy_reload_authority": True,
        "production_write_authority": False,
        "business_mutation_authority": False,
        "ubuntu_authority": False,
        "database_recreation_allowed": False,
        "volume_recreation_allowed": False,
        "dns_change_allowed": False,
        "woo_write_authority": False,
        "automatic_retry": False,
        "automatic_rollback": False,
    }
    result.update(facts)
    return result


__all__ = [
    "API_CLIENT", "ARTIFACTS", "AUTHORITY_ID", "AUTHORITATIVE_WORK_ITEM",
    "BROWSER_STOREFRONT", "WORDPRESS_STOREFRONT_UI",
    "ACTIVATION_BUNDLE_FILES", "CADDYFILE", "CADDYFILE_SHA256", "CADDY_POLICY", "COMPOSE",
    "CONTEXT", "CONTROL_PLANE_PORT", "ContractError", "DATABASE_CONTAINER_ID",
    "DATABASE_VOLUME", "DEV_HOST", "DEV_PORT", "EFFECTIVE_CADDY_STATE",
    "EXPECTED_PORTS", "EXPECTED_VOLUME_NAMES", "INGRESS", "MAXIMUM_LIFETIME_SECONDS", "MAXIMUM_USES",
    "MUTATION_ID", "POLICY_VERSION", "PROFILE", "PROFILE_FILE", "PROFILE_SHA256",
    "PUBLIC_HOST", "PUBLIC_PORT", "STOREFRONT_PLUGIN", "WORDPRESS_CONTAINER_ID",
    "WORDPRESS_VOLUME", "canonical_json", "digest_bytes", "parse_preconditions",
    "precondition_template", "projection", "validate_post_activation",
    "validate_preconditions", "validate_source_identity",
]
