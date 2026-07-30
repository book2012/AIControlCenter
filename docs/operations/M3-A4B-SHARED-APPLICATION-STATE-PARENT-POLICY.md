# M3-A4B Shared Application-State Parent Policy

`~/Library/Application Support/AIControlCenter` is the shared application-state
parent. Deployment control owns only `audit/`, `security/` and `monitoring/`.

An absent parent created by controlled bootstrap must be `0700`. A pre-existing
parent must be the exact absolute trusted-home path, a real non-symlink
directory with no symlinked parent component, owned by the current non-root Mac
operator, not group/world writable, local, non-removable, non-network-backed,
outside Git, and used without a caller-selected root or production authority.
It is never chmodded, chowned or metadata-rewritten. Existing mode `0755` is
allowed with `EXISTING_SHARED_PARENT_MODE_NOT_0700`.

All three managed roots and every database, backup and manifest target must be
absent before and after permit claim. Any partial state, symlink or unknown
managed artifact blocks execution. Existing unrelated siblings are counted and
identity-digested without exposing contents or recursively traversing them.

New managed directories are `0700`; new managed files are `0600`. Failure
cleanup is creation-ledger based and cannot remove the shared parent unless
that parent was created by the same failed execution and is empty.
