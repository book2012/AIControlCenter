# MASTER

## MariaDB Continuity Phase B1 — IMPLEMENTATION AND VALIDATION COMPLETE

Implementation commit: `acdbd859872b842691c293b5e094472b344d304b`.

The factual one-shot state model is `NEW -> AUTHORIZED -> CONSUMED ->
PRE_ATTEMPT -> ATTEMPT_INITIATED -> TERMINAL`. `PRE_ATTEMPT -> TERMINAL` keeps
`attempted_count=0`; `ATTEMPT_INITIATED -> TERMINAL` keeps
`attempted_count=1`. No skip, reversal, repetition, post-terminal transition,
or second attempt is allowed. `AUTHORIZED` is factual and grants no authority.

The frozen value-free sources are exactly `CREDENTIAL_SOURCE`,
`EXPECTED_IDENTITY_DESCRIPTOR`, `DATA_IDENTITY_BASELINE`, and
`DATA_CONTINUITY_BASELINE`. Their current availability remains false:
`credential_material_available=false`,
`expected_identity_descriptor_available=false`,
`data_identity_baseline_available=false`, and
`data_continuity_baseline_available=false`. Public construction rejects
unsupported positive and contradictory source facts.

Credential custody remains Mac-Control-Plane-owned through one external fixed
slot outside Git, a `0700` protected parent, a `0600` regular non-symlink file,
and explicit trusted uid/gid. There is no ambient `HOME`/UID authority,
env/argv/JSON secret/Governance transport, secret logging/hash, fallback,
enumeration, or candidate iteration. Acquisition is at most once and only
after capability consumption. No actual credential was verified or read.

Target `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE` is owned by
`MAC_CONTROL_PLANE`. `canonical_target_contract_defined=true`,
`numeric_loopback_port_assigned=false`, `target_deployed=false`, and
`production_target_ready=false`; readiness derives strictly from numeric port
assignment AND deployment. Callers provide no host, port, DSN, URL, database,
or username, and Phase B1 assigns no numeric MariaDB port.

No PyMySQL, MariaDB driver, SQL, network, filesystem credential-source
implementation, env/argv credential transport, retry, reconnect, pooling,
Production access, or MariaDB authentication was added or performed.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
`PRODUCTION_ACCESS_GATE=NOT_PERFORMED`;
`MARIADB_AUTHENTICATION=NOT_PERFORMED`; runtime, Docker, Colima, and Notion
access were `NOT_PERFORMED`; secret values read `NO`; PyMySQL installed `NO`;
requirements changed `NO`.

`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact six unchanged actions
are `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains a target only. Mac AIControlCenter is the
sole Control Plane; Ubuntu remains a stateless infrastructure worker.

Validation history: initial focused `22 passed in 0.07s`; first architecture
review `BLOCKED` for public factual forgeability, contradiction handling, and
associated test coverage; correction `PASS`; corrected focused `37 passed in
0.06s`; final read-only architecture review `PASS`. Canonical executed exactly
once after final reviewed code/test state: `3593 passed, 5 deselected, 447
warnings in 133.58s`, `RC=0`. Canonical rerun after commit: `NOT_RUN`.

Phase B2 remains future work only and may cover PyMySQL selection/pinning, a
synchronous one-shot Mac adapter, fixed loopback resolution, a protected
credential reader, independent expected DB/account/grants and identity/
continuity baseline readers, and fixed parameterized read-only SQL using one
connection with no retry, reconnect, or pooling. It is not implemented or
Production-ready, and no new numeric milestone identifier is asserted.

## MariaDB Continuity Validation Prerequisite / Phase A — CLOSED

Repository-complete after documentation closeout. Implementation commit:
`ccf3ce00f7f6602d2cc6a84ec5632c7088cae418`.

The closed Phase A scope is value-free prerequisite/readiness facts and a Mac
Control Plane process-local composition boundary. The non-serializable one-shot
`HumanPresenceGrant` prohibits direct construction, permits only private inert
Phase-A test issuance, binds the canonical request, enforces concurrent
exactly-once use, consumes before assembly and permanently after assembly
failure, redacts exceptions, and invokes no capability during composition.

This is not Production validation readiness. No driver, Production credential
source/material verification, SQL, connectivity, canonical target,
identity/continuity baseline, real Production capability/authentication,
consumer compatibility validation, mutation authority, or activation exists.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`;
historical MariaDB credential continuity remains unresolved.

`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six Shopping secret
provisioning actions remain unchanged. Mac AIControlCenter remains the sole
Control Plane and Ubuntu remains a stateless infrastructure worker.

Validation evidence: focused `13 passed in 0.07s`; final architecture review
`PASS`; canonical `3556 passed, 5 deselected, 447 warnings`, `RC=0`, executed
exactly once on the final reviewed implementation tree; canonical rerun after
commit `NOT_RUN`. Production access and MariaDB authentication were
`NOT_PERFORMED`; runtime, Docker, Colima, and Notion were `NOT_PERFORMED`;
secret values read `NO`.

## SM-01B-02D-06 — MariaDB Historical Credential Continuity Validation Boundary v1 — CLOSED

Implementation commit `3c93ad39586080db618ee090a7548806c024c44a` closes the
Mac mini M4 AIControlCenter-owned, value-free, read-only validation boundary.
It is not a Production mutation boundary or `ControlledExecutionPort`, uses no
`GovernanceMutationBudget`, and its factual result/evidence grants zero
mutation, authorization, execution, retry, or rollback authority.

Exact outcomes are `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`,
`MALFORMED`, `UNCERTAIN`. `VALIDATED` requires `attempted_count=1` and distinct
`CONFIRMED` observations of credential acceptance, expected database and
account identities, required grants, data identity, and data continuity;
authentication alone is insufficient. Consumer compatibility is
`NOT_EVALUATED`; `UNCERTAIN` fails closed. No retry, fallback credential,
candidate iteration, guessing, rollback, or compensation exists.

The future Production capability is externally supplied, non-factual,
non-serializable authority metadata, absent from request/result/projection, not
minted by core, and invocable at most once per application validation
invocation. 06 provides no real MariaDB client or Production capability. It
changes neither authorization consumption/durable SQLite, Governance execution,
SEC-02/postconditions/audit/evidence, coordinator, config, schemas, nor 05
`ContinuityDecision`; the exact six Shopping provisioning actions remain and
`SHOPPING_SECRET_PROVISIONING` remains only their target.

No Production authentication or historical-credential validation occurred;
continuity remains `UNRESOLVED`. No `RECOVER` confirmation, `ROTATE`, `REPLACE`,
DB/account/grant/payload mutation, materialization, DB-client/runtime cutover,
old-account retirement, or activation occurred;
`SHOPPING_RUNTIME_ACTIVATED=false`. Phase B architecture discovery is the next
development boundary and must precede any separately explicitly
human-authorized Production validation. 06 grants no authorization for such an
operation.

Focused: `33 passed in 0.08s`. Architecture review: `PASS`, all severities
`NONE`. Canonical was accidentally executed twice on the same unchanged
final-reviewed implementation tree; each run reported `3543 passed`, `5
deselected`, `447 warnings`, `RC=0`. The duplicate run is an operational
process deviation, not a code or architecture failure, with no code/test change
between runs. Push `PASS`; final Git clean, divergence `0 0`. Production access,
runtime inspection, Docker, Colima, and Notion sync: `NOT_PERFORMED`; secret
values read: `NO`. Mac mini M4 remains sole Control Plane and Ubuntu stateless;
no authority is delegated to WordPress, WooCommerce, n8n, Ubuntu, MariaDB, or
external custody systems.

## SM-01B-02D-05 — MariaDB Credential Continuity Decision Model v1 — CLOSED

Implementation commit `9f168cc475345e7d2c949f375ef5c44f2ad2fda9` closes the
fail-closed public factual `ContinuityDecision` model. Exact states:
`UNRESOLVED`, `STRATEGY_DECLARED`, `VALIDATION_REQUIRED`, `RESOLVED`. Exact
strategies: `RECOVER`, `ROTATE`, `REPLACE`. `RESOLVED`, strategy selection, and
caller-supplied `validation_confirmed` grant zero authority. Trustworthy
Production acquisition of that confirmation is a future separately bounded
validation concern. `mutation_authority=false`; `capability_id=null`.

No credential or secret value is stored or transported. No password, username,
secret-derived hash/digest, private identity, recipient value, arbitrary path,
environment value, stdout/stderr, command, argv, executable, callback, port,
authorization, mutation budget, execution request, or execution receipt was
introduced. The six provisioning actions remain exactly the two tool ensures,
Control Plane identity creation, two recipient registration/validation actions,
and offline-recovery intake; `SHOPPING_SECRET_PROVISIONING` remains a target
identifier and is not a seventh action.

There is no change to `AuthorizationConsumptionPort`, durable SQLite
authorization consumption, mutation budgets, `ControlledExecutionPort`, SEC-02
or postcondition semantics, Governance audit/evidence,
`ShoppingProvisioningGovernanceCoordinator`, `secret_provisioning_adapters.py`,
config, schema, or inspectors. No Production credential validation,
`MARIADB_CREDENTIAL_ROTATE`, `MARIADB_CREDENTIAL_REPLACE`, recovery, rotation,
replacement, DB secret payload/materialization, DB-dependent validation,
WordPress/WooCommerce DB cutover, runtime cutover, or activation was
implemented or claimed. Historical credentials were not claimed recovered,
validated, rotated, replaced, materialized, or activated.

Mac mini M4 AIControlCenter remains the sole Control Plane; Ubuntu remains a
stateless infrastructure worker. No authority is delegated to WordPress,
WooCommerce, n8n, Ubuntu, or external recovery custody systems. Focused:
`39 passed in 0.04s`. Canonical: `3510 passed`, `5 deselected`, `447 warnings`,
`RC=0`. Architecture review: `PASS`; `CRITICAL=NONE`, `HIGH=NONE`,
`MEDIUM=NONE`, `LOW=NONE`. Implementation push: `PASS`. Production access:
`NOT_PERFORMED`. Notion sync: `NOT_PERFORMED`.

## SM-01B-02D-04B — Provisioning Runtime Composition & Read-Only Postconditions v1 — CLOSED

Commit `a4cb53d5398dffdc33366ac042fdb7813f6d4577` adds Mac-Control-Plane-owned,
JSON-first deterministic, read-only, structural and value-free readiness
composition; Ubuntu remains stateless. Readiness is closed to `READY`,
`MISSING`, `BLOCKED`, `UNSAFE`, `MALFORMED`, with false/false -> `MISSING`,
true/false -> `BLOCKED`, true/true -> `READY`, and contradictory false/true ->
fail-closed `MALFORMED` for payload/runtime dependencies. Malformed blocks
readiness and activation.

Six actions, separate offline intake/registration, Governance authorization,
durable consumption, and `ControlledExecutionPort` remain unchanged. No
mutation API, payload, materialization, or cutover occurred;
`materialization_implemented=false`, `SHOPPING_RUNTIME_ACTIVATED=false`.
Unresolved MariaDB continuity blocks DB readiness/materialization, validation,
DB cutover and activation. No recovery/replacement is claimed; dedicated
Shopping materialization architecture is future work.

Focused `47 passed`; canonical `3471 passed, 5 deselected, 447 warnings` in
approximately `133.97s`, `CANONICAL_RC=0`, `CANONICAL_GATE=PASS`; implementation
push, clean, divergence `0 0`, closeout PASS. Production access and Notion sync
were not performed; canonical was not rerun for docs closeout.

## SM-01B-02D-04A — Governed Offline Public Recipient Intake v1 — IMPLEMENTATION VALIDATED

Implementation commit `6e1aa0135b652b199f05a4911c0f45817a8529f4` is
validated and Git-closed; documentation closeout is complete, so 04A is CLOSED. The sixth exact action is
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`. It moves only one typed,
already-public age recipient into the fixed, no-clobber Mac Control Plane inbox
under descriptor/inode-bound filesystem checks. The private recovery identity
remains external.

Intake and the existing
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE` action are
separate Production mutations. Each requires a fresh human authorization,
budget, execution request, and durable consumption record. Mac AIControlCenter
remains the sole Control Plane and Governance authority; Ubuntu remains a
stateless worker with no AI workload, business logic, or Governance state.
`SM-01B-02D-03` remains CLOSED and its durable port, SQLite adapter/path
policy, and semantics are unchanged;
`CORE_GOVERNANCE_SEMANTICS_CHANGE_REQUIRED=false`.

Validation: focused `163 passed`; canonical `3457 passed, 5 deselected, 447
warnings in 133.23s`, `RC=0`; implementation closeout PASS, clean, divergence
`0 0`. No Production mutation or recipient intake occurred. Historical
MariaDB credential continuity remains unresolved and still blocks DB-secret
payload/materialization, database validation, DB/runtime cutover, and
`SHOPPING_RUNTIME_ACTIVATED`. 04B is CLOSED. The next Production milestone remains
`SHOPPING_RUNTIME_ACTIVATED`; Notion is deferred until then.

## SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store v1 — VALIDATED

`SM_01B_02D_03_DURABLE_AUTHORIZATION_CONSUMPTION_VALIDATED=true` at commit
`681a9e342fde47c7bcb9d3aa2d497b737a19e052`; implementation Git closeout PASS,
pushed, upstream divergence `0 0`. This generic Governance implementation is
owned by the Mac AIControlCenter Control Plane, not Shopping or Ubuntu;
`AuthorizationConsumptionPort` is unchanged and
`CORE_SEMANTICS_CHANGE_REQUIRED=false`.

Governance-owned SQLite state is external to Git/source at
`~/Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3`.
Ownership is validated; the shared parent is unchanged rather than forced to
`0700`; Governance is `0700` and the database `0600`. `DURABLY_CLAIMED` precedes
an atomic final authorization/budget `CONSUMED`, zero
invocation/completed/uncertain accounting, and `COMMITTED` receipt. All
protected identities use value-free canonical binding/integrity digests; no
secret values persist.

Fresh replay after `COMMITTED` never returns historical results and fails
closed, as does a stranded claim. No claim stealing, lease, expiry, automatic
recovery, retry, rollback, or compensation exists. Only the same invocation
with ambiguous final commit acknowledgement may reconcile against the exact
expected validated `COMMITTED` record. Evidence and remaining budget grant no
execution/retry authority: recollect/recompare read-only preconditions, rerun
SEC-02, and require `ALLOW_SINGLE_INVOCATION` before `ControlledExecutionPort`.
Replay cannot resurrect invocation authority.

Focused `372 passed`; corrected-tree canonical `3433 passed, 5 deselected, 447
warnings in 135.93s`, `RC=0`, exactly once after final fixture correction.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, `NOTION_SYNC=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`.

SM-01B remains incomplete with no Production provisioning. SOPS/age, control-plane
identity, recipients, payload/materialization, and activation are outstanding.
MariaDB credential continuity remains unresolved; SOPS+age cannot recover it.
Offline-recovery private identity remains outside the Production Mac; only
public recipient metadata may enter, and its operational intake requires
explicit governance. Notion remains deferred until
`SHOPPING_RUNTIME_ACTIVATED`.

