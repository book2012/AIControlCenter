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
