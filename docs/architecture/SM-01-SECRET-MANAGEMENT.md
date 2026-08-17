# SM-01 — Shopping Secret Management

Status: **SM-01B-02D-01B IMPLEMENTATION AND VALIDATION COMPLETE**

Current milestone: `SM-01B-02D-01B — Shopping Provisioning Governance Coordinator v1`

Milestone identifier: `SM_01B_02D_01B_SHOPPING_PROVISIONING_GOVERNANCE_COORDINATOR_VALIDATED`

Implementation commit: `8229288d68d46383082cec48ffc726bd0dbee09a`

Next engineering milestone: `SM-01B-02D-02 — Concrete Provisioning Capabilities v1`

This architecture separates metadata, evaluation, delivery, materialization,
and mutation authority. SM-01A established layers 1 and 2. SM-01B-01 adds the
architecture and read-only inspection portion of layer 3; it does not deploy
the toolchain or backend.

SM-01B-02B adds a provisioning planner. SM-01B-02C implements bounded mutation
adapter code only. The
canonical provisioning definition and Draft 2020-12 schema define exactly five
typed actions. Core `ProvisioningPlan` is vendor-neutral and value-free.
Malformed input emits only sanitized `UNKNOWN_ACTION` or
`MALFORMED_CONFIGURATION` evidence. The read-only macOS provisioning inspector
performs planning only, and core imports from `ops` and `integrations` remain
zero. The adapters reuse SEC-02 `ControlledExecutionPort`, accept only exact
target `SHOPPING_SECRET_PROVISIONING` and an exact action, and invoke at most
one narrow injected capability. They issue or consume no authorization; do not
retry, rollback, or compensate; and produce value-free
`GovernanceExecutionReceipt` evidence with a deterministic injective receipt
identity namespace over the full `execution_request_id`. They provide no
generic shell/argv/package-manager execution framework and create no parallel
governance framework. Implementing bounded adapters is not authorization to
execute them.

SM-01B-02D-01A resolves the previous SM-01B-02D-00 blocker with the generic
SEC-02 `AuthorizationConsumptionPort` and immutable
`AuthorizationConsumptionCommand` and `AuthorizationConsumptionResult`.
Authorization consumption is a generic Governance boundary, not a
Shopping-specific boundary. `consume_once` is its only API.

`consume_once` requires `AUTHORIZED` authorization, `AVAILABLE` mutation
budget, exact lifecycle/authorization/target/action-scope/mutation-budget
bindings, and a matching zero-invocation budget line item. It returns only
`CONSUMED` authorization, exactly `CONSUMED` zero-invocation mutation budget,
a `COMMITTED` `GovernanceAuthorizationConsumptionReceipt`, and an exact-bound
`GovernanceExecutionRequest`. The result is evidence and grants no execution
authority.

SM-01B-02D-01B enforces planner -> explicit human-authorized lifecycle ->
read-only precondition -> SEC-02 `ALLOW_AUTHORIZATION_CONSUMPTION` ->
`AuthorizationConsumptionPort.consume_once` -> fresh read-only precondition ->
SEC-02 `ALLOW_SINGLE_INVOCATION` -> exactly one of five bounded
`ControlledExecutionPort` adapters -> read-only postcondition -> closeout or
stop. Consumption evidence grants no execution authority. `READY`, `BLOCKED`,
or `MALFORMED` causes zero consumption and zero invocation. Post-consumption
drift stops with consumed authorization and zero invocation. `FAILED` or
`UNCERTAIN` stops after one attempt. There is no automatic retry, rollback, or
compensation.

## 1. Secret Contract — implemented

`deploy/shopping/config/secret-contract.json` is the single canonical metadata
authority. It is JSON-first and value-free. Python does not duplicate its exact
canonical key table.

The current `runtime_cutover` action requires:

- `SHOPPING_WORDPRESS_PORT`
- `SHOPPING_DB_NAME`
- `SHOPPING_DB_USER`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`

The current `bootstrap` action requires:

- `SHOPPING_WORDPRESS_PORT`
- `SHOPPING_DB_NAME`
- `SHOPPING_DB_USER`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`
- `SHOPPING_SITE_URL`
- `SHOPPING_SITE_TITLE`
- `SHOPPING_ADMIN_USER`
- `SHOPPING_ADMIN_PASSWORD`
- `SHOPPING_ADMIN_EMAIL`

The current secret-classified names are:

- `SHOPPING_ADMIN_PASSWORD`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`

Classification is metadata, not a stored value. The contract contains no
secret material and grants no activation or mutation authority.

## 2. Secret Preflight — implemented

`ops/macos/shopping/secret_preflight.py` is a read-only consumer and validator
of the canonical JSON contract. It performs structural fail-closed validation,
resolves required names for the requested action, and evaluates name presence
only. Values are never inspected or serialized.

Unsupported actions, unknown supplied key names, invalid contract structure,
and missing required keys produce non-success. Not-evaluated is a separate
state, not a synonym for pass or fail. The preflight performs no authorization,
mutation, secret materialization, Keychain query, or Docker, Colima, runtime,
WordPress, WooCommerce, MariaDB, Caddy, or Ubuntu access.

Compose intentionally remains plain `${SHOPPING_*}` interpolation. This keeps
read-only runtime observation independent of secret material. Neither
`.env.admin` nor `.env.woocommerce` is a runtime authority.

## 3. Secret Backend — architecture/inspection implemented; provisioning not deployed

SM-01B-01 selects SOPS+age as the replaceable Shopping secret-backend
architecture. This selection is not deployment. Production status remains
`NOT_DEPLOYED`; SOPS installation, age installation, age key generation,
encrypted Shopping payload provisioning, and secret materialization are all
false.

`config/shopping-secret-backend.json` is the canonical backend definition and
`config/schemas/shopping-secret-backend.schema.json` its canonical schema.
`core/secrets/ports.py` is the vendor-neutral port. SOPS+age specifics are
isolated in the read-only macOS outer adapter
`ops/macos/shopping/sops_age_backend.py`; core imports from `ops` and
`integrations` remain zero. JSON Schema and runtime safety validation are
aligned.

Identity custody is portable: base `control-plane-home`, relative path
`.config/sops/age/keys.txt`. No concrete `/Users/<username>` path is canonical;
`control_plane_home` is dependency-injected. The adapter does not discover
HOME, environment, pwd, Keychain, runtime, Docker, Colima, or network. It uses
metadata-only `lstat` inspection and never reads identity or payload contents.

The canonical logical encrypted payload path is
`deploy/shopping/secrets/shopping.enc.yaml`. The metadata policy requires two
recipient roles, `control-plane` and `offline-recovery`, but stores no recipient
material in the canonical definition. `materialization_implemented=false`.
AIControlCenter on the Mac remains the sole Control Plane; Ubuntu must not own,
persist, select, or govern Shopping secrets.

`SM-01B-02B — Provisioning Planner v1` and `SM-01B-02C — Bounded Mutation
Adapters v1` are validated. The five exact actions remain:

- `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`
- `SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`
- `SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`
- `SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`
- `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`

Offline-recovery private custody remains external.

## 4. Secret Materialization — not implemented

No component currently transforms backend-held material into process,
container, file, or command input. SM-01A reads no secret value and defines no
materialization lifecycle. Presence-only preflight must remain value-free even
after a backend is introduced.

## 5. Authorization / Mutation — generic consumption boundary implemented; execution not authorized

A valid contract or successful preflight is not authorization. A desired-state
package is not activation authority. Any future Production mutation requires
explicit human authorization immediately before execution. One human
authorization lifecycle maps to one exact, bounded Production mutation.
Invocation still requires current read-only precondition recollection,
followed by SEC-02 `ALLOW_SINGLE_INVOCATION`, and then
`ControlledExecutionPort.invoke_once`. There is NO automatic retry, NO
automatic rollback, and NO compensation.

AIControlCenter on the Mac mini M4 remains the sole Control Plane and owns
governance, policy, orchestration, approval, authorization, audit, deployment
control, and business logic. Ubuntu remains an optional stateless
infrastructure worker and owns no AI workload, application state, Shopping
secret, or Control Plane authority. Host Caddy remains the only public edge;
WordPress remains the CMS Engine and WooCommerce the Commerce Engine.

## Runtime and activation truth

The desired WordPress binding remains
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`, and desired
`SHOPPING_WORDPRESS_PORT` remains `58082`. MariaDB remains unpublished.
Shopping service and WooCommerce capability status remain `NOT_DEPLOYED`.

`SHOPPING_RUNTIME_ACTIVATED=false`

SM-01A performed no Production shopping runtime activation, port cutover,
secret delivery, materialization, or new Production authorization. SM-01B-01
selected only an architecture and performed metadata-only inspection: it did
not install SOPS or age, generate an age key, provision an encrypted payload,
materialize secrets, inspect Production runtime, query Keychain, read secret
values, or mutate Production. `SHOPPING_STOREFRONT_ONLINE_READ_ONLY` remains
future work after runtime activation.

Historical MariaDB credential continuity remains unresolved. Introducing
SOPS+age cannot recover or silently replace historical MariaDB credentials.
Production runtime cutover remains blocked on an explicit
continuity/recovery/rotation strategy.

Offline-recovery private custody remains external. SM-01B-02C does not recover,
rotate, replace, derive, invent, or validate historical MariaDB credentials.

## SM-01B-02D-01B validation record

