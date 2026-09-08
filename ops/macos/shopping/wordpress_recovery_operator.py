"""Fixed Mac 01G1D operator. Importing this module performs no observation or write."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.runtime_cutover_secret_source import _open_source
from core.shopping import wordpress_recovery_reconciliation as contract
from core.shopping.wordpress_recovery_authorization import ConsumptionFailure, validate_consumption_result
from ops.macos.shopping.wordpress_recovery_authorization_store import WordPressRecoveryAuthorizationStore
from ops.macos.shopping import wordpress_port_live_operator as trusted

# Select fields at Docker, never retrieve environment values, logs, healthcheck output or headers.
CONTAINER_FORMAT = (
    '{"status":{{json .State.Status}},"pid":{{json .State.Pid}},"exit_code":{{json .State.ExitCode}},'
    '"host_ports":{{json .HostConfig.PortBindings}},"network_mode":{{json .HostConfig.NetworkMode}},"id":{{json .Id}},"started":{{json .State.StartedAt}},'
    '"restart_count":{{json .RestartCount}},"running":{{json .State.Running}},'
    '"healthy":{{with (index .State "Health")}}{{json .Status}}{{else}}null{{end}},"paused":{{json .State.Paused}},'
    '"restarting":{{json .State.Restarting}},"image":{{json .Image}},'
    '"configured_image":{{json .Config.Image}},'
    '"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
    '"service":{{json (index .Config.Labels "com.docker.compose.service")}},'
    '"ports":{{json .NetworkSettings.Ports}},"networks":{{json .NetworkSettings.Networks}},'
    '"mounts":{{json .Mounts}}}'
)
NETWORK_FORMAT = '{"id":{{json .Id}},"internal":{{json .Internal}}}'
VOLUME_FORMAT = '{"Name":{{json .Name}},"Driver":{{json .Driver}},"Scope":{{json .Scope}},"CreatedAt":{{json .CreatedAt}}}'
IMAGE_FORMAT = '{"id":{{json .Id}},"digests":{{json .RepoDigests}}}'


def _json(raw):
    contract.require(len(raw) <= 65536)
    def unique(pairs):
        value = {}
        for key, item in pairs:
            contract.require(key not in value)
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def _read(arguments):
    result = subprocess.run(
        [trusted._trusted_docker_executable(), "--context", contract.TARGET_CONTEXT, *arguments],
        cwd=contract.ROOT, env=trusted._fixed_environment(), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False,
    )
    contract.require(result.returncode == 0)
    return _json(result.stdout)


def _repository():
    def git(*args):
        completed = subprocess.run(["/usr/bin/git", *args], cwd=contract.ROOT,
                                   env={"PATH": "/usr/bin:/bin", "HOME": "/var/empty", "GIT_CONFIG_NOSYSTEM": "1"},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, timeout=10, check=False)
        contract.require(completed.returncode == 0)
        return completed.stdout.decode("ascii").strip()
    head = git("rev-parse", "HEAD")
    contract.require(not git("status", "--porcelain=v1", "--untracked-files=all"))
    digests = {}
    for name in contract.ARTIFACTS:
        path = contract.ROOT / name
        contract.require(path.resolve(strict=True) == path and path.is_file() and path.stat().st_size <= 65536)
        digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    contract.require(digests == contract.ARTIFACTS)
    return head, digests


def _source_metadata():
    home = resolve_trusted_mac_account_home()
    owner = issue_trusted_ownership_expectation(home)
    opened, descriptors = _open_source(home, owner, contract.ROOT)
    try:
        # Opening for fstat is intentional; no read, hash or parse of env values.
        return {name: getattr(opened.metadata, name) for name in (
            "st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_size", "st_nlink", "st_mtime_ns", "st_ctime_ns")}
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _container(name):
    value = _read(("container", "inspect", "--format", CONTAINER_FORMAT, name))
    contract.require(value["healthy"] in (None, "starting", "healthy", "unhealthy"))
    value["healthy"] = value["healthy"] == "healthy"
    value["networks"] = {name: metadata["NetworkID"] for name, metadata in value["networks"].items()}
    value["mounts"] = sorted([
        dict(type=m["Type"], name=m.get("Name", ""), source=m["Source"], destination=m["Destination"], rw=m["RW"])
        for m in value["mounts"]], key=lambda m: m["destination"])
    return value


def _snapshot():
    contract.require(sys.platform == "darwin")
    source = _source_metadata()  # trusted Darwin identity and source metadata first
    head, artifacts = _repository()
    image = _read(("image", "inspect", "--format", IMAGE_FORMAT, contract.WORDPRESS_IMAGE))
    digest = "wordpress@" + contract.WORDPRESS_IMAGE.split("@", 1)[1]
    contract.require(type(image["digests"]) is list and digest in image["digests"])
    return dict(head=head, clean=True, artifacts=artifacts,
                wordpress=_container(contract.WORDPRESS_CONTAINER), database=_container(contract.DATABASE_CONTAINER),
                image=dict(id=image["id"], digest=digest),
                volumes={name: _read(("volume", "inspect", "--format", VOLUME_FORMAT, name)) for name in contract.VOLUMES},
                networks={name: _read(("network", "inspect", "--format", NETWORK_FORMAT, name)) for name in contract.NETWORKS},
                source_metadata=source, production=False, ubuntu=False)


def observe_preconditions():
    """Two matching read-only snapshots reject torn or unstable observations."""
    first, second = _snapshot(), _snapshot()
    contract.validate_snapshot(first)
    contract.require(first == second)
    return first


def _prepare_mutation():
    invocation = contract.build_mutation_invocation()
    executable = trusted._trusted_docker_executable()
    command = (executable, *invocation.argv[1:])
    environment = trusted._fixed_environment()

    def mutate():
        # Closed-over, fixed command: no command or target accepting execution API.
        try:
            result = subprocess.run(command, cwd=contract.ROOT, env=environment,
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False)
            return contract.ExecutionOutcome.SUCCEEDED if result.returncode == 0 else contract.ExecutionOutcome.FAILED
        except Exception:
            return contract.ExecutionOutcome.UNCERTAIN
    return mutate


def _validate_post(before):
    # Read-only convergence horizon from the existing WordPress healthcheck contract.
    for attempt in range(25):
        if attempt:
            time.sleep(15)
        try:
            first = _snapshot()
            time.sleep(1)
            second = _snapshot()
            contract.require(first == second)
            contract.validate_post(before, second)
            return True
        except Exception:
            continue
    return False


def run():
    consumed = False
    attempted = False
    try:
        home = resolve_trusted_mac_account_home()
        owner = issue_trusted_ownership_expectation(home)
        authorization = WordPressRecoveryAuthorizationStore.open_existing()
        prepared = _prepare_mutation()
        consumed = None
        result = authorization.consume(observe_preconditions)
        consumed = True
        receipt = validate_consumption_result(result, now=datetime.now(timezone.utc), uid=owner.expected_uid, gid=owner.expected_gid)
        before = contract.parse_binding(receipt.precondition_json)
        # No further mutable preparation occurs between consumption and the sole call.
        attempted = True
        outcome = prepared()
        validated = _validate_post(before)  # diagnostics never upgrade failed/uncertain execution
        accepted = outcome is contract.ExecutionOutcome.SUCCEEDED and validated is True
        return contract.projection("ACCEPTED" if accepted else "UNCERTAIN", consumed=True, attempted=True)
    except ConsumptionFailure as error:
        consumed = {contract.AuthorizationConsumptionState.NOT_CONSUMED: False,
                    contract.AuthorizationConsumptionState.CONSUMED: True}.get(error.state)
    except Exception:
        pass
    return contract.projection("BLOCKED" if consumed is False else "UNCERTAIN", consumed=consumed, attempted=attempted)


def main():
    result = contract.projection("CALLER_OVERRIDE_REJECTED") if len(sys.argv) != 1 else run()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ACCEPTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
