# SEC-02A9 Durable Evidence and API Projection

Status: `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`

Validated milestone: `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`

Next: `SEC-02A10 ARCHITECTURE CLOSURE REVIEW`

## Boundary

A9 adds two pure application policies: an immutable durable-evidence storage
evaluation and an immutable typed Governance read projection. It adds no
filesystem writer, persistence adapter, SQLite store, network route, HTTP
framework, Production or Runtime access, provider access, Ubuntu access,
authorization mutation, execution, retry, rollback, or compensation.

The storage descriptor contains only facts already observed or configured by
an operator. Application code does not parse paths or inspect storage. The
actual external Control Plane data root is operator-configured; no
user-specific absolute data-root path is hard-coded.

## Durable evidence policy

Canonical runtime Governance evidence belongs in external Control Plane
durable data storage outside immutable application source and outside the
repository working tree. Acceptance requires non-ephemeral storage, atomic
write publication, restrictive permissions, durable synchronization, manifest
binding, caller-supplied identities/digests, and value-free evidence.

`/private/tmp` is transient controller-report storage only and is rejected as
canonical durable evidence. Historical SEC-01/SEC-02 reports there are not
durable evidence. Git-tracked evidence JSON remains canonical documentation
and audit evidence, but is not mutable runtime application state. A future
concrete `EvidencePersistencePort` adapter must receive its external data root
from operator configuration; A9 adds no writer or adapter.

## Read-only projection

`GovernanceReadModel` is a frozen, typed, value-free observation carrying the
lifecycle, authorization and precondition states, mutation accounting,
execution/postcondition state, failure/manual-action flags, safe evidence and
Git/documentation references, and caller-supplied projection time. Invalid or
negative count combinations and empty lifecycle identity fail closed.

`project_governance_api_envelope` deterministically produces the unchanged A6
`GovernanceApiEnvelope` shape. It reads no clock, invokes no adapter, persists
nothing, grants or consumes no authorization, creates no budget, and cannot
execute, retry, roll back, or expose mutation. It is projection data, not an
API route, and no HTTP mutation route was added. Dashboards may observe
Governance only; Shopping business logic remains Shopping-owned, and Ubuntu
remains a stateless infrastructure Worker with no Governance state or
authority.

## Value-free safety

The typed policies contain no generic payload, environment, headers, cookies,
credentials, or secrets bags. They exclude secret values and derivatives,
tokens, API keys, passwords, authorization header values, cookies, environment
dumps, private keys, provider credential/response bodies, and raw commands.
Stable codes, IDs, counts, statuses, and caller-supplied non-secret digests are
permitted.

External validation reported `265 passed in 1.45s` for the focused Governance
regression, validating the durable-evidence policy, deterministic READ ONLY
projection, and `GovernanceApiEnvelope` compatibility. This was not the full
repository regression. No concrete evidence persistence adapter and no
Production, provider, or Ubuntu mutation were added or performed.
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` remains unclaimed until
A10. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.
