# M3-A4B2B2 — Runtime Request Contract

The request is strict canonical JSON with exactly:

- `request_id`
- `mode`
- `branch`
- `commit`
- `operator_identity`
- `requested_at`
- `claim_at`
- `permit_path`
- `issuance_evidence_path`
- `evidence_directory`
- `metadata`

Paths must be absolute and traversal-free. Timestamps are explicit,
timezone-aware inputs. The branch and 40-character commit bind every permit,
claim and receipt. Metadata is sorted and may not contain passwords, keys,
tokens, private keys, cookies, authorization headers, raw environment/nonce,
shell, command, argv, script or URL material.

The request cannot contain arbitrary commands. The Python implementation uses
no subprocess, network, API route or generic command runner. Canonical IDs and
digests are stable for identical semantic inputs and timestamps.
## R2 controlled request

A controlled request binds a valid activation authorization digest, explicit
timestamp, exact branch and commit, trusted operational path, live permit and
issuance evidence, controlled non-production scope and
`production_authorized=false`. Environment-only and CLI-only activation are
invalid.
