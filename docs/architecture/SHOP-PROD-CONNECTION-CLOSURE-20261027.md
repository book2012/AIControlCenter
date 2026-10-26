# PROD connection lifecycle candidate

Mac AIControlCenter continues to own orchestration and business state. No Ubuntu or external authority changes.

One SQLite connection is owned by one persistence operation and is closed deterministically after the existing transaction context exits. The implementation preserves read-only URI flags, claim-before-dispatch, idempotency, rollback and uncertain-outcome non-retry semantics. Four existing modules change; no global monkeypatch, connection pool or schema migration is introduced.

[Baseline, validation, proposed activation and rollback](../operations/PROD_CONNECTION_CANDIDATE_20261027.md). Production remains unchanged until the separate activation gate is satisfied.
