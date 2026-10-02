"""Read-only observation and single-Caddy-reload execution lane for Activation-02."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Protocol

from core.deployment.adapters.macos.caddy_sites import classify_caddy_sites, load_site_policy
from core.deployment.contracts import load_schema_registry, validate_contract_payload
from core.shopping.public_storefront_v2_activation_02_authorization import ConsumptionFailure, validate_consumption_result
from core.shopping.public_storefront_v2_activation_02_reconciliation import (
    ACTIVATION_BUNDLE_FILES, ARTIFACT_FILES, AUTHORITY_ID, BASE_HEAD, CADDYFILE, CADDY_POLICY,
    COMPOSE, CONTEXT, DATABASE_CONTAINER_ID, DATABASE_NETWORKS, DATABASE_VOLUME, DEV_HOST, DEV_PORT,
    EFFECTIVE_CADDY_STATE, INGRESS, MUTATION_ID, PROFILE, PROFILE_ARTIFACT, PROFILE_FILE, PUBLIC_HOST,
    PUBLIC_PORT, SHOPPING_PORT, WORDPRESS_CONTAINER_ID, WORDPRESS_NETWORKS, WORDPRESS_VOLUME,
    WORDPRESS_BIND_MOUNTS, WORDPRESS_IMAGE, DATABASE_IMAGE, canonical_json, digest_bytes, parse_preconditions,
    precondition_template, projection, validate_post_activation,
)

DOCKER = "/opt/homebrew/bin/docker"
COLIMA = "/opt/homebrew/bin/colima"
CADDY = "/opt/homebrew/bin/caddy"
RUNTIME_ROOT = Path("/Users/kyouhan/AIControlCenter")
_LIMIT = 262144


def _trusted_docker_executable() -> str:
    """Reuse the repository's fixed Homebrew Docker identity validator."""
    from ops.macos.shopping.wordpress_port_live_operator import (
        _trusted_docker_executable as resolve_trusted_docker,
    )
    return resolve_trusted_docker()


