# SHOP-SERVICE-START-01G1C WordPress generation boundary

Mutation identity: `SHOP-SERVICE-START-01G1C:WORDPRESS_RUNTIME_GENERATION_RECONCILIATION`.
This implementation does not issue live authorization or perform live mutation.
The consumed 01B port authorization remains unchanged and cannot authorize 01G1C.

The dedicated issuer is `ops.macos.shopping.issue_wordpress_generation_authorization`.
The dedicated zero-argument operator is `ops.macos.shopping.wordpress_generation_operator`.
Both reject CLI arguments. Any future issuance and execution require a separately
approved task, a reviewed committed repository and a clean worktree. This task
leaves its implementation uncommitted as requested, so live preconditions would fail.

The interactive issuer requires the exact `AUTHORIZE` acknowledgement followed by
the mutation identity. It binds two matching non-secret observations before the
prompt and rechecks after acknowledgement. The ten-minute, single-use record lives
at the trusted passwd home's `Library/Application Support/AIControlCenter/authorization/wordpress-generation-01g1c-authorization.sqlite3`.
Its independent schema, application ID, exact authorization/receipt types and
mutation identity reject 01B stores and records without migrating them.

Bound identity includes HEAD, clean worktree, reviewed Compose/Apache/PHP digests,
WordPress and database container IDs, StartedAt and restart counts, pinned image,
both named volume Name/Driver/Scope/CreatedAt identities, exact publishers, exact
network membership with network IDs/internal flags, and the current mount closed
set. The stale candidate must have only the WordPress volume and storefront bind.
Named volumes must use the canonical local Docker volume source paths; different
paths fail closed. The trusted source resolver's filesystem contract is reused by
opening and obtaining metadata only: no env content read, parsing or hashing.
Filesystem identity is bound too. No environment values, logs, headers, credentials,
capability, verifier or bearer data enter the record or result.

The store obtains a SQLite immediate transaction, re-observes the full binding,
checks expiry again, and only then claims authorization durably. Drift or unknown
facts fail before consumption and mutation. A durable claim cannot become available
again. A committed read-back receipt is required before execution. Failures after
claiming remain consumed or uncertain and never cause execution retries.

The operator prepares the existing trusted Homebrew Compose executable with the
existing fixed environment and the trusted passwd-home env path. Its closed-over
command is equivalent to:

```text
docker --context colima-aicontrolcenter-commerce compose --project-name ai-shopping --file deploy/shopping/compose.yaml --env-file <trusted-passwd-home runtime source> up -d --no-deps --pull never --force-recreate wordpress
```

Only this WordPress lifecycle call can occur, once. There is no database target,
volume/network removal, unrelated service operation, activation profile, build,
image pull, retry or rollback. The existing 01B implementation is not modified.
As with existing local operators, Docker, the trusted account, package-manager
executable domain and repository filesystem remain trusted; external actors are
not atomically locked together with Docker by a SQLite claim.

Post-observation is read-only and bounded to 25 attempts separated by 15 seconds,
using two matching snapshots per successful validation. Acceptance requires a
changed WordPress ID with a stable running/healthy generation and the same pinned
image; unchanged healthy database identity/generation without published ports;
unchanged identities of both volumes and networks; exact service network membership;
only `127.0.0.1:58082->80/tcp`; and exactly four unique WordPress mount destinations:
HTML named volume rw, Apache safety bind ro, PHP safety bind ro, storefront bind ro.
Repository and source metadata must remain unchanged too. Failed, unknown or timed
out execution cannot become accepted even if later observations satisfy checks.

Recreation starts the image entrypoint and healthcheck, which can write filesystem
or application state. Authority covers only this lifecycle replacement and does
not authorize customer, order or catalog business mutations. This boundary does
not prove backup/restore, content preservation, loaded Apache/PHP state, public
edge isolation, deployment logging safety, complete component inventory,
authenticated Shopping reads or soft-launch readiness. Production and Ubuntu
remain false; AIControlCenter on the Mac is the sole Control Plane.

Validation is fixture-only in `tests/test_shop_service_start_01g1c_wordpress_generation.py`,
plus focused regression tests for the reused 01B contracts. No canonical suite,
commit, push, live authorization or live mutation is part of this task.
