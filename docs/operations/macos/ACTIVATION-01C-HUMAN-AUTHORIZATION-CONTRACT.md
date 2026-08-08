# ACTIVATION-01C Human Authorization Contract

<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:START -->
## ACTIVATION-01C Controlled Pointer Activation

Status: `COMPLETE`

Authorized transition:

`b9ad351a7241 -> acd80ab9f6ae`

Runtime pointer activation:

`PASS`

Activation report SHA-256:

`d59a3aa81accca4e6f330c85774924221e33e247376a069a1d922f5716dec24a`

Natural launchd KeepAlive recovery:

`PASS`

Explicit service restart commands:

`0`

Launchd state:

`running`

Listener:

`127.0.0.1:18100`

Listener/PID correlation:

`PASS`

Approved wrapper SHA-256:

`a58d926f8845f6b0aa7863250b02c0c461ea843bfa03a83313eaaa547ca98212`

Wrapper serving target:

`core.api.shadow:app`

HTTP validation:

- `GET /health -> 200`
- `GET /runtime/health -> 200`
- `POST /health -> 405`

Post-activation ACTIVATION-01B inspection ID:

`activation-inspection-bc8f2b34d45242c4b835d4ba852667a3`

Post-activation report digest:

`sha256:f419242b927804a6c97ad947ad4eb2deb9b2a07545724d750fd85ab3a80def22`

01B terminal status:

`BLOCKED`

Remaining transition-phase blockers:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","PROCESS_SERVING_TARGET_MATCH","RUNTIME_CURRENT_MATCH"]`

Operational Runtime, launchd, listener and HTTP checks passed.

The residual blockers are contract-phase mismatches:

- pre-activation Runtime expectation
- Control Plane Git identity versus Candidate source identity
- launchd wrapper indirection versus direct serving-target inference

01C independently verifies the exact approved wrapper SHA and its
static `uvicorn core.api.shadow:app` exec chain.

Rollback executions:

`0`

Explicit launchd mutation commands:

`0`

Caddy changes:

`0`

Public openings:

`0`

Ubuntu changes:

`0`

Production authorization:

`NO`

ACTIVATION-01C does not constitute PI-009 Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:END -->

Status: `FROZEN`

Production authorization: `NO`

## Approval Subject

Requested mutation:

`runtime/current`

Current target:

`/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/b9ad351a7241`

Authorized candidate:

`/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/acd80ab9f6ae`

Expected source commit:

`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

## Required Human Authorization

The pointer mutation must not execute until explicit human approval
is recorded after this contract is frozen.

Canonical approval statement:

`ACTIVATION-01C AUTHORIZE POINTER SWITCH acd80ab9f6ae FROM b9ad351a7241`

Equivalent explicit approval is acceptable only when it clearly
identifies all of the following:

- ACTIVATION-01C
- pointer switch
- source Runtime `b9ad351a7241`
- target Runtime `acd80ab9f6ae`

General instructions such as "continue", "proceed", or "next" do not
constitute this mutation authorization.

## Exact Mutation Allowlist

One invocation only:

    bash ops/macos/runtime/bootstrap-production-runtime.sh --mode activate --release "/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/acd80ab9f6ae" --expected-source-commit "acd80ab9f6aeb848900e1a19e3fa3afd69face8a"

This command may:

- validate the immutable Candidate Runtime
- atomically replace `runtime/current`
- write the canonical activation report produced by the existing
  Runtime bootstrap script

It may not issue service-management commands.

## Service Authority

Explicit service mutation is not included.

The following remain unauthorized:

- kickstart
- bootstrap
- bootout
- restart
- launchd configuration changes

Existing KeepAlive behavior may naturally retry the daemon after the
pointer changes.

## Immediate Validation Requirement

After the activation command returns, read-only validation must
verify the pointer and execute the ACTIVATION-01B inspector.

No second mutation may occur during validation.

## Failure Handling

If activation validation fails:

- stop
- preserve evidence
- do not kickstart
- do not repair the immutable Candidate Runtime
- do not automatically roll back

Rollback requires separate authorization.

## Rollback Authorization

The previous target `b9ad351a7241` is evidence, not permission.

Any rollback must name its target and receive a new explicit human
authorization.

## Production

This contract does not authorize Production.

PI-009 and HUMAN-APPROVAL-GATES remain authoritative for Production
authorization.
