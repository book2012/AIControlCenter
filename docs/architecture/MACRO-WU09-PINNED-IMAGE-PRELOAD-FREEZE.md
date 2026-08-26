# Macro-WU09 Pinned-Image Preload Architecture Freeze

## Status

This document freezes the architecture for a future Macro-WU09 pinned-image preload capability. It is documentation only and grants no Production authority.

- `WU09_IMAGE_PRELOAD_FREEZE_GATE=FROZEN`
- `CODE_CHANGE_REQUIRED=true`
- `CANONICAL=NOT_RUN`
- WU09 repository implementation exists.
- WU09 Production deployment has not occurred.
- No WU09 pinned-image preload Production authorization has been consumed.
- The exact pinned image is currently absent locally.
- No concrete bounded WU09 image-preload execution capability exists yet.

## Separate Production Mutation Boundary

WU09 image preload is a separate Production mutation from WU09 deployment. One preload authorization permits exactly one bounded image-pull invocation and nothing else. The preload authorization grants no deployment authority. WU09 deployment requires a fresh, later authorization and must pass its own authorization and execution gates.

The stable action identifier is:

`SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT`

The invocation is hard-bound to:

- Docker context: `colima-aicontrolcenter-commerce`
- Image: `alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1`

The authorization and bounded capability must not accept caller-supplied argv, Docker context, image name, tag, digest, registry, or alternate target. Desired state is not activation authorization.

## Frozen Execution Constraints

The future preload capability must enforce all of the following:

1. No caller-supplied argv.
2. No caller-supplied Docker context.
3. No caller-supplied image, tag, or digest.
4. No shell execution.
5. No retry.
6. No fallback tag.
7. No alternate digest.
8. No alternate registry or image.
9. No container deployment.
10. No database mutation.
11. No network mutation.
12. No credential access.
13. No MariaDB connection.
14. No SQL.
15. No WU10 authority.
16. No WU11 authority.

The preload path must not be routed through `UbuntuWorkerClient.execute`, a generic remote-command facility, or a generic Docker execution surface.

## Reused Governance and Execution Semantics

Existing SEC-02 domain semantics, durable authorization consumption, mutation budgets, and the `ControlledExecutionPort` abstraction are reusable. Their semantics are frozen unchanged:

- Governance core remains unchanged.
- SEC-02 semantics remain unchanged.
- `ControlledExecutionPort` semantics remain unchanged.
- One authorized mutation budget permits one bounded invocation only.
- Authorization consumption remains durable.

The Mac remains the sole Control Plane. Ubuntu is a stateless infrastructure worker with zero authority and must not own, authorize, orchestrate, or execute this preload capability.

## Required Future Implementation

Future code must provide exactly one Mac-only, non-generic `ControlledExecutionPort` adapter dedicated to the hard-bound preload action. It must provide read-only precondition observation for the exact preload and read-only postcondition validation proving that the exact pinned image is present. It must expose no generic Docker execution surface.

The implementation is required before any preload can be authorized or performed. This freeze does not constitute implementation, approval, activation, or authorization consumption.

## Preconditions

Before the single authorized mutation, read-only observation must prove all of the following:

- Execution is on the Darwin/Mac Control Plane.
- Git is clean and upstream aligned.
- Docker context `colima-aicontrolcenter-commerce` is reachable.
- The exact digest `alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1` is absent before mutation.
- The WU09 adapter container is absent.
- Host port `58083` is free.
- `ai-shopping-internal` exists and is internal.
- `shopping-db` is running and attached.
- No WU09 deployment is already active.

Failure or ambiguity in any precondition must fail closed without mutation and without retry or fallback.

## Postconditions

After the one bounded invocation, read-only validation must prove all of the following:

- The exact digest `alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1` is present locally in Docker context `colima-aicontrolcenter-commerce`.
- The WU09 adapter was not deployed by the preload.
- No unrelated runtime mutation is claimed.

Postcondition reporting must remain evidence-bound. It must not infer deployment authority, deployment completion, database changes, network changes, or any unrelated runtime effect from image presence.

## Authority and Review Record

- `EXACT_ACTION_TYPE=SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT`
- `GENERIC_EXECUTOR_ALLOWED=NO`
- `CALLER_SUPPLIED_ARGV_ALLOWED=NO`
- `RETRY_ALLOWED=NO`
- `FALLBACK_ALLOWED=NO`
- `WU09_DEPLOYMENT_AUTHORIZED=NO`
- `WU10_AUTHORIZED=NO`
- `WU11_AUTHORIZED=NO`
- `PRODUCTION_ACCESS_PERFORMED=NO`
- `PRODUCTION_MUTATION_PERFORMED=NO`
- `PRODUCTION_AUTHORIZATION_CONSUMED=NO`
- `CANONICAL=NOT_RUN`

The previous review did not run canonical. No Production access, Docker mutation, authorization consumption, pytest, canonical validation, staging, commit, or push is authorized or recorded by this freeze.
