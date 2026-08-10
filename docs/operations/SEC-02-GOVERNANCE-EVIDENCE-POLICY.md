# SEC-02 Governance Evidence Policy

Status: `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`

## Canonical storage

Durable Governance evidence must use an operator-configured external Control
Plane data root. The target must be outside immutable application source and
must not use the repository working tree as runtime state. Application policy
accepts caller-supplied storage identity and classification facts only; it does
not discover, parse, create, or write a path.

`/private/tmp` is suitable only for transient controller reports. Historical
SEC-01 and SEC-02 reports stored there must not be treated as canonical durable
evidence. Repository evidence JSON is canonical documentation/audit evidence,
not mutable runtime application state.

An acceptable target is non-ephemeral and supports atomic write publication,
restrictive permissions, durable synchronization, evidence-manifest binding,
caller-supplied digest/reference identities, and value-free evidence. Any
missing property is a deterministic rejection. No concrete persistence adapter
or writer exists in A9.

## Content restrictions

Evidence and API projections must contain typed safe references only. Secret
values or hashes, prefixes/suffixes, access tokens, API keys, passwords,
authorization header values, cookies, raw environments, private key material,
provider credential or arbitrary response bodies, and raw commands are
forbidden. Generic payload, environment, headers, cookies, credentials, or
secrets escape fields are forbidden.

The read-only API projection cannot authorize, approve, consume authority,
widen budget, execute, retry, roll back, alter evidence, or persist evidence.
No Production mutation API or HTTP route is added. Shopping retains Shopping
business logic. Ubuntu stores no Governance state and owns no Governance
authority.

External validation of the focused Governance regression reported `265 passed
in 1.45s`, validating
`SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`, including unchanged
`GovernanceApiEnvelope` compatibility. This was not the full repository
regression. No concrete evidence persistence adapter and no Production,
provider, or Ubuntu mutation were added or performed. Next: `SEC-02A10
ARCHITECTURE CLOSURE REVIEW`. The milestone
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` is not yet claimed.
Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.
