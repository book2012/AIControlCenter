# Autonomous Delivery Controller

AUTO-01 defines architecture and deterministic planning only. M4-A3 is closed
at `873ad5cc8fcbf2cb48bd3205ce1ee6451c5338ec` with
`READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`.

AIControlCenter is the single Control Plane and owns roadmap compilation,
scheduling, dependencies, policy, authorization, approvals, retries, recovery,
evidence, completion and deployment control. Codex is a bounded, replaceable
implementation executor. It is never governance, approval, audit, scheduling,
recovery or retry authority.

## Autonomy

- L0 observes read-only Git and test evidence.
- L1 produces architecture, manifests and deterministic roadmap plans.
- L2 permits test-only, side-effect-free implementation.
- L3 permits bounded code, tests, documentation, one commit and push.
- L4 requires independent human approval and bounded operational authorization;
  a single-use permit and atomic claim apply where policy requires them.
- L5 requires its own architecture gate, independent production approval,
  production authorization and fail-closed recovery.

Least privilege is the default and a manifest cannot self-escalate. Readiness
and approval do not imply authorization or activation.

## Lifecycle and boundaries

The success path is `PLANNED → PREFLIGHT → RUNNING → VALIDATING →
DOCUMENTING → COMMITTING → PUSHING → CLOSED`. The typed validator prohibits
skips, environment-only decisions, running before exact-baseline evidence,
committing before tests and documentation, pushing before commit evidence, and
closing before remote verification. Approval cannot be crossed automatically.

`BLOCKED`, `FAILED_CLOSED`, `AWAITING_APPROVAL`, `RECOVERY_REQUIRED` and
`CANCELLED` are explicit non-success states. Transition evidence is immutable.
No automatic retry is allowed after a real claim.

The planner is pure and in-memory: no network and no filesystem mutation.
Ubuntu can later participate only as a stateless infrastructure worker and
cannot own orchestration or state. API routes, n8n, WordPress, WooCommerce and
Codex cannot acquire governance authority.

AUTO-01 creates no runner, subprocess, shell adapter, daemon, launchd service,
network client, authorization, permit, claim or operational write. AUTO-02 will
design the persistent runner, terminal independence, adapter and recovery
mechanics behind separate gates. Persistent state and launchd remain future
work. Production is `NOT_AUTHORIZED`; no `.env` or application secret is
required. The existing 427 deprecation warnings remain separate backlog.

Decision: `READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Closeout and Deferral Status

AUTO-01 is an architecture-only foundation and is closed.

Persistent runner implementation, automatic ROADMAP execution and
continued controlled-activation work are deferred. Codex remains a
bounded replaceable executor and does not own governance, approvals,
retry policy or production authorization.

The next active task is `SHOP-00_ARCHITECTURE_REPRIORITIZATION`.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->
