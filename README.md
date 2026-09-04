# AIControlCenter

## SHOP-SERVICE-START-01B fixed source remediation boundary

The existing work item includes narrow controlled-non-production domain
remediation orchestration and a private, fixture-tested atomic implementation
fixed to the trusted runtime-cutover source and
`SHOPPING_WORDPRESS_PORT=58082`. The injectable domain orchestration preserves
consume-before-fresh-exact-revalidation ordering, atomic mutation, and read-only
post-validation for tests and future governed wiring. There is no durable live
authorization adapter: public `run()` accepts no caller authorization and
returns `LIVE_AUTHORIZATION_ADAPTER_UNAVAILABLE` without observation or
mutation. A caller-supplied fake or in-memory consumer is a test seam only, not
a live authority path. No public direct live mutation capability is exposed.

No live source mutation, authorization creation/consumption, WordPress runtime
mutation, Shopping activation, Production/Ubuntu access, or Notion sync
occurred. Secret values may be transiently UTF-8 validated/read for exact
byte-preserving transformation, but are not retained, emitted, logged, hashed,
or semantically compared. Source remediation and WordPress recreation require
separate human authorizations; no content-preservation or backup/restore claim
is created. Shopping remains inactive and Notion remains unsynced.

## SHOP-SERVICE-START-01B volume identity continuity

This existing work item now includes immutable, JSON-safe observations for the
two canonical Shopping volumes and a fixed-context macOS read-only adapter.
Continuity requires matching stable creation identity plus exact, unambiguous
Docker-volume attachment at `/var/lib/mysql` and `/var/www/html`; the name alone
is insufficient. Physical mountpoints and environment values are excluded.

`VOLUME_EXISTS != VOLUME_IDENTITY_CONTINUITY`;
`VOLUME_IDENTITY_CONTINUITY != CONTENT_PRESERVATION`;
`CONTENT_PRESERVATION != VERIFIED_BACKUP_RESTORE`; and
`SAFETY_EVIDENCE != AUTHORITY`. The adapter has not been used against live
Docker. Backup/restore and content preservation remain unproven, destructive
recovery remains unavailable, and no mutation, authorization, Production,
Ubuntu, live-secret access, or Notion sync occurred.

## SHOP-SERVICE-START-01B Broken-profile recovery policy

The authoritative work item now includes a repository-only pure profile-health
and recovery decision policy. Infrastructure `HEALTHY`, `BROKEN`, and `UNKNOWN`
remain separate from Shopping service state. Broken never becomes `STOPPED` or
selects start; Unknown selects no mutation. Only an existing healthy, stopped
profile with independent lifecycle-only proof may expose an unselected
`START_EXISTING_PROFILE_ONCE` candidate. The configuration-bearing
`--save-config` planner is not that proof.

`ai-shopping-wordpress` and `ai-shopping-database` remain protected persistent
state. Preservation and verified backup/restore evidence are safety facts, not
authority; neither is proven, and destructive recovery is unavailable. No
repair, recreation, live mutation, authorization,
runtime activation, Production/Ubuntu access, or Notion sync occurred.

`AUTHORITATIVE_WORK_ITEM=SHOP-SERVICE-START-01B`
`BROKEN_PROFILE_POLICY=IMPLEMENTED`
`BROKEN_NORMALIZES_TO_STOPPED=NO`
`BROKEN_AUTOMATIC_START=NO`
`STORAGE_PROTECTION_EVIDENCE_IS_AUTHORITY=NO`
`REPAIR_EXECUTOR_IMPLEMENTED=NO`
`RECREATE_EXECUTOR_IMPLEMENTED=NO`
`DESTRUCTIVE_RECOVERY_AVAILABLE=NO`
`STORAGE_PRESERVATION_PROVEN=NO`
`MUTATION_SELECTED=NO`
`MUTATION_EXECUTED=NO`
`SHOPPING_RUNTIME_ACTIVATED=NO`
`NOTION_SYNC=NO`


## Runtime-cutover secret source authority

Within the existing authoritative `SHOP-SERVICE-START-01B` work item, the
repository now owns a fixed, read-only source contract at trusted Darwin passwd
home + `Library/Application Support/AIControlCenter/secrets/shopping-commerce.env`.
The prior live metadata observation informed the portable suffix but supplied
no authority. Descriptor-relative no-follow checks enforce the canonical safe
parent chain and a regular, non-empty, trusted UID/GID file with mode no broader
than `0600`; the bounded observer emits only canonical `runtime_cutover`
key-name presence from
`deploy/shopping/config/secret-contract.json`.

No new Work Unit, caller path override, executor, cutover, authorization,
materialization, or runtime mutation was added. The implementation bundle did
not access the live source, and repository tests used fixtures. A later bounded
live read-only preflight accessed and parsed the source value-blind; no secret
value was inspected, serialized, emitted, logged, hashed, compared, or exposed.

`SOURCE_READY=YES`
`SOURCE_REASON=READY`
`SECRET_SOURCE_ACCESSED=YES`
`SECRET_CONTENT_PARSED_VALUE_BLIND=YES`
`SECRET_VALUES_EMITTED=NO`
`SECRET_VALUES_LOGGED=NO`
`SECRET_VALUES_HASHED=NO`

SOPS/age remains `NOT_DEPLOYED`,
`materialization_implemented=false`, WordPress remains conflicting, and
`SHOPPING_RUNTIME_ACTIVATED=NO`. No Notion synchronization is claimed.

## Current work boundary

`SHOP-SERVICE-START-01A=CLOSED`. Its read-only scope—architecture discovery,
observer contracts, live adapter, typed diagnostics, and bounded observation—is
complete. Evidence remains unresolved, no service-start decision is ready, and
Shopping is not activated.

The next authoritative work is `SHOP-SERVICE-START-01B`, a
`CONTROLLED_NON_PRODUCTION_RUNTIME_GOVERNANCE` boundary. It does not authorize
mutation. It resolves dependency layers in order using fresh credential-blind,
fail-closed evidence, then permits at most one separately human-approved,
predetermined mutation followed immediately by read-only reconciliation.
Candidates are Colima profile create/start, Docker context create/select, and
Shopping Compose provision/start; none is selected and the decision remains
`MUTATION_UNDETERMINED`.

The Mac mini M4 and AIControlCenter remain the sole Control Plane. The future
executor must be Mac-only, one-use, fixed-invocation, structured-JSON, no-retry,
and no-automatic-rollback, with fresh preconditions and reconciliation. It may
not accept arbitrary commands/argv, access Ubuntu, gain Production authority,
silently read secrets, or combine multiple runtime-layer mutations in one
approval. Runtime availability resolution needs no secrets or MariaDB login.

Canonical runtime identities are Colima `aicontrolcenter-commerce`, Docker
context `colima-aicontrolcenter-commerce`, and Compose project `ai-shopping`.
The observer base remains `127.0.0.1:58081`; desired WordPress is
`127.0.0.1:58082`. `127.0.0.1:8000` and `bokstory.iptime.org:58088` are
historical unless separately revalidated. Production WU09, `SHOP-CMS-01B`, and
Apple external signing remain outside this path.

## Closed work boundary — SHOP-SERVICE-START-01A

`SHOP-SERVICE-START-01A` includes a Mac-only, credential-blind live adapter
that reuses the existing runtime inspector and six-state aggregation model.
Valid repository-defined HTTP non-healthy responses produce complete unhealthy
evidence; malformed schemas remain unknown. Safe typed diagnostics distinguish
runtime inspection failures without exposing raw output or HTTP bodies.
Focused validation passed with `55 passed`; architecture, security, diff, and
final code reviews passed. Canonical
`ops/macos/validation/run-deployment-regression-gate.sh -q` ran exactly once,
invocation `1135d3cd1b8546c7a064a462fd420726`, and passed with `4573 passed,
5 deselected, 463 warnings, 2 subtests passed in 466.83s (0:07:46)` at
`/private/tmp/aicontrolcenter-canonical-evidence.0Q7FTA`.

The one bounded `CONTROLLED_NON_PRODUCTION` Mac observation classified all six
Shopping components and overall as `UNKNOWN`. No repository desired state was
claimed as live state, and WooCommerce was observed independently. No
Production access or mutation, authorization consumption, secret read,
MariaDB authentication, SQL, automatic retry, Ubuntu access, or activation
occurred. `SHOPPING_RUNTIME_ACTIVATED=NO`; no mutation target is supported
until fresh evidence resolves the unknown runtime state.
MariaDB and WordPress reported `runtime_unavailable`; WooCommerce,
AIControlCenter Shopping, Dashboard, and Homepage reported
`loopback_http_unavailable`.

`READ_ONLY_OBSERVER_IMPLEMENTED=YES`
`LIVE_OBSERVATION_PERFORMED=YES`
`LIVE_EVIDENCE_RESOLVED=NO`
`SERVICE_START_DECISION_READY=NO`

`WU09_PRODUCTION_PATH=BLOCKED`
`PRODUCTION_AUTHORITY_BYPASS=FORBIDDEN`
`APPLE_SIGNING_STREAM=DEFERRED`
`SHOPPING_RUNTIME_ACTIVATED=NO`
`MARIADB_CONTINUITY_STATE=UNRESOLVED`
`SERVICE_START_PLANNING=ACTIVE`
`EXISTING_REUSABLE_RUNTIME_BOUNDARY=CONTROLLED_NON_PRODUCTION`
`AUTHORITATIVE_NEXT_WORK=SHOP-SERVICE-START-01B`
`NEXT_WORK_KIND=CONTROLLED_NON_PRODUCTION_RUNTIME_GOVERNANCE`

## Current authoritative — WU09 Production composition ready

`WU09_PINNED_IMAGE_PRELOAD_PRODUCTION_COMPOSITION_READY=COMPLETE`. The Mac-only
composition root validates the existing trusted WU09 authorization facts,
complete immutable precondition snapshot, and signed Mac operator identity
before assembling the existing SEC-02 coordinator, deferred
`AuthorizationConsumptionPort`, exact pinned-image `ControlledExecutionPort`,
and bounded read-only observers. Composition performs no durable store
initialization, authorization consumption, Docker/Colima probe, image preload,
adapter deployment, credential provisioning, or Production mutation. The Mac
mini M4 remains the sole Control Plane; Ubuntu remains stateless. The next
existing boundary is separately authorized `WU09_PINNED_IMAGE_PRELOADED`.

## Current authoritative — C5A operator metadata entrypoint validated

Commit `8a0836f` connects the operator to the real C5A issuer,
`SEC02ProductionSigningCredentialCeremony.validateExplicitPathForFutureImport(...)`,
establishing `C5A_OPERATOR_METADATA_VALIDATION_ENTRYPOINT_VALIDATED`. Only
`validation.observation` is JSON. Opaque `SEC02ValidatedCredentialInputEvidence`
is non-Codable, non-serialized, non-persisted, process-local, and non-reusable
as Production authority. No credential content, passphrase, import, Keychain
mutation, or Production mutation is involved.

Operator metadata success is not reusable C5A evidence, C5B authorization,
import success, a Production signing identity, authoritative Team ID, signing
authority, or Production authority. A separately authorized live C5B ceremony
must run fresh C5A validation and immediately consume its opaque evidence in the
same native process, followed by durable C5B success, read-only C6A, and
mandatory read-only C4. C4 alone verifies the live Developer ID Application and
supplies authoritative Team ID.

Validation passed: focused `4 passed, 268 warnings in 50.19s`; compatibility
`9 passed, 268 warnings in 34.69s`; architecture, security, diff, and canonical
gates `PASS`. Canonical invocation `a0aa6bdb2e3e48f785cfa9113fd7e332` recorded
`4504 passed, 5 deselected, 723 warnings, 2 subtests passed in 464.81s (0:07:44)`
and is not rerun. Live signing readiness remains `NOT_READY`.

## Current authoritative — SEC02-FS-MACRO-03B4R2-C6A validated

Commit `e9cb294` (`feat: add production signing credential availability
observer`) completed the Mac-only, read-only Production signing credential
availability observation coordinator. Milestone:
`PRODUCTION_SIGNING_CREDENTIAL_AVAILABILITY_OBSERVATION_FOUNDATION_VALIDATED`.
C6A observes established C5A credential-input evidence and C5B import result
state; it creates neither and may progress to the sole-authoritative C4 local
Keychain verifier only from `SUCCEEDED_PENDING_C4_VERIFICATION`.

The observation states are `EXTERNAL_CREDENTIAL_REQUIRED`,
`LOCAL_INPUT_METADATA_READY`, `IMPORT_REQUIRED`,
`IDENTITY_VERIFICATION_REQUIRED`, and
`PRODUCTION_SIGNING_IDENTITY_VERIFIED`. Before C4 produces an authoritative Team
ID, JSON explicitly serializes `authoritative_team_id` as `null`. The contract
is not Production authority. `ATTEMPTING`, `FAILED_CONSUMED`, and
`UNCERTAIN_CONSUMED` never open C4 progression; consumed failure and uncertainty
are terminal and never automatically retried. C4 alone verifies the live
Developer ID Application identity and derives the authoritative Team ID.

C6A reads no credential contents, handles no passphrases, imports nothing,
mutates no Keychain, signs or notarizes nothing, registers no `SMAppService`,
performs no Production mutation, and grants no Production authority. Focused
C6A tests `4 passed`; C4/C5A/C5B compatibility tests `16 passed`; architecture,
security, diff, and canonical validation `PASS`. Canonical invocation
`7f0b4913e9c6493e972a6a8bdf1b5af8` recorded `4499 passed, 5 deselected, 703
warnings, 2 subtests passed in 446.30s (0:07:26)` at
`/private/tmp/aicontrolcenter-canonical-evidence.WwxhL9`; it is not rerun for
documentation closeout.

`WU=SEC02-FS-MACRO-03B4R2-C6A`
`C6A_IMPLEMENTATION=COMPLETE`
`C6A_FOCUSED_TESTS=PASS`
`C6A_ARCHITECTURE_REVIEW=PASS`
`C6A_SECURITY_REVIEW=PASS`
`C6A_CANONICAL=PASS`
`C6A_DOCUMENTATION=COMPLETE`
`LIVE_DEVELOPER_ID_APPLICATION_STATE=ABSENT`
`AUTHORITATIVE_TEAM_ID_AVAILABLE=NO`
`PRODUCTION_SIGNING_IDENTITY_VERIFIED=NO`
`SIGNED_PACKAGE_READY=NO`
`LIVE_SIGNING_READINESS=NOT_READY`
`SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`

## Current authoritative — SEC02-FS-MACRO-03B4R2-C5B validated

Commit `343ecd6` validated the repository-only future Mac-only Production
signing credential import ceremony foundation, establishing
`PRODUCTION_SIGNING_CREDENTIAL_IMPORT_CEREMONY_FOUNDATION_VALIDATED`. No real
credential import, Keychain mutation, signing, notarization, registration, or
Production mutation exists.

C5A validated evidence is required before `READY`; a raw path or fingerprint
alone is insufficient. Consumption is durably claimed before at most one
bounded importer attempt. The lifecycle is `NOT_STARTED`, `READY`, `ATTEMPTING`,
`SUCCEEDED_PENDING_C4_VERIFICATION`, `FAILED_CONSUMED`, and
`UNCERTAIN_CONSUMED`; the consumed failure/uncertainty states are terminal.
Invalid or ambiguous consumed nonterminal state fails closed to uncertainty
without importer or secret-mediation calls. Reconstruction cannot replay an
import. Success grants no Production authority and opens only read-only C4
verification.

Only real Darwin validation issues authoritative evidence; injected inspectors
cannot. Secrets remain opaque and are never persisted, logged, passed through
argv/environment/configuration/Git, or exposed as `String`/`Data`. Canonical
evidence is `4495 passed, 5 deselected, 703 warnings, 2 subtests passed in
429.53s (0:07:09)`, invocation `08f9b94830e741058c6147274d76e0ff`; it is not
rerun for documentation closeout.

`SEC02_FS_MACRO_03B4R2_C5B_IMPLEMENTATION=COMPLETE`
`PRODUCTION_SIGNING_CREDENTIAL_IMPORT_CEREMONY_FOUNDATION_VALIDATED=YES`
`RECONSTRUCTED_SUCCESS_REQUIRES_C4=YES`
`UNCERTAIN_STATE_OPENS_C4_PROGRESSION=NO`
`PRODUCTION_SIGNING_IDENTITY_VERIFIED=NO`
`PRODUCTION_AUTHORITY_GRANTED=NO`
`CANONICAL_RERUN_REQUIRED=NO`

## Current authoritative — SEC02-FS-MACRO-03B4R2-C5A validated

Commit `ef0df21` (`feat: validate SEC-02 signing credential ceremony`) completed
and validated the read-only, metadata-only Production signing credential
ceremony foundation. Milestone:
`PRODUCTION_SIGNING_CREDENTIAL_CEREMONY_FOUNDATION_VALIDATED`. The foundation
requires an explicit absolute `.p12` or `.pfx` path, rejects lexical dot
components and symlink traversal, uses descriptor-relative `openat` plus
`O_NOFOLLOW`, and requires a regular, invoking-user-owned leaf with safe mode
bits and stable device/inode binding. It never reads credential contents.

Absent input requires an external credential; valid local metadata is ready
only for a separate import ceremony; invalid input is not ready. No credential
was acquired or imported, no passphrase was accepted through argv/environment
or persisted/logged, and no Keychain mutation, signing, notarization,
registration, or Production mutation occurred. A future Mac-only import requires
one explicit human ceremony and one bounded attempt, with no retry or credential
reuse after `FAILED`/`UNCERTAIN`. Successful import still requires the C4
verifier; only that verifier may establish the authoritative Team ID and
Production signing identity.

Evidence: focused `3 passed, 228 warnings`; canonical `4466 passed, 5
deselected, 675 warnings`; final architecture/security review `PASS`; `git diff
--check` `PASS`. The implementation commit was pushed clean and synchronized.
Canonical is not rerun for this documentation-only closeout.

`SEC02_FS_MACRO_03B4R2_C5A_IMPLEMENTATION=COMPLETE`
`SEC02_FS_MACRO_03B4R2_C5A_TEST=PASS`
`PRODUCTION_SIGNING_CREDENTIAL_CEREMONY_FOUNDATION_VALIDATED=YES`
`C5A_DOCUMENTATION_PREPARED=YES`
`LIVE_DEVELOPER_ID_APPLICATION_STATE=ABSENT`
`AUTHORITATIVE_TEAM_ID_AVAILABLE=NO`
`PRODUCTION_SIGNING_IDENTITY_VERIFIED=NO`
`SIGNED_PACKAGE_READY=NO`
`LIVE_SIGNING_READINESS=NOT_READY`
`SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`
`CANONICAL_RERUN_REQUIRED=NO`

## Current authoritative — SEC02-FS-MACRO-03B4R2-C4 verifier validated

Commit `1cf8648` (`feat: validate SEC-02 production signing identity`) completed
and validated the read-only Production signing identity verifier. Milestone:
`PRODUCTION_SIGNING_IDENTITY_VERIFIER_VALIDATED`. Security.framework is primary;
the narrow `/usr/bin/security` fallback can prove only exact zero-identity
absence and can never produce readiness, a candidate, or a Team ID. Exactly one
fully qualified verified Developer ID Application credential is required for an
authoritative Team ID. Multiple qualified valid candidates are ambiguous;
rejected observations do not create ambiguity. Private-key usability is only
capability evidence.

The verifier performs no signing or credential persistence and causes zero
Keychain and Production mutation. `LAContext.interactionNotAllowed=true`; no
pre-authenticated context or `evaluatePolicy()` is used. Evidence: focused C4
`8 passed`; native Swift type-check `PASS`, zero warnings; ambiguity semantics
validated; deprecated authentication-UI keys absent; canonical `4463 passed, 5
deselected, 675 warnings`. Canonical was not rerun for this documentation-only
closeout.

Readiness remains seven separate stages: C2 source/toolchain compatibility; C3
real unsigned package validation; C4 verifier validation; actual Production
identity verification; signed-package readiness; `SMAppService` registration;
and Production remediation / 03B5 readiness. Only the first three are complete.

`SEC02_FS_MACRO_03B4R2_C4_IMPLEMENTATION=COMPLETE`
`PRODUCTION_SIGNING_IDENTITY_VERIFIER_IMPLEMENTED=YES`
`PRODUCTION_SIGNING_IDENTITY_VERIFIER_VALIDATED=YES`
`LIVE_DEVELOPER_ID_APPLICATION_STATE=ABSENT`
`AUTHORITATIVE_TEAM_ID_AVAILABLE=NO`
`PRODUCTION_SIGNING_IDENTITY_VERIFIED=NO`
`SIGNED_PACKAGE_READY=NO`
`LIVE_SIGNING_READINESS=NOT_READY`
`SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`
`CANONICAL_RERUN_REQUIRED=NO`

## Current authoritative — SEC02-FS-MACRO-03B4R2-C3 complete

Commit `85b9e32` (`feat: build unsigned SEC-02 native package`) completed and
validated the C3 repository work. `AIControlCenter` and
`SEC02GovernanceRemediationHelper` are real, non-empty arm64 thin Mach-O
executables in the exact package allowlist. The helper embeds validated bundle
metadata, explicitly retains its XPC delegate, and binds the unresolved signing
requirement to each incoming connection before resume. Neither executable has
`LC_CODE_SIGNATURE`; linker ad-hoc signing is disabled and no signing occurred.
Milestone: `SEC02_UNSIGNED_NATIVE_PACKAGE_VALIDATED`.

C2's source type-check evidence and synthetic temporary layout validation remain
historical, distinct milestones. C3 proves a real unsigned native executable
and package, not a signed package, universal/fat binary validation, bit-for-bit
reproducibility, registration, trusted-issuer operation, or live Production
readiness. Implementation evidence: focused `22 passed`; canonical `4455
passed, 5 deselected, 659 warnings`.

`DEVELOPER_ID_APPLICATION_AVAILABLE=NO`
`AUTHORITATIVE_TEAM_ID_AVAILABLE=NO`
`SIGNED_PACKAGE_READY=NO`
`LIVE_SIGNING_READINESS=NOT_READY`
`SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO`
`SEC02_TRUSTED_ISSUER_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`
`FULL_XCODE_ESTABLISHED=NO`

## Current authoritative — SEC02-FS-MACRO-03B4R2-C2 current state

`NativeFoundation.swift` now type-checks with the selected Command Line Tools
developer directory `/Library/Developer/CommandLineTools`, Apple Swift `6.3.3`,
and macOS SDK `26.5`: `NATIVE_TYPECHECK_RC=0`,
`NATIVE_TOOLCHAIN_COMPATIBLE=YES`, and
`SECURE_ENCLAVE_PROVISIONER_TYPECHECKED=YES`. The implementation correction is
commit `51e9a96` (`fix: compile SEC-02 native signing flags`); the canonical
deployment regression is `4449 passed, 5 deselected, 651 warnings`.

This is source/toolchain compatibility only. Full Xcode is not established.
Code-signing discovery found `0 valid identities`; Developer ID Application is
absent (count `0`), the user keychain search list contains only
`login.keychain-db`, and the authoritative Team ID remains unresolved. The
signed native package is not ready. No `SMAppService` registration, live
fresh-human approval, or governance remediation was performed, and the SEC-02
trusted issuer is not operational. Mac remains the sole Control Plane; signing
readiness grants no Production mutation authority, every bounded Production
mutation still requires one fresh human authorization, and Ubuntu receives no
authority. `READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

Current SEC-02 source hardening requires static code validity before signing
metadata, exact native/Python algorithm-ID agreement, and exact-one Secure
Enclave key recognition with absence-only future creation. Public-key identity
is SHA-256 over the ANSI X9.63 uncompressed P-256 public representation and is
64 lowercase hex; journal receipt replay identity has the same strict shape.
The package script validates only a temporary placeholder layout—not executable
build, signing, registration, or operational readiness. The two helper methods
remain explicit and mutually authority-separated. No live key, identity,
authentication, helper, journal, registration, or Production operation exists.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

Current SEC-02 status: the fresh-human-evidence foundation is implemented in the
repository but is not operational. It selects Secure Enclave P-256 user-presence
signing, binds approval to the exact request and `AuthorizationReplayKey`, and
requires verification before the durable one-attempt claim. The composite path
separately requires a valid bounded Authorization Services right; its success is
not fresh-human proof, while fresh-human evidence grants no execution authority.
Neither gate creates attempt authority. Only after both gates and the durable
claim succeed is the exact attempt created as claimed for one helper call. No live key,
authentication, privileged helper, or Production remediation is available. See
[`SEC-02-FRESH-HUMAN-EVIDENCE.md`](docs/architecture/SEC-02-FRESH-HUMAN-EVIDENCE.md).

## Current authoritative — SEC02-FS-MACRO-03B4R2-A foundation closed

The repository now contains non-deployable app/helper/LaunchDaemon templates,
fail-closed mutual signing configuration, a type-checked native replay digest,
and an exact create-only journal provisioning contract. No concrete bundle IDs,
Team ID, Mach service, or signing identity were invented. Full Xcode, live
signing, fresh-human evidence, Production journal/helper operation, and
Production remediation remain unavailable.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

## Current authoritative — SEC02-FS-MACRO-03B4R readiness closed

Architecture contracts exist. The earlier toolchain-compatibility blocker is
resolved for native source type-check only; signing identities, signed
app/helper packaging, concrete mutual requirements, live fresh-human proof,
journal provisioning, and helper operation remain blocked. The
journal-provisioning authority is defined only.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

## Current authoritative — SEC02-FS-MACRO-03B3 durable journal closed

The distinct pre-bootstrap remediation attempt journal is repository implemented
and temporary-path validated. A purpose/version-bound SQLite claim commits before
the fake helper call; claimed and every terminal state permanently deny replay.
The journal stores no authorization capability and does not reuse ordinary
SEC-02 consumption. The future Production path is frozen but not provisioned.

`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_DEFINED=YES`
`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_REPOSITORY_IMPLEMENTED=YES`
`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_OPERATIONAL=NO`
`DURABLE_CLAIM_PRECEDES_HELPER_ATTEMPT=YES`
`AUTHORIZATION_EXTERNAL_FORM_PERSISTED=NO`
`REPLAY_FINGERPRINT_CRYPTO_CONTRACT_DEFINED=YES`
`REPLAY_FINGERPRINT_OPERATIONALLY_VALIDATED=NO`
`JOURNAL_PROVISIONING_AUTHORITY_READY=NO`
`DURABLE_CRASH_SAFE_CONSUMPTION_OPERATIONAL=NO`
`LIVE_FRESH_APPROVAL_VERIFICATION_READY=NO`
`LIVE_PRIVILEGED_HELPER_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`

## Current authoritative — SEC02-FS-MACRO-03B2 foundation closed

The narrow governance remediation now has a pre-authorization exact-eligibility
gate, a one-operation XPC contract, mandatory fail-closed peer code-signing
policy, and a macOS 13+ bundled LaunchDaemon package contract. No signing identity
or native app bundle is asserted, no external authorization form is persisted or
represented as application state, and no live authorization/helper path exists.

`PRE_AUTHORIZATION_ELIGIBILITY_GATE=YES`
`INELIGIBLE_PLAN_MAY_TRIGGER_AUTHORIZATION=NO`
`AUTHORIZATION_EXTERNAL_FORM_EPHEMERAL_ONLY=YES`
`AUTHORIZATION_EXTERNAL_FORM_PERSISTENCE_ALLOWED=NO`
`XPC_PEER_CODE_SIGNING_POLICY_DEFINED=YES`
`SMAPPSERVICE_PACKAGE_FOUNDATION=YES`
`LIVE_FRESH_APPROVAL_VERIFICATION_READY=NO`
`DURABLE_CRASH_SAFE_CONSUMPTION_OPERATIONAL=NO`
`LIVE_AUTHORIZATION_SERVICES_OPERATIONAL=NO`
`LIVE_PRIVILEGED_HELPER_OPERATIONAL=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`

## Current authoritative — SEC02-AR-01 anti-rollback receipt architecture closed

The exact receipt schema, P-256/SHA-256 Secure Enclave signing architecture,
non-exportable installation-authority key custody, fixed Mac-local storage,
atomic full-sync journal, monotonic version rules, and fail-closed read-only
reconciliation are frozen in
`docs/architecture/SEC-02-RELEASE-INSTALL-ANTI-ROLLBACK-AUTHORITY-FREEZE.md`.
The receipt is evidence, never authority. The existing external Continuity
Witness supplies non-circular durable history and remains evidence-only; Mac
mini M4 remains the sole Control Plane and Ubuntu remains zero-authority.

`ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES`

`ANTI_ROLLBACK_RECEIPT_IMPLEMENTED=NO`

`ANTI_ROLLBACK_RECEIPT_OPERATIONALLY_VALIDATED=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`CANONICAL_RERUN_REQUIRED=NO`

