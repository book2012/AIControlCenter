"""Zero-argument Mac-only observation. Run with python -m ops.macos.shopping.effective_runtime_attestor.

No WordPress bootstrap, PHP application execution, credentials, logs, environment
inspection or remediation. File observations NEVER establish loaded SAPI state.
Unbound deployment identities and serving generations remain explicitly unproven.
"""
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time

from core.shopping.control_plane_read.effective_runtime import CHECKS, reduce_evidence
from core.shopping.control_plane_read.runtime_components import CATEGORIES
from core.shopping.control_plane_read import transport
from ops.macos.shopping import preactivation_observer as repository

LIMIT = 131072
TOTAL_SECONDS = 30.0
CADDY = "/opt/homebrew/bin/caddy"
ENV = {"PATH": "/usr/bin:/bin", "HOME": "/var/empty",
       "DOCKER_CONFIG": "/var/empty/aicc-runtime-attestation-no-config",
       "LC_ALL": "C"}
CONTAINER_FORMAT = (
    '{"id":{{json .Id}},"started":{{json .State.StartedAt}},'
    '"running":{{json .State.Running}},"ports":{{json .NetworkSettings.Ports}},'
    '"mode":{{json .HostConfig.NetworkMode}},"networks":{{json .NetworkSettings.Networks}},'
    '"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
    '"service":{{json (index .Config.Labels "com.docker.compose.service")}}}'
)
NETWORK_FORMAT = ('{"internal":{{json .Internal}},"name":{{json .Name}},"id":{{json .Id}},'
                  '"project":{{json (index .Labels "com.docker.compose.project")}}}')


WORDPRESS_IMAGE = "wordpress:php8.3-apache@sha256:9fac4d47b61186131ffefb5d966f0045d0eea94bfd7bd40cafae29b78a709d1b"
BINDING_FORMAT = (
    '{"id":{{json .Id}},"image":{{json .Image}},"configured_image":{{json .Config.Image}},'
    '"started":{{json .State.StartedAt}},"running":{{json .State.Running}},'
    '"paused":{{json .State.Paused}},"restarting":{{json .State.Restarting}},'
    '"pid":{{json .State.Pid}},"restart_count":{{json .RestartCount}},'
    '"mounts":{{json .Mounts}}}'
)
IMAGE_FORMAT = '{"id":{{json .Id}},"digests":{{json .RepoDigests}}}'


def _normalize_mounts(raw):
    """Project Docker identity fields only; metadata cannot supply proof policy."""
    if type(raw) is not list:
        return None
    required = {"Type", "Source", "Destination", "RW"}
    mounts, destinations = [], set()
    for item in raw:
        if (type(item) is not dict or not required <= item.keys()
                or any(type(item[key]) is not str for key in ("Type", "Source", "Destination"))
                or type(item["RW"]) is not bool
                or item["Type"] not in ("volume", "bind")
                or any(not item[key] for key in ("Type", "Source", "Destination"))
                or item["Destination"] in destinations):
            return None
        name = item.get("Name", "")
        if type(name) is not str or (item["Type"] == "volume" and not name):
            return None
        destinations.add(item["Destination"])
        mounts.append(dict(type=item["Type"], name=name, source=item["Source"],
                           destination=item["Destination"], rw=item["RW"]))
    return mounts


