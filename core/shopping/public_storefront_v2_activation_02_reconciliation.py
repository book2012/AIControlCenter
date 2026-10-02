"""Pure Activation-02 contract for the already-running commerce generation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


AUTHORITY_ID = "PUBLIC-STOREFRONT-V2-ACTIVATION-02"
AUTHORITATIVE_WORK_ITEM = AUTHORITY_ID
MUTATION_ID = AUTHORITY_ID + ":ONE_SHOT_CADDY_V2_CUTOVER"
BASE_HEAD = "e19202e79a3a90d1365926fc4bcc48eb77c8cb15"

PROFILE = "aicontrolcenter-commerce"
PROFILE_FILE = "/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml"
CONTEXT = "colima-aicontrolcenter-commerce"
PUBLIC_HOST = "bokstory.duckdns.org"
DEV_HOST = "dev.bokstory.duckdns.org"
PUBLIC_PORT = 58082
SHOPPING_PORT = 58081
DEV_PORT = 18080
EFFECTIVE_CADDY_STATE = "PRE_V2"
MAXIMUM_USES = 1
MAXIMUM_LIFETIME_SECONDS = 600

# This is a reviewed runtime anchor, not the generation binding.  Every
# mutable generation property is also captured from Docker and rebound in the
# durable precondition document before issuance.
WORDPRESS_CONTAINER_ID = "0636d4cad86d31f0119ccadb1c83ef59ea4b2192bdd74b3f459c2947d24f2a0e"
DATABASE_CONTAINER_ID = "434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323"
WORDPRESS_VOLUME = "ai-shopping-wordpress"
DATABASE_VOLUME = "ai-shopping-database"
WORDPRESS_IMAGE = "wordpress:php8.3-apache@sha256:9fac4d47b61186131ffefb5d966f0045d0eea94bfd7bd40cafae29b78a709d1b"
DATABASE_IMAGE = "mariadb:11.4.12@sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7"
WORDPRESS_BIND_MOUNTS = (
    ("deploy/shopping/config/shopping-apache-safety.conf", "/etc/apache2/sites-available/000-default.conf", False),
    ("deploy/shopping/config/shopping-php-safety.ini", "/usr/local/etc/php/conf.d/zz-shopping-safety.ini", False),
    ("deploy/shopping/wordpress/plugins/ai-shopping-storefront", "/var/www/html/wp-content/plugins/ai-shopping-storefront", False),
)
WORDPRESS_NETWORKS = ("ai-shopping-internal", "ai-shopping-network")
DATABASE_NETWORKS = ("ai-shopping-internal",)

CADDYFILE = "ops/macos/caddy/Caddyfile"
CADDY_POLICY = "config/deployment/caddy-site-policy.json"
INGRESS = "config/deployment/ingress.json"
COMPOSE = "deploy/shopping/compose.yaml"
PROFILE_ARTIFACT = "ops/macos/colima/commerce-runtime.json"
ARTIFACT_FILES = (CADDYFILE, CADDY_POLICY, INGRESS, COMPOSE, PROFILE_ARTIFACT)
ACTIVATION_BUNDLE_FILES = (
    "core/shopping/public_storefront_v2_activation_02_authorization.py",
    "core/shopping/public_storefront_v2_activation_02_reconciliation.py",
    "ops/macos/shopping/PUBLIC_STOREFRONT_V2_ACTIVATION_02.md",
    "ops/macos/shopping/issue_public_storefront_v2_activation_02_authorization.py",
    "ops/macos/shopping/public_storefront_v2_activation_02_authorization_store.py",
    "ops/macos/shopping/public_storefront_v2_activation_02_operator.py",
    "ops/macos/shopping/public_storefront_v2_effective_caddy_observer.py",
)


class ContractError(ValueError):
    pass


def require(condition: bool) -> None:
    if not condition:
        raise ContractError("PUBLIC_STOREFRONT_V2_ACTIVATION_02_CONTRACT_REJECTED")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_bytes(raw: bytes) -> str:
    require(type(raw) is bytes and len(raw) <= 262144)
    return hashlib.sha256(raw).hexdigest()


def _keys(value: Any, expected: tuple[str, ...]) -> None:
    require(type(value) is dict and tuple(sorted(value)) == tuple(sorted(expected)))


def _hex(value: Any, length: int) -> None:
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None)


def _generation(value: Any, *, database: bool) -> None:
    _keys(value, ("container_id", "created", "image", "image_id", "project", "service",
                  "running", "healthy", "restart_policy", "ports", "mounts", "networks"))
    _hex(value["container_id"], 64)
    require(type(value["created"]) is str and value["created"])
    require(value["image"] == (DATABASE_IMAGE if database else WORDPRESS_IMAGE))
    require(type(value["image_id"]) is str and value["image_id"].startswith("sha256:"))
    _hex(value["image_id"][len("sha256:"):], 64)
    require(value["project"] == "ai-shopping" and value["service"] == ("database" if database else "wordpress"))
    require(type(value["running"]) is bool and type(value["healthy"]) is bool)
    require(value["running"] is True and value["healthy"] is True)
    require(value["restart_policy"] == ("unless-stopped" if database else "no"))
    require(type(value["ports"]) is dict)
    require(type(value["networks"]) is dict)
    for network_id in value["networks"].values():
        _hex(network_id, 64)
    if database:
        require(value["ports"] == {})
        require(value["mounts"] == [{"type": "volume", "name": DATABASE_VOLUME, "source": None,
                                     "destination": "/var/lib/mysql", "rw": True}])
        require(tuple(sorted(value["networks"])) == tuple(sorted(DATABASE_NETWORKS)))
    else:
        require(value["ports"] == {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]})
        mounts = value["mounts"]
        require(type(mounts) is list and len(mounts) == 4)
        require({(m["type"], m.get("name"), m.get("source"), m["destination"], m["rw"]) for m in mounts} == {
            ("volume", WORDPRESS_VOLUME, None, "/var/www/html", True),
            *(('bind', None, source, destination, rw) for source, destination, rw in WORDPRESS_BIND_MOUNTS),
        })
        require(tuple(sorted(value["networks"])) == tuple(sorted(WORDPRESS_NETWORKS)))


def validate_source(value: Any) -> None:
    _keys(value, ("head", "clean", "artifacts", "activation_bundle_sha256"))
    require(type(value["head"]) is str and re.fullmatch(r"[0-9a-f]{40}", value["head"]))
    require(value["head"] != "")
    require(value["clean"] is True)
    require(type(value["artifacts"]) is dict and tuple(sorted(value["artifacts"])) == tuple(sorted(ARTIFACT_FILES)))
    for digest in value["artifacts"].values():
        _hex(digest, 64)
    _hex(value["activation_bundle_sha256"], 64)


def precondition_template(*, source: dict[str, Any], colima: dict[str, Any],
                          wordpress: dict[str, Any], database: dict[str, Any],
                          volumes: dict[str, str], networks: dict[str, str],
                          caddy: dict[str, Any]) -> dict[str, Any]:
    value = {
        "source": source,
        "desired": {"public_host": PUBLIC_HOST, "public_root": "127.0.0.1:58082",
                     "shopping_get_upstream": "127.0.0.1:58081", "dev_host": DEV_HOST,
                     "dev_upstream": "127.0.0.1:18080"},
        "colima": colima,
        "wordpress": wordpress,
        "database": database,
        "volumes": volumes,
        "networks": networks,
        "caddy": caddy,
        "authority": {"colima_restart": False, "wordpress_runtime_mutation": False,
                       "database_recreation": False, "volume_recreation": False,
                       "ubuntu": False, "woo_write": False, "dns_change": False},
    }
    validate_preconditions(value)
    return value


def validate_preconditions(value: Any) -> None:
    _keys(value, ("source", "desired", "colima", "wordpress", "database", "volumes", "networks", "caddy", "authority"))
    validate_source(value["source"])
    require(value["desired"] == {"public_host": PUBLIC_HOST, "public_root": "127.0.0.1:58082",
                                  "shopping_get_upstream": "127.0.0.1:58081", "dev_host": DEV_HOST,
                                  "dev_upstream": "127.0.0.1:18080"})
    _keys(value["colima"], ("profile", "status", "semantic_profile"))
    require(value["colima"] == {"profile": PROFILE, "status": "Running", "semantic_profile": "PASS"})
    _generation(value["wordpress"], database=False)
    _generation(value["database"], database=True)
    require(value["volumes"] == {"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME})
    require(type(value["networks"]) is dict and set(value["networks"]) == set(WORDPRESS_NETWORKS))
    for network_id in value["networks"].values():
        _hex(network_id, 64)
    _keys(value["caddy"], ("state", "trusted_executable", "listeners"))
    require(value["caddy"]["state"] == EFFECTIVE_CADDY_STATE and
            value["caddy"]["trusted_executable"].startswith("/opt/homebrew/Cellar/caddy/") and
            value["caddy"]["trusted_executable"].endswith("/bin/caddy") and
            value["caddy"]["listeners"] == ["127.0.0.1:2019", "*:58080", "*:58443"])
    require(value["authority"] == {"colima_restart": False, "wordpress_runtime_mutation": False,
                                    "database_recreation": False, "volume_recreation": False,
                                    "ubuntu": False, "woo_write": False, "dns_change": False})


def parse_preconditions(raw: str) -> dict[str, Any]:
    require(type(raw) is str and len(raw) <= 65536)
    try:
        value = json.loads(raw)
    except Exception:
        raise ContractError("PUBLIC_STOREFRONT_V2_ACTIVATION_02_CONTRACT_REJECTED") from None
    validate_preconditions(value)
    require(canonical_json(value) == raw)
    return value


def validate_post_activation(value: Any) -> None:
    _keys(value, ("loaded_v2", "public_host", "public_root", "public_root_upstream", "shopping_read_upstream",
                  "shopping_get_allowlist", "public_basic_auth_absent",
                  "dev_basic_auth_preserved", "management_denied", "wordpress_private_denied",
                  "rest_route_guard", "shopping_writes_not_proxied", "legacy_redirect", "wordpress_generation_unchanged",
                  "database_generation_unchanged", "colima_lifecycle_mutation", "caddy_reload_count"))
    require(value == {"loaded_v2": True, "public_host": PUBLIC_HOST, "public_root": "127.0.0.1:58082",
                      "public_root_upstream": True, "shopping_read_upstream": True,
                      "shopping_get_allowlist": True, "public_basic_auth_absent": True,
                      "dev_basic_auth_preserved": True, "management_denied": True,
                      "wordpress_private_denied": True, "rest_route_guard": True,
                      "shopping_writes_not_proxied": True, "legacy_redirect": True,
                      "wordpress_generation_unchanged": True, "database_generation_unchanged": True,
                      "colima_lifecycle_mutation": False, "caddy_reload_count": 1})


def projection(status: str, *, authorization_consumed: bool | None = False,
               mutation_attempted: bool = False, **facts: Any) -> dict[str, Any]:
    result = {"status": status, "authority_id": AUTHORITY_ID, "mutation_id": MUTATION_ID,
              "authorization_consumed": authorization_consumed, "mutation_attempted": mutation_attempted,
              "maximum_uses": MAXIMUM_USES, "maximum_lifetime_seconds": MAXIMUM_LIFETIME_SECONDS,
              "colima_restart_authority": False, "wordpress_runtime_mutation_authority": False,
              "database_recreation_authority": False, "volume_recreation_authority": False,
              "ubuntu_authority": False, "woo_write_authority": False, "dns_change_authority": False,
              "automatic_retry": False, "automatic_rollback": False, "caddy_reload_max": 1}
    result.update(facts)
    return result


__all__ = [name for name in globals() if name.isupper()] + [
    "ContractError", "canonical_json", "digest_bytes", "parse_preconditions",
    "precondition_template", "projection", "validate_post_activation", "validate_preconditions",
]