## Current authoritative — SEC-02 Continuity Witness repository foundation closed

The repository-only foundation is complete: WU-01 Domain/Contract foundation
and WU-02 Port/authority boundary foundation closed at
`5bcaecd05eef403ce2fbc34e97605cccabe37316`; WU-03 Lifecycle state machine/fake
adapter foundation closed at
`a9a511fdf116a4c8f37712b170a0400ea0d7d658`. The validated focused suite passed
`65 tests`. Canonical regression was not rerun for this docs-only reconciliation
and no new canonical PASS is claimed.

The foundation enforces these validated semantics: a durable claim binds the
exact `expected_transition_intent_digest`; Stage B rejects intent substitution
before lifecycle planning or mutation; and a rejected durable claim remains
consumed and non-reusable. `version_maxima` is defensively copied and immutable,
with non-empty string keys and exact non-negative integer values. GENESIS
requires complete verified historical absence, while immutable history remains
evidence only. RECOVERY preserves host identity and enrollment generation with
nondecreasing maxima. DECOMMISSION requires no fresh MDA and is terminal.
MIGRATION is one operation containing exactly two ordered transitions.
Ambiguous external result creates no mutation-retry authority, and DB
`COMMITTED` without exact checkpoint proof is `UNCERTAIN_CONSUMED`.

The Mac mini M4 remains the sole Control Plane. Continuity Witness is not a
second Control Plane, and Ubuntu has zero Continuity Witness implementation
authority. This closes repository-foundation work only; operational/cloud
implementation remains a separate planned security track.

`SEC02_REPOSITORY_FOUNDATION=COMPLETE`

`WU_01_DOMAIN_CONTRACT_FOUNDATION=COMPLETE`

`WU_02_PORT_AUTHORITY_BOUNDARY_FOUNDATION=COMPLETE`

`WU_03_LIFECYCLE_STATE_MACHINE_FAKE_ADAPTER_FOUNDATION=COMPLETE`

`WU_03_IMPLEMENTATION_COMMIT=a9a511fdf116a4c8f37712b170a0400ea0d7d658`

`FOCUSED_VALIDATION=65_TESTS_PASSED`

`CONTINUITY_WITNESS_IMPLEMENTED=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`AWS_DEPLOYMENT_PERFORMED=NO`

`MDM_IMPLEMENTED=NO`

`PRODUCTION_MUTATION_PERFORMED=false`

`NEXT_PRODUCTION_MILESTONE=SHOPPING_RUNTIME_ACTIVATED_AND_HOMEPAGE_SERVICE_VALIDATED`

Service dependency chain: `SM-01B` -> Shopping runtime activation -> MariaDB +
WordPress runtime validation -> WooCommerce runtime validation ->
AIControlCenter Shopping integration -> Homepage live service validation.

`CANONICAL_RERUN_REQUIRED=NO`

## Current authoritative — SEC-02 Continuity Witness implementation definition frozen

`SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_DEFINITION_ARCHITECTURE_FROZEN=YES`

`ARCHITECTURE_COMMIT=54268cf`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=YES`

`CONTINUITY_WITNESS_IMPLEMENTED=NO`

Commit `54268cf` freezes the repository implementation definition: exact JSON
contracts, transaction and approval-claim semantics, immutable-history lookup,
checkpoint canonicalization, cryptographic and MDA adapter boundaries, closed
classifications, and deterministic fake/test strategy. It implements and
deploys nothing.

Human Lifecycle Approval binds pre-mutation intent only:

`expected_transition_intent_digest = SHA-256(RFC8785_JCS(TransitionIntent))`

Stage-B `resulting_transition_digests` are output evidence only. The checkpoint
digest chain is exact and non-circular:

`CheckpointPayload -> application_payload_digest -> WitnessCheckpointSigningEnvelope -> StoredCheckpoint -> object_digest`

`object_digest` is not embedded in the `StoredCheckpoint` it hashes. Immutable
history lookup is version-aware; a delete marker or latest-key 404 proves
neither history absence nor GENESIS.

The Mac mini M4 remains the sole Control Plane. The Continuity Witness owns
external durable evidence only and is not a second Control Plane. Ubuntu is a
stateless infrastructure worker with zero authority. DECOMMISSION retains the
`41e9f4f` precedence: no fresh MDA, one exact Human Lifecycle Approval bound to
the current evaluation and record, and a terminal result.

`KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTED=NO`

`CONTINUITY_WITNESS_CLOUD_HOST_SELECTED=NO`

`CONTINUITY_WITNESS_INGRESS_TOPOLOGY_DEFINED=NO`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`SEC02_SEMANTICS_CHANGED=false`

`GOVERNANCE_CORE_CHANGED=false`

`CONTROLLED_EXECUTION_PORT_CHANGED=false`

`WU09_FILES_CHANGED=false`

`CANONICAL_RERUN_REQUIRED=NO`

## Prior authoritative — SEC-02 Witness deployment/key-custody architecture frozen

`SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_ARCHITECTURE_FROZEN=YES`

`SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_FREEZE=COMPLETE`

`ARCHITECTURE_COMMIT=7057c96`

This architecture-only milestone selects AWS for a stateless external Witness,
a PostgreSQL-compatible primary datastore, S3 Object Lock Compliance immutable
history, AWS KMS signing custody, and AWS KMS HMAC privacy-index custody. It
does not select an operational AWS account, region, concrete host, ingress, or
resource, and claims no implementation, deployment, or operational validation.

`CONTINUITY_WITNESS_DEPLOYMENT_ARCHITECTURE_DEFINED=YES`

`KEY_CUSTODY_ARCHITECTURE_DEFINED=YES`

`CONTINUITY_WITNESS_CLOUD_PROVIDER=AWS`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO`

`KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTED=NO`

`MDM_VENDOR_SELECTED=NO`

`CONTINUITY_WITNESS_CLOUD_HOST_SELECTED=NO`

`CONTINUITY_WITNESS_INGRESS_TOPOLOGY_DEFINED=NO`

`IMPLEMENTATION_READY=NO`

`FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO`

`SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY`

`BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

PostgreSQL rollback, retention expiry, and missing or incomplete immutable
history cannot establish historical absence or unseen hardware; unavailable or
conflicting immutable history fails closed. No operational S3 bucket or
retention schedule is implemented. Hardware lookup uses versioned RFC 8785 JCS
with separate UDID and serial fields and AWS KMS HMAC-SHA-256; raw identifiers
are not durable external identifiers, unkeyed hashing is prohibited, and key
ambiguity must never make hardware appear unseen.

Witness and human lifecycle signing use separate non-exportable AWS KMS
Ed25519 keys and distinct purpose domains. Only a human principal may sign
lifecycle approvals. Signed envelopes use RFC 8785 JCS, strict unpadded
base64url, schema and domain binding, no floats, a 4096-byte canonical maximum,
and payload-digest binding; Ed25519ph is not selected.

DECOMMISSION follows lifecycle authority commit `41e9f4f`: one exact Human
Continuity Lifecycle Approval bound to the current evaluation and record, no
fresh MDA, and a terminal result. Commit `96db578`'s conflicting fresh-identity
wording is a non-authoritative documentation overconstraint erratum corrected
by `7057c96`. GENESIS, RECOVERY, and MIGRATION rules are unchanged and
`SEC02_SEMANTICS_CHANGED=false`.

Durably claimed approvals remain permanently consumed; claim stealing,
automatic recovery, and retries are prohibited. Ambiguous commit acknowledgement
allows read-only exact-result reconciliation only. The Mac mini M4 remains the
sole Control Plane, the Witness owns external durable evidence only, and Ubuntu
remains a stateless worker with zero authority.

`NEXT_SPRINT=SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_DEFINITION`

`NEXT_SPRINT_STATUS=PLANNED_NOT_STARTED`

The next sprint defines contracts, schemas, protocols, adapters, fail-closed
validation, and tests only; it does not deploy or activate Production.

## Prior authoritative milestone — SEC-02 Witness implementation/crypto architecture frozen

`SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_CRYPTO_ARCHITECTURE_FROZEN=YES`

`SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_CRYPTO_FREEZE=COMPLETE`

`ARCHITECTURE_COMMIT=96db578`

This is an architecture-only milestone. DeviceInformation is the selected MDA
transport architecture, lifecycle approvals are permanently consumed upon
`AVAILABLE -> DURABLY_CLAIMED`, ambiguous COMMIT outcomes permit read-only
exact-result reconciliation only, and separate Ed25519 keys are required for
Witness and lifecycle-approval signing. Implementation, key custody, cloud
hosting, Witness ingress, MDM configuration, operational validation, and
Production bootstrap remain undefined or unavailable.

`FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO`

`KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

The Mac mini M4 remains the sole Control Plane. The external Continuity Witness
is durable evidence authority only, not a second Control Plane; Ubuntu remains
a stateless infrastructure worker with zero authority. That milestone was
followed by the deployment/key-custody architecture freeze at `7057c96`.

## Current authoritative — generic SEC-02 trusted human authorization intake validated

`SEC02_TRUSTED_AUTHORIZATION_INTAKE_VALIDATED` is complete at
`IMPLEMENTATION_COMMIT=349a9c5`. The canonical deployment regression gate
passed with `4212 passed, 5 deselected, 599 warnings` and `CANONICAL_RC=0`.

This is reusable SEC-02 infrastructure, not WU09-specific. A human issuer
creates an immutable signed authorization artifact; generic trusted intake
verifies it before the existing SEC-02 boundary and a feature-specific
`ControlledExecutionPort`. Issuer, Intake, Operator, and Executor remain
distinct. Authenticity and durable authorization consumption are evidence, not
execution authority: fresh post-consumption preconditions and an independent
SEC-02 `ALLOW_SINGLE_INVOCATION` decision remain mandatory. There is no retry,
consumed-authorization reuse, claim stealing, or stranded-claim recovery.

Production runtime stores only public verification material and trusted issuer
metadata. No Production private signing-key API or generic Production executor
was introduced; synthetic private keys remain tests/fixtures only. Mac operator
identity is derived from Darwin/passwd-record-backed local identity rather than
caller-supplied text, environment, argv, or JSON authority, and trust-root path
handling fails closed. The Mac mini M4 remains the sole Control Plane; Ubuntu
remains a stateless infrastructure worker with zero trust, intake, governance,
or execution authority.

This validation did not activate operational trust roots, Production runtime,
or Shopping. `WU09_PINNED_IMAGE_PRELOADED=false`, `WU09_DEPLOYED=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`; no Production access, mutation,
authorization consumption, Docker operation, or WU09 implementation change
occurred.

## Current authoritative — Macro-WU09 governance identity binding correction

`WU09_IDENTITY_BINDING_CORRECTION=COMPLETE` at
`IDENTITY_BINDING_CORRECTION_COMMIT=9e7a4a2`, after the initial preload
implementation at `IMPLEMENTATION_COMMIT=e179fb0`. The correction changed
exactly `ops/macos/shopping/wu09_image_preload.py` and
`tests/test_macro_wu09_pinned_image_preload.py`.

`GovernanceIdentity` semantics are now explicitly keyword-bound. Requester is
`identity_id=<requester identity>` with `identity_type=HUMAN`; approver is
`identity_id=<approver identity>` with `identity_type=HUMAN`; the Mac Control
Plane collector/target is `identity_id=MAC_MINI_M4` with
`identity_type=CONTROL_PLANE`.

Authoritative validation is `CANONICAL_GATE=PASS`,
`CANONICAL_RESULT=4130_PASSED_5_DESELECTED`, `CANONICAL_WARNINGS=587`, and
`CANONICAL_RC=0`. This closeout did not run canonical.

The correction preserves `GOVERNANCE_IDENTITY_DOMAIN_CHANGED=false`,
`GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`. It remains implementation
only: `WU09_PRELOAD_EXECUTED=false`, `WU09_DEPLOYED=false`,
`WU09_DEPLOYMENT_AUTHORIZED=false`, `WU10_AUTHORIZED=false`, and
`WU11_AUTHORIZED=false`.

`WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`,
`TRUSTED_SEC02_PRODUCTION_HUMAN_ISSUER_EXISTS=false`,
`TRUSTED_AUTHORIZATION_ARTIFACT_BOUNDARY_REQUIRED=true`, and
`PRODUCTION_COMPOSITION_READY=false`. The pinned image is not claimed to be
present in Production. `WU09_TRUSTED_PRODUCTION_AUTHORIZATION_INTAKE_FREEZE`
is complete as a validation-only exact-binding layer over generic SEC-02
trusted intake. It does not consume authorization or grant execution, retry,
rollback, or Ubuntu authority. The next existing work is
`WU09_PINNED_IMAGE_PRELOAD_PRODUCTION_COMPOSITION_READY`.

Implementation commit `b56b960b5dc0b329df2a28a1ccd747eb2b56b704`
passed focused validation with `98 passed in 0.15s`. Durable canonical evidence
is `/private/tmp/aicontrolcenter-canonical-evidence.xQ73HP`, invocation
`5c676295647b4164bd4462ea74c589d8`: `STATE=COMPLETED_PASS`, capture and pytest
exit status `0`, `validated_pass=true`, and
`CANONICAL_PYTEST_SUMMARY="4516 passed, 5 deselected, 719 warnings, 2 subtests passed in 468.03s (0:07:48)"`.
Final architecture,
security, source-integrity, authority-boundary, trusted-facts replay-risk, and
diff review passed. Generic SEC-02 `HUMAN_AUTHORITY` enforcement is
repository-authoritative. No authorization consumption,
`ControlledExecutionPort` invocation, retry or rollback authority, Docker or
Colima access, Production mutation, secret handling, trust bootstrap, or
Shopping runtime activation occurred. The Mac mini M4 remains the sole Control
Plane; AIControlCenter owns governance, policy, authorization, orchestration,
audit, and deployment control; Ubuntu remains a stateless infrastructure worker
with zero Production authorization or Shopping business-logic authority.
Canonical was not rerun after these documentation-only changes. The existing
pytest permission-cleanup warning family remains separate non-blocking
technical debt.

## Current authoritative — Macro-WU09 governed pinned-image preload implementation

`WU09_PINNED_IMAGE_PRELOAD_IMPLEMENTATION=COMPLETE`, following
`FREEZE_COMMIT=c15c976` at `IMPLEMENTATION_COMMIT=e179fb0`. Validation recorded
`FOCUSED_TEST_GATE=PASS`, `FOCUSED_TEST_RESULT=30_PASSED`,
`CANONICAL_GATE=PASS`, `CANONICAL_RESULT=4129_PASSED_5_DESELECTED`, and
`CANONICAL_WARNINGS=579`.

The repository implements only
`EXACT_ACTION_TYPE=SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT`, with
`EXACT_DOCKER_CONTEXT=colima-aicontrolcenter-commerce` and
`EXACT_IMAGE=alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1`.
There is no generic Docker executor, caller-supplied argv/context/image/tag/
digest, shell, retry, or fallback. A preload authorization permits exactly one
bounded preload invocation. Preload is a separate Production mutation from
WU09 deployment, grants no deployment authority, and deployment requires a
fresh later human authorization.

Current truth is `IMPLEMENTED=true`, `PRELOAD_EXECUTED=false`,
`WU09_DEPLOYED=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
`PRODUCTION_MUTATION_PERFORMED=false`, and
`WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`. The pinned image is not claimed to
be present in Production. `WU09_DEPLOYMENT_AUTHORIZED=false`,
`WU10_AUTHORIZED=false`, and `WU11_AUTHORIZED=false`.

The capability includes no database mutation, network mutation, credential
access, MariaDB connection, or SQL. `GOVERNANCE_CORE_CHANGED=false`,
`SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`. Mac remains the sole
Control Plane (`MAC_CONTROL_PLANE=true`); Ubuntu remains zero-authority
(`UBUNTU_AUTHORITY=false`).

## Current authoritative — Macro-WU09 Production-targeting correction

The correction at `CORRECTION_COMMIT=efdcc5e2da5aee821f28be43011fa08f63e5373d`
is now authoritative: `WU09_PRODUCTION_TARGETING_CORRECTION=COMPLETE`.
Execution explicitly binds `DOCKER_CONTEXT=colima-aicontrolcenter-commerce`;
`DOCKER_CONTEXT_EXPLICIT_BINDING=true` and `ACTIVE_CONTEXT_INDEPENDENCE=true`.
Implicit image pull is disabled with `--pull never`:
`IMPLICIT_IMAGE_PULL_DISABLED=true`.

The exact Production target remains project `ai-shopping-mariadb-loopback`,
service `mariadb-loopback-adapter`, bind `127.0.0.1:58083`, target
`database:3306`, and network `ai-shopping-internal`. Corrected validation is
`FOCUSED_RESULT=19_PASSED`, `CANONICAL_RESULT=4095_PASSED_5_DESELECTED`, and
`CANONICAL_WARNINGS=575`.

`IMPLEMENTED=true`, `DEPLOYED=false`,
`HOST_PORT_ACTIVE_IN_PRODUCTION=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
`PRODUCTION_MUTATION_PERFORMED=false`, and
`PRODUCTION_AUTHORIZATION_CONSUMED=false`. WU10 and WU11 remain separate and
unauthorized. `GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_COUPLED=false`. `MAC_CONTROL_PLANE=true` and
`UBUNTU_AUTHORITY=false`. Recovery truth remains
`RECOVER_EVIDENCE_SUFFICIENT=false` and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

## Current authoritative — Macro-WU09 repository implementation closeout

Macro-WU09 repository implementation is complete at
`IMPLEMENTATION_COMMIT=815d3d5`, following
`ARCHITECTURE_FREEZE_COMMIT=6d31afe`. The canonical gate passed with
`CANONICAL_RESULT=4093_PASSED_5_DESELECTED` and `CANONICAL_WARNINGS=567`.

The loopback adapter contract is `PROJECT=ai-shopping-mariadb-loopback`,
`SERVICE=mariadb-loopback-adapter`, `BIND_HOST=127.0.0.1`,
`TARGET_HOST=database`, `TARGET_PORT=3306`, and
`EXTERNAL_NETWORK=ai-shopping-internal`. `HOST_PORT_ASSIGNED=58083` is desired
non-secret JSON configuration. `IMPLEMENTED=true` does not mean deployed:
`DEPLOYED=false`, `HOST_PORT_ACTIVE_IN_PRODUCTION=false`,
`PRODUCTION_ACCESS_PERFORMED=false`, `PRODUCTION_MUTATION_PERFORMED=false`, and
`PRODUCTION_AUTHORIZATION_CONSUMED=false`. A WU09 Production deployment remains
a separate future human-authorized mutation. WU10 and WU11 remain separate and
unauthorized.

No main-compose, secret-contract, secret-preflight, Governance core, SEC-02, or
`ControlledExecutionPort` coupling occurred. No database-container or network
mutation, credential access, MariaDB connection, or SQL execution occurred.
Mac remains the sole Control Plane (`MAC_CONTROL_PLANE=true`); Ubuntu remains
zero-authority (`UBUNTU_AUTHORITY=false`). Recovery state is unchanged:
`RECOVER_EVIDENCE_SUFFICIENT=false` and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

## Authoritative Macro-WU06 documentation closeout

Authoritative Macro-WU06 is closed: `MACRO_WU_06_CLOSE_GATE=PASS` and
`MACRO_WU_06=CLOSED`. Current remaining state is
`REMAINING_AUTHORITATIVE_MACRO_WUS=6` and
`AUTHORITATIVE_REMAINING_RANGE=WU07-WU12`.

The actual offline evaluation passed its execution gate while finding the
repository-defined historical evidence incomplete:
`ACTUAL_OFFLINE_EVIDENCE_EVALUATION_GATE=PASS`,
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATION=EVIDENCE_INCOMPLETE`,
`AUTH_PLUGIN_EVIDENCE_STATE=MISSING`,
`PYMYSQL_COMPATIBILITY_EVIDENCE_STATE=MISSING`,
`DATA_IDENTITY_EVIDENCE_STATE=MISSING`, and
`CONTINUITY_LINEAGE_EVIDENCE_STATE=MISSING`. Therefore
`RECOVER_EVIDENCE_SUFFICIENT=false` and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

Four separately human-authorized, exact-path, metadata-only `os.lstat`
observations occurred. Under repository terminology this records
`FILESYSTEM_IO_PERFORMED=true` and `PROTECTED_SOURCE_ACCESS_PERFORMED=true`,
while `FILESYSTEM_CONTENT_READ_PERFORMED=false` and
`PRODUCTION_ACCESS_PERFORMED=false`. All four historical evidence leaves were
factually absent; no evidence content was read, no alternate source was
searched, and no fallback or enumeration occurred. `MARIADB_ACTIVITY=NONE`,
`SQL_EXECUTION=NOT_PERFORMED`, `PYMYSQL_ACTIVITY=NONE`, and
`SECRET_VALUES_READ=NO`.

Architecture remains `MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
`CONTROLLED_EXECUTION_PORT_COUPLED=false`, `GOVERNANCE_CORE_CHANGED=false`,
`SEC_02_CHANGED=false`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The current next authoritative
step is `NEXT_STEP=MACRO_WU_07_RECOVER_EVIDENCE_SUFFICIENCY_DECISION`.

## Protected evidence acquisition repository validation closeout

`ARCHITECTURE_COMMIT=f05c652` preceded `IMPLEMENTATION_COMMIT=07bf1bd`.
`PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_IMPLEMENTED=true` and
`PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_VALIDATED=true`. Recorded validation
is `FOCUSED_TEST_GATE=PASS`, `FINAL_CODE_REVIEW_GATE=PASS`,
`CANONICAL_REGRESSION_GATE=PASS`,
`CANONICAL_RESULT="4044 passed, 5 deselected, 555 warnings"`, and
`GIT_DIFF_CHECK_GATE=PASS`.

The repository contains fail-closed authorization durability mechanics,
source/leaf contracts, policy, schema, codec, and tests. Durable `COMMITTED`
facts provide no invocation authority; Python object identity is not
authority. `DURABILITY_ZERO_INVOCATION_AUTHORITY=true`,
`DURABILITY_RESULT_NO_CAPABILITY=true`, and
`DURABILITY_RECEIPT_NO_CAPABILITY=true`. No trusted human Production issuer is
available through this repository boundary, and Production capability issuance
is unavailable. Both Production acquisition entry points fail closed before
filesystem I/O:
`PRODUCTION_HUMAN_ISSUER_AVAILABLE=false`,
`PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE=false`,
`PRODUCTION_ACQUISITION_AVAILABLE=false`, and
`PRODUCTION_FILESYSTEM_IO_AVAILABLE=false`.

No actual acquisition or access occurred:
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
and `FILESYSTEM_IO_PERFORMED=false`. Architecture remains
`MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
`CONTROLLED_EXECUTION_PORT_COUPLED=false`,
`GOVERNANCE_CORE_CHANGED=false`, and `SEC_02_CHANGED=false`.

