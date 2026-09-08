# Shopping 01G2 closed deployment proof contract

Schema: `shopping/effective-runtime-attestation/v2`. This repository-only
implementation follows SHOP-SERVICE-START-01B and the 01G1B approved model.
v1 used an intentionally impossible loaded-state proof model: universal
Apache/WordPress behavior could not be maintainably observed. v2 separates
control-enforced repository invariants, deployment identity binding, runtime
observations, and closed component/control obligations. No security requirement
was removed. Logging safety describes the reviewed closed deployment invariant,
not observation of arbitrary future executable behavior.

## Contract and decisions

The pure internal reducer accepts only closed boolean groups and exact reviewed
manifest policy plus identity-only component observations from a trusted collector. There is no human evidence ingestion
interface. Unknown fields/types, missing facts, unresolved identities, mismatches,
and duplicate component identifiers fail closed; input values are never emitted.
The aggregate schema is versioned rather than reinterpreting v1 fields.

* `repository_invariants`: reviewed edge/safety policy, fixed target with no
  generic proxy, and absence of a public observation endpoint.
* `deployment_identity`: pinned immutable expected WordPress image and matched
  actual image, container identity, fresh runtime and serving-generation provenance,
  expected mounts/configuration and artifact integrity, no unexpected mutable code
  or configuration, Caddy executable/config generation, Control Plane implementation.
* `caddy_effective` and `topology`: runtime observations; loaded Caddy configuration
  must equal the reviewed adaptation under host process identity. Upstream and
  WordPress publication are exactly 127.0.0.1:58082, private namespace/rest_route
  denied, no alternate handler, no database publication, expected networks only,
  and trusted Mac binding. `transport` requires fixed bounded read-only transport.
* `closed_controls`: Apache configuration closure and discard-only access/error
  sinks, PHP disabled/discard logging, disabled display/startup errors, suppressed
  exception arguments, false WordPress debug/log/display policy, reviewed
  Authorization code without deliberate secret projection, no Authorization-capture
  tracing/APM/logging, and no unresolved executable/logging components.

`public_edge_runtime_isolation_proven` requires the edge repository controls,
loaded Caddy edge facts, topology and fixed transport. It does not require the
Apache/PHP/WordPress logging inventory or the Caddy logging sink decision.
`deployment_logging_safety_proven` requires repository safety, every deployment
binding and closed control, complete component identity comparison, and loaded
Caddy identity/config equality with discard sinks. Repository file hashes or
Apache/PHP file equality alone cannot pass it.
`controlled_nonprod_soft_launch_ready` requires both decisions, all exact
component/deployment identities and every required fact without errors. It is an
informational prerequisite only: activation remains BLOCKED and no capability,
verifier installation or authenticated request is authorized. Production=false;
Ubuntu=false, even with complete synthetic evidence.

Digest-bound reviewed artifacts establish edge/safety controls but do not close
the full route/proxy registration inventory. The collector keeps
`no_generic_proxy_or_caller_target` and `no_public_observation_endpoint` false;
generic repository safety cannot establish these specific absence claims.

## Component closure

`config/schemas/shopping-runtime-component-manifest.schema.json` defines
`shopping/runtime-component-manifest/v1`; the repository manifest is
`config/deployment/shopping-runtime-component-manifest.json`.
All seven categories currently remain DISCOVERY_REQUIRED. This is never an empty
approved inventory. REVIEWED_COMPLETE with an empty list represents explicitly
reviewed absence; it still needs trusted actual inventory and deployment binding.
Runtime reports identity; AIControlCenter owns and applies component policy.
Observed entries contain exactly `identifier`, `version`, and
`artifact_digest_or_immutable_identity`; the enclosing category supplies category.
All additional observed keys are rejected. Role, effect class, permissions,
Authorization handling, observation participation, identity approval status and
approval membership come only from the repository manifest.
`CONTROL_ENFORCED != RUNTIME_OBSERVED`.
Required identities must all occur; optional approved identities may occur; every
unknown identity is denied. No wildcard approval or existence-implies-safe rule.

WooCommerce, ai-shopping-storefront and ai-controlcenter-shopping-read are required.
WooCommerce deployed version/identity is unknown. Source versions 0.16.0 and 1.0.0
for the other two do not establish deployed identity. Storefront source uses
wp_remote_get and set_transient and activation writes options/rewrites. Shopping
read handles authorization, has no explicit source application-state writes or
outbound requests. These source annotations do not approve dependency behavior.
None participates in observation. Exact artifact identities remain null/UNRESOLVED.
Apache/PHP/Zend, network plugins, mu-plugins and drop-ins remain unresolved and BLOCKED.

## Collector limits and execution boundary

The rejected FILES_PROBE and its Docker exec/PHP subprocess were removed.
No native Apache module, WordPress runtime sensor, public telemetry endpoint or
custom image was added. No WordPress bootstrap occurs. Existing fixed read-only
metadata and Caddy mechanisms are retained for a separately authorized later run;
none was executed in this implementation pass. No runtime deployment performed.