## SM-01B-02D-02B — Shopping Secret Provisioning Capabilities v1 — VALIDATED

Milestone identifier:
`SM_01B_02D_02B_SECRET_PROVISIONING_CAPABILITIES_VALIDATED=true`.
Implementation commit: `bffe28a153eb83d3c61e04d38f2ab96892a6feb5`.

Five narrow Shopping secret provisioning capabilities are validated with
explicit `expected_uid` injection and no ambient UID/HOME authority. Execution
is constrained to a fixed trusted Homebrew executable boundary; no generic
shell/argv execution API is exposed. No-overwrite/no-clobber behavior is
enforced, mutation uncertainty fails closed, and no automatic retry, rollback,
or compensation exists. Python does not read the private control-plane age
identity for recipient derivation. Offline recovery remains
public-recipient-metadata only, and the value-free evidence contract remains
intact.

Focused validation recorded `421 passed`. Canonical regression recorded `3387
passed, 5 deselected, 447 warnings in 132.49s`, `RC=0`, with canonical execution
count exactly `1`. Git closeout: PASS. Upstream divergence: `0 0`.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, and `NOTION_SYNC=false`.

Actual SOPS/age installation, age identity creation, recipient registration,
secret materialization, and runtime activation have not occurred. Historical
MariaDB credential continuity remains explicitly unresolved.
`SHOPPING_RUNTIME_ACTIVATED` remains the future Production milestone. Notion
remains deferred until after Runtime Activation. Next engineering recommendation:
`SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store v1` —
generic Governance-owned, Mac Control Plane only, replay-safe and durable, with
no Shopping business logic.

## SM-01B-02D-01B — Shopping Provisioning Governance Coordinator v1 — VALIDATED

Milestone identifier:
`SM_01B_02D_01B_SHOPPING_PROVISIONING_GOVERNANCE_COORDINATOR_VALIDATED`.
Implementation commit: `8229288d68d46383082cec48ffc726bd0dbee09a`.

The coordinator enforces planner -> explicit human-authorized lifecycle ->
read-only precondition -> SEC-02 `ALLOW_AUTHORIZATION_CONSUMPTION` ->
`AuthorizationConsumptionPort.consume_once` -> fresh read-only precondition ->
SEC-02 `ALLOW_SINGLE_INVOCATION` -> exactly one of five bounded
`ControlledExecutionPort` adapters -> read-only postcondition -> closeout or
stop. Consumption evidence grants no execution authority. `READY`, `BLOCKED`,
or `MALFORMED` causes zero consumption and zero invocation. Post-consumption
drift stops with consumed authorization and zero invocation. `FAILED` or
`UNCERTAIN` stops after one attempt. There is no automatic retry, rollback, or
compensation.

Focused validation recorded `181 passed`. Canonical regression recorded `3349
passed, 5 deselected, 447 warnings`, `RC=0`, with canonical execution count
exactly `1`. This validation activity recorded `PRODUCTION_MUTATION=false`,
`AUTHORIZATION_CONSUMED=false`, `SECRET_VALUES_READ=false`,
`RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`, `COLIMA_ACCESS=false`,
`MATERIALIZATION_IMPLEMENTED=false`, and `NOTION_SYNC=false`. Historical
MariaDB credential continuity remains unresolved; `SHOPPING_RUNTIME_ACTIVATED`
remains the Production milestone.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
worker. Core has no dependency on `ops.macos`, and no generic shell or argv
execution API exists. Next engineering milestone:
`SM-01B-02D-02 — Concrete Provisioning Capabilities v1`.

## SM-01B-02C — Bounded Mutation Adapters v1 — CLOSED

Milestone `SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED` is complete at
implementation commit `5a811cb1f9c782acb4f3e537596fb47ae0c599ff`.
SM-01B-02C implements bounded mutation adapter code only for the exact
`SHOPPING_SECRET_PROVISIONING` target and five exact actions:
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`.

The adapters reuse SEC-02 `ControlledExecutionPort`, accept only the exact
target/action, invoke at most one narrow injected capability, issue or consume
no authorization, and perform no retry, rollback, or compensation. Their
value-free `GovernanceExecutionReceipt` evidence uses a deterministic,
injective receipt-identity namespace over the full `execution_request_id`.
Offline-recovery private custody remains external. No generic
shell/argv/package-manager execution framework or parallel governance
framework exists.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker with no Shopping secret ownership. Historical MariaDB
credential continuity remains unresolved; SM-01B-02C does not recover, rotate,
replace, derive, invent, or validate historical credentials.

Production truth remains `production_status=NOT_DEPLOYED`;
`materialization_implemented=false`; `SOPS_INSTALLATION=false`;
`AGE_INSTALLATION=false`; `AGE_KEY_GENERATION=false`;
`OFFLINE_RECOVERY_KEY_GENERATION=false`; `SECRET_PAYLOAD_CREATION=false`;
`SECRET_MATERIALIZATION=false`; `AUTHORIZATION_CONSUMED=false`;
`RUNTIME_INSPECTION=false`; `PRODUCTION_MUTATION=false`;
`SHOPPING_RUNTIME_ACTIVATED=false`.

Final evidence: focused `128 passed`; canonical `3288 passed, 5 deselected,
447 warnings`, `RC=0`, executed exactly once on final implementation code.
Exact three-file implementation scope, post-canonical scope, staged scope,
staged diff check, commit, push, and upstream alignment `0 0` all passed. Next
development milestone is `SM-01B-02D — Authorized Toolchain & Identity
Provisioning v1`. Adapter implementation is not authorization to execute
adapters. Each future Production mutation requires separate human
authorization immediately before exactly one bounded invocation, with no
automatic retry or rollback. SM-01B overall remains incomplete.

## SM-01B-02B — Provisioning Planner v1 — CLOSED

Milestone `SM_01B_02B_PROVISIONING_PLANNER_VALIDATED` is complete at
implementation commit `2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`. The
canonical provisioning definition and Draft 2020-12 schema define exactly five
typed actions. Core `ProvisioningPlan` is vendor-neutral and value-free.
Malformed input produces only sanitized `UNKNOWN_ACTION` or
`MALFORMED_CONFIGURATION` evidence. The read-only macOS provisioning inspector
performs planning only. Core imports from `ops` and `integrations` remain zero.
Future execution must reuse SEC-02 `ControlledExecutionPort` and must not
create a parallel governance framework.

Mac AIControlCenter remains the sole Control Plane; Ubuntu is a stateless
worker with no Shopping secret ownership. Offline-recovery custody stays
external. Historical MariaDB credential continuity is unresolved, and this
milestone does not recover, replace, rotate, or invent historical credentials.
Production truth is `NOT_DEPLOYED`; `materialization_implemented=false`;
`SOPS_INSTALLATION=false`; `AGE_INSTALLATION=false`;
`AGE_KEY_GENERATION=false`; `OFFLINE_RECOVERY_KEY_GENERATION=false`;
`SECRET_PAYLOAD_CREATION=false`; `SECRET_MATERIALIZATION=false`;
`AUTHORIZATION_CONSUMED=false`; `RUNTIME_INSPECTION=false`;
`PRODUCTION_MUTATION=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.

Final implementation evidence: focused `73 passed`; canonical `3236 passed,
5 deselected, 447 warnings`, `RC=0`, executed exactly once on final
implementation code. Exact six-file implementation scope, post-canonical
scope, staged scope, staged diff check, commit, push, and upstream alignment
all passed. Next development milestone is `SM-01B-02C — Bounded Mutation
Adapters v1`; implementation is not authorization to execute adapters. SM-01B
overall remains incomplete.

## SM-01B-01 — SOPS/age Secret Backend Inspection v1 — CLOSED

Implementation and validation are complete at
`SM_01B_01_SECRET_BACKEND_INSPECTION_VALIDATED`, implementation commit
`1ada572a75cf4313f65288e81134777948900cda`. SOPS+age is the selected
replaceable architecture, but is `NOT_DEPLOYED`. The canonical definition and
schema, vendor-neutral core port, and macOS metadata-only outer adapter preserve
zero core imports from `ops` and `integrations`.

The Mac remains sole Control Plane; Ubuntu remains stateless and owns no
Shopping secrets. Identity custody is portable through injected
`control_plane_home` and `.config/sops/age/keys.txt`. The adapter performs only
`lstat` metadata inspection, never content reads or discovery through HOME,
environment, pwd, Keychain, runtime, Docker, Colima, or network. The logical
encrypted payload is `deploy/shopping/secrets/shopping.enc.yaml`; policy
requires `control-plane` and `offline-recovery` roles without storing recipient
material.

SOPS/age installation, key generation, encrypted payload provisioning,
materialization, Production mutation, runtime inspection, secret-value reads,
and Keychain queries did not occur. `materialization_implemented=false` and
`SHOPPING_RUNTIME_ACTIVATED=false`. Historical MariaDB credential continuity
remains unresolved and runtime cutover is blocked on an explicit
continuity/recovery/rotation strategy. Next is `SM-01B-02 — SOPS/age Toolchain
& Identity Provisioning`; SM-01B overall is not complete. Any future mutating
provisioning requires fresh human authorization immediately before one bounded
invocation, with no automatic retry or rollback.

## SM-01A — Shopping Secret Contract & Fail-Closed Preflight v1 — CLOSED

SM-01A implementation and validation are complete. The canonical, value-free
metadata authority is `deploy/shopping/config/secret-contract.json`.
`ops/macos/shopping/secret_preflight.py` is a read-only consumer and validator;
it does not duplicate the exact canonical key table. It validates structure,
resolves action-specific required names, and performs presence-only evaluation.
Unsupported actions, unknown supplied names, missing required names, and
invalid structure fail closed; not-evaluated is distinct from pass/fail.

Only layers 1 (Secret Contract) and 2 (Secret Preflight) exist. Layer 3
(Secret Backend), layer 4 (Secret Materialization), and layer 5
(Authorization / Mutation) are not implemented by SM-01A. No SOPS, age, or
Keychain backend is selected as deployed truth. The preflight performs no
authorization, mutation, secret read, Keychain query, runtime access, or
materialization. Compose remains plain `${SHOPPING_*}` interpolation, keeping
read-only monitoring independent of secret material.

AIControlCenter on the Mac remains the sole Control Plane; Ubuntu remains a
stateless infrastructure worker with no secret ownership. Shopping service and
WooCommerce capability remain `NOT_DEPLOYED`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. No Production port cutover, activation, or
new Production authorization occurred. Next:
`SM-01B — Secret Delivery Backend v1`; it must retain replaceable backends,
value-free monitoring/preflight, Mac Control Plane ownership, no Ubuntu secret
ownership, and one exact human authorization immediately before each bounded
Production mutation invocation, without automatic retry or rollback.

## PA-04 — Notification Platform v1 — CLOSED

Milestone after Git closeout: `NOTIFICATION_PLATFORM_V1_VALIDATED`.

AIControlCenter owns notification intent, routing policy, provider selection,
governance, authorization, audit, retry policy, and the future delivery
lifecycle; external providers own transport capability only. n8n, OpenClaw,
WordPress, providers, and Ubuntu own no platform-wide notification business
logic or Production authorization. `core.notifications` is provider-neutral,
`integrations.notifications` holds replaceable observation-only adapters, and
`ops.macos.runtime.application` is outer composition. Core imports neither
`ops.*` nor `integrations.*`; both verified counts are zero.

Provider and routing statuses are separate. Provider observations fail closed,
and only explicitly `AVAILABLE`, configured, and available providers route.
Malformed, contradictory, exceptional, mismatched, duplicate, or invalid
providers do not. Identities match `^[a-z0-9][a-z0-9._-]{0,63}$`; invalid values
are never echoed and normalize to literal `UNKNOWN`. Telegram is the known
optional, `NOT_DEPLOYED` reference provider; configuration/readiness are
unknown absent explicit evidence, and no runtime/network convention is inferred.
V1 has no delivery lifecycle because execution is not implemented.

`core.capabilities.manifest` now provides narrow, fail-closed, schema-validated
canonical service metadata lookup for exactly one requested identity. OpenClaw
and n8n reuse it with unchanged outward behavior; it is not another topology or
lifecycle framework.

The exact new API consists of `GET /api/notifications/platform` and
`GET /api/notifications/providers`, with no action, send, retry, execution,
Production authorization, or infrastructure operation. Existing GET/POST
`/notifications` remains unchanged, **LEGACY / OUTSIDE PA-04 SCOPE**, and
independent of PA-04. Its migration/deprecation is separately governed future
work.

Final exact-code focused validation passed 85 tests after identity hardening;
one canonical PA-04 regression invocation passed with `RC=0`; and `git diff
--check` passed. No Production mutation, notification, external provider I/O,
or PA-04 execution occurred. Legacy POST ran only in TestClient compatibility
tests. No launchd, Docker, `runtime/current`, credential, Caddy, WordPress,
Ubuntu, or live-provider mutation occurred. No Notion synchronization is
claimed. OPS-01B and PA-01 through PA-03 remain closed and unchanged.

## PA-03 — n8n Control Plane Adapter v1 — CLOSED

Milestone after Git closeout: `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`.

n8n is a replaceable external automation capability, not the AIControlCenter
Control Plane. AIControlCenter retains business logic, workflow and
orchestration policy, Production authorization, governance, audit, deployment
control, infrastructure mutation authority, and business/customer state.

The final dependency direction is `ops.macos.runtime.application` →
`integrations.n8n` → `core.capabilities`, with dependency injection into
`core.api.create_app`; core imports neither `ops.*` nor `integrations.*`.
Existing `core.capabilities` contracts and `CapabilityStatusService` are reused;
no second capability framework exists. Platform-neutral `create_app` performs
no n8n discovery and fails closed with value-free `UNAVAILABLE` evidence when
no adapter is injected. macOS outer application composition injects the n8n
adapter and truthfully projects `NOT_DEPLOYED`.

Canonical manifest/schema validation precedes trust in the unique n8n identity.
Its current canonical truth is optional, `NOT_DEPLOYED`,
`runtime_health=false`, `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`. No
sufficiently proven executable, lifecycle, log, or runtime identity exists, so
no PA-01 `service_platform` lifecycle definition was added. Configuration,
authentication, runtime, and transport remain `UNKNOWN` unless explicitly
injected as evidence. No invented n8n endpoint, environment, or authentication
convention is used by the implementation.

The sole PA-03 v1 API projection is `GET /api/capabilities/n8n`. There is no
POST/PUT/PATCH/DELETE capability implementation, workflow execution, workflow
enable/disable, webhook creation, credential creation, schedule mutation,
Production authorization, or infrastructure mutation. Secret/config evidence
is value-free: URLs, API keys, tokens, cookies, headers, webhook secrets,
environment values, configuration contents, and exception messages are not
projected. Shared governance explicitly states
`platform_business_policy_ownership=false` for external capabilities; PA-02
OpenClaw remains compatible.

Focused PA-03 validation passed 96 tests. Canonical deployment regression
passed with `RC=0` on exactly one PA-03 canonical invocation, and
`git diff --check` passed. No Production mutation or n8n workflow, credential,
Docker, launchd, `runtime/current`, or live-service operation occurred. No
Notion synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
unchanged.

