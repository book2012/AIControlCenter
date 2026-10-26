# PROD SQLite connection closure — approval-ready candidate

Status: SOURCE_VALIDATED. NOT_DEPLOYED. PRODUCTION_ACTIVATION_REQUIRES_SEPARATE_AUTHORIZATION.

## Trigger and resulting behavior

PROD API currently answers HTTP 200 with poller and product management RUNNING. PID 85957 was observed with 213 file entries, including 52 inquiry handles and 95 Telegram router handles. This is a point-in-time observation, not a measured growth rate or a prediction of when it will stop responding.

DEV had already stopped accepting requests with Errno 24. Checkout closure alone removed checkout handles but left an independent inquiry leak. Applying both fixes on DEV yielded 13 successful health samples over 120 seconds, constant 63 file entries, and zero sampled checkout/inquiry handles. That is short-term evidence, not long-term certification.

## Exact candidate boundary

Base: live PROD API source `3bf63c045c22fa332e176ae6703e4e71423ea84e`.
Branch: `feature/prod-connection-candidate-20261027`.

Production code changes are limited to deterministic connection closure around existing SQLite transaction contexts:

- `core/shopping/order_core/guest_checkout.py`: 7 sites.
- `core/shopping/guest_operator.py`: 1 site.
- `ops/macos/shopping/dev_inquiry_queue.py`: 11 sites; this adapter is also composed by the PROD runtime.
- `core/shopping/operator_environment.py`: 4 sites.

The outer closing context runs after existing transaction commit/rollback. Schema, permissions, provider configuration, order-state semantics, claim-before-dispatch behavior and non-retry after uncertain outcomes are preserved. No SENS or other unreleased DEV feature is included.

## Validation

75 focused tests passed on this exact PROD baseline with one existing Starlette warning. New router regressions failed before the fix and pass after it; they verify conversation and non-conversation dispatch/replay, conflicting updates, and handler failure remaining claimed without redispatch. Existing checkout/inquiry lifecycle and checkout/order/fulfillment/customer-isolation tests available on this baseline also pass.

The whole project suite has not been run. Git diff whitespace validation is required before commit and will be recorded in execution evidence.

Fresh SQL and media backups exist under `/Users/kyouhan/AIControlCenterAudit/20261027/backups`. Fresh SQL restored 50 tables with mariadb-check success, and media restored 8,396 members / 7,193 regular files. SQLite backup copies passed integrity checks. Cross-store atomicity and full application recovery are not claimed.

## Proposed action after explicit approval

1. Re-observe live PROD API identity and ensure it still uses `3bf63c0`. If changed, stop and rebuild the candidate against the new baseline.
2. Recheck durable router/order/bridge/outbox state, active sessions and pending writes. Do not restart while an in-flight or uncertain operation requires reconciliation.
3. Take a fresh timestamped application DB/SQLite snapshot and save the current PROD API launch plist and release metadata without printing secrets.
4. Archive the approved clean candidate Git commit to a new immutable PROD API release directory; verify source hashes and provenance.
5. Change only `com.aicontrolcenter.prod-commerce-api` to that release using the session-compatible launchd lifecycle, then start it. A brief API/admin/bot interruption is expected during restart; measure duration.
6. Verify actual process cwd, `/shopping/health`, public storefront response and operator polling status. Observe descriptors and SQLite handles without sending a Telegram message or mutating a real order.
7. If startup or validation fails, restore the saved launch plist/metadata and start the retained `3bf63c0` release. Re-observe health; never blindly replay an uncertain order operation.
8. Update service-specific release evidence and documentation with the actual outcome.

Homepage, WordPress/container generation, Caddy, DNS, database schemas, SMS providers and senders are outside the proposed activation. Existing background queues resume according to their current contracts; approval does not authorize synthetic messages, refunds or order tests on PROD.

## Approval requirement

The repository AGENTS.md states: `Production activation requires a separate authorization gate.` It also restricts production writes. The user's instruction to proceed as far as possible without required approval has been used for inspection, backups, isolated restore, source/test/documentation work and DEV recovery. It has not been treated as the separate PROD activation authorization. The next approval is specifically the scoped PROD API release and restart described above.
