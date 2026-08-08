# ACTIVATION-01C Human Authorization Contract

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
