# DEV_INGRESS_001 — Phase B2c

Phase B2c records the approved Dev-site edge-guard correction. The repository
Caddyfile now classifies as production plus a guarded preview, while repository
evidence remains insufficient for live readiness or effective-runtime
attestation. The active loaded Caddy configuration has not been observed after
the edit.

## Policy and classification

`config/deployment/caddy-site-policy.json` defines `dev-ingress/v1` under the
existing `dpl/v1` schema registry as `CaddySitePolicy`. This new closed schema
does not extend or replace `IngressContract.upstream`.

| Role | Exact site | Sole allowed upstream | Presence |
| --- | --- | --- | --- |
| Production | `bokstory.duckdns.org` | `127.0.0.1:58082` | Exactly one |
| Preview | `dev.bokstory.duckdns.org` | `127.0.0.1:18080` | Zero or one |

The production identity must also match the supplied, validated
`IngressContract.upstream`. Policy versions, hosts, ports, roles, logging and
authority settings are closed; changing them requires contract review.
Credentials are not policy fields. Duplicate JSON keys and unknown fields fail
closed. The entrypoint remains `ops/macos/caddy/Caddyfile`, owned by host Caddy,
with HTTP/HTTPS ports 58080/58443 and no activation authority.

`core/deployment/adapters/macos/caddy_sites.py:classify_caddy_sites` is the single
classification entrypoint used by both `CaddyIngressAdapter` and
`CaddyFileAdapter`. Each adapter reads the versioned policy and canonical
`IngressContract` through the repository reader, then either classifies the
entire Caddyfile or raises a fixed, value-free rejection code. Its
immutable result contains production and optional preview identities, without
READY/PASS, loaded-config evidence, authentication material, or authority fields.
Production code performs no subprocess, network, environment expansion or
import resolution. Raw syntax trees are private and do not display their values
in representations.

## Deliberately narrow accepted grammar

The implementation supports the reviewed line-oriented subset, not arbitrary
Caddy syntax. Unsupported configurations are rejected even if Caddy itself
could interpret them. Input size, line count and nesting depth are bounded.
LF/CRLF, indentation, blank lines, standalone comments and either site order are
accepted. Inline blocks/comments, escapes, continuations, imports, snippets,
wildcards, fallback sites, dynamic targets and unknown directives are rejected.

The sole global block contains the exact listener settings and discard logging.
Each site requires its exact safety headers, discard logging, all three named
private-route matchers, and exactly one unconditional ordered `route` block:

- Production: namespace deny, parsed `rest_route` deny, ambiguous/encoded query
  deny, the two existing health responses, then the sole production proxy.
- Preview: the same three edge denies, unconditional `basic_auth` (bcrypt), then
  the sole preview proxy. No unauthenticated health exception or alternate route
  is accepted.

The complete private-query expression must equal the existing reviewed
namespace grammar, including encoded/repeated query variants. A guard appearing
elsewhere, a matcher-limited route/authentication directive, a late deny, or an
extra handler is not sufficient. Every proxy must contain exactly one literal
target and no options block. Every logger must contain only `output discard`.
Header projection, `log_credentials` and alternate sinks are rejected.

Preview authentication requires 1–8 unique bounded ASCII account identifiers
and syntactically complete bcrypt values. This proves the accepted configuration
structure, not password strength, credential ownership, successful login, loaded
behavior, or preview-process identity. No actual account or hash is a fixture.

## Verification

Tests live in `tests/deployment/test_dev_ingress_001.py`; their production source
is the independent, test-owned
`tests/fixtures/deployment/dev-ingress-production.Caddyfile`. Guarded preview
fixtures and unsafe mutations use synthetic authentication data. They cover
production-only compatibility, explicit preview classification, closed policy
validation, every guard, missing/duplicate sites and proxies, unknown sites,
wildcards/fallbacks, invalid targets, hidden targets, missing/incomplete/late or
matcher-limited authentication, unsafe logging/projection and ambiguous syntax.

Two positive cases independently invoke offline `caddy adapt` on test-owned
files under the canonical harness's provisioned bootstrap test root. They check
actual adapted deny/auth/proxy ordering and discard sinks. They never contact
the Caddy admin API, serve traffic, or change the running process. Offline
adaptation is not live attestation. The existing ingress adapter is separately
checked to remain fail-closed for two upstreams.

Focused command (no broad suite):

```sh
ops/macos/validation/run-deployment-regression-gate.sh -q tests/deployment/test_dev_ingress_001.py tests/deployment/test_dpl_v1_contracts.py
```

Final evidence: **164 passed in 32.20s**, zero failures, warnings or skips;
canonical invocation `7dfe736999db48ccadb780f4558f8c72`, evidence directory
`/private/tmp/aicontrolcenter-canonical-evidence.0ZMDL9`.
This comprises 134 Phase A cases (7 positive, 127 rejection cases) and 30
existing DPL contract tests. The earlier implementation run passed 154 cases
with 280 warnings from pytest's stale shared temporary-directory cleanup; the
final offline adaptation cases use the harness-provisioned isolated root.

