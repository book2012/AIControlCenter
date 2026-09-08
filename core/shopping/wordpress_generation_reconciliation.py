"""01G1C identity contract. No live calls, business mutations or 01B authority."""
from __future__ import annotations

import json
import re
import stat
from pathlib import Path

from core.shopping.wordpress_port_reconciliation import (
    AuthorizationConsumptionState, ExecutionOutcome, MutationInvocation,
    COMPOSE_FILE, COMPOSE_PROJECT, COMPOSE_SERVICE, TARGET_CONTEXT,
    DATABASE_CONTAINER, WORDPRESS_CONTAINER, ENVIRONMENT,
    build_mutation_invocation,
)

AUTHORITATIVE_WORK_ITEM = "SHOP-SERVICE-START-01G1C"
MUTATION_ID = AUTHORITATIVE_WORK_ITEM + ":WORDPRESS_RUNTIME_GENERATION_RECONCILIATION"
EXPECTED_BEFORE_BINDING = EXPECTED_AFTER_BINDING = "127.0.0.1:58082->80/tcp"
ROOT = Path(__file__).resolve().parents[2]
WORDPRESS_IMAGE = "wordpress:php8.3-apache@sha256:9fac4d47b61186131ffefb5d966f0045d0eea94bfd7bd40cafae29b78a709d1b"
ARTIFACTS = {
    COMPOSE_FILE: "341c9dfcd69cb001bc9514d34427335a47b1b4dcad6d95cb40072752a1643f8b",
    "deploy/shopping/config/shopping-apache-safety.conf": "b9b6ee7bbe7649d6e2392658c8b06af08f392bdb7807c9c69e8eadf1ac0261b9",
    "deploy/shopping/config/shopping-php-safety.ini": "7c1a0eb3f858102b9f14db79e4e279fc2f0403f5c2b4e034d81b5f325a18c7eb",
}
VOLUMES = ("ai-shopping-wordpress", "ai-shopping-database")
NETWORKS = ("ai-shopping-internal", "ai-shopping-network")


def require(condition):
    if not condition:
        raise ValueError("GENERATION_IDENTITY_REJECTED")


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected.split()))


def matches(value, pattern):
    return type(value) is str and re.fullmatch(pattern, value) is not None


