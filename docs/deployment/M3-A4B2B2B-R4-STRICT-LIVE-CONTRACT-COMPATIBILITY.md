# M3-A4B2B2B-R4 Strict Live Contract Compatibility

R4 closes two contract defects found by the authorized strict-live attempt,
which ended `BLOCKED_PRE_AUTHORIZATION`. Strict artifact normalization passed,
but the live reader rejected the required `ubuntu_participation` field before
contract validation, and live permit issuance returned a mapping where the
orchestrator required a typed value.

The strict shared-parent preflight reader now owns one narrow exception:
`ubuntu_participation` is required, must be a Boolean, and must be exactly
`false`. It is governance deny-evidence proving Ubuntu did not participate; it
does not authorize Ubuntu activation. Missing, true, null, string, integer,
list, object, nested, alternate, host, command, worker, destination,
environment, and unknown fields remain rejected. The global unsafe-field
policy was not weakened and no Ubuntu client or runtime dependency was added.

`ControlledLivePermitService` and
`ControlledOperationalBootstrapOrchestrator` now share the immutable
`ControlledLivePermitResult`. Its canonical serialization and digest bind the
one-use controlled-non-production permit, Git revision, identities, validity
window, execution deadline, inactive capabilities, and
`production_authorized=false`. The orchestration boundary rejects mappings,
invalid scope, mismatches, expiry, and tampering before serialization.

Pytest-only coverage beneath injected temporary roots proves the strict field
round-trip and the typed permit path through orchestration. Existing tests
continue through atomic claim and the test-confined Mac coordinator with
writers, monitoring, and dispatch inactive. No real activation authorization,
permit, claim, bootstrap, managed target, database, backup, Ubuntu change, or
production activation occurred.

Actual managed targets remain absent, actual operational bootstrap remains
`NOT EXECUTED`, and production remains `NOT_AUTHORIZED`. Fresh independent
approval must bind the R4 commit before a separately authorized Mac bootstrap.
M3-A4B3 must not begin before that actual bootstrap succeeds.
