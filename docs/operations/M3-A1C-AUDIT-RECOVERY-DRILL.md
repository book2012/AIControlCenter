# M3-A1C Audit Recovery Drill

The drill runs only with pytest temporary databases and roots.

1. Bootstrap the inert M3-A1B test schema and inspect it with M3-A1A.
2. Record source bytes and logical ledger identity.
3. Back up and verify the canonical manifest.
4. Restore to a separate nonexistent pytest path.
5. Compare schema, count, ordered event identities, payload digests, previous
   hashes, event hashes and all logical ledger digests.
6. Reinspect the restored database and require `HEALTHY`.
7. Repeat with the same semantic inputs and require stable IDs and report.
8. Exercise corrupt database, modified manifest, overlap, symlink, existing
   target, forbidden payload and production-authorization denials.
9. Confirm source and backup are unchanged and failures leave no final output.

`RECOVERY_VALID` does not authorize operational selection. Operational
databases, schedules and restores remain zero. No migration, repair, Ubuntu
change, command, network activity or Production activation is part of the
drill.
