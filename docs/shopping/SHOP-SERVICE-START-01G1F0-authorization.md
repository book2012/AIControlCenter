# SHOP-SERVICE-START-01G1F0 operational contract

Implementation only. No authorization has been issued and no runtime observation or
mutation has been performed by this work item implementation.

The issuer and operator are separate zero-argument commands:

- `python -m ops.macos.shopping.issue_wordpress_restart_policy_authorization`
- `python -m ops.macos.shopping.wordpress_restart_policy_operator`

Three identities have distinct roles:

- Supplied implementation baseline: `470de1254010e94ba805903ff68fe112ae9a37e9`
  for this closeout (the original implementation baseline was
  `f4d50eae4e452434922013463a3a486a2bbd8c52`). Neither grants authority.
- Canonical-reviewed artifact identity: a SHA-256 content digest obtained from an
  independent canonical review record. This implementation does not claim that
  canonical review has occurred. Canonical validation remains a separate gate.
- Issuance-observed clean Git HEAD: the exact current 40-character commit SHA,
  independently observed and matched to the human's expected HEAD at issuance.

The artifact uses schema `SHOP-SERVICE-START-01G1F0:reviewed-artifact:v1`.
Inventory is `git ls-files -z -- core ops integrations config configs requirements.txt
 deploy/shopping/compose.yaml`. Every tracked file in these authority roots is
included, including package initializers, transitive local trust/observation/store
helpers, historical dependencies, immutable constants, configuration, and dependency
versions. The scope and digest verifier are themselves included. Each sorted entry
is `[repository-relative path, integer permission mode, SHA-256 of exact file bytes]`; the final SHA-256 hashes
ASCII JSON `[schema, entries]` with `ensure_ascii=True` and separators `(',', ':')`.
File reads use no-follow descriptors and reject metadata drift across the read.
They retain the existing ownership, mode, regular-file, hardlink, symlink,
ancestor and size checks. Missing, unsafe or oversized files fail closed.

Commit metadata, documentation and tests are outside the artifact scope. A new
commit packaging the same reviewed authority bytes therefore has the same artifact
identity. Any edit, addition, deletion or rename inside the scope changes or
invalidates that identity; extending authority through a new import also changes
its covered importing implementation. The implementation assumes the existing
trusted Python/dependency runtime; this is not runtime supply-chain attestation.

The issuer requires both the expected clean HEAD and the canonical-reviewed digest
from the independent review record, observes twice, displays only allowlisted
metadata and mutation argv, and requires exactly:

`AUTHORIZE SHOP-SERVICE-START-01G1F0:WORDPRESS_RESTART_POLICY_RECONCILIATION`

A clean later HEAD alone is insufficient. The expected artifact must match the
observed bytes before acknowledgement, and the complete observations must still
match afterward. The reviewer must not substitute a freshly computed, unreviewed
digest for the review record. The human review boundary attests provenance; a hash
alone does not prove review. No digest or packaging HEAD is embedded in its own
hashed implementation, and there is no automatic review-record refresh.

Both `head` and `reviewed_artifact` are durably bound in `precondition_json` and
propagate unchanged into the consumption receipt. Consumption and the final
pre-mutation check re-observe both; postconditions retain both. Old F0 bindings
without the artifact field fail closed. Historical 01G1C/01G1D authorization types,
stores and 01G1F semantics remain isolated and unchanged. The reviewed compose
SHA-256 remains `0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c`.

This closeout runs synthetic focused tests only, with Git/Docker observations
stubbed. No authorization, operator execution or canonical validation is performed.

Authority lasts at most ten minutes and permits one use. The dedicated store under
the trusted Mac account's `Library/Application Support/AIControlCenter/authorization/`
is `wordpress-restart-policy-01g1f0-authorization.sqlite3`. Its parent must be owned by
that account with exact mode 0700; an existing unsafe parent is rejected, never repaired.
The store is mode 0600 and refuses issuance if any prior row exists, including expired,
claimed or consumed rows. Retain the store permanently; deleting/replacing it is outside
this contract and must never be used to obtain another attempt.

The operator durably claims and commits authority, verifies a structured receipt,
then rechecks the bound observations and expiry before exactly one possible command:

```
docker --context colima-aicontrolcenter-commerce update --restart=no 0636d4cad86d31f0119ccadb1c83ef59ea4b2192bdd74b3f459c2947d24f2a0e
```

The executable is resolved and validated in the existing trusted Homebrew Docker domain.
Input, stdout and stderr are discarded; timeout is 30 seconds. No retry or rollback exists.
A nonzero exit, timeout, ambiguous consumption or postcondition failure is UNCERTAIN.
An already-no container fails closed without an update. Read-only post-observation follows
an attempted update even when its outcome is unsuccessful or ambiguous.

Bindings include clean HEAD, unchanged compose digest and desired `no`, exact context
endpoint and socket inode/device/ownership/mode, full WordPress ID, created/non-running
state, restart count zero and initial `unless-stopped` with maximum retry count zero.
Postconditions require the same metadata with only the restart policy changed to `no`.
DB container metadata, volume identity and attachment must remain exactly equal.
These observations prove metadata continuity only: no backup or content preservation claim.
Docker offers no atomic compare-and-update operation; external concurrent administrators
must not mutate these objects during execution. Detected drift always fails closed.

Production, Ubuntu, business, Colima lifecycle, WordPress generation recovery, capability
and verifier authority are all false. No compose invocation, Colima command, application
container lifecycle/exec operation, DB/volume mutation, secret read or application data
access is allowed. RECONCILED does not authorize 01G1F: that remains a separate next gate
with its existing `wordpress_restart == "no"` requirement.