Recovery truth remains `RECOVER_EVIDENCE_SUFFICIENT=false`,
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`. Therefore
`MARIADB_CONTINUITY_RECOVERY_INTEGRATED_PROGRAM=IN_PROGRESS`,
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. The next operational objective is
`ACTUAL_HISTORICAL_EVIDENCE_ACQUISITION_AND_OFFLINE_EVALUATION`; it has not
occurred. Existing `datetime.utcnow` deprecations and pytest `rm_rf` cleanup
warnings are technical debt/test hygiene, not blockers.

## Offline historical evidence evaluator repository closeout

`IMPLEMENTATION_COMMIT=b51092f` is closed, implemented, and validated:
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_IMPLEMENTED=true`,
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_VALIDATED=true`,
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`, and
`FINAL_OFFLINE_EVALUATOR_ARCHITECTURE_REVIEW_GATE=PASS`. Evidence is focused
`14 passed in 0.03s`, `CANONICAL_REGRESSION_GATE=PASS`,
`CANONICAL_RESULT="4018 passed, 5 deselected"`, 547 warnings,
`CANONICAL_RC=0`, `WORKTREE_AFTER_IMPLEMENTATION_PUSH=CLEAN`, `AHEAD=0`, and
`BEHIND=0`.

The evaluator is repository-only, value-free, fail-closed, and exposes
immutable/slotted factual inputs and results. Callers cannot inject a positive
result. The exact five data identity categories are `WORDPRESS_IDENTITY`,
`SITE_IDENTITY`, `APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`, and
`CLOSED_TABLE_CHARACTERISTICS`. The exact three continuity lineage categories
are `LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and
`PERSISTENT_VOLUME_SNAPSHOT`. Existing `EvidenceAcquisitionCategory` is reused.
Provenance is required for `EVIDENCE_COMPLETE`; `EVIDENCE_COMPLETE` does not
promote operational `RECOVER` sufficiency.

The exact semantic boundary is `Source != Acquisition != Fact !=
OfflineEvaluation != RECOVERDecision != ProductionAccess !=
CredentialValidation != Authorization != Authority`. The evaluator has zero
mutation budget and no filesystem I/O, protected-source acquisition, network,
MariaDB/SQL connection, or Production access. Mac AIControlCenter is the sole
Control Plane; Ubuntu has zero authority. Governance and SEC-02 are unchanged,
and `ControlledExecutionPort` remains uncoupled.

Operational facts remain exactly `FILESYSTEM_IO_PERFORMED=false`,
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
`PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

Actual protected evidence content must not be opened or read yet. Before
actual acquisition, a separate architecture boundary must cover exact
protected leaf metadata, a regular non-symlink leaf, permissions no broader
than `0600`, trusted UID/GID, stable FD/inode/device binding,
TOCTOU-resistant acquisition, an exact fixed source slot, one-shot
human-authorized acquisition, and at most one acquisition per authorization,
with no enumeration, candidates, fallback, retry, recovery, or authorization
reuse. The existing directory metadata snapshot is point-in-time only and is
not stable binding or content-acquisition authority. This milestone does not
claim trusted source contents acquired, protected evidence verified,
Production readiness, or MariaDB credential continuity validated.

## Filesystem target metadata snapshot repository closeout

Architecture `44f4ef0` preceded implementation `e9a3645`. The capability is
`FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_IMPLEMENTED=true` and
`FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_VALIDATED=true`. Evidence is
focused `122 passed in 0.09s`, canonical
`4004 passed, 5 deselected, 543 warnings`, `CANONICAL_RC=0`, and closed,
successful, clean, synchronized implementation Git closeout
(`IMPLEMENTATION_COMMIT_RC=0`, `IMPLEMENTATION_PUSH_RC=0`,
`WORKTREE_STATE=CLEAN`, `AHEAD=0`, `BEHIND=0`).

`FilesystemTargetMetadataSnapshotRequest` contains exactly `concrete_path` and
`ownership_expectation`; outcome and target classification are not caller
inputs. `MacFilesystemTargetMetadataSnapshotAdapter` owns observation. Invalid
requests make zero observations. Otherwise, the exact unchanged target string
is passed to at most one `os.lstat`, and only `st_mode`, `st_uid`, and `st_gid`
are consumed. `reason` is the sole classifier input to the repository snapshot
factory, whose canonical outcome and classification mappings are repository
owned. The positive vocabulary is `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`,
not `SAFE_BOUND` or `METADATA_SAFE_AND_STABLY_BOUND`.

The snapshot is a factual, point-in-time, zero-authority value. It always
preserves `stable_handle_bound=false`, `toctou_closed=false`, and
`fd_inode_device_bound=false`; it does not establish stable binding, TOCTOU
closure, FD/inode/device binding, content acquisition, evidence admission or
verification, `RECOVER` sufficiency, or Production readiness/authorization.
`ConcreteProtectedEvidencePath`, `TrustedOwnershipExpectation`, request,
snapshot, source existence, metadata inspection, metadata safety, acquisition,
admission, verification, and authority remain semantically distinct.

Operational facts remain exactly `TRUSTED_GID_SOURCE_ESTABLISHED=false`,
`TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`,
`CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`,
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
`PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. Mac AIControlCenter remains sole
Control Plane; Ubuntu has zero role and zero authority. Governance and SEC-02
remain unchanged, `ControlledExecutionPort` uncoupled, mutation budget zero.
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## Trusted ownership expectation repository closeout

Architecture freeze `c9bc387` preceded implementation `220c170`. Repository capability is `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_IMPLEMENTED=true` and `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_VALIDATED=true`. Evidence: focused `26 passed in 0.03s`, `FINAL_IMPLEMENTATION_ARCHITECTURE_REVIEW_GATE=PASS`, `CANONICAL_REGRESSION_GATE=PASS`, canonical `3882 passed, 5 deselected, 539 warnings in 136.33s`, `CANONICAL_RC=0`, and `IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`, `WORKTREE_STATE=CLEAN`, `AHEAD=0`, `BEHIND=0`.

The implementation consumes an already-existing `ResolvedTrustedMacAccountHome`, sets `expected_uid` from `bound_uid`, and performs zero additional UID observations and zero additional passwd lookups. Exact repository policy is `TRUSTED_APPLICATION_GROUP_NAME="staff"`; at most one `grp.getgrnam("staff")` lookup uses only `gr_gid`, validates exact `int` and non-negative GID, and fails closed with no retry, fallback, or alternate group lookup. Immutable/slotted `TrustedOwnershipExpectation` has exactly `expected_uid` and `expected_gid`, grants zero authority, and performs no filesystem observation, protected-source access, or Production access.

Operational facts remain exactly `TRUSTED_GID_SOURCE_ESTABLISHED=false`, `TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`, `PROTECTED_SOURCE_ACCESS_PERFORMED=false`, `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. Mac AIControlCenter remains sole Control Plane; Ubuntu has zero role and zero authority. Governance and SEC-02 remain unchanged, `ControlledExecutionPort` uncoupled, and mutation budget zero. `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

Next is separately gated `MACRO_WU_06_FILESYSTEM_TARGET_METADATA_SNAPSHOT_BOUNDARY`, separate from `TrustedOwnershipExpectation`, `ConcreteProtectedEvidencePath`, evidence acquisition, and Production authority. It may later define `FilesystemTargetMetadataSnapshotRequest`, `FilesystemTargetMetadataSnapshot`, and the exact-target single-`lstat` adapter; none is implemented here.

## Concrete protected-evidence path composer repository closeout

The repository composer is implemented and validated
(`CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_IMPLEMENTED=true`,
`CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_VALIDATED=true`). Contract
`254241a` preceded implementation `2810c0c`. Validation recorded focused
`11 passed in 0.03s`, Final Architecture Review `PASS`, canonical regression
`PASS`, and
`3856 passed, 5 deselected, 535 warnings in 133.68s (0:02:13)`,
`CANONICAL_RC=0`. Git closeout recorded `IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`,
`WORKTREE_STATE=CLEAN`, `AHEAD=0`, and `BEHIND=0`.

`ConcreteProtectedEvidencePath` is lexical only and grants zero authority. It
is not provenance, authorization, capability, verification evidence,
filesystem existence/safety evidence, `RECOVER` evidence sufficiency,
Production authorization/readiness, or a security boundary. Python object
identity is not a security boundary. Downstream security-sensitive boundaries
independently validate facts, evidence, and authority.

Repository capability is not runtime establishment:
`TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`,
`CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`,
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
`PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

Mac AIControlCenter remains sole Control Plane; Ubuntu has zero role and zero
authority. Governance and SEC-02 are unchanged, and `ControlledExecutionPort`
remains uncoupled. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## Trusted Mac account-home runtime resolver implementation closeout

The trusted Mac account-home `RuntimeHomeResolver` is implemented and
repository-validated; no runtime invocation is claimed
(`RUNTIME_HOME_RESOLVER_REPOSITORY_IMPLEMENTED=true`,
`RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true`). Contract `41963c1` and
clarification `cf9c34d` preceded implementation `288eb68`. Validation evidence:
focused `28 passed in 0.03s`, Final Architecture Review `PASS`, canonical
`3845 passed, 5 deselected, 531 warnings`, `CANONICAL_RC=0`.

The resolver requires one exact `Darwin` platform observation before any UID
observation; observes real and effective UID exactly once each before root
validation; rejects either zero UID; requires and binds equality; and performs
one bound-UID passwd lookup. It requires exact-string (not subclass), non-empty,
NUL-free, lexically absolute POSIX `pw_dir` and preserves it unchanged. It fails
closed with no retry, fallback, reconnect, recovery, `getpwnam`, caller/HOME/
environment/argv home authority, `Path.home`, `expanduser`, strip,
normalization/canonicalization, filesystem probing or existence/type/symlink
checks, metadata or ownership/mode inspection, or enumeration.

`ResolvedTrustedMacAccountHome` is immutable, slotted, and exactly two-field:
`bound_uid` and `passwd_home`. Supported direct construction and arbitrary
UID/home convenience factories are prohibited; resolver success is the
supported creation path. The object has zero authority and is not unforgeable
provenance, authorization, capability, admission/verification evidence,
`RECOVER` sufficiency, Production authorization/readiness, or a security
boundary. Possession grants no authority; downstream boundaries validate
independently.

Policy != runtime identity observation != resolver != resolved home != suffix
policy != suffix != concrete path != existence != metadata inspection != safety
!= acquisition != admission != verification != authority. Mac AIControlCenter
remains sole Control Plane; Ubuntu has zero resolver authority. Governance and
SEC-02 are unchanged; `ControlledExecutionPort` is uncoupled.

Repository implementation does not mean the resolver ran during this work:
`TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`,
`CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`,
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
`RECOVER_EVIDENCE_SUFFICIENT=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

`MACRO_WU_06_TRUSTED_MAC_ACCOUNT_HOME_RUNTIME_RESOLVER_IMPLEMENTATION=CLOSED`,
but `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; historical evidence acquisition and
offline evaluation remain required. Next is read-only architecture
discovery/freeze for composing the resolved home and frozen exact suffix into a
distinct zero-authority `ConcreteProtectedEvidencePath`, without existence or
metadata inspection, `stat`/`lstat`, protected evidence access/acquisition,
authority, or Production access.

## Trusted Mac account-home repository policy implementation closeout

The architecture contract/freeze at `d9def864c83e3660ce9e6afa646ee4f5851934b3`
preceded the symbolic, zero-authority repository implementation, completed and
Git-closed at `d07054901b5c3eccac401e90afa4126a9bda9515`. The policy is Darwin-only,
rejects root, binds equal real/effective UIDs sourced from `os.getuid()` and
`os.geteuid()`, and freezes the future lookup rule
`pwd.getpwuid(bound_uid).pw_dir` without executing UID/passwd lookup or
implementing a runtime home resolver.

Policy != runtime identity observation != resolver != trusted home value !=
suffix != absolute path composition != existence != metadata inspection !=
metadata safety != acquisition != admission != verification != authority. No
trusted home, absolute/concrete path, filesystem I/O, protected-source or
Production access, historical evidence, metadata fact, or authority was
established. `RUNTIME_HOME_RESOLVER_AVAILABLE=false`,
`TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`,
`CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`,
`PROTECTED_SOURCE_ACCESS_PERFORMED=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
`RECOVER_EVIDENCE_SUFFICIENT=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

Validation: focused `6 passed in 0.06s`; Final Architecture Review `PASS`;
canonical `3817 passed, 5 deselected, 527 warnings in 133.93s`;
`CANONICAL_RC=0`. Git closeout: `COMMIT_RC=0`, `PUSH_RC=0`, clean worktree,
`AHEAD=0`, `BEHIND=0`. Mac AIControlCenter remains sole Control Plane; Ubuntu
remains a stateless zero-authority infrastructure worker. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. Next is read-only architecture
discovery/freeze for the runtime trusted Mac account-home resolver boundary—not
its implementation. The next Production-relevant milestone remains Macro-WU06
Actual Historical Evidence Acquisition + Offline Evaluation; Production
validation and Shopping runtime activation are not ready.

## Authoritative Mac protected evidence suffix policy implementation closeout

The exact suffix architecture contract was established at
`e1e66ac17b3506a4bff4bd0a9322fc7360ca6536`, then implemented and Git-closed at
`6c7b18ab942024120b06d1eb0235c7b67b7916df`. The closed repository submilestone
owns only the exact relative suffix
`Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`,
relative to a future trusted Mac account home. It establishes no absolute or
concrete path and provides no runtime home resolver.

The separation remains base-location identity != base-path policy identity !=
suffix-policy identity != exact suffix value != runtime trusted Mac account-home
resolution != absolute path != concrete path != source existence != metadata
inspection != metadata safety != acquisition != admission != verification !=
authority. Caller path/base/home/suffix, environment/`HOME`, argv, fallback,
enumeration, and candidate-iteration authority remain prohibited. There is no
filesystem I/O, protected-source or Production access, MariaDB/SQL/PyMySQL
activity, Docker/Colima mutation, Ubuntu authority, Governance-core or SEC-02
change, or `ControlledExecutionPort` coupling; the legacy caller-path observer
remains isolated and unreachable.

Focused validation was `6 passed in 0.06s`; Final Architecture Review was
`PASS`; canonical was `3811 passed, 5 deselected, 523 warnings in 134.83s`,
`CANONICAL_RC=0`; warnings were non-failing. All path, existence, inspection,
safety, acquisition, admission, verification, sufficiency, Production-readiness,
and Shopping activation facts remain false as frozen;
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

Mac AIControlCenter remains sole Control Plane and Ubuntu remains stateless with
zero Control Plane authority. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. Next is architecture discovery/freeze
of the trusted Mac account-home resolution boundary before any concrete path
composition or runtime resolver. The next Production-relevant milestone remains
actual historical evidence acquisition and offline evaluation completion under
Macro-WU06.

## Authoritative Mac base path policy implementation

`MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION` is closed as a
repository-only implementation/documentation submilestone. Macro-WU06 remains
`IN_PROGRESS`; `REMAINING_AUTHORITATIVE_MACRO_WUS=7` and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
zero-authority infrastructure worker.
`AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity` is symbolic identity
only. `AuthoritativeMacProtectedEvidenceBasePathPolicy` is repository-owned and
value-free, with an immutable closed mapping from
`ProtectedExternalEvidenceBaseLocationIdentity`. Its canonical factory accepts
no caller path, home, or suffix input.

No runtime account-home resolver exists. Production/source implementation uses
no `Path.home`, `HOME`, `os.environ`, `os.getenv`, `sys.argv`, `pwd.getpwuid`,
`os.getuid`, or `os.getgid`. It performs zero filesystem I/O and contains no
filesystem adapter, metadata inspector, content reader, or Production adapter.
It has zero authorization, capability, execution, mutation, retry, reconnect,
rollback, acquisition, admission, or verification authority. Governance core
and SEC-02 semantics are unchanged; there is no `ControlledExecutionPort`
coupling.

Repository policy identity != exact suffix policy != runtime account-home
resolution != concrete path != source existence != metadata inspection !=
metadata safety != content acquisition != admission != verification !=
authority. The exact suffix is unresolved and must not be guessed; no directory,
path, source existence, inspection, acquisition, or Production access occurred.

Implementation commit `ab9de4a08c35de3805983346cf7f1a6d9accccdb` was pushed
successfully. Focused validation was `6 passed in 0.05s`; final architecture
review was `PASS`; canonical was `3805 passed, 5 deselected, 519 warnings` with
`CANONICAL_RC=0`. The warnings were non-failing.

Preserved facts include `BASE_PATH_POLICY_LAYER_REQUIRED=true`,
`AUTHORITATIVE_BASE_PATH_POLICY_DEFINED=true`, all required exact suffix, path,
existence, metadata, content, admission, verification, sufficiency, Production
readiness, and Shopping activation flags as false;
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`;
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`; and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

Next is architecture discovery/freeze for the future exact protected-evidence
suffix policy—not suffix implementation, directory selection, path
establishment, or runtime resolution.

## Current milestone — Protected external evidence source access and metadata inspection boundary closeout

The repository-only, path-free, zero-authority implementation submilestone
`MACRO_WU_06_PROTECTED_EXTERNAL_EVIDENCE_SOURCE_ACCESS_AND_METADATA_INSPECTION_BOUNDARY`
is `CLOSED`; Macro-WU-06 is not. Mac AIControlCenter remains sole Control Plane;
Ubuntu remains a stateless infrastructure worker with zero authority here.

`ProtectedSourceMetadataInspectionRequest` carries only closed symbolic source
identity and `mutation_budget=0`. Capabilities bind exact request-instance
identity, not dataclass equality: same-source/different-request and cross-source
substitution fail before consumption, mismatch does not consume, the original
exact request succeeds at most once, reuse fails, and concurrency remains exactly
once. Inert test provenance is distinct from operational factual evidence; inert
`SAFE_BOUND` is not operational evidence. No supported
`HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION` issuer exists:
`OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED=false`,
`OPERATIONAL_CANONICAL_PATH_ISSUER_IMPLEMENTED=false`, and
`PRODUCTION_OPERATIONAL_INSPECTION_AVAILABLE=false`. Legacy
`observe_fixed_protected_source` is isolated and unreachable through this
boundary. No caller path/callback, HOME/environment, argv, fallback, enumeration,
or candidate-iteration authority exists. Governance/SEC-02 is unchanged and
`ControlledExecutionPort` is not reused.

Focused validation: `27 passed`. Final architecture review: `PASS`. Canonical:
`3799 passed, 5 deselected, 515 warnings`; `CANONICAL_RC=0`. Warnings were not
failures. Implementation commit `daff799d35709da31434ebb280e0771073b12b52`
was pushed. Production/protected-source access, metadata inspection, content
acquisition, and MariaDB/SQL/PyMySQL/Docker/Colima/Ubuntu activity did not occur.

Architecture freeze: `BASE_PATH_POLICY_LAYER_REQUIRED=YES`; proposed
`AuthoritativeMacProtectedEvidenceBasePathPolicy` and
`AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity`.
`ProtectedExternalEvidenceBaseLocationIdentity.PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION`
is symbolic input only, not a path. Repository-owned policy != runtime
account-home resolution != concrete path != source existence != metadata
inspection != metadata safety. A future resolver may use `pwd.getpwuid(os.getuid()).pw_dir`
only after exact repository suffix policy exists. No exact suffix/path is selected.

`CONCRETE_PATH_VALUE_ESTABLISHED=false`,
`AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false`,
`SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`,
`CONTENT_ACQUISITION_PERFORMED=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, and
`PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`. Caller base-path selection/path
injection, environment/HOME authority, fallback, enumeration, and iteration all
remain false. `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.

Actual acquisition and offline evaluation have not occurred:
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. At that boundary closeout, next was
repository-only
`MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION`, initially
value-free with zero filesystem I/O or Production/protected-source access and no
path resolution, existence check, metadata inspection, or runtime resolver. The
exact protected-evidence suffix remains unresolved and must not be guessed.

## Current milestone — Protected External Evidence Concrete Source Location Descriptor documentation closeout

Exactly four closed symbolic Concrete Source Location identities map one-to-one
and immutably from the four Fixed Source Slot identities. This establishes only
descriptors—not an Authoritative Mac Base Path, Concrete Path Value, existence,
metadata inspection/safety, acquisition, admission, verification, `RECOVER`
sufficiency, or authority.

The exact chain is category != bundle != protected profile != fixed slot !=
Concrete Source Location Descriptor != Concrete Path Value != Source Existence
!= Metadata Inspection != Metadata Safety != Content Acquisition != Admission
!= Verification != Authority. `PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION` is
closed repository policy identity only, not a filesystem path, existence fact,
resolved path, metadata-safe location, or acquisition source. All downstream
facts remain false, offline acquisition `UNKNOWN`, and Production access
unjustified.

All caller/environment/HOME/argv path authority, fallback, enumeration, and
candidate iteration remain prohibited. Reverse lookup is deterministic traversal
of the closed immutable mapping solely to recover canonical profile identity,
not discovery, probing, fallback, iteration, caller selection, or environment
authority. Fixed Source Slot protections are future requirements only: Mac
ownership outside Git; exact `0700` parent; regular non-symlink leaf no broader
than `0600`; trusted uid/gid; future FD/inode and human authorization binding;
one-shot acquisition, maximum one per authorization; and no fallback,
enumeration, candidate iteration, environment/HOME authority, argv/JSON secret
transport, secret logging, or secret hashing.

Chronology: focused `7 passed in 0.06s`; final architecture review `PASS`;
canonical exactly once, `3772 passed, 5 deselected, 511 warnings in 134.12s
(0:02:14)`, `CANONICAL_RC=0`; no correction or rerun; implementation Git
closeout `PASS` at `c3760d2fd9bb0810d3e285ec203b40e5b7b77814`, `AHEAD=0`,
`BEHIND=0`.

Governance, `ControlledExecutionPort`, all authorization/mutation semantics,
Mac sole Control Plane, stateless zero-authority Ubuntu, exact-six Shopping
actions, and target-only provisioning remain unchanged. This is preparation in
Macro-WU-06. Acquisition and offline evaluation did not occur, sufficiency was
not evaluated, and Macro-WU-07 did not start. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## Current milestone — Protected External Evidence Fixed Source Slot documentation closeout

The repository owns exactly four symbolic
`ProtectedExternalEvidenceFixedSourceSlotIdentity` values:
`AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
`PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
`DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`, and
`CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`. Its immutable
one-to-one mapping starts at `ProtectedExternalEvidenceSourceProfileIdentity`.
`CALLER_SLOT_SELECTION_ALLOWED=false`; `CALLER_PATH_INJECTION_ALLOWED=false`.

The required separation is `EvidenceAcquisitionCategory` != Source Bundle
Identity != Protected Source Profile Identity != Fixed Source Slot Identity !=
Concrete Source Location != Source Existence != Metadata Safety != Content
Acquisition != Admission != Verification != Authority. Fixed Source Slot Identity
is symbolic only. `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`.
It establishes no path, source or historical-evidence existence, metadata
inspection or safety, or content acquisition:
`CONCRETE_PATH_ESTABLISHED=false`, `SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`, and
`CONTENT_ACQUISITION_PERFORMED=false`. `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN` and
`PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`.

Protection requirements are future policy only, not current operational facts:
Mac Control Plane ownership outside Git; protected parent exact mode `0700`;
regular non-symlink leaf no broader than `0600`; explicit trusted uid/gid; future
FD/inode binding, explicit human authorization, and one-shot acquisition; maximum
one acquisition per future authorization; no fallback, enumeration, candidate
iteration, environment/HOME authority, argv or JSON secret-value transport,
secret logging, or secret hashing.

Validation chronology: focused `40 passed in 0.14s`; authoritative final
architecture review `PASS`; canonical exactly once, `3765 passed, 5 deselected,
507 warnings in 134.47s`, `CANONICAL_RC=0`; no later code/test correction and no
rerun. Commit `7ccebffcce281590d57f4f8fc93d9e53032bb822`, implementation
push, and Git closeout passed with `AHEAD=0`, `BEHIND=0`.

This is repository preparation inside authoritative Macro-WU-06. Actual
historical evidence acquisition and offline evaluation have not occurred, and
`RECOVER_EVIDENCE_SUFFICIENT` has not been factually evaluated.
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; do not start Macro-WU-07.

All governance remains unchanged, including
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`,
`STRATEGY_EXECUTED=false`, `PRODUCTION_VALIDATION_READY=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. The exact six Shopping actions are unchanged;
`SHOPPING_SECRET_PROVISIONING` remains target-only. No Governance,
`ControlledExecutionPort`, or authorization behavior changed. Mac AIControlCenter
remains sole Control Plane; Ubuntu remains stateless and has no Control Plane
authority. No Production, MariaDB, metadata, content, SQL, PyMySQL, secret-value,
or Notion activity was performed.

## Prior milestone — Protected External Evidence Source Profile documentation closeout

The repository now has four closed symbolic
`ProtectedExternalEvidenceSourceProfileIdentity` values:
`AUTH_PLUGIN_PROTECTED_SOURCE_PROFILE`, `PYMYSQL_PROTECTED_SOURCE_PROFILE`,
`DATA_IDENTITY_PROTECTED_SOURCE_PROFILE`, and
`CONTINUITY_LINEAGE_PROTECTED_SOURCE_PROFILE`. The existing four
`EvidenceReferenceIdentityClass` bundle identities map one-to-one to these
profiles through immutable, repository-owned
`BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING`; caller selection remains closed.
The exact four-file implementation is complete and remains
`repository_only=true`, `value_free=true`, `fail_closed=true`, and
`zero_authority=true`.

The semantic boundary is exact: `EvidenceAcquisitionCategory` != source bundle
identity != protected source profile identity != concrete source location !=
source existence != metadata safety != acquisition != admission != verification
!= authority. A protected profile identity establishes none of those downstream
facts. `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`.