## PA-02 — OpenClaw Adapter v1 — CLOSED

Milestone after Git closeout: `OPENCLAW_ADAPTER_V1_VALIDATED`.

OpenClaw is isolated in `integrations.openclaw` behind the vendor-neutral
`core.capabilities.CapabilityObserver` port and an AIControlCenter-owned status
facade. Its projection is GET-only at `/api/capabilities/openclaw`, JSON
compatible, value-free for configuration/authentication evidence, and
fail-closed across unavailable, malformed, timeout, connection, and
indeterminate states.

The canonical service manifest already identifies OpenClaw as optional,
`NOT_DEPLOYED`, and outside Runtime Health. Local read-only discovery found no
executable, named application/config path, or launchd identity. Therefore no
PA-01 Service Platform lifecycle contract was added and optional absence does
not affect aggregate health. The adapter owns no business policy, Production
authorization, deployment governance, infrastructure mutation, customer state,
prompt forwarding, or tool/action execution.

The final dependency direction is `ops.macos.runtime.application` →
`integrations.openclaw` → `core.capabilities`, with injection into
`core.api.create_app`; core imports neither `ops.*` nor `integrations.*`.
Platform-neutral `create_app` performs no OpenClaw discovery and fails closed
with value-free `UNAVAILABLE` evidence without an injected adapter. macOS outer
composition injects the adapter and projects `NOT_DEPLOYED` from the
schema-validated unique manifest entry.

Endpoint, authentication, transport, and runtime identity remain
`UNKNOWN`/unproven by default. No `OPENCLAW_ENDPOINT` or `OPENCLAW_API_KEY`
convention is used. The only API surface is GET-only; no mutating capability
implementation or execution authority exists, and no secret/config value or
exception message is projected.

Focused PA-02 validation passed 79 tests. Canonical deployment regression
passed with `RC=0` on exactly one PA-02 canonical invocation, and
`git diff --check` passed. No Production mutation or additional deployment,
`launchctl`, `runtime/current`, credential, or live-service operation occurred.
No Notion synchronization is claimed. PA-01 and OPS-01B remain closed and
unchanged; WordPress and unrelated Shadow maintenance remain separate future
work.

## PA-01 — Control Plane Service Platform v1 — CLOSED

Milestone after Git closeout: `CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`.

The canonical service manifest is the service-definition source of truth.
`ServiceDefinition` is a pure core service-level contract, `ServiceHealth`
remains sole owner of aggregate runtime health, and `core` has zero direct
`ops.*` imports. macOS outer composition is
`ops/macos/runtime/service_platform.py`; `inspect_platform_services()` composes
`ServiceTopology.platform_services()`, existing `ServiceHealth` launchd and
heartbeat observation, strict filesystem readiness, and immutable
runtime/source validation.

Stable filesystem owner/group names resolve only at the macOS boundary. Exact
file type, symlink, mode, owner, and group validation is fail-closed. Only
`ENOENT` is missing; other filesystem/identity inspection errors fail closed
with value-free evidence. Canonical immutable `runtime/current` and Source
validation reuses the authoritative immutable-source validator and does not
execute Production worktree code.

Lifecycle remains inspect-only. Dry-run may describe bootstrap planning only
for `NOT_DEPLOYED` with trusted launchd observation, ready filesystem, and
immutable runtime/source preconditions. It has no authorization and performs no
mutation, retry, rollback, or kickstart. Application Scheduler and canonical
API were reference services only; validated Production lifecycle behavior did
not change. The API entrypoint remains `ops.macos.runtime.application:app`, and
Shadow remains separate.

Final evidence: 94 focused tests passed under umask `077`; exactly one canonical
deployment-regression invocation for the final candidate passed with `RC=0`;
`git diff --check` passed; Production mutation was zero. No Notion
synchronization is claimed. WordPress and Shadow maintenance remains deferred
and separate.

## Authoritative Production checkpoint — 2026-08-13

Status: `CANONICAL_API_HOMEPAGE_RECOVERY_COMPLETE`.

- Full commit: `ef07532bd3d7ba91868d46375d48cac4821d6a56`
- Runtime ID: `ef07532bd3d7`
- Active Runtime: `runtime/venvs/ef07532bd3d7`
- Immutable Source: `runtime/sources/ef07532bd3d7`
- Source content SHA-256:
  `2357749d768dfd8391a582669ae6b87b1f8e1c17cf477f5c505f47e051b15ce6`
- Source archive SHA-256:
  `b6cc292b95cc1327d35fcba0874bb7822f199ac15cf295226f7573bac3dcadbe`
- Source Git tree: `2b157f1391cf34dd72c21cce6d5c82c212730bfd`
- Immutable writable objects: `0`
- Python bytecode contamination: absent before and after service starts
- ProductDraft main DB SHA-256 unchanged:
  `761d07099f051e2d1c934fce63fc66aee47bb052bf49138c220418c06ab604c4`

Runtime/Source commit identity matches exactly. Runtime and Source were each
built exactly once; dependency installation, application import, test suite,
and independent Source validation passed. `runtime/current` moved exactly once
from `9a7216a75323` to `ef07532bd3d7`; shadow reconciled exactly once and runs
from the new Source (PID `37951`). Canonical runner and plist were byte-exact
with Source and retained required metadata (`root:wheel 0755` and
`root:wheel 0644` respectively), `RunAtLoad=true`, and `KeepAlive=false`.

One separately human-authorized canonical kickstart recovered the registered,
not-running service from its prior exit `3`. Canonical now runs from the new
Source (PID `38153`), launchd state is `running`, and runs is `2`. Shadow and
canonical both return `200` for `GET /health` and `405` for `POST /health`.
Public ingress is operational: DNS resolved to `222.111.236.227`, HTTP root
returned `308`, and HTTPS `/health` and `/homepage/product-management`
returned `200`. A later duplicate wrapper request was rejected by failed-state
preflight before authorization or mutation; second canonical kickstart is
`false`.

This checkpoint does **not** declare the whole Runtime healthy.
`GET /runtime/health` returns HTTP `200` but reports `healthy=false`;
`services.api`, `services.telegram`, and `services.scheduler` are
`unavailable`; `scheduler_heartbeat.status=STALE` and `fresh=false`. Its latest
heartbeat says `ALIVE` but was created at
`2026-08-05T07:43:56.748515`. Runtime-health reconciliation is the next open
operational debt. No ProductDraft generation, WooCommerce mutation, Ubuntu
change, automatic retry, automatic rollback, or Production mutation occurred
during this documentation closeout.

## SHOP-AI-01A — ProductDraft generation foundation ready

Status: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY`. Verified
implementation HEAD: `52db3600ae76c70926e27ce930be70fe34f98452`. Verified
canonical regression: `2691 passed, 5 deselected, 437 warnings` via
`ops/macos/validation/run-deployment-regression-gate.sh -q`.

`core/shopping/` remains canonical. SHOP-02 `ProductDraft`, its existing
`ProposedFields`, and immutable revision model are reused. Structured generation
contract `1.0.0` records AI `SuggestionProvenance` and prepares a candidate
that remains `LifecycleState.DRAFT`, without automatic validation, human
approval, or deployment intent. The canonical provider boundary is reused with
one injected provider, `RetryPolicy(max_attempts=1)`, bounded timeout, no
fallback, snapshotted source context, and traceable provider request ID.

An operation key is consumed before invocation. Semantics are **AT-MOST-ONE
provider invocation per consumed operation key within the injected
coordinator's durability scope**, with concurrent duplicate suppression—not
global exactly-once. The current in-memory coordinator is non-production. No
durable ProductDraft or operation persistence, transactional Unit of Work,
generation mutation surface, recommendation engine, Commerce integration, or
Production authority exists. Next:
`SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`, beginning with
architecture/discovery of existing durable persistence and transaction
conventions. Ubuntu may own no ProductDraft or AI application state.

## SHOP-01A — Shopping read-only foundation ready

Status: `SHOP-01A_SHOPPING_READ_ONLY_FOUNDATION_READY`. SHOP-01A1 runtime
reconciliation and SHOP-01A2 repository/architecture reconciliation are
complete at the verified SHOP-01A2 baseline HEAD
`55270476e4b4e8d57c041084ff8eafda889c2660`. Canonical regression:
`2670 passed, 5 deselected, 437 warnings` via
`ops/macos/validation/run-deployment-regression-gate.sh -q`.

The Mac mini M4 is the always-on Brain and AIControlCenter is the single
Control Plane, owning Shopping business logic and Governance, authorization,
and orchestration. Ubuntu is a stateless infrastructure Worker only, with no
Shopping business logic, Governance, AI workload, application state, or
Control Plane authority. WordPress is the CMS/presentation boundary and
WooCommerce is the Commerce Engine. `core/shopping/` is the canonical Shopping
domain; the Shopping API is GET-only and runtime composition uses
`build_default_shopping_service()`.

Each WooCommerce read invocation permits exactly one outbound HTTP GET attempt.
There is no automatic retry or rollback. Capabilities remain
`write_catalog=false`, `write_executor_available=false`, and
`production_mutation_authorized=false`. `WooCommerceControlledWriteAdapter`
remains intercepted `ACTIVE_LIBRARY` code and is not Production enabled. No
concrete Production outbound write transport, Production credential provider,
runtime write construction, mutation API endpoint, or Production mutation
authority exists.

Next: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION`, reusing the existing
SHOP-02 `ProductDraft` work without restarting Shopping architecture; the
following milestone is
`SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`.
No Git push or external Notion synchronization is claimed.

## SHOP-01A2 — Repository utilization and architecture reconciliation

Status: `SHOP-01A2_REPOSITORY_UTILIZATION_AND_ARCHITECTURE_RECONCILED` at
SHOP-01A1 HEAD `f95ba9ae2133b55db06c362df321b16785f21423`. The canonical
macOS wrapper regression is `2670 passed, 5 deselected, 437 warnings` via
`ops/macos/validation/run-deployment-regression-gate.sh -q`. Existing
SHOP-01/02/03 chronology is retained; `core/shopping/` remains canonical.
Runtime reads are single-attempt and Production mutation authority is disabled.
The intercepted SHOP-03 adapter is retained as `ACTIVE_LIBRARY`, with no
Production transport, credential provider, runtime/API wiring, or mutation
endpoint. Repository classification and ownership are canonicalized in
`docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md`.
SHOP-01A3 closeout is recorded by the final SHOP-01A state above.

## SEC-02A10 — Architecture closure

Status: `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`. The A0-A10
architecture phase is complete and the A1-A9 canonical evidence chain is
`VALIDATED`. This is reusable Governance Control Plane architecture readiness,
not Production execution or mutation authority. No concrete Production adapter,
Shopping write automation, retry, rollback, or Ubuntu Governance ownership was
introduced. The exact closure invariants and evidence are recorded in
`docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md`.

Canonical full repository regression:
`========= 2667 passed, 5 deselected, 437 warnings in 166.69s (0:02:46) =========`.
Prior focused Governance regression: `265 passed in 1.45s`. Git closeout will
be performed by the external controller. Notion actual external synchronization
has not occurred; documentation payload status is `READY_FOR_FINAL_SYNC`.
Next: `SHOP-01A_SHOPPING_PLATFORM_ARCHITECTURE_AND_READ_ONLY_FOUNDATION`.

## SEC-02A9 — Durable evidence and API projection

Status: `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`. A9 adds pure
immutable storage classification policy and a typed, value-free Governance read model
projected deterministically to the unchanged A6 API envelope. Durable evidence
belongs in an operator-configured external Control Plane data root;
`/private/tmp` is transient only, and repository evidence JSON is
documentation/audit evidence rather than mutable runtime state. No
user-specific data-root path, concrete persistence adapter, writer, HTTP
mutation route, Production mutation API, authorization mutation or
consumption, execution, retry, rollback, or persistence capability was added. Atomic write
publication, restrictive permissions, durable synchronization, manifest
binding, and value-free evidence are required. External validation reported
`265 passed in 1.45s` for the focused Governance regression and validated the
deterministic READ ONLY projection and unchanged `GovernanceApiEnvelope`
compatibility. This was not the full repository regression, and no Production,
provider, or Ubuntu mutation occurred. Next: `SEC-02A10 ARCHITECTURE CLOSURE
REVIEW`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`; architecture-ready is not claimed before A10.

## SEC-02A8 — Orchestration policy and safety tests

Status: `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. A8 is a pure immutable
application policy that inspects A2-A5 facts and returns only the next permitted
disposition. It invokes no port or adapter and performs no consumption,
invocation, retry, rollback, compensation, persistence, or external access.
Authorization consumption is a distinct gate. Current preconditions must
`MATCH` before invocation permission; consumed authorization remains consumed
after later drift, and one permission maps to one bounded invocation.
`FAILED`, `UNCERTAIN`, postcondition `FAIL`, and failure evidence each produce
`STOP`. Remaining mutation count is accounting, not retry authority. There is
no automatic retry, automatic rollback, or compensation authority. External
validation reported `231 passed in 1.42s` for the focused Governance
regression; this was not a full repository regression. No Production, provider,
or Ubuntu mutation and no public mutation API were added. Next:
`SEC-02A9 DURABLE EVIDENCE AND API PROJECTION`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## SEC-02A7 — Adapter ports and compatibility mappings

Status: `SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`.
Governance now owns seven abstract typed port capabilities and a deterministic
immutable catalog
that classifies existing deployment, Runtime, audit, evidence, governance
operations, and Shopping boundaries without importing or invoking them. Every
concrete Production adapter remains absent. Initial external validation was `1
failed, 193 passed in 1.56s`. R1 fixed the Protocol-only interface gate under
`PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT`: the diagnosis identified
test-inspection semantics, not implementation `__init__` semantics. The final
focused Governance regression was `194 passed in 1.53s`; this was not a full
repository regression. Adapters cannot authorize, widen scope or mutation
budget, or decide retry or rollback. Git evidence remains read-only, Runtime
identity observation-only, Governance Operations operational audit/read-model
only, Shopping rules Shopping-owned, and Ubuntu a stateless Worker with zero
Governance authority. Next:
`SEC-02A8 ORCHESTRATION POLICY AND SAFETY TESTS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## SEC-02A6 — JSON Schema registry and contract tests

Status: `SEC-02A6_JSON_SCHEMA_REGISTRY_AND_CONTRACT_TESTS_VALIDATED`. Exactly 16
governance v1 Draft 2020-12 schemas, the deterministic local-only registry, and
valid/invalid fixture contracts were validated by the focused governance
regression: `173 passed in 1.39s`. This was not a full repository regression.
The R1 blocker was
`SEC-02A6-R1_CONTROLLER_REGISTRY_API_ASSUMPTION_DEFECT`: the controller assumed
a public `registry.contract_names()` function although the frozen contract
required behavior, not that exact API name. It was not an A6 contract
implementation defect. The schemas grant no authorization, and validation
involved no Production, provider, or Ubuntu mutation and no execution adapter.
Next: `SEC-02A7 ADAPTER PORTS AND COMPATIBILITY MAPPINGS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## SEC-02A5 — Receipts, failure, and evidence models

