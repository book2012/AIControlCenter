# M3-A1A Audit Integrity Checklist

- Confirm the configured path was explicitly injected and passes Mac
  application-state policy.
- Confirm a missing file returns `UNAVAILABLE` and remains missing.
- Confirm SQLite header, URI `mode=ro`, `query_only`, bounded timeout and
  deterministic connection close.
- Review schema version, required tables, columns and unique indexes.
- Review journal mode, foreign-key setting and `quick_check`.
- Review event count, sequence bounds, duplicate IDs/sequences and gaps.
- Review previous-hash continuity and canonical event identity/hash results.
- Review privacy and prohibited Production-authorization findings.
- Confirm payload contents are absent from findings and reports.
- Confirm writes, migrations and repairs all equal zero.
- Confirm no database file is staged and Production remains
  `NOT_AUTHORIZED`.

The inspector never repairs findings. Escalate any non-`HEALTHY` report for
offline investigation. M3-A1B is the next separately gated task.