Current factual state remains `concrete_source_location_established=false`,
`source_exists=false`, `historical_evidence_exists=false`,
`source_metadata_safe=false`, `content_acquired=false`,
`evidence_admitted=false`, `evidence_verified=false`, and `authority=false`.
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN` and
`PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`. Actual historical evidence was
not acquired or evaluated offline; its existence, concrete location, and
metadata safety are not established.

Validation chronology was protected source profile discovery/freeze, exact
four-file implementation, focused `37 passed in 0.13s`, authoritative final
architecture review `PASS`, and canonical exactly once with `3753 passed, 5
deselected, 503 warnings` and `CANONICAL_RC=0`. No code/test correction followed
and canonical was not rerun. Implementation commit
`a206a6aad23ba79a548bf3f7498a4c3883fec067` was pushed normally;
`IMPLEMENTATION_GIT_CLOSEOUT=PASS`, `GIT_PUSH=PASS`, `AHEAD=0`, and `BEHIND=0`.

This is not authoritative Macro-WU-07. It is repository preparation inside
authoritative Macro-WU-06 Actual Historical Evidence Acquisition + Offline
Evaluation. `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`,
and `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; original Macro-WU-07 remains the
later factual `RECOVER_EVIDENCE_SUFFICIENT` decision. Macro-WU-06 remains open.

Governance remains `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `ROTATE_AUTHORIZED=false`,
`REPLACE_AUTHORIZED=false`, `STRATEGY_EXECUTED=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
Mac AIControlCenter remains sole Control Plane; Ubuntu remains a stateless
infrastructure worker with no Control Plane authority. The exact six Shopping
actions remain unchanged; `SHOPPING_SECRET_PROVISIONING` remains target-only.
Operational truth remains `PRODUCTION_ACCESS=NOT_PERFORMED`,
`MARIADB_ACTIVITY=NONE`, `SECRET_VALUES_READ=NO`,
`SQL_EXECUTION=NOT_PERFORMED`, `PYMYSQL_ACTIVITY=NONE`, and
`NOTION_SYNC=NOT_PERFORMED`.

## Prior milestone — MariaDB Continuity Evidence Source Binding documentation closeout

The source-binding contract now has four closed typed protected-source bundle
identities and a total, unique set of twelve `EvidenceAcquisitionCategory`
mappings. It is repository-only, value-free, fail-closed, zero-I/O,
zero-authority, and performed no Production access.

WU-11 completed the exact four-file implementation. Its initial focused pass was
followed by an architecture finding on caller-selectable bundle/category
construction. The permanent Git-state test was removed, caller construction was
closed, and immutable `MappingProxyType` mapping was preserved. Final hardening
made `_canonical_bundle` accept identity only and derive categories exclusively
from `CATEGORY_TO_BUNDLE_MAPPING`; no helper accepts caller category tuples and
direct caller construction of `ProtectedSourceBundlePolicy` is impossible.
Canonical instances remain frozen, with exactly four identities and twelve total
unique categories. Final focused validation was `26 passed in 0.11s`; the final
architecture review was `PASS`.

WU-12 canonical ran exactly once after that corrected review and returned
`3742 passed, 5 deselected, 499 warnings`, `CANONICAL_RC=0`. Warnings were
non-failing; no later code/test correction or canonical rerun occurred.
Implementation commit `795d93c6e9f577a0e222c9617c23468b354d7a5b` and normal
push passed with `AHEAD=0`, `BEHIND=0`.

Descriptor classification, source bundle identity, source location, source
existence, metadata safety, acquisition, admission, verification, and authority
remain distinct in that order. `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`,
`repository_only=true`, `value_free=true`, `fail_closed=true`, and
`zero_authority=true` remain preserved.

Local `SOURCE_BINDING WU-10/WU-11/WU-12` are preparation substeps within
authoritative Macro-WU-06, not authoritative integrated-program Macro-WUs.
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. Original Macro-WU-07 remains the later
factual `RECOVER_EVIDENCE_SUFFICIENT` decision. No actual historical evidence
was acquired or evaluated, and Macro-WU-06 remains open.

Governance remains `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `ROTATE_AUTHORIZED=false`,
`REPLACE_AUTHORIZED=false`, `STRATEGY_EXECUTED=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
The exact six Shopping actions remain unchanged and
`SHOPPING_SECRET_PROVISIONING` remains target-only. Operational truth remains
`PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
`SECRET_VALUES_READ=NO`, `SQL_EXECUTION=NOT_PERFORMED`, `PYMYSQL_ACTIVITY=NONE`,
and `NOTION_SYNC=NOT_PERFORMED`.

## Current milestone — MariaDB Continuity Integrated WU-09 documentation closeout

Exact chronology: `MARIADB_CONTINUITY_INTEGRATED_WU_07_DISCOVERY_RECONCILE_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_IMPLEMENTATION_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_FOCUSED_GATE=PASS`,
`FOCUSED_RESULT=17 passed in 0.07s`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_FINAL_ARCHITECTURE_REVIEW_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_08_CANONICAL_GATE=PASS`,
`CANONICAL_RESULT=3733 passed, 5 deselected, 495 warnings`, `CANONICAL_RC=0`,
`IMPLEMENTATION_GIT_CLOSEOUT=PASS`,
`IMPLEMENTATION_COMMIT=63370cfdf4ea0c80ca54395dd5913317ba529dca`, `GIT_PUSH=PASS`,
`AHEAD=0`, and `BEHIND=0`.

Implementation and validation are complete for the exact four-file,
repository-only, value-free, fail-closed, zero-authority Evidence Acquisition
Descriptor Contract. Its closed classifications are auth-plugin authoritative
evidence; PyMySQL 1.2.0 compatibility evidence; expected database identity;
expected account identity; required grants; five-category data identity;
three-category continuity lineage; timestamp evidence; immutable integrity
binding; trusted issuer; account binding; and baseline binding.

These are descriptors, not sources or evidence. Descriptor classification,
source identity, source existence, acquisition, evidence existence, admission,
verification, authoritative evidence, provenance, integrity, timestamp, issuer,
account/baseline binding, identity completeness, continuity completeness,
`RECOVER` sufficiency, Production readiness, and authority remain strictly
separate. Nothing is located, retrieved, ingested, parsed, admitted, or verified;
no historical evidence or downstream positive fact is established. Caller
positive-fact/source-path/reference injection, external evidence values, and
secret-bearing content are prohibited. I/O, network, SQL, Production access,
runtime mutation, and acquisition/admission/verification authority remain zero.

Mac AIControlCenter remains sole Control Plane; Ubuntu remains a stateless
infrastructure worker. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact
six Shopping actions remain unchanged; `SHOPPING_SECRET_PROVISIONING` remains
target-only; `ROTATE_AUTHORIZED=false`; `REPLACE_AUTHORIZED=false`;
`STRATEGY_EXECUTED=false`; `PRODUCTION_VALIDATION_READY=false`; and
`SHOPPING_RUNTIME_ACTIVATED=false`. Operational truth is
`PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
`SECRET_VALUES_READ=NO`, `SQL_EXECUTION=NOT_PERFORMED`,
`PYMYSQL_ACTIVITY=NONE`, and `NOTION_SYNC=NOT_PERFORMED`.

## Current milestone — MariaDB Continuity Phase B2B-1D Package-4

Package-4 is a repository-only external evidence admission and verification
boundary contract. Discovery, Architecture Freeze, exact four-file
implementation, focused `8 passed in 0.05s`, self-review, and Final Architecture
Review passed. Sandbox canonical failed only because two unrelated dashboard
tests could not open audit SQLite (`2 failed, 3722 passed, 5 deselected, 481
warnings`, `RC=1`; `ENVIRONMENT_ONLY_FAILURE`). Host preflight was writable and
authoritative host canonical passed (`3724 passed, 5 deselected, 487 warnings`,
`RC=0`). No correction followed review and no canonical rerun followed host
pass. Implementation commit `9f63463dc9f1c48fdda0ceaba698fead6dd3fab2`
and its normal push passed; current HEAD and upstream are aligned at that commit
with divergence `0 0`. Documentation Git closeout remains pending, so Package-4
is not `CLOSED`.

The contract is value-free, zero-authority, zero-I/O, zero-network, fail-closed,
accepts no positive caller facts, arbitrary references, evidence, or credentials,
and keeps presentation, admission, verification, reference-local verification,
existence, provenance, integrity, issuer, bindings, compatibility, completeness,
sufficiency, readiness, and authority separate. It is not ingestion, retrieval,
verification execution, Production access, MariaDB/credential validation, SQL,
or activation and claims no historical evidence. Auth-plugin/PyMySQL evidence
remains unavailable; five/three categories incomplete; `RECOVER` insufficient;
ROTATE/REPLACE unauthorized; strategy/readiness/runtime false. Mac remains sole
Control Plane; Ubuntu stateless; legacy readiness factual-only; Phase-06 and the
exact six Shopping actions unchanged; provisioning target-only.

## Current milestone — MariaDB Continuity Phase B2B-1D Package-3

`PHASE_B2B_1D_PACKAGE_3_EXTERNAL_EVIDENCE_ATTESTATION_REFERENCE_CONTRACT` is
implementation-complete and validation-complete at
`1f9790fe1c96a6c20135508e4bcfbfce5d897546`. Implementation Git closeout and
push passed, followed by a clean worktree and divergence `0 0`.

Architecture Freeze passed. Initial focused was `8 passed in 0.05s`; review #1
blocked an incorrect canonical `VERIFIED_EXTERNAL_REFERENCE` default. Corrected
focused was `9 passed in 0.05s`, review #2 passed, and canonical #1 was `3716
passed, 5 deselected, 475 warnings`, `RC=0`. Closeout preflight later blocked
only on trailing EOF blank lines in exactly two files. The correction was
semantically unchanged; architecture reconcile and all prior gates passed;
corrected canonical was `3716 passed, 5 deselected, 479 warnings`, `RC=0`. Late
focused on the identical committed snapshot was `9 passed in 0.04s`. No
canonical rerun occurred after implementation Git closeout.

Canonical reference state is `VERIFICATION_REQUIRED`.
`VERIFIED_EXTERNAL_REFERENCE` remains a separate reference-local,
zero-promotion state only. Package-3 is repository-only, immutable,
fail-closed, value-free, zero-authority, zero-I/O, and zero-network. It accepts
no actual evidence values, caller-positive fact injection, or arbitrary
reference strings, and directly reuses `EvidenceRequirementCategory`,
`VerificationState`, `DataIdentityCategory`, and `ContinuityEvidenceCategory`.

Auth-plugin and PyMySQL evidence remain unavailable; five-category identity and
three-category lineage incomplete; `RECOVER` evidence insufficient;
ROTATE/REPLACE unauthorized; strategy unexecuted; Production readiness and
Shopping runtime false. No actual historical evidence is claimed.

Mac AIControlCenter remains sole Control Plane and Ubuntu stateless. Legacy
readiness stays factual-only; the exact six Shopping actions, target-only
`SHOPPING_SECRET_PROVISIONING`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO` remain unchanged. Repository
milestone closure awaits final documentation review and documentation Git
closeout of exactly these six documents.

## Current status — MariaDB Continuity Phase B2B-1D Package-2 documentation candidate

`PHASE_B2B_1D_PACKAGE_2_EXTERNAL_EVIDENCE_REFERENCE_MANIFEST` is implemented at
`0c6cf471da9e918e798f8a71fb2d28a4afc98d46`; implementation and Git closeout
passed. Focused validation was `29 passed in 0.05s`; final architecture review
was `PASS`; canonical ran exactly once afterward and returned `3707 passed, 5
deselected, 471 warnings`, `RC=0`. Warnings are not failures, and no focused or
canonical rerun followed implementation Git closeout.

The manifest is repository-only, immutable, fail-closed, value-free, and
zero-authority. Evidence requirement, reference state, existence, provenance
validity, authority, compatibility, and reference-local readiness are seven
separate facts; none implies another. `VerificationState` is exactly
`UNAVAILABLE`, `REFERENCED_UNVERIFIED`, `VERIFICATION_REQUIRED`, and
`VERIFIED_EXTERNAL_REFERENCE`. The last state and
`reference_readiness_established` are reference-local facts only—not evidence
existence/provenance authority, canonical availability, compatibility, aggregate
readiness, `RECOVER` sufficiency, Production validation readiness, or any
authorization/capability/execution/mutation authority.

The five required non-B1 categories are `AUTH_PLUGIN_HISTORICAL_EVIDENCE`,
`PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE`, `EXPECTED_DATABASE_IDENTITY`,
`EXPECTED_ACCOUNT_IDENTITY`, and `REQUIRED_GRANTS_PROFILE`. Existing frozen
types are reused directly: `DataIdentityCategory` contains `WORDPRESS_IDENTITY`,
`SITE_IDENTITY`, `APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`, and
`CLOSED_TABLE_CHARACTERISTICS`; `ContinuityEvidenceCategory` contains
`LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and `PERSISTENT_VOLUME_SNAPSHOT`. No
duplicate enums were introduced.

Safety remains frozen: `MANIFEST_VALUE_FREE=true`; references cannot be caller
supplied, assert existence/authority/compatibility/readiness, contain secret
values, credential hashes, arbitrary free text, or SQL, or trigger I/O, network,
or Production access. Source projections have authorization, capability,
execution, mutation, retry, reconnect, and rollback authority all `false`, with
`value_free=true`.

Current truth is unchanged: auth plugin unresolved; authoritative auth-plugin
evidence unavailable; PyMySQL compatibility false; five-category identity and
three-category continuity lineage incomplete; and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`. `RECOVER` is the human
strategy decision under zero authority, not execution, Production, credential,
validation, or mutation authority. ROTATE and REPLACE remain unauthorized and
no strategy was executed. Fixed SQL, numeric loopback port, deployed Production
target, concrete credential path, and credential value reader remain unavailable
or false.

Production access and MariaDB authentication were not performed; secret values
were not read; SQL, PyMySQL installation, and Notion sync were not performed.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`. Mac
AIControlCenter remains sole Control Plane; Ubuntu remains stateless. Legacy
`production_validation_ready` stays factual-only.
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the six actions remain
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only.

This is a documentation candidate, not Package-2 closure. Final documentation
review, commit and normal push of exactly these six documents, clean Git, and
divergence `0 0` self-activate closure without a second SHA-recording edit. Only
then is the next work the next MariaDB continuity evidence/strategy boundary.

## Current status — MariaDB Continuity Phase B2B-1D Package-1 documentation candidate

Implementation is complete at `cacc659fd518c751544a8062ce0c36813f1c7bcc`;
Git closeout and architecture review #3 passed. Focused was `79 passed in
0.20s`; canonical ran once: `3678 passed, 5 deselected, 467 warnings in
133.11s`, `RC=0`. Reruns are `NOT_RUN`; canonical requires code/test change.

Package-1 is repository-safe, value-free, and zero-authority. It defines
fail-closed contracts for authoritative historical auth-plugin evidence,
canonical truth and override prohibition, compatibility proof, Mac-owned
independent identity, complete five-category data identity, exact
three-category continuity lineage with independent provenance, human decision
on insufficient `RECOVER` evidence, and a fixed closed operation profile.
`AUTH_PLUGIN_STATE=UNRESOLVED`; evidence, PyMySQL compatibility, and proof are
unavailable. The prior `PyMySQL==1.2.0` declaration is not installation/import
or proof. Fixed SQL remains unavailable and prohibited.

Production has zero mutation budget, at most one future connection/auth attempt
per distinct human authorization, no authorization reuse, and no
retry/reconnect/rollback. There is no aggregate readiness authority; Phase-A
legacy `production_validation_ready` DTO semantics remain unchanged. No
Production access, MariaDB authentication/connection, secret read, or SQL
occurred. Readiness/runtime remain false.

Mac mini AIControlCenter remains sole Control Plane; Ubuntu remains stateless.
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six Shopping actions
remain unchanged and `SHOPPING_SECRET_PROVISIONING` remains target-only.
Package-1 is not `CLOSED`: final review, exact-six-doc commit/push, clean Git,
and divergence `0 0` self-activate closure. No future SHA is claimed. Next is a
B2B-1D architecture/evidence boundary, not immediate Production validation.

## Current status — MariaDB Continuity Phase B2B-1C documentation closeout candidate

Implementation is complete at `d4802054366178c6e3282ad089e393726f2d9309`
(`9 files changed`, `91 insertions`, `4 deletions`) and implementation Git
closeout is `PASS`. Focused validation was `42 passed in 0.16s`; final
architecture review was `PASS`; canonical ran exactly once afterward with
`3674 passed, 5 deselected, 463 warnings in 134.93s`, `CANONICAL_RC=0`. No
focused or canonical rerun is required unless code or tests change.

This six-document update is the documentation closeout candidate.
`PHASE_B2B_1C` is not yet authoritatively closed. It becomes closed only after
final documentation review passes, the containing documentation commit is
created and normally pushed, Git status is clean, and upstream divergence is
`0 0`. No second documentation edit is needed merely to record that commit SHA.

`requirements.txt` now declares exactly `PyMySQL==1.2.0`. The driver contract
remains `PYMYSQL` `1.2.0`, synchronous one-shot. Declaration is not runtime
proof: `PYMYSQL_INSTALLED=NO`, `driver_imported=false`,
`PYMYSQL_COMPATIBILITY_ESTABLISHED=false`, `AUTH_PLUGIN_STATE=UNRESOLVED`, and
driver readiness remains false.

Credentials remain symbolic only, with no concrete path or value read. Future
requirements remain a fixed closed source, exact `0700` protected parent,
regular non-symlink leaf no broader than `0600`, trusted uid/gid, FD/inode
binding, one acquisition maximum per authorization only after capability
consumption, and no fallback, enumeration, candidate iteration,
environment/`HOME` authority, argv/JSON/log secret, or secret hashing.

The B1 `ContinuityEvidenceCategory` type remains frozen with exactly
`LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and `PERSISTENT_VOLUME_SNAPSHOT`;
`independent_historical_provenance_required=true`. There is no database
connection, SQL, retry, reconnect, pooling, `ControlledExecutionPort` use,
Governance semantics change, or Production authority.

Mac remains the sole Control Plane; Ubuntu remains stateless.
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six Shopping actions
remain unchanged and `SHOPPING_SECRET_PROVISIONING` remains target-only.
Production access and MariaDB authentication were `NOT_PERFORMED`, secret
values read `NO`, SQL execution `NOT_PERFORMED`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
Do not begin Production validation. After authoritative closure, the next
milestone remains a separate architecture/discovery boundary.

## Current status — MariaDB Continuity Phase B2B-1A

`PHASE_B2B_1A` is implemented at
`aa049e2940707ff9209a730ecfbcc5f705062171` as exactly 16 new files and 924
insertions of repository-only, value-free prerequisite contracts. Implementation,
focused validation, architecture review, canonical validation, and implementation
Git closeout are closed. The prior reviewed documentation snapshot and its
documentation Git closeout are evidenced by
`099258ce3470f57e9260a1f671b404ed9d42a623`; that commit is not this
reconciliation's commit.

This exact six-document reconciliation is the `FINAL CLOSURE CANDIDATE` while
uncommitted. `PHASE_B2B_1A=CLOSED` becomes authoritative only after the commit
containing this exact reconciliation is committed, normally pushed, and the
post-push checks show clean Git status and upstream divergence `0 0`. When those
conditions pass, the same rule records documentation Git and repository
closeout as closed; no second documentation mutation is required.

After a blocked initial review, import-root handling, Git-scope validation, and
B1 enum reuse were corrected. Focused validation was `49 passed in 0.14s`;
review #2 was `PASS`; canonical ran exactly once afterward with `3673 passed, 5
deselected, 459 warnings in 134.90s`, `RC=0`; Git closeout was `PASS`.

PyMySQL `1.2.0` remains an uninstalled synchronous one-shot contract with
unresolved auth plugin and compatibility false. Credentials remain symbolic and
Mac-owned; identity, grants, and historical baselines remain unavailable. No
fixed/arbitrary SQL, assigned port, deployed target, Production/MariaDB access,
secret read, Docker/Colima access, dependency change, or Notion sync occurred.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.

Mac remains the sole Control Plane; Ubuntu remains stateless.
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six Shopping actions
remain unchanged and `SHOPPING_SECRET_PROVISIONING` remains target-only. Next is
the read-only `PHASE_B2B_1B_CONCRETE_READINESS_DISCOVERY` boundary, authorizing
no installation, requirements change, Production/authentication/credential/SQL
access, numeric-port deployment, or activation.

## MariaDB Continuity Phase B2A — documentation closeout

Phase B2A implementation and validation are closed at
`6063ce08b62e99331f5d442afc9d2a71703bcabf`; documentation and repository
closeout completed at `cfb1d7eae4b9676373ba31c485330b8449cd90f3`.
It adds only value-free MariaDB continuity contracts. Canonical truth stays
separate from constructible observations.
Runtime observation states are exactly `CONFIRMED`, `REJECTED`,
`NOT_EVALUATED`, and `UNCERTAIN`; all six mandatory facts must be confirmed for
complete validation. Projections grant no authorization, capability, execution,
mutation, retry, reconnect, or rollback authority.

The fixed protected source is metadata-only: parent exact `0700`, directory,
non-symlink, expected uid/gid; leaf non-empty regular non-symlink, permissions
no broader than `0600`, expected uid/gid. Reasons are a closed vocabulary and
contradictions are rejected. A manually constructed positive is only an inert
value-free factual/fake DTO, never readiness or authority. Trusted filesystem
evidence is separately produced by `observe_fixed_protected_source`; no secret
value is read, and there is no enumeration or fallback.

Target `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE` is owned by
`MAC_CONTROL_PLANE`; its numeric port is unassigned, it is undeployed, and it
is not ready. The contract specifies PyMySQL `1.2.0`, synchronous one-shot,
unresolved auth plugin, and at most one future connection per authorization.
PyMySQL is neither imported nor installed, `requirements.txt` is unchanged,
and Phase B2A contains no network, SQL, retry, reconnect, or pooling.

Implementation is limited to
`core/secrets/mariadb_continuity_observations.py` and the protected-source,
PyMySQL-adapter, and target-resolver modules under `ops/macos/shopping/`, with
their four matching `tests/test_sm_mariadb_continuity_*.py` test files.

Evidence: initial focused `21 passed in 0.35s`; first final architecture review
`BLOCKED`; corrected focused `31 passed in 0.13s`; final read-only architecture
review #2 `PASS`; canonical exactly once on final reviewed code/test state,
`3624 passed, 5 deselected, 455 warnings in 134.66s`, `RC=0`. Post-commit focused
and canonical reruns were `NOT_RUN`. Normal push, final clean check, and
divergence `0 0` passed. A duplicate closeout correctly failed closed on stale
expected pre-commit HEAD and made no second commit, push, or implementation
change.

Runtime remains: no Production access, MariaDB authentication, SQL, Docker,
Colima, or Notion sync; no secret values read; PyMySQL not installed;
requirements unchanged; auth plugin unresolved; MariaDB loopback port
unassigned; `PRODUCTION_VALIDATION_READY=false`; and
`SHOPPING_RUNTIME_ACTIVATED=false`.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains stateless.
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The six preserved actions are
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only. Repository closeout is
complete. The next boundary is `PHASE_B2B_CONCRETE_INTEGRATION_DISCOVERY`; B2B is not
implemented now.

## MariaDB Continuity Phase B1 — closed implementation boundary

Phase B1 is implementation- and validation-complete at
`acdbd859872b842691c293b5e094472b344d304b`. Its one-shot factual lifecycle is
`NEW -> AUTHORIZED -> CONSUMED -> PRE_ATTEMPT -> ATTEMPT_INITIATED -> TERMINAL`.
Terminal closure from `PRE_ATTEMPT` preserves `attempted_count=0`; terminal
closure from `ATTEMPT_INITIATED` preserves `attempted_count=1`. There are no
skipped, reverse, repeated, post-terminal, or second-attempt transitions.
`AUTHORIZED` is a fact, not authority.

The value-free frozen sources are exactly `CREDENTIAL_SOURCE`,
`EXPECTED_IDENTITY_DESCRIPTOR`, `DATA_IDENTITY_BASELINE`, and
`DATA_CONTINUITY_BASELINE`. Their current availability facts are respectively
`credential_material_available=false`,
`expected_identity_descriptor_available=false`,
`data_identity_baseline_available=false`, and
`data_continuity_baseline_available=false`. Supported public construction
rejects unsupported positive and contradictory availability.

Credential custody remains Mac-Control-Plane-owned: one external fixed slot
outside Git, `0700` protected parent, `0600` regular non-symlink file, explicit
trusted uid/gid, and no ambient `HOME`/UID authority. No environment, argv,
JSON secret-value or Governance transport, secret log/hash, fallback,
enumeration, or candidate iteration is allowed. At most one acquisition may
occur, only after capability consumption. No credential material was read or
verified.

The Mac-Control-Plane-owned target is
`CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`. Current facts are
`canonical_target_contract_defined=true`,
`numeric_loopback_port_assigned=false`, `target_deployed=false`, and
`production_target_ready=false`, where readiness is derived from
`numeric_loopback_port_assigned AND target_deployed`. Callers supply no
host/port/DSN/URL/database/username, and Phase B1 has no numeric MariaDB port.

Phase B1 includes no PyMySQL, MariaDB driver, SQL, network, filesystem
credential reader, environment/argv credential transport, retry, reconnect,
pooling, Production access, or MariaDB authentication.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
Production access/authentication, runtime inspection, Docker, Colima, and
Notion sync were `NOT_PERFORMED`; secret values read `NO`; PyMySQL installed
`NO`; requirements changed `NO`.

`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The six unchanged actions are
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
`SHOPPING_SECRET_PROVISIONING` remains target-only. Mac AIControlCenter remains
the sole Control Plane and Ubuntu a stateless infrastructure worker.

Validation history: initial focused `22 passed in 0.07s`; first architecture
review `BLOCKED` for insufficient public factual forgeability/contradiction
handling and test coverage; correction `PASS`; corrected focused `37 passed in
0.06s`; final read-only architecture review `PASS`. Canonical ran exactly once
after final reviewed code/test state: `3593 passed, 5 deselected, 447 warnings
in 133.58s`, `RC=0`; post-commit canonical rerun `NOT_RUN`.

Phase B2 is future work only: possible PyMySQL selection/pinning, a synchronous
one-shot Mac adapter, fixed loopback resolver, protected credential reader,
independent expected DB/account/grants and identity/continuity baseline
readers, and fixed parameterized read-only SQL with one connection and no
retry/reconnect/pooling. It is not implemented or Production-ready.

