# SHOP-SERVICE-START-01G1F0 operational contract

Implementation only. No authorization has been issued and no runtime observation or
mutation has been performed by this work item implementation.

The issuer and operator are separate zero-argument commands:

- `python -m ops.macos.shopping.issue_wordpress_restart_policy_authorization`
- `python -m ops.macos.shopping.wordpress_restart_policy_operator`

Execution requires a separately reviewed, clean Git HEAD containing this implementation.
The issuer asks the human for that exact 40-character HEAD, observes twice, displays
only allowlisted metadata and the mutation argv, and requires exactly:

`AUTHORIZE SHOP-SERVICE-START-01G1F0:WORDPRESS_RESTART_POLICY_RECONCILIATION`

The supplied implementation baseline was `f4d50eae4e452434922013463a3a486a2bbd8c52`.
It is not an authorization for a later implementation HEAD. The reviewed compose
SHA-256 remains `0120c2e8bbdb00d6e9ae690fa504a5bd5aee124a70ed37b47e75658e7c278f2c`.
Historical 01G1C/01G1D identities and 01G1F semantics are unchanged.

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
