"""Zero-argument Mac-local operator for the fixed WordPress reconciliation."""
from __future__ import annotations
import json, os, pwd, stat, subprocess, sys
from pathlib import Path
from core.shopping.observability.storage_continuity import StorageContinuityObservation
from core.shopping.wordpress_port_reconciliation import (
    COMPOSE_PROJECT, DATABASE_CONTAINER, TARGET_CONTEXT, WORDPRESS_CONTAINER,
    ContainerRuntimeFact, ExecutionOutcome, MutationInvocation,
    WordPressPortRuntimeFacts, build_mutation_invocation, execute_reconciliation,
)
from ops.macos.shopping.storage_continuity_observer import observe_storage_continuity
from ops.macos.shopping.wordpress_port_authorization_store import WordPressPortAuthorizationStore

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TRUSTED_DOCKER_ENTRYPOINT = Path("/opt/homebrew/bin/docker")
_TRUSTED_COMPOSE_ENTRYPOINT = Path("/opt/homebrew/bin/docker-compose")
_TRUSTED_EXECUTABLE_ROOT = Path("/opt/homebrew")
_FIXED_PATH = "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
_DOCKER_SELECTION_VARIABLES = frozenset({
    "COMPOSE_ENV_FILES", "COMPOSE_FILE", "COMPOSE_PATH_SEPARATOR",
    "COMPOSE_PROFILES", "COMPOSE_PROJECT_NAME", "DOCKER_API_VERSION",
    "DOCKER_CERT_PATH", "DOCKER_CONTEXT", "DOCKER_HOST", "DOCKER_TLS",
    "DOCKER_TLS_VERIFY",
})

def _trusted_homebrew_executable(entrypoint: Path, formula: str, label: str) -> str:
    """Trust a bounded Homebrew package-manager domain, not immutable files.

    Darwin admin (gid 80) may write only the shared prefix/bin/Cellar.
    Formula-rack directories and the executable retain strict writer checks.
    """
    root = _TRUSTED_EXECUTABLE_ROOT
    try:
        resolved = entrypoint.resolve(strict=True)
        metadata = resolved.stat()
        trusted_uid = pwd.getpwuid(os.getuid()).pw_uid
    except (KeyError, OSError, RuntimeError) as error:
        raise RuntimeError(f"trusted {label} executable unavailable") from error
    try:
        parts = resolved.relative_to(root).parts
    except ValueError as error:
        raise RuntimeError(f"unexpected {label} executable identity") from error
    if (entrypoint != root / "bin" / formula or len(parts) != 5
            or parts[:2] != ("Cellar", formula)
            or parts[3:] != ("bin", formula)):
        raise RuntimeError(f"unexpected {label} executable identity")
    if (not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid not in (0, trusted_uid)
            or metadata.st_mode & 0o022
            or not metadata.st_mode & 0o111):
        raise RuntimeError(f"unsafe {label} executable identity")
    shared = {root, root / "bin", root / "Cellar"}
    parents = {root, entrypoint.parent}
    current = root
    for component in parts[:-1]:
        current = current / component
        parents.add(current)
    try:
        for parent in parents:
            parent_metadata = parent.stat()
            shared_admin_write = (
                parent in shared
                and parent_metadata.st_uid == trusted_uid
                and parent_metadata.st_gid == 80
            )
            if (parent.is_symlink()
                    or not stat.S_ISDIR(parent_metadata.st_mode)
                    or parent_metadata.st_uid not in (0, trusted_uid)
                    or parent_metadata.st_mode & 0o002
                    or (parent_metadata.st_mode & 0o020 and not shared_admin_write)):
                raise RuntimeError(f"unsafe {label} executable path")
    except OSError as error:
        raise RuntimeError(f"trusted {label} executable path unavailable") from error
    return str(resolved)


def _trusted_docker_executable() -> str:
    return _trusted_homebrew_executable(_TRUSTED_DOCKER_ENTRYPOINT, "docker", "Docker")


def _trusted_compose_executable() -> str:
    return _trusted_homebrew_executable(_TRUSTED_COMPOSE_ENTRYPOINT, "docker-compose", "Compose")

def _fixed_environment() -> dict[str, str]:
    """Remove ambient Docker/Compose selectors and bind trusted account state."""
    account = pwd.getpwuid(os.getuid())
    environment = {
        "HOME": account.pw_dir,
        "USER": account.pw_name,
        "LOGNAME": account.pw_name,
        "PATH": _FIXED_PATH,
        "DOCKER_CONFIG": str(Path(account.pw_dir) / ".docker"),
    }
    for name in ("LANG", "LC_ALL", "TMPDIR"):
        if name in os.environ:
            environment[name] = os.environ[name]
    return environment