Status: `IMPLEMENTED_PENDING_EXTERNAL_TEST_VALIDATION` (pure domain evidence
vocabulary only). Caller-supplied consumption and execution facts,
postcondition decisions, mandatory non-retry/non-rollback failure evidence,
and value-free lifecycle-bound evidence references now have immutable,
deterministic JSON-safe models. Tests were added but not run by Codex. The
target milestone is
`SEC-02A5_RECEIPTS_FAILURE_AND_EVIDENCE_MODELS_VALIDATED`. Next: `SEC-02A6 JSON
SCHEMA REGISTRY AND CONTRACT TESTS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## SEC-02A4 — Mutation budget and invocation accounting

Status: `IMPLEMENTED_PENDING_EXTERNAL_TEST_VALIDATION` (pure domain only).
Immutable explicit action line items now separate authorization consumption
from completed, confirmed-zero-effect, and uncertain invocation accounting.
Remaining count is accounting only and never retry authority. The target
milestone is `SEC-02A4_MUTATION_BUDGET_AND_INVOCATION_ACCOUNTING_VALIDATED`;
tests were added but not run by Codex. Next: `SEC-02A5 RECEIPTS FAILURE AND
EVIDENCE MODELS`. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## AI-PROVIDER-01C-A — Control Plane workflow integration

Status: `READY_FOR_GIT_CLOSEOUT` (repository only). Canonical `BrainAgent.ask`
business logic now invokes the explicitly selected provider through
`ProviderRouter` and receives only normalized `ProviderAdapter` results or safe
errors. There is no vendor SDK ownership in business logic and no automatic
cross-provider fallback. No authenticated call occurred. Production Runtime
remains `7b171f135dc7`; 01C-B creates a new Candidate Runtime and 01C-C requires
explicit human authorization for Production promotion. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`.

## AI-PROVIDER-01B — Authenticated OpenAI transport

Status: `READY_FOR_AUTHENTICATED_SMOKE` (repository only). The Responses API is
implemented behind `ProviderAdapter` with invocation-time external
`OPENAI_API_KEY`, bounded timeout/output, one request, no automatic retry and no
cross-provider fallback. Focused tests are mocked; the human-controlled
authenticated smoke remains pending. Production Runtime `7b171f135dc7` is
untouched. AI-PROVIDER-01C owns candidate Runtime integration/promotion. Notion
is `DEFERRED_UNTIL_FINAL_PHASE`.

## AI-PROVIDER-01A — Provider baseline

Status: `IMPLEMENTED` (repository only). AIControlCenter owns provider
governance, explicit routing, normalization and policy. Replaceable adapters
isolate vendor behavior from business logic. Credentials are external secrets
and API keys never belong in Git. No authenticated provider call occurred;
Production Runtime `7b171f135dc7` and PI-009 authorization remain intact.
AI-PROVIDER-01B secure credential installation and authenticated connectivity
are not started. Notion synchronization is `PENDING`.

<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:START -->
## ACTIVATION-01C Controlled Pointer Activation

Status: `COMPLETE`

Authorized transition:

`b9ad351a7241 -> acd80ab9f6ae`

Runtime pointer activation:

`PASS`

Activation report SHA-256:

`d59a3aa81accca4e6f330c85774924221e33e247376a069a1d922f5716dec24a`

Natural launchd KeepAlive recovery:

`PASS`

Explicit service restart commands:

`0`

Launchd state:

`running`

Listener:

`127.0.0.1:18100`

Listener/PID correlation:

`PASS`

Approved wrapper SHA-256:

`a58d926f8845f6b0aa7863250b02c0c461ea843bfa03a83313eaaa547ca98212`

Wrapper serving target:

`core.api.shadow:app`

HTTP validation:

- `GET /health -> 200`
- `GET /runtime/health -> 200`
- `POST /health -> 405`

Post-activation ACTIVATION-01B inspection ID:

`activation-inspection-bc8f2b34d45242c4b835d4ba852667a3`

Post-activation report digest:

`sha256:f419242b927804a6c97ad947ad4eb2deb9b2a07545724d750fd85ab3a80def22`

01B terminal status:

`BLOCKED`

Remaining transition-phase blockers:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","PROCESS_SERVING_TARGET_MATCH","RUNTIME_CURRENT_MATCH"]`

Operational Runtime, launchd, listener and HTTP checks passed.

The residual blockers are contract-phase mismatches:

- pre-activation Runtime expectation
- Control Plane Git identity versus Candidate source identity
- launchd wrapper indirection versus direct serving-target inference

01C independently verifies the exact approved wrapper SHA and its
static `uvicorn core.api.shadow:app` exec chain.

Rollback executions:

`0`

Explicit launchd mutation commands:

`0`

Caddy changes:

`0`

Public openings:

`0`

Ubuntu changes:

`0`

Production authorization:

`NO`

ACTIVATION-01C does not constitute PI-009 Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:START -->
## ACTIVATION-01C Authorization Contract

Status: `FROZEN`

Active Runtime: `b9ad351a7241`

Candidate Runtime: `acd80ab9f6ae`

Candidate source commit: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Candidate startup import gate: `PASS`

Observed Active Runtime failure:

`ModuleNotFoundError: No module named 'jsonschema'`

First mutation boundary:

`Runtime pointer activation only`

Explicit service restart authority:

`NO`

Automatic rollback authority:

`NO`

Ubuntu changes:

`NO`

Public opening:

`NO`

Production authorization:

`NO`

Canonical human approval statement:

`ACTIVATION-01C AUTHORIZE POINTER SWITCH acd80ab9f6ae FROM b9ad351a7241`

The exact mutation command and rollback boundary are defined in:

- `docs/deployment/ACTIVATION-01C-CONTROLLED-ACTIVATION-ARCHITECTURE.md`
- `docs/operations/macos/ACTIVATION-01C-HUMAN-AUTHORIZATION-CONTRACT.md`
<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:START -->
## ACTIVATION-01B Read-Only Operational Validation

Status: `COMPLETE`

Classification: `PASS / FAIL-CLOSED`

The bounded read-only inspector completed the full Mac control-plane
observation path.

Inspector exit code: `2`

Overall status: `BLOCKED`

Inspection ID: `activation-inspection-7f2591c5066142dfaa383a31ae943f0d`

Report digest: `sha256:5afa71f7bd1edb1111203f0227a1cb3314a306cc1355ec465d33f5d10800e9e4`

Inspector commit: `698f60444894cb4f22c9cbc647abc2ee2a530e59`

Blocking reasons:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","HTTP_GET_HEALTH","HTTP_GET_RUNTIME_HEALTH","HTTP_POST_HEALTH_DENIED","LAUNCHD_RUNNING","LISTENER_COUNT_MATCH","LISTENER_PID_MATCH","PROCESS_SERVING_TARGET_MATCH"]`

Sanitized errors:

`[]`

Operational safety:

- Runtime mutations: `0`
- Service restarts: `0`
- Rollback executions: `0`
- launchd changes: `0`
- Caddy changes: `0`
- Public openings: `0`
- Production writes: `0`
- Ubuntu changes: `0`
- Production authorization: `NO`

`READY_FOR_AUTHORIZATION_REVIEW` is evidence readiness only.

A `BLOCKED` result is a successful fail-closed operational
validation. It does not authorize remediation or Production.

Notion synchronization remains pending as the final
project-management gate.
<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:START -->
## ACTIVATION-01B HTTP Evidence Contract Correction

Status: `COMPLETE`

Operational validation exposed a direct-localhost
`HTTP_PROBE_FAILED` condition.

The registered HTTP evidence contract uses:

- `actual_status`
- `result`
- `body_length`
- `sanitized_error`
- `attempt_count`
- `redirect_followed`

Transport or connection failures are now represented as probe
evidence:

- `actual_status = null`
- `result = ERROR`
- `body_length = 0`
- bounded `sanitized_error`
- `attempt_count = 1`
- `redirect_followed = false`

The corresponding blocking inspection check fails.

A transport failure therefore resolves to `BLOCKED` rather than
being promoted to an inspector execution `ERROR`.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:START -->
## ACTIVATION-01B Launchd Parser Scope Correction

Status: `COMPLETE`

Operational validation discovered that `launchctl print` contains
nested resource and jetsam records whose field names overlap with the
top-level service record.

Observed example:

- service scope: `state = spawn scheduled`
- resource scope: `state = active`
- jetsam scope: `state = active`

The previous parser flattened all scopes and therefore emitted
`LAUNCHD_CONFLICTING_FIELD`.

The corrected parser is brace-depth aware and consumes identity,
state, pid, username and program arguments only from the service
record scope.

Nested launchd metadata is ignored rather than selected
heuristically.

Conflicting values within the service scope still fail closed.

The change affects observation logic only.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:START -->
## ACTIVATION-01B Runtime Layout Correction

Status: `COMPLETE`

Read-only operational validation discovered a Control Plane
observation-path mismatch.

Canonical Runtime layout:

- Runtime environments: `runtime/venvs/<runtime-id>`
- Candidate metadata: `metadata.json`
- Source identity: `.aicontrolcenter-source-commit`

The inspector previously looked under `runtime/releases/<runtime-id>`
and expected `runtime-metadata.json`.

The repair changes observation logic only.

No Runtime environment was created, removed or modified.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C4:START -->
## ACTIVATION-01B-C4 Read-Only Inspector

Status: `COMPLETE`

ACTIVATION-01B read-only inspector implementation is complete.

Implemented capabilities:

- Versioned activation inspection policy
- Versioned localhost route manifest
- Existing bounded Git evidence reuse
- Bounded macOS read-only adapters
- Exact `launchctl print` inspection
- Structured `lsof -F` listener inspection
- Runtime filesystem observation
- Isolated Runtime Python `-I -S --version` probe
- Exact localhost HTTP probes
- Immutable pure evaluator
- Launchd serving-target observation
- Canonical `PROCESS_SERVING_TARGET_MATCH` check
- Actual-evidence report materialization
- Evidence digest regeneration
- Check evidence-reference regeneration
- Canonical report digest generation
- Final report JSON Schema validation
- Deterministic CLI exit codes

Status contract:

- `READY_FOR_AUTHORIZATION_REVIEW` -> exit `0`
- `BLOCKED` -> exit `2`
- Invalid policy, manifest or contract -> exit `3`
- Observation or internal error -> exit `4`

Evidence mismatches remain `BLOCKED`.

No exit code grants Production authorization.

C4 focused integration gate: `43 passed`

Base commit: `9f7d71a08235d23502c72c417a029b480b29a5e8`

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_C4:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C3:START -->
## ACTIVATION-01B-C3 Bounded macOS Read-Only Adapters

Status: `COMPLETE`

Implemented bounded macOS observation adapters for:

- exact `launchctl print`
- structured `lsof -F` listener inspection
- Runtime pointer, metadata and source-marker reads
- isolated Runtime Python `-I -S --version` probe
- exact `127.0.0.1` single-attempt HTTP probes

Safety boundaries:

- absolute executable paths
- `shell=False`
- bounded timeout and output size
- no retries or redirects
- no credentials, cookies or authorization headers
- no launchd mutation operations
- no Runtime mutation
- no Ubuntu operations

Focused gate: `35 passed`

Base commit: `e2781094351fd9d68b562f0806799c8dbc4f100a`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C3:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C2:START -->
## ACTIVATION-01B-C2 Pure Evaluator

Status: `COMPLETE`

Implemented immutable inspection models and a deterministic,
fail-closed evaluator producing only:

- `READY_FOR_AUTHORIZATION_REVIEW`
- `BLOCKED`
- `ERROR`

The evaluator validates C1 contracts and digest bindings, orders
checks deterministically, derives blocking reasons, sanitizes
errors and emits a canonical inspection report.

Focused gate: `PASS`

Base commit: `4ad97e44c9bf499fc3368be5d41017ccb9924134`

No host adapter, Runtime command, HTTP probe, service operation,
launchd change, Ubuntu change or Production authorization occurred.

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C2:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:START -->
## ACTIVATION-01B-C1 Contract Foundation

Status: `COMPLETE`

C1 owns immutable JSON-first validation and evidence identity.
It performs no host observation, Runtime command, HTTP request,
service operation or infrastructure mutation.

Next stage:

`ACTIVATION-01B-C2 — Immutable Models and Pure Evaluator`

Architecture base commit:

`dc482780fdd36ba50d4947e8193380d7426d8367`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:START -->
## ACTIVATION-01B Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

ACTIVATION-01B is a thin read-only orchestration layer over the
existing canonical deployment contracts, Git evidence capability
and bounded macOS adapters.

It will produce canonical JSON eligibility evidence using closed
states:

- `READY_FOR_AUTHORIZATION_REVIEW`
- `BLOCKED`
- `ERROR`

No result grants activation or Production authorization.

The implementation phase may now create versioned schemas,
policy, route manifest, pure models and services, bounded macOS
adapters, a JSON CLI and no-mutation tests.

Architecture predecessor commit:

`43975f6e26986fd91c9a715786e7c68deb63f612`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## ACTIVATION-01A Runtime Activation Gate

Status: `COMPLETE`

Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`

ACTIVATION-01A defines architecture and runbook contracts only.

The contract binds atomic `runtime/current` replacement, the exact
`system/com.aicontrolcenter.api.shadow` restart identity, localhost
validation, fail-closed behavior, evidence requirements and a separate
rollback authorization boundary.

Candidate Runtime `acd80ab9f6ae` is not active. Active Runtime remains
`b9ad351a7241`.

The candidate application source remains coupled to the mutable
repository through effective `PYTHONPATH`; this limitation must be
removed or explicitly accepted before Production authorization.

Production remains `NOT_AUTHORIZED`.

Next controlled gate after documentation closeout:
`ACTIVATION-01B — Read-Only Activation Inspector`.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## RUNTIME-BUILD-04A Current Gate

Build-only and direct localhost shadow smoke are complete for release
`acd80ab9f6ae`, built from source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`. Dependency installation,
application import, the Full Suite, source marker, and metadata validation
passed. FastAPI was `0.139.0`, Uvicorn was `0.51.0`, and `jsonschema` was
available. The canonical target `core.api.shadow:app` is a `ReadOnlyASGI`
application composing internal FastAPI target `core.api.app:app`.

Direct smoke returned 200 for all six required GET routes and 405 for
`POST /health`; exact smoke PID cleanup and listener cleanup passed. The
builder's structured JSON stdout report was recovered and validated from its
log because the host wrapper found no canonical report file. That and the
unavailable optional host `rg` command are tooling observations, not release
defects.

Active Runtime `b9ad351a7241` and `runtime/current` remained unchanged; the new
release was not activated. Python and dependencies are release-owned, while
application source remains repository-bound through `PYTHONPATH`
(`source_bundled_inside_release=false`, `repository_source_binding=true`).
Source bundling, source manifesting, and source-independent launch remain open.

Activation is unauthorized. The next controlled gate is ACTIVATION-01A
architecture and an activation/rollback runbook only, after documentation
commit, non-force push with remote verification, and a new-chat handoff before
the activation risk boundary. No service, launchd, Caddy, Ubuntu, public,
production, or production-write change occurred. Runtime activation, rollback
execution, service restart, public staging, production, and production writes
remain `NOT_AUTHORIZED`.

## RUNTIME-BUILD-02 Documentation Reconciliation Gate

