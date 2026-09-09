# SHOP-SERVICE-START-01G1F — lifecycle reconciliation

Mutation: `SHOP-SERVICE-START-01G1F:COLIMA_RUNTIME_LIFECYCLE_RECONCILIATION`.
This implementation does not issue authority or run an operator. Repository tests
are synthetic. Production, external Ubuntu worker, business mutation, WordPress
recovery, capability and verifier activation authority remain false. The guest
access described here is to the Mac-owned Colima VM, never the Ubuntu worker.
01G1E remains consumed and must never be reissued or rerun.

## Decision and exact sequence

One invocation, with a trusted Homebrew-resolved executable:

```text
[<resolved /opt/homebrew/bin/colima>, "restart", "--profile", "aicontrolcenter-commerce"]
```

No force flag. The supported restart command gracefully stops, loads the saved
configuration and starts the same profile. It avoids a separately orchestrated
stop/start pair and profile edits. Only this lifecycle transition is authorized;
Docker's runtime interruption and existing database restart are inherent effects.
No application, container, volume or network mutation command is invoked.
Mutation stdin/stdout/stderr are discarded; timeout is 180 seconds. A timeout may
leave Colima descendants running: it is UNCERTAIN, never cancellation proof or
permission to retry. No retry, rollback, cleanup mutation or recovery follows.

Primary implementation references checked 2026-09-09:

