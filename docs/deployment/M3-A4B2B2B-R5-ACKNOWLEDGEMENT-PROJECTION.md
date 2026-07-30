# M3-A4B2B2B-R5 Acknowledgement Projection

## Status

R5 separates full restriction acknowledgement evidence from the exact
executor warning acknowledgement pair. Production remains `NOT_AUTHORIZED`.
The current-user Mac operational bootstrap remains `NOT EXECUTED`.

## Incident and preserved evidence

The latest operational attempt created one activation authorization and one
typed permit, then stopped before atomic claim with
`DUAL_WARNING_ACKNOWLEDGEMENTS_REQUIRED`. The permit was not reused. The
read-only forensic root `/private/tmp/aicontrolcenter-live-bootstrap.OR75nI`
is preserved with one authorization, one permit, zero claims, zero bootstrap
executions, and no operational target writes.

## Contract

`ControlledRestrictionAcknowledgement` retains every active restriction,
identity, canonical acknowledgement digest, restriction digest, branch,
commit, request binding, and non-synthetic/non-placeholder state.
`ControlledWarningAcknowledgementProjector` locates `warnings-427`
semantically and requires exactly the Mac operator and independent approver.
It sorts canonically, never selects by input position, never truncates, and
preserves the full evidence in an immutable projection.

`ControlledLivePermitResult` binds both the canonical full-evidence digest and
the exact warning-projection digest into its permit digest. Tampering with
either invalidates the permit. Maximum uses remains one and production,
writers, monitoring, and external dispatch remain unauthorized.

## Compatibility gates

The orchestrator constructs and validates the typed projection before calling
activation authorization or permit issuance. An invalid projection therefore
creates zero authorizations, permits, claims, or managed writes. Permit
issuance consumes that validated report. The same report and the issued typed
permit are revalidated immediately before execution/claim.

The executor validator still requires exactly two warning acknowledgements;
its global count rule was not relaxed.

## Operational disposition

Actual managed targets remain absent. R5 creates no real operational
authorization, permit, claim, directory, database, backup, restore, or
bootstrap execution. A fresh independent approval is required before any
future authorized Mac bootstrap. M3-A4B3 remains blocked until that actual
bootstrap succeeds.