## MariaDB Continuity Validation Prerequisite / Phase A

Phase A is repository-complete after documentation closeout at implementation
commit `ccf3ce00f7f6602d2cc6a84ec5632c7088cae418`. It provides only value-free
MariaDB prerequisite/readiness facts and a Mac Control Plane process-local
composition boundary. The non-serializable one-shot `HumanPresenceGrant` has
prohibited direct construction, private inert Phase-A test issuance only,
canonical request binding, concurrent exactly-once use, consume-before-assembly
and permanent consumption after failure, redacted exceptions, and no capability
invocation during composition.

It does not provide a driver, Production credential source/material
verification, SQL, connectivity, canonical target, identity/continuity
baseline, real Production validation capability/authentication, consumer
compatibility validation, mutation authority, or activation. This is not
Production validation readiness: `PRODUCTION_VALIDATION_READY=false`,
`SHOPPING_RUNTIME_ACTIVATED=false`, and historical MariaDB credential continuity
remains unresolved.

`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact six Shopping secret
provisioning actions are preserved. Mac AIControlCenter remains the sole Control
Plane; Ubuntu remains a stateless infrastructure worker.

Evidence: focused `13 passed in 0.07s`; final architecture review `PASS`;
canonical `3556 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly
once on the final reviewed implementation tree; canonical rerun after commit
`NOT_RUN`. Production access and MariaDB authentication were `NOT_PERFORMED`;
runtime, Docker, Colima, and Notion were `NOT_PERFORMED`; secret values read
`NO`.

## SM-01B-02D-06 MariaDB Historical Credential Continuity Validation Boundary v1

SM-01B-02D-06 is CLOSED at implementation commit
`3c93ad39586080db618ee090a7548806c024c44a`. It is a Mac mini M4
AIControlCenter-owned, value-free, read-only boundary—not a Production mutation
boundary or `ControlledExecutionPort`. It uses no `GovernanceMutationBudget`,
and its factual result/evidence grants no mutation, authorization, execution,
retry, or rollback authority.

Outcomes are exactly `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`,
`MALFORMED`, `UNCERTAIN`. `VALIDATED` requires `attempted_count=1` and separate
`CONFIRMED` facts for credential acceptance, expected database identity,
expected account identity, required grants, data identity, and data continuity.
Authentication alone is insufficient; consumer compatibility stays
`NOT_EVALUATED`; `UNCERTAIN` fails closed. There is no retry, fallback,
candidate iteration, guessing, automatic rollback, or compensation.

The future Production capability is externally supplied, non-factual,
non-serializable authority metadata, absent from request/result/projection, not
minted by core, and usable at most once per application validation invocation.
06 has no real MariaDB client or Production capability. It leaves authorization
consumption/durable SQLite, Governance execution, SEC-02/postconditions/audit,
the coordinator, config, schemas, 05 `ContinuityDecision`, and the exact six
Shopping provisioning actions unchanged; `SHOPPING_SECRET_PROVISIONING` is
still a target, not an action.

No Production MariaDB authentication or historical-credential validation took
place. Continuity remains `UNRESOLVED`; no `RECOVER` confirmation, `ROTATE`,
`REPLACE`, DB/grant/payload mutation, materialization, DB-client/runtime
cutover, old-account retirement, or activation occurred, and
`SHOPPING_RUNTIME_ACTIVATED=false`. Phase B architecture discovery is the next
development boundary and must precede any separately explicitly
human-authorized Production validation. 06 itself does not authorize such an
operation.

Validation: focused `33 passed in 0.08s`; architecture review `PASS`, all
severities `NONE`. Canonical was accidentally run twice on the same unchanged
final-reviewed tree; both successful runs reported `3543 passed`, `5
deselected`, `447 warnings`, `RC=0`. This duplicate run is an operational
process deviation, not a code or architecture failure; no code/test change
occurred between runs. Push `PASS`; final Git clean, divergence `0 0`.
Production access, runtime inspection, Docker, Colima, and Notion sync were not
performed; secret values read: `NO`. Mac mini M4 remains sole Control Plane;
Ubuntu remains stateless, and no authority is delegated to WordPress,
WooCommerce, n8n, Ubuntu, MariaDB, or external recovery custody systems.

## SM-01B-02D-05 MariaDB Credential Continuity Decision Model v1

SM-01B-02D-05 is CLOSED at implementation commit
`9f168cc475345e7d2c949f375ef5c44f2ad2fda9`. `ContinuityDecision` is a
fail-closed public factual model with exactly four states—`UNRESOLVED`,
`STRATEGY_DECLARED`, `VALIDATION_REQUIRED`, `RESOLVED`—and exactly three
strategies—`RECOVER`, `ROTATE`, `REPLACE`. `RESOLVED`, strategy selection, and
caller-supplied `validation_confirmed` grant zero authority. Trustworthy
Production acquisition of confirmation remains a future separately bounded
validation concern. `mutation_authority=false`; `capability_id=null`.

It stores/transports no credential or secret value and introduces no password,
username, secret-derived hash/digest, private identity, recipient value,
arbitrary path, environment value, stdout/stderr, command, argv, executable,
callback, port, authorization, mutation budget, execution request, or receipt.
All six existing Shopping provisioning actions remain unchanged;
`SHOPPING_SECRET_PROVISIONING` is their target identifier, not a seventh action.

The milestone changes no authorization-consumption port or durable SQLite
semantics, budget, controlled-execution, SEC-02, postcondition, Governance
audit/evidence, coordinator, adapter, config, schema, or inspector behavior. It
does not implement or claim Production credential validation, recovery,
rotation, replacement, `MARIADB_CREDENTIAL_ROTATE`,
`MARIADB_CREDENTIAL_REPLACE`, DB payload/materialization, DB-dependent
validation, WordPress/WooCommerce DB cutover, runtime cutover, or
`SHOPPING_RUNTIME_ACTIVATED`. Historical credentials were not claimed
recovered, validated, rotated, replaced, materialized, or activated.

Mac mini M4 AIControlCenter remains the sole Control Plane. Ubuntu remains a
stateless infrastructure worker; WordPress, WooCommerce, n8n, Ubuntu, and
external recovery custody systems receive no delegated authority. Validation:
focused `39 passed in 0.04s`; canonical `3510 passed`, `5 deselected`, `447
warnings`, `RC=0`. Final architecture review: `PASS`, `CRITICAL=NONE`,
`HIGH=NONE`, `MEDIUM=NONE`, `LOW=NONE`. Implementation push: `PASS`. Production
access: `NOT_PERFORMED`. Notion sync: `NOT_PERFORMED`.

## SM-01B-02D-04B Provisioning Runtime Composition & Read-Only Postconditions v1

SM-01B-02D-04B is CLOSED at implementation commit
`a4cb53d5398dffdc33366ac042fdb7813f6d4577` (`feat(shopping): add secret
provisioning readiness composition`). Mac AIControlCenter remains the sole
Control Plane and Ubuntu an optional stateless worker. Its JSON-first,
deterministic, read-only projection is structural and value-free, excluding
secret/recipient values, private identities, arbitrary paths, stdout/stderr,
environment values, and mutation authority.

Readiness is closed to `READY`, `MISSING`, `BLOCKED`, `UNSAFE`, and
`MALFORMED`. Configured/ready false/false, true/false, true/true, and false/true
map to `MISSING`, `BLOCKED`, `READY`, and fail-closed `MALFORMED`; malformed
state blocks readiness and activation. All six actions remain unchanged,
offline intake and registration remain separate, and Governance authorization,
durable consumption, and `ControlledExecutionPort` semantics are unchanged.
No mutation API, payload, materialization, or cutover was added or performed;
`materialization_implemented=false`, `SHOPPING_RUNTIME_ACTIVATED=false`.

Historical MariaDB continuity remains unresolved and blocks DB payload
readiness/materialization, DB validation and cutover, and runtime activation.
04B claims no credential recovery/replacement; dedicated Shopping
materialization architecture remains future work. Validation: focused `47
passed`; canonical `3471 passed, 5 deselected, 447 warnings` in approximately
`133.97s`, `CANONICAL_RC=0`, `CANONICAL_GATE=PASS`; implementation push, clean,
divergence `0 0`, and closeout gates PASS. Production access and Notion sync
were not performed; canonical was not rerun for docs closeout.

## SM-01B-02D-04A Governed Offline Public Recipient Intake v1

04A implementation and validation are complete at
`6e1aa0135b652b199f05a4911c0f45817a8529f4`; implementation and documentation closeout are complete, so the milestone is CLOSED. The provisioning model now has a
sixth bounded action,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`, for one typed,
value-redacted, already-public age recipient at the fixed Mac Control Plane
inbox. It is separate from
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`; each action
requires its own fresh authorization, budget, request, and durable consumption
record.

The private offline-recovery identity stays external to the Production Mac.
The intake is fixed-path, outside Git, no-clobber, owner/mode checked, and
descriptor/inode bound; ambiguous post-mutation outcomes are `UNCERTAIN` with
no cleanup or retry. Validation: focused `163 passed`; canonical `3457 passed,
5 deselected, 447 warnings in 133.23s`, `RC=0`; implementation Git closeout
PASS, clean, divergence `0 0`. No Production intake or other Production
mutation occurred. MariaDB continuity remains unresolved, Notion remains
deferred, and `SHOPPING_RUNTIME_ACTIVATED=false`. 04B is CLOSED as documented
above.

## SM-01B-02D-03 Durable Authorization Consumption & Evidence Store v1

Validated at `SM_01B_02D_03_DURABLE_AUTHORIZATION_CONSUMPTION_VALIDATED=true`;
implementation commit `681a9e342fde47c7bcb9d3aa2d497b737a19e052`. The generic
Governance implementation belongs to the Mac AIControlCenter Control Plane, not
Shopping or Ubuntu. `AuthorizationConsumptionPort` is unchanged and
`CORE_SEMANTICS_CHANGE_REQUIRED=false`.

Its Governance-owned SQLite Production store remains outside Git/source at
`~/Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3`.
Path ownership is validated; the shared application-state parent is not mutated
or forced to `0700`; Governance is `0700` and the database `0600`.
`DURABLY_CLAIMED` precedes an atomic final transaction recording authorization
and mutation budget `CONSUMED`, zero invocation/completed/uncertain accounting,
and the `COMMITTED` receipt. All protected lifecycle, authorization, budget,
claim, execution, request, and decision identities use replay-protected,
value-free canonical binding/integrity digests. No secret value persists.

Fresh replay after `COMMITTED` and stranded `DURABLY_CLAIMED` both fail closed;
historical `AuthorizationConsumptionResult` is never returned externally. There
is no claim stealing, lease, expiry, automatic recovery, retry, rollback, or
compensation. Only the same invocation with ambiguous final commit acknowledgement
may reconcile, against its exact validated expected `COMMITTED` record.
Consumption evidence grants no execution authority and remaining budget is not
retry authority. Recollect/recompare current read-only preconditions, rerun
SEC-02, and obtain `ALLOW_SINGLE_INVOCATION` before `ControlledExecutionPort`;
replay cannot resurrect invocation authority.

Validation: focused `372 passed`; corrected-tree canonical `3433 passed, 5
deselected, 447 warnings in 135.93s`, `RC=0`, exactly once after final fixture
correction; implementation Git closeout PASS, pushed, divergence `0 0`.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, `NOTION_SYNC=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`.

SM-01B remains incomplete; no Production provisioning occurred. SOPS/age
installation, control-plane age identity creation, recipient registration,
secret payload/materialization, and runtime activation remain outstanding.
Historical MariaDB credential continuity remains unresolved and SOPS+age cannot
recover it. Offline-recovery private identity remains external to the Production
Mac; only public recipient metadata may enter the Control Plane, and its
operational inbox/intake write boundary needs explicit governance before
activation. Notion remains deferred until `SHOPPING_RUNTIME_ACTIVATED`.

## SM-01B-02D-02B Shopping Secret Provisioning Capabilities v1

Implementation, validation, and Git closeout are complete at
`SM_01B_02D_02B_SECRET_PROVISIONING_CAPABILITIES_VALIDATED=true`, implementation
commit `bffe28a153eb83d3c61e04d38f2ab96892a6feb5`.

The validated implementation provides five narrow Shopping secret provisioning
capabilities with explicit `expected_uid` injection and no ambient UID/HOME
authority. It fixes execution to a trusted Homebrew executable boundary and
exposes no generic shell/argv API. No-overwrite/no-clobber behavior is enforced;
mutation uncertainty fails closed; and no automatic retry, rollback, or
compensation exists. Python does not read the private control-plane age identity
for recipient derivation. Offline recovery remains public-recipient-metadata
only, and evidence remains value-free.

Focused validation recorded `421 passed`; canonical regression recorded `3387
passed, 5 deselected, 447 warnings in 132.49s`, `RC=0`, executed exactly once.
Git closeout: PASS. Upstream divergence: `0 0`. The closeout records
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, and `NOTION_SYNC=false`.

Actual SOPS/age installation, age identity creation, recipient registration,
secret materialization, and runtime activation have not occurred. Historical
MariaDB credential continuity remains explicitly unresolved, and
`SHOPPING_RUNTIME_ACTIVATED` remains the future Production milestone. Notion is
deferred until after Runtime Activation. Next engineering recommendation:
`SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store v1` —
generic Governance-owned, Mac Control Plane only, replay-safe and durable, with
no Shopping business logic.

## SM-01B-02D-01B Shopping Provisioning Governance Coordinator v1

Status: implementation and validation complete at
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

## SM-01B-02C Bounded Mutation Adapters v1

SM-01B-02C is implementation- and validation-complete at
`SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED`, implementation commit
`5a811cb1f9c782acb4f3e537596fb47ae0c599ff`. It implements bounded mutation
adapter code only. The adapters reuse SEC-02 `ControlledExecutionPort`, accept
only the exact `SHOPPING_SECRET_PROVISIONING` target and one of the five exact
Shopping provisioning actions, and invoke at most one narrow injected
capability. They issue and consume no authorization; do not retry, rollback,
or compensate; and emit value-free `GovernanceExecutionReceipt` evidence with
a deterministic injective identity namespace over the full
`execution_request_id`. They provide no generic shell/argv/package-manager
execution framework and create no parallel governance framework.

The five actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`.
Offline-recovery private custody remains external.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
infrastructure worker with no Shopping secret ownership. Historical MariaDB
credential continuity remains unresolved. SM-01B-02C does not recover, rotate,
replace, derive, invent, or validate historical credentials.

Production truth remains `production_status=NOT_DEPLOYED`;
`materialization_implemented=false`; `SOPS_INSTALLATION=false`;
`AGE_INSTALLATION=false`; `AGE_KEY_GENERATION=false`;
`OFFLINE_RECOVERY_KEY_GENERATION=false`; `SECRET_PAYLOAD_CREATION=false`;
`SECRET_MATERIALIZATION=false`; `AUTHORIZATION_CONSUMED=false`;
`RUNTIME_INSPECTION=false`; `PRODUCTION_MUTATION=false`;
`SHOPPING_RUNTIME_ACTIVATED=false`.

Final implementation validation recorded focused `128 passed` and canonical
`3288 passed, 5 deselected, 447 warnings`, `RC=0`, exactly once on final
implementation code. Exact three-file implementation scope, post-canonical
scope, staged scope, staged diff check, commit, push, and upstream alignment
`0 0` passed. Next: `SM-01B-02D — Authorized Toolchain & Identity Provisioning
v1`. Adapter implementation is not authorization to execute adapters. Every
future Production mutation requires separate human authorization immediately
before exactly one bounded invocation, with no automatic retry or rollback.
SM-01B overall remains incomplete.

## SM-01B-02B Provisioning Planner v1

SM-01B-02B is implementation- and validation-complete at
`SM_01B_02B_PROVISIONING_PLANNER_VALIDATED`, implementation commit
`2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`. The canonical provisioning
definition and Draft 2020-12 schema define exactly five typed actions. The core
`ProvisioningPlan` is vendor-neutral and value-free; malformed input exposes
only sanitized `UNKNOWN_ACTION` or `MALFORMED_CONFIGURATION` evidence. The
read-only macOS provisioning inspector plans only. Core imports from `ops` and
`integrations` remain zero. Any future execution must reuse SEC-02
`ControlledExecutionPort`, without a parallel governance framework.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
worker and owns no Shopping secrets. Offline-recovery custody remains external,
and historical MariaDB credential continuity remains unresolved. This
milestone does not recover, replace, rotate, or invent historical credentials.
Production remains `NOT_DEPLOYED`; `materialization_implemented=false`.
`SOPS_INSTALLATION=false`, `AGE_INSTALLATION=false`,
`AGE_KEY_GENERATION=false`, `OFFLINE_RECOVERY_KEY_GENERATION=false`,
`SECRET_PAYLOAD_CREATION=false`, `SECRET_MATERIALIZATION=false`,
`AUTHORIZATION_CONSUMED=false`, `RUNTIME_INSPECTION=false`,
`PRODUCTION_MUTATION=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.

Recorded final implementation validation is `73 passed` focused and `3236
passed, 5 deselected, 447 warnings`, `RC=0` canonical regression, run exactly
once on final implementation code. Exact six-file implementation scope,
post-canonical scope, staged scope, staged diff check, commit, push, and
upstream alignment passed. Next: `SM-01B-02C — Bounded Mutation Adapters v1`;
adapter implementation is not execution authorization. SM-01B remains
incomplete.

## SM-01B-01 SOPS/age Secret Backend Inspection v1

SM-01B-01 implementation and validation are complete at
`SM_01B_01_SECRET_BACKEND_INSPECTION_VALIDATED` (implementation commit
`1ada572a75cf4313f65288e81134777948900cda`). SOPS+age is the selected
replaceable Shopping secret-backend architecture, not a deployed backend.
Canonical metadata is in `config/shopping-secret-backend.json` with its schema
at `config/schemas/shopping-secret-backend.schema.json`; the vendor-neutral
port is `core/secrets/ports.py`, and macOS-specific metadata-only inspection is
isolated in `ops/macos/shopping/sops_age_backend.py`.

The Mac remains the sole Control Plane; Ubuntu owns no secrets. Portable age
identity custody uses injected `control_plane_home` plus
`.config/sops/age/keys.txt`, never a canonical `/Users/<username>` path. The
adapter reads no identity or encrypted payload contents and performs no HOME,
environment, pwd, Keychain, runtime, Docker, Colima, or network discovery. The
logical encrypted payload is `deploy/shopping/secrets/shopping.enc.yaml`; its
value-free policy requires `control-plane` and `offline-recovery` recipient
roles while storing no recipient material.

Production status remains `NOT_DEPLOYED`. SOPS and age were not installed; no
key, encrypted payload, materialization, Production mutation, runtime
inspection, secret-value read, or Keychain query occurred.
`materialization_implemented=false` and `SHOPPING_RUNTIME_ACTIVATED=false`.
Historical MariaDB credential continuity remains unresolved and blocks runtime
cutover pending an explicit continuity, recovery, or rotation strategy. Next:
`SM-01B-02 — SOPS/age Toolchain & Identity Provisioning`; SM-01B overall is
not complete.

## SM-01A Shopping Secret Contract & Fail-Closed Preflight v1

SM-01A is complete as a documentation and implementation milestone. Its
single canonical, value-free metadata authority is
`deploy/shopping/config/secret-contract.json`; the Python preflight reads and
validates that JSON without duplicating the exact canonical key table. The
preflight is read-only, resolves action-specific required names, checks
presence only, and fails closed for malformed contracts, unsupported actions,
unknown supplied names, or missing required names. It neither reads nor emits
secret values and provides no authorization or mutation capability.

