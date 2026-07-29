# M3-A1B Audit Append Checklist

Status: validation-only; operational activation is not authorized.

Before any future separately authorized composition:

- Confirm the Mac mini M4 remains the single Control Plane and ledger owner.
- Inject an absolute, non-repository, non-symlink application-state path.
- Confirm the parent and database already exist; do not create either.
- Confirm the database schema matches `dpl/audit-sqlite/v1`.
- Confirm both unique indexes and both UPDATE/DELETE rejection triggers exist.
- Confirm WAL was configured beforehand; the writer must not change it.
- Confirm `foreign_keys=ON`, `synchronous=FULL`, and bounded busy timeout.
- Confirm the request is canonical, non-production and contains no prohibited
  secret, environment, shell, command, argv or script fields.
- Confirm full-chain validation succeeds before append.
- Confirm read-back verification succeeds before commit.
- Confirm an idempotent retry adds no row.
- Confirm failure leaves no partial row.

M3-A1B does not authorize operational database creation, schema bootstrap,
migration, repair, backup execution, API write routes, Ubuntu ownership,
service restart or Production activation. Production remains
`NOT_AUTHORIZED`.

