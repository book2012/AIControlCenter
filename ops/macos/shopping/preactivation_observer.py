"""Zero-argument Mac observer of repository readiness and selected local metadata.

PASS means repository controls and container topology are ready for a separately
controlled verification step. It never attests loaded Caddy, persisted wp-config,
PHP extensions or active plugins. Those remain an explicit activation blocker.
No environment inspection, logs, HTTP probes, retries or mutation commands.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.shopping.control_plane_read.preactivation import NAMESPACE, _evaluate
from core.shopping.control_plane_read import transport

DOCKER = "/opt/homebrew/bin/docker"
ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = frozenset((
    "ops/macos/caddy/Caddyfile", "config/deployment/ingress.json",
    "deploy/shopping/compose.yaml", "ops/macos/colima/commerce-runtime.json",
    "deploy/shopping/config/shopping-apache-safety.conf",
    "deploy/shopping/config/shopping-php-safety.ini",
    "deploy/shopping/wordpress/plugins/ai-controlcenter-shopping-read/ai-controlcenter-shopping-read.php",
    "core/shopping/control_plane_read/transport.py",
))
FALSE_POLICY_FIELDS = (
    "access_authorization_capture", "error_authorization_projection",
    "WP_DEBUG", "WP_DEBUG_LOG", "WP_DEBUG_DISPLAY", "request_tracing_enabled",
    "apm_enabled", "plugin_header_logging", "plugin_capability_logging",
    "plugin_verifier_logging", "production_authority", "ubuntu_authority",
)
FORMAT = ('{"running":{{json .State.Running}},'
          '"ports":{{json .NetworkSettings.Ports}},'
          '"mode":{{json .HostConfig.NetworkMode}},'
          '"networks":{{json .NetworkSettings.Networks}},'
          '"project":{{json (index .Config.Labels "com.docker.compose.project")}}}')
NETWORK_FORMAT = '{"internal":{{json .Internal}},"name":{{json .Name}},"id":{{json .Id}}}'


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous evidence")
        result[key] = value
    return result


def _json(text):
    return json.loads(text, object_pairs_hook=_unique_object)


def _socket():
    home = resolve_trusted_mac_account_home()
    return "unix://" + str(Path(home.passwd_home) / ".colima/aicontrolcenter-commerce/docker.sock")


def _read_metadata(target):
    if target not in ("shopping-wordpress", "shopping-db", "ai-shopping-internal"):
        return None
    try:
        command = [DOCKER, "--host", _socket()]
        if target == "ai-shopping-internal":
            command += ["network", "inspect", "--format", NETWORK_FORMAT, target]
        else:
            command += ["inspect", "--format", FORMAT, target]
        result = subprocess.run(
            command, env={"PATH": "/usr/bin:/bin", "HOME": "/var/empty",
                          "DOCKER_CONFIG": "/var/empty/aicc-preactivation-no-config"},
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        if result.returncode or len(result.stdout) > 8192:
            return None
        value = _json(result.stdout)
        return value if type(value) is dict else None
    except Exception:
        return None


def _metadata(container):
    value = _read_metadata(container)
    if (value is not None and set(value) == {"running", "ports", "mode", "project", "networks"}
            and value["running"] is True and value["project"] == "ai-shopping"
            and value["mode"] in ("ai-shopping-internal", "ai-shopping-network")
            and type(value["ports"]) is dict and type(value["networks"]) is dict):
        return value
    return None


def _repository_facts():
    """Reviewed digests bind policy to complete files, rejecting ambiguous additions.

    These are versioned source identities, never mutable runtime status evidence.
    Changes require review and updating the policy's artifact digests together.
    """
    try:
        policy = _json((ROOT / "config/deployment/shopping-logging-policy.json").read_text())
        if (policy.get("schema_version") != 1 or policy.get("kind") != "repository-safety-policy"
                or policy.get("namespace") != NAMESPACE
                or any(policy.get(key) is not False for key in FALSE_POLICY_FIELDS)
                or policy.get("exception_projection") != "generic-value-free"
                or policy.get("activation_requires_effective_runtime_attestation") is not True):
            return False
        artifacts = policy.get("reviewed_repository_artifacts")
        if type(artifacts) is not dict or set(artifacts) != ARTIFACTS:
            return False
        for name, digest in artifacts.items():
            path = ROOT / name
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                return False
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                return False
        ingress = _json((ROOT / "config/deployment/ingress.json").read_text())
        return (ingress["upstream"]["port"] == 58082
                and ingress["upstream"]["host"] == "127.0.0.1")
    except Exception:
        return False


def observe():
    facts = {"namespace": NAMESPACE}
    repository = _repository_facts()
    facts["repository_controls_verified"] = repository
    facts["direct_validation_loopback_only"] = (
        transport.HOST == "127.0.0.1" and transport.PORT == 58082
        and transport.REST_PATH == NAMESPACE + "products"
        and transport.ControlPlaneShoppingReadAdapter.max_retries == 0)
    wordpress = database = None
    if sys.platform == "darwin":
        wordpress = _metadata("shopping-wordpress")
        database = _metadata("shopping-db")
        network = _read_metadata("ai-shopping-internal")
        facts["mac_only_path_verified"] = True
        facts["wordpress_loopback_only"] = wordpress is not None and wordpress["ports"] == {
            "80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]}
        facts["mariadb_internal_only"] = (
            database is not None and all(value is None for value in database["ports"].values())
            and set(database["networks"]) == {"ai-shopping-internal"}
            and type(network) is dict and set(network) == {"internal", "name", "id"}
            and network["internal"] is True and network["name"] == "ai-shopping-internal"
            and type(database["networks"]["ai-shopping-internal"]) is dict
            and type(network["id"]) is str and bool(network["id"])
            and network["id"] == database["networks"]["ai-shopping-internal"].get("NetworkID"))
        facts["runtime_evidence_complete"] = (
            wordpress is not None and database is not None
            and set(wordpress["networks"]) == {"ai-shopping-internal", "ai-shopping-network"}
            and all(type(v) is dict and bool(v.get("NetworkID"))
                    for v in wordpress["networks"].values())
            and type(database["networks"].get("ai-shopping-internal")) is dict
            and wordpress["networks"]["ai-shopping-internal"].get("NetworkID")
            == database["networks"]["ai-shopping-internal"].get("NetworkID"))
    result = _evaluate(facts)
    result["local_container_metadata_available"] = wordpress is not None and database is not None
    result["mariadb_has_no_published_ports"] = (
        database is not None and all(value is None for value in database["ports"].values()))
    return result


def main():
    if len(sys.argv) != 1:
        result = _evaluate({})
        result["reason_codes"] = ["CALLER_OVERRIDE_REJECTED"]
    else:
        result = observe()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