Only the contract and preflight layers exist. No secret delivery backend,
SOPS/age/Keychain deployed selection, secret materialization, or Production
mutation layer exists. Compose keeps plain `${SHOPPING_*}` interpolation so
runtime observation remains independent of secret material. The Shopping
service and WooCommerce capability remain `NOT_DEPLOYED`;
`SHOPPING_RUNTIME_ACTIVATED=false`; no port cutover or Production activation
occurred. The desired loopback WordPress binding remains
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80` at port `58082`, with MariaDB
unpublished.

See [SM-01 Secret Management](docs/architecture/SM-01-SECRET-MANAGEMENT.md).
Next development milestone: `SM-01B — Secret Delivery Backend v1`.

## PA-04 Notification Platform v1

PA-04 is validated and closed after Git closeout at milestone
`NOTIFICATION_PLATFORM_V1_VALIDATED`. AIControlCenter owns notification intent,
routing policy, provider selection, governance, authorization, audit, retry
policy, and the future delivery lifecycle; providers own transport capability
only. `core.notifications` is provider-neutral,
`integrations.notifications` contains observation-only adapters, and
`ops.macos.runtime.application` is the outer composition root. Core imports
neither `ops.*` nor `integrations.*`.

Provider observations fail closed. Only explicitly `AVAILABLE`, configured and
available providers are routable. Invalid identities are never echoed and
normalize to `UNKNOWN`. Telegram is the optional, `NOT_DEPLOYED` reference
provider; readiness/configuration require explicit observation, and no runtime
or network convention is inferred. Provider status and routing status are
separate, and v1 has no delivery lifecycle because execution is absent.

The exact new read-only surface is `GET /api/notifications/platform` and
`GET /api/notifications/providers`; it offers no mutation, send, retry,
transport, Production authorization, or infrastructure operation. Existing
`GET /notifications` and `POST /notifications` remain compatible and are
**LEGACY / OUTSIDE PA-04 SCOPE**. PA-04 neither calls nor depends on that
surface.

Final focused validation passed 85 tests after identity hardening; exactly one
canonical PA-04 regression invocation passed with `RC=0`; `git diff --check`
passed; and both core import counts are zero. No Production mutation,
Production notification, external provider I/O, or PA-04 execution occurred.
Legacy POST was exercised only through TestClient tests. No Notion
synchronization is claimed. OPS-01B and PA-01 through PA-03 remain closed and
unchanged. See
[`docs/architecture/PA-04-NOTIFICATION-PLATFORM.md`](docs/architecture/PA-04-NOTIFICATION-PLATFORM.md).

## PA-03 n8n Control Plane Adapter v1

PA-03 is validated and marked closed after Git closeout at milestone
`N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`. n8n is a replaceable external
automation capability, not the AIControlCenter Control Plane. AIControlCenter
retains business logic, workflow and orchestration policy, Production
authorization, governance, audit, deployment control, infrastructure mutation
authority, and business/customer state.

The dependency direction is `ops.macos.runtime.application` →
`integrations.n8n` → `core.capabilities`, with dependency injection into
`core.api.create_app`; core imports neither `ops.*` nor `integrations.*`.
Existing `core.capabilities` contracts and `CapabilityStatusService` are
reused; PA-03 creates no second capability framework. Platform-neutral
`create_app` performs no n8n discovery and, without an injected adapter, fails
closed with value-free `UNAVAILABLE` evidence. macOS outer application
composition injects the adapter and truthfully projects `NOT_DEPLOYED`.

The only PA-03 v1 API projection is `GET /api/capabilities/n8n`. No
POST/PUT/PATCH/DELETE capability implementation, workflow execution,
workflow enable/disable, webhook or credential creation, schedule mutation,
Production authorization, or infrastructure mutation exists. The canonical
manifest/schema is validated before its unique n8n identity is trusted. Its
current truth is optional, `NOT_DEPLOYED`, `runtime_health=false`,
`runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`. No sufficiently proven
executable, lifecycle, log, or runtime identity exists, so no PA-01
`service_platform` lifecycle definition was added.

Configuration, authentication, runtime, and transport remain `UNKNOWN` unless
explicitly injected as evidence; implementation invents no n8n endpoint,
environment, or authentication convention. Secret/config evidence is
value-free: URLs, API keys, tokens, cookies, headers, webhook secrets,
environment values, configuration contents, and exception messages are not
projected. Shared governance explicitly reports
`platform_business_policy_ownership=false` for external capabilities, while
PA-02 OpenClaw remains compatible.

Focused PA-03 validation passed 96 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-03 canonical invocation, and
`git diff --check` passed. No Production mutation or n8n workflow, credential,
Docker, launchd, `runtime/current`, or live-service operation occurred. No
Notion synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
unchanged. See
[`docs/architecture/PA-03-N8N-ADAPTER.md`](docs/architecture/PA-03-N8N-ADAPTER.md).

## PA-02 OpenClaw Adapter v1

PA-02 is validated and closed after Git closeout at milestone
`OPENCLAW_ADAPTER_V1_VALIDATED`. OpenClaw is an optional, replaceable external
capability, not a Control Plane. AIControlCenter retains business logic,
governance, Production authorization, deployment control, workflow policy,
infrastructure mutation authority, audit, and business/customer state.

The dependency direction is `ops.macos.runtime.application` →
`integrations.openclaw` → `core.capabilities`, with dependency injection into
`core.api.create_app`; core imports neither `ops.*` nor `integrations.*`.
Platform-neutral `create_app` performs no discovery and fails closed with
value-free `UNAVAILABLE` evidence without injection. macOS composition injects
the adapter and projects the schema-validated manifest truth: optional,
`NOT_DEPLOYED`, and `runtime_health=false`.

The only API surface is `GET /api/capabilities/openclaw`; no mutating capability
method, prompt forwarding, tool/action or lifecycle execution, Production
authorization, or infrastructure mutation exists. No trustworthy
launchd/runtime/Service Platform identity is proven, so no `service_platform`
lifecycle definition was added. Endpoint, authentication, transport, and
runtime identity remain `UNKNOWN`/unproven by default, with no
`OPENCLAW_ENDPOINT` or `OPENCLAW_API_KEY` convention. Evidence projects no
secret/config values or exception messages. Focused validation passed 79 tests;
the canonical deployment regression passed with `RC=0` on exactly one PA-02
canonical invocation. No Production mutation or additional live-service
operation occurred, and no Notion synchronization is claimed. See
[`docs/architecture/PA-02-OPENCLAW-ADAPTER.md`](docs/architecture/PA-02-OPENCLAW-ADAPTER.md).

## PA-01 Control Plane Service Platform v1

PA-01 is closed after Git closeout at milestone
`CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`. The canonical service manifest
is the service-definition source of truth. Pure-core `ServiceDefinition`
describes a service; `ServiceHealth` remains sole owner of aggregate runtime
health; and `core` has zero direct `ops.*` imports.

The macOS composition in `ops/macos/runtime/service_platform.py` provides
`inspect_platform_services()`, combining `ServiceTopology.platform_services()`,
existing `ServiceHealth` launchd/heartbeat observation, strict filesystem
readiness, and authoritative immutable `runtime/current`/Source validation
without executing Production worktree code. Stable owner/group names resolve
only at the macOS boundary. Exact file type, symlink, mode, owner, and group
checks fail closed. Only `ENOENT` means missing; other inspection failures
produce value-free evidence.

Lifecycle remains inspect-only. Dry-run bootstrap planning metadata is eligible
only for `NOT_DEPLOYED` with trusted launchd observation, ready filesystem, and
immutable runtime/source preconditions. It has no authorization and performs no
mutation, retry, rollback, or kickstart. Application Scheduler and canonical
API behavior did not change; the API entrypoint remains
`ops.macos.runtime.application:app`, and Shadow remains separate.

Final focused validation passed 94 tests under umask `077`; exactly one
canonical deployment-regression invocation for the final candidate passed with
`RC=0`; `git diff --check` passed; and no Production mutation occurred. No
Notion synchronization is claimed. WordPress and Shadow maintenance remains
deferred and separate.

## Canonical Production API and Homepage

Current Production release: `ef07532bd3d7`, from commit
`ef07532bd3d7ba91868d46375d48cac4821d6a56`.

The Mac mini M4 is the always-on Brain and sole Control Plane. Host Caddy is
the only public edge. The active Python Runtime is
`runtime/venvs/ef07532bd3d7`, selected by `runtime/current`, and both the
shadow and canonical API execute from the paired immutable Source
`runtime/sources/ef07532bd3d7`. WordPress remains the CMS Engine,
WooCommerce remains the Commerce Engine, and Ubuntu remains an optional
stateless infrastructure worker with no application state or Control Plane
authority.

The canonical API and Homepage recovery is complete. The canonical launchd
service is running from the immutable Source; direct health behavior is
`GET /health = 200` and `POST /health = 405`. Public DNS resolves through the
host edge, HTTP redirects to HTTPS, and public `/health` and
`/homepage/product-management` return `200`.

Production operations remain JSON-first, read-only-first, Git-first, and
fail-closed. One human authorization permits one bounded Production mutation
invocation. A successful mutation followed by wrapper or observation failure
enters read-only reconciliation and is never retried automatically. Duplicate
lifecycle requests must fail before authorization or mutation when the
observed precondition no longer matches. Immutable Source artifacts reject
writable objects and generated Python bytecode; privileged Python executors
must set `sys.dont_write_bytecode = True` before importing project-local
modules. A contaminated immutable release is retired and replaced, never
repaired in place.

Whole-runtime health remains degraded and is open operational debt. Although
`GET /runtime/health` returns HTTP `200`, its JSON reports `healthy=false`, API,
Telegram, and scheduler services `unavailable`, and a stale scheduler
heartbeat. This does not invalidate the completed canonical API/Homepage
recovery, and it must not be represented as full platform health.

## SHOP-AI-01A ProductDraft Generation Foundation

Status: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified
HEAD `52db3600ae76c70926e27ce930be70fe34f98452`; canonical regression: `2691
passed, 5 deselected, 437 warnings` via
`ops/macos/validation/run-deployment-regression-gate.sh -q`.

The canonical `core/shopping/` domain now has a bounded preparation service
that reuses SHOP-02 `ProductDraft`, existing `ProposedFields`, immutable
revisions, and the canonical provider adapter. Contract `1.0.0` produces an AI
provenance-bearing candidate that remains `DRAFT`; it performs no validation,
approval, deployment, API/Dashboard mutation, persistence, or Commerce write.
Provider execution uses one injected provider, one attempt, bounded timeout,
and no fallback. The in-memory coordinator provides scoped at-most-one
invocation and concurrent duplicate suppression but is non-production and not
durable. See
[`docs/architecture/SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md`](docs/architecture/SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md).
Next: `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`; recommendation
architecture is the separate future stream
`SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE`.

## SHOP-01A2 Repository and Architecture Reconciliation

Status: `SHOP-01A2_REPOSITORY_UTILIZATION_AND_ARCHITECTURE_RECONCILED`.
SHOP-01A is a retrospective reconciliation of existing SHOP-01/02/03 work, not
a greenfield restart. At SHOP-01A1 HEAD
`f95ba9ae2133b55db06c362df321b16785f21423`, the canonical wrapper
`ops/macos/validation/run-deployment-regression-gate.sh -q` reported `2670
passed, 5 deselected, 437 warnings`. Shopping remains GET-only with one outbound
GET attempt per read invocation and no automatic retry. Production mutation
authority remains disabled. See
[`docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md`](docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md).
Next: `SHOP-01A3_CLOSEOUT_AND_FINAL_SYNC`; Notion payload is
`READY_FOR_FINAL_SYNC`, not synchronized.

## SEC-02A Governance Control Plane Architecture Ready

Status: `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`

The A0-A10 SEC-02A architecture phase is complete. AIControlCenter now has a
reusable Governance Control Plane architecture with strict authorization,
precondition, consumption, single-invocation, failure-stop, evidence, adapter,
and READ ONLY projection boundaries. The canonical closure record is
[`docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md`](docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md).

This milestone enables no concrete Production execution adapter or Production
mutation, no Shopping write automation, no automatic retry or rollback, and no
Ubuntu Governance authority. The next production-development milestone is
`SHOP-01A_SHOPPING_PLATFORM_ARCHITECTURE_AND_READ_ONLY_FOUNDATION`; commerce
writes remain separately governed and require explicit future authorization.
Notion external synchronization has not been performed; documentation payload
status is `READY_FOR_FINAL_SYNC`.

## AI-PROVIDER-01C-A Control Plane Workflow Integration

The canonical `BrainAgent.ask` workflow now selects an explicit configured or
request-supplied provider through `ProviderRouter`, which is the application
provider boundary. Business logic receives only normalized JSON-safe results
from `ProviderAdapter`; it owns no vendor SDK transport behavior. Unknown
providers fail closed, and no automatic cross-provider fallback or retry is
allowed. Focused FakeProvider tests made zero network calls and no authenticated
provider call occurred. Production Runtime remains `7b171f135dc7`. 01C-B will
create a new Candidate Runtime; 01C-C requires explicit human authorization for
Production promotion. Notion is `DEFERRED_UNTIL_FINAL_PHASE`.

## AI-PROVIDER-01B Authenticated OpenAI Transport

The OpenAI Responses API transport is implemented behind the vendor-neutral
`ProviderAdapter` contract. `OPENAI_API_KEY` remains external, is read only at
invocation time, and must never be stored in Git. Requests have explicit model
and input, bounded timeout/output, exactly one attempt, and no cross-provider
fallback. Mocked repository tests made no network request; the human-controlled
authenticated smoke is pending. Production Runtime `7b171f135dc7` remains
untouched, AI-PROVIDER-01C owns candidate Runtime integration/promotion, and
Notion is `DEFERRED_UNTIL_FINAL_PHASE`. See
`docs/architecture/AI-PROVIDER-ADAPTER-ARCHITECTURE.md`.

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

Added three versioned read-only inspection contracts:

- `ActivationInspectionPolicy`
- `ActivationRouteManifest`
- `ActivationInspectionReport`

Validation evidence:

- Focused contract gate: `41 passed`
- Safe deployment regression: `1017 passed`
- Warnings: `9`
- Operational harness suites: `DEFERRED`

Deferred operational suites require isolated test-root
environments and are tracked separately as test-infrastructure
work.

Architecture base commit:

`dc482780fdd36ba50d4947e8193380d7426d8367`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:START -->
## ACTIVATION-01B Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

Architecture:

`docs/deployment/ACTIVATION-01B-READ-ONLY-INSPECTOR-ARCHITECTURE.md`

Runbook:

`docs/operations/macos/ACTIVATION-01B-READ-ONLY-INSPECTOR-RUNBOOK.md`

The frozen design defines a JSON-first, fail-closed inspector
for Git, Runtime, Python, launchd, process, listener and direct
localhost HTTP evidence.

The inspector implementation and real-host inspection have not
started.

Runtime activation, service restart, rollback, public opening,
Ubuntu changes and Production authorization remain prohibited.

Architecture predecessor commit:

`43975f6e26986fd91c9a715786e7c68deb63f612`
<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## ACTIVATION-01A Runtime Activation

Status: `COMPLETE`

Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`

Gate: `ACTIVATION-01A — Architecture and Runbook Only`

The atomic Runtime activation contract is documented at
`docs/operations/macos/ACTIVATION-01A-RUNTIME-ACTIVATION-CONTRACT.md`.

Bound baseline:

- Candidate Runtime: `acd80ab9f6ae`
- Active Runtime: `b9ad351a7241`
- Canonical serving target: `core.api.shadow:app`
- LaunchDaemon: `system/com.aicontrolcenter.api.shadow`
- Localhost listener: `127.0.0.1:18100`
- Production: `NOT_AUTHORIZED`

No Runtime switch, service restart, rollback, launchd or Caddy change,
public opening, Ubuntu change or Production authorization occurred.

The candidate application source remains repository-bound through
effective `PYTHONPATH`. ACTIVATION-01B is the next read-only gate after
the ACTIVATION-01A documentation commit.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## Current verified platform status

AIControlCenter remains the Mac mini M4-owned Control Plane, with Ubuntu only
as an optional stateless infrastructure worker. Controlled bootstrap tests now
use immutable trusted evidence binding and a deterministic canonical
non-production evidence generator instead of historical host evidence. Git
identity inspection is file-backed and read-only, with loose-ref precedence,
exact packed-ref fallback, detached-HEAD support, and fail-closed bounded
symbolic resolution.

Source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a` produced validated side-by-side
release `acd80ab9f6ae`. The canonical serving target is
`core.api.shadow:app`; its `ReadOnlyASGI` Shadow application composes internal
FastAPI target `core.api.app:app`. Dependency installation, application import,
the Full Suite, source marker, and metadata validation passed. FastAPI was
`0.139.0`, Uvicorn was `0.51.0`, and `jsonschema` was available.

The canonical macOS Runtime builder requires an explicit `build` or `activate`
mode and fails closed otherwise. Build uses owned staging, validates metadata
and the exact source marker, atomically finalizes an immutable release, and
preserves `runtime/current`. Activation is separately authorized, accepts only
an already finalized validated release, and atomically switches
`runtime/current` without installing dependencies or restarting services. The
builder is executable with Git mode `100755`, protected by a deterministic
regression test. Runtime current remains active release `b9ad351a7241`;
`runtime/current` was unchanged and new release `acd80ab9f6ae` was not
activated. Rollback foundations exist through side-by-side releases and an
atomic-current design, but neither activation nor rollback has occurred.

Direct localhost smoke returned 200 for `/health`, `/runtime/health`,
`/homepage/status`, `/homepage`, `/homepage/product-management`, and
`/datacenter/status`; `POST /health` returned 405. Exact smoke PID and listener
cleanup passed. The builder report was valid structured JSON on stdout and was
recovered and validated from the builder log after the wrapper found no
canonical report file. That report persistence gap and an unavailable optional
host `rg` command are operational tooling debt, not release defects.

The internal Homepage and Product Management Console have completed direct
localhost HTTP smoke, but not activation, staging, Caddy authentication, or
public exposure. Python and dependencies are release-owned; application source
is still loaded from the mutable repository through `PYTHONPATH`
(`source_bundled_inside_release=false`, `repository_source_binding=true`). The
release must not be described as fully source-immutable. Source bundling,
source manifesting, and source-independent launch remain future work.

The next controlled sequence is: documentation commit; non-force push and
remote verification; new-chat handoff before the activation risk boundary;
ACTIVATION-01A architecture and runbook only; read-only activation preflight;
separately authorized atomic switch; exact service restart; post-activation
validation; rollback validation; and authenticated Caddy staging. Runtime
activation, rollback execution, service restart, public staging, production,
and production writes remain `NOT_AUTHORIZED`. No service, launchd, Caddy,
Ubuntu, public, or production change occurred.

M3-A4B2B2B-R4 aligns the strict preflight and live permit contracts. The exact
Boolean `ubuntu_participation=false` is accepted only as Ubuntu
non-participation evidence; all unsafe alternatives remain default-deny.
Permit issuance and orchestration now share an immutable typed result. The
authorized attempt was `BLOCKED_PRE_AUTHORIZATION`; no actual authorization,
permit, claim, bootstrap, or managed target exists. Fresh approval must bind
R4, production remains `NOT_AUTHORIZED`, and M3-A4B3 remains blocked.

Recovery-2 closes the first blocked R3 recovery with a bounded read-only
`/usr/bin/git` adapter isolated in `core.deployment.git_readonly_evidence`.
Public audit/replay inspectors, PRE_ACTIVATION monitoring, and post-claim
failure evidence are independently validated. The validation runner remains
validation-only; actual bootstrap is `NOT EXECUTED`, managed targets remain
absent, fresh approval must bind the final commit, and production is
`NOT_AUTHORIZED`.

The previous M3-A4B2B2B-R3 attempt was `BLOCKED`. R3 recovery adds the
reviewed default live composition and mandatory pytest-only end-to-end
orchestration. The existing execution runner remains validation-only; the live
runner uses the dedicated composition root. No actual Mac bootstrap ran,
actual managed targets remain absent, fresh independent approval must bind the
recovery commit, and production activation remains `NOT_AUTHORIZED`.

## M3-A4B2B2B-R1 closure

Existing safe Mac application-state parents are compatible with controlled
bootstrap without changing parent metadata or unrelated siblings. Deployment
control owns only absent `audit`, `security` and `monitoring` children. Mode
`0755` is accepted with an explicit restriction; managed directories remain
`0700` and managed files `0600`. Recovery was read-only: no operational permit,
claim or bootstrap occurred. Fresh approval is required and Production remains
`NOT_AUTHORIZED`.

## M3-A4B2B1A closure

The deterministic operational permit issuance review package is AVAILABLE.
M3-A4A, M3-A4B1, M3-A4B2A, M3-A4B2B0 and M3-A4B2B1A are CLOSED after
validation. Human identities and restriction acknowledgements are NOT PROVIDED.
No permit is issued or claimed, no bootstrap is authorized or executed, no
operational target is created, and production remains NOT_AUTHORIZED. Next:
M3-A4B2B1B.

AIControlCenter is the Brain of the AI Home Datacenter.

## Brain
- Mac mini M4
- AI Agents
- FastAPI
- Telegram
- Provider Manager
- BrainAgent
- Command Router

## Optional Worker
- Ubuntu
- Docker
- Storage
- Backup
- Immich
- Nextcloud
- Plex

## Telegram Commands

/status
/storage
/backup
/tasks
/help
/ask <message>

## Current Status

Core Platform is operational.

### M3-A4B2B0

M3-A4A, M3-A4B1, M3-A4B2A and M3-A4B2B0 are closed. The deterministic,
read-only Mac operational bootstrap host preflight is available. Operational
permit is not issued, authorization is not granted, bootstrap is not executed,
operational directories and databases are not created, and Production
activation is `NOT_AUTHORIZED`. Next: M3-A4B2B1 Operational Permit Issuance.

### M3-A4B2A

M3-A4A, M3-A4B1 and M3-A4B2A are closed. The controlled Mac bootstrap
executor is implemented and validated only beneath injected pytest temporary
paths. Synthetic permit consumption, audit/replay schema bootstrap, baseline
backup/restore and failure cleanup are validated. No operational permit was
issued, operational bootstrap was not executed, operational state was not
created, writers and monitoring were not activated, and Production activation
is `NOT_AUTHORIZED`. Next: M3-A4B2B Authorized Mac Operational Bootstrap
Execution.

### M3-A4B1

M2, M3-A1, M3-A2, M3-A3, M3-A4A and M3-A4B1 are closed. Controlled
non-production bootstrap authorization contracts and a single-use registry
port are available; synthetic permit issuance is validated. No operational
permit was issued, bootstrap authorization was not granted, bootstrap was not
executed, operational paths were not created, writers were not activated, and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2 Controlled Mac
Operational Bootstrap.

### M3-A4A

M2, M3-A1, M3-A2, M3-A3 and M3-A4A are closed. The pure activation readiness
gate and controlled bootstrap plan are available, but neither authorizes nor
executes bootstrap or activation. Operational databases are not created;
operational writers and monitoring are not activated; external alert dispatch
is not implemented; bootstrap authorization is not granted; Production
activation is `NOT_AUTHORIZED`. Next: M3-A4B Controlled Mac Operational
Bootstrap.

### M3-A3C

M3-A1, M3-A2, M3-A3A, M3-A3B and M3-A3C are closed; the M3-A3 Monitoring and
Alert Track is closed. The deterministic end-to-end monitoring drill and
simulated logical delivery are validated using only an object-scoped in-memory
sink. External dispatch and alert persistence are not implemented. Operational
monitoring is not activated, operational databases were not created, and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4 Controlled Operational
Activation Gate.

### M3-A3B

M3-A1, M3-A2, M3-A3A and M3-A3B are closed. Logical alert routing,
deterministic deduplication and severity escalation policy are available.
External alert dispatch and alert-routing persistence are not implemented.
Operational monitoring is not activated, operational databases were not
created, and Production activation is `NOT_AUTHORIZED`. Next: M3-A3C
Monitoring and Alert Operational Drill.

### M3-A2A

M2 controlled pilot validation, M3-A1 and M3-A2A are closed. Deterministic
read-only permit/replay SQLite inspection is available for an explicitly
injected Mac application-state path. The operational permit/replay database
was not created; durable reservation, consumption and persistent nonce writes
are not enabled; Production activation is `NOT_AUTHORIZED`. Next: M3-A2B
Durable Permit Reservation and Consumption.

### M3-A1C

M2 controlled pilot validation and M3-A1A through M3-A1C are closed. SQLite
online backup, separate-target restore and deterministic recovery validation
were verified only with pytest temporary databases. The operational audit
database was not created, an operational backup schedule was not activated,
an operational restore was not performed, persistent audit writer activation
is not started, and Production activation is `NOT_AUTHORIZED`. Next: M3-A2
Durable Permit and Replay State.

### M3-A1B

M2 controlled pilot validation, M3-A1A and M3-A1B are closed. The separate
append-only SQLite writer is implemented and verified only with pytest-owned
temporary databases. No operational database was created, operational writer
activation is not started, persistent Production audit writes are not enabled,
and Production activation is `NOT_AUTHORIZED`. Next: M3-A1C Backup, Restore
and Recovery Validation.

### M2-P3

M2-P3 is closed. Immutable activation evidence is validated before a fixed,
evidence-derived plan can reach an injected test-only rollback port. Exactly
one controlled activation and rollback were validated only in pytest-owned
temporary sandboxes. Persistent host activation is not started, persistent
host rollback and persistent SQLite audit are not implemented, and Production
activation is `NOT_AUTHORIZED`. Next: M3-A1 Durable SQLite Audit Adapter.

### DPL-04C

DPL-04C is closed. AIControlCenter owns durable deployment audit on the Mac
Control Plane. Pure immutable audit contracts define canonical JSON, stable
digests and tamper-evident hash-chain verification behind a replaceable
`DurableAuditPort`. The selected future adapter is an append-only SQLite ledger;
no adapter, database, persistence or API write path is implemented. DPL-04A,
DPL-04B and DPL-04C are closed; DPL-04D is ready, M2 is not complete and
production activation is `NOT_AUTHORIZED`.

### DPL-04B

The Mac-only sandbox adapter implements the typed non-production executor port
for development, test and staging. Its root must be explicitly injected; the
default remains deny-only. It writes only canonical JSON manifest/evidence
files below that confined root and performs no command, network, service,
Ubuntu, repository or production operation. Evidence is not durably persisted
as audit state, and production activation remains unauthorized.

Next Sprint

- DPL-04D

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform

AI Shopping Platform is a service layer inside AIControlCenter.

Current status:

- Development environment: Virtual
- Production target: Mac mini M4
- Frontend and CMS: WordPress
- Commerce engine: WooCommerce
- Business logic: AIControlCenter
- AI operations: AI Agent
- Automation execution: n8n
- Current write mode: Read-only

Shopping documentation:

- docs/shopping/README.md
- docs/shopping/ARCHITECTURE.md
- docs/shopping/API.md
- docs/shopping/TESTING.md
- docs/shopping/DEPLOYMENT.md
- docs/shopping/RUNBOOK.md
<!-- AI_SHOPPING_PLATFORM_END -->

## SHOP-03A controlled Commerce write boundary

SHOP-03A is complete with immutable eligibility, exact deny-by-default authorization, successful-plan idempotency, deterministic preview, and only an isolated fake/dry-run Commerce write adapter. A real WooCommerce write adapter is `NOT_IMPLEMENTED`; there is no mutation route or persistent queue. ProductDraft contracts remain 1.0.0 and production writes remain `NOT_AUTHORIZED`. SHOP-03B requires separate explicit architecture and authorization.

<!-- SHOPPING_M4_START -->

## AI Shopping Platform — M4

AI Shopping Platform is integrated as an AIControlCenter service layer.

Implemented capabilities:

- WordPress CMS runtime
- WooCommerce Commerce Engine
- Read-only product and category APIs
- Mock and WooCommerce Adapter selection
- systemd runtime configuration
- Git-excluded Secret management
- External HTTP development access

Production HTTPS remains blocked until a user-owned domain is available.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## AI Shopping Platform — M5 Storefront

AI Shopping Platform now provides an external Storefront powered by AIControlCenter.

Implemented:

- Featured Products
- Product Search
- Category Filter
- Price Filter
- Stock Filter
- Pagination
- Product Image and Placeholder
- Modular WordPress Presentation Plugin
- External Storefront page

Storefront:

http://bokstory.iptime.org:58088/ai-shopping/

WordPress remains the Presentation Layer.
AIControlCenter owns all Shopping business logic.
<!-- SHOPPING_M5_END -->

---

## Orange Coco Homepage

The storefront now renders curated homepage sections.

- NEW ARRIVALS
- BEST SELLERS
- TOP
- DRESS
- OUTER
- BAG
- SALE

Homepage collections are rendered from AIControlCenter Shopping API.

<!-- AI_SHOPPING_STOREFRONT_V016_BASELINE -->
## AI Shopping Storefront v0.16.0

The AI Shopping Storefront is a presentation adapter for the
AIControlCenter Shopping API.

Runtime assets:

- `assets/storefront.css`
- `assets/orange-coco-v6.css`
- `assets/storefront-ui.js`

Product detail contract:

- Existing product: `GET /product/{id}/` returns HTTP 200
- Missing product: `GET /product/{id}/` returns HTTP 404
- Product data is supplied by AIControlCenter
- WordPress owns presentation, not shopping business logic

Runtime validation:

- WordPress PHP 8.3
- Homepage HTTP 200
- Product detail HTTP 200
- Missing product HTTP 404

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Production Baseline

The Mac mini M4 is the always-on Brain and the
single AIControlCenter Control Plane.

Current validated baseline:

- Branch: `sprint/mac-control-plane-foundation`
- Commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/1e102c001c28`
- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Listener: `127.0.0.1:18100`
- Health contract: HTTP `200`
- Mutating request contract: HTTP `405`
- Mode: `shadow-read-only`
- GUI login required: `false`
- Transactional canonical apply: implemented
- Transactional rollback: implemented
- launchd bootout settle policy: 2 seconds
- Final restart: `19761 → 19842`

Shadow observation:

- Duration: `23.535` hours
- Samples: `283/283` passed
- Failed samples: `0`
- Success ratio: `100.0%`
- PID transitions: `0`
- Observation SHA-256:
  `a1c79121ff04699d0ee717d72aa158e81c954fe84387c0689a1c5c08fb83519d`
- Summary SHA-256:
  `c980df46e94b40b0b72086a55501f2cad4f748ad98d4f6ec7ceea9c15a02c8de`

Control Plane implementation is complete.
Production write cutover remains blocked pending
an explicit Production approval.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## Dashboard Shadow Control Plane

AIControlCenter exposes a read-only Control Plane status contract through the Mac mini Shadow API.

Runtime endpoint:

- Listener: `127.0.0.1:18100`
- Health: `GET /health`
- Dashboard: `GET /dashboard`
- Write requests: rejected with HTTP `405`

The Dashboard response includes:

- Control Plane service identity
- Shadow operating mode
- Read-only enforcement state
- Local listener address
- Commit-specific Runtime metadata
- Runtime metadata validation status

Runtime identity requires immutable `metadata.json` and
`.aicontrolcenter-source-commit` files generated together during explicit
build mode. The marker is an exact lowercase 40-character Git SHA plus one
newline. Build finalizes only after generation and validation and does not
change `runtime/current`. Explicit, separately authorized activate mode
revalidates the finalized release before the atomic switch, and the Shadow
daemon fails closed when the marker is missing or invalid. Existing immutable
releases are not repaired in place.

Dashboard requests do not execute Git, `launchctl`, or shell commands.

Runtime activation is allowed only after:

1. Dependency installation succeeds.
2. Application import succeeds.
3. The test suite succeeds.
4. Runtime metadata is generated.
5. Runtime metadata schema validation succeeds.

Current validated PI-001 Runtime:

- Commit: `ba8d2c9772577863c3c040d01654c4f011e2d45e`
- Short commit: `ba8d2c977257`
- Health status: HTTP `200`
- Dashboard status: HTTP `200`
- Write probe: HTTP `405`

<!-- AICONTROLCENTER:PI-002:START -->
## Ubuntu Worker Monitoring

AIControlCenter exposes Ubuntu worker monitoring through the Mac mini Control Plane.

Production endpoints:

