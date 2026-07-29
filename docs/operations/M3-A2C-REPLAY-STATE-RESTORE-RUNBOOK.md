# M3-A2C Replay-State Restore Runbook

This runbook describes test-validated recovery and grants no activation
authority.

1. Supply existing backup and canonical manifest paths plus a separate,
   nonexistent restore target under an existing restore root.
2. Reject repository, protected, Ubuntu, network/removable, symlink, traversal,
   secret-bearing, overlapping and existing-target paths.
3. Verify manifest canonical form and digest, database byte digest, schema
   version, event count, logical ledger digest and derived state digest.
4. Inspect the backup read-only and require a healthy chain and lifecycle.
5. Restore through SQLite `Connection.backup` into a mode `0600` temporary file
   within the restore root.
6. Reinspect and prove exact event IDs, sequences, hashes, payload bindings and
   every permit state before atomic rename.
7. Confirm unchanged backup bytes and that the restored file was not selected
   operationally.

Operational restore: `NOT PERFORMED`. Operational writer: `NOT ACTIVATED`.
Production activation: `NOT_AUTHORIZED`.