Exact Phase A test functions below all have the node prefix
`tests/deployment/test_dev_ingress_001.py::`. Parameter definitions and explicit
case names are in that file; each parameterized case passed.

| Test function | Cases | Expectation |
| --- | ---: | --- |
| `test_production_only_compatibility` | 1 | Accept |
| `test_fully_guarded_preview_classification` | 3 | Accept |
| `test_policy_registry_and_input_immutability` | 1 | Accept without changing inputs |
| `test_accepted_fixtures_have_expected_offline_caddy_semantics` | 2 | Accept; independently check adaptation |
| `test_missing_duplicate_unknown_and_fallback_sites_rejected` | 10 | Reject |
| `test_unapproved_and_hidden_proxy_targets_rejected` | 22 | Reject |
| `test_alternate_proxy_routes_rejected` | 5 | Reject |
| `test_each_site_has_exactly_one_upstream` | 4 | Reject missing/duplicate proxy |
| `test_preview_authentication_cannot_be_missing_partial_or_bypassed` | 14 | Reject |
| `test_every_private_guard_is_required_and_ordered` | 24 | Reject |
| `test_private_guard_bypasses_rejected` | 6 | Reject |
| `test_unsupported_or_ambiguous_syntax_rejected` | 13 | Reject |
| `test_unsafe_logging_and_credential_projection_rejected` | 8 | Reject |
| `test_site_safety_is_checked_independently_of_safe_global_logging` | 6 | Reject |
| `test_invalid_policy_cannot_authorize_sites` | 6 | Reject |
| `test_policy_loading_rejects_ambiguous_and_changed_identities` | 6 | Reject |
| `test_production_contract_is_not_replaced_by_site_policy` | 1 | Reject |
| `test_unguarded_authenticated_dev_is_rejected` | 1 | Reject with `PRIVATE_GUARDS_REQUIRED` |
| `test_phase_a_does_not_relax_existing_ingress_adapter` | 1 | Existing adapter still rejects two proxies |

## Historical Phase B1 and B2a results

`CaddyFileAdapter.observe_caddy_desired_state()` now reports explicit
`production` and optional `preview` site identities, the canonical production
upstream, policy version, repository-only evidence references, and explicit
false authority/readiness fields. It reports all classified loopback upstreams
under `upstreams` while preserving the production endpoint separately.
`CaddyIngressAdapter.observe()` projects the same shared observation into the
canonical production endpoint used by readiness; it does not replace
`IngressContract.upstream` with the preview endpoint.

Phase B2a adds an application readiness boundary: repository-only Caddy
classification (`evidence_scope=repository-desired-state` or
`live_network_test_performed=false`) produces `DEGRADED`, even when all desired
state checks align. Classification therefore cannot establish live readiness.

The following result describes the pre-B2c state and is retained as historical
evidence: the unguarded live-referenced Caddyfile failed closed with
`PRIVATE_GUARDS_REQUIRED`, and inventory recorded `host-caddy` as unavailable
and `public-edge-policy` as degraded. It is not the current repository desired
state after B2c.

Focused B1 verification (historical; not a B2c result):

```sh
ops/macos/validation/run-deployment-regression-gate.sh -q tests/deployment/test_dev_ingress_001.py tests/deployment/test_dpl_02c_ingress.py tests/deployment/test_macos_inventory_adapters.py tests/deployment/test_mac_inventory_application.py
```

Final result: **236 passed, 288 warnings, 0 failures**; canonical invocation
`6f96e292e4cc4fc7b7fafd28283f13f7`, evidence directory
`/private/tmp/aicontrolcenter-canonical-evidence.ytEOxS`. Warnings originate in
existing deployment-test temporary-directory cleanup and are non-blocking.
The previous 226-test run omitted the direct role-specific inventory assertion;
the final count includes it.

The Phase A security regression remains in `test_dev_ingress_001.py`; B1 added
adapter rejection, role projection, sanitized failure and cache/re-read tests.

## Phase B2c correction and approval boundaries

The approved edit adds the reviewed three private-route matchers and ordered
403 denies to the Dev site. The existing Dev authentication and proxy target
remain unchanged. Offline adaptation succeeds, and the shared classifier
accepts the complete production-plus-preview desired state.

The directly affected readiness regression now separates two claims: the
current repository Caddyfile is guarded and classified with canonical
production upstream `127.0.0.1:58082`, while repository-only evidence produces
`DEGRADED`; a test-owned unguarded preview fixture still fails closed with
sanitized reporting.

The reviewed Caddyfile digest remains stale by design. No Caddy reload,
restart, deployment, active-runtime observation, production activation, or
external authenticated QA has occurred.

Focused B2c correction verification:

```sh
ops/macos/validation/run-deployment-regression-gate.sh -q tests/deployment/test_dpl_02c_ingress.py tests/deployment/test_macos_inventory_adapters.py::test_caddy_sole_edge_mapping tests/deployment/test_mac_inventory_application.py::test_inventory_reports_classified_production_and_preview_roles
```