- `GET /health` — Control Plane availability
- `GET /dashboard` — integrated Control Plane and worker status
- `GET /workers` — worker monitoring data

The Production Dashboard monitors `ubuntu-main` by default.

Worker transport failures are represented as structured JSON with `OPTIONAL_UNAVAILABLE` status. The Dashboard remains available with HTTP `200`.

Production baseline:

- Implementation commit: `39dc5c3db72c9ac1592fc3920012aba3eacd23cd`
- Immutable implementation runtime: `39dc5c3db72c`
- Supervisor: system LaunchDaemon
- Worker configuration: `config/workers.mac-production.yaml`
- Worker environment contract: `root:staff 640`
- Regression result: `412 passed, 5 deselected`
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## Mac Standalone and Optional Ubuntu Worker

AIControlCenter runs independently on the Mac mini when the Ubuntu worker is offline.

Validated behavior:

- Control Plane health remains `ONLINE`.
- `GET /health` remains HTTP `200`.
- `GET /dashboard` remains HTTP `200`.
- The offline Ubuntu worker is reported as `OPTIONAL_UNAVAILABLE`.
- Worker errors remain structured JSON.

Ubuntu service recovery:

- Docker is enabled and active after boot.
- Immich containers start automatically.
- Nextcloud containers start automatically.
- Required containers use `restart: unless-stopped`.

Ubuntu may remain powered off until its infrastructure services are required.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## Mac Standalone Production Baseline

PI-004 validated AIControlCenter as an independent Mac mini Production platform.

- `/health` returned HTTP `200`.
- `/dashboard` returned HTTP `200`.
- `/homepage/status` returned HTTP `200`.
- Platform status remained `ONLINE`.
- Ubuntu remained optional and powered off.
- Storage and backup were reported as optional external capabilities.
- LaunchDaemon recovery after Mac reboot was validated.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## Mac Service Deployment Platform

PI-005 provides dependency-free JSON interfaces for service manifest validation, read-only planning, Mac service inspection, desired/actual diff, Ollama dry-run generation, and installation approval requests.

Ollama remains uninstalled and execution remains disabled. Actual installation requires a separate approved Sprint.
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
## Model Governance

AIControlCenter exposes a read-only model-governance endpoint:

`GET /api/governance/models`

The endpoint compares the AIControlCenter-approved model registry with the
inventory observed from Ollama.

Current Production baseline:

- mode: `read-only`
- default policy: `DENY`
- approved models: `0`
- observed models: `0`
- violations: `0`
- write operations allowed: `false`

Operational check:

`curl -fsS http://127.0.0.1:18100/api/governance/models`

The API supports `GET` only. Model pull, create, copy, and delete operations are
outside the approved PI-007 scope and remain denied.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — Model Governance Audit and Dashboard Integration

PI-008 is complete and active in Production.

Capabilities:

- immutable governance audit snapshots
- append-only SQLite persistence
- historical compliance comparison
- read-only audit query services
- GET-only audit APIs
- Dashboard governance audit integration
- metadata-backed Production runtime identity
- Git-independent Production restart and rollback compatibility

Production identity:

- commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime: `b9ad351a7241`
- rollback runtime: `0352e396f329`

Validation:

- full suite: `636 passed, 5 deselected`
- Production health: online
- Dashboard: online and read-only
- Ollama models: `0`
- governance write methods: `0`
- audit database: outside runtime
- append-only SQLite triggers: valid

<!-- PI-009:START -->
## PI-009 Governance Audit Operations

PI-009 adds read-only operational visibility for governance audit
snapshot and SQLite online-backup verification workflows.

Key behavior:

- router-level GET `/operations` presentation;
- Dashboard key `governance_audit_operations`;
- strict API errors and panel-local Dashboard fail-soft behavior;
- missing database or schema produces an UNKNOWN read-only projection;
- no write actions are exposed;
- production migration and scheduler activation remain disabled.

Validated baseline:

- 17 targeted tests passed;
- 710 tests passed, 5 deselected;
- production database SHA-256 remained unchanged;
- WAL content remained unchanged.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Governance Operations — Closed

PI-009 was closed on 2026-07-22 with a JSON-first,
one-shot governance operation runner owned by
AIControlCenter.

Supported operations:

- governance_audit_snapshot
- sqlite_online_backup_verification

Runner interface:

    .venv/bin/python -m core.governance.operations.scheduler       --operation <operation> --once --json

Production composition:

- SQLiteOperationsEventRepository
- SystemUTCClock
- AutomationExecutor
- BackupVerifyService
- OperationsApplicationService

Safety boundaries:

- no automatic retry
- no automatic catch-up
- no automatic remediation
- no automatic restore
- no launchd activation
- no scheduling policy embedded in the runner
- Mac mini remains the Control Plane
- Ubuntu remains a stateless infrastructure worker

Validation baseline:

- implementation commit:
  d1072aa35fb5034c1097923fd7f6d7643132460b
- targeted tests: 14 passed
- full regression:
  717 passed, 5 deselected, 427 warnings
- Production database and WAL unchanged

Cadence policy and controlled launchd activation are
deferred to PI-010.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Production Governance Scheduler

PI-010 closed on 2026-07-23.

The Mac mini Control Plane runs AIControlCenter governance operations through a managed headless user crontab adapter.

Governance audit snapshots run daily at 03:10 Asia/Seoul. SQLite online backup verification runs Sunday at 04:10 Asia/Seoul.

The snapshot capability performs read-only database validation and creates an immutable JSON evidence artifact. The backup capability uses the SQLite online backup API and validates quick_check, row counts, and the resulting artifact hash.

Automatic retry, catch-up, remediation, and restore remain disabled. Ubuntu remains a stateless infrastructure worker.

<!-- BEGIN AICONTROLCENTER SPF-002 README -->
## Shopping Platform Foundation

Status: Architecture Foundation complete

Shopping is a governed AIControlCenter domain.
WordPress provides headless CMS capabilities.
WooCommerce provides replaceable commerce capabilities.

Sprint 1 remains read-only.
Product, customer, order, price, inventory, and publish writes are disabled.

Architecture documentation:

- `docs/architecture/shopping-platform-foundation.md`
- `docs/architecture/shopping-context-map.md`
- `docs/architecture/shopping-ownership-matrix.md`
- `docs/security/shopping-write-approval-gates.md`
- `docs/contracts/shopping-json-v1.md`

Next gated task: SPF-003 Shopping package and read-only port skeleton.
<!-- END AICONTROLCENTER SPF-002 README -->

<!-- SPF-003:START -->
## Shopping Platform Foundation Status

SPF-003 is closed. The repository contains an import-safe Shopping package foundation, seven asynchronous keyword-only read or compute ports, provisional JSON-first contracts, legacy `CommerceCatalogPort` compatibility, and deny-by-default write governance.

Validation: 6 targeted tests passed; 747 full regression tests passed with 5 deselected.

Next milestone: **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation — SPF-004

SPF-004 Canonical JSON Schema v1 is complete.

Current Shopping foundation capabilities:

- 15 canonical read-contract schemas
- versioned schema registry
- explicit local-only schema loading
- Draft 2020-12 runtime validation
- fail-closed unknown-contract behavior
- strict unknown-field rejection
- schema discriminator validation for snapshots
- targeted schema suite: 6 passed
- full regression suite: 753 passed

Production and Shopping write operations remain disabled.

Next foundation task: **SPF-005 Capability Registry — deny by default**.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-005 CLOSED

SPF-005 establishes deny-by-default capability governance inside AIControlCenter.

- 11 executable READ capabilities
- 9 reserved non-executable WRITE capabilities
- immutable capability registry
- policy evaluation required for registered reads
- unknown and write capabilities denied before policy execution
- policy exceptions fail closed without leaking vendor messages
- 22 targeted tests passed
- 775 full regression tests passed
- Shopping writes remain disabled

Shopping Platform Foundation progress: **5/10** after SPF-005 closure.

Next: **SPF-006 Read Adapter Contracts**.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-006 CLOSED

SPF-006 establishes replaceable read adapter contract boundaries inside AIControlCenter.

- Commerce and CMS ports remain authoritative.
- Adapter contracts are vendor-neutral.
- Canonical Shopping contracts are required at the adapter boundary.
- Commerce and CMS capability bindings remain isolated.
- Vendor DTO escape is prohibited.
- Business logic and policy ownership inside adapters are prohibited.
- Shopping WRITE methods remain prohibited.
- Live vendor connections remain disabled.
- 28 targeted tests passed.
- 803 full regression tests passed.

Shopping Platform Foundation progress after SPF-006: **6/10 — 60%**.

Next: **SPF-007 Adapter Health Monitoring**.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-007 CLOSED

SPF-007 establishes vendor-neutral, read-only adapter health monitoring inside AIControlCenter.

- Health probe normalization is JSON-safe and sanitized.
- Health states are HEALTHY, DEGRADED, and UNAVAILABLE.
- Health aggregation is deterministic and stateless.
- UNAVAILABLE has highest aggregation precedence.
- Empty adapter input fails closed as UNAVAILABLE.
- Probe-layer retry and persistence are disabled.
- Health does not replace capability authorization or policy evaluation.
- Shopping WRITE operations remain disabled.
- Live vendor transport remains disabled.
- 34 targeted tests passed.
- 837 full regression tests passed.

Shopping Platform Foundation progress after SPF-007: **7/10 — 70%**.

Next: **SPF-008 Read-only Snapshots**.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation — SPF-008 CLOSED

SPF-008 establishes read-only snapshot normalization and query orchestration inside AIControlCenter.

- Canonical snapshot payloads are normalized deterministically.
- Snapshot read models are immutable and detached from source mutation.
- Snapshot queries are authorized before repository access.
- Denied or failed authorization produces zero repository calls.
- Snapshot repository failures are sanitized.
- No snapshot creation or persistence is enabled.
- No vendor refresh is performed by snapshot queries.
- Shopping WRITE operations remain disabled.
- Production live registration remains disabled.
- 35 targeted tests passed.
- 872 full regression tests passed.

Shopping Platform Foundation progress after SPF-008: **8/10 — 80%**.

Next: **SPF-009 Validation and Schema Drift**.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Shopping Platform Foundation progress: **9/10 tasks complete (90%)**.
- SPF-009 adds canonical runtime schema validation, deterministic fail-closed validation results, conservative schema drift classification, and authorization-first read-only drift monitoring.
- Validation targeted suite: **58 passed**.
- Full regression: **930 passed, 5 deselected**.
- Implementation commit: `3fa21878e72cdb9608a728a1c676e70fb70b5717`.
- No production, Ubuntu, vendor-write, schema-write, or application-state changes were enabled.
- Next foundation task: **SPF-010 regression, operational validation, documentation and production-readiness closure**.

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
- Current milestone: Shopping Platform Foundation 10/10 CLOSED — Production Readiness Gate Passed.
- Next milestone: post-Foundation read-only external integration and monitoring planning.

<!-- SRI-06B-R1:README -->
## SRI Production Baseline and Codex Workflow

Shopping External Read Integration is the production READ baseline for AIControlCenter.

- Mac mini M4 remains the always-on Control Plane.
- Ubuntu remains a stateless on-demand infrastructure worker.
- WooCommerce is the Commerce Engine.
- WordPress is the CMS Engine.
- AIControlCenter owns policy, orchestration, normalization, evidence and operational decisions.
- Production products and orders remain zero and no business fixture was introduced.

### Runtime READ paths

- WooCommerceReadTransportSession to WooCommerceRESTAdapter to canonical commerce models.
- WordPressRESTAdapter to ContentSnapshot and ContentSnapshotPage.
- ExternalReadObserver executes Health, Schema, Snapshot and Drift.

### Development execution model

AI Home Datacenter Architect retains architecture and production authority.
Codex acts as implementation executor for approved repository tasks.
Architecture changes, production writes and scope expansion require explicit Architect review.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## Deployment Package Lifecycle

DPL is the current program after SRI closure.

`inventory → validate → diff → dry-run plan → readiness → audit`

DPL v1 uses immutable, versioned JSON desired-state packages and observation
reports. DPL-02 is read-only and does not apply, install, restart, bootstrap,
execute rollback, write to production or run generic Ubuntu commands.

The Mac mini M4 remains the single Control Plane, Host Caddy remains the only
public edge, and Ubuntu remains an optional stateless worker. Production
activation is not authorized.

See `docs/deployment/DPL-01-INVENTORY-ASSESSMENT.md`.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04D M2 Operational Readiness

DPL-04A, DPL-04B, DPL-04C, DPL-04D and DPL-04 are CLOSED. The pure injected-
evidence gate accepted the canonical sandbox fixture:
`M2 READINESS_ACCEPTED`. This is not deployment: `M2 ACTIVATION_NOT_STARTED`
and Production activation is `NOT_AUTHORIZED`. M2-P1 is CLOSED and pilot
authorization policy is AVAILABLE. The next milestone is M2-P2 Controlled
Sandbox Pilot Activation and Evidence. Persistent SQLite deployment audit is
required before broader mutable deployment.

## M3-A2C Replay-State Recovery

M3-A1 and M3-A2A through M3-A2C are CLOSED. Explicit-path online SQLite backup,
canonical manifest, restore, exact recovery and post-recovery concurrency were
validated only with pytest temporary databases. The operational replay DB was
not created; no backup schedule, restore or writer was activated; raw nonce
writes remain zero; and Production activation is `NOT_AUTHORIZED`. Next:
M3-A3 Operational Monitoring and Alerts.
# M3-A4B2B1B status

M3-A4B2B1A is CLOSED. M3-A4B2B1B is CLOSED after validation: the human
approval gate is AVAILABLE, synthetic dual-identity approval and in-memory
permit issuance are VALIDATED, and the current recommended review is DENIED.
The requester/operator is `mac-account:kyouhan`; the independent approver is
`UNASSIGNED`, so independent approval and acknowledgement are NOT PROVIDED.
No operational permit was issued or claimed, bootstrap remains unauthorized
and unexecuted, and production activation is `NOT_AUTHORIZED`. Next:
M3-A4B2B1C Independent Approver Action and Live Permit Issuance.
# M3-A4B2B2A authorized Mac bootstrap execution

The authorized Mac bootstrap execution capability is available and validated
in test-only confinement. Atomic permit claim and fail-closed cleanup passed;
controlled operational mode was not executed, no operational targets or
databases were created, writers and monitoring remain inactive, and production
activation is `NOT_AUTHORIZED`. A fresh preflight and fresh permit are required
for M3-A4B2B2B.
# M3-A4B2B2B-R2

The controlled non-production operational activation authorization boundary is
implemented and validated as a default-deny capability. No real permit, claim
or Mac operational bootstrap was performed; production remains unauthorized.
# R5 acknowledgement compatibility

M3-A4B2B2B-R5 preserves full restriction acknowledgements separately from the
exact two-entry executor warning projection. Compatibility is validated before
authorization/issuance and again before claim. The actual bootstrap remains
`NOT EXECUTED`; production is `NOT_AUTHORIZED`.

# M3-A4B3 bootstrap evidence and recovery

The single controlled non-production bootstrap at commit
`f7a81b73b86c170300bb6b80f437dbb753362f7e` is now content- and
digest-validated from read-only snapshots. Audit and replay are `HEALTHY` with
zero events, and both baseline backups passed isolated restores. The permit is
permanently consumed; writers, monitoring, dispatch, Ubuntu, and production
authorization remain false. Next: `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.

# M3-A4C controlled activation closeout

M3 is closed at `0f23abdf362965c09db5f4f35483cbff47853643` with
`READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`. This is not
activation or production authorization. The Mac remains the Control Plane;
writers, monitoring, dispatch, Ubuntu participation, and production remain
false. Future activation requires a separate gate. The 427 warnings remain
backlog.

# M4-A1 controlled activation architecture

M4 begins with pure architecture contracts bound to M3 closeout commit
`89d10da82545e6cfd173085719076bb71e14c120`. Five capabilities default to
inactive and unauthorized and require independent capability-scoped approval,
permit, claim, evidence, validation, and rollback boundaries. The deterministic
planner has no operational side effects. Its
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS` decision is not authorization.
Mac remains the Control Plane, Ubuntu remains stateless, production is
`NOT_AUTHORIZED`, and the 427 warnings remain separate backlog.

# M4-A1R1 SQLite fixture isolation

M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a` is closed with a
formal retained-source versus disposable-working-copy SQLite fixture boundary.
All inspection and recovery validation uses copied database/WAL/SHM sets;
retained bytes, modes, sizes, mtimes, and digests remain unchanged. Actual
operational state was not accessed or changed, `.env` is not required, and
production remains `NOT_AUTHORIZED`. The architecture-only decision remains
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`; next is
`M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.

# M4-A2 capability authorization contracts

M4-A1 and M4-A1R1 are closed. M4-A2 defines immutable, canonical,
single-capability request and independent-approval contracts for all five
registry capabilities. Exact Git, M3, M4-A1, identity, restriction, dependency,
and bounded-time validation produces only a deterministic test grant plan.
`READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION` creates no authorization,
permit, claim, writer, monitoring runtime, dispatch, or activation.

Authorization never implies activation or another capability. Production
remains `NOT_AUTHORIZED`, Ubuntu remains excluded, external-notification
endpoint details and secrets are outside scope, and `.env` is not required.
The existing 427 deprecation warnings remain separate backlog. Next:
`M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION`.

# M4-A3 test-only authorization simulation

M4-A1, M4-A1R1, M4-A2, and M4-A3 are closed. M4-A3 provides deterministic
in-memory simulation for all five independent capabilities. Every artifact is
unmistakably test-only and operationally invalid; live boundaries reject it.
No real authorization, operational permit, claim, writer, monitoring, dispatch,
notification, Ubuntu action, or activation occurred. Production remains
`NOT_AUTHORIZED`, `.env` is not required, and the 427 warnings remain backlog.
Decision: `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`. Next:
`M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION`.
# AUTO-01 autonomous delivery controller architecture

AUTO-01 is closed as architecture and deterministic planning only.
AIControlCenter remains the single Control Plane; Codex is a replaceable,
bounded executor only. Typed autonomy levels, lifecycle gates, JSON-first sprint
manifests, deterministic DAG planning, approval and retry policies, evidence
requirements and an abstract executor port are defined. No runner, subprocess,
launchd service, operational write, authorization, permit, claim, monitoring,
dispatch or activation was created.

M4-A3 remains CLOSED with `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`.
AUTO-01 decides `READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`. AUTO-02 will address
terminal independence, persistent runner and recovery architecture. Human
approval remains mandatory for L4/L5 and post-claim recovery; automatic retry
after a real claim is prohibited. Ubuntu remains stateless-worker-only, `.env`
is not required, production is `NOT_AUTHORIZED`, and the 427 deprecation
warnings remain separate backlog.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Primary Product Roadmap

The active product roadmap is:

1. Shopping Platform
2. AI Integration Platform
3. Personal AI Assistant

Shopping must work without AI. AI enhances Shopping but does not own
Commerce. The Assistant consumes service APIs but does not own service
business logic.

AUTO-01 is closed as an architecture foundation. AUTO-02, AUTO-03 and
M4-A4 through M4-A6 are deferred until product-facing milestones require
them. Production remains `NOT_AUTHORIZED`.
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

## SHOP-02A Product Draft Workflow

SHOP-01E read foundation is closed; SHOP-01E3D persistent activation remains deferred. SHOP-02A defines immutable, revision-bound ProductDraft contracts and human-only approval architecture. WooCommerce remains product truth. Production writes are `NOT_AUTHORIZED`; the observed catalog baseline remains zero products and one category, independent of draft work. Next: `SHOP-02B_PRODUCT_DRAFT_DOMAIN_IMPLEMENTATION`.

## SHOP-02B Product Draft Domain

SHOP-02B implements the immutable ProductDraft 1.0.0 value objects, revision aggregate, closed lifecycle evaluator, deterministic serialization, repository port, and isolated in-memory adapter. The adapter is non-production: no persistent storage, API mutation route, WooCommerce write, or deployment authorization was added. Production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02C_PRODUCT_DRAFT_VALIDATION_APPROVAL_SERVICE`.

## SHOP-02C Product Draft Application Services

SHOP-02C adds deterministic contract validation and authorized, exact-revision human review application services. Authorization is deny-by-default; APPROVE, REJECT, and REVOKE are HUMAN-only. Audit and idempotency adapters are isolated in-memory test infrastructure. ProductDraft contracts remain 1.0.0. No API mutation route, persistent storage, or WooCommerce write was added, and production writes remain `NOT_AUTHORIZED`. Next: `SHOP-02D_PRODUCT_DRAFT_READ_API_DASHBOARD`.
# SHOP-02D ProductDraft reads

AIControlCenter exposes GET-only ProductDraft reads at `/shopping/product-drafts`, `/shopping/product-drafts/{draft_id}`, and `/shopping/product-drafts/{draft_id}/revisions/{revision_id}`. The Dashboard key is `product_draft_review`. Its replaceable source is unavailable by default; an explicitly configured empty source is valid and distinct from `UNAVAILABLE`. Contracts remain 1.0.0. No mutation routes, WooCommerce writes, or persistent ProductDraft storage were added. Production writes remain `NOT_AUTHORIZED`; SHOP-03 controlled WooCommerce write architecture is next.
# SHOP-03B1 controlled live-write boundary

SHOP-03B is user-attested as authorized at `2026-08-03T08:54:00+09:00` for architecture, implementation, and intercepted validation. SHOP-03B1 adds a synchronous, injected WooCommerce write boundary under ProductDraft deployment. Credentials are obtained only at call time and passed separately from immutable request metadata; the default credential provider and transport fail closed. There is no concrete network transport, no mutation route, and every result remains `INTERCEPTED_VALIDATION` with `live_write_performed: false`.

No exact product, ProductDraft revision, deployment intent, or execution timestamp is authorized. External requests: 0. Live writes: 0. Production activation: `NOT_AUTHORIZED`. ProductDraft and deployment-intent contracts remain version 1.0.0. SHOP-03B2 is the next one-product controlled pilot.
## UI-01 internal Shopping Homepage

The internal read-only Shopping operations Homepage is available at `GET
/homepage`. It consumes only same-origin `GET /dashboard`, including the exact
`shopping_management` and `product_draft_review` projections. It adds no
frontend framework, public Caddy exposure, authentication change, mutation API,
or live Commerce write. See `docs/homepage/UI-01-shopping-dashboard.md`.

## UI-02 internal Product Management Console

