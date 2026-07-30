# M3-A4B2B2B Live Fail-Closed Recovery

Post-claim failure evidence is canonical mode-0600 JSON binding the request,
permit, consumed claim, after-claim failure, cleanup, shared-parent/sibling
preservation, inactive writers/monitoring/dispatch, and production
`NOT_AUTHORIZED`. Its digest and rejected second execution are independently
validated.

Pre-claim failure leaves managed targets absent and does not create a claim.
Post-claim failure leaves the claim permanently consumed. Close handles, roll
back active transactions, and remove only incomplete managed artifacts created
by that execution. Preserve the existing parent, unrelated siblings, claim,
and failure evidence. Never automatically retry or report success.

A later attempt needs a new permit and fresh independent approval whenever a
binding changed. Production activation remains `NOT_AUTHORIZED`.
