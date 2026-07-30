# M3-A4B2B2 — Permit Claim and Fail-Closed Policy

A claim is canonical JSON adjacent to its permit. The claim parent is mode
`0700`; the claim is exclusively created with mode `0600`, flushed with
`fsync`, and the parent directory is flushed where supported. It binds permit
ID/digest, exact branch/commit, operator, explicit claim time and execution
request ID.

There is no claim delete, reset or permit-reuse operation. A second or
conflicting claim fails. Expiry and all other permit checks occur before claim.

Pre-claim failure writes nothing to operational targets. After claim, the
permit stays consumed after every outcome. Failures roll back and close
database work, remove only artifacts created by that execution, remove newly
created empty directories in reverse order, preserve the claim/failure
evidence, and never report success or activate writers, monitoring, dispatch
or production.

M3-A4B2B2A validated atomic claim and cleanup only in injected pytest roots.
It made zero live claims.