RUNTIME-BUILD-02A is locally complete and verified at
`5517fdb25a68c65f1bc8db03110900aa44ff173f`. The canonical macOS builder now
requires an explicit fail-closed mode, separates BUILD/VALIDATE from ACTIVATE,
builds only in owned staging, and atomically finalizes immutable releases
without changing `runtime/current`. Activation accepts and revalidates only an
already finalized release, atomically switches `runtime/current`, and performs
no dependency installation, service restart, or `launchctl` operation.

RUNTIME-BUILD-02B is locally complete and verified at
`f8f2890178c78862cff53362fd167982fa672c99`. It restores the canonical builder
Git mode to `100755` after the RUNTIME-BUILD-02A `100644` regression and adds a
deterministic executable-mode regression test. Its phase-specific identities
and verification counts remain recorded in CHANGELOG and PROJECT_HISTORY.

Its documentation reconciliation was completed before RUNTIME-CONTRACT-04A.
The later controlled Runtime gates are governed by the current section above.

OPS-01B-R5-R3A closes the runtime metadata source-marker implementation gap.
Each new immutable runtime must contain `metadata.json` and the exact
`.aicontrolcenter-source-commit` file before `runtime/current` activation. The
Shadow daemon validates the marker and fails closed. Existing releases are not
repaired; OPS-01B-R5-R3 requires a separately authorized build from committed
Git source. No activation or restart occurred.

M4-A1, M4-A1R1, M4-A2, and M4-A3 are CLOSED. M4-A3 validates deterministic,
in-memory, test-only authorization lifecycles for five independent
capabilities. Its artifacts are operationally invalid and live-boundary
rejected. No real authorization, permit, claim, writer, monitoring, dispatch,
notification, Ubuntu action, or activation occurred. Production is
`NOT_AUTHORIZED`; `.env` is not required. Decision:
`READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`. Next:
`M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION`; 427 warnings remain backlog.

M3-A4B2B2B-R4 is complete after strict-live contract compatibility validation.
The prior authorized attempt stopped `BLOCKED_PRE_AUTHORIZATION`; artifact
normalization passed, and actual counters remain zero. Ubuntu denial evidence
and the typed one-use permit boundary are repaired without operational
execution. Fresh independent approval must bind R4. Production is
`NOT_AUTHORIZED`; M3-A4B3 must not begin before actual bootstrap succeeds.

R3 Recovery-2 closes the first recovery's Git-evidence blocker through the
isolated read-only adapter and independently validates audit, replay,
PRE_ACTIVATION, and preserved post-claim failure evidence. Actual bootstrap
remains `NOT EXECUTED`; fresh approval is required and production is
`NOT_AUTHORIZED`.

The previous R3 attempt was `BLOCKED`. Recovery closes the default-composition
and pytest end-to-end gates without issuing a real permit or running the actual
Mac bootstrap. Actual targets remain absent, fresh approval must bind the
recovery commit, and production activation is `NOT_AUTHORIZED`.

## M3-A4B2B1A

CLOSED after validation. Review package AVAILABLE; human operator, independent
approver and restriction acknowledgements NOT PROVIDED. Permit NOT
ISSUED/CLAIMED, bootstrap NOT AUTHORIZED/EXECUTED, targets NOT CREATED,
production NOT_AUTHORIZED. Next: M3-A4B2B1B.

## M3-A4B2B0 Closure

M3-A4A, M3-A4B1, M3-A4B2A and M3-A4B2B0 are `CLOSED`. Read-only Mac host
preflight is `AVAILABLE`. Operational permit `NOT ISSUED`; operational
authorization `NOT GRANTED`; bootstrap `NOT EXECUTED`; operational directories
and databases `NOT CREATED`; Production activation `NOT_AUTHORIZED`. Next:
M3-A4B2B1 Operational Permit Issuance.

## M3-A4B2A Closure

M3-A4A, M3-A4B1 and M3-A4B2A are `CLOSED`. The controlled Mac bootstrap
executor is `IMPLEMENTED` and validated only under injected pytest temporary
paths. Synthetic permit consumption, audit/replay bootstrap, baseline
backup/restore and cleanup are `VALIDATED`. Operational permit `NOT ISSUED`;
operational bootstrap `NOT EXECUTED`; operational state `NOT CREATED`; writers
and monitoring `NOT ACTIVATED`; Production activation `NOT_AUTHORIZED`. Next:
M3-A4B2B Authorized Mac Operational Bootstrap Execution.

## M3-A4B1 Closure

M2, M3-A1, M3-A2, M3-A3, M3-A4A and M3-A4B1 are CLOSED. Controlled bootstrap
authorization capability is AVAILABLE and synthetic permit issuance plus
single-use claiming are VALIDATED. No operational permit was issued,
operational authorization was not granted, bootstrap was not executed,
operational directories and databases were NOT CREATED, writers were NOT
ACTIVATED, and Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2
Controlled Mac Operational Bootstrap.

## M3-A2A Closure

M2 controlled pilot validation, M3-A1 and M3-A2A are CLOSED. Permit/replay
read-only inspection is AVAILABLE. The future Mac application-state path and
event-based schema are defined, but the operational permit/replay database was
NOT CREATED. Durable reservation and consumption and persistent nonce writes
are NOT ENABLED. Production activation is `NOT_AUTHORIZED`. Next: M3-A2B
Durable Permit Reservation and Consumption.

## M3-A1C Closure

M2 controlled pilot validation and M3-A1A through M3-A1C are CLOSED. SQLite
audit backup, restore and deterministic recovery validation are IMPLEMENTED
and verified only with pytest temporary databases. The operational audit
database was NOT CREATED, the operational backup schedule was NOT ACTIVATED,
an operational restore was NOT PERFORMED, persistent writer activation is NOT
STARTED and Production activation is `NOT_AUTHORIZED`. Next: M3-A2 Durable
Permit and Replay State.

## M3-A1B Closure

M2 controlled pilot validation, M3-A1A and M3-A1B are CLOSED. The append-only
SQLite audit writer is IMPLEMENTED and verified only against pytest temporary
databases. The operational database was NOT CREATED, operational writer
activation is NOT STARTED, persistent Production audit writes are NOT ENABLED,
and Production activation is `NOT_AUTHORIZED`. Next: M3-A1C Backup, Restore
and Recovery Validation.

## M2-P3 Closure

M2 controlled pilot validation is CLOSED. DPL-04 is CLOSED, readiness is
ACCEPTED, and M2-P1 through M2-P3 are CLOSED. Exactly one pytest-owned
controlled activation and rollback were validated. Persistent host activation
is NOT STARTED, persistent host rollback and SQLite audit are NOT IMPLEMENTED,
and Production activation is `NOT_AUTHORIZED`. Next: M3-A1 Durable SQLite
Audit Adapter.

## M2-P1 Closure

M2-P1 is CLOSED and controlled non-production sandbox pilot authorization
policy is AVAILABLE. DPL-04 is CLOSED and M2 readiness is ACCEPTED. The policy
issues only deterministic one-use, Mac-only, non-production permits after
exact evidence binding and separation-of-duty checks. Pilot activation is NOT
STARTED, persistent SQLite audit is NOT IMPLEMENTED, and Production activation
is `NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot Activation and
Evidence.

## DPL-04C Closure

DPL-04C is closed with pure immutable audit contracts, deterministic canonical
JSON digests and hash-chain verification behind `DurableAuditPort`.
AIControlCenter and the Mac Control Plane own durable audit; the selected future
adapter is an append-only SQLite ledger outside Git. No adapter, database,
persistence or API write path exists. DPL-04A through DPL-04C are closed,
DPL-04D is ready, M2 is not complete and production activation is
`NOT_AUTHORIZED`.

## DPL-04B Closure

The Mac Control Plane now has an explicit-root sandbox-only implementation of
the DPL-04A non-production executor port. It supports sandbox verification,
preparation and evidence collection through canonical JSON artifacts only.
Root confinement, authorization rebinding and default denial preserve zero
production, repository, Ubuntu, network and runtime-command effects. No
durable audit or production activation is enabled. DPL-04C is next.

## DPL-04A Status

Status: COMPLETE

- Typed non-production executor contracts and ports
- Development, test and staging allowlist
- Mac Control Plane ownership
- Typed operation allowlist
- Default-deny composition
- No real executor, API route, runtime command, Ubuntu change or production
  write

Next deployment-package task: DPL-04B.

## Completed

- Brain Runtime
- FastAPI
- Provider Manager
- OpenAI
- Google
- BrainAgent
- Telegram
- Command Router
- Storage Registry
- Backup Registry
- Task Registry

## Current Sprint

Doctor Service

## Next

Logs

Backup Verify

Worker Health

Backup Execute

## Current Sprint

Sprint 21

Brain Scheduler

Current Focus

- Internal Scheduler
- Heartbeat
- Job Registry
- Automation Foundation

<!-- AI_SHOPPING_PLATFORM_START -->
## Current Program

Project: AI Shopping Platform

Status: Active Development

Current Sprint: Shopping Control Plane Bootstrap

Development runtime: Virtual Environment

Production target: Mac mini M4

Current implementation:

- Shopping domain
- Shopping health API
- Shopping readiness API
- Shopping capabilities API
- Safe read-only defaults
- Shopping test suite
- Shopping documentation

Architecture ownership:

- WordPress owns presentation and CMS
- WooCommerce owns commerce records
- AIControlCenter owns business and AI logic
- n8n executes automation
- Ubuntu remains an infrastructure worker
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 Status

Milestone: Live WooCommerce Control Plane

State:

- Architecture implemented
- WordPress and MariaDB runtime healthy
- WooCommerce REST Adapter implemented
- Product and Category APIs implemented
- Runtime Adapter selection implemented
- Read-only policy enforced
- Documentation and Git Gate in progress

Next service milestone: Shopping Homepage and AI Product Generation.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 Status

Milestone:

AI Shopping Storefront Foundation

State:

- Featured Product API implemented
- Product Search API implemented
- Product image contract implemented
- Storefront Plugin active
- External Storefront reachable
- Search and filters connected to AIControlCenter
- M5 Production Gate and Git closeout in progress

Next milestone:

M6 AI Product Generation and Approval Foundation
<!-- SHOPPING_M5_END -->

---

## Commit 19

Status: Complete

Implemented

- Homepage Renderer
- Homepage Curated Sections
- NEW / BEST / TOP / DRESS / OUTER / BAG / SALE
- Shopping Search API Integration
- Multi-section Storefront Rendering

UI Progress

95%

<!-- AI_SHOPPING_STOREFRONT_V016_MASTER -->
## Shopping Platform Baseline

Version: AI Shopping Storefront v0.16.0

Status: Feature Complete / Production Validation Passed

Git baseline:

- Commit: `a4d6098`
- Branch: `feature/shopping-platform-bootstrap`

Validated:

- Orange Coco v6 storefront
- AIControlCenter Shopping API integration
- Product detail page
- Homepage HTTP 200
- Product detail HTTP 200
- Missing product HTTP 404
- PHP 8.3 syntax validation
- JavaScript syntax validation

Next production milestone:

- Mac mini Production Control Plane migration

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Baseline

Status: **Implementation Complete**

- Final commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Service:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- Final restart: `19761 → 19842`
- Observation:
  `283/283` successful samples
- Observation duration:
  `23.535` hours
- Transactional apply: complete
- Transactional rollback: complete
- Production write cutover: not approved

Next program milestone:

AIControlCenter Platform Integration using the
completed Mac Control Plane baseline.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## PI-001 Production Baseline

Status: COMPLETE

Validated on: 2026-07-16

Production Runtime:

- Commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Short commit: `ba8d2c977257`
- Listener: `127.0.0.1:18100`
- Runtime mode: shadow
- Runtime metadata: available
- Runtime metadata schema: version 1

Operational validation:

- `GET /health`: HTTP `200`
- `GET /dashboard`: HTTP `200`
- `POST /dashboard`: HTTP `405`
- Shadow API read-only policy: enforced
- Runtime commit matches Git HEAD
- Runtime activation gated by metadata validation

Architecture status:

- Mac mini remains the always-on Control Plane.
- AIControlCenter remains the single orchestration layer.
- Ubuntu remains a stateless infrastructure worker.
- Dashboard requests do not execute Git, launchctl or shell commands.
- Runtime identity is consumed through immutable JSON metadata.

Next Production Milestone:

- Complete PI-001 documentation closeout.
- Merge the feature branch after final review.
- Define the next read-only Control Plane integration.

<!-- AICONTROLCENTER:PI-002:START -->
## PI-002 Production Status

Status: **Production Gate Passed**

Completed:

- Ubuntu worker health JSON contract
- Read-only SSH adapter
- Production worker configuration
- Dashboard worker monitoring
- Structured optional failure continuity
- system LaunchDaemon environment integration
- Immutable runtime validation
- Full regression validation

Production state:

- Mac mini owns orchestration and monitoring.
- Ubuntu remains an optional stateless worker.
- Worker unavailability does not interrupt the Control Plane.
- Production writes remain disabled.

Next operational milestone:

- Establish successful dedicated-key SSH health collection from the LaunchDaemon.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Production Status

Status: **Complete**

Primary platform milestone:

- Mac mini standalone Production Control Plane

Ubuntu status:

- Optional infrastructure extension
- May remain powered off
- Immich and Nextcloud recover automatically after Ubuntu boot
- Detailed Ubuntu integration deferred

Production result:

- AIControlCenter operates independently of Ubuntu.
- Optional worker failure does not interrupt the platform.
- Mac mini service deployment is now the primary program focus.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Production Status

Status: **Complete**

Current Production baseline:

- Mac mini standalone Control Plane
- AIControlCenter system LaunchDaemon
- immutable commit-specific runtime
- embedded Homepage API
- Ubuntu optional and powered-off permitted
- reboot recovery validated

Next milestone: PI-005 Mac Service Deployment Platform.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 Status

**Complete — Mac Service Deployment Platform baseline**

Production evidence confirms the full test suite and all PI-005 JSON gates passed with deployment execution disabled.

Next production milestone: approved native Ollama deployment on the Mac mini.
<!-- AICONTROLCENTER:PI-005:END -->

<!-- AICONTROLCENTER:PI-006:START -->
## PI-006 — Approved Ollama Native Deployment Complete

PI-006 established Ollama 0.32.1 as an approved native macOS runtime on the Mac mini M4 Control Plane.

Production baseline:

- AIControlCenter remains the single Control Plane.
- Ollama is a replaceable local model runtime and owns no platform business logic.
- Ubuntu remains a stateless infrastructure worker and runs no AI workloads.
- Ollama service: `system/com.aicontrolcenter.ollama`
- Ollama endpoint: `127.0.0.1:11434`
- AIControlCenter service: `system/com.aicontrolcenter.api.shadow`
- AIControlCenter endpoint: `127.0.0.1:18100`
- Read-only API: `GET /api/services/ollama`
- Production runtime: `3679588b760c`
- Rollback runtime: `7cb2e7a400a6`
- Model inventory: `0`
- AIControlCenter and Ollama listeners: loopback-only
- Operational gate: passed
- Git state at operational validation: clean

Validation:

- Full suite: 481 passed, 5 deselected, 423 warnings.
- AIControlCenter health: ONLINE.
- Ollama health: ONLINE.
- Runtime metadata gate: passed.
- Deployment summary validation code: 0.

Production evidence:

`~/Library/Application Support/AIControlCenter/runtime/evidence/pi-006/api-release-3679588b760c-20260720T235541Z`

Safety corrections completed during PI-006:

- Isolated mocked Ollama binary targets from `/opt/homebrew/bin/ollama`.
- Separated Homebrew user operations from privileged system operations.
- Restored and correctly registered the Ollama API router inside `create_app`.
- Distinguished the active system LaunchDaemon architecture from the legacy GUI LaunchAgent manager.
- Revalidated the final operational gate using a Python assertion after a pasted shell assertion was damaged.

Deferred technical debt:

- Replace deprecated `datetime.utcnow()` usage with timezone-aware UTC values.
- Resolve remaining Python, Starlette, and dependency deprecation warnings.
- Approve model acquisition, checksum, retention, resource, and removal policies before downloading a model.
<!-- AICONTROLCENTER:PI-006:END -->

<!-- AICONTROLCENTER:PI-007:START -->
## PI-007 Status

Status: **Production Complete — Documentation Closure Pending**

PI-007 delivered approved model lifecycle monitoring and governance under the
AIControlCenter control plane.

Production identifiers:

- source commit:
  `39fe04e3330e398f38567efa58bddb39b9893756`
- active runtime: `39fe04e3330e`
- rollback runtime: `3679588b760c`
- endpoint: `GET /api/governance/models`
- policy: default `DENY`
- write boundary: disabled
- approved models: `0`
- observed models: `0`
- violations: `0`

Architecture, implementation, focused tests, full tests, immutable deployment,
Production validation, and rollback-readiness validation are complete.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 Completion Record

Status: COMPLETE

Title: Model Governance Audit and Dashboard Integration

Production milestone:

- active source commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime release: `b9ad351a7241`
- rollback runtime release: `0352e396f329`
- Production runner: metadata-based and Git-independent
- Production closure gate: passed

Delivered:

- immutable governance audit snapshots
- append-only SQLite persistence
- audit comparison
- read-only query service
- GET-only API
- Dashboard integration
- runtime provenance
- rollback-independent runner contract

Validation:

- full test suite: `636 passed, 5 deselected`
- health endpoint: passed
- Ollama endpoint: passed
- governance endpoint: passed
- audit endpoints: passed
- Dashboard endpoint: passed
- OpenAPI write-method validation: passed
- SQLite append-only validation: passed
- process identity validation: passed
- rollback compatibility validation: passed
- Git clean: passed

<!-- PI-009:START -->
## PI-009 Master Status

**State:** Implementation Complete / Production Activation Pending

Implementation commit:

`e1d46099427321a3ba7a150aad589320c8f1261a`

Validation:

- targeted: 17 passed;
- full regression: 710 passed, 5 deselected, 427 warnings;
- Git status: clean;
- Production DB modified: no;
- Write API: disabled;
- Dashboard policy: panel-local fail-soft.

Remaining gates:

1. External Notion synchronization.
2. Explicit Production migration authorization.
3. Explicit scheduler activation authorization.
4. Post-activation observation and rollback validation.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## Current Production Milestone

PI-009 Governance Operations: CLOSED

Completed:

- operation domain and application contracts
- append-only SQLite operation event storage
- Production schema migration and verified backup
- manual backup verification operation
- Production UTC clock adapter
- JSON-first one-shot operation runner
- full regression and Git-clean implementation gate

Final implementation commit:

    d1072aa35fb5034c1097923fd7f6d7643132460b

Operational state:

- runner available
- scheduler inactive
- LaunchAgents not installed
- cadence policy deferred
- Production database protected

Next Production milestone:

PI-010 Controlled Scheduler Policy and Activation

This section is the repository-backed Notion handoff
source. External Notion synchronization is not performed
by this Git task.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Status

Status: CLOSED

Production governance scheduling is active on the Mac mini Control Plane through the managed AIControlCenter user crontab adapter.

Production execution, semantic capability evidence, append-only audit correlation, backup protection, rollback, regression, Git cleanliness, and documentation gates passed.

Next Production milestone: Shopping Platform Foundation.

<!-- BEGIN AICONTROLCENTER SPF-002 MASTER -->
## Current Production Milestone

Milestone: Shopping Platform Foundation

- PI-010: CLOSED
- SPF-001: CLOSED
- SPF-002: CLOSED
- Architecture commit: `9e4476abfe53cad9b19c0c5c472028f6c91f82e5`
- Regression baseline: 741 passed, 5 deselected, 427 warnings
- Production governance scheduler: Active
- Governance database quick check: Passing
- Shopping writes: Disabled
- Ubuntu Shopping state and business logic: Prohibited

Next task: SPF-003 Shopping package and read-only port skeleton.
<!-- END AICONTROLCENTER SPF-002 MASTER -->

<!-- SPF-003:START -->
## SPF-003 Closure Record

- Status: CLOSED
- Milestone: Shopping Platform Foundation
- Scope: package boundaries, compatibility migration, provisional contracts, seven read-only ports, and validation
- Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`
- Targeted validation: 6 passed
- Full regression: 747 passed with 5 deselected
- Production modified: false
- Ubuntu modified: false
- Write operations enabled: false
- Next task: **SPF-004 — Canonical JSON Schema v1**
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Status — SPF-004

