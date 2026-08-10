# SEC-02 Controlled Mutation Policy

Status: `SEC_02A1_FINAL_STATUS=GOVERNANCE_DOMAIN_AND_JSON_CONTRACT_FROZEN`

This operator policy applies to future SEC-02 controlled-mutation workflows.
SEC-02A is not a Production mutation implementation and grants no operational
authority.

## Before consumption

Validate the request and contract, authorization identity and scope, then
recollect all bound preconditions and compare exact bindings and the snapshot
digest. Validate the exact action line item and allowed count before claiming
authorization.

Any bound drift stops the workflow with zero controlled invocation and changes
an `AUTHORIZED` authorization to terminal `STALE`. Expiry before claim is
`STALE` with `AUTHORIZATION_EXPIRED`. Neither condition may be repaired in
place; a new request, snapshot, and human decision are required.

## Consumption boundary

Authorization consumption is an atomic, irreversible claim immediately before
execution-start evidence and the first bounded adapter call. Ambiguous claim or
persistence status fails closed. Treat the authorization as non-reusable until
manual inspection establishes durable state; never infer permission from an
absent receipt alone.

A desired state, manifest, idempotency key, or remaining budget is not
authorization. Consumed authority never becomes available again, including
when no invocation was completed.

## Mutation-budget accounting

Every authorization has explicit action line items with `action_type`,
`allowed_count`, `actual_invocation_count`, `completed_count`,
`uncertain_count`, and `status`.

- `AVAILABLE`: not claimed; no controlled invocation crossed.
- `CONSUMED`: claimed; zero or more boundaries may have been crossed. This does
  not permit retry.
- `EXHAUSTED`: the authorized invocation count is fully used.
- `VIOLATED`: an invariant/count was exceeded or safety cannot be proven; this
  is a terminal safety incident.

Increment `actual_invocation_count` when the typed adapter invocation boundary
is crossed, whether the outcome succeeds, fails, or is uncertain. Increment
`completed_count` only for confirmed completion and `uncertain_count` for an
outcome that cannot be proven. `remaining_count` is accounting only and never
permission to retry after failure.

## Execution and failure

After atomic consumption:

1. persist execution-start audit evidence;
2. cross exactly the authorized adapter boundary;
3. record the receipt;
4. validate postconditions;
5. persist durable evidence;
6. complete any applicable Git/documentation gate.

On any failure after consumption: stop. Keep authorization `CONSUMED`. Do not
automatically retry, roll back, compensate, replay an idempotency key, or reuse
the claim. `VIOLATED` never triggers automatic compensation. Manual recovery
requires inspection and a separately planned and authorized lifecycle.

## Evidence handling

Write canonical, schema-versioned JSON to configured durable Mac Control Plane
storage using atomic writes, restrictive permissions, and durability
confirmation. `/private/tmp` is never authoritative durable evidence. Preserve
failure evidence even when execution, postcondition checks, or final evidence
persistence fails.

Git may contain a value-free summary/closeout only. It cannot authorize work and
must avoid host-sensitive absolute paths, secret values, and credential
identifiers.

Never collect provider secret values, secret-derived hashes/comparisons,
prefixes/suffixes, access-granting authorization material, raw Authorization
headers, cookies, raw environments, secret-bearing commands, or opaque provider
responses that might contain credentials.

## Manual recovery

After `STALE`, `CONSUMED`, `REJECTED`, an uncertain result, persistence
ambiguity, or `VIOLATED`, an operator must inspect durable state and evidence.
Any further mutation needs a completely new request, fresh snapshot, exact
human authorization, and new budget. Production validation is a separately
authorized layer and is outside SEC-02A.

## Normative post-consumption failure invariants

These markers are normative Control Plane safety contracts:

- **NO AUTOMATIC RETRY** — after authorization consumption or a controlled
  mutation invocation boundary is crossed, failure never grants permission
  to repeat the mutation automatically. Any later attempt requires a new
  request, fresh precondition snapshot, and explicit human authorization.

- **NO AUTOMATIC ROLLBACK** — failure after authorization consumption never
  triggers an automatic compensating mutation. Evidence is preserved and the
  workflow stops for explicit operator review and separately authorized
  recovery, if any.

Remaining mutation-budget count is accounting information only. It is never
retry authority.