def _env() -> dict[str, str]:
    return {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", "HOME": "/var/empty", "LC_ALL": "C"}


def _runtime_env() -> dict[str, str]:
    """Use the fixed trusted account environment for local runtime readers."""
    from ops.macos.shopping.wordpress_port_live_operator import _fixed_environment
    return _fixed_environment()


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["/usr/bin/git", *args], cwd=root, env=_env(), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
    if result.returncode != 0 or len(result.stdout) > _LIMIT:
        raise RuntimeError("CANDIDATE_IDENTITY_UNAVAILABLE")
    return result.stdout.decode("ascii", errors="strict").strip()


def activation_bundle_identity(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative in ACTIVATION_BUNDLE_FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
            raise RuntimeError("ACTIVATION_BUNDLE_UNAVAILABLE")
        files[relative] = digest_bytes(path.read_bytes())
    return files


def source_identity(root: Path, *, clean_required: bool = True) -> dict[str, Any]:
    root = root.resolve(strict=True)
    status = _run_git(root, "status", "--porcelain")
    if clean_required and status:
        raise RuntimeError("CANDIDATE_NOT_CLEAN")
    head = _run_git(root, "rev-parse", "HEAD")
    if len(head) != 40 or _run_git(root, "merge-base", "--is-ancestor", BASE_HEAD, "HEAD") != "":
        # git merge-base --is-ancestor returns an empty string on success and
        # raises on failure, making a non-ancestor a value-free block.
        raise RuntimeError("CANDIDATE_BASE_MISMATCH")
    artifacts = {relative: digest_bytes((root / relative).read_bytes()) for relative in ARTIFACT_FILES}
    bundle = activation_bundle_identity(root)
    bundle_digest = hashlib.sha256(canonical_json(bundle).encode("ascii")).hexdigest()
    return {"head": head, "clean": not bool(status), "artifacts": artifacts,
            "activation_bundle_sha256": bundle_digest}


def _safe_json(raw: bytes) -> Any:
    if len(raw) > _LIMIT:
        raise RuntimeError("OBSERVATION_OVERSIZED")
    return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


class ActivationPort(Protocol):
    def observe_preconditions(self) -> dict[str, Any]: ...
    def validate_caddy_offline(self) -> bool: ...
    def reload_caddy_once(self) -> bool: ...
    def effective_caddy_v2(self) -> bool: ...
    def post_activation(self) -> dict[str, Any]: ...


@dataclass
class ActivationRunner:
    store: Any
    port: ActivationPort
    uid: int
    gid: int

    def run(self) -> dict[str, Any]:
        facts = {"fresh_pre_reload_reobservation": False, "caddy_reload_attempted": False,
                 "caddy_reload_count": 0}
        try:
            result = self.store.consume(self.port.observe_preconditions)
            receipt = validate_consumption_result(result, now=datetime.now(timezone.utc), uid=self.uid, gid=self.gid)
            bound = parse_preconditions(receipt.precondition_json)
            # This is the mandatory post-consumption read-only barrier.  No
            # reload is reachable until the complete generation and edge
            # binding is freshly equal to the consumed authority.
            if self.port.observe_preconditions() != bound:
                return projection("UNCERTAIN", authorization_consumed=True, **facts)
            facts["fresh_pre_reload_reobservation"] = True
            if not self.port.validate_caddy_offline():
                return projection("UNCERTAIN", authorization_consumed=True, **facts)
            facts["caddy_reload_attempted"] = True
            facts["caddy_reload_count"] = 1
            if not self.port.reload_caddy_once():
                return projection("UNCERTAIN", authorization_consumed=True, **facts)
            if not self.port.effective_caddy_v2():
                return projection("UNCERTAIN", authorization_consumed=True, **facts)
            post = self.port.post_activation()
            validate_post_activation(post)
            return projection("ACTIVATED", authorization_consumed=True, mutation_attempted=True,
                              **{**facts, **post})
        except ConsumptionFailure as error:
            consumed = {"NOT_CONSUMED": False, "CONSUMED": True, "UNCERTAIN": None}.get(error.state)
            return projection("BLOCKED" if consumed is False else "UNCERTAIN",
                              authorization_consumed=consumed, **facts)
        except Exception:
            return projection("UNCERTAIN", authorization_consumed=True, **facts)


class MacActivationPort:
    """Fixed Mac implementation.  It contains no runtime lifecycle command."""

    def __init__(self, *, source_root: Path, runtime_root: Path = RUNTIME_ROOT):
        self.source_root = source_root.resolve(strict=True)
        self.runtime_root = runtime_root.resolve(strict=True)
        if self.runtime_root != RUNTIME_ROOT:
            raise RuntimeError("RUNTIME_ROOT_IDENTITY_REJECTED")
        source_identity(self.source_root, clean_required=True)
        self._reload_count = 0
        self._bound_wordpress: dict[str, Any] | None = None
        self._bound_database: dict[str, Any] | None = None
        self._source: dict[str, Any] | None = None

    def _run(self, argv: list[str], *, cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
        return subprocess.run(argv, cwd=cwd, env=_runtime_env(), stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False)

    def _docker_inspect(self, identity: str) -> dict[str, Any]:
        fmt = ('{"id":{{json .Id}},"created":{{json .Created}},"image":{{json .Config.Image}},'
               '"image_id":{{json .Image}},"state":{{json .State.Status}},"running":{{json .State.Running}},'
               '"healthy":{{with (index .State "Health")}}{{json .Status}}{{else}}null{{end}},'
               '"ports":{{json .NetworkSettings.Ports}},"mounts":{{json .Mounts}},"networks":{{json .NetworkSettings.Networks}},'
               '"restart":{{json .HostConfig.RestartPolicy.Name}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
               '"service":{{json (index .Config.Labels "com.docker.compose.service")}}}')
        result = self._run([_trusted_docker_executable(), "--context", CONTEXT, "container", "inspect", "--format", fmt, identity], cwd=self.runtime_root)
        if result.returncode != 0:
            raise RuntimeError("DOCKER_INSPECTION_UNAVAILABLE")
        value = _safe_json(result.stdout)
        if type(value) is not dict:
            raise RuntimeError("DOCKER_INSPECTION_INVALID")
        return value

    def _profile_pass(self) -> bool:
        result = self._run([COLIMA, "list", "--profile", PROFILE, "--json"], cwd=self.runtime_root)
        if result.returncode != 0:
            return False
        rows = _safe_json(result.stdout)
        if isinstance(rows, dict):
            rows = [rows]
        if not (isinstance(rows, list) and len(rows) == 1 and rows[0].get("name") == PROFILE and rows[0].get("status") == "Running"):
            return False
        # Reuse the repository's strict semantic profile attestation; it only
        # reads the YAML and JSON contract and never starts or changes Colima.
        try:
            from core.shopping.public_storefront_v2_activation_03_final_reconciliation import attest_runtime_profile
            contract = json.loads((self.runtime_root / PROFILE_ARTIFACT).read_text())
            attest_runtime_profile(Path(PROFILE_FILE).read_bytes(), contract=contract,
                                   trusted_deployment_root=self.runtime_root)
            return True
        except Exception:
            return False

    def _mounts(self, raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            raise RuntimeError("MOUNT_OBSERVATION_INVALID")
        result = []
        for mount in raw:
            if type(mount) is not dict:
                raise RuntimeError("MOUNT_OBSERVATION_INVALID")
            kind = mount.get("Type")
            entry = {"type": kind, "destination": mount.get("Destination"), "rw": mount.get("RW")}
            if kind == "volume":
                entry["name"] = mount.get("Name")
                entry["source"] = None
            elif kind == "bind":
                source = Path(str(mount.get("Source", ""))).resolve(strict=False)
                try:
                    entry["source"] = source.relative_to(self.runtime_root).as_posix()
                except ValueError:
                    raise RuntimeError("BIND_MOUNT_ROOT_REJECTED") from None
                entry["name"] = None
            else:
                raise RuntimeError("MOUNT_TYPE_REJECTED")
            result.append(entry)
        return sorted(result, key=lambda item: (item["destination"], item["type"]))

    @staticmethod
    def _networks(raw: Any) -> dict[str, str]:
        if type(raw) is not dict:
            raise RuntimeError("NETWORK_OBSERVATION_INVALID")
        result = {}
        for name, metadata in raw.items():
            if type(name) is not str or type(metadata) is not dict or type(metadata.get("NetworkID")) is not str:
                raise RuntimeError("NETWORK_IDENTITY_INVALID")
            result[name] = metadata["NetworkID"]
        return result

    def _generation(self, identity: str, *, database: bool) -> dict[str, Any]:
        raw = self._docker_inspect(identity)
        ports = raw.get("ports")
        if database and isinstance(ports, dict):
            ports = {key: value for key, value in ports.items() if value not in (None, [])}
        value = {"container_id": raw.get("id"), "created": raw.get("created"), "image": raw.get("image"),
                 "image_id": raw.get("image_id"), "project": raw.get("project"), "service": raw.get("service"),
                 "running": raw.get("running"), "healthy": raw.get("healthy") == "healthy",
                 "restart_policy": raw.get("restart"), "ports": ports, "mounts": self._mounts(raw.get("mounts")),
                 "networks": self._networks(raw.get("networks"))}
        return value

    def observe_preconditions(self) -> dict[str, Any]:
        wordpress = self._generation(WORDPRESS_CONTAINER_ID, database=False)
        database = self._generation(DATABASE_CONTAINER_ID, database=True)
        networks = {name: wordpress["networks"][name] for name in WORDPRESS_NETWORKS}
        if database["networks"].get("ai-shopping-internal") != networks["ai-shopping-internal"]:
            raise RuntimeError("NETWORK_CONTINUITY_MISMATCH")
        caddy = __import__("ops.macos.shopping.public_storefront_v2_effective_caddy_observer", fromlist=["observe_pre_v2"])
        observed = caddy.observe_pre_v2(reviewed_root=self.source_root, runtime_root=self.runtime_root)
        if observed.get("status") != "PASS":
            raise RuntimeError("CADDY_PRECONDITION_UNPROVEN")
        trusted = caddy._trusted_caddy_executable()
        self._bound_wordpress, self._bound_database = wordpress, database
        source = source_identity(self.source_root, clean_required=True)
        self._source = source
        return precondition_template(
            source=source,
            colima={"profile": PROFILE, "status": "Running", "semantic_profile": "PASS"} if self._profile_pass() else
                    {"profile": PROFILE, "status": "Stopped", "semantic_profile": "BLOCKED"},
            wordpress=wordpress, database=database,
            volumes={"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME}, networks=networks,
            caddy={"state": EFFECTIVE_CADDY_STATE, "trusted_executable": trusted,
                   "listeners": ["127.0.0.1:2019", "*:58080", "*:58443"]},
        )

    def validate_caddy_offline(self) -> bool:
        try:
            caddyfile = self.runtime_root / CADDYFILE
            if self._source is None or any(
                    (self.runtime_root / relative).is_symlink() or
                    (self.runtime_root / relative).resolve(strict=True) != self.runtime_root / relative or
                    digest_bytes((self.runtime_root / relative).read_bytes()) != digest
                    for relative, digest in self._source["artifacts"].items()):
                return False
            policy = load_site_policy((self.runtime_root / CADDY_POLICY).read_text())
            ingress = json.loads((self.runtime_root / INGRESS).read_text())
            validate_contract_payload(registry=load_schema_registry(), contract_name="CaddySitePolicy", payload=policy)
            classification = classify_caddy_sites(caddyfile.read_text(), policy=policy, ingress_contract=ingress)
            if not (classification.production.hostname == PUBLIC_HOST and classification.production.port == PUBLIC_PORT and
                    classification.production.authentication_required is False and classification.preview is not None and
                    classification.preview.hostname == DEV_HOST and classification.preview.port == DEV_PORT and
                    classification.preview.authentication_required is True):
                return False
            result = self._run([CADDY, "validate", "--config", str(caddyfile), "--adapter", "caddyfile"], cwd=self.runtime_root)
            return result.returncode == 0
        except Exception:
            return False

    def reload_caddy_once(self) -> bool:
        if self._reload_count:
            return False
        self._reload_count = 1
        try:
            result = self._run([CADDY, "reload", "--config", str(self.runtime_root / CADDYFILE), "--adapter", "caddyfile"], cwd=self.runtime_root)
            return result.returncode == 0
        except Exception:
            return False

    def effective_caddy_v2(self) -> bool:
        try:
            return self._effective_caddy_proof()["loaded_config_matches_reviewed_adaptation"]
        except Exception:
            return False

    def _effective_caddy_proof(self) -> dict[str, bool]:
        caddy = __import__("ops.macos.shopping.public_storefront_v2_effective_caddy_observer", fromlist=["observe_caddy_effective_v2"])
        result = caddy.observe_caddy_effective_v2(reviewed_root=self.source_root, runtime_root=self.runtime_root)
        if result.get("status") != "PASS":
            raise RuntimeError("CADDY_V2_PROOF_UNAVAILABLE")
        return {key: result[key] for key in caddy._PROOF_KEYS if type(result.get(key)) is bool}

    def post_activation(self) -> dict[str, Any]:
        current_wp = self._generation(WORDPRESS_CONTAINER_ID, database=False)
        current_db = self._generation(DATABASE_CONTAINER_ID, database=True)
        proof = self._effective_caddy_proof()
        return {"loaded_v2": proof["loaded_config_matches_reviewed_adaptation"],
                "public_host": PUBLIC_HOST if proof["production_host"] else "",
                "public_root": "127.0.0.1:58082" if proof["public_root_upstream"] else "",
                "public_root_upstream": proof["public_root_upstream"],
                "shopping_read_upstream": proof["shopping_read_upstream"],
                "shopping_get_allowlist": proof["public_get_allowlist_matcher_loaded"] and proof["shopping_read_upstream"],
                "public_basic_auth_absent": proof["public_has_no_basic_auth"],
                "dev_basic_auth_preserved": proof["dev_basic_auth_loaded"],
                "management_denied": proof["private_management_matcher_loaded"],
                "wordpress_private_denied": proof["wordpress_rest_matcher_loaded"],
                "rest_route_guard": proof["raw_query_rest_route_ambiguity_guard_loaded"],
                "shopping_writes_not_proxied": proof["shopping_writes_not_proxied"],
                "legacy_redirect": proof["legacy_redirect_loaded"],
                "wordpress_generation_unchanged": current_wp == self._bound_wordpress,
                "database_generation_unchanged": current_db == self._bound_database,
                "colima_lifecycle_mutation": False, "caddy_reload_count": self._reload_count}


def run(*, source_root: Path, runtime_root: Path = RUNTIME_ROOT) -> dict[str, Any]:
    source_identity(source_root, clean_required=True)
    owner = os.getuid(), os.getgid()
    from ops.macos.shopping.public_storefront_v2_activation_02_authorization_store import PublicStorefrontV2ActivationAuthorizationStore
    store = PublicStorefrontV2ActivationAuthorizationStore.open_existing()
    return ActivationRunner(store, MacActivationPort(source_root=source_root, runtime_root=runtime_root), *owner).run()


def main() -> int:
    print(json.dumps(projection("CALLER_OVERRIDE_REJECTED"), sort_keys=True, separators=(",", ":")))
    return 2


__all__ = ["ActivationPort", "ActivationRunner", "MacActivationPort", "activation_bundle_identity", "main", "run", "source_identity"]


if __name__ == "__main__":
    raise SystemExit(main())