SPF-004 Canonical JSON Schema v1: **CLOSED**

Authoritative state:

- Shopping Sprint completed tasks: 4/10
- Shopping Sprint remaining tasks: 6/10
- canonical contract schemas: 15
- schema resources: 17
- schema assets including registry: 18
- targeted schema tests: 6 passed
- full regression: 753 passed
- production modified: false
- Ubuntu modified: false
- Shopping writes enabled: false

Implementation commit: `7a436a62fbaa2c176e877297d88b810b255f2776`

Next task: **SPF-005 Capability Registry — deny by default**.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-005 CLOSED

Current sprint progress: **5/10 tasks complete**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default

SPF-005 production invariants:
- AIControlCenter owns capability governance.
- Default authorization behavior is DENY.
- Shopping WRITE capabilities are not executable.
- Ubuntu remains a stateless infrastructure worker.
- WordPress and WooCommerce do not own platform authorization or business logic.

Next task: **SPF-006 Read Adapter Contracts**.

Remaining Shopping Platform Foundation work: **5/10 tasks**.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-006 CLOSED

Current sprint progress: **6/10 tasks complete — 60%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts

Current production invariants:
- AIControlCenter owns all Shopping business logic and governance.
- Adapters remain replaceable and vendor-neutral at the platform boundary.
- WordPress and WooCommerce do not own platform-wide authorization or business logic.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-007 Adapter Health Monitoring**.

Remaining Shopping Platform Foundation work: **4/10 tasks**.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-007 CLOSED

Current sprint progress: **7/10 tasks complete — 70%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring

Current production invariants:
- AIControlCenter remains the single Shopping control plane.
- Adapter health is monitoring data, not authorization.
- Health normalization and aggregation remain read-only and stateless.
- WordPress and WooCommerce do not own platform-wide business logic.
- Live vendor transport remains disabled.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-008 Read-only Snapshots**.

Remaining Shopping Platform Foundation work: **3/10 tasks**.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation Status — SPF-008 CLOSED

Current sprint progress: **8/10 tasks complete — 80%**.

Closed:
- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1
- SPF-005 Capability Registry deny-by-default
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring
- SPF-008 Read-only Snapshots

Current production invariants:
- AIControlCenter remains the single Shopping control plane.
- Snapshot queries remain read-only.
- Snapshot creation and persistence remain disabled.
- Authorization occurs before snapshot repository access.
- WordPress and WooCommerce do not own platform-wide business logic.
- Ubuntu remains a stateless infrastructure worker.
- Shopping WRITE operations remain disabled.

Next task: **SPF-009 Validation and Schema Drift**.

Remaining Shopping Platform Foundation work: **2/10 tasks**.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Project state: SPF-009 CLOSED, Shopping Platform Foundation **9/10**.
- Implementation commit: `3fa21878e72cdb9608a728a1c676e70fb70b5717`.
- Runtime schema validation and schema drift monitoring are read-only control-plane capabilities owned by AIControlCenter.
- Validation gate: 58 targeted tests passed; full regression 930 passed and 5 deselected.
- Production mutation: false.
- Ubuntu application state: false.
- Write operations enabled: false.
- Next production milestone: SPF-010 final regression, operational and documentation closure.

<!-- AICONTROLCENTER:SPF-010:CLOSED -->
## SPF-010 Closure — Shopping Platform Foundation

- Status: CLOSED
- Shopping Platform Foundation: 10/10 (100%)
- Production Readiness Gate: PASSED for the read-only Foundation.
- AIControlCenter remains the single Control Plane on Mac mini M4.
- Ubuntu Server remains a stateless infrastructure worker only.
- AI workloads, business logic, and application state remain outside Ubuntu.
- Production write operations remain disabled.
- Automatic schema adoption and automatic schema migration remain disabled.
- Any future mutation or write capability requires a separate sprint and explicit production gate.
- Shopping regression: 233 passed.
- Full regression: 930 or more passed, 5 deselected, 0 failed, 0 errors.
- Read-only operational smoke validation: PASSED.
- Release blockers at final audit: 0.
- Master project status: SPF-010 CLOSED.
- Shopping Platform Foundation status: COMPLETE.
- Next phase must preserve read-only-first governance and adapter boundaries.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Shopping External Read Integration — Authoritative State

**Program:** SRI — Shopping External Read Integration
**Branch:** `feature/shopping-external-read-integration`

### Progress

- SRI-01 — CLOSED
- SRI-02 — CLOSED
- SRI-03 — IN PROGRESS
- SRI-04 — PENDING
- SRI-05 — PENDING
- SRI-06 — PENDING

**Program closure:** 2/6 CLOSED

### SRI-03 completed

- Canonical WooCommerce read wrapper
- Canonical normalization and schema validation
- GET-only bounded read transport
- Caddy runtime validation
- Mac LAN ingress validation
- External WAN HTTP 80 validation
- DDNS and public IPv4 validation
- Authoritative parent CAA root-cause confirmation

### Current blocker

Controlled Production DNS and trusted HTTPS are required before the first real canonical WooCommerce production READ.

### Safety state

- Shopping writes: DISABLED
- Production ACME on `bokstory.iptime.org`: STOPPED
- Ubuntu business logic changes: NONE

### Next production milestone

Trusted HTTPS on a platform-controlled production hostname followed by one controlled canonical WooCommerce READ.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:MASTER -->
## Production Contracts Established by SRI

### Platform invariants

- AIControlCenter is the single Control Plane.
- Mac mini M4 owns orchestration, AI, business logic and application state.
- Ubuntu remains a stateless infrastructure worker.
- External components integrate through replaceable adapters and APIs.

### External READ governance

- Read-only monitoring precedes validation and write operations.
- Persisted JSON evidence is authoritative.
- Credential values must not appear in Git, console output or evidence.
- Generic monitoring owns orchestration and domain logic remains in its domain.

### Production write gate

No production write is authorized by SRI.
Future writes require explicit architecture review, authorization, audit evidence, rollback design and production validation.

### Codex execution governance

- AI Home Datacenter Architect remains architecture and production authority.
- Codex is an implementation executor.
- Codex must preserve approved scope, run tests and update documentation.
- Codex must not change architecture or infrastructure ownership implicitly.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## Current Program — DPL Deployment Package

### SRI baseline

- Status: COMPLETE
- Final SRI commit:
  `ba6fdb6a69ee9398b44fdd0810102b078c38c7f8`
- Final regression baseline: `984 passed, 5 deselected`
- Production business writes: `0`

### DPL status

- DPL-01 Inventory and Architecture Assessment: COMPLETE
- DPL-02 Read-only Package Contract and Validation: COMPLETE (M1)
- DPL-03 Read/Plan/Apply Dependency Separation: NEXT
- Production activation: NOT AUTHORIZED

DPL preserves AIControlCenter ownership, the Mac mini M4 single Control Plane,
Host Caddy as the sole public edge, and Ubuntu as an optional stateless worker.
DPL-02 is restricted to inventory, validation, diff, dry-run planning,
readiness and audit.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 / M2 Readiness Status

- DPL-04A: CLOSED
- DPL-04B: CLOSED
- DPL-04C: CLOSED
- DPL-04D: CLOSED
- DPL-04: CLOSED
- M2: READINESS_ACCEPTED
- M2 activation: ACTIVATION_NOT_STARTED
- M2-P1: CLOSED
- Pilot authorization policy: AVAILABLE
- Production activation: NOT_AUTHORIZED
- Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence
- Broader mutable deployment prerequisite: persistent SQLite audit adapter

## M3-A4A Status

- M2: CLOSED
- M3-A1: CLOSED
- M3-A2: CLOSED
- M3-A3: CLOSED
- M3-A4A: CLOSED
- Activation readiness gate: AVAILABLE
- Controlled bootstrap plan: AVAILABLE
- Operational databases: NOT CREATED
- Operational writers: NOT ACTIVATED
- Operational monitoring: NOT ACTIVATED
- External alert dispatch: NOT IMPLEMENTED
- Bootstrap authorization: NOT GRANTED
- Production activation: NOT_AUTHORIZED
- Next: M3-A4B Controlled Mac Operational Bootstrap

## M3-A3C Status

- M3-A1: CLOSED
- M3-A2: CLOSED
- M3-A3A: CLOSED
- M3-A3B: CLOSED
- M3-A3C: CLOSED
- M3-A3 Monitoring and Alert Track: CLOSED
- End-to-end monitoring drill: VALIDATED
- Simulated logical delivery: VALIDATED
- External alert dispatch: NOT IMPLEMENTED
- Alert persistence: NOT IMPLEMENTED
- Operational monitoring: NOT ACTIVATED
- Operational databases: NOT CREATED
- Production activation: NOT_AUTHORIZED
- Next: M3-A4 Controlled Operational Activation Gate

## M3-A3B Status

- M3-A1: CLOSED
- M3-A2: CLOSED
- M3-A3A: CLOSED
- M3-A3B: CLOSED
- Read-only monitoring snapshot: AVAILABLE
- Alert candidate evaluation: AVAILABLE
- Logical alert routing: AVAILABLE
- Deterministic deduplication: AVAILABLE
- Severity escalation policy: AVAILABLE
- External alert dispatch: NOT IMPLEMENTED
- Alert routing persistence: NOT IMPLEMENTED
- Operational monitoring: NOT ACTIVATED
- Durable permit writer: IMPLEMENTED, NOT OPERATIONALLY ACTIVATED
- Operational audit database: NOT CREATED
- Operational replay database: NOT CREATED
- Operational backup schedule: NOT ACTIVATED
- Production activation: NOT_AUTHORIZED
- Next: M3-A3C Monitoring and Alert Operational Drill
# M3-A4B2B1B closure