The collector has zero arguments, trusted passwd/UID Mac account resolution, fixed
commands, no caller/environment overrides, no secret/environment inspection,
no shell/retry/mutation, streaming 128 KiB stdout bounds, five-second child limits
and a 30-second total deadline. Synthetic tests replace runtime commands.
Its existing reads cannot establish immutable image/mount integrity or authoritative
serving-generation provenance. These fields stay false with deterministic missing
field reasons and RUNTIME_BINDING_UNPROVEN / SERVING_GENERATION_PROVENANCE_UNPROVEN.
Repeated metadata is not proof that no reload occurred or opcode cache is current.
The collector supplies no actual component inventory, so cannot pass logging or
soft launch even after future manifest review without new reviewed binding support.

Soft launch is still BLOCKED. No runtime inspection, deployment, canonical,
capability creation, verifier mutation or authenticated read occurred in 01G2.
The historical evidence below is v1 only and was not rerun.

## 01G execution evidence

Validation: focused 01G tests 256 passed; related preactivation/control-plane-read
tests 329 passed. The canonical harness ran exactly once after final code changes:
`ec03d0f406604222964341137ea1c134`, 5537 passed, 5 deselected, 583 warnings,
2 subtests passed, exit 0. Known cleanup/deprecation warnings do not grant or
withhold runtime proof. These test results do not promote launch readiness.

Executed once on 2026-09-08 against baseline
`aca4bb7e0b899737c0a28ca96255d0237a402c53`. Result: **BLOCKED**, exit 2.
Repository transport controls were validated. Local inspection commands returned
nonzero; container topology and Caddy loaded configuration could not be proven
in this execution context. This is unavailable evidence, not a diagnosis of the
underlying services. No retry/remediation or authenticated read was performed.
Public-edge runtime isolation and deployment logging safety are both false.
Activation remains BLOCKED; capability creation, verifier mutation, runtime
mutation, secret exposure, production authority and Ubuntu authority are false.
The following reason codes denote absent proofs (including names ending in
`_PROVEN`); they are not assertions that the named control passed.

```json
["APACHE_EFFECTIVE_AUTHORIZATION_NOT_LOGGED_PROVEN","APACHE_EFFECTIVE_CUSTOM_LOG_SAFE_PROVEN","APACHE_EFFECTIVE_ERROR_LOG_SAFE_PROVEN","APACHE_EFFECTIVE_LOADED_CONFIG_PROVEN","APACHE_EFFECTIVE_MODULES_SAFE_PROVEN","APACHE_EFFECTIVE_OVERRIDE_DISABLED_PROVEN","APACHE_LOADED_STATE_UNOBSERVABLE","CADDY_EFFECTIVE_AUTHORIZATION_NOT_LOGGED_PROVEN","CADDY_EFFECTIVE_HOST_EDGE_IDENTITY_PROVEN","CADDY_EFFECTIVE_LOADED_CONFIG_PROVEN","CADDY_EFFECTIVE_NAMESPACE_DENY_PROVEN","CADDY_EFFECTIVE_NO_ALTERNATE_HANDLER_PROVEN","CADDY_EFFECTIVE_REST_ROUTE_DENY_PROVEN","CADDY_EFFECTIVE_SAFE_SINK_PROVEN","CADDY_EFFECTIVE_UPSTREAM_58082_PROVEN","PHP_APACHE_SAPI_LOADED_STATE_UNOBSERVABLE","PHP_EFFECTIVE_DISPLAY_ERRORS_OFF_PROVEN","PHP_EFFECTIVE_DISPLAY_STARTUP_ERRORS_OFF_PROVEN","PHP_EFFECTIVE_ERROR_LOG_SAFE_PROVEN","PHP_EFFECTIVE_EXCEPTION_ARGS_IGNORED_PROVEN","PHP_EFFECTIVE_EXTENSIONS_SAFE_PROVEN","PHP_EFFECTIVE_LOADED_CONFIG_PROVEN","PHP_EFFECTIVE_LOG_ERRORS_OFF_PROVEN","SUBPROCESS_NONZERO","TOPOLOGY_DATABASE_IDENTITY_PROVEN","TOPOLOGY_EXPECTED_NETWORKS_PROVEN","TOPOLOGY_INTERNAL_NETWORK_PROVEN","TOPOLOGY_MARIADB_NO_PUBLISHED_PORTS_PROVEN","TOPOLOGY_WORDPRESS_IDENTITY_PROVEN","TOPOLOGY_WORDPRESS_LOOPBACK_58082_PROVEN","WORDPRESS_ACTIVE_PLUGINS_UNOBSERVABLE","WORDPRESS_EFFECTIVE_ACTIVE_PLUGINS_SAFE_PROVEN","WORDPRESS_EFFECTIVE_CONSTANTS_UNOBSERVABLE","WORDPRESS_EFFECTIVE_DEBUG_DISPLAY_FALSE_PROVEN","WORDPRESS_EFFECTIVE_DEBUG_FALSE_PROVEN","WORDPRESS_EFFECTIVE_DEBUG_LOG_FALSE_PROVEN","WORDPRESS_EFFECTIVE_DROP_INS_SAFE_PROVEN","WORDPRESS_EFFECTIVE_MU_PLUGINS_SAFE_PROVEN","WORDPRESS_EFFECTIVE_READ_PLUGIN_ACTIVE_PROVEN","WORDPRESS_EFFECTIVE_READ_PLUGIN_DEPLOYED_PROVEN"]
```
