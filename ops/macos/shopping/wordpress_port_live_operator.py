"""Zero-argument Mac-local operator for the fixed WordPress reconciliation."""
from __future__ import annotations
import json, subprocess
from core.shopping.observability.storage_continuity import StorageContinuityObservation
from core.shopping.wordpress_port_reconciliation import (
    COMPOSE_PROJECT, DATABASE_CONTAINER, TARGET_CONTEXT, WORDPRESS_CONTAINER,
    ContainerRuntimeFact, ExecutionOutcome, MutationInvocation,
    WordPressPortRuntimeFacts, build_mutation_invocation, execute_reconciliation,
)
from ops.macos.shopping.storage_continuity_observer import observe_storage_continuity
from ops.macos.shopping.wordpress_port_authorization_store import WordPressPortAuthorizationStore

def _command(argv):
    return subprocess.run(list(argv),text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=False)

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
    try: completed=_command(invocation.argv)
    except Exception: return ExecutionOutcome.UNCERTAIN
    return ExecutionOutcome.SUCCEEDED if completed.returncode==0 else ExecutionOutcome.FAILED

def run():
    try: authorization=WordPressPortAuthorizationStore.open_existing()
    except Exception: authorization=None
    return execute_reconciliation(observe_runtime=_observe_runtime,observe_storage=observe_storage_continuity,authorization=authorization,runner=_run_compose)

__all__=("run",)
