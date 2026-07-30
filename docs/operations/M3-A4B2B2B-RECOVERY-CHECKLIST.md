# M3-A4B2B2B Recovery Checklist

Independently validate the canonical failure digest, request/permit/claim
binding, cleanup and preservation records, inactive capabilities, and rejected
second execution.

After an R3 post-claim failure, preserve the consumed claim and evidence.
Remove only incomplete artifacts from that execution; preserve the shared
parent and unrelated siblings.

- Confirm the earlier attempt stopped before permit issuance.
- Record the read-only result `ROOT_EXISTS_SAFE_PARENT_CANDIDATE`.
- Resolve home through the trusted local account database; reject alternatives.
- Verify exact path, directory type, owner, symlink-free components, local
  fixed storage, safe mode and repository separation.
- Record `0755` as `EXISTING_SHARED_PARENT_MODE_NOT_0700` when applicable.
- Verify `audit`, `security`, `monitoring`, databases, backups and manifests are
  all absent; reject partial or unknown state.
- Capture only non-recursive sibling identity digests.
- Confirm the shared parent and every sibling remain unchanged.
- Confirm actual managed directories, databases and backups remain absent.
- Confirm zero operational permits, claims and controlled executions.
- Require fresh independent approval and a permit bound to the new commit.
- Keep production activation `NOT_AUTHORIZED`.

For the R4 recovery, preserve the prior strict-live directory as forensic
evidence and do not reuse or mutate it. Record the attempt as
`BLOCKED_PRE_AUTHORIZATION`, normalization as passed, and activation,
permit, claim, bootstrap, target, writer, monitoring, dispatch, Ubuntu, and
production counters as zero. Require fresh approval for the R4 commit.
# R5 incident recovery

- Preserve `/private/tmp/aicontrolcenter-live-bootstrap.OR75nI` read-only.
- Confirm its permit remains unclaimed and is not reused.
- Confirm managed targets remain absent and bootstrap remains `NOT EXECUTED`.
- Require fresh independent approval before a separately authorized attempt.
- Keep production `NOT_AUTHORIZED` and M3-A4B3 blocked.

# M3-A4B3 isolated recovery checklist

- Use only the injected immutable operational and evidence snapshots.
- Put every restore, mutation, and tamper fixture under injected recovery work.
- Validate canonical manifest and exact database byte digest before restore.
- Reject missing, empty, truncated, modified, cross-service, wrong-schema,
  symlinked, broad-mode, traversal, outside-root, and pre-existing targets.
- Restore audit and replay to distinct fresh `0700` directories and `0600`
  files; require public inspector `HEALTHY`, current schema, and zero events.
- Compare source hash, size, and mtime before/after.
- Never restore into operational state. Production remains `NOT_AUTHORIZED`.

# M3-A4C retention

The isolated drills are bound to M3-A4B3 commit
`0f23abdf362965c09db5f4f35483cbff47853643`. M3-A4C performs no restore
and treats failed recovery validation as a hard blocker.
