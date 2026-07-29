# M3-A1C Audit Backup Checklist

Status: validation-only; operational backup is `NOT ACTIVATED`.

1. Inject an existing healthy source and existing Mac application-state backup
   root outside Git.
2. Inject nonexistent backup and manifest paths directly below that root.
3. Inject the semantic creation timestamp; keep production and operational
   flags false.
4. Require M3-A1A `HEALTHY`, valid schema and chain, and zero privacy and
   production violations.
5. Verify receipt, manifest digest, database byte digest and logical digest.
6. Confirm source bytes are unchanged and final files are restrictive.
7. Accept only an exact idempotent retry; deny conflicting existing content.

Do not create directories, copy a live WAL file, run commands, repair, migrate,
schedule, activate or use Ubuntu, network or removable storage.
