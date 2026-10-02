"""Mac-only execution lane for PUBLIC-STOREFRONT-V2-ACTIVATION-01.

The lane is intentionally narrow.  It has no Compose-up, volume, database,
WooCommerce, SSH, Ubuntu, DNS, or generic remote-command capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from core.deployment.adapters.macos.caddy_sites import classify_caddy_sites, load_site_policy
from core.deployment.contracts import load_schema_registry, validate_contract_payload
from core.shopping.public_storefront_v2_activation_03_final_authorization import (
    ConsumptionFailure, validate_consumption_result,
)
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    ACTIVATION_BUNDLE_FILES, API_CLIENT, ARTIFACTS, AUTHORITY_ID, BROWSER_STOREFRONT, CADDYFILE, CADDYFILE_SHA256,
    CADDY_POLICY, COMPOSE, COMPOSE_SHA256, CONTEXT, CONTROL_PLANE_PORT, DATABASE_CONTAINER_ID,
    DATABASE_VOLUME, DEV_HOST, DEV_PORT, EFFECTIVE_CADDY_STATE, EXPECTED_PORTS,
    INGRESS, INGRESS_SHA256, MUTATION_ID, POLICY_VERSION, PROFILE, PROFILE_ARTIFACT,
    PROFILE_FILE, PUBLIC_HOST, PUBLIC_PORT, STOREFRONT_PLUGIN, WORDPRESS_CONTAINER_ID,
    WORDPRESS_STOREFRONT_UI, WORDPRESS_VOLUME, canonical_json, digest_bytes, parse_preconditions,
    attest_runtime_profile, projection, validate_post_activation, validate_preconditions,
    validate_source_identity,
)
from ops.macos.shopping.public_storefront_v2_activation_03_final_authorization_store import (
    PublicStorefrontV2ActivationAuthorizationStore,
)


RUNTIME_ROOT = Path("/Users/kyouhan/AIControlCenter")
COLIMA = "/opt/homebrew/bin/colima"
DOCKER = "/opt/homebrew/bin/docker"
CADDY = "/opt/homebrew/bin/caddy"
_HTTP_LIMIT = 262144


def _fixed_environment() -> dict[str, str]:
    return {
        "HOME": "/Users/kyouhan",
        "USER": "kyouhan",
        "LOGNAME": "kyouhan",
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "DOCKER_CONFIG": "/Users/kyouhan/.docker",
        "LC_ALL": "C",
    }


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(root), *args], cwd=root,
        env={"PATH": "/usr/bin:/bin", "HOME": "/var/empty", "GIT_CONFIG_NOSYSTEM": "1"},
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=10, check=False,
    )
    if result.returncode != 0 or len(result.stdout) > 65536:
        raise RuntimeError("GIT_SOURCE_IDENTITY_UNAVAILABLE")
    return result.stdout.decode("utf-8", errors="strict").strip()


def _reviewed_file_digest(root: Path, relative: str) -> str:
    path = root / relative
    if (path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path or
            not path.resolve().is_relative_to(root)):
        raise RuntimeError("REVIEWED_ARTIFACT_UNSAFE")
    return digest_bytes(path.read_bytes())


def activation_bundle_identity(root: Path) -> dict[str, Any]:
    """Hash the closed activation mechanism and reviewed runtime file set."""
    root = root.resolve(strict=True)
    mechanism = {relative: _reviewed_file_digest(root, relative)
                 for relative in ACTIVATION_BUNDLE_FILES}
    runtime = {}
    for relative, expected in sorted(ARTIFACTS.items()):
        actual = _reviewed_file_digest(root, relative)
        if actual != expected:
            raise RuntimeError("REVIEWED_ARTIFACT_DRIFT")
        runtime[relative] = actual
    manifest = canonical_json({"activation_mechanism": mechanism, "reviewed_runtime_artifacts": runtime})
    return {
        "sha256": digest_bytes(manifest.encode("ascii")),
        "mechanism_files": mechanism,
        "runtime_artifacts": runtime,
    }


def source_identity(root: Path, *, clean_required: bool) -> dict[str, Any]:
    """Bind the exact clean candidate HEAD, bundle, and reviewed runtime bytes."""
    root = root.resolve(strict=True)
    if not root.is_dir() or (root / ".git").is_symlink():
        raise RuntimeError("SOURCE_ROOT_UNSAFE")
    head = _git(root, "rev-parse", "HEAD")
    clean = not bool(_git(root, "status", "--porcelain=v1", "--untracked-files=all"))
    if clean_required and not clean:
        raise RuntimeError("CLEAN_CANDIDATE_REQUIRED")
    artifacts: dict[str, str] = {}
    for relative, expected in ARTIFACTS.items():
        actual = _reviewed_file_digest(root, relative)
        if actual != expected:
            raise RuntimeError("REVIEWED_ARTIFACT_DRIFT")
        artifacts[relative] = actual
    bundle = activation_bundle_identity(root)
    identity = {"head": head, "clean": clean, "artifacts": artifacts,
                "activation_bundle_sha256": bundle["sha256"]}
    validate_source_identity(identity, clean_required=clean_required)
    return identity


def runtime_artifact_identity(root: Path) -> dict[str, str]:
    """Validate only runtime files in the fixed execution target."""
    root = root.resolve(strict=True)
    result = {}
    for relative, expected in ARTIFACTS.items():
        actual = _reviewed_file_digest(root, relative)
        if actual != expected:
            raise RuntimeError("REVIEWED_ARTIFACT_DRIFT")
        result[relative] = actual
    return result


def _safe_json(raw: bytes) -> Any:
    if len(raw) > _HTTP_LIMIT:
        raise RuntimeError("RESPONSE_TOO_LARGE")
    return json.loads(raw)


class ActivationPort(Protocol):
    def observe_preconditions(self) -> dict[str, Any]: ...
    def reconcile_colima(self) -> bool: ...
    def validate_existing_generations(self) -> bool: ...
    def start_existing_wordpress(self) -> bool: ...
    def wordpress_healthy(self) -> bool: ...
    def server_side_api_connectivity(self) -> bool: ...
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
        consumed: bool | None = False
        attempted = False
        colima_attempted = False
        wordpress_attempted = False
        caddy_attempted = False
        facts: dict[str, Any] = {
            "colima_repair_attempted": False,
            "wordpress_start_attempted": False,
            "caddy_reload_attempted": False,
            "COLIMA_REPAIR_ATTEMPTED": False,
            "WORDPRESS_START_ATTEMPTED": False,
            "CADDY_RELOAD_ATTEMPTED": False,
            "colima_retry": False,
        }
        try:
            receipt_result = self.store.consume(self.port.observe_preconditions)
            receipt = validate_consumption_result(
                receipt_result, now=datetime.now(timezone.utc), uid=self.uid, gid=self.gid,
            )
            consumed = True
            before = parse_preconditions(receipt.precondition_json)
            # A claim is not permission to ignore drift between the claim and the
            # first mutation.  Drift burns the one-shot authority and stops.
            if self.port.observe_preconditions() != before:
                return projection("UNCERTAIN", authorization_consumed=True, **facts)

            attempted = True
            colima_attempted = facts["colima_repair_attempted"] = True
            facts["COLIMA_REPAIR_ATTEMPTED"] = True
            if not self.port.reconcile_colima():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  colima_repair_ready=False, **facts)
            # Phase B starts only after the one and only authorized Colima
            # repair has returned success.  A failed identity check burns the
            # authority and cannot fall through to a start or retry.
            if not self.port.validate_existing_generations():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  colima_repair_ready=True, phase_b_existing_generation_proof=False,
                                  **facts)
            wordpress_attempted = facts["wordpress_start_attempted"] = True
            facts["WORDPRESS_START_ATTEMPTED"] = True
            if not self.port.start_existing_wordpress():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  existing_wordpress_reuse_ready=False, **facts)
            if not self.port.wordpress_healthy():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  wordpress_healthy=False, **facts)
            if not self.port.server_side_api_connectivity():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  server_side_api_connectivity=False, **facts)
            if not self.port.validate_caddy_offline():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  caddy_v2_reload_ready=False, **facts)
            caddy_attempted = facts["caddy_reload_attempted"] = True
            facts["CADDY_RELOAD_ATTEMPTED"] = True
            if not self.port.reload_caddy_once():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  caddy_reload_count=1, caddy_v2_reload_ready=False, **facts)
            if not self.port.effective_caddy_v2():
                return projection("UNCERTAIN", authorization_consumed=True, mutation_attempted=True,
                                  caddy_reload_count=1, effective_caddy_v2_proof=False, **facts)
            post = self.port.post_activation()
            validate_post_activation(post)
            return projection("ACTIVATED", authorization_consumed=True, mutation_attempted=True,
                              colima_repair_ready=True, phase_b_existing_generation_proof=True,
                              existing_wordpress_reuse_ready=True,
                              wordpress_healthy=True, server_side_api_connectivity=True,
                              caddy_v2_reload_ready=True, effective_caddy_v2_proof=True,
                              public_read_allowlist=True, dev_basic_auth=True, **facts, **post)
        except ConsumptionFailure as error:
            consumed = {"NOT_CONSUMED": False, "CONSUMED": True, "UNCERTAIN": None}.get(error.state)
        except Exception:
            # Never project exception text or attempt a retry after a claim or
            # lifecycle ambiguity.
            pass
        status = "BLOCKED" if consumed is False and not attempted else "UNCERTAIN"
        return projection(status, authorization_consumed=consumed, mutation_attempted=attempted,
                          **facts)


class MacActivationPort:
    """Fixed Mac implementation.  Its mutators are intentionally explicit."""

    def __init__(self, *, source_root: Path, runtime_root: Path = RUNTIME_ROOT):
        self.source_root = source_root.resolve(strict=True)
        self.runtime_root = runtime_root.resolve(strict=True)
        if self.runtime_root != RUNTIME_ROOT:
            raise RuntimeError("RUNTIME_ROOT_IDENTITY_REJECTED")
        source_identity(self.source_root, clean_required=True)
        runtime_artifact_identity(self.runtime_root)

    def _observe_profile_config(self) -> dict[str, Any]:
        """Read and semantically attest the fixed host profile; Docker is not involved."""
        path = Path(PROFILE_FILE)
        if (path.is_symlink() or not path.is_file() or
                path.resolve(strict=True) != path or len(path.read_bytes()) > _HTTP_LIMIT):
            raise RuntimeError("COLIMA_PROFILE_CONFIG_UNAVAILABLE")
        contract_path = self.runtime_root / PROFILE_ARTIFACT
        if (contract_path.is_symlink() or not contract_path.is_file() or
                contract_path.resolve(strict=True) != contract_path):
            raise RuntimeError("COLIMA_RUNTIME_CONTRACT_UNAVAILABLE")
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            return attest_runtime_profile(
                path.read_bytes(), contract=contract,
                trusted_deployment_root=self.runtime_root,
            )
        except Exception as error:
            if isinstance(error, RuntimeError):
                raise
            raise RuntimeError("COLIMA_PROFILE_SEMANTIC_DRIFT") from None

    def _run(self, argv: list[str], *, cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            argv, cwd=cwd, env=_fixed_environment(), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False,
        )

    def _docker_inspect(self, identity: str) -> dict[str, Any]:
        fmt = ('{"id":{{json .Id}},"state":{{json .State.Status}},"running":{{json .State.Running}},'
               '"healthy":{{with (index .State "Health")}}{{json .Status}}{{else}}null{{end}},'
               '"ports":{{json .NetworkSettings.Ports}},"mounts":{{json .Mounts}},'
               '"restart":{{json .HostConfig.RestartPolicy.Name}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
               '"service":{{json (index .Config.Labels "com.docker.compose.service")}}}')
        result = self._run([DOCKER, "--context", CONTEXT, "container", "inspect", "--format", fmt, identity], cwd=self.runtime_root)
        if result.returncode != 0:
            raise RuntimeError("DOCKER_INSPECTION_UNAVAILABLE")
        value = _safe_json(result.stdout)
        if type(value) is not dict:
            raise RuntimeError("DOCKER_INSPECTION_INVALID")
        return value

    def observe_preconditions(self) -> dict[str, Any]:
        """Phase A: host-only evidence that is valid while Colima is Broken.

        In particular, this method must never call Docker.  Container and
        volume inspection is intentionally deferred to Phase B, after the
        single authorized Colima repair has returned success.
        """
        colima = self._run([COLIMA, "list", "--profile", PROFILE, "--json"], cwd=self.runtime_root)
        if colima.returncode != 0:
            raise RuntimeError("COLIMA_INSPECTION_UNAVAILABLE")
        rows = _safe_json(colima.stdout)
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("name") != PROFILE:
            raise RuntimeError("COLIMA_PROFILE_IDENTITY_UNAVAILABLE")
        status = rows[0].get("status")
        if status != "Broken":
            raise RuntimeError("COLIMA_PRECONDITION_DRIFT")
        semantic_projection = self._observe_profile_config()
        source = source_identity(self.source_root, clean_required=True)
        # The forwarding owner is intentionally supplied only by a fixed,
        # read-only Colima inspection seam.  An unproven listener is a block;
        # this lane never kills a PID or guesses ownership.
        forwarding = self._observe_colima_forwarding()
        return {
            "source": source,
            "desired": {"policy_version": POLICY_VERSION, "public_host": PUBLIC_HOST,
                         "dev_host": DEV_HOST, "public_upstream": "127.0.0.1:58082",
                         "shopping_api_upstream": "127.0.0.1:58081", "dev_upstream": "127.0.0.1:18080"},
            "effective": {"caddy_state": self._observe_effective_caddy_state()},
            "colima": {"profile": PROFILE, "profile_file": PROFILE_FILE,
                        "semantic_projection": semantic_projection, "status": status},
            "forwarding": forwarding,
            # Durable reviewed expectations, not live Docker observations.
            "wordpress": {"container_id": WORDPRESS_CONTAINER_ID, "state": "created",
                           "running": False, "published": "127.0.0.1:58082->80/tcp"},
            "database": {"container_id": DATABASE_CONTAINER_ID, "state": "running",
                         "healthy": True, "published": False, "volume": DATABASE_VOLUME},
            "volumes": {"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME},
            "ports": EXPECTED_PORTS,
            "authority": {"ubuntu_authority": False, "business_mutation_authority": False,
                           "database_recreation_allowed": False, "volume_recreation_allowed": False,
                           "woo_write_authority": False},
        }

    def _observe_colima_forwarding(self) -> dict[str, Any]:
        # Read-only ownership proof for the one stale listener.  This lane
        # never kills a PID; the bounded Colima restart is the only operation
        # allowed to reconcile it.
        result = self._run([
            "/usr/sbin/lsof", "-nP", "-Fpc", "-a", "-iTCP:58082", "-sTCP:LISTEN",
        ], cwd=self.runtime_root, timeout=10)
        if result.returncode != 0:
            raise RuntimeError("COLIMA_FORWARDING_INSPECTION_UNAVAILABLE")
        lines = result.stdout.decode("ascii", errors="strict").splitlines()
        pids = [line[1:] for line in lines if line.startswith("p") and line[1:].isdigit()]
        commands = [line[1:] for line in lines if line.startswith("c") and line[1:]]
        if len(pids) != 1 or len(commands) != 1:
            raise RuntimeError("COLIMA_FORWARDING_OWNERSHIP_AMBIGUOUS")
        process = self._run(["/bin/ps", "-p", pids[0], "-o", "command="], cwd=self.runtime_root, timeout=10)
        command = process.stdout.decode("utf-8", errors="strict").strip()
        if (process.returncode != 0 or not command or PROFILE not in command or
                not any(marker in command for marker in ("colima", "ssh", "limactl"))):
            raise RuntimeError("COLIMA_FORWARDING_OWNER_MISMATCH")
        return {"owner": "colima", "profile": PROFILE, "host": "127.0.0.1",
                "port": PUBLIC_PORT, "required_for_lifecycle": True}

    def _observe_effective_caddy_state(self) -> str:
        from ops.macos.shopping import public_storefront_v2_effective_caddy_observer as observer
        observed = observer.observe_pre_v2(reviewed_root=self.source_root,
                                           runtime_root=self.runtime_root)
        if observed.get("status") != "PASS":
            raise RuntimeError("CADDY_PRECONDITION_UNPROVEN")
        return EFFECTIVE_CADDY_STATE

    def reconcile_colima(self) -> bool:
        # The only lifecycle mutation: one bounded graceful restart.  A timeout
        # or nonzero result is uncertain and is never retried.
        try:
            result = self._run([COLIMA, "restart", "--profile", PROFILE], cwd=self.runtime_root, timeout=180)
            return result.returncode == 0
        except Exception:
            return False

    def _profile_is_running(self) -> bool:
        result = self._run([COLIMA, "list", "--profile", PROFILE, "--json"], cwd=self.runtime_root)
        if result.returncode != 0:
            return False
        rows = _safe_json(result.stdout)
        if isinstance(rows, dict):
            rows = [rows]
        if not (isinstance(rows, list) and len(rows) == 1 and rows[0].get("name") == PROFILE and rows[0].get("status") == "Running"):
            return False
        return True

    def _docker_endpoint_observable(self) -> bool:
        """Prove the fixed Docker API is reachable, without requesting data."""
        result = self._run([
            DOCKER, "--context", CONTEXT, "version", "--format", "{{json .Server}}",
        ], cwd=self.runtime_root, timeout=15)
        if result.returncode != 0:
            return False
        try:
            value = _safe_json(result.stdout)
        except Exception:
            return False
        return type(value) is dict and bool(value)

    def _docker_volume_inspect(self, name: str) -> dict[str, Any]:
        result = self._run([
            DOCKER, "--context", CONTEXT, "volume", "inspect", "--format",
            '{"Name":{{json .Name}},"Driver":{{json .Driver}},"Scope":{{json .Scope}},"CreatedAt":{{json .CreatedAt}}}',
            name,
        ], cwd=self.runtime_root, timeout=15)
        if result.returncode != 0:
            raise RuntimeError("DOCKER_VOLUME_INSPECTION_UNAVAILABLE")
        value = _safe_json(result.stdout)
        if type(value) is not dict or set(value) != {"Name", "Driver", "Scope", "CreatedAt"}:
            raise RuntimeError("DOCKER_VOLUME_INSPECTION_INVALID")
        if (value["Name"] != name or value["Driver"] != "local" or
                value["Scope"] != "local" or not isinstance(value["CreatedAt"], str) or
                not value["CreatedAt"]):
            raise RuntimeError("DOCKER_VOLUME_IDENTITY_MISMATCH")
        return value

    def validate_existing_generations(self) -> bool:
        """Phase B: live Docker evidence after exactly one successful repair."""
        try:
            if not self._profile_is_running() or not self._docker_endpoint_observable():
                return False
            wordpress = self._docker_inspect(WORDPRESS_CONTAINER_ID)
            database = self._docker_inspect(DATABASE_CONTAINER_ID)
            wordpress_ports = {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]}
            wordpress_mount = any(
                type(mount) is dict and mount.get("Type") == "volume" and
                mount.get("Name") == WORDPRESS_VOLUME and mount.get("Destination") == "/var/www/html" and
                mount.get("RW") is True
                for mount in wordpress.get("mounts", [])
            )
            database_mount = any(
                type(mount) is dict and mount.get("Type") == "volume" and
                mount.get("Name") == DATABASE_VOLUME and mount.get("Destination") == "/var/lib/mysql" and
                mount.get("RW") is True
                for mount in database.get("mounts", [])
            )
            wordpress_volume = self._docker_volume_inspect(WORDPRESS_VOLUME)
            database_volume = self._docker_volume_inspect(DATABASE_VOLUME)
            if (wordpress.get("id") != WORDPRESS_CONTAINER_ID or wordpress.get("project") != "ai-shopping" or
                    wordpress.get("service") != "wordpress" or wordpress.get("ports") != wordpress_ports or
                    not wordpress_mount):
                return False
            if (database.get("id") != DATABASE_CONTAINER_ID or database.get("project") != "ai-shopping" or
                    database.get("service") != "database" or database.get("state") != "running" or
                    database.get("healthy") != "healthy" or type(database.get("ports")) is not dict or
                    any(value not in (None, []) for value in database["ports"].values()) or
                    not database_mount):
                return False
            # Exact named volume identity is the continuity boundary.  No
            # create/rm/Compose command exists in this module, so a matching
            # object and exact existing container IDs prove no recreation in
            # this activation lane.
            self._phase_b_volume_identity = {
                "wordpress": wordpress_volume["Name"], "database": database_volume["Name"],
            }
            return self._phase_b_volume_identity == {
                "wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME,
            }
        except Exception:
            return False

    def start_existing_wordpress(self) -> bool:
        # Existing-generation recovery contract: start this exact container;
        # never Compose-up, recreate, or touch either named volume.
        try:
            result = self._run([DOCKER, "--context", CONTEXT, "container", "start", WORDPRESS_CONTAINER_ID], cwd=self.runtime_root, timeout=30)
            return result.returncode == 0
        except Exception:
            return False

    def wordpress_healthy(self) -> bool:
        deadline = time.monotonic() + 460
        while time.monotonic() < deadline:
            try:
                value = self._docker_inspect(WORDPRESS_CONTAINER_ID)
                if (value.get("state") == "running" and value.get("running") is True and
                        value.get("healthy") == "healthy" and value.get("ports") == {
                            "80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "58082"}]
                        }):
                    return True
            except Exception:
                return False
            time.sleep(5)
        return False

    def server_side_api_connectivity(self) -> bool:
        # Read-only WordPress probe; it proves the server-side plugin's fixed
        # host-gateway target without exposing cookies or credentials.
        try:
            result = self._run([DOCKER, "--context", CONTEXT, "exec", "--env", "HOME=/var/empty",
                                WORDPRESS_CONTAINER_ID, "php", "-r",
                                "$s=@fsockopen('host.docker.internal',58081,$e,$m,3); exit($s?0:1);"] ,
                               cwd=self.runtime_root, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def validate_caddy_offline(self) -> bool:
        try:
            path = self.runtime_root / CADDYFILE
            if digest_bytes(path.read_bytes()) != CADDYFILE_SHA256:
                return False
            policy = load_site_policy((self.runtime_root / CADDY_POLICY).read_text())
            validate_contract_payload(registry=load_schema_registry(), contract_name="CaddySitePolicy", payload=policy)
            ingress = json.loads((self.runtime_root / INGRESS).read_text())
            classification = classify_caddy_sites(path.read_text(), policy=policy, ingress_contract=ingress)
            if not (classification.production.hostname == PUBLIC_HOST and classification.production.port == PUBLIC_PORT and
                    classification.production.authentication_required is False and classification.preview is not None and
                    classification.preview.hostname == DEV_HOST and classification.preview.port == DEV_PORT and
                    classification.preview.authentication_required is True):
                return False
            result = self._run([CADDY, "validate", "--config", str(path), "--adapter", "caddyfile"], cwd=self.runtime_root, timeout=30)
            if result.returncode != 0:
                return False
            browser_sources = "\n".join(
                (self.runtime_root / relative).read_text()
                for relative in (BROWSER_STOREFRONT, WORDPRESS_STOREFRONT_UI)
            )
            return not any(
                forbidden in browser_sources
                for forbidden in ("wc/v3", "consumer_key", "consumer_secret", "Authorization", "wp-json")
            ) and "127.0.0.1:18080" not in path.read_text().split("bokstory.duckdns.org", 1)[1].split("dev.bokstory.duckdns.org", 1)[0]
        except Exception:
            return False

    def reload_caddy_once(self) -> bool:
        try:
            result = self._run([CADDY, "reload", "--config", str(self.runtime_root / CADDYFILE), "--adapter", "caddyfile"], cwd=self.runtime_root, timeout=30)
            return result.returncode == 0
        except Exception:
            return False

    def effective_caddy_v2(self) -> bool:
        """Require the local admin/attestor to prove the loaded V2 document."""
        try:
            from ops.macos.shopping import public_storefront_v2_effective_caddy_observer as observer
            evidence = observer.observe_caddy_effective_v2(reviewed_root=self.source_root,
                                                           runtime_root=self.runtime_root)
            return evidence.get("status") == "PASS" and all(
                evidence.get(key) is True for key in (
                    "production_host", "public_root_upstream", "shopping_read_upstream",
                    "public_get_allowlist_matcher_loaded", "private_management_matcher_loaded",
                    "wordpress_rest_matcher_loaded", "raw_query_rest_route_ambiguity_guard_loaded",
                    "dev_host", "dev_basic_auth_loaded", "public_has_no_basic_auth",
                )
            )
        except Exception:
            return False

    def _http_get(self, url: str) -> tuple[int, dict[str, str], bytes]:
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        request = Request(url, method="GET", headers={"Accept": "application/json,text/html;q=0.9"})
        opener = build_opener(NoRedirect)
        try:
            response = opener.open(request, timeout=15)
            body = response.read(_HTTP_LIMIT + 1)
            return response.status, dict(response.headers.items()), body
        except HTTPError as error:
            body = error.read(_HTTP_LIMIT + 1)
            return error.code, dict(error.headers.items()), body
        except (URLError, TimeoutError):
            return 0, {}, b""

    def post_activation(self) -> dict[str, Any]:
        status, headers, body = self._http_get("https://" + PUBLIC_HOST + "/")
        # Repository-owned template marker; do not infer storefront health from
        # a guessed generic word in arbitrary HTML.
        rendered = status in range(200, 300) and body.decode("utf-8", errors="ignore").count(
            'class="ai-shopping-storefront"'
        ) == 1
        public = {"https_success": status in range(200, 300),
                  "basic_auth": "www-authenticate" in {key.lower() for key in headers},
                  "storefront_rendered": rendered}
        reads: dict[str, bool] = {}
        for name, path in (("categories", "/shopping/categories"), ("search", "/shopping/search"),
                           ("featured_products", "/shopping/featured-products"),
                           ("products", "/shopping/products?page=1&page_size=20")):
            code, _, data = self._http_get("https://" + PUBLIC_HOST + path)
            reads[name] = code in range(200, 300) and bool(data)
        catalog_state = "VALID_EMPTY"
        dynamic_detail = False
        if reads.get("products"):
            try:
                listing = _safe_json(data)
                items = listing.get("items") if type(listing) is dict else None
                valid_listing = (
                    type(listing) is dict and type(items) is list and
                    type(listing.get("page")) is int and listing["page"] == 1 and
                    type(listing.get("page_size")) is int and 1 <= listing["page_size"] <= 20 and
                    len(items) <= listing["page_size"]
                )
                if not valid_listing:
                    reads["products"] = False
                elif items:
                    product_id = items[0].get("id") if type(items[0]) is dict else None
                    if type(product_id) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", product_id):
                        reads["products"] = False
                    else:
                        catalog_state = "VALID_NONEMPTY"
                        detail_code, _, detail_data = self._http_get(
                            "https://" + PUBLIC_HOST + "/shopping/products/" + product_id
                        )
                        try:
                            detail = _safe_json(detail_data)
                        except Exception:
                            detail = None
                        dynamic_detail = (
                            detail_code in range(200, 300) and type(detail) is dict and
                            detail.get("id") == product_id
                        )
                else:
                    dynamic_detail = False
            except Exception:
                reads["products"] = False
        private = {}
        for path in ("/wp-admin", "/wp-login.php", "/wp-json", "/wp-json/", "/management",
                     "/deployment", "/runtime", "/governance", "/providers", "/tasks",
                     "/shopping/cart", "/shopping/checkout", "/shopping/orders", "/wp-json/wc/v3/products"):
            code, _, _ = self._http_get("https://" + PUBLIC_HOST + path)
            private[path] = code in (403, 404)
        query_route_paths = (
            "/?rest_route=/wp/v2/users", "/?REST_ROUTE=/wp/v2/users",
            "/?rest%5froute=/wp/v2/users", "/?rest.route=/wp/v2/users",
            "/?rest+route=/wp/v2/users",
        )
        query_route_denied = []
        for path in query_route_paths:
            code, _, _ = self._http_get("https://" + PUBLIC_HOST + path)
            query_route_denied.append(code in (403, 404))
        dev_code, dev_headers, _ = self._http_get("https://" + DEV_HOST + "/")
        legacy_code, legacy_headers, _ = self._http_get("https://" + PUBLIC_HOST + "/homepage/storefront")
        return {
            "public": {"https_success": public["https_success"], "basic_auth": not public["basic_auth"],
                       "storefront_rendered": rendered},
            "shopping_reads": {key: reads[key] for key in ("categories", "search", "featured_products", "products")},
            "product_catalog": catalog_state,
            "private_boundary": {"wordpress_paths_denied": all(private[path] for path in ("/wp-admin", "/wp-login.php", "/wp-json", "/wp-json/")),
                                  "rest_routes_denied": private["/wp-json/"] and all(query_route_denied), "management_paths_denied": all(private[path] for path in ("/management", "/deployment", "/runtime", "/governance", "/providers", "/tasks")),
                                  "shopping_writes_not_proxied": private["/shopping/cart"], "order_payment_cart_checkout_not_proxied": private["/shopping/checkout"] and private["/shopping/orders"]},
            "dev": {"https_success": dev_code in range(200, 300), "basic_auth_required": dev_code == 401 and "www-authenticate" in {key.lower() for key in dev_headers}, "production_never_uses_dev": True},
            "legacy": {"path": "/homepage/storefront", "status": legacy_code, "location": legacy_headers.get("Location", "")},
            "direct_browser_woo_denied": private["/wp-json/wc/v3/products"],
            "wordpress_loopback": "127.0.0.1:58082",
            "server_side_api": "127.0.0.1:58081",
            "database_continuity": self._database_continuity(),
            "effective_caddy_v2": True,
            "rest_route_live_proof": all(query_route_denied),
            "product_detail_dynamic_id": dynamic_detail,
            "public_commerce_write_request": "NOT_PERFORMED",
            "caddy_reload_count": 1,
        }

    def _database_continuity(self) -> bool:
        try:
            value = self._docker_inspect(DATABASE_CONTAINER_ID)
            volumes = {
                "wordpress": self._docker_volume_inspect(WORDPRESS_VOLUME)["Name"],
                "database": self._docker_volume_inspect(DATABASE_VOLUME)["Name"],
            }
            return (value.get("id") == DATABASE_CONTAINER_ID and value.get("state") == "running" and
                    value.get("healthy") == "healthy" and type(value.get("ports")) is dict and
                    all(item in (None, []) for item in value["ports"].values()) and
                    volumes == {"wordpress": WORDPRESS_VOLUME, "database": DATABASE_VOLUME})
        except Exception:
            return False


def run(*, source_root: Path, runtime_root: Path = RUNTIME_ROOT) -> dict[str, Any]:
    source_identity(source_root, clean_required=True)
    owner = os.getuid(), os.getgid()
    store = PublicStorefrontV2ActivationAuthorizationStore.open_existing()
    return ActivationRunner(store, MacActivationPort(source_root=source_root, runtime_root=runtime_root), *owner).run()


def main() -> int:
    # The standalone operator is intentionally not a caller-configurable
    # execution surface.  The TTY-gated combined issuer invokes run() only
    # after the exact human acknowledgement and durable issuance.
    print(json.dumps(projection("CALLER_OVERRIDE_REJECTED"), sort_keys=True, separators=(",", ":")))
    return 2


__all__ = ["ActivationPort", "ActivationRunner", "MacActivationPort", "RUNTIME_ROOT", "activation_bundle_identity",
           "main", "run", "runtime_artifact_identity", "source_identity"]


if __name__ == "__main__":
    raise SystemExit(main())
