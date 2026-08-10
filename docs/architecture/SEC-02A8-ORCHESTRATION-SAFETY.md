# SEC-02A8 Orchestration Policy and Safety

Status:
`SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`

Next: `SEC-02A9 DURABLE EVIDENCE AND API PROJECTION`

## Pure application boundary

A8 answers only: **what is the next permitted governance disposition?** The
immutable orchestration context composes A2-A5 domain facts, and the immutable
decision projects one of exactly five dispositions:

- `ALLOW_AUTHORIZATION_CONSUMPTION`
- `ALLOW_SINGLE_INVOCATION`
- `REQUIRE_POSTCONDITION_VALIDATION`
- `ALLOW_CLOSEOUT`
- `STOP`

The policy imports no port or adapter and performs no external action. It does
not consume authorization, change mutation accounting, invoke execution,
validate a postcondition, persist evidence, read the clock, or create an
identity or digest. Progress dispositions are narrow permissions for a later
external Governance coordinator, never proof that the permitted boundary was
crossed.

## Fail-closed ordering

Existing failure evidence stops evaluation before progress. Exact lifecycle,
authorization, claim, request, budget, execution, action, and postcondition
bindings are then checked. Non-authoritative lifecycle states, absent or
drifted current preconditions, missing consumption evidence, violated or
exhausted accounting, failed or uncertain execution, and failed
postconditions all produce `STOP`. A lower-priority success fact cannot
override one of these blockers.

Current preconditions are required both before authorization consumption and
again before the single-invocation permission. Drift after consumption stops
with manual action required; consumed authority remains consumed and cannot be
restored or reused.

## Consumption and single invocation

`ALLOW_AUTHORIZATION_CONSUMPTION` requires `AUTHORIZED`, a current `MATCH`, an
exact-bound `AVAILABLE` budget, no failure or consumption evidence, no
execution receipt, and no prior-invocation ambiguity. It grants permission
only for a later atomic claim operation.

`ALLOW_SINGLE_INVOCATION` requires `CONSUMED`, an exact-bound committed
consumption receipt and execution request, a revalidated current `MATCH`, and
an explicit unattempted action line item in a `CONSUMED` budget. It permits
exactly one later controlled invocation boundary. A different composite action
requires its own explicit execution request and fresh evaluation.

## No retry or rollback authority

Every decision freezes `retry_prohibited=true` and
`rollback_prohibited=true`. Remaining mutation count is accounting only. A
failed or uncertain receipt always stops, including when remaining count is
positive. An already-attempted action is not made eligible by unused count.
No retry, rollback, compensation, replay, or multi-attempt loop API exists.

Completed execution without a matching postcondition report requires
postcondition validation. Completed execution plus `PASS` permits closeout
only; it creates no authorization or further invocation permission. `FAIL`
stops and requires manual action. Existing failure evidence always stops and
retains its non-retryable, non-rollback safety intent.

## Validation state

External validation of the focused Governance regression reported `231 passed
in 1.42s`, validating the pure A8 orchestration policy at milestone
`SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. The focused modules
cover progress gates, priority-ordered denials, binding failures, precondition
revalidation, deterministic immutable projection, and source-level exclusions
for ports, adapters, side effects, retry, rollback, compensation, and attempt
loops. This was not a full repository regression.

A8 adds no Production, Runtime, provider, Ubuntu, filesystem, network,
subprocess, SQLite, Git-command, environment, secret, clock, persistence,
public mutation API, or concrete adapter capability. No Production, provider,
or Ubuntu mutation occurred. The milestone
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` is not claimed. Notion
remains `DEFERRED_UNTIL_FINAL_PHASE`.