- [Colima restart implementation](https://github.com/abiosoft/colima/blob/main/cmd/restart.go)
- [Colima profile selection](https://github.com/abiosoft/colima/blob/main/cmd/root/root.go)
- [Colima supported guest command transport](https://github.com/abiosoft/colima/blob/main/cmd/ssh.go)
- [Colima list JSON](https://github.com/abiosoft/colima/blob/main/cmd/list.go)
- [Colima autoActivate default](https://github.com/abiosoft/colima/blob/main/config/config.go)
- [Lima source/target mount tags](https://github.com/lima-vm/lima/blob/master/pkg/limayaml/defaults.go)

The local installed CLI was not queried in this repository-only task. Unsupported
runtime observations fail closed. Future version changes require review at the
fresh Git-bound authorization boundary; these references are not installed-version
attestations.

## Read / authorize / apply separation

The pure contract is `core.shopping.colima_lifecycle_reconciliation`; authorization
uses separate exact types, SQLite application ID `0x43473146`, schema and table.
The store is fixed to the trusted Darwin account's
`Library/Application Support/AIControlCenter/authorization/colima-lifecycle-01g1f-authorization.sqlite3`.
No 01G1E authorization or operator is called. Reuse from 01G1E is limited to
read-only snapshot/file validation and immutable declaration facts.

The separate zero-argument issuer requires a TTY, an exact reviewed Git HEAD and:

```text
AUTHORIZE SHOP-SERVICE-START-01G1F:COLIMA_RUNTIME_LIFECYCLE_RECONCILIATION
```

It displays the nonsecret contract and fresh preconditions before ACK, then
observes again. Maximum lifetime is ten minutes; maximum uses is one. It binds
canonical immutable JSON containing the clean exact Git HEAD, trusted UID/GID,
profile name/path, profile SHA256
`35dc5344e8072f7d787b801b18dec65bf499b93859ec71e7595526a3f7074dce`,
desired file SHA256
`3074cf3a5fd4a2a24fcfd396b86ceab4380d85e388dc054e8639539e1281d4fe`,
exact 01G1E declaration content, both exact read-only mounts, virtiofs, running
Docker profile, exact failed WordPress state, exact pre-lifecycle database
StartedAt/restart/health, database storage/attachment, and narrow authority flags.
Git HEAD is the freshly reviewed implementation commit, not the pre-implementation
baseline `e9a37efb6d8bbc65060e44eb5319fc4c9af1fdb5`.

Before issuance/consumption, startup scripts, Lima defaults/overrides, Kubernetes,
legacy layer routing, and automatic context activation must be absent/disabled.
`autoActivate: false` must be explicit; absence defaults to true and blocks.
The exact pinned profile is never edited to satisfy these guards. WordPress's
restart policy must be `no`. Docker context inspection must resolve to the exact
local Colima socket before any container/volume observations. No ambient
Colima/Lima/XDG selectors are passed to lifecycle commands.

The operator observes inside the claim transaction and compares with the issued
binding. The store commits an irreversible claim with SQLite FULL synchronization,
then commits and verifies the consumption receipt before the single lifecycle
attempt. Ambiguous claim/commit state prevents mutation. Once claimed, the record
cannot be used again, including after a crash. A second issuance into the same
store is refused even when the old record expires or is consumed.

## Active projection proof

The fixed supported guest observation is:

```text
[<trusted colima>, "ssh", "--profile", "aicontrolcenter-commerce", "--",
 "/bin/cat", "/proc/self/mountinfo"]
```

It reads kernel mount metadata only, with stderr suppressed. No guest file is
written and no secret file or content is read. Both exact host paths must be
virtiofs mount targets with root `/`, source-bound tags and effective VFS `ro`
flags without `rw`. Lima's accepted source tag is `lima-` plus the first 16 hex
characters of SHA256(`source + ':' + target`). This couples each active mount to
its exact source/target pair. Legacy positional `mount0`/`mount1` or unknown tags
are rejected; YAML and matching file contents cannot replace source proof.

The observer rejects extra virtiofs projections, duplicate target mounts,
shopping ancestor/child overmounts and subdirectory roots. Two identical guest
reads are required after mutation. Before issuance, the existing storefront
projection must already support this proof format; config may still be missing.
This prevents spending authority on known unsupported positional tag evidence.
Read-only is a kernel mount-namespace observation, not an assurance against a
future privileged remount. The trusted Colima guest/kernel and trusted Homebrew
package domain are the same administrative trust boundary as local runtime
observers; hostile privileged guest/host replacement is outside this model.

## Truthful database continuity

Pre-lifecycle checks require the exact authoritative container ID, StartedAt,
restart count zero, running and healthy. They additionally pin existing local
volume `ai-shopping-database`, its creation timestamp, local driver/scope, and
its exact writable `/var/lib/mysql` attachment/source.

Post-lifecycle checks require the same database container ID, volume metadata and
attachment, with running/healthy observed. StartedAt may advance and RestartCount
may reset or increase. Neither is falsely required to survive a VM restart
unchanged. Storage metadata continuity is not a content digest, backup, logical
integrity check or proof of data preservation. No SQL, backups, volume recreation
or database recreation are performed. MariaDB's own normal shutdown/recovery may
write its files as an inherent lifecycle effect; no business writes are authorized.

## Results and operational caveats

`RECONCILED` requires exit zero, profile running, active projection proven,
database metadata continuity observed, and all remaining preconditions preserved.
Any failed/ambiguous lifecycle result stays `UNCERTAIN` even if subsequent reads
look healthy. Post-observation still runs after nonzero exit or timeout; independent
running/projection/database evidence is reported separately. Unavailable evidence
is false/unknown, never assumed. Health still starting is UNCERTAIN; no polling
retry is hidden in this operator. Changed WordPress state also prevents success.
After consumption, only separately initiated read-only forensics are appropriate.

The result always denies WordPress recovery, business/production/Ubuntu authority,
automatic retry/rollback, backup and database content-preservation claims.
There is no capability/verifier activation path. Runtime compatibility and all
live preconditions remain unverified by this repository-only work. If the pinned
profile enables autoActivate or the installed Lima uses positional tags, issuance
is blocked; resolving that needs a separately reviewed work item, not broader
01G1F authority. Concurrent privileged changes cannot be made atomic with an
external CLI invocation; fresh repeated observations reduce that window and any
observed drift blocks or becomes UNCERTAIN.

## Validation scope

Focused synthetic tests cover authorization, exact ACK/TTL, drift, consumption
ordering/faults, one use, historical authority isolation, fixed argv, suppressed
output, no retry/rollback/application commands, post-failure forensics, truthful
database continuity, projection success/failure/unknown, endpoint selection and
startup guards. Related regression coverage includes 01G1C, 01G1D, 01G1E and
storage/runtime observers. A new canonical run is required before claiming a new
canonical PASS because repository code changed; it is not run automatically here.
Project-wide closure documentation remains deferred as explicitly requested.