- Status: implementation and validation complete
- Milestone: `SM_01B_02D_01B_SHOPPING_PROVISIONING_GOVERNANCE_COORDINATOR_VALIDATED`
- Implementation commit: `8229288d68d46383082cec48ffc726bd0dbee09a`
- Focused validation: `181 passed`
- Canonical regression: `3349 passed, 5 deselected, 447 warnings`, `RC=0`
- Canonical execution count: exactly `1`
- `PRODUCTION_STATUS_NOT_DEPLOYED=true`
- `MATERIALIZATION_IMPLEMENTED=false`
- `PRODUCTION_MUTATION=false`
- `AUTHORIZATION_CONSUMED=false`
- `SECRET_VALUES_READ=false`
- `RUNTIME_INSPECTION=false`
- `DOCKER_ACCESS=false`
- `COLIMA_ACCESS=false`
- `NOTION_SYNC=false`

Authorization-consumption result evidence grants no execution authority. One
human authorization lifecycle remains required per bounded Production
mutation. Historical MariaDB credential continuity remains unresolved, and
`SHOPPING_RUNTIME_ACTIVATED` remains the Production milestone.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
worker. Core has no dependency on `ops.macos`. No generic shell or argv
execution API exists. Next engineering milestone is
`SM-01B-02D-02 — Concrete Provisioning Capabilities v1`.

## SM-01B-02C validation record

- Milestone: `SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED`
- Implementation commit: `5a811cb1f9c782acb4f3e537596fb47ae0c599ff`
- Focused final validation: `128 passed`
- Canonical final validation: `3288 passed, 5 deselected, 447 warnings`,
  `RC=0`, executed exactly once on final implementation code
- Exact three-file implementation scope: PASS
- Post-canonical scope: PASS
- Staged scope: PASS
- Staged diff check: PASS
- Commit: PASS
- Push: PASS
- Upstream alignment: PASS (`0 0`)
- `production_status=NOT_DEPLOYED`
- `materialization_implemented=false`
- `SOPS_INSTALLATION=false`
- `AGE_INSTALLATION=false`
- `AGE_KEY_GENERATION=false`
- `OFFLINE_RECOVERY_KEY_GENERATION=false`
- `SECRET_PAYLOAD_CREATION=false`
- `SECRET_MATERIALIZATION=false`
- `AUTHORIZATION_CONSUMED=false`
- `RUNTIME_INSPECTION=false`
- `PRODUCTION_MUTATION=false`
- `SHOPPING_RUNTIME_ACTIVATED=false`

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker with no Shopping secret ownership. Adapter implementation
is not authorization to execute adapters. Each future Production mutation
requires separate human authorization immediately before exactly one bounded
invocation. There is no automatic retry or rollback. Next development
milestone: `SM-01B-02D — Authorized Toolchain & Identity Provisioning v1`.
SM-01B overall remains incomplete.

## SM-01B-02B validation record

- Milestone: `SM_01B_02B_PROVISIONING_PLANNER_VALIDATED`
- Implementation commit: `2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`
- Focused final validation: `73 passed`
- Canonical regression: `3236 passed, 5 deselected, 447 warnings`, `RC=0`,
  executed exactly once on final implementation code
- Exact six-file implementation scope: PASS
- Post-canonical scope: PASS
- Staged scope: PASS
- Staged diff check: PASS
- Commit: PASS
- Push: PASS
- Upstream alignment: PASS (`0 0`)
- Production truth: `NOT_DEPLOYED`
- `materialization_implemented=false`
- `SOPS_INSTALLATION=false`
- `AGE_INSTALLATION=false`
- `AGE_KEY_GENERATION=false`
- `OFFLINE_RECOVERY_KEY_GENERATION=false`
- `SECRET_PAYLOAD_CREATION=false`
- `SECRET_MATERIALIZATION=false`
- `AUTHORIZATION_CONSUMED=false`
- `RUNTIME_INSPECTION=false`
- `PRODUCTION_MUTATION=false`
- `SHOPPING_RUNTIME_ACTIVATED=false`

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
worker with no Shopping secret ownership. SM-01B overall remains incomplete.

## SM-01B-01 validation record

- Focused final validation: `66 passed`
- Canonical regression: `3205 passed, 5 deselected, 447 warnings`, `RC=0`,
  executed exactly once on final implementation code
- Post-canonical exact six-file scope: PASS
- Staged scope: PASS
- Staged diff check: `RC=0`
- Implementation commit/push: PASS
- Git upstream counts: `0 0`
- Implementation commit: `1ada572a75cf4313f65288e81134777948900cda`
- Production mutation: false
- Secret values read: false
- Keychain query: false
- SOPS installation: false
- age installation and key generation: false
- Secret provisioning/materialization: false
- Runtime inspection and activation: false

SM-01B overall delivery is not complete.

## SM-01A validation record

- Focused final validation: `111 passed, 9 warnings`
- Canonical regression: `3179 passed, 5 deselected, 447 warnings`, `RC=0`,
  executed exactly once on final code
- Implementation commit: `ffdf034ed9e1587328b6ecad35a6fcbe1381d8b0`
- Production mutation: false
- Secret values read: false
- Keychain query: false
- Secret backend/materialization: false
- Notion synchronization: false
