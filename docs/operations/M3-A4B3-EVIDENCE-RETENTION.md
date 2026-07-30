# M3-A4B3 Evidence Retention

Retain the canonical approval, preflight, live request, activation
authorization, authorization evidence, typed permit, issuance evidence, atomic
claim, bootstrap receipt, bootstrap evidence, post-bootstrap validation, and
baseline backup manifests as one immutable chain. Retain database and backup
snapshots read-only and record hashes, sizes, modes, ownership, and mtimes
before and after inspection.

Never retain restored drills beside operational databases. Create restored
databases, mutations, and tamper fixtures only beneath the approved recovery
work root. A restore result is evidence, not operational state. Never remove or
rewrite the consumed claim, and never represent the permit as reusable.

Documentation uses a generic operational-root notation. The completed chain is
bound to commit `f7a81b73b86c170300bb6b80f437dbb753362f7e`; writers,
monitoring, dispatch, Ubuntu, and production authorization remain false.
