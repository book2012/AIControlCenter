# M3-A4C Activation Validation and Closeout

M3-A4C closes M3 with
`READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`. This is readiness
only: no activation or production authorization is performed.

## Validated state

- M3-A4B2B2B actual Mac bootstrap: `COMPLETE`, commit
  `f7a81b73b86c170300bb6b80f437dbb753362f7e`.
- M3-A4B3 evidence and recovery: `COMPLETE`, commit
  `0f23abdf362965c09db5f4f35483cbff47853643`.
- The evidence chain, consumed single-use permit, one atomic claim, receipt,
  post-validation, and failure-evidence absence are valid.
- Audit and replay are `HEALTHY` with zero events; both isolated restores
  passed, while tampered, cross-service, and unsafe cases failed closed.
- Operational and evidence state remained unchanged.
- Writers, monitoring, dispatch, Ubuntu participation, and production
  authorization remain false.

## Architecture and future contract

The immutable AIControlCenter-owned boundary has no issuer, claim store,
runner, writer, restore, API, command, network, SSH, Docker, Ubuntu, n8n,
WordPress, WooCommerce, notification, or production port. The Mac remains the
always-on brain and sole Control Plane; Ubuntu remains an optional stateless
infrastructure worker.

A future sprint must separately require exact Git binding, explicit
default-false capabilities, independent approval and identity rules, bounded
TTL, a single-use permit, atomic claim, bootstrap and M3-A4B3 evidence binding,
healthy audit and replay, per-capability authorization, and fail-closed
evidence. Ubuntu participation and production authorization remain false.
M3-A4C creates no request, authorization, permit, or claim. The existing 427
deprecation warnings remain a separate backlog track.
