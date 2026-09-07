# Shopping 01G effective runtime attestation

Run from the repository root, with no arguments:

```sh
.venv/bin/python -m ops.macos.shopping.effective_runtime_attestor
```

Schema: `shopping/effective-runtime-attestation/v1`. Stdout is one compact JSON
object; exit 0 means PASS, exit 2 means BLOCKED. Both retain activation BLOCKED.
There is no input evidence file, environment override, remediation or bearer path.
The pure reducer is internal, not an interface for submitting runtime assertions.

The Mac account resolver binds the fixed commerce Docker socket to passwd/UID.
Selected inspect fields establish project/service identity, running state, exact
loopback publish, database port absence and both network IDs. A second observation
rejects changed metadata, including container IDs and start times. Environment,
container logs and Docker credential configuration are never inspected.

Caddy proof requires a single host Caddy process owning the fixed admin and edge
listeners, executable identity matching the local Homebrew executable, successful
HTTP 200 admin configuration reads, and complete equality with adaptation of the
digest-bound reviewed policy. Reads bracket adaptation and listener identity.
Extra routes, changed ordering, stale upstreams or any logging changes block.
Adaptation alone cannot prove anything about loaded state. Missing privileges,
admin access or listener visibility block; the attestor does not enable them.

The filesystem probe uses `php -n` without loading WordPress, plugins or ini files.
It emits only selected public-file digests and booleans. It tokenizes wp-config
without executing it, never prints configuration values, and treats duplicate or
nonliteral debug definitions as unproven. Plugin presence and reviewed file identity
are distinct from activation. Any component beyond the reviewed read plugin and
standard inert plugin index, any mu-plugin or known drop-in is unapproved.
Plugin filenames/configuration and wp-config hashes are not emitted.

**This collector cannot currently produce a live PASS.** It intentionally has no
authoritative observation channel into the already-running Apache/PHP SAPI or
WordPress active-plugin state. Apache config-test output, fresh CLI ini/module
output, persisted constants and on-disk extension absence would not establish
that loaded state. Those controls remain false with explicit `*_UNOBSERVABLE`
reason codes even when every inspected file matches. Unknown extensions, active
plugins and cached code therefore cannot be silently classified as safe. Adding
an authoritative observation mechanism requires a separately reviewed design;
this task installs none and does not bootstrap WordPress to query its database.

Transport proof reuses the reviewed complete-source identities and checks fixed
loopback/port, disabled environment/redirect/retry behavior, total deadline and
response bound. No transport method or capability operation is invoked.

Each subprocess has at most five seconds, stdout is capped while streaming at
128 KiB, and observations share a 30-second monotonic deadline (with up to one
second to reap a killed local inspection child). Stderr is discarded. Malformed,
duplicate, oversized, changed or unavailable evidence blocks with fixed codes.
Only local inspection subprocesses may be killed for timeout cleanup; no service
process is signaled. These are point-in-time observations, not a continuous lease.

Architecture review: fixed Mac path, engine boundaries preserved, Ubuntu and
production authority false; no activation or desired-state apply path.
Security review: bounded output, strict JSON, explicit unknown-state blockers,
no application bootstrap, secret projection, credential use or runtime writes.
Maintainability review: one collector, one pure reducer, fixed schema/commands,
and deterministic synthetic failure coverage. No project readiness promotion.

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