def _deployment_binding(before, after, image_before, image_after, topology, safe):
    """Bind inspect identities only; stability is neither freshness nor SAPI provenance."""
    result = dict.fromkeys(CHECKS["deployment_identity"], False)
    result["reviewed_pinned_identity_contract"] = safe is True
    result["expected_immutable_wordpress_image"] = safe is True
    keys = {"id", "image", "configured_image", "started", "running", "paused",
            "restarting", "pid", "restart_count", "mounts"}
    if (type(before) is not dict or set(before) != keys or before != after
            or not topology or not all(topology.values()) or before["running"] is not True
            or before["paused"] is not False or before["restarting"] is not False
            or type(before["pid"]) is not int or before["pid"] <= 0
            or type(before["restart_count"]) is not int or before["restart_count"] < 0
            or type(before["id"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", before["id"])
            or type(before["started"]) is not str or not re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{1,9}Z", before["started"])
            or before["started"].startswith("0001-")):
        return result
    result["container_identity_bound"] = True
    result["runtime_generation_identity_bound"] = True
    result["actual_runtime_image_matches"] = (
        safe is True and before["configured_image"] == WORDPRESS_IMAGE
        and type(image_before) is dict and set(image_before) == {"id", "digests"}
        and image_before == image_after and type(image_before["id"]) is str
        and re.fullmatch(r"sha256:[0-9a-f]{64}", image_before["id"]) is not None
        and before["image"] == image_before["id"]
        and type(image_before["digests"]) is list
        and "wordpress@" + WORDPRESS_IMAGE.split("@", 1)[1] in image_before["digests"])
    expected = [dict(type="volume", name="ai-shopping-wordpress",
                     destination="/var/www/html", rw=True)]
    for source, destination in (
        ("config/shopping-apache-safety.conf", "/etc/apache2/sites-available/000-default.conf"),
        ("config/shopping-php-safety.ini", "/usr/local/etc/php/conf.d/zz-shopping-safety.ini"),
        ("wordpress/plugins/ai-shopping-storefront", "/var/www/html/wp-content/plugins/ai-shopping-storefront"),
    ):
        expected.append(dict(type="bind", name="", source=str(repository.ROOT / "deploy/shopping" / source),
                             destination=destination, rw=False))
    mounts = _normalize_mounts(before["mounts"])
    if (safe is True and mounts is not None and len(mounts) == len(expected)
            and all(sum(all(m[k] == v for k, v in e.items()) for m in mounts) == 1 for e in expected)):
        result["expected_mounts_config_bound"] = True
    # A read-only bind identifies the mount, not immutable bytes or loaded state.
    # The writable WordPress volume also prevents executable-config closure.
    return result


class EvidenceError(Exception):
    """Carries only a fixed reason code; raw tool errors never escape."""


def _json(raw):
    if len(raw) > LIMIT:
        raise EvidenceError("STDOUT_OVERSIZED")
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise EvidenceError("DUPLICATE_JSON_KEYS")
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if type(value) is not dict:
            raise ValueError()
        return value
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("MALFORMED_JSON") from None


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise EvidenceError("TOTAL_DEADLINE_EXCEEDED")
    return remaining


def _run(argv, deadline):
    """Private fixed-command runner: cap memory while reading, kill on deadline.

    Unlike communicate()/run(PIPE), an oversized producer cannot accumulate
    unbounded output before its size is checked. No shell or inherited stdin.
    """
    _remaining(deadline)
    end = min(deadline, time.monotonic() + 5.0)
    process = None
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, env=ENV, close_fds=True)
        raw = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                if not selector.select(max(0, end - time.monotonic())):
                    raise EvidenceError("SUBPROCESS_TIMEOUT")
                block = os.read(process.stdout.fileno(), min(8192, LIMIT + 1 - len(raw)))
                raw.extend(block)
                if len(raw) > LIMIT:
                    raise EvidenceError("STDOUT_OVERSIZED")
                if not block:
                    break
                if time.monotonic() >= end:
                    raise EvidenceError("SUBPROCESS_TIMEOUT")
        if process.wait(timeout=max(0.001, end - time.monotonic())):
            raise EvidenceError("SUBPROCESS_NONZERO")
        _remaining(deadline)
        return bytes(raw)
    except subprocess.TimeoutExpired:
        raise EvidenceError("SUBPROCESS_TIMEOUT") from None
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("INSPECTION_UNAVAILABLE") from None
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=1)
            finally:
                process.stdout.close()