The read-only console is available at `GET /homepage/product-management`. It
uses only the three existing same-origin ProductDraft GET resources, keeps
empty and unavailable states distinct, and exposes no mutation or live Commerce
control. It is not publicly exposed and production activation remains
`NOT_AUTHORIZED`. See `docs/homepage/UI-02-product-management-console.md`.
Next: `OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## PI-009A1 Deployment Test Gate

PI-009A1 is complete.

The deployment regression harness and dependency-boundary policy were repaired
and the complete deployment suite passed with 1133 tests.

Production remains unauthorized.

The remaining technical Production blocker is `RUNTIME_SOURCE_ISOLATION`:
the service must execute immutable release source instead of importing
application code from the mutable repository working tree.

## PI-009A2 Runtime Source Isolation

The PI-009A2 architecture is frozen.

AIControlCenter production Runtime identity will consist of a paired immutable
venv and Git source snapshot. The existing current pointer remains unchanged.

Repository implementation is allowed first. Runtime source creation and wrapper
cutover require separate explicit human authorizations.

Production remains unauthorized.

### PI-009A2 Application State Isolation

Immutable-source validation exposed two repository-relative SQLite state paths.

Memory and scheduler state now use the canonical
`AICONTROLCENTER_DATA_ROOT` contract.

Production source remains read-only while writable state lives under the
AIControlCenter application data root.

The former Candidate `acd80ab9f6ae` cannot be promoted as the final
immutable-source release. A new Candidate is required.

### PI-009A2 A2.1 Complete

Immutable Runtime source artifact tooling and the immutable-source wrapper
template are implemented.

The source artifact is read-only and application state remains external through
`AICONTROLCENTER_DATA_ROOT`.

The canonical Runtime bootstrap is HEAD-only. Therefore the A2.1 completion
commit is the source identity for the next Runtime Candidate.

No operational source artifact or service cutover has occurred.

Production remains unauthorized.

### PI-009A2 A2.2A Runtime Candidate Validated

Runtime Candidate `7b171f135dc7` was built exactly once through the canonical
Runtime bootstrap from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The canonical build, dependency validation, full test suite and temporary
immutable-source/external-state execution all passed.

The active Runtime, live wrapper and service remained unchanged.

Production remains unauthorized.

### PI-009A2 A2.2B Immutable Source Validated

Runtime Candidate `7b171f135dc7` now has a matching operational immutable
source artifact built from source commit `7b171f135dc7882546bf7f733208778f1aef4943`.

The artifact is read-only, has no Git metadata, matches the Runtime identity,
and successfully loads the shadow application with writable state externalized.

The active Runtime and live wrapper remain unchanged.

Production remains unauthorized.

### PI-009A2 A2.3 Live Cutover

Runtime `7b171f135dc7` is now serving from its paired immutable source artifact.
Persistent application state is externalized under the macOS AIControlCenter
application data root. Repository source and repository-local DB state are no
longer part of the live execution boundary.

Production authorization remains separate.

### PI-009 Production Authorization

Runtime `7b171f135dc7` with source commit `7b171f135dc7882546bf7f733208778f1aef4943` is authorized for
Production under PI-009.

The authorization followed a clean final technical gate, immutable Runtime/source
validation, external persistent-state validation, HTTP validation and a
deployment regression result of 2337 passed with 5 deselected.

Production authorization is recorded as governance evidence; no operational
restart or reactivation was required.

### AI-PROVIDER-01C-B Candidate Validated

Candidate Runtime/source `102b8f1fa862`, bound to commit
`102b8f1fa8628d00d25575cb94538826a1a04e10`, passed canonical build,
immutable-source, and network-free FakeProvider workflow validation.
Production remains on `7b171f135dc7`; promotion requires separate explicit
AI-PROVIDER-01C-C authorization. Notion is `DEFERRED_UNTIL_FINAL_PHASE`.

### Production AI Provider Workflow

Production Runtime `102b8f1fa862` now executes the canonical AI provider path:

`BrainAgent -> ProviderRouter -> ProviderAdapter -> OpenAIAdapter`

The immutable Production artifact has passed a corrected authenticated workflow
validation. Persistent daemon credential wiring remains deferred to SEC-01.
# SEC-01B provider credential delivery

The repository now defines deterministic, redacted provider credential validation and wrapper injection. See [Provider Secret Delivery](docs/architecture/PROVIDER-SECRET-DELIVERY.md). This is repository-only; live installation is deferred to explicitly authorized SEC-01C.

# SEC-01C-R1 repository repair

The canonical wrapper restores immutable Runtime/source execution while retaining deterministic secret injection. SEC-01C consumed two installs and one restart; its frozen wrapper served mutable repository source, so HTTP recovery did not pass the immutable gate. No rollback occurred. R1 performs no live install or restart. Runtime `102b8f1fa862` has importable `jsonschema`, but the live installation remains blocked pending new exact human authorization for wrapper replacement and one restart. Notion is `DEFERRED_UNTIL_FINAL_PHASE`.

## SEC-01C Production daemon secret delivery

SEC-01C is `COMPLETE` at milestone
`PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`. R1 converged immutable execution;
R2/R3 removed the remaining mutable repository config dependency; R3Q stopped
before mutation after detecting drift; and separately authorized R3Q2 made one
logical-value-preserving quoting correction and exactly one restart. The running
daemon uses matching immutable source/config, passes HTTP `200/200/405`, and has
validated `OPENAI_API_KEY` presence without value exposure or provider calls.
SEC-01 is not complete. Next: SEC-01D Secret Lifecycle & Recovery Validation.
See [the evidence-backed closeout](docs/operations/SEC-01C-PRODUCTION-SECRET-DELIVERY-CLOSEOUT.md).

## Current Production security status — SEC-01 complete

SEC-01 / the provider-secret lifecycle is complete at
`PRODUCTION_SECRET_LIFECYCLE_VALIDATED`. Production Runtime `102b8f1fa862` is
bound to matching immutable source. Persistent daemon delivery, restart and
reboot recovery, missing-secret fail-closed behavior, storage rotation, daemon
delivery rotation, provider administration lifecycle, and candidate cleanup
were validated. Previous credential revocation/deletion is operator-attested;
provider admin revocation is not machine verified, authenticated provider
validation was not performed, and credential identity was not proven locally.
No secret value or credential identifier belongs in documentation. The service
was healthy after E5 and the candidate `.next` file was removed.

The authoritative final regression gate is SEC-01 FINAL R4: the canonical
`ops/macos/validation/run-deployment-regression-gate.sh` harness produced 2402
passed, 5 deselected, and 437 warnings, with no repository modification by
tests, no Production mutation, unchanged Production PID, preserved canonical
secret metadata, and no candidate. FINAL R1 remains in the audit trail: raw
pytest produced 2 failed, 2338 passed, 5 deselected, and 62 errors because it
bypassed the harness-provisioned isolated test roots. It is classified
`INVALID_RAW_PYTEST_GATE_INVOCATION`, not an application or documentation
failure. FINAL R2 was read-only diagnosis; FINAL R3 passed 3/3 representative
selections (17 tests) through the canonical harness. Warnings are not failures.

The Mac mini M4 remains the always-on Brain and AIControlCenter the single
Control Plane. Ubuntu remains a stateless JSON-API infrastructure Worker with no
AI workloads, business logic, application state, governance, authorization, or
provider-secret policy. Secrets use Protected File-Per-Provider Secrets with
Deterministic Wrapper Injection; business logic never reads secret files.
Production mutation remains explicitly human-authorized, with no automatic
rollback after controlled mutation failure. Next:
`SEC-02_CONTROL_PLANE_GOVERNANCE_AUTOMATION`. SEC-01 completion does not mean
the AI Home Datacenter project is complete.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## Application Scheduler deployment readiness

The existing runtime `ServiceHealth` projection observes Scheduler runtime
health and readiness through an injected macOS log inspector; it is not a
deployment lifecycle executor. The canonical Scheduler bootstrap lifecycle
gate is `application_scheduler_bootstrap.py`. Dry-run and apply both consume
the same read-only log contract and probe registration eligibility; apply alone
may perform exactly one bootstrap after all gates pass.

The immutable Production API runner uses
`ops.macos.runtime.application:app`, whose outer macOS composition injects the
log inspector into `core.api.app.create_app(...)`. Core has no `ops.*` import
and remains fail-closed without an injected adapter.

The contract can also be checked directly:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  ops/macos/launchd/application_scheduler_logs.py validate
```

It requires `/var/log/aicontrolcenter` to remain `root:wheel 0755` and both
Application Scheduler logs to be regular, non-symlink `kyouhan:staff 0640`
files. Missing files require a separate, bounded
`application_scheduler_logs.py provision` invocation. The Python root check is
only a local executor precondition—not human authorization. The outer governed
executor owns and must consume authorization immediately before
one bounded Production invocation. Provisioning never invokes launchctl and
never retries, rolls back, or repairs an invalid existing file. Bootstrap does
not provision, kickstart, retry, or roll back.

Application Scheduler Production recovery was already operational before the
recurrence-prevention closeout. Focused recurrence validation passed. Canonical
deployment regression invocation #1 failed with 13 test failures caused by
umask-sensitive Scheduler fixtures and a controlled-live test that hashed the
independently mutable real-home AIControlCenter tree. Only those test defects
were corrected; Product contracts were not weakened. The corrected focused
scope passed 39 tests under umask `077`, with the controlled live root
explicitly confined to `/private/tmp`. Canonical deployment regression
invocation #2 passed with `RC=0`. Exactly two canonical invocations were made
because code/test changes occurred after invocation #1; no test count is
claimed for invocation #2.

No Production mutation occurred during recurrence-prevention validation, and
no additional activation, bootstrap, log provisioning, kickstart, retry, or
rollback was performed. Final milestone:

`OPS-01B_RECURRENCE_PREVENTION_VALIDATED_AND_CLOSED`

WordPress and Shadow work remain separate future work.

## Production Runtime Health

Current Production release:

`ed2424e39bb1`
(`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`)

The canonical AIControlCenter API runs on the Mac Control Plane at
`127.0.0.1:58081` and is published through Caddy.

`GET /runtime/health` currently reports a truthful degraded state:

- API: required and `RUNNING`.
- Telegram: optional and `NOT_DEPLOYED`.
- Application Scheduler: required and `NOT_DEPLOYED`.
- Scheduler heartbeat: `STALE`.
- Service topology: `VALID`.
- Aggregate `healthy`: `false`.

The aggregate becomes healthy only after the dedicated Mac Application
Scheduler is deployed and produces a fresh heartbeat.

The Ubuntu Server remains an on-demand infrastructure Worker. Runtime Health,
application scheduling, orchestration and business logic remain on the Mac
Control Plane.

The existing Shadow service on `127.0.0.1:18100` is not part of public ingress.
Shadow release alignment is a separate maintenance concern and is not required
for the current Production release.

## PA-05 — WooCommerce Headless Adapter v1

PA-05 is validated. Milestone:
`WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`.

AIControlCenter remains the sole Control Plane and owns shopping business
logic. `core.shopping` remains authoritative for ProductDraft lifecycle,
product policy, workflow, recommendation, customer automation, governance,
and business logic. WordPress remains CMS-only; WooCommerce remains
commerce-engine-only. `integrations.woocommerce` is replaceable and read-only,
and `ops.macos.runtime.application` is the outer composition root. Core imports
neither `ops.*` nor `integrations.*`.

PA-05 exposes only `GET /shopping/providers/woocommerce`. It adds no
POST/PUT/PATCH/DELETE endpoint and no create/update/delete product, order,
inventory, customer, coupon, execute, retry, or Production mutation action.
The canonical Production manifest contains no WooCommerce identity, but
absence is not treated as `NOT_DEPLOYED`. Deployment, configuration, and
authentication remain `UNKNOWN`; catalog/API availability is unproven; the
default is fail-closed `UNAVAILABLE`. Invalid or ambiguous lookups invent no
manifest evidence, and validated evidence requires exactly one successfully
returned WooCommerce identity.

Governance remains owned by `core.capabilities`; typed boolean-only extensions
cannot override `authority=AICONTROLCENTER`, `read_only=true`,
`production_authorization=false`, `infrastructure_mutation=false`,
`platform_business_policy_ownership=false`, or `action_execution=false`.
WooCommerce adds `commerce_engine_only=true` and `automatic_retry=false`.
Provider fallbacks use `UnavailableCapabilityObserver`; platform-neutral
`create_app` performs no WooCommerce, n8n, or OpenClaw external discovery, so
PA-02 and PA-03 outward fail-closed behavior remains compatible.

Final focused validation passed 91 tests after the final architecture
correction. Canonical deployment regression passed `RC=0` in exactly one
PA-05 execution. Import checks recorded `CORE_OPS_IMPORT_COUNT=0` and
`CORE_INTEGRATIONS_IMPORT_COUNT=0`. No Production WooCommerce request or
external commerce I/O occurred, and no WordPress, WooCommerce, Shopping
SQLite, Docker, launchd, `runtime/current`, Caddy, Ubuntu, credential,
database, plugin, or theme mutation occurred.

Next production sprint: `SHOP-CMS-01 — WordPress + WooCommerce Runtime
Foundation`. It will establish the actual runtime, persistent-state, secret,
backup, health/readiness, manifest, and activation architecture before public
storefront exposure. The Production runtime and public storefront are not yet
claimed available. No Notion synchronization is claimed.

## SHOP-CMS-01A — WordPress + WooCommerce Runtime Foundation

Phase A is validated and closed at milestone
`SHOPPING_RUNTIME_FOUNDATION_VALIDATED`. The canonical lifecycle is one
Mac-owned, Ubuntu-independent `shopping-runtime`, currently `NOT_DEPLOYED`,
using Docker Compose on the dedicated `aicontrolcenter-commerce` Colima
profile. WordPress and MariaDB are stack components, not independent lifecycle
services. WooCommerce is a WordPress-hosted capability, not a daemon, and is
`NOT_DEPLOYED` with activation unauthorized.

The profile was observed stopped and the active default Docker daemon was
unavailable, so no runtime/container, WordPress, MariaDB, WooCommerce,
storefront, or storefront-routing availability is claimed. Active Caddy and
canonical FastAPI public behavior remained unchanged. No Production/runtime
mutation or Notion synchronization occurred.

Validation: 72 initial focused passes; canonical #1 `3151 passed, 2 failed, 5
deselected` due only to stale 8-to-9 service-count expectations; corrected
targeted 2 passed; focused compatibility 47 passed; canonical #2 `RC=0`.
Exactly two canonical invocations were used. Next:
`SHOP-CMS-01B — bounded Production runtime activation`, milestone
`SHOPPING_RUNTIME_ACTIVATED`; future storefront milestone
`SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## SHOP-CMS-01B — Runtime Foundation activation phase

The corrected desired contract publishes WordPress only on
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`, with
`SHOPPING_WORDPRESS_PORT=58082`; MariaDB has no host port. Reserved Control
Plane ports come from the canonical service manifest, and even a healthy
WordPress container fails runtime readiness with `error_type=PortCollision`
when it publishes on one. Compose JSON inspection accepts bounded array,
single-object, NDJSON, and empty-output shapes, rejects malformed/scalar/
non-object content, and distinguishes valid empty observation from malformed
inspection. WooCommerce readiness is never inferred from container health.

The dedicated Colima start authorization was consumed exactly once and
succeeded. Read-only reconciliation then observed existing stored WordPress
and MariaDB containers running/healthy under restart policy and persistent
volumes; it did not authorize or perform Compose up. The live WordPress
publisher remained on reserved FastAPI port `58081`, so it was correctly
classified `PortCollision`; the earlier FastAPI-style REST 404 came from the
canonical FastAPI listener, not WordPress. No port cutover to `58082` occurred.
Required bootstrap secret files were absent, and WooCommerce namespace/API/
catalog readiness remains unproven.

The service manifest and WooCommerce capability remain `NOT_DEPLOYED`.
`SHOPPING_RUNTIME_FOUNDATION_VALIDATED` remains achieved, while
`SHOPPING_RUNTIME_ACTIVATED=false`. Next is a separately human-authorized
WordPress port cutover to `58082` followed by read-only reconciliation;
WooCommerce bootstrap/readiness and `SHOP-STOREFRONT-01` follow activation.
No additional Production authorization, automatic retry/rollback, Compose,
WordPress, WooCommerce, database, Caddy, Ubuntu, or port-cutover mutation was
performed, and no Notion synchronization is claimed.
## CURRENT AUTHORITATIVE — Macro-WU07 Closeout

- `MACRO_WU_06=CLOSED`; WU06 was not reopened (`WU06_REOPEN_REQUIRED=false`).
- `MACRO_WU_07=CLOSED`
- `MACRO_WU_07_DISCOVERY_GATE=PASS`
- `EXISTING_DECISION_PRIMITIVE_FOUND=true`
- `NEW_CODE_REQUIRED=false`
- `ARCHITECTURE_FREEZE_REQUIRED=false`
- `RECOVER_DECISION_INPUT=EVIDENCE_INCOMPLETE`
- `RECOVER_EVIDENCE_SUFFICIENT=false`
- `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`
- `REMAINING_AUTHORITATIVE_MACRO_WUS=5`
- `AUTHORITATIVE_REMAINING_RANGE=WU08-WU12`
- `NEXT_STEP=MACRO_WU_08_CONCRETE_VALIDATOR_PREPARATION`
- `PRODUCTION_ACCESS_REQUIRED=false`; no Production access occurred during WU07.
- `FILESYSTEM_ACCESS_REQUIRED=false`; no filesystem access occurred during WU07.
- `MARIADB_ACTIVITY=NONE`
- `SQL_EXECUTION=NOT_PERFORMED`
- `PYMYSQL_ACTIVITY=NONE`
- `SECRET_VALUES_READ=NO`
- `MAC_CONTROL_PLANE=true`; Mac AIControlCenter remains the sole Control Plane.
- `UBUNTU_AUTHORITY=false`; Ubuntu retains zero Control Plane authority.
- `GOVERNANCE_CORE_CHANGED=false`
- `SEC_02_CHANGED=false`
- `CONTROLLED_EXECUTION_PORT_COUPLED=false`
- `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`
- `CANONICAL=NOT_RUN`
- `BLOCKER=NONE`

## Prior authoritative record — Macro-WU08 Closeout

- `MACRO_WU_06=CLOSED`; WU06 was not reopened.
- `MACRO_WU_07=CLOSED`; WU07 was not reopened.
- `MACRO_WU_08=CLOSED`
- `WU08_IMPLEMENTATION_GATE=PASS`
- `WU08_CORRECTION_GATE=PASS`
- `TEST_GIT_STATE_COUPLING_GATE=PASS`
- `SQL_SINGLE_STATEMENT_GATE=PASS`
- `FOCUSED_TEST_GATE=PASS`; `FOCUSED_RESULT=32 passed`.
- `FINAL_CODE_REVIEW_GATE=PASS`
- `CANONICAL_REGRESSION_GATE=PASS`; `CANONICAL_RESULT=4076 passed, 5 deselected, 555 warnings`.
- `IMPLEMENTATION_COMMIT=303e4ea`
- `WU08_IMPLEMENTATION_GIT_CLOSEOUT=COMPLETE`
- `CONCRETE_MARIADB_CONTINUITY_VALIDATOR_REPOSITORY_IMPLEMENTED=true`
- `CONCRETE_MARIADB_CONTINUITY_VALIDATOR_REPOSITORY_VALIDATED=true`
- `PRODUCTION_VALIDATION_AVAILABLE=false`
- `PRODUCTION_ACCESS_PERFORMED=false`
- `PROTECTED_SOURCE_ACCESS_PERFORMED=false`
- `CREDENTIAL_VALIDATION_PERFORMED=false`
- `MARIADB_CONNECTION_PERFORMED=false`
- `SQL_EXECUTION_PERFORMED=false`
- `PRODUCTION_AUTHORIZATION_CONSUMED=false`
- `RECOVER_DECISION_INPUT=EVIDENCE_INCOMPLETE`
- `RECOVER_EVIDENCE_SUFFICIENT=false`
- `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`
- `GOVERNANCE_CORE_CHANGED=false`
- `SEC_02_CHANGED=false`
- `CONTROLLED_EXECUTION_PORT_COUPLED=false`
- `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`
- `MAC_CONTROL_PLANE=true`; Mac AIControlCenter remains the sole Control Plane.
- `UBUNTU_AUTHORITY=false`; Ubuntu remains a stateless infrastructure worker with zero Control Plane authority.
- `REMAINING_AUTHORITATIVE_MACRO_WUS=4`
- `AUTHORITATIVE_REMAINING_RANGE=WU09-WU12`
- `NEXT_STEP=MACRO_WU_09_MARIADB_LOOPBACK_PORT_DEPLOYMENT`

WU08 does not authorize WU09, WU10, or WU11 and creates no reusable Production authority.

## SEC02-FS-01 — Pre-bootstrap filesystem authority freeze

The create-only Mac Control Plane authority for the fixed SEC-02 `governance`
and `trust` directories is now defined, not implemented or operationally
validated. It requires one fresh, dedicated macOS Authorization Services
approval for one bounded attempt, derives home/UID/GID only from the bound
Darwin passwd record, and exposes no arbitrary path, chmod, chown, command,
registry, database, retry, repair, or later-stage authority. See
`docs/architecture/SEC-02-PRE-BOOTSTRAP-FILESYSTEM-AUTHORITY-FREEZE.md`.

The current governance directory was operationally observed at mode `0755`.
Under the exact-`0700` contract it is `UNSAFE_EXISTING`; create-only v1 cannot
remediate it, so the current operational gate is blocked. SEC02-FS-02 will only
plan and classify read-only. If it confirms that state, a separate later
remediation authority review and implementation is required; this freeze does
not define one.
## SEC-02 FS-02 repository closure

The repository implements the pure pre-bootstrap filesystem plan, closed
read-only classifier, and an uninvoked Darwin observation adapter. It also
defines repository-only narrow remediation planning for the exact governance
directory `0755` to `0700` case. No live remediation adapter or operational
authority exists; Production bootstrap and the trusted issuer remain unavailable.

## SEC02-FS-MACRO-03A authorization contract

The repository now implements the immutable, pure authorization contract for
one future exact governance-directory `0755` to `0700` attempt. It accepts only
one fresh interactive approval for one purpose-specific macOS right and makes
success, failure, and uncertainty consuming terminal outcomes. Authorization
artifacts contain no caller-selected execution, path, mode, UID, or GID data.
No Authorization Services call, chmod adapter, Production access, filesystem
mutation, bootstrap authority, or feature authority was added. Operational/API
validation and any bounded live adapter remain separate SEC02-FS-MACRO-03B work.
## SEC-02 bounded remediation adapter foundation

SEC02-FS-MACRO-03B1 adds repository-only fixed Authorization Services and
privileged-helper ports, intercepted adapters, and fail-closed one-attempt
orchestration. It performs no prompt, helper installation, or filesystem
mutation. Fresh interaction is not inferred from `InteractionAllowed`, and
Production remediation remains unavailable.
# SEC-02 packaging readiness update

A deterministic, non-Production SEC-02 native package contract and remaining ceremony DAG are documented in `docs/architecture/SEC-02-LIVE-SECURITY-PACKAGING.md`. Nothing is signed, registered, provisioned, installed, or operational.


## OPS-VAL-01B Canonical Regression Evidence

The canonical macOS deployment regression command remains:

`ops/macos/validation/run-deployment-regression-gate.sh -q`

The runner now writes invocation-bound evidence using schema `ops-val-01b/canonical-evidence/v2`. Evidence includes the canonical command, invocation ID, capture status, pytest exit status, exact final pytest summary, completion state, and validated-pass result.

A missing or incomplete pytest summary or failed evidence capture cannot be reported as a validated PASS.

Linked Git worktrees are supported by the repository observation adapter without using Git mutation subprocesses. Shared Git refs are read from common metadata, while worktree-local refs remain isolated to private worktree metadata.

OPS-VAL-01B validation completed at implementation commit `0b15dbc` with invocation `5bbec183020441a39c275f18d248f946`:

`4490 passed, 5 deselected, 699 warnings, 2 subtests passed in 412.64s (0:06:52)`

Warnings remain non-blocking and are tracked separately from OPS-VAL-01B.
## Current authoritative — SEC02-FS-MACRO-03B4R2-C6B readiness foundation

C6B defines a deterministic JSON, Mac-only, repository-only readiness contract
for future external Production signing credential acquisition. Only a represented
Apple Developer ID Application candidate with a represented matching private key
may be marked acceptable for eventual C5A/C5B ceremony progression. Apple
Development, ad-hoc, self-signed, Developer ID Installer, unsupported, invented
Team ID, and Xcode-derived authority claims fail closed.

C6B acquires, downloads, reads, imports, signs, notarizes, registers, or mutates
nothing and handles no passphrase. It grants neither Production nor Ubuntu
authority. `authoritative_team_id` remains `null`; only C4 may establish it from
a live verified identity after a separate future import.

Validation: focused C6B `4 passed`; C4/C5A/C5B/C6A compatibility `20 passed`;
canonical `4503 passed, 5 deselected, 719 warnings, 2 subtests passed`.
## Current authoritative — Shopping Runtime preproduction Bundle B

Repository preparation for the existing WU09 preload, WU09 loopback deployment,
WU10 credential-slot provisioning, and WU11 one-shot read-only continuity
boundaries is complete. The preload composition is an opaque process-local
identity whose module-private immutable coordinator/lifecycle state is consumed
before execution; its destructive one-use ceremony entry remains uncalled. The other boundaries have exact,
value-free readiness contracts reusing existing implementation and governance.
Continuity remains `UNRESOLVED`. Production access/mutation, authorization
consumption, Docker/Colima access, secret reads, MariaDB connection/SQL, Ubuntu
mutation, Notion sync, and Shopping Runtime activation were all `false`/`none`.
This is not operational Production ceremony readiness: trusted SEC-02
issuer/trust roots are unavailable; there is no fresh Production authorization
or observation, durable consumption, `ALLOW_SINGLE_INVOCATION`, or Production
invocation.
Each future Production boundary requires separate human authorization. Next:
the existing `WU09_PINNED_IMAGE_PRELOADED` Production mutation.

Implementation commit: `cfde5874392b75206cd66b7e7ee3202517de5e54`.
Validation: focused `52 passed in 0.13s`; final durable canonical invocation
`9b77e3f128b64c3a88f229a9a8898f93` completed and validated PASS with `4533
passed, 5 deselected, 447 warnings, 2 subtests passed in 468.64s (0:07:48)` from
`/private/tmp/aicontrolcenter-canonical-evidence.iaI3ci`.
## SHOP-SERVICE-START-01B WordPress port reconciliation executor

The repository implements the governed, WordPress-only candidate that can
change `127.0.0.1:58081` to desired `127.0.0.1:58082` only after exact
read-only preconditions and fresh one-use human authorization. It uses the
fixed trusted `runtime_cutover` source, performs at most one no-dependencies,
no-pull forced recreation, and requires fresh read-only reconciliation after
any attempt. It does not prove content preservation or backup/restore and does
not activate Shopping or WooCommerce.

Execution invariant:
`AUTHORIZATION_CONSUMPTION -> FRESH_EXPECTED_BEFORE_OBSERVATION -> EXACT_REVALIDATION -> AT_MOST_ONE_MUTATION`.
Pure classification never selects mutation. Failed fresh validation consumes
authorization but selects and executes no mutation, with no restore or retry.

`AUTHORITATIVE_WORK_ITEM=SHOP-SERVICE-START-01B`
`COLIMA_HOST_STATE=RUNNING`
`DOCKER_REACHABLE=YES`
`MARIADB_STATE=HEALTHY`
`MARIADB_HOST_PORT_PUBLISHED=NO`
`WORDPRESS_STATE=CONFLICTING`
`WORDPRESS_ACTUAL_BINDING=127.0.0.1:58081`
`WORDPRESS_DESIRED_BINDING=127.0.0.1:58082`
`DATABASE_VOLUME_PRESENT=YES`
`WORDPRESS_VOLUME_PRESENT=YES`
`SINGLE_SNAPSHOT_PROVES_CONTINUITY=NO`
`CONTENT_PRESERVATION_PROVEN=NO`
`BACKUP_RESTORE_PROVEN=NO`
`WORDPRESS_PORT_RECONCILIATION_EXECUTOR_IMPLEMENTED=YES`
`LIVE_MUTATION_EXECUTED=NO`
`AUTHORIZATION_CONSUMED=NO`
`SHOPPING_RUNTIME_ACTIVATED=NO`
`NOTION_SYNC=NO`

## WordPress runtime-cutover port source guard

`SHOP-SERVICE-START-01B` now validates the trusted runtime-cutover source's
non-secret `SHOPPING_WORDPRESS_PORT` bytes against exact `58082`. The observer
publishes boolean/reason evidence rather than an assignment record, and the
initial and post-authorization reconciliation classifications both require the
guard. No live source observation or cutover is claimed.

Secret assignment records retain the pre-existing strict UTF-8 validation
contract. Secret values may be transiently decoded for syntax validation but
are not retained, serialized, emitted, logged, hashed, or semantically compared.

`AUTHORITATIVE_WORK_ITEM=SHOP-SERVICE-START-01B`
`WORDPRESS_PORT_EXPECTED=58082`
`WORDPRESS_PORT_SOURCE_VALUE_GUARD_IMPLEMENTED=YES`
`SECRET_VALUES_RETAINED=NO`
`SECRET_VALUES_EMITTED=NO`
`LIVE_MUTATION_EXECUTED=NO`
`AUTHORIZATION_CONSUMED=NO`
`SHOPPING_RUNTIME_ACTIVATED=NO`
`NOTION_SYNC=NO`
