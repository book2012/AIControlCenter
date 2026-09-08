# SHOP-SERVICE-START-01G1E — Colima Bind-Source Projection Recovery

Repository implementation only. No live authorization, profile access, lifecycle
operation, container mutation, production access or Ubuntu access was performed.
Implementation baseline: `9ad63b4b9ca29f9ec533979ca5a47d28f3d33eef` on
`feature/homepage-product-management-console`. This work remains uncommitted.

The Git-owned desired contract is `deploy/shopping/colima-mounts.json`. It requires
profile `aicontrolcenter-commerce`, file
`/Users/kyouhan/.colima/aicontrolcenter-commerce/colima.yaml`, `mountType: virtiofs`,
and only these mount locations, each with literal `writable: false`:

- `/Users/kyouhan/AIControlCenter/deploy/shopping/wordpress/plugins/ai-shopping-storefront`
- `/Users/kyouhan/AIControlCenter/deploy/shopping/config`

The observer requires the existing storefront-only declaration. Already patched,
duplicate, unknown, broad, aliased, writable or ambiguous declarations fail closed.
The patch inserts only the missing config entry and preserves existing YAML bytes;
unsupported YAML layouts fail rather than being reformatted. The parser also rejects
duplicate keys, aliases, anchors, explicit tags and merge keys in unrelated fields.

## Separate one-shot authority

Mutation ID: `SHOP-SERVICE-START-01G1E:COLIMA_BIND_SOURCE_PROJECTION_RECOVERY`.

Future entry points, neither invoked during implementation:

- `ops.macos.shopping.issue_colima_projection_authorization`
- `ops.macos.shopping.colima_projection_operator`

Both reject CLI overrides. The issuer requires a TTY, a separately reviewed expected
40-character Git HEAD, and this exact interactive acknowledgment:

```text
AUTHORIZE SHOP-SERVICE-START-01G1E:COLIMA_BIND_SOURCE_PROJECTION_RECOVERY
```

The expected HEAD must match fresh observations; it is not the pre-implementation
baseline hardcoded into the new feature. A future committed feature necessarily has
a different HEAD. Clean Git state includes untracked files. Two identical read-only
snapshots are required before the prompt, after the prompt, and during consumption.
The issuer binds the complete profile hash, desired contract hash, both safety-file
hashes, trusted Mac UID/staff GID, fixed profile identity and exact runtime identities.
Ownership comes from the existing Darwin passwd resolver, never `$HOME`. Profile and
artifact paths must be regular, single-link files without symlinks or group/world
write access; ancestor directories must have trusted ownership and permissions.

A distinct SQLite application ID, schema, record/receipt types and file at the trusted
passwd home's `Library/Application Support/AIControlCenter/authorization/colima-projection-01g1e-authorization.sqlite3`
is used. Maximum uses is exactly one; lifetime is at most ten minutes. The store will
not issue another record even after expiry or consumption. Historical 01G1C/01G1D
files and records are never opened, migrated, reused, retried or reissued here.

A SQLite immediate transaction validates fresh observations and expiry before claim.
Drift fails without consumption. A durable claim, final commit and read-back receipt
precede the sole profile replacement attempt. A crash after claim burns authority.
Errors and uncertain completion never trigger retry or rollback. Staging-file cleanup
is not restoration of the profile. The trusted user, filesystem and repository remain
trusted; unrelated external processes are not locked by the authorization transaction.

## Mutation and lifecycle boundary

There is **no mutation argv** and no lifecycle execution in this implementation.
The sole mutation is a Python same-directory staged write, file fsync, atomic
`os.replace` of the exact profile, then directory fsync. Owner and permission bits
are retained. The original bytes and metadata are rechecked before replacement.
No shell, Colima executable, SSH, Compose, container start or recreation is used.
All subprocess calls are read-only Git or field-selected Docker inspection, with
stderr discarded. No raw profile contents, process stderr, exception text, Docker
environment, health logs or secrets are included in JSON output or durable authority.
There is no lifecycle stdout/stderr because no lifecycle process exists.

Successful declaration verification returns `DECLARED_PENDING_LIFECYCLE`, never
`ACCEPTED` or active-projection success. Updating YAML does not establish that the
running VM is using it. Any future lifecycle operation requires a separate explicit,
bounded authority and reviewed command contract; this work item supplies none.
In particular, a VM restart may violate the required database start/restart continuity,
so it must not be inferred as a permissible next step from the desired package.

## Read-only validation and remaining live steps

WordPress must retain failed container
`0636d4cad86d31f0119ccadb1c83ef59ea4b2192bdd74b3f459c2947d24f2a0e`,
created/nonrunning, PID 0, exit 127, zero StartedAt and zero restart count.
Database must retain
`434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323`,
StartedAt `2026-09-03T03:10:22.559242003Z`, restart count 0, running and healthy.
Post-declaration checks require both identities and all other bound facts unchanged.

The pure `validate_post(before, after, guest)` additionally requires read-only guest
evidence that config resolves to virtiofs ro, both named safety artifacts resolve as
regular files, and storefront remains virtiofs ro. Production and Ubuntu must be
false. It does not accept missing facts or changed database continuity. This is a
validator, **not a guest evidence collector or provenance attestation**. No guest
transport is implemented because this task excludes SSH. Caller-supplied fixture
JSON must never be presented as live proof.

Remaining work: review and commit through a separately authorized Git task; perform
fresh read-only observations; explicitly authorize and issue 01G1E only for the file
reconciliation; execute once; separately design/authorize any necessary lifecycle
and trusted read-only guest evidence collection; then validate actual projection
and exact database continuity. If continuity cannot be preserved, this contract
cannot be declared successful. No automatic lifecycle or rollback is a fallback.

WordPress generation recovery needs a later separate authority. Capability/verifier
creation, authenticated Shopping reads, business changes, production, Ubuntu and
soft-launch activation remain outside this feature. Mac AIControlCenter remains the
sole governance and orchestration Control Plane.

Fixture tests: `tests/test_shop_service_start_01g1e_colima_projection.py`. Tests use
mocked subprocess/ownership boundaries and temporary SQLite/profile files. They do
not invoke live entry points or access `~/.colima`. Only focused tests and
`git diff --check` are required here; no full canonical gate, commit or push.