def timestamp(value):
    require(matches(value, r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?(?:Z|[+-][0-9]{2}:[0-9]{2})") and not value.startswith("0001-"))


def volume_mount(name, destination):
    return dict(type="volume", name=name, source=f"/var/lib/docker/volumes/{name}/_data", destination=destination, rw=True)


def expected_mounts(post):
    mounts = [volume_mount(VOLUMES[0], "/var/www/html")]
    binds = [("wordpress/plugins/ai-shopping-storefront", "/var/www/html/wp-content/plugins/ai-shopping-storefront")]
    if post:
        binds += [("config/shopping-apache-safety.conf", "/etc/apache2/sites-enabled/000-default.conf"),
                  ("config/shopping-php-safety.ini", "/usr/local/etc/php/conf.d/zz-shopping-safety.ini")]
    return mounts + [dict(type="bind", name="", source=str(ROOT / "deploy/shopping" / source), destination=destination, rw=False) for source, destination in binds]


def validate_snapshot(value, *, post=False):
    """Closed schema: only constrained non-secret identities may be persisted."""
    keys(value, "head clean artifacts wordpress database image volumes networks source_metadata production ubuntu")
    require(matches(value["head"], r"[0-9a-f]{40}") and value["clean"] is True)
    require(value["production"] is False and value["ubuntu"] is False)
    require(value["artifacts"] == ARTIFACTS)
    keys(value["source_metadata"], "st_dev st_ino st_mode st_uid st_gid st_size st_nlink st_mtime_ns st_ctime_ns")
    require(all(type(v) is int and v >= 0 for v in value["source_metadata"].values()))
    metadata = value["source_metadata"]
    require(stat.S_ISREG(metadata["st_mode"]) and stat.S_IMODE(metadata["st_mode"]) & ~0o600 == 0
            and metadata["st_nlink"] == 1 and 0 < metadata["st_size"] <= 65536)
    keys(value["image"], "id digest")
    require(matches(value["image"]["id"], r"sha256:[0-9a-f]{64}"))
    require(value["image"]["digest"] == "wordpress@" + WORDPRESS_IMAGE.split("@", 1)[1])
    require(type(value["volumes"]) is dict and set(value["volumes"]) == set(VOLUMES))
    for name, volume in value["volumes"].items():
        keys(volume, "Name Driver Scope CreatedAt")
        require(volume["Name"] == name and volume["Driver"] == "local" and volume["Scope"] == "local")
        timestamp(volume["CreatedAt"])
    require(type(value["networks"]) is dict and set(value["networks"]) == set(NETWORKS))
    for name, network in value["networks"].items():
        keys(network, "id internal")
        require(matches(network["id"], r"[0-9a-f]{64}") and network["internal"] is (name == NETWORKS[0]))
    require(value["networks"][NETWORKS[0]]["id"] != value["networks"][NETWORKS[1]]["id"])
    for service in ("wordpress", "database"):
        container = value[service]
        keys(container, "id started restart_count running healthy paused restarting image configured_image project service ports networks mounts")
        require(matches(container["id"], r"[0-9a-f]{64}"))
        timestamp(container["started"])
        require(type(container["restart_count"]) is int and container["restart_count"] >= 0)
        require(container["running"] is True and container["healthy"] is True and container["paused"] is False and container["restarting"] is False)
        require(container["project"] == COMPOSE_PROJECT and container["service"] == service)
        require(matches(container["image"], r"sha256:[0-9a-f]{64}"))
        if service == "wordpress":
            require(container["image"] == value["image"]["id"] and container["configured_image"] == WORDPRESS_IMAGE)
            require(container["ports"] == {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]})
            mounts = expected_mounts(post)
            networks = NETWORKS
        else:
            require(container["configured_image"] == "mariadb:11.4.12@sha256:a794d9eb009e20de605858a11f32f63b4075cbd197c650436f0e3b457e4caed7")
            require(type(container["ports"]) is dict and all(matches(k, r"[0-9]{1,5}/(?:tcp|udp)") and v is None for k, v in container["ports"].items()))
            mounts = [volume_mount(VOLUMES[1], "/var/lib/mysql")]
            networks = NETWORKS[:1]
        require(container["networks"] == {name: value["networks"][name]["id"] for name in networks})
        require(type(container["mounts"]) is list and len(container["mounts"]) == len(mounts))
        for mount in container["mounts"]:
            keys(mount, "type name source destination rw")
            require(type(mount["rw"]) is bool)
        require(all(container["mounts"].count(mount) == 1 for mount in mounts))
    require(value["wordpress"]["id"] != value["database"]["id"])


def canonical_snapshot(value):
    validate_snapshot(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def parse_binding(raw):
    require(type(raw) is str and len(raw) <= 16384)
    value = json.loads(raw)
    require(canonical_snapshot(value) == raw)
    return value


def validate_post(before, after):
    validate_snapshot(before)
    validate_snapshot(after, post=True)
    require(before["wordpress"]["id"] != after["wordpress"]["id"])
    for name in before.keys() - {"wordpress"}:
        require(before[name] == after[name])


def projection(status, *, consumed=False, attempted=False):
    """Never include observations, exception text, process output or receipts."""
    return dict(status=status, mutation_id=MUTATION_ID,
                authorization_consumed=consumed, mutation_attempted=attempted,
                production_authority=False, ubuntu_authority=False,
                database_recreation_allowed=False, volume_recreation_allowed=False,
                unrelated_service_mutation_allowed=False,
                automatic_retry=False, automatic_rollback=False,
                backup_restore_proven=False, content_preservation_proven=False,
                loaded_apache_state_proven=False, loaded_php_state_proven=False,
                public_edge_isolation_proven=False, deployment_logging_safety_proven=False,
                component_inventory_complete=False, authenticated_shopping_read_performed=False,
                shopping_soft_launch_ready=False, business_mutation_authority=False,
                entrypoint_and_healthcheck_startup_writes_possible=True)
