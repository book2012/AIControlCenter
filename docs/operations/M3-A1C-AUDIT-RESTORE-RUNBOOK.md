# M3-A1C Audit Restore Runbook

Status: validation-only; operational restore is `NOT PERFORMED`.

1. Inject an existing backup and canonical manifest, an existing restore root
   and a separate nonexistent target.
2. Verify path policy, non-overlap, manifest digest, database byte digest,
   logical ledger digest, schema and M3-A1A health.
3. Restore through SQLite online backup to a restrictive temporary file.
4. Require exact event count, ordered identity, payload digest, previous hash
   and event hash equality.
5. Require M3-A1A `HEALTHY` before atomic rename.
6. Retain the immutable receipt as validation evidence only.

Never overwrite, create a parent, repair, migrate or automatically activate.
Failure must leave no final restored database.