M3-A4B2B1A: CLOSED. M3-A4B2B1B: CLOSED after validation. Human approval gate:
AVAILABLE. Synthetic dual-identity approval and permit issuance: VALIDATED.
Current review: DENIED (`mac-account:kyouhan`; approver `UNASSIGNED`).
Operational permit NOT ISSUED/NOT CLAIMED; bootstrap NOT AUTHORIZED/NOT
EXECUTED; production `NOT_AUTHORIZED`. Next: M3-A4B2B1C.
# M3-A4B2B2A CLOSED

Authorized Mac bootstrap execution capability: AVAILABLE. Atomic claim:
VALIDATED in tests. Controlled operational mode: NOT EXECUTED. Operational
targets/databases: NOT CREATED. Writers/monitoring: NOT ACTIVATED. Production:
NOT_AUTHORIZED. Next: M3-A4B2B2B Fresh Permit and Authorized Mac Bootstrap
Execution.
# M3-A4B2B2B-R1 CLOSED

Existing safe shared-parent compatibility and failure recovery are validated
only under injected temporary roots. Actual bootstrap is NOT EXECUTED; fresh
approval and permit are required. Production is NOT_AUTHORIZED.
# M3-A4B2B2B-R2

Controlled operational activation boundary: implemented and capability
validated. Fresh independent approval is required for the next exact commit.
# M3-A4B2B2B-R5

Acknowledgement projection compatibility is implemented. The prior attempt
stopped before claim and its permit is not reusable. Fresh independent approval
and an authorized Mac bootstrap remain required; M3-A4B3 is blocked.

# M3-A4B3 CLOSED

The commit `f7a81b73b86c170300bb6b80f437dbb753362f7e` bootstrap evidence
chain, single consumed permit/claim, `HEALTHY` zero-event audit and replay
state, baseline backups, and isolated restores are validated. Writers,
monitoring, dispatch, Ubuntu, and production remain inactive/unauthorized.
Next: `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.

# M3-A4C CLOSED — M3 CLOSED

Readiness is validated at `0f23abdf362965c09db5f4f35483cbff47853643`
against the bootstrap at `f7a81b73b86c170300bb6b80f437dbb753362f7e`.
Operational state is unchanged; writers, monitoring, dispatch, Ubuntu, and
production remain false. Next: `M4_CONTROLLED_ACTIVATION_ARCHITECTURE`.

# M4-A1 CLOSED

Controlled activation architecture is defined with five independently
authorized, default-inactive capabilities and an exact immutable transition
chain. Planning is deterministic and test-only. Decision:
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`; this authorizes nothing.
No writer or runtime was implemented. Mac remains the Control Plane, Ubuntu
remains stateless, and production remains `NOT_AUTHORIZED`. Next:
`M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.

# M4-A2 CLOSED

Typed immutable authorization request, approval, restriction, evidence,
validation, and test grant-plan contracts cover the exact M4-A1 registry.
Canonical SHA-256 binding, independent identities, exact Git/M3/M4-A1 binding,
full restrictions, injected-clock expiry, and one-hour maximum TTL fail closed.
Every capability remains independent; dependencies never authorize.

Decision: `READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`. No real
authorization, permit, claim, activation, writer, monitoring runtime, dispatch,
Ubuntu change, API write route, command, environment secret, or production
authorization was created. Production is `NOT_AUTHORIZED`; next:
`M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION`.

# M4-A1R1 CLOSED

M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a` remains
architecture-only. Retained SQLite snapshots are immutable copy sources;
inspection and recovery operate only on disposable working copies, including
their WAL/SHM files. Actual operational state remained unchanged, `.env` is not
required, and production is `NOT_AUTHORIZED`. Decision:
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`. Next:
`M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.
# AUTO-01 CLOSED

AUTO-01 closes the autonomous delivery controller architecture with decision
`READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`. M4-A3 remains CLOSED. AIControlCenter
is the single Control Plane; Codex is bounded executor only. No persistent
runner, authorization, permit, claim, write or activation exists. Next:
`AUTO-02_PERSISTENT_CODEX_RUNNER_AND_RECOVERY`.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Active Milestone Decision — 2026-07-31

- AUTO-01: CLOSED
- AUTO-02: DEFERRED
- AUTO-03: DEFERRED
- M4-A4: DEFERRED
- M4-A5: DEFERRED
- M4-A6: DEFERRED
- SHOP-00: ACTIVE NEXT TASK

The deployment and controlled-activation foundations are retained.
Further framework expansion is deferred while the Shopping Platform
delivers product-facing value.

Production remains `NOT_AUTHORIZED`.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## SHOP-00 Shopping Platform Reprioritization

SHOP-00 is closed.

Repository inventory and regression validation confirmed that the
existing Shopping Platform Foundation and Shopping External Read
Integration are already part of the current branch history.

Existing capabilities designated for reuse:

- WooCommerce external read adapter
- WooCommerce transport and normalization
- WordPress CMS adapter
- normalized product snapshot JSON contracts
- read authorization and deny-by-default policy
- schema validation and drift monitoring
- adapter health monitoring
- nine read-only Shopping API routes
- Orange Coco storefront

The former SHOP-01 WooCommerce Read Adapter scope is therefore
`CLOSED_BY_EXISTING_SRI`.

The first incomplete product capability is:

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

Architecture invariants:

- Storefront and management Dashboard are separate surfaces.
- Dashboard consumes AIControlCenter APIs only.
- Dashboard does not call WooCommerce directly.
- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns business workflow and normalized management
  views.
- SHOP-01 is read-only.
- Product draft, approval and controlled write remain separate tasks.
- No Shopping business logic is placed on Ubuntu.
- Production writes remain `NOT_AUTHORIZED`.


Current milestone status:

- SHOP-00: CLOSED
- SHOP-01: ACTIVE NEXT
- SHOP-02: PLANNED
- SHOP-03: PLANNED
- SHOP-04: PLANNED
- SHOP-05: PLANNED
- SHOP-06: PLANNED
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## SHOP-01B Shopping Management Read Model

SHOP-01B adds a pure read-only application projection for
operator-facing product management data.

The projection consumes the existing `ShoppingService` boundary and
produces deterministic JSON-safe output containing:

- service health
- readiness
- read/write capability state
- adapter integration state
- catalog totals
- in-stock and out-of-stock counts
- inventory quantity totals
- normalized product list fields

The module performs no network calls, persistence, product mutation,
WooCommerce imports or Dashboard registration.

The Product Management Dashboard remains a projection of WooCommerce
truth through AIControlCenter. It is not a second product database.

The next task is `SHOP-01C_DASHBOARD_JSON_INTEGRATION`.
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## SHOP-01C Dashboard JSON Integration

The existing `GET /dashboard` projection now includes an optional
`shopping_management` section.

The section is generated through the completed Shopping management
read model and remains read-only.

Failure isolation rules:

- Shopping configuration failure does not fail the Dashboard.
- Shopping catalog failure does not fail the Dashboard.
- Internal exception details are never exposed.
- An unavailable Shopping dependency returns a deterministic
  `UNAVAILABLE` envelope.
- Existing Dashboard behavior is preserved when no Shopping
  projection is injected.

The Dashboard imports no WooCommerce adapter and creates no local
product truth.

The next task is `SHOP-01D_VALIDATION_AND_CLOSEOUT`.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## SHOP-01 Product Management Read Model and Dashboard

SHOP-01 is closed.

Completed capabilities:

- deterministic Shopping management read model
- product and inventory summary
- normalized operator-facing product list
- health, readiness, capability and integration projection
- optional `shopping_management` Dashboard dependency
- `GET /dashboard.shopping_management` JSON projection
- deterministic `UNAVAILABLE` failure envelope
- internal error-detail suppression
- source and result mutation isolation
- existing Dashboard compatibility
- default-configuration read-only operational observation

Architecture boundaries remain unchanged:

- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns management projections and workflow logic.
- The Dashboard does not import WooCommerce adapters.
- No local product truth was created.
- No Shopping mutation route was added.
- Production writes remain `NOT_AUTHORIZED`.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## SHOP-01E2 Shopping Product Compatibility Adapter

The default Mock catalog returned the legacy `Product` contract while
the management read model required the canonical product projection.

A dedicated application adapter now translates the existing
`ShoppingService` result into the canonical management contract.

Explicit mappings:

- `id` to `product_id`
- `image_url` to `image_urls`
- `Decimal` price to a JSON number

Missing SKU, inventory quantity, URL and updated timestamp values
remain null. The adapter does not synthesize unknown Commerce data.

The canonical management contract was not weakened. The Dashboard
continues to have no direct WooCommerce dependency.

The next task is:

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## SHOP-02A Status

SHOP-01E read foundation: CLOSED. SHOP-01E3D persistent activation: DEFERRED. SHOP-02A architecture: COMPLETE. Immutable revisions and exact-revision human approval are defined; AI approval is forbidden. Production writes: `NOT_AUTHORIZED`. WooCommerce observation: zero products, one category; ProductDraft work is independent of population. Next: `SHOP-02B_PRODUCT_DRAFT_DOMAIN_IMPLEMENTATION`.

## SHOP-02B Status

`SHOP-02B_PRODUCT_DRAFT_DOMAIN_IMPLEMENTATION`: COMPLETE. ProductDraft contract version remains 1.0.0. Immutable revisions, lifecycle evaluation, optimistic concurrency, deterministic idempotency, and the repository port are implemented. The in-memory adapter is non-production; there is no persistent store, mutation route, or WooCommerce write. Production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02C_PRODUCT_DRAFT_VALIDATION_APPROVAL_SERVICE`.

## SHOP-02C Status

`SHOP-02C_PRODUCT_DRAFT_VALIDATION_APPROVAL_SERVICE`: COMPLETE. Deterministic validation, deny-by-default authorization, exact-revision HUMAN-only approval/rejection/revocation, request-review orchestration, immutable audit events, instance-local idempotency, and read-only projections are implemented. Contracts remain 1.0.0; audit and idempotency adapters are in-memory and non-production. No API mutation route, persistent storage, or WooCommerce write exists. Production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02D_PRODUCT_DRAFT_READ_API_DASHBOARD`.
# SHOP-02D status

SHOP-02D ProductDraft GET-only API and Dashboard projection are complete. Routes: `/shopping/product-drafts`, `/shopping/product-drafts/{draft_id}`, and `/shopping/product-drafts/{draft_id}/revisions/{revision_id}`. Dashboard key: `product_draft_review`. Default source behavior is `UNAVAILABLE`; configured empty snapshots remain available. ProductDraft contract 1.0.0 is unchanged, and SHOP-03 controlled WooCommerce write architecture is next.

## SHOP-03A Status

`SHOP-03A_CONTROLLED_WOOCOMMERCE_WRITE_ARCHITECTURE`: COMPLETE. Exact immutable approved revisions can produce deterministic controlled fake/dry-run plans only after source freshness and digest checks plus exact deny-by-default authorization. ProductDraft contracts remain 1.0.0. No mutation API, persistent queue, real WooCommerce adapter, or production write authorization exists. SHOP-03B requires a separate explicit gate.
# SHOP-03B status

SHOP-03B program authorization is user-attested at `2026-08-03T08:54:00+09:00`. SHOP-03B1 is complete as an intercepted-only adapter contract and credential boundary. Exact product/revision execution authorization remains unbound, no real transport exists, and production activation remains `NOT_AUTHORIZED`. Next: `SHOP-03B2_ONE_PRODUCT_CONTROLLED_PILOT`.
## UI-01 — Homepage Shopping Dashboard

Complete: the internal read-only browser route is `GET /homepage`, consuming
exactly `GET /dashboard` (`shopping_management` and `product_draft_review`). No
frontend framework, public Caddy exposure, authentication change, mutation API,
or live Commerce write was added. ProductDraft and deployment contracts remain
unchanged. Public opening awaits OPS-01; next is UI-02 Product Management
Console.

## UI-02 — Product Management Console

Complete: internal `GET /homepage/product-management` consumes only existing
ProductDraft GET APIs in `INTERNAL_READ_ONLY` mode. It exposes lifecycle,
validation, human-review, and returned deployment-intent state without controls.
Public opening and production activation remain absent and `NOT_AUTHORIZED`.
Next: `OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## PI-009A1 Status

Status: COMPLETE

Implementation commit:
`fe0e89af58c28d8b72b47c4c4e2f8fa86cc5739c`

Final deployment regression:
`1133 passed, 9 warnings`

Runtime/service mutations during PI-009A1:
0

Production authorized:
NO

Next Production blocker:
`RUNTIME_SOURCE_ISOLATION`

## PI-009A2

Status: ARCHITECTURE FROZEN

Target:

`runtime/venvs/<runtime-id>` + `runtime/sources/<runtime-id>`

Current Candidate Runtime:

`acd80ab9f6ae`

Candidate source commit:

`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Current pointer migration required:
NO

Production authorized:
NO

Next gate:
A2.1 repository implementation and tests.

## PI-009A2 State Isolation

Status:
REPAIR IMPLEMENTED

Immutable source:
READ ONLY

Writable application state:
EXTERNAL DATA ROOT

Canonical environment contract:
`AICONTROLCENTER_DATA_ROOT`

Former Candidate final promotion:
BLOCKED

Reason:
The former source commit contains repository-relative SQLite state defaults.

Required:
new source commit and new Runtime Candidate.

Production authorized:
NO

## PI-009A2 A2.1

Status:
COMPLETE

Immutable source artifact tooling:
VALIDATED

Immutable-source wrapper template:
VALIDATED

Source/state isolation:
VALIDATED

Canonical Runtime build source:
CLEAN HEAD

Operational source artifact:
NOT CREATED

Live wrapper:
UNCHANGED

Runtime pointer:
UNCHANGED

Production authorized:
NO

Next gate:
new Runtime Candidate build authorization.

## PI-009A2 A2.2A

Status:
VALIDATED

Runtime Candidate:
`7b171f135dc7`

Source commit:
`7b171f135dc7882546bf7f733208778f1aef4943`

Canonical report SHA-256:
`61f88c861a4ecf44a17570e46dc1608866193b987c0448e8eca747d294dfa77b`

Immutable source/state smoke:
PASS

Active Runtime changed:
NO

Operational source artifact created:
NO

Live wrapper changed:
NO

Service mutated:
NO

Production authorized:
NO

Milestone:
NEW_IMMUTABLE_RUNTIME_CANDIDATE_VALIDATED

## PI-009A2 A2.2B

Status:
VALIDATED

Runtime:
`7b171f135dc7`

Immutable source:
PRESENT

Runtime/source identity:
PASS

Manifest SHA-256:
`a74977db05ac93bfc5c9e3d621d0748822c5f7f6021f7f0d0fb7c2d3f1983626`

Content SHA-256:
`f2454fc4e90a860515caa95d7f42382d611da4cae530d534111131ce3e61e6e8`

Immutable application execution:
PASS

Active Runtime changed:
NO

Live wrapper changed:
NO

Service mutation:
NO

Production authorized:
NO

Milestone:
IMMUTABLE_SOURCE_ARTIFACT_OPERATIONALLY_VALIDATED

## PI-009A2 A2.3

Status:
VALIDATED

Live Runtime:
`7b171f135dc7`

Immutable source:
YES

External persistent state:
YES

Repository source serving:
NO

Repository DB serving:
NO

