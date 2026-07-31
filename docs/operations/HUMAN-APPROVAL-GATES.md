# Human Approval Gates

Approval requirements are explicit: none, independent human, operational write,
production, and post-claim recovery. States are `NOT_REQUIRED`, `REQUIRED`,
`AWAITING_APPROVAL`, `APPROVED`, `REJECTED`, `EXPIRED`, and `CONSUMED`.

L4 requires independent human approval, bounded authorization, and single-use
permit and atomic claim controls where applicable. L5 requires a separate
architecture gate, independent production approval and explicit production
authorization. Post-claim recovery always requires human approval and never
automatically retries.

Approval is not activation and readiness is not authorization. AUTO-01 creates
no real approval. AIControlCenter remains approval authority; Codex, Ubuntu,
APIs, n8n, WordPress and WooCommerce cannot approve or govern delivery.
Production remains `NOT_AUTHORIZED`.
