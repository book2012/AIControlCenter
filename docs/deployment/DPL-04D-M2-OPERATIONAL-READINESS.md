# DPL-04D M2 Operational Readiness Gate

Status: **CLOSED**

`core.deployment.m2_readiness` evaluates immutable, injected JSON evidence.
The gate is pure and deterministic: it performs no Git, filesystem, runtime,
network, executor, Ubuntu or production probe. Stable check order, canonical
JSON, report ID and digest derive only from semantic evidence and the explicit
evaluation timestamp.

The thirteen mandatory categories cover Control Plane ownership, deployment
contracts, Mac inventory and ingress, dependency boundaries, planning,
authorization, replay protection, typed executor policy, the Mac sandbox,
audit architecture, tests, Git/documentation and zero safety counters.
Complete passing evidence returns
`READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX`; complete failing evidence
returns `NOT_READY`; missing, malformed or contradictory evidence returns
`BLOCKED`.

A ready decision is restricted to sandbox-only, Mac-Control-Plane-only,
non-production evaluation. It provides no real infrastructure executor,
Ubuntu execution, production authorization, public write API or pilot
activation. Operator authorization is still required. The persistent SQLite
audit adapter remains absent and is required before a broader mutable
deployment milestone.

DPL-04A, DPL-04B, DPL-04C, DPL-04D and DPL-04 are closed after validation.
The canonical passing fixture establishes `M2 READINESS_ACCEPTED`, not
deployment or completion. `M2 ACTIVATION_NOT_STARTED` and Production
activation is `NOT_AUTHORIZED`.

M2-P1 is now CLOSED and its pilot authorization policy is AVAILABLE. This does
not change the DPL-04D readiness decision: pilot activation remains NOT
STARTED, persistent SQLite audit remains NOT IMPLEMENTED, and Production
activation remains `NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot
Activation and Evidence.