Production authorized:
NO

Milestone:
IMMUTABLE_RUNTIME_LIVE_CUTOVER_VALIDATED

## PI-009 Production Status

Production status:

`PRODUCTION_AUTHORIZED`

Runtime:

`7b171f135dc7`

Source commit:

`7b171f135dc7882546bf7f733208778f1aef4943`

Authorized governance baseline:

`d3dda82e8f26b6405212071d0713a6e9acb4d6ee`

Technical gate:

PASS

Deployment regression:

2337 passed, 5 deselected

Immutable source:

YES

External persistent state:

YES

Milestone:

`PI_009_PRODUCTION_AUTHORIZED`

## AI-PROVIDER-01B

Status:

VALIDATED

OpenAI authenticated connectivity:

YES

Responses API:

VALIDATED

Production integration:

PENDING AI-PROVIDER-01C

Notion:

DEFERRED_UNTIL_FINAL_PHASE

## AI-PROVIDER-01C-B

Status:

VALIDATED

Candidate Runtime/source:

`102b8f1fa862`

Source commit:

`102b8f1fa8628d00d25575cb94538826a1a04e10`

Production Runtime:

`7b171f135dc7` UNCHANGED

Next gate:

SEPARATE HUMAN AUTHORIZATION FOR AI-PROVIDER-01C-C

## AI-PROVIDER-01

Status:

VALIDATED

Production Runtime:

`102b8f1fa862`

Production source:

`102b8f1fa8628d00d25575cb94538826a1a04e10`

Canonical Production AI workflow:

`BrainAgent -> ProviderRouter -> ProviderAdapter -> OpenAIAdapter`

Authenticated Production-artifact workflow:

VALIDATED

Persistent daemon credential wiring:

PENDING SEC-01

Milestone:

`AI_PROVIDER_PRODUCTION_ARTIFACT_WORKFLOW_VALIDATED`
# SEC-01B security control

The authoritative provider-secret design is Protected File-Per-Provider Secrets with Deterministic Wrapper Injection. Repository implementation is complete; live helper/wrapper installation remains an SEC-01C authorization-gated operation. Production Runtime remains `102b8f1fa862`.

## SEC-02 active governance program

SEC-01 remains complete at `PRODUCTION_SECRET_LIFECYCLE_VALIDATED`. SEC-02 is
active. SEC-02A0 governance inventory and the SEC-02A1
architecture/domain/contract freeze are complete:

`SEC_02A1_FINAL_STATUS=GOVERNANCE_DOMAIN_AND_JSON_CONTRACT_FROZEN`

A2 is the preserved authorization-domain baseline. A3 now has a pure-domain
implementation and focused tests, with no test run by Codex. Its target
milestone
`SEC-02A3_PRECONDITION_SNAPSHOT_AND_STALE_SEMANTICS_VALIDATED` remains pending
external focused-test success. Immutable snapshots, deterministic exact-bound
comparison, receipt/snapshot validation, drift-to-`STALE`, and caller-time
expiry-to-`STALE` add no Production mutation capability. AIControlCenter on the
Mac mini remains the sole Control Plane; Ubuntu remains a stateless bounded-JSON
infrastructure Worker. Mature DPL, governance operations, and shopping
ownership is preserved. Next:
`SEC-02A4 MUTATION BUDGET AND INVOCATION ACCOUNTING`.

The SEC-02A governance architecture-ready milestone is not claimed. Notion
remains `DEFERRED_UNTIL_FINAL_PHASE`.

# SEC-01C-R1 repair state

Repository repair is validated, but SEC-01C is incomplete. The live attempt consumed two installs and one restart; its frozen wrapper used mutable source. HTTP recovery was insufficient and no rollback occurred. The repaired wrapper is not installed, and the current installation remains blocked pending new exact human authorization for replacement and one restart. Runtime `102b8f1fa862` has importable `jsonschema`. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.

## SEC-01C final state

Status: `COMPLETE`

Milestone: `PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`

R1 subsequently converged immutable-source execution. R2 found and classified
the workers config as `VERSIONED_APPLICATION_CONFIG`; R3 froze its matching
immutable-source binding without intended live mutation. R3Q stopped on drift
before mutation with zero edit/restart attempts. Separately authorized R3Q2
changed only the entry's quoting representation and performed exactly one
restart. Current source and workers config are immutable and matched; mutable
repository dependencies are false; operational state and HTTP `200/200/405` are
validated; and credential presence was verified without exposing the value or
calling the provider. SEC-01 is not complete. Next: SEC-01D Secret Lifecycle &
Recovery Validation. Notion: `DEFERRED_UNTIL_FINAL_PHASE`.

## SEC-01 final production state

Status: `COMPLETE`

Milestone: `PRODUCTION_SECRET_LIFECYCLE_VALIDATED`

Governance baseline HEAD:
`68a107432ceabf8527f0071db6b0bb7cd2bec71b`

Production Runtime/source: `102b8f1fa862` at
`/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/sources/102b8f1fa862`

Validated: persistent daemon delivery; restart and reboot recovery; isolated
missing-secret fail-closed behavior; one atomic storage replacement; one
authorized E3 daemon restart; provider administration; and candidate cleanup.
Previous credential revocation/deletion is operator-attested. Provider admin
revocation machine verified: false. Authenticated provider validation
performed: false. Credential identity proven locally: false. No secret value or
credential identifier belongs in documentation. The service was healthy after
E5 and the candidate `.next` file was removed.

Final quality gate: R1 is retained as
`INVALID_RAW_PYTEST_GATE_INVOCATION` (raw pytest: 2 failed, 2338 passed, 5
deselected, 62 errors) because it bypassed the canonical harness and lacked its
isolated test-root environment. It demonstrated no application regression and
was not caused by documentation. R2 was `DIAGNOSED_READ_ONLY` with no mutation.
R3 passed 3/3 representative selections (17 tests) through the canonical
harness. R4 is authoritative: the canonical deployment regression harness, not
raw pytest, reported 2402 passed, 5 deselected, and 437 warnings. Warnings are
not failures; tests did not modify the repository, Production PID was unchanged,
canonical secret metadata was preserved, the candidate was absent, and
Production mutation was zero.

Permanent exceptions:
`SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`,
`SEC-01D-C3-BOOT-PARSER-DEFECT`, and
`SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`. They are neither retroactive authority
nor a claim that lost evidence was restored. Durable evidence belongs in the
Control Plane evidence root, not `/private/tmp` across reboot.

Next milestone: `SEC-02_CONTROL_PLANE_GOVERNANCE_AUTOMATION`. The wider project
remains in progress.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## Production Runtime Status — 2026-08-13

Production release:

`ed2424e39bb1`
(`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`)

Status:

`AIControlCenter_RUNTIME_HEALTH_MODEL_PRODUCTION_DEPLOYED`

The canonical AIControlCenter API runs on the Mac mini Control Plane at
`127.0.0.1:58081`.

Production Runtime Health currently reports:

- API — required, launchd, `RUNNING`.
- Telegram — optional, `NOT_DEPLOYED`.
- Application Scheduler — required, `NOT_DEPLOYED`.
- Scheduler heartbeat — `STALE`.
- Service topology — `VALID`.
- Aggregate — `healthy=false` by design until the required Scheduler becomes
  operational with a fresh heartbeat.

Public HTTP/HTTPS ingress is terminated by Caddy on the Mac and forwarded to
the canonical API. Ubuntu remains a stateless on-demand infrastructure Worker
and does not own AI workloads, application scheduling, business logic or
platform-wide state.

OPS-01B final milestone:

`OPS-01B_RECURRENCE_PREVENTION_VALIDATED_AND_CLOSED`

OPS-01B lifecycle readiness requires the root-owned `0755` canonical log
directory and regular, non-symlink `kyouhan:staff 0640` Scheduler stdout and
stderr files. Read-only validation and missing-file provisioning are separate
from launchd activation. There is no automatic remediation, activation, retry,
or rollback. The existing runtime `ServiceHealth` projection observes log
readiness through an injected adapter and owns no deployment lifecycle
mutation. The canonical Scheduler deployment lifecycle gate is
`application_scheduler_bootstrap.py`; dry-run and apply share read-only
contract and registration probes, while only apply may issue one bootstrap
after eligibility passes. Root identity is only an executor precondition and
does not constitute human authorization; the outer governed executor retains
that boundary.

The canonical immutable API runner now targets
`ops.macos.runtime.application:app`. This outer macOS composition supplies the
Scheduler log inspector to the platform-neutral core application factory.

Application Scheduler Production recovery was already operational before the
recurrence-prevention closeout. Focused recurrence validation passed. Canonical
deployment regression invocation #1 failed with 13 test failures caused by
umask-sensitive Scheduler fixtures and a controlled-live test that hashed the
independently mutable real-home AIControlCenter tree. Only test defects were
corrected, without weakening Product contracts. The corrected focused scope
passed 39 tests under umask `077`, with the controlled live root explicitly
confined to `/private/tmp`. Canonical deployment regression invocation #2
passed with `RC=0`. Exactly two canonical invocations were made because
code/test changes occurred after invocation #1; no canonical test count is
claimed for invocation #2.

No Production mutation occurred during recurrence-prevention validation. No
additional activation, bootstrap, log provisioning, kickstart, retry, or
rollback was performed. OPS-01B recurrence prevention is validated and
OPS-01B is closed.

Shadow release alignment is a separate maintenance Sprint and is not a blocker
for the active Production release.

## PA-05 — WooCommerce Headless Adapter v1 closeout

PA-05 is validated at milestone
`WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`. AIControlCenter remains the sole
Control Plane and owner of shopping business logic. `core.shopping` is
authoritative for ProductDraft lifecycle, product policy, workflow,
recommendation, customer automation, governance, and business logic.
WordPress remains CMS-only, WooCommerce remains commerce-engine-only, and
`integrations.woocommerce` remains a replaceable read-only adapter.
`ops.macos.runtime.application` is the outer composition root; core imports
neither `ops.*` nor `integrations.*` (`CORE_OPS_IMPORT_COUNT=0`,
`CORE_INTEGRATIONS_IMPORT_COUNT=0`).

The canonical Production manifest has no WooCommerce service identity.
Absence does not prove `NOT_DEPLOYED`. Deployment, configuration, and
authentication are `UNKNOWN`; catalog/API availability is unproven; default
capability status is fail-closed `UNAVAILABLE`. Missing, duplicate, malformed,
schema-invalid, and unreadable lookups emit no invented `canonical_manifest`
evidence. Validated evidence requires exactly one successfully returned
WooCommerce identity.

`core.capabilities` retains governance. Typed boolean-only extensions cannot
override the reserved facts `authority=AICONTROLCENTER`, `read_only=true`,
`production_authorization=false`, `infrastructure_mutation=false`,
`platform_business_policy_ownership=false`, and `action_execution=false`.
WooCommerce extension facts are `commerce_engine_only=true` and
`automatic_retry=false`. `UnavailableCapabilityObserver` is the
provider-neutral fallback. Platform-neutral `create_app` makes no WooCommerce,
n8n, or OpenClaw discovery and preserves PA-02/PA-03 outward fail-closed
compatibility.

The sole PA-05 API is `GET /shopping/providers/woocommerce`; there is no
POST/PUT/PATCH/DELETE endpoint and no product, order, inventory, customer,
coupon, execute, retry, or Production mutation action. Final focused
validation passed 91 tests after the final architecture correction. Canonical
deployment regression passed `RC=0` and ran exactly once for PA-05. No
Production WooCommerce request, external commerce I/O, WordPress, WooCommerce,
Shopping SQLite, Docker, launchd, `runtime/current`, Caddy, Ubuntu, credential,
database, plugin, or theme mutation occurred.

Next production sprint: `SHOP-CMS-01 — WordPress + WooCommerce Runtime
Foundation`. It will establish the actual runtime, persistent-state, secret,
backup, health/readiness, manifest, and activation architecture before public
storefront exposure. The Production WordPress/WooCommerce runtime and public
storefront are not claimed available. No Notion synchronization is claimed.

## SHOP-CMS-01A — Runtime Foundation closeout

Status: **VALIDATED AND CLOSED**

Milestone: `SHOPPING_RUNTIME_FOUNDATION_VALIDATED`

The Mac mini M4 owns `shopping-runtime`; AIControlCenter remains the sole
Control Plane and retains ProductDraft lifecycle, product policy, AI
generation, recommendations, workflow, customer automation, analytics,
notification, authorization, governance, audit, orchestration, and deployment
control. WordPress remains CMS capability, WooCommerce remains the hosted
commerce-engine capability/provider-side record owner, and Ubuntu owns no
shopping or commerce state.

Canonical lifecycle: `shopping-runtime`, `docker-compose-on-colima`,
`supervisor=docker-compose`, `NOT_DEPLOYED`, `lifecycle=not_deployed`,
`owner=aicontrolcenter`, `ubuntu_dependency=false`,
`state_policy=mac-owned-docker-volumes`. Canonical capability: `woocommerce`,
host `shopping-runtime`, kind `wordpress-plugin-commerce-engine`,
`NOT_DEPLOYED`, `activation_authorized=false`.

Validation: 72 initial focused passes; canonical #1 `3151 passed, 2 failed, 5
deselected` due only to stale service-count assertions; corrected targeted 2
passed; focused compatibility 47 passed; canonical #2 `RC=0`; exactly two
canonical invocations. Direct core imports of outer `ops` and `integrations`
remain 0. No Production/runtime mutation occurred, and no runtime, service,
storefront, routing, activation, or Notion availability is claimed.

Next: `SHOP-CMS-01B — bounded Production runtime activation`, milestone
`SHOPPING_RUNTIME_ACTIVATED`. Future storefront milestone:
`SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## SHOP-CMS-01B — Activation-phase current state

Status: **CORRECTION VALIDATED; RUNTIME ACTIVATION NOT ACHIEVED**

The desired WordPress contract is loopback-only
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80` with port `58082`; MariaDB remains
unpublished. The inspector derives reserved Control Plane ports from the
canonical service manifest and reports `PortCollision` even for healthy
containers when WordPress publishes on a reserved port. It accepts bounded
Compose JSON array, object, NDJSON, and empty observations, rejects malformed/
scalar/non-object data fail-closed, and never equates container health with
WooCommerce readiness.

Exactly one authorized Colima start succeeded. Later read-only reconciliation
observed existing stored WordPress and MariaDB containers running/healthy
under restart policy and persistent volumes. This observation was not a new
Production mutation or an independently authorized Compose up. The existing
publisher remains on canonical FastAPI port `58081`; its REST 404 was FastAPI,
not WordPress. No cutover to `58082` has occurred, bootstrap secrets were not
present, and WooCommerce readiness has not been proven.

ServiceTopology and the WooCommerce capability remain `NOT_DEPLOYED`;
`SHOPPING_RUNTIME_ACTIVATED=false`. A desired-state package is not activation
authorization. Next is a separate human authorization for the exact WordPress
port cutover, followed by read-only reconciliation. WooCommerce bootstrap and
readiness are subsequent; `SHOP-STOREFRONT-01` remains after activation.
AIControlCenter remains the Control Plane, Host Caddy the only public edge,
and Ubuntu a stateless worker.