Result: **22 passed, 0 failed, 0 skipped, 0 deselected, 0 warnings**;
canonical invocation `658b02fa82164ea68961870d4ffca032`, evidence directory
`/private/tmp/aicontrolcenter-canonical-evidence.e7Hmcp`.

## Phase B2f integration and approval boundaries

Phase B2f integrates the existing `dev-ingress/v1` classifier into the
repository-backed preactivation and effective-runtime evidence paths. The
classifier is shared with the Caddy adapters; no second parser or relaxed
security rule set was added. Preactivation now requires a valid, role-specific
classification in addition to the reviewed artifact checks, and effective
runtime attestation requires the same repository proof before evaluating its
existing process, listener, loaded-versus-adapted equality, and stability
proofs.

| Files | Required work |
| --- | --- |
| `core/deployment/adapters/macos/ingress.py`, `core/deployment/adapters/macos/repository.py` | Already integrated in Phase B1. Further changes are limited to approved readiness and runtime evidence correlation. |
| `core/api/dependencies/deployment.py` | No B1 change required; revisit only if dependency injection is needed for a later readiness integration. |
| `core/deployment/application/ingress_readiness.py`, `core/deployment/application/mac_inventory.py` | Correlate classified roles and retain sanitized fail-closed reporting; never discard unknown sites to obtain readiness. |
| `ops/macos/shopping/preactivation_observer.py` | **B2f complete:** require the shared classification and its policy/schema/registry/ingress/Caddyfile closure in repository evidence. The reviewed Caddyfile digest remains stale, so repository safety remains blocked until separately approved. |
| `ops/macos/shopping/effective_runtime_attestor.py` | **B2f complete:** require the same repository classification before runtime proofs. Existing process identity, listener, loaded-versus-adapted equality, stability, and fail-closed checks remain unchanged. |
| `core/shopping/control_plane_read/effective_runtime.py` | No B2f change; production activation and effective-runtime policy gates remain separate from repository classification. |
| `tests/test_shopping_preactivation.py`, `tests/test_shopping_effective_runtime_attestation.py` | **B2f complete:** cover production-only and production-plus-preview role assertions, stale-digest blocking, classifier-required runtime evidence, adapter ordering, and sanitized fail-closed behavior. |

The repository desired state now meets the reviewed edge-guard policy. Active
runtime qualification still requires separate loaded-versus-adapted observation,
digest review, and operational authorization for any reload or restart. Its
LaunchDaemon does not need to change under this architecture. Preview
provenance, runtime activation and dependency-policy blockers remain separate.

The Caddyfile, LaunchDaemon, logging-policy digests, existing adapters/observers,
canonical ingress contract, dependency policy and all three previously modified
Shopping tests are preserved in Phase A. No Git staging or publication is part
of this work.

Focused B2f verification:

```sh
ops/macos/validation/run-deployment-regression-gate.sh -q tests/test_shopping_preactivation.py tests/test_shopping_effective_runtime_attestation.py
```

Result: **663 passed, 0 failed, 0 skipped, 0 deselected, 288 warnings**;
canonical invocation `845b413dc7564908893a8882d6b35f11`, evidence directory
`/private/tmp/aicontrolcenter-canonical-evidence.Px5FyU`. The warnings are the
existing pytest temporary-directory cleanup warnings and do not change the
fail-closed result.

This repository-only result does not authorize a digest refresh, active Caddy
observation, reload, restart, deployment, or production activation. The
current repository classification is accepted, but readiness remains
DEGRADED while the reviewed digest is stale and active loaded configuration is
unverified.

## Phase B2p diagnostic observability

B2p adds a fixed, value-free `caddy_diagnostic` envelope around the existing
loopback admin-read path in `ops/macos/shopping/effective_runtime_attestor.py`.
It records only a safe timestamp, fixed source identifier, process-generation
and stability states, loaded-document and comparison states, and allowlisted
failure categories and codes. It does not change the approved endpoint, add an
alternate evidence source, retain raw stderr or response data, or add fields to
the reducer contract. Diagnostic metadata alone cannot establish readiness,
effective-runtime attestation, or activation; exact loaded-versus-adapted
comparison and stability remain required.

Focused B2p tests cover fixed-schema redaction, classified subprocess failures,
unknown exceptions, ambiguous generation, successful mocked loaded evidence,
exact comparison, and fail-closed runtime status. No real admin read or runtime
observation is part of B2p.

## Phase B2r single-read boundary

B2r adds a repository-only `observe_caddy_single_read()` seam for a future,
separately approved observation. The seam validates internal current-process
provenance before making at most one bounded request to the existing loopback
admin endpoint. It does not call the full collector, retry, follow redirects,
discover another endpoint, or manufacture stability. The current repository
does not provide a verified process-start/generation source, so the default is
`NOT_ATTEMPTED` / `PROVENANCE_UNVERIFIED` with zero requests. Mocked tests may
exercise the contract, but one successful read remains a limited observation:
exact loaded-versus-adapted comparison can be recorded, while stability,
effective-runtime attestation, readiness, and activation remain blocked.
