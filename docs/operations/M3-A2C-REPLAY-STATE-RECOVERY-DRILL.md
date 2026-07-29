# M3-A2C Replay-State Recovery Drill

The completed pytest-only drill covers empty and multi-lifecycle ledgers with
persistent `RESERVED`, `CONSUMED` and `FAILED_CLOSED` states.

Recovery proves complete ordered event, identity, hash, count and derived-state
equality, healthy inspection, zero replay violations, no secret/raw nonce
material and no Production authorization. Post-recovery retries cannot reuse
terminal permits or create duplicate events.

Two bounded in-process threads use independent SQLite connections for identical
reservation attempts and conflicting terminal transitions. Exactly one
reservation commits, the identical loser is idempotent, exactly one terminal
commits and the conflict is denied. Reinspection requires a healthy ledger
with no duplicate sequence or event ID.

Controlled failures cover backup before rename, manifest write, restore before
rename, integrity rejection and interrupted reservation/terminal transactions.
Partial final files are absent, transactions roll back and original source and
backup bytes remain unchanged.

Only pytest temporary artifacts were created. No operational database, backup,
restore, transition, schedule, writer or Production capability was activated.