def _command(argv):
    if not isinstance(argv, tuple) or not argv or argv[0] != "docker":
        raise ValueError("exact Docker command required")
    command = [_trusted_docker_executable(), *argv[1:]]
    return subprocess.run(
        command, cwd=_REPOSITORY_ROOT, env=_fixed_environment(), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
        check=False,
    )

def _fact(row, expected_name):
    if not isinstance(row,dict) or row.get("Name") not in (expected_name,"/"+expected_name): raise ValueError("container identity mismatch")
    labels=((row.get("Config") or {}).get("Labels") or {})
    if labels.get("com.docker.compose.project")!=COMPOSE_PROJECT: raise ValueError("compose project mismatch")
    state=row.get("State") or {}; ports=((row.get("NetworkSettings") or {}).get("Ports") or {})
    publishers=[]
    for target, bindings in ports.items():
        target_port=target.split("/",1)[0]
        if bindings is None: continue
        if not isinstance(bindings,list): raise ValueError("malformed publisher evidence")
        for binding in bindings:
            if not isinstance(binding,dict) or not isinstance(binding.get("HostIp"),str) or not isinstance(binding.get("HostPort"),str): raise ValueError("malformed publisher evidence")
            publishers.append(f"{binding['HostIp']}:{binding['HostPort']}->{target_port}/tcp")
    health=(state.get("Health") or {}).get("Status")
    return ContainerRuntimeFact(True,state.get("Running") is True,health=="healthy",tuple(sorted(publishers)))

def _observe_runtime():
    info=_command(("docker","--context",TARGET_CONTEXT,"info","--format","{{json .ServerVersion}}"))
    reachable=info.returncode==0
    observed={}
    if reachable:
        result=_command(("docker","--context",TARGET_CONTEXT,"container","inspect",DATABASE_CONTAINER,WORDPRESS_CONTAINER))
        if result.returncode!=0: raise RuntimeError("fixed container inspection unavailable")
        rows=json.loads(result.stdout)
        if not isinstance(rows,list) or len(rows)!=2: raise ValueError("malformed container inspection")
        by_name={str(row.get("Name","")).lstrip("/"):row for row in rows if isinstance(row,dict)}
        observed[DATABASE_CONTAINER]=_fact(by_name.get(DATABASE_CONTAINER),DATABASE_CONTAINER)
        observed[WORDPRESS_CONTAINER]=_fact(by_name.get(WORDPRESS_CONTAINER),WORDPRESS_CONTAINER)
    absent=ContainerRuntimeFact(False,False,False,())
    return WordPressPortRuntimeFacts(TARGET_CONTEXT,COMPOSE_PROJECT,DATABASE_CONTAINER,WORDPRESS_CONTAINER,reachable,observed.get(DATABASE_CONTAINER,absent),observed.get(WORDPRESS_CONTAINER,absent),StorageContinuityObservation(()))

def _run_compose(invocation: MutationInvocation) -> ExecutionOutcome:
    if type(invocation) is not MutationInvocation or invocation != build_mutation_invocation(): raise ValueError("exact fixed invocation required")
    compose_file = _REPOSITORY_ROOT / invocation.argv[7]
    if (compose_file != _REPOSITORY_ROOT / "deploy/shopping/compose.yaml"
            or compose_file.is_symlink()
            or not compose_file.is_file()
            or compose_file.resolve() != compose_file):
        raise RuntimeError("repository Compose file identity unavailable")
    try:
        command = [
            _trusted_compose_executable(),
            *invocation.argv[1:3],
            *invocation.argv[4:],
        ]
        completed = subprocess.run(
            command, cwd=_REPOSITORY_ROOT, env=_fixed_environment(), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
            check=False,
        )
    except Exception: return ExecutionOutcome.UNCERTAIN
    return ExecutionOutcome.SUCCEEDED if completed.returncode==0 else ExecutionOutcome.FAILED

def run():
    try: authorization=WordPressPortAuthorizationStore.open_existing()
    except Exception: authorization=None
    return execute_reconciliation(observe_runtime=_observe_runtime,observe_storage=observe_storage_continuity,authorization=authorization,runner=_run_compose)

def main():
    """Execute the fixed governed operation once and emit its safe projection."""
    try:
        result = run()
        print(json.dumps(result.to_json_safe(), sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        error = {
            "error": "WORDPRESS_PORT_OPERATOR_CLI_FAILURE",
            "failure_stage": "OPERATOR_CLI",
            "reason_codes": ["WORDPRESS_PORT_OPERATOR_CLI_FAILURE"],
            "authorization_consumption_state": "UNCERTAIN",
            "authorization_consumed": None,
            "production_authority": False,
            "ubuntu_authority": False,
        }
        print(json.dumps(error, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 1

__all__=("main","run")

if __name__ == "__main__":
    raise SystemExit(main())
