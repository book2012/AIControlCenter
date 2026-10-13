# DEV order lookup recovery — 2026-10-13

Two independently reproduced failures: the over-escaped JavaScript digit regex skipped public lookup; the DEV API exhausted its file descriptor limit with retained SQLite connections (174 aftersales and 52 dialogue handles observed). SQLite transaction context managers commit/rollback but do not close the connection.

The UI now recognizes 10-digit public numbers, does not probe a customer session on page load, and does not fall back to authentication on public lookup failure. A transaction context helper closes connections in a finally block while preserving commit/rollback semantics. Applied to aftersales, returns/refunds, dialogue, DEV product operations and SMS outbox. No global SQLite monkeypatch or garbage-collection workaround.

Validation: UI script execution verifies actual numeric input renders an order without a session request and missing orders remain unauthenticated. Retained-reference transaction tests repeat 300 writes and verify closed handles plus rollback. 168 focused regressions passed. Production activation is prohibited in this task; no real orders, payments, inventory or SMS configuration changes.

Deploy clean commit archives into independent DEV API and homepage releases, preserve prior immutable releases, restart only DEV services, and verify public lookup repeatedly plus stable database descriptor usage. DEV edge Basic Auth remains as configured; widening public paths is not part of this recovery.
