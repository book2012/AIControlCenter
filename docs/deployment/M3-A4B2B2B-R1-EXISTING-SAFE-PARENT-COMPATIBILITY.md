# M3-A4B2B2B-R1 Existing Safe Parent Compatibility

The initial bootstrap attempt was blocked before permit issuance because the
Mac application-state parent already existed. Read-only recovery inspection
reported `ROOT_EXISTS_SAFE_PARENT_CANDIDATE`: it is the exact trusted-home
directory, is owned by the current non-root operator, is not a symlink, has
mode `0755`, is not group/world writable, is local and outside the repository.

The application-state parent is shared state, not an exclusively owned
deployment-control directory. Existing siblings remain opaque and outside
bootstrap ownership. Their identities may be represented only by digests; they
are not recursively inspected, migrated, chmodded, chowned, removed or
modified.

Compatibility is fail closed. An existing parent is accepted only with the
strict path, owner, symlink, permission, filesystem, repository, caller-root,
managed-target-absence and non-production gates. Mode `0755` records the
nonblocking restriction `EXISTING_SHARED_PARENT_MODE_NOT_0700`; it is not
misreported as satisfying managed-directory policy.

Only absent `audit`, `security` and `monitoring` subtrees may be created, each
with mode `0700`. Managed databases, backups and manifests remain `0600`.
Unknown, partial or symlinked managed state is rejected rather than reused or
repaired. Cleanup removes only artifacts created by the failed execution and
never changes a pre-existing parent or sibling.

The actual operational bootstrap remains **NOT EXECUTED**. No permit was
issued or claimed. A fresh approval and permit bound to the new commit are
required. Production activation remains `NOT_AUTHORIZED`.