def _topology(wp, db, internal, external):
    result = {key: False for key in CHECKS["topology"]}
    result["mac_only_proven"] = True  # called only after trusted Mac resolution
    def container(value, service):
        return (type(value) is dict and set(value) == {
            "id", "started", "running", "ports", "mode", "networks", "project", "service"}
            and value["running"] is True and value["project"] == "ai-shopping"
            and value["service"] == service and type(value["id"]) is str and bool(value["id"])
            and type(value["started"]) is str and bool(value["started"])
            and value["mode"] in ("ai-shopping-internal", "ai-shopping-network")
            and type(value["networks"]) is dict and type(value["ports"]) is dict)
    def network(value, name, is_internal):
        return (type(value) is dict and set(value) == {"internal", "name", "id", "project"}
                and value["name"] == name and value["internal"] is is_internal
                and value["project"] == "ai-shopping" and type(value["id"]) is str and bool(value["id"]))
    wp_ok, db_ok = container(wp, "wordpress"), container(db, "database")
    result["wordpress_identity_proven"], result["database_identity_proven"] = wp_ok, db_ok
    result["wordpress_loopback_58082_proven"] = wp_ok and wp["ports"] == {
        "80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]}
    result["mariadb_no_published_ports_proven"] = db_ok and all(v is None for v in db["ports"].values())
    result["internal_network_proven"] = network(internal, "ai-shopping-internal", True)
    if (wp_ok and db_ok and result["internal_network_proven"]
            and network(external, "ai-shopping-network", False)):
        def attached(value, expected):
            return set(value["networks"]) == set(expected) and all(
                type(value["networks"][name]) is dict
                and value["networks"][name].get("NetworkID") == identity
                for name, identity in expected.items())
        result["expected_networks_proven"] = attached(wp, {
            "ai-shopping-internal": internal["id"], "ai-shopping-network": external["id"]
        }) and attached(db, {"ai-shopping-internal": internal["id"]})
    return result


def _host_pid(raw):
    """All three fixed listeners must belong to one host Caddy process.

    Admin must bind IPv4 loopback exactly. Extra/duplicate listeners fail closed.
    """
    try:
        lines = raw.decode("ascii").splitlines()
        pids = [line[1:] for line in lines if line.startswith("p")]
        commands = [line[1:] for line in lines if line.startswith("c")]
        names = [line[1:] for line in lines if line.startswith("n")]
        if (len(pids) != 1 or not pids[0].isdigit() or commands != ["caddy"]
                or len(names) != 3 or "127.0.0.1:2019" not in names
                or sorted(name.rsplit(":", 1)[-1] for name in names) != ["2019", "58080", "58443"]
                or any(line[:1] not in ("p", "c", "n", "f") for line in lines)):
            return None
        return pids[0]
    except Exception:
        return None


def _caddy_proofs(loaded, adapted, identity, repository_safe):
    # Complete equality with the digest-bound reviewed adaptation rejects extra
    # servers/handlers, reordered denies, changed upstreams, or any logger change.
    # Adaptation by itself can never pass: loaded admin JSON and host identity
    # are independently required. Empty/ambiguous documents cannot pass.
    authoritative = identity is True and type(loaded) is dict and type(loaded.get("apps")) is dict and bool(loaded["apps"])
    safe = authoritative and repository_safe is True and type(adapted) is dict and loaded == adapted
    result = {key: safe for key in CHECKS["caddy_effective"]}
    result["loaded_config_proven"] = authoritative
    result["host_edge_identity_proven"] = identity is True
    return result


def _admin_json(raw):
    body, separator, status = raw.rpartition(b"\n")
    if not separator or status != b"200":
        raise EvidenceError("INSPECTION_UNAVAILABLE")
    return _json(body)


def observe():
    deadline = time.monotonic() + TOTAL_SECONDS
    facts, errors = {}, []
    manifest = None
    observed_components = dict.fromkeys(CATEGORIES, None)  # unknown, never an empty inventory
    if sys.platform != "darwin":
        return reduce_evidence({}, ["MAC_IDENTITY_UNPROVEN"])
    try:
        socket = repository._socket()  # passwd/UID resolver, never ambient HOME
    except Exception:
        return reduce_evidence({}, ["MAC_IDENTITY_UNPROVEN"])
    try:
        with (repository.ROOT / "config/deployment/shopping-runtime-component-manifest.json").open("rb") as stream:
            manifest = _json(stream.read(LIMIT + 1))
        safe = all((repository.ROOT / path).stat().st_size <= LIMIT for path in
                   repository.ARTIFACTS | {"config/deployment/shopping-logging-policy.json"}) and repository._repository_facts()
        facts["repository_invariants"] = dict(
            reviewed_edge_policy_valid=safe, reviewed_safety_controls_valid=safe,
            # Reviewed digests do not close the full route/proxy inventory.
            no_generic_proxy_or_caller_target=False, no_public_observation_endpoint=False,
        )
        adapter = transport.ControlPlaneShoppingReadAdapter
        facts["transport"] = dict(
            repository_controls_proven=safe,
            literal_loopback_proven=safe and transport.HOST == "127.0.0.1",
            port_58082_proven=safe and transport.PORT == 58082,
            fixed_target_proven=safe and transport.REST_PATH == repository.NAMESPACE + "products",
            trust_env_false_proven=safe and adapter.trust_env is False,
            redirects_disabled_proven=safe and adapter.redirects is False,
            retries_zero_proven=safe and type(adapter.max_retries) is int and adapter.max_retries == 0,
            total_deadline_enforced=safe and transport.TOTAL_TIMEOUT == 5.0,
            response_bounded_proven=safe and transport.MAX_RESPONSE_BYTES == 32768,
        )
        prefix = [repository.DOCKER, "--host", socket]
        targets = ("shopping-wordpress", "shopping-db", "ai-shopping-internal", "ai-shopping-network")
        commands = [prefix + (["inspect", "--format", CONTAINER_FORMAT] if index < 2
                    else ["network", "inspect", "--format", NETWORK_FORMAT]) + [name]
                    for index, name in enumerate(targets)]
        def read(command):
            try:
                return _json(_run(command, deadline))
            except EvidenceError as exc:
                errors.append(exc.args[0])
                return None
        binding_command = prefix + ["inspect", "--format", BINDING_FORMAT, "shopping-wordpress"]
        image_command = prefix + ["image", "inspect", "--format", IMAGE_FORMAT, WORDPRESS_IMAGE]
        binding_before, image_before = read(binding_command), read(image_command)
        metadata = [read(command) for command in commands]
        facts["topology"] = _topology(*metadata)
        listeners = ["/usr/sbin/lsof", "-nP", "-iTCP:2019", "-iTCP:58080", "-iTCP:58443",
                     "-sTCP:LISTEN", "-Fpcn"]
        try:
            before = _run(listeners, deadline)
            pid = _host_pid(before)
            identity = False
            if pid is not None:
                executable = _run(["/usr/sbin/lsof", "-a", "-p", pid, "-d", "txt", "-Fn"], deadline)
                identity = ("n" + str(Path(CADDY).resolve(strict=True))) in executable.decode("utf-8").splitlines()
            if not identity:
                errors.append("CADDY_HOST_PROCESS_UNPROVEN")
            else:
                admin = ["/usr/bin/curl", "-q", "--silent", "--fail", "--noproxy", "*",
                         "--proxy", "", "--max-time", "4", "--max-filesize", str(LIMIT),
                         "--proto", "=http", "--write-out", "\n%{http_code}",
                         "http://127.0.0.1:2019/config/"]
                loaded = _admin_json(_run(admin, deadline))
                adapted = read([CADDY, "adapt", "--config", str(repository.ROOT / "ops/macos/caddy/Caddyfile"),
                                "--adapter", "caddyfile"])
                stable = loaded == _admin_json(_run(admin, deadline)) and before == _run(listeners, deadline)
                facts["caddy_effective"] = _caddy_proofs(loaded, adapted, identity and stable, safe)
                if not all(facts["caddy_effective"].values()):
                    errors.append("CADDY_LOADED_CONFIG_MISMATCH")
        except EvidenceError as exc:
            errors.append(exc.args[0])
        metadata_after = [read(command) for command in commands]
        binding_after, image_after = read(binding_command), read(image_command)
        if metadata != metadata_after:
            facts["topology"] = {}
            errors.append("UNEXPECTED_EVIDENCE")
        binding_topology = facts["topology"]
        if (not metadata or type(metadata[0]) is not dict or type(binding_before) is not dict
                or metadata[0].get("id") != binding_before.get("id")
                or metadata[0].get("started") != binding_before.get("started")):
            binding_topology = {"wordpress_identity_proven": False}
        facts["deployment_identity"] = _deployment_binding(
            binding_before, binding_after, image_before, image_after, binding_topology, safe)
        errors.extend(("RUNTIME_BINDING_UNPROVEN", "SERVING_GENERATION_PROVENANCE_UNPROVEN"))
        _remaining(deadline)
    except EvidenceError as exc:
        errors.append(exc.args[0])
    except Exception:
        errors.append("INSPECTION_UNAVAILABLE")
    # Repository manifest is not an observed inventory. No current mechanism
    # establishes the closed deployment controls or actual component bindings.
    return reduce_evidence(facts, errors, manifest=manifest, observed_components=observed_components)


def main():
    try:
        result = reduce_evidence({}, ["CALLER_OVERRIDE_REJECTED"]) if len(sys.argv) != 1 else observe()
    except Exception:
        result = reduce_evidence({}, ["INSPECTION_UNAVAILABLE"])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
