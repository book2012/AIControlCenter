# Autonomous Sprint Manifest

The AUTO-01 manifest is immutable, typed and JSON-first. Its schema is
`config/autopilot/sprint-manifest.schema.json`.

Every manifest binds schema version, task identity, milestone, exact branch and
40-character commit, dependencies, autonomy ceiling, test-only and production
flags, Ubuntu policy, allowed and forbidden paths and dependency zones, Git,
test, documentation, approval, retry and evidence gates, commit and next-task
policy, and forbidden operations.

Canonical JSON uses sorted keys and compact UTF-8 encoding. The canonical
manifest digest is SHA-256 over the manifest payload excluding the digest field.
Validation recalculates it and fails closed on mismatch.

Unsafe inputs are rejected: floating baselines, missing gates, autonomy
self-escalation, lower-level production, L4 without human approval, L5 without
production approval, environment-only authorization, Ubuntu ownership,
non-AIControlCenter governance, automatic post-claim retry, wildcard scopes
without explicit policy, empty forbidden operations, and secret or `.env`
dependencies.

Roadmap compilation validates unique IDs and dependencies, rejects cycles, uses
lexicographically stable topological ordering, and produces canonical JSON with
a digest. Incomplete dependencies block scheduling. Dependency completion never
confers approval, operational authorization or activation.
