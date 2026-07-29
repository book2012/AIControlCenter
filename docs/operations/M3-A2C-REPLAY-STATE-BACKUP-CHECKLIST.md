# M3-A2C Replay-State Backup Checklist

This checklist documents a validated boundary; it does not authorize an
operational backup.

1. Supply separate explicit absolute source, backup and manifest paths.
2. Require the supplied backup root to exist outside Git, protected, Ubuntu,
   network and removable storage.
3. Reject symlinks, traversal, secret-bearing names, overlaps and conflicting
   outputs.
4. Require M3-A2A inspection `HEALTHY`, valid schema/indexes, chain and
   lifecycle, and zero replay/privacy/Production violations.
5. Record source bytes and source inspection-report binding.
6. Use only SQLite `Connection.backup` into a mode `0600` temporary file inside
   the supplied root.
7. Reinspect and compare it, write the canonical manifest and atomically rename
   both verified outputs.
8. Confirm unchanged source bytes and cleanup of partial outputs on failure.

Validated only under pytest temporary paths. Operational schedule:
`NOT ACTIVATED`; Production activation: `NOT_AUTHORIZED`.
