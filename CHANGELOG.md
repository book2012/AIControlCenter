# CHANGELOG

## 2026-08-31 — SEC-02 fresh-human evidence foundation

- Added immutable RFC 8785-canonical challenge/evidence models, typed exact
  verification, and intercepted orchestration before the existing durable claim.
- Selected future Secure Enclave P-256 `userPresence` signing without creating a
  key or reusable `LAContext`; native contracts type-check but are not operational.
- Hardened peer signing so arbitrary strings cannot create READY identities.
- Validation: focused `29 passed, 192 warnings`; related SEC-02 `234 passed, 184
  warnings`; canonical exactly once `4432 passed, 5 deselected, 635 warnings`.

## 2026-08-30 — SEC02-FS-MACRO-03B4R2-A repository foundation

- Added unresolved-identity app/helper/LaunchDaemon templates and fixed bundle
  layout metadata under the established `com.aicontrolcenter` namespace.
- Hardened bidirectional signing readiness against missing, wildcard,
  permissive, and role-collapsed requirements.
- Added and type-checked native domain-separated SHA-256 replay derivation.
- Implemented the exact-path, create-only, remediation-separated journal
  provisioning repository contract without privileged execution.
- Validation: focused `25 passed, 180 warnings`; related SEC-02 `218 passed,
  180 warnings`; canonical `4413 passed, 5 deselected, 635 warnings` once.

## 2026-08-30 — SEC02-FS-MACRO-03B4R readiness review closed

- Recorded exact read-only toolchain, SDK, signing, package, XPC, replay,
  fresh-approval, and journal-provisioning evidence.
- Defined the separate create-only Production journal provisioning authority
  without implementing or invoking it.
- Kept Production remediation and every missing live prerequisite unavailable.

## 2026-08-30 — SEC02-FS-MACRO-03B3 durable journal foundation

- Added a distinct temp-path-only SQLite attempt journal with schema version 1,
  fixed purpose/version, unique replay fingerprint, strict closed states, and
  full-synchronous rollback-journal commits.
- Integrated durable claim-before-helper orchestration with consuming success,
  failure, uncertainty, stranded-claim replay denial, and no retry/steal/reset.
- Kept raw authorization capability and ordinary SEC-02 consumption out of the
  journal; froze but did not create the future Production path.
- Validation: focused `52 passed`; related SEC-02 `302 passed`; canonical
  `4408 passed, 5 deselected, 627 warnings` in exactly one run.

`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_REPOSITORY_IMPLEMENTED=YES`
`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_OPERATIONAL=NO`
`REPLAY_FINGERPRINT_OPERATIONALLY_VALIDATED=NO`
`JOURNAL_PROVISIONING_AUTHORITY_READY=NO`
`PRODUCTION_REMEDIATION_AVAILABLE=NO`

## 2026-08-30 — SEC02-FS-MACRO-03B2 privileged-helper foundation

- Moved exact remediation validation and eligibility ahead of authorization;
  all malformed, ineligible, forged, trust-target, and bool/int-confused plans
  now produce zero authorization and helper calls.
- Added immutable fail-closed helper/peer/package contracts and a syntax-checked
  Swift macOS 13+ foundation for the single fixed XPC operation and SDK-native
  bidirectional code-signing requirements.
- Recorded signing identity as absent and package readiness as `NOT_READY`.
  External-form persistence, live authorization, registration, XPC execution,
  helper launch, and filesystem mutation remain absent.
- Validation: focused `71 passed`; related SEC-02 `189 passed, 176 warnings`;
  canonical `4384 passed, 5 deselected, 619 warnings` in one run.

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

## 2026-08-30 — SEC02-FS-MACRO-03A authorization contract implemented

- Froze and repository-implemented the dedicated, purpose-specific macOS
  authorization contract for only the passwd-home governance directory and
  only mode `0755` to `0700`.
- Enforced one fresh interactive approval, one claim, one attempt, no retry or
  reuse, and consuming `SUCCESS`, `FAILURE`, and `UNCERTAIN` outcomes.
- Kept authorization artifacts free of executable, command, environment, path,
  mode, UID, GID, bootstrap, release, issuer, feature, and generic execution
  authority; independently reject forged target/mode/identity plans.
- Added immutable models and pure policy tests only. No Authorization Services
  invocation, live chmod adapter, Production access, or filesystem mutation
  occurred. Operational/API validation remains SEC02-FS-MACRO-03B work.

`CONCRETE_REMEDIATION_AUTHORIZATION_CONTRACT_DEFINED=YES`

`CONCRETE_REMEDIATION_AUTHORIZATION_CONTRACT_IMPLEMENTED=YES`

`AUTHORIZATION_SERVICES_INVOKED=NO`

`LIVE_CHMOD_ADAPTER_IMPLEMENTED=NO`

## 2026-08-30 — SEC02-AR-01 anti-rollback receipt architecture closed

- Froze the canonical receipt schema and identity, exact Secure Enclave
  ECDSA-P256/SHA-256 primitive, non-exportable key custody, fixed root-owned
  local storage, atomic/full-sync journal, and read-only reconciliation model.
- Required existing Continuity Witness immutable history to be durable before
  local receipt commit; preserved the Witness as evidence-only and the Mac mini
  M4 as sole Control Plane.
- Preserved fail-closed first-install/reset, monotonic versions, no same-version
  artifact substitution, no automatic retry/rollback, and no receipt-granted
  authority. No implementation, keys, AWS, Production, Docker/Colima, or
  runtime access occurred.

`SEC02_AR_01_GATE=PASS`

`ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES`

`ANTI_ROLLBACK_RECEIPT_IMPLEMENTED=NO`

`ANTI_ROLLBACK_RECEIPT_OPERATIONALLY_VALIDATED=NO`

`CANONICAL_RERUN_REQUIRED=NO`

## 2026-08-30 — SEC-02 Continuity Witness repository foundation reconciled

- Closed WU-01 Domain/Contract foundation and WU-02 Port/authority boundary
  foundation at `5bcaecd05eef403ce2fbc34e97605cccabe37316`.
- Closed WU-03 Lifecycle state machine/fake adapter foundation at
  `a9a511fdf116a4c8f37712b170a0400ea0d7d658`; focused validation passed 65
  tests. No canonical regression was run or newly claimed.
- Recorded exact durable intent binding, pre-planning/pre-mutation Stage-B
  substitution rejection, permanent claim consumption, immutable defensive
  `version_maxima` validation, complete-history GENESIS proof, evidence-only
  immutable history, identity-preserving RECOVERY, terminal no-fresh-MDA
  DECOMMISSION, ordered two-transition MIGRATION, and fail-closed ambiguous
  result/checkpoint handling.
- Preserved Mac mini M4 as sole Control Plane, Continuity Witness as not a
  second Control Plane, and Ubuntu with zero Continuity Witness implementation
  authority.
- Closed SEC-02 repository-foundation work and restored service delivery as the
  primary track. Operational/cloud Continuity Witness implementation remains a
  separate planned security track.

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

## 2026-08-29 — SEC-02 Continuity Witness implementation definition frozen

- Recorded architecture commit `54268cf` and completed the implementation-
  definition architecture freeze without implementation, deployment,
  Production access, Docker/Colima access, AWS access, MDM access, or canonical
  regression.
- Corrected Human Lifecycle Approval binding to the pre-mutation
  `TransitionIntent` digest only; Stage-B `resulting_transition_digests` are
  output evidence only.
- Froze the exact non-circular checkpoint chain from `CheckpointPayload` through
  `StoredCheckpoint` to publication `object_digest`, which is not embedded in
  the stored object it hashes.
- Froze version-aware immutable-history lookup: delete markers and latest-key
  404 results prove neither history absence nor GENESIS.
- Preserved durable approval consumption, migration transition atomicity,
  hardware-binding rotation, signed errors, DECOMMISSION precedence, Mac-only
  Control Plane authority, evidence-only Witness authority, and Ubuntu zero
  authority.

`SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_DEFINITION_ARCHITECTURE_FROZEN=YES`

`ARCHITECTURE_COMMIT=54268cf`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=YES`

`CONTINUITY_WITNESS_IMPLEMENTED=NO`

`CHECKPOINT_CANONICALIZATION_GATE=PASS`

`APPROVAL_TRANSITION_INTENT_BINDING_GATE=PASS`

`IMMUTABLE_HISTORY_VERSION_LOOKUP_GATE=PASS`

`DECOMMISSION_PRECEDENCE_GATE=PASS`

`CONTROL_PLANE_BOUNDARY_GATE=PASS_MAC_MINI_M4_SOLE_CONTROL_PLANE`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`SEC02_SEMANTICS_CHANGED=false`

`GOVERNANCE_CORE_CHANGED=false`

`CONTROLLED_EXECUTION_PORT_CHANGED=false`

`WU09_FILES_CHANGED=false`

`CANONICAL_RERUN_REQUIRED=NO`

## 2026-08-28 — SEC-02 Witness deployment/key-custody architecture frozen

- Completed the docs/architecture-only milestone at commit `7057c96`:
  `SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_ARCHITECTURE_FROZEN=YES`
  and `SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_FREEZE=COMPLETE`.
- Architecture-selected AWS for a stateless external Witness, PostgreSQL-
  compatible transactions, S3 Object Lock Compliance immutable history,
  separate AWS KMS Ed25519 Witness and human lifecycle keys, AWS KMS HMAC-SHA-
  256 hardware indexing, and RFC 8785 JCS signed envelopes.
- Froze rollback-resistant history and fail-closed missing/conflicting-history
  behavior; no PostgreSQL rollback, retention expiry, or incomplete history may
  prove GENESIS, and no operational retention schedule is implemented.
- Recorded the chronology without rewriting it: `41e9f4f` requires no fresh MDA
  for terminal DECOMMISSION and requires one exact human approval bound to the
  current evaluation and record. `96db578`'s conflicting wording is a non-
  authoritative documentation overconstraint erratum corrected by `7057c96`;
  GENESIS, RECOVERY, and MIGRATION freshness rules did not change.
- Preserved permanent durable-claim consumption, read-only reconciliation
  after ambiguous commit acknowledgement, Mac-only Control Plane authority,
  evidence-only Witness authority, Ubuntu zero authority, and every
  implementation and Production blocker.
- No implementation, deployment, operational validation, Production mutation,
  Docker access, AWS API or credential access, cloud resource creation, or
  canonical regression occurred.

`ARCHITECTURE_COMMIT=7057c96`

`CONTINUITY_WITNESS_DEPLOYMENT_ARCHITECTURE_DEFINED=YES`

`KEY_CUSTODY_ARCHITECTURE_DEFINED=YES`

`CONTINUITY_WITNESS_CLOUD_PROVIDER=AWS`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO`

`KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO`

`CONTINUITY_WITNESS_CLOUD_HOST_SELECTED=NO`

`CONTINUITY_WITNESS_INGRESS_TOPOLOGY_DEFINED=NO`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`DECOMMISSION_FRESH_MDA_REQUIRED=NO`

`COMMIT_96db578_DECOMMISSION_FRESH_IDENTITY_REQUIREMENT=DOCUMENTATION_OVERCONSTRAINT_ERRATUM`

`COMMIT_96db578_DECOMMISSION_FRESH_IDENTITY_REQUIREMENT_AUTHORITATIVE=NO`

`SEC02_SEMANTICS_CHANGED=false`

`GOVERNANCE_CORE_CHANGED=false`

`CONTROLLED_EXECUTION_PORT_CHANGED=false`

`WU09_FILES_CHANGED=false`

`CANONICAL_RERUN_REQUIRED=NO`

`PRODUCTION_ACCESS_PERFORMED=false`

`PRODUCTION_MUTATION_PERFORMED=false`

`PRODUCTION_AUTHORIZATION_CONSUMED=false`

`DOCKER_RUNTIME_ACCESSED=false`

`AWS_API_ACCESSED=false`

`CLOUD_RESOURCE_CREATED=false`

`AWS_CREDENTIALS_ACCESSED=false`

## 2026-08-28 — SEC-02 Witness implementation/crypto architecture frozen

- Completed the architecture-only milestone at commit `96db578`:
  `SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_CRYPTO_ARCHITECTURE_FROZEN=YES` and
  `SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_CRYPTO_FREEZE=COMPLETE`.
- Selected DeviceInformation as the MDA transport architecture; no MDM
  configuration, DeviceInformation attestation run, or transport implementation
  is claimed.
- Froze lifecycle states `AVAILABLE`, `DURABLY_CLAIMED`, `COMMITTED`,
  `FAILED_CONSUMED`, and `UNCERTAIN_CONSUMED`. The transition
  `AVAILABLE -> DURABLY_CLAIMED` permanently consumes the exact approval;
  rollback, crash, timeout, disconnect, ambiguity, reconciliation failure, or
  failure to record a later terminal classification can never make it reusable.
  Terminal classifications are durable but are not what destroys authority.
- Froze ambiguous database COMMIT/connection/HTTP-delivery handling: never
  repeat the mutation POST or create retry authority; use only read-only exact-
  result reconciliation through `GET /v1/lifecycle-operations/{operation_id}`.
  Success requires an exact matching `COMMITTED` operation; otherwise fail
  closed, and any later mutation requires a new evaluation and exact approval.
- Selected Ed25519 independently for Witness signing and lifecycle-approval
  signing, with separate keys. Key custody remains undefined.
- Preserved the Mac mini M4 as sole Control Plane, the external Witness as
  durable evidence authority only, Ubuntu as a stateless zero-authority worker,
  Host Caddy as only the Mac AIControlCenter public edge, and Witness ingress as
  undefined.
- Preserved unresolved implementation, MDM transport, key-custody, cloud-host,
  readiness, and Production-bootstrap blockers. No implementation, operational
  activation, Production access, Docker access, or canonical regression
  occurred.

`ARCHITECTURE_COMMIT=96db578`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTED=NO`

`KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO`

`CLOUD_HOST_SELECTED=NO`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`SEC02_SEMANTICS_CHANGED=false`

`GOVERNANCE_CORE_CHANGED=false`

`CONTROLLED_EXECUTION_PORT_CHANGED=false`

`WU09_FILES_CHANGED=false`

`CANONICAL_RERUN_REQUIRED=NO`

## 2026-08-28 — SEC-02 continuity identity lifecycle architecture frozen

- Recorded commit `41e9f4f` and
  `MILESTONE=SEC02_CONTINUITY_IDENTITY_LIFECYCLE_ARCHITECTURE_FROZEN`.
- Froze the witness-assigned, non-operator-selectable `continuity_host_id` and
  Apple Managed Device Attestation as device-identity authentication evidence,
  hardware-bound to the attested UDID and serial number. Apple services are not
  the Continuity Witness, and user enrollment is not allowed.
- Froze GENESIS enrollment, recovery, decommission, physical Mac migration,
  transport-specific exact MDA freshness semantics, and separate Human
  Continuity Lifecycle Approver authority.
- Recorded architecture-level first-install reset resistance as resolved while
  preserving operational resolution as false.
- Implementation has not started, Production bootstrap is unavailable, and no
  Production or Docker access occurred.
- Canonical regression was not required or run because this reconciliation is
  documentation-only.

`FIRST_INSTALL_RESET_ATTACK_ARCHITECTURE_RESOLVED=YES`

`FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO`

`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO`

`MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO`

`IMPLEMENTATION_READY=NO`

`PRODUCTION_BOOTSTRAP_AVAILABLE=NO`

`CANONICAL_RERUN_REQUIRED=NO`

## 2026-08-27 — Generic SEC-02 trusted authorization intake validation

- Validated reusable, non-WU09-specific trusted human authorization intake at
  `IMPLEMENTATION_COMMIT=349a9c5`; canonical deployment regression passed with
  `4212 passed, 5 deselected, 599 warnings` and `CANONICAL_RC=0`.
- Preserved Issuer/Intake/Operator/Executor separation, existing durable
  consumption semantics, fresh post-consumption preconditions, and the
  independent SEC-02 `ALLOW_SINGLE_INVOCATION` requirement. Authenticity and
  consumption evidence do not independently authorize execution.
- Added no generic Production executor or Production private signing-key API.
  Production runtime stores only public verification material and trusted
  issuer metadata; synthetic private keys are tests/fixtures only.
- This is implementation validation, not trusted issuer/trust-root operational
  bootstrap. Production and Docker were not accessed, no Production mutation
  or authorization consumption occurred, and Shopping remains not activated.

## 2026-08-27 — Macro-WU09 governance identity binding correction closeout

- Recorded `WU09_IDENTITY_BINDING_CORRECTION=COMPLETE` at
  `IDENTITY_BINDING_CORRECTION_COMMIT=9e7a4a2`, after initial preload
  `IMPLEMENTATION_COMMIT=e179fb0`.
- Recorded that the correction changed exactly
  `ops/macos/shopping/wu09_image_preload.py` and
  `tests/test_macro_wu09_pinned_image_preload.py`.
- Recorded explicit `GovernanceIdentity` keyword binding: requester
  `identity_id=<requester identity>`, `identity_type=HUMAN`; approver
  `identity_id=<approver identity>`, `identity_type=HUMAN`; Mac Control Plane
  collector/target `identity_id=MAC_MINI_M4`,
  `identity_type=CONTROL_PLANE`.
- Recorded authoritative `CANONICAL_GATE=PASS`,
  `CANONICAL_RESULT=4130_PASSED_5_DESELECTED`, `CANONICAL_WARNINGS=587`, and
  `CANONICAL_RC=0`; canonical was not run for this documentation-only closeout.
- Preserved `GOVERNANCE_IDENTITY_DOMAIN_CHANGED=false`,
  `GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`, and
  `CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`.
- Preserved `WU09_PRELOAD_EXECUTED=false`, `WU09_DEPLOYED=false`,
  `WU09_DEPLOYMENT_AUTHORIZED=false`, `WU10_AUTHORIZED=false`,
  `WU11_AUTHORIZED=false`, and
  `WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`.
- Recorded `TRUSTED_SEC02_PRODUCTION_HUMAN_ISSUER_EXISTS=false`,
  `TRUSTED_AUTHORIZATION_ARTIFACT_BOUNDARY_REQUIRED=true`, and
  `PRODUCTION_COMPOSITION_READY=false`; no claim is made that the pinned image
  is present in Production.
- Recorded next architecture milestone
  `WU09_TRUSTED_PRODUCTION_AUTHORIZATION_INTAKE_FREEZE` and next Production
  readiness milestone
  `WU09_PINNED_IMAGE_PRELOAD_PRODUCTION_COMPOSITION_READY`.

## 2026-08-27 — Macro-WU09 governed pinned-image preload implementation closeout

- Recorded `WU09_PINNED_IMAGE_PRELOAD_IMPLEMENTATION=COMPLETE`,
  `FREEZE_COMMIT=c15c976`, and `IMPLEMENTATION_COMMIT=e179fb0`.
- Recorded `FOCUSED_TEST_GATE=PASS`, `FOCUSED_TEST_RESULT=30_PASSED`,
  `CANONICAL_GATE=PASS`, `CANONICAL_RESULT=4129_PASSED_5_DESELECTED`, and
  `CANONICAL_WARNINGS=579`.
- Recorded the bounded contract
  `EXACT_ACTION_TYPE=SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT`,
  `EXACT_DOCKER_CONTEXT=colima-aicontrolcenter-commerce`, and
  `EXACT_IMAGE=alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1`.
- Preserved exactly one bounded preload invocation per preload authorization,
  with no deployment authority. Preload is a separate Production mutation from
  WU09 deployment, which requires fresh later human authorization.
- Preserved no generic Docker executor, caller-supplied argv/context/image/tag/
  digest, shell, retry, fallback, database mutation, network mutation,
  credential access, MariaDB connection, or SQL.
- Recorded `IMPLEMENTED=true`, `PRELOAD_EXECUTED=false`, `WU09_DEPLOYED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `PRODUCTION_MUTATION_PERFORMED=false`,
  and `WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`; no Production image-presence
  claim is made.
- Recorded `WU09_DEPLOYMENT_AUTHORIZED=false`, `WU10_AUTHORIZED=false`, and
  `WU11_AUTHORIZED=false`.
- Preserved `GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`,
  `CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`,
  `MAC_CONTROL_PLANE=true`, and `UBUNTU_AUTHORITY=false`.

## 2026-08-26 — Macro-WU09 Production-targeting correction

- Recorded `WU09_PRODUCTION_TARGETING_CORRECTION=COMPLETE` and
  `CORRECTION_COMMIT=efdcc5e2da5aee821f28be43011fa08f63e5373d`.
- Fixed execution to `DOCKER_CONTEXT=colima-aicontrolcenter-commerce`, with
  `DOCKER_CONTEXT_EXPLICIT_BINDING=true`, `ACTIVE_CONTEXT_INDEPENDENCE=true`,
  and `IMPLICIT_IMAGE_PULL_DISABLED=true` through `--pull never`.
- Preserved the exact Production target: project
  `ai-shopping-mariadb-loopback`, service `mariadb-loopback-adapter`, bind
  `127.0.0.1:58083`, target `database:3306`, and network
  `ai-shopping-internal`.
- Recorded `FOCUSED_RESULT=19_PASSED`,
  `CANONICAL_RESULT=4095_PASSED_5_DESELECTED`, and `CANONICAL_WARNINGS=575`.
- Preserved `IMPLEMENTED=true`, `DEPLOYED=false`,
  `HOST_PORT_ACTIVE_IN_PRODUCTION=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
  `PRODUCTION_MUTATION_PERFORMED=false`, and
  `PRODUCTION_AUTHORIZATION_CONSUMED=false`; WU10 and WU11 remain separate and
  unauthorized.
- Preserved `GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`,
  `CONTROLLED_EXECUTION_PORT_COUPLED=false`, `MAC_CONTROL_PLANE=true`, and
  `UBUNTU_AUTHORITY=false`.
- Preserved `RECOVER_EVIDENCE_SUFFICIENT=false` and
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

## 2026-08-26 — Macro-WU09 repository implementation documentation closeout

- Recorded `MACRO_WU_09_IMPLEMENTATION=COMPLETE`,
  `ARCHITECTURE_FREEZE_COMMIT=6d31afe`, and
  `IMPLEMENTATION_COMMIT=815d3d5`.
- Recorded `CANONICAL_GATE=PASS`,
  `CANONICAL_RESULT=4093_PASSED_5_DESELECTED`, and
  `CANONICAL_WARNINGS=567`.
- Recorded desired non-secret JSON configuration for
  `PROJECT=ai-shopping-mariadb-loopback`,
  `SERVICE=mariadb-loopback-adapter`, `BIND_HOST=127.0.0.1`,
  `HOST_PORT_ASSIGNED=58083`, `TARGET_HOST=database`, `TARGET_PORT=3306`, and
  `EXTERNAL_NETWORK=ai-shopping-internal`.
- Preserved the deployment boundary: `IMPLEMENTED=true`, `DEPLOYED=false`,
  `HOST_PORT_ACTIVE_IN_PRODUCTION=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
  `PRODUCTION_MUTATION_PERFORMED=false`, and
  `PRODUCTION_AUTHORIZATION_CONSUMED=false`. WU09 Production deployment remains
  a separate future human-authorized mutation; WU10 and WU11 remain separate
  and unauthorized.
- Preserved uncoupled main compose, secret contract, secret preflight,
  Governance core, SEC-02, and `ControlledExecutionPort`; no database-container
  or network mutation, credential access, MariaDB connection, or SQL execution
  occurred. Mac remains the sole Control Plane and Ubuntu zero-authority.
- Preserved `RECOVER_EVIDENCE_SUFFICIENT=false` and
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

## 2026-08-25 — Authoritative Macro-WU06 documentation closeout

- Closed authoritative Macro-WU06 with `MACRO_WU_06_CLOSE_GATE=PASS` and
  `MACRO_WU_06=CLOSED`; current state is
  `REMAINING_AUTHORITATIVE_MACRO_WUS=6` and
  `AUTHORITATIVE_REMAINING_RANGE=WU07-WU12`.
- Recorded `ACTUAL_OFFLINE_EVIDENCE_EVALUATION_GATE=PASS` and
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATION=EVIDENCE_INCOMPLETE`, with
  `AUTH_PLUGIN_EVIDENCE_STATE=MISSING`,
  `PYMYSQL_COMPATIBILITY_EVIDENCE_STATE=MISSING`,
  `DATA_IDENTITY_EVIDENCE_STATE=MISSING`, and
  `CONTINUITY_LINEAGE_EVIDENCE_STATE=MISSING`.
- Preserved `RECOVER_EVIDENCE_SUFFICIENT=false` and
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.
- Recorded four separately human-authorized, exact-path, metadata-only
  `os.lstat` observations. Repository terminology therefore records
  `FILESYSTEM_IO_PERFORMED=true` and
  `PROTECTED_SOURCE_ACCESS_PERFORMED=true`, while
  `FILESYSTEM_CONTENT_READ_PERFORMED=false` and
  `PRODUCTION_ACCESS_PERFORMED=false`. All four leaves were absent; no content,
  alternate-source search, fallback, enumeration, MariaDB, SQL, PyMySQL, or
  secret-value access occurred.
- Preserved `MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
  `CONTROLLED_EXECUTION_PORT_COUPLED=false`, `GOVERNANCE_CORE_CHANGED=false`,
  `SEC_02_CHANGED=false`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. Set
  `NEXT_STEP=MACRO_WU_07_RECOVER_EVIDENCE_SUFFICIENCY_DECISION`.

## 2026-08-25 — Protected evidence acquisition repository validation closeout

- Recorded `ARCHITECTURE_COMMIT=f05c652`, `IMPLEMENTATION_COMMIT=07bf1bd`,
  `PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_IMPLEMENTED=true`, and
  `PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_VALIDATED=true`.
- Recorded `FOCUSED_TEST_GATE=PASS`, `FINAL_CODE_REVIEW_GATE=PASS`,
  `CANONICAL_REGRESSION_GATE=PASS`,
  `CANONICAL_RESULT="4044 passed, 5 deselected, 555 warnings"`, and
  `GIT_DIFF_CHECK_GATE=PASS`. Existing `datetime.utcnow` deprecations and
  pytest `rm_rf` cleanup warnings remain non-blocking technical debt/test
  hygiene.
- Documented fail-closed authorization durability mechanics, source/leaf
  contracts, policy, schema, codec, and tests. Durable `COMMITTED` facts and
  Python object identity grant no authority. Preserved
  `DURABILITY_ZERO_INVOCATION_AUTHORITY=true`,
  `DURABILITY_RESULT_NO_CAPABILITY=true`, and
  `DURABILITY_RECEIPT_NO_CAPABILITY=true`.
- Preserved `PRODUCTION_HUMAN_ISSUER_AVAILABLE=false`,
  `PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE=false`,
  `PRODUCTION_ACQUISITION_AVAILABLE=false`, and
  `PRODUCTION_FILESYSTEM_IO_AVAILABLE=false`; both Production acquisition
  entry points fail closed before filesystem I/O.
- Recorded `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, and `FILESYSTEM_IO_PERFORMED=false`.
- Preserved `MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
  `CONTROLLED_EXECUTION_PORT_COUPLED=false`,
  `GOVERNANCE_CORE_CHANGED=false`, and `SEC_02_CHANGED=false`.
- Preserved `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `MARIADB_CONTINUITY_RECOVERY_INTEGRATED_PROGRAM=IN_PROGRESS`,
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- Set next operational objective
  `ACTUAL_HISTORICAL_EVIDENCE_ACQUISITION_AND_OFFLINE_EVALUATION`; actual
  acquisition requires separate authorization and has not occurred.

## 2026-08-25 — Offline historical evidence evaluator repository closeout

- Recorded `IMPLEMENTATION_COMMIT=b51092f`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_IMPLEMENTED=true`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_VALIDATED=true`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`,
  and `FINAL_OFFLINE_EVALUATOR_ARCHITECTURE_REVIEW_GATE=PASS`.
- Recorded focused `14 passed in 0.03s`, `CANONICAL_REGRESSION_GATE=PASS`,
  `CANONICAL_RESULT="4018 passed, 5 deselected"`, 547 warnings,
  `CANONICAL_RC=0`, `WORKTREE_AFTER_IMPLEMENTATION_PUSH=CLEAN`, `AHEAD=0`, and
  `BEHIND=0`.
- Documented a repository-only, value-free, fail-closed evaluator with
  immutable/slotted factual inputs and results, no caller positive-result
  injection, provenance required for `EVIDENCE_COMPLETE`, and no promotion
  from `EVIDENCE_COMPLETE` to operational `RECOVER` sufficiency.
- Froze exactly five data identity categories: `WORDPRESS_IDENTITY`,
  `SITE_IDENTITY`, `APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`,
  and `CLOSED_TABLE_CHARACTERISTICS`; and exactly three continuity lineage
  categories: `LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and
  `PERSISTENT_VOLUME_SNAPSHOT`. Reused existing
  `EvidenceAcquisitionCategory`.
- Preserved `Source != Acquisition != Fact != OfflineEvaluation !=
  RECOVERDecision != ProductionAccess != CredentialValidation != Authorization
  != Authority`, zero mutation budget, no filesystem I/O, protected-source
  acquisition, network, MariaDB/SQL connection, or Production access, Mac-only
  Control Plane authority, Ubuntu zero authority, unchanged Governance/SEC-02,
  and uncoupled `ControlledExecutionPort`.
- Preserved exactly `FILESYSTEM_IO_PERFORMED=false`,
  `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- Kept actual protected evidence content unopened and unread. Before actual
  acquisition, require a separate architecture boundary for exact protected
  leaf metadata; regular non-symlink leaf; permissions no broader than `0600`;
  trusted UID/GID; stable FD/inode/device binding; TOCTOU-resistant
  acquisition; exact fixed source slot; one-shot human authorization; maximum
  one acquisition per authorization; and no enumeration, candidates, fallback,
  retry, recovery, or authorization reuse. The existing directory metadata
  snapshot is point-in-time only, not stable binding or content-acquisition
  authority. No trusted contents, protected-evidence verification, Production
  readiness, or MariaDB credential continuity is claimed.

## 2026-08-25 — Filesystem target metadata snapshot repository closeout

- Recorded architecture `44f4ef0`, implementation `e9a3645`, focused
  `122 passed in 0.09s`, canonical `4004 passed, 5 deselected, 543 warnings`,
  `CANONICAL_RC=0`, and closed implementation Git evidence:
  `IMPLEMENTATION_COMMIT_RC=0`, `IMPLEMENTATION_PUSH_RC=0`,
  `WORKTREE_STATE=CLEAN`, `AHEAD=0`, `BEHIND=0`.
- Marked `FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_IMPLEMENTED=true` and
  `FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_VALIDATED=true`.
- Recorded the exact two-field request (`concrete_path`,
  `ownership_expectation`), caller exclusion from outcome/classification,
  Mac adapter observation ownership, zero observations for invalid requests,
  and at most one `os.lstat` using the exact unchanged target and consuming
  only `st_mode`, `st_uid`, and `st_gid`.
- Recorded repository-owned reason mappings with `reason` as the sole factory
  classifier input. The positive vocabulary is only
  `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`, never `SAFE_BOUND` or
  `METADATA_SAFE_AND_STABLY_BOUND`.
- Preserved the factual, point-in-time, zero-authority snapshot and
  `stable_handle_bound=false`, `toctou_closed=false`,
  `fd_inode_device_bound=false`; claimed no binding, TOCTOU closure,
  acquisition, evidence admission/verification, `RECOVER` sufficiency, or
  Production readiness/authorization.
- Preserved strict path/expectation/request/snapshot/existence/inspection/
  safety/acquisition/admission/verification/authority separation; all required
  false/unknown operational state; Mac sole Control Plane; Ubuntu zero role and
  authority; unchanged Governance/SEC-02; uncoupled `ControlledExecutionPort`;
  mutation budget zero; `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## 2026-08-24 — Trusted ownership expectation repository closeout

- Recorded freeze `c9bc387`, implementation `220c170`, `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_IMPLEMENTED=true`, `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_VALIDATED=true`, focused `26 passed in 0.03s`, final implementation architecture review `PASS`, canonical regression `PASS`, canonical `3882 passed, 5 deselected, 539 warnings in 136.33s`, `CANONICAL_RC=0`, and closed, clean, synchronized implementation Git closeout.
- Recorded existing resolved-home input, `expected_uid` from `bound_uid`, zero added UID/passwd observations, exact `TRUSTED_APPLICATION_GROUP_NAME="staff"`, at most one exact group lookup using only `gr_gid`, exact non-negative `int`, fail-closed no-retry/fallback/alternate behavior, immutable/slotted exact two-field value, zero authority, and no filesystem/protected-source/Production access.
- Preserved `TRUSTED_GID_SOURCE_ESTABLISHED=false`, `TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`, `PROTECTED_SOURCE_ACCESS_PERFORMED=false`, `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, Mac sole Control Plane, Ubuntu zero role/authority, unchanged Governance/SEC-02, uncoupled execution port, mutation budget zero, `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- Next is separately gated `MACRO_WU_06_FILESYSTEM_TARGET_METADATA_SNAPSHOT_BOUNDARY`, apart from ownership expectation, concrete path, acquisition, and Production authority; no future request, snapshot, or exact-target single-`lstat` adapter was implemented.

## 2026-08-21 — Concrete protected-evidence path composer repository closeout

- Recorded architecture contract `254241a` before implementation `2810c0c`;
  froze `CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_IMPLEMENTED=true`
  and `CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_VALIDATED=true`.
- Recorded focused `11 passed in 0.03s`, Final Architecture Review `PASS`,
  canonical regression `PASS`, canonical
  `3856 passed, 5 deselected, 535 warnings in 133.68s (0:02:13)`, and
  `CANONICAL_RC=0`.
- Recorded `IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`, `WORKTREE_STATE=CLEAN`,
  `AHEAD=0`, and `BEHIND=0`.
- Preserved `ConcreteProtectedEvidencePath` as lexical only and zero-authority,
  not provenance, authorization, capability, verification evidence,
  filesystem existence/safety evidence, `RECOVER` sufficiency, Production
  authorization/readiness, or a security boundary. Python object identity is
  not a security boundary; downstream sensitive boundaries independently
  validate facts, evidence, and authority.
- Preserved all runtime facts as unestablished: trusted home, absolute path,
  concrete path, filesystem I/O, protected-source access, Production access,
  and `RECOVER` sufficiency remain false; offline acquisition remains unknown;
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT` and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- Preserved Mac AIControlCenter as sole Control Plane, Ubuntu zero role and zero
  authority, unchanged Governance and SEC-02, and uncoupled
  `ControlledExecutionPort`.
- Kept `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## 2026-08-21 — Trusted Mac account-home runtime resolver implementation closeout

- Closed only
  `MACRO_WU_06_TRUSTED_MAC_ACCOUNT_HOME_RUNTIME_RESOLVER_IMPLEMENTATION=CLOSED`;
  kept
  `MACRO_WU_06=IN_PROGRESS`, seven authoritative WUs remaining, and range
  WU06-WU12 because actual historical evidence acquisition and offline
  evaluation remain required.
- Recorded architecture contract `41963c1`, architecture clarification
  `cf9c34d`, and implementation `288eb68`; froze
  `RUNTIME_HOME_RESOLVER_REPOSITORY_IMPLEMENTED=true` and
  `RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true`.
- Recorded focused `28 passed in 0.03s`, Final Architecture Review `PASS`, and
  canonical `3845 passed, 5 deselected, 531 warnings`, `CANONICAL_RC=0`.
- Implemented the exact ordered, fail-closed boundary: one platform observation
  requiring exact `Darwin` before UID observation; exactly one real and one
  effective UID observation before root validation; reject either root UID;
  require and bind equality; then exactly one bound-UID passwd lookup.
- Required exact-string, non-empty, NUL-free, lexically absolute POSIX `pw_dir`,
  rejecting `str` subclasses and preserving the passwd string unchanged.
- Preserved no retry/fallback/reconnect/recovery/`getpwnam`; no caller,
  environment, `HOME`, argv, `Path.home`, or `expanduser` authority; no strip,
  normalization, resolution, realpath, canonicalization, filesystem probing,
  existence/type/symlink checks, metadata or ownership/mode inspection, or path
  enumeration.
- Kept `ResolvedTrustedMacAccountHome` immutable, slotted, and limited to
  `bound_uid` and `passwd_home`; prohibited supported direct construction and
  arbitrary UID/home factories. It remains forgeable through theoretical
  Python object-model bypasses, zero-authority, and neither provenance,
  authorization, capability, admission/verification evidence, `RECOVER`
  sufficiency, Production readiness/authorization, nor a security boundary.
- Preserved the exact policy/observation/resolver/resolved-home/suffix-policy/
  suffix/concrete-path/existence/inspection/safety/acquisition/admission/
  verification/authority separation, independent downstream validation, Mac
  sole Control Plane, Ubuntu zero resolver authority, unchanged Governance and
  SEC-02, and uncoupled `ControlledExecutionPort`.
- Preserved `TRUSTED_HOME_VALUE_ESTABLISHED=false`,
  `ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`,
  `FILESYSTEM_IO_PERFORMED=false`, `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; no resolver execution or trusted
  home value is claimed for this repository work.
- Next: read-only architecture discovery/freeze for composing the resolved home
  and frozen exact suffix into distinct zero-authority
  `ConcreteProtectedEvidencePath`, without existence/metadata inspection,
  `stat`/`lstat`, protected evidence access/acquisition, authority, or Production
  access.

## 2026-08-21 — Trusted Mac account-home repository policy implementation closeout

- Preserved chronology: architecture contract/freeze
  `d9def864c83e3660ce9e6afa646ee4f5851934b3`, then symbolic zero-authority
  implementation and Git closeout
  `d07054901b5c3eccac401e90afa4126a9bda9515`.
- Recorded Darwin-only, non-root policy; real UID from `os.getuid()`, effective
  UID from `os.geteuid()`, required equality, and future lookup rule
  `pwd.getpwuid(bound_uid).pw_dir`, without runtime UID/passwd lookup or a
  runtime resolver.
- Preserved policy != runtime identity observation != resolver != trusted home
  != suffix != absolute path composition != existence != inspection != safety
  != acquisition != admission != verification != authority. No trusted home,
  path, filesystem I/O, protected-source/Production access, metadata inspection,
  historical evidence, or authority was established.
- Preserved all required false/unknown facts, including
  `RUNTIME_HOME_RESOLVER_AVAILABLE=false`, `TRUSTED_HOME_VALUE_ESTABLISHED=false`,
  `ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`,
  `FILESYSTEM_IO_PERFORMED=false`, `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- Recorded focused `6 passed in 0.06s`, Final Architecture Review `PASS`,
  canonical `3817 passed, 5 deselected, 527 warnings in 133.93s`, and
  `CANONICAL_RC=0`; Git closeout had `COMMIT_RC=0`, `PUSH_RC=0`, clean worktree,
  `AHEAD=0`, and `BEHIND=0`.
- Preserved Mac sole Control Plane, stateless zero-authority Ubuntu,
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- Next: read-only architecture discovery/freeze for the runtime trusted Mac
  account-home resolver boundary, not resolver implementation. The next
  Production-relevant milestone remains Macro-WU06 Actual Historical Evidence
  Acquisition + Offline Evaluation; Production validation and Shopping runtime
  activation remain unestablished.

## 2026-08-21 — Authoritative Mac protected evidence suffix policy implementation closeout

- Recorded chronology: exact suffix architecture contract established at
  `e1e66ac17b3506a4bff4bd0a9322fc7360ca6536`; repository policy implemented and
  Git-closed at `6c7b18ab942024120b06d1eb0235c7b67b7916df`.
- Closed only
  `MACRO_WU_06_AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY_IMPLEMENTATION`;
  preserved `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- Established the exact repository-owned relative suffix
  `Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`
  and preserved its strict separation from base identities, runtime trusted Mac
  account-home resolution, absolute/concrete path, existence, inspection,
  safety, acquisition, admission, verification, and authority.
- Preserved no caller/environment/HOME/argv/fallback/enumeration/iteration path
  authority; zero filesystem I/O and zero protected-source/Production access;
  no MariaDB/SQL/PyMySQL, Docker/Colima, Ubuntu, Governance-core, SEC-02, or
  `ControlledExecutionPort` coupling; and isolated/unreachable legacy observer.
- Preserved every required false/unestablished downstream fact,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- Recorded focused `6 passed in 0.06s`, Final Architecture Review `PASS`, and
  canonical `3811 passed, 5 deselected, 523 warnings in 134.83s`,
  `CANONICAL_RC=0`; warnings were non-failing.
- Preserved Mac AIControlCenter as sole Control Plane and Ubuntu as a stateless
  infrastructure worker with zero Control Plane authority.
- Next repository activity: architecture-discover/freeze the trusted Mac
  account-home resolution boundary before any concrete path composition or
  runtime resolver. The next Production-relevant milestone remains actual
  historical evidence acquisition and offline evaluation completion under
  Macro-WU06.

## 2026-08-20 — Authoritative Mac base path policy implementation closeout

- Closed `MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION` as a
  repository-only implementation/documentation submilestone; Macro-WU06 remains
  `IN_PROGRESS` with seven authoritative WUs remaining across WU06-WU12.
- Established symbolic-only `AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity`
  and repository-owned, value-free
  `AuthoritativeMacProtectedEvidenceBasePathPolicy`, with an immutable closed
  mapping from `ProtectedExternalEvidenceBaseLocationIdentity`. Its canonical
  factory accepts no caller path, home, or suffix input.
- Recorded no runtime account-home resolver; no production/source use of
  `Path.home`, `HOME`, `os.environ`, `os.getenv`, `sys.argv`, `pwd.getpwuid`,
  `os.getuid`, or `os.getgid`; zero filesystem I/O; and no filesystem adapter,
  metadata inspector, content reader, or Production adapter.
- Preserved zero authorization/capability/execution/mutation/retry/reconnect/
  rollback/acquisition/admission/verification authority, unchanged Governance
  core and SEC-02 semantics, and no `ControlledExecutionPort` coupling.
- Preserved policy identity != exact suffix policy != runtime home resolution !=
  concrete path != existence != inspection != safety != acquisition != admission
  != verification != authority. The suffix remains unresolved and unguessed; no
  directory, path, source existence, inspection, or Production access occurred.
- Recorded commit `ab9de4a08c35de3805983346cf7f1a6d9accccdb`, push `PASS`,
  `AHEAD=0`, `BEHIND=0`, focused `6 passed in 0.05s`, architecture review `PASS`,
  and canonical `3805 passed, 5 deselected, 519 warnings`, `CANONICAL_RC=0`; the
  warnings were non-failing.
- Preserved `BASE_PATH_POLICY_LAYER_REQUIRED=true`,
  `AUTHORITATIVE_BASE_PATH_POLICY_DEFINED=true`, all required downstream
  false/unknown facts, `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- Next: architecture discovery/freeze for the future exact protected-evidence
  suffix policy, without implementing or guessing a suffix, selecting a
  directory, establishing a path, or adding a runtime resolver.

## 2026-08-20 — Protected external evidence source access and metadata inspection boundary closeout

- Closed `MACRO_WU_06_PROTECTED_EXTERNAL_EVIDENCE_SOURCE_ACCESS_AND_METADATA_INSPECTION_BOUNDARY`
  as a repository implementation submilestone only; Macro-WU-06 remains open.
- Preserved Mac sole Control Plane, stateless zero-authority Ubuntu,
  repository-owned path-free zero-authority metadata inspection,
  symbolic-source-only `ProtectedSourceMetadataInspectionRequest`, and `mutation_budget=0`.
- Preserved exact request-instance capability binding (not dataclass equality):
  pre-consumption same-source/different-request and cross-source rejection,
  non-consuming mismatches, at-most-once original success, rejected reuse, and
  exactly-once concurrency.
- Kept inert test provenance distinct from operational evidence; inert
  `SAFE_BOUND` is not operational evidence. No supported
  `HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION` issuer exists; all operational issuer,
  canonical path issuer, and Production inspection availability flags remain false.
- Kept legacy `observe_fixed_protected_source` isolated and unreachable; added no
  caller path/callback, HOME/environment, argv, fallback, enumeration, iteration,
  Governance/SEC-02 change, or `ControlledExecutionPort` reuse.
- Recorded focused `27 passed`, architecture review `PASS`, canonical
  `3799 passed, 5 deselected, 515 warnings`, `CANONICAL_RC=0`, and successful
  push of `daff799d35709da31434ebb280e0771073b12b52`; warnings were non-failing.
- Recorded no Production/protected-source access, inspection/acquisition, or
  MariaDB/SQL/PyMySQL/Docker/Colima/Ubuntu activity.
- Froze `BASE_PATH_POLICY_LAYER_REQUIRED=YES`, proposed
  `AuthoritativeMacProtectedEvidenceBasePathPolicy` and
  `AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity`, and retained the
  existing base-location identity as symbolic-only input. Repository policy,
  runtime home resolution, concrete path, existence, inspection, and safety are
  distinct; `pwd.getpwuid(os.getuid()).pw_dir` is only a possible future trusted
  resolver after exact suffix policy. No exact suffix/path is established.
- Preserved all requested false/unknown path, existence, metadata, acquisition,
  path-authority, `RECOVER`, Production-readiness, and runtime facts.
- Preserved `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12` because acquisition/evaluation have
  not occurred. At that closeout, the next repository-only milestone was
  `MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION`; it is now
  closed as recorded above. It remains value-free and zero-I/O, without path
  resolution, existence check, inspection, runtime resolver, or access; the
  protected-evidence suffix remains unresolved.

## 2026-08-20 — Protected External Evidence Concrete Source Location Descriptor documentation closeout

- Recorded exactly four closed symbolic Concrete Source Location identities and
  their immutable one-to-one mapping from the four Fixed Source Slot identities.
  This establishes descriptors only, not authoritative base, path, existence,
  metadata, acquisition, admission, verification, sufficiency, or authority.
- Preserved the exact semantic chain through Concrete Source Location Descriptor,
  Concrete Path Value, Source Existence, Metadata Inspection, Metadata Safety,
  Content Acquisition, Admission, Verification, and Authority.
- Kept `PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION` symbolic repository policy
  identity only. All downstream factual flags remain false, offline acquisition
  unknown, Production access unjustified, and all caller/environment/HOME/argv,
  fallback, enumeration, and candidate-iteration authority prohibited.
- Classified reverse lookup solely as deterministic closed immutable mapping
  traversal to recover canonical profile identity—not discovery, probing,
  fallback, iteration, caller selection, or environment authority.
- Reused Fixed Source Slot protection requirements as future policy only,
  including Mac/outside-Git ownership, `0700` parent, non-symlink leaf no broader
  than `0600`, uid/gid and future FD/inode/human authorization binding, one-shot
  maximum-one acquisition, and every no-secret-transport/logging/hashing rule.
- Recorded focused `7 passed in 0.06s`, final architecture review `PASS`,
  canonical exactly once (`3772 passed, 5 deselected, 511 warnings in 134.12s
  (0:02:14)`, `CANONICAL_RC=0`), no correction/rerun, and implementation Git
  closeout `PASS` at `c3760d2fd9bb0810d3e285ec203b40e5b7b77814`, divergence 0/0.
- Preserved all Governance, `ControlledExecutionPort`, authorization/mutation,
  Control Plane, Shopping, and target-only provisioning semantics. Kept
  Macro-WU-06 in progress with seven WUs remaining over WU06-WU12; no acquisition
  or evaluation occurred, sufficiency was not evaluated, and WU-07 did not start.

## 2026-08-20 — Protected External Evidence Fixed Source Slot documentation closeout

- Recorded exactly four symbolic `ProtectedExternalEvidenceFixedSourceSlotIdentity`
  values: `AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
  `PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
  `DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`, and
  `CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`, with immutable,
  repository-owned, one-to-one mapping from
  `ProtectedExternalEvidenceSourceProfileIdentity`. Preserved
  `CALLER_SLOT_SELECTION_ALLOWED=false` and `CALLER_PATH_INJECTION_ALLOWED=false`.
- Recorded focused `40 passed in 0.14s`, authoritative final architecture review
  `PASS`, and canonical exactly once afterward: `3765 passed, 5 deselected, 507
  warnings in 134.47s`, `CANONICAL_RC=0`; no code/test correction or canonical
  rerun followed.
- Recorded implementation commit
  `7ccebffcce281590d57f4f8fc93d9e53032bb822`, implementation push `PASS`, `AHEAD=0`,
  `BEHIND=0`, and implementation Git closeout `PASS`.
- Preserved exact semantic separation: `EvidenceAcquisitionCategory` != Source
  Bundle Identity != Protected Source Profile Identity != Fixed Source Slot
  Identity != Concrete Source Location != Source Existence != Metadata Safety !=
  Content Acquisition != Admission != Verification != Authority. Fixed Source
  Slot Identity is symbolic only and establishes none of those downstream facts.
  Preserved `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`,
  `repository_only=true`, `value_free=true`, `fail_closed=true`, and
  `zero_authority=true`.
- Recorded all concrete-path, existence, historical-existence, metadata-inspection,
  metadata-safety, and content-acquisition facts as false; offline acquisition
  remains unknown and Production access unjustified. Protection requirements are
  future policy only: Mac-owned outside Git, exact `0700` parent, regular
  non-symlink leaf no broader than `0600`, trusted uid/gid, future FD/inode and
  human authorization binding, future one-shot acquisition, and all required
  no-fallback/no-enumeration/no-secret-transport/logging/hashing constraints.
- This fixed-source-slot milestone is repository preparation inside
  authoritative Macro-WU-06 and is not authoritative Macro-WU-07.
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; original Macro-WU-07 remains the
  later factual `RECOVER_EVIDENCE_SUFFICIENT` decision. Actual acquisition and
  offline evaluation have not occurred; `RECOVER_EVIDENCE_SUFFICIENT` has not
  been factually evaluated. `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`
  and `PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`.
- Preserved `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`,
  `STRATEGY_EXECUTED=false`, `PRODUCTION_VALIDATION_READY=false`, and
  `SHOPPING_RUNTIME_ACTIVATED=false`. Operational truth remains
  `PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
  `SECRET_VALUES_READ=NO`, `METADATA_INSPECTION=NOT_PERFORMED`,
  `CONTENT_ACQUISITION=NOT_PERFORMED`, `SQL_EXECUTION=NOT_PERFORMED`,
  `PYMYSQL_ACTIVITY=NONE`, and `NOTION_SYNC=NOT_PERFORMED`.
- Preserved Mac AIControlCenter as sole Control Plane and Ubuntu as a stateless
  infrastructure worker with no Control Plane authority.
- No Governance, `ControlledExecutionPort`, or authorization behavior changed.

## 2026-08-20 — MariaDB Continuity Integrated WU-07/WU-08 closeout

- Exact chronology: `MARIADB_CONTINUITY_INTEGRATED_WU_07_DISCOVERY_RECONCILE_GATE=PASS`,
  `MARIADB_CONTINUITY_INTEGRATED_WU_07_IMPLEMENTATION_GATE=PASS`,
  `MARIADB_CONTINUITY_INTEGRATED_WU_07_FOCUSED_GATE=PASS`,
  `FOCUSED_RESULT=17 passed in 0.07s`,
  `MARIADB_CONTINUITY_INTEGRATED_WU_07_FINAL_ARCHITECTURE_REVIEW_GATE=PASS`,
  `MARIADB_CONTINUITY_INTEGRATED_WU_08_CANONICAL_GATE=PASS`,
  `CANONICAL_RESULT=3733 passed, 5 deselected, 495 warnings`,
  `CANONICAL_RC=0`, `IMPLEMENTATION_GIT_CLOSEOUT=PASS`,
  `IMPLEMENTATION_COMMIT=63370cfdf4ea0c80ca54395dd5913317ba529dca`,
  `GIT_PUSH=PASS`, `AHEAD=0`, and `BEHIND=0`.
- Completed the exact four-file implementation and validation of a closed
  twelve-category, repository-only, value-free Evidence Acquisition Descriptor
  Contract. The classifications cover auth-plugin and PyMySQL compatibility
  evidence; database, account, grants, five-category identity, three-category
  lineage, timestamp, integrity, issuer, account-binding, and baseline-binding
  requirements.
- Kept classification, source identity/existence, acquisition, evidence
  existence, admission, verification, authoritative evidence, provenance,
  integrity, timestamp, issuer, bindings, completeness, `RECOVER` sufficiency,
  Production readiness, and authority strictly separate. No source or evidence
  existence, acquisition, admission, verification, or historical evidence is
  claimed.
- Preserved fail-closed zero authority and zero I/O/network/SQL/runtime mutation;
  prohibited caller positive facts, source paths, arbitrary references,
  external evidence values, and secret-bearing content.
- Preserved Mac sole Control Plane, stateless Ubuntu,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, unchanged exact six Shopping
  actions, target-only `SHOPPING_SECRET_PROVISIONING`,
  `ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`,
  `STRATEGY_EXECUTED=false`, `PRODUCTION_VALIDATION_READY=false`, and
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- Operational truth: `PRODUCTION_ACCESS=NOT_PERFORMED`,
  `MARIADB_ACTIVITY=NONE`, `SECRET_VALUES_READ=NO`,
  `SQL_EXECUTION=NOT_PERFORMED`, `PYMYSQL_ACTIVITY=NONE`, and
  `NOTION_SYNC=NOT_PERFORMED`.

## 2026-08-20 — MariaDB Continuity Phase B2B-1D Package-4 documentation candidate

- Recorded discovery and Architecture Freeze `PASS`, exact four-file
  implementation, focused `8 passed in 0.05s`, self-review `PASS`, and Final
  Architecture Review `PASS` across all frozen gates.
- Recorded sandbox canonical `2 failed, 3722 passed, 5 deselected, 481 warnings`,
  `RC=1`, as `ENVIRONMENT_ONLY_FAILURE`: two unrelated dashboard audit-SQLite
  open failures. Host audit-parent preflight was writable; authoritative host
  canonical passed with `3724 passed, 5 deselected, 487 warnings`, `RC=0`.
- No code/test correction followed final review and no canonical rerun followed
  the host pass. Implementation commit
  `9f63463dc9f1c48fdda0ceaba698fead6dd3fab2` and its normal push are `PASS`;
  current HEAD and upstream are aligned at that commit with divergence `0 0`.
  Documentation Git closeout remains pending, so Package-4 is not `CLOSED`.
- Documented only a repository-only, value-free, zero-authority, zero-I/O,
  zero-network, fail-closed external evidence admission and verification
  boundary contract. Presentation, admission, verification, reference-local
  verification, all evidence/provenance/integrity/issuer/binding/compatibility
  facts, completeness, `RECOVER` sufficiency, readiness, and authority remain
  separate. No ingestion, retrieval, verification execution, Production access,
  MariaDB/credential validation, SQL, activation, or historical evidence is
  claimed.
- Preserved unavailable auth-plugin/PyMySQL evidence, false five/three-category
  completeness, insufficient `RECOVER`, unauthorized ROTATE/REPLACE, unexecuted
  strategy, false readiness/runtime, Mac sole Control Plane, stateless Ubuntu,
  factual-only legacy readiness, unchanged Phase-06 semantics and exact six
  Shopping actions, and target-only `SHOPPING_SECRET_PROVISIONING`.

## 2026-08-20 — MariaDB Continuity Phase B2B-1D Package-3 documentation candidate

- Recorded `PHASE_B2B_1D_PACKAGE_3_EXTERNAL_EVIDENCE_ATTESTATION_REFERENCE_CONTRACT`
  as implementation-complete and validation-complete at
  `1f9790fe1c96a6c20135508e4bcfbfce5d897546`; implementation Git closeout and
  push passed, with final clean worktree and upstream divergence `0 0`.
- Recorded Architecture Freeze `PASS`; initial focused `8 passed in 0.05s`;
  review #1 `BLOCKED` on the incorrect canonical
  `VERIFIED_EXTERNAL_REFERENCE` default; correction `PASS`; corrected focused
  `9 passed in 0.05s`; and review #2 `PASS`.
- Recorded canonical #1 `3716 passed, 5 deselected, 475 warnings`, `RC=0`.
  Closeout preflight then blocked on trailing EOF blank lines in exactly two
  files. The EOF-only correction had `SEMANTIC_CHANGE_GATE=NO_CHANGE`;
  architecture reconcile and all prior gates passed; corrected canonical was
  `3716 passed, 5 deselected, 479 warnings`, `RC=0`.
- Recorded late focused on the identical committed snapshot as `9 passed in
  0.04s`; no canonical rerun occurred after implementation Git closeout.
- Documented canonical `VERIFICATION_REQUIRED`, with
  `VERIFIED_EXTERNAL_REFERENCE` separate, reference-local, and zero-promotion.
  Package-3 is repository-only, immutable, fail-closed, value-free,
  zero-authority, zero-I/O, and zero-network; it accepts no evidence values,
  caller-positive fact injection, or arbitrary reference strings.
- Documented direct reuse of `EvidenceRequirementCategory`, `VerificationState`,
  `DataIdentityCategory`, and `ContinuityEvidenceCategory`.
- Preserved unavailable auth-plugin/PyMySQL evidence, incomplete five/three
  categories, insufficient `RECOVER` evidence, unauthorized ROTATE/REPLACE,
  unexecuted strategy, and false Production readiness/runtime. No actual
  historical evidence is claimed.
- Preserved Mac sole Control Plane, stateless Ubuntu, factual-only legacy
  readiness, the exact six Shopping actions, target-only
  `SHOPPING_SECRET_PROVISIONING`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- Repository milestone closure remains pending final documentation review and
  documentation Git closeout of exactly these six documents.

## 2026-08-19 — MariaDB Continuity Phase B2B-1D Package-2 documentation candidate

- Recorded `PHASE_B2B_1D_PACKAGE_2_EXTERNAL_EVIDENCE_REFERENCE_MANIFEST` at
  implementation commit `0c6cf471da9e918e798f8a71fb2d28a4afc98d46`, with
  implementation and Git closeout `PASS`, focused `29 passed in 0.05s`, final
  architecture review `PASS`, and exactly-once post-review canonical `3707
  passed, 5 deselected, 471 warnings`, `RC=0`. Warnings are not failures; no
  focused or canonical rerun followed implementation Git closeout.
- Recorded implementation scope as
  `core/secrets/mariadb_continuity_evidence_reference_manifest.py` and
  `ops/macos/shopping/mariadb_continuity_evidence_reference_source.py`, with
  focused tests in
  `tests/test_sm_mariadb_continuity_evidence_reference_manifest.py` and
  `tests/test_sm_mariadb_continuity_evidence_reference_source.py`.
- Documented repository-only, immutable, fail-closed, value-free, zero-authority
  separation of requirement, reference state, existence, provenance validity,
  authority, compatibility, and reference-local readiness. `VerificationState`
  is exactly `UNAVAILABLE`, `REFERENCED_UNVERIFIED`, `VERIFICATION_REQUIRED`,
  and `VERIFIED_EXTERNAL_REFERENCE`; verified/reference readiness remains local
  factual state, not existence, provenance, canonical availability,
  compatibility, aggregate readiness, `RECOVER` sufficiency, Production
  validation readiness, or authorization/capability/execution/mutation authority.
- Recorded the five exact non-B1 categories and direct reuse—without duplicate
  enums—of all five frozen `DataIdentityCategory` values and all three frozen
  `ContinuityEvidenceCategory` values.
- Froze value-free manifest safety: no caller-supplied reference; no assertion
  of existence, authority, compatibility, or readiness; no secret, credential
  hash, arbitrary free text, or SQL; and no I/O, network, or Production trigger.
  Source projections grant no authorization, capability, execution, mutation,
  retry, reconnect, or rollback authority.
- Preserved unresolved auth plugin, unavailable authoritative evidence,
  compatibility false, incomplete five/three category evidence, and insufficient
  `RECOVER` evidence. The human `RECOVER` decision remains zero-authority;
  ROTATE/REPLACE are unauthorized and strategy execution is false. Fixed SQL,
  numeric port, target deployment, concrete credential path, and credential
  reader remain false/unavailable.
- No Production access, MariaDB authentication, secret read, SQL, PyMySQL
  installation, or Notion sync occurred; Production readiness and Shopping
  runtime remain false. Preserved Mac Control Plane ownership, stateless Ubuntu,
  factual-only legacy `production_validation_ready`,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping actions,
  and target-only `SHOPPING_SECRET_PROVISIONING`.
- This edit is not Package-2 closure. Final documentation review, exact-six-doc
  commit and normal push, clean-tree verification, and divergence `0 0`
  self-activate closure without a second SHA-recording edit. Only afterward is
  the next work the next MariaDB continuity evidence/strategy boundary.

## 2026-08-18 — MariaDB Continuity Phase B2B-1D Package-1 documentation candidate

- Recorded implementation `cacc659fd518c751544a8062ce0c36813f1c7bcc`, Git
  closeout `PASS`, focused `79 passed in 0.20s`, architecture review #3 `PASS`,
  and canonical-once `3678 passed, 5 deselected, 467 warnings in 133.11s`,
  `RC=0`. Reruns are `NOT_RUN`; canonical rerun requires code/test change.
- Added repository-safe, value-free, zero-authority contracts for authoritative
  historical auth-plugin evidence, its single source of truth, override
  prohibition, compatibility proof, Mac-owned identity, complete five-category
  data identity, exact three-category continuity lineage, independent
  provenance, and human strategy choice when `RECOVER` evidence is insufficient.
- Preserved fail-closed auth truth and the prior `PyMySQL==1.2.0` declaration as
  declaration only: no installation/import and no compatibility proof.
- Fixed the closed operation profile while keeping fixed SQL unavailable and
  prohibited; preserved zero Production mutation, one future attempt maximum
  per non-reusable human authorization, and no retry/reconnect/rollback.
- Added no aggregate readiness authority; preserved the Phase-A legacy
  `production_validation_ready` DTO, exact six Shopping actions, target-only
  `SHOPPING_SECRET_PROVISIONING`, Mac ownership, stateless Ubuntu, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- No Production access, MariaDB authentication/connection, secret read, or SQL
  occurred; readiness/runtime remain false. Package-1 is not `CLOSED`: review,
  exact-six-doc commit/push, clean Git, and divergence `0 0` self-activate
  closure. Next is a B2B-1D evidence/architecture boundary, not Production.

## 2026-08-18 — MariaDB Continuity Phase B2B-1C documentation closeout candidate

- Recorded completed implementation at
  `d4802054366178c6e3282ad089e393726f2d9309`: `9 files changed`, `91
  insertions`, `4 deletions`; implementation Git closeout `PASS`.
- Recorded focused validation `42 passed in 0.16s`, final architecture review
  `PASS`, and the exactly-once post-review canonical result `3674 passed, 5
  deselected, 463 warnings in 134.93s`, `CANONICAL_RC=0`. No rerun is required
  absent code/test changes.
- Recorded the exact dependency declaration `PyMySQL==1.2.0` and preserved
  `DRIVER_FAMILY=PYMYSQL`, `DRIVER_VERSION=1.2.0`, and
  `DRIVER_MODE=SYNCHRONOUS_ONE_SHOT`. The declaration establishes neither
  installation, import, compatibility, nor readiness: `PYMYSQL_INSTALLED=NO`,
  `driver_imported=false`, `PYMYSQL_COMPATIBILITY_ESTABLISHED=false`, and
  `AUTH_PLUGIN_STATE=UNRESOLVED`.
- Preserved the symbolic-only credential boundary with no concrete path or
  value read. Future requirements remain a fixed closed source, exact `0700`
  protected parent, regular non-symlink leaf no broader than `0600`, trusted
  uid/gid, FD/inode binding, and at most one acquisition per authorization only
  after capability consumption; no fallback, enumeration, candidate iteration,
  environment/`HOME` authority, argv/JSON/log secret, or secret hashing.
- Preserved frozen B1 `ContinuityEvidenceCategory` as exactly `LOGICAL_EXPORT`,
  `RECOVERY_ARTIFACT`, and `PERSISTENT_VOLUME_SNAPSHOT`, with
  `independent_historical_provenance_required=true`. Added no connection, SQL,
  retry, reconnect, pooling, `ControlledExecutionPort` use, Governance semantics
  change, or Production authority.
- Preserved Mac Control Plane ownership, stateless Ubuntu,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping actions,
  and target-only `SHOPPING_SECRET_PROVISIONING`.
- Preserved runtime truth: Production access and MariaDB authentication
  `NOT_PERFORMED`, secret values read `NO`, SQL `NOT_PERFORMED`,
  `PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
- This six-document state is only the documentation closeout candidate.
  `PHASE_B2B_1C` becomes authoritatively `CLOSED` after final documentation
  review, creation and normal push of its containing documentation commit,
  clean Git status, and upstream divergence `0 0`. That self-activating rule
  requires no second mutation to record the commit SHA. The next milestone
  remains a separate architecture/discovery boundary, not Production invocation.

## 2026-08-18 — MariaDB Continuity Phase B2B-1A final closure candidate

- Prepared this exact six-document reconciliation as the `FINAL CLOSURE
  CANDIDATE` while uncommitted; it does not claim that its own Git closeout has
  completed.
- Preserved implementation, focused validation, architecture review, canonical
  validation, and implementation Git closeout as `CLOSED`, and recorded
  `099258ce3470f57e9260a1f671b404ed9d42a623` only as evidence for the prior
  reviewed documentation snapshot and its documentation Git closeout.
- Defined the self-activating transition: `PHASE_B2B_1A=CLOSED` becomes
  authoritative only when the commit containing this exact reconciliation is
  committed, normally pushed, followed by clean Git status, and followed by
  upstream divergence `0 0`; passing those checks requires no second
  documentation mutation.
- Preserved the prior `IN_CLOSEOUT` chronology, all validation evidence, the
  exactly-once canonical policy, runtime false/unavailable facts, architecture
  invariants, and the read-only next milestone
  `PHASE_B2B_1B_CONCRETE_READINESS_DISCOVERY`.

## 2026-08-18 — MariaDB Continuity Phase B2B-1A implementation closeout

- Implemented `PHASE_B2B_1A` at
  `aa049e2940707ff9209a730ecfbcc5f705062171`: exactly 16 new files and 924
  insertions of repository-only, value-free prerequisite contracts.
- Architecture review #1 was `BLOCKED` by incorrect `ImportFrom` alias-based
  root inspection, an invalid permanent pytest approach to untracked Git scope,
  incomplete preservation of the five frozen B1 `DataIdentityCategory`
  meanings, and a duplicate `ContinuityEvidenceCategory`.
- Corrected root detection through `node.module`, assigned exact untracked scope
  to the external Git closeout gate, directly reused both frozen B1 enum types,
  and explicitly tested enum identity/type reuse. Corrected focused validation:
  `49 passed in 0.14s`; final architecture review #2: `PASS`.
- Canonical executed exactly once after final architecture `PASS`: `3673 passed,
  5 deselected, 459 warnings in 134.90s`, `RC=0`; it must not be rerun without
  code/test changes. Git implementation closeout: `PASS`.
- Preserved PyMySQL `1.2.0` synchronous one-shot, unresolved auth plugin and
  compatibility false; symbolic Mac-owned credentials; unavailable identity,
  grants, and historical baselines; no fixed/arbitrary SQL; unassigned port;
  undeployed target.
- Production/MariaDB/SQL/Docker/Colima/Notion access was `NOT_PERFORMED`;
  secret values read `NO`; authorization consumed `NO`; PyMySQL installed `NO`;
  requirements changed `NO`; `PRODUCTION_VALIDATION_READY=false` and
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- Preserved all B2A/B1/Phase A invariants,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, Mac as sole Control Plane,
  Ubuntu as stateless worker, the exact six Shopping actions, and target-only
  `SHOPPING_SECRET_PROVISIONING`. Documentation is `IN_CLOSEOUT`; next is the
  read-only `PHASE_B2B_1B_CONCRETE_READINESS_DISCOVERY` boundary with no
  installation, Production/authentication/credential/SQL access, numeric-port
  deployment, requirements change, or activation implied.

## 2026-08-18 — MariaDB Continuity Phase B2A documentation closeout

- Recorded Phase B2A implementation and validation as closed at
  `6063ce08b62e99331f5d442afc9d2a71703bcabf`; documentation and repository
  closeout completed at `cfb1d7eae4b9676373ba31c485330b8449cd90f3`.
- Added value-free continuity contracts only. Canonical current truth remains
  separate from constructible observations. Runtime states are exactly
  `CONFIRMED`, `REJECTED`, `NOT_EVALUATED`, and `UNCERTAIN`; complete validation
  requires all six mandatory facts confirmed. All projections grant zero
  authorization, capability, execution, mutation, retry, reconnect, and
  rollback authority.
- Added metadata-only validation for one fixed protected source: parent `0700`,
  directory, non-symlink, expected uid/gid; leaf non-empty regular non-symlink,
  permissions no broader than `0600`, expected uid/gid. The reason vocabulary
  is closed and contradictions are rejected. Manually constructed positives
  remain inert value-free factual/fake DTOs without readiness or authority;
  trusted filesystem evidence remains separately produced by
  `observe_fixed_protected_source`. No value read, enumeration, or fallback.
- Preserved target `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`, owner
  `MAC_CONTROL_PLANE`, with `numeric_loopback_port_assigned=false`,
  `target_deployed=false`, and `production_target_ready=false`; no numeric port
  is assigned.
- Recorded driver contract `PYMYSQL` `1.2.0`, synchronous one-shot,
  `AUTH_PLUGIN_STATE=UNRESOLVED`, maximum one future connection per
  authorization. PyMySQL import/install is absent, requirements unchanged, and
  no network, SQL, retry, reconnect, or pooling exists.
- Production files: `core/secrets/mariadb_continuity_observations.py`,
  `ops/macos/shopping/mariadb_continuity_protected_sources.py`,
  `ops/macos/shopping/mariadb_continuity_pymysql_adapter.py`, and
  `ops/macos/shopping/mariadb_continuity_target_resolver.py`. Tests are the
  corresponding four `tests/test_sm_mariadb_continuity_*.py` files for
  observations, protected sources, PyMySQL adapter, and target resolver.
- Validation: initial focused `21 passed in 0.35s`; first final review
  `BLOCKED`; corrected focused `31 passed in 0.13s`; final read-only review #2
  `PASS`; canonical exactly once on final reviewed state, `3624 passed, 5
  deselected, 455 warnings in 134.66s`, `RC=0`. Both post-commit reruns:
  `NOT_RUN`.
- Normal push, final clean check, and divergence `0 0` passed. A duplicate
  closeout was correctly rejected for stale expected pre-commit HEAD, producing
  no second commit, push, or implementation change.
- Runtime: Production access, MariaDB authentication, SQL, Docker, Colima, and
  Notion sync `NOT_PERFORMED`; secret values read `NO`; PyMySQL installed `NO`;
  requirements changed `NO`; auth plugin unresolved; loopback port unassigned;
  `PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
- Preserved Mac as sole Control Plane, Ubuntu as stateless worker,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping actions
  named in the preserved architecture record, and target-only
  `SHOPPING_SECRET_PROVISIONING`. Named next boundary
  `PHASE_B2B_CONCRETE_INTEGRATION_DISCOVERY` without implementing it.

## 2026-08-18 — MariaDB Continuity Phase B1 documentation closeout

- Marked Phase B1 implementation- and validation-complete at
  `acdbd859872b842691c293b5e094472b344d304b`.
- Added the factual one-shot lifecycle `NEW -> AUTHORIZED -> CONSUMED ->
  PRE_ATTEMPT -> ATTEMPT_INITIATED -> TERMINAL`. Pre-attempt closure preserves
  `attempted_count=0`; initiated-attempt closure preserves `attempted_count=1`.
  Skips, reversal, repetition, post-terminal transition, and a second attempt
  are prohibited; `AUTHORIZED` grants no authority.
- Froze the value-free source categories as exactly `CREDENTIAL_SOURCE`,
  `EXPECTED_IDENTITY_DESCRIPTOR`, `DATA_IDENTITY_BASELINE`, and
  `DATA_CONTINUITY_BASELINE`. All four availability facts remain false, and
  supported public construction rejects unsupported positive or contradictory
  availability.
- Preserved the Mac-Control-Plane-owned credential contract: external fixed
  slot outside Git, `0700` protected parent, `0600` regular non-symlink file,
  explicit trusted uid/gid, no ambient `HOME`/UID authority, no env/argv/JSON
  secret/Governance transport, no secret log/hash, fallback, enumeration, or
  candidate iteration, and at most one post-consumption acquisition. No actual
  credential material was read or verified.
- Defined target `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`, owner
  `MAC_CONTROL_PLANE`, with `canonical_target_contract_defined=true`,
  `numeric_loopback_port_assigned=false`, `target_deployed=false`, and derived
  `production_target_ready=false`. No caller host/port/DSN/URL/database/username
  and no numeric MariaDB port exist in Phase B1.
- Added no PyMySQL, MariaDB driver, SQL, network, filesystem credential reader,
  env/argv credential transport, retry, reconnect, pooling, Production access,
  or MariaDB authentication. `PRODUCTION_VALIDATION_READY=false` and
  `SHOPPING_RUNTIME_ACTIVATED=false`; access/authentication/runtime/Docker/
  Colima/Notion were `NOT_PERFORMED`, secret values read `NO`, PyMySQL installed
  `NO`, and requirements changed `NO`.
- Preserved `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six actions
  remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
  `SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
  `SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
  `SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
  `SHOPPING_SECRET_PROVISIONING` remains target-only; Mac AIControlCenter is the
  sole Control Plane and Ubuntu remains stateless.
- Recorded the full validation history: initial focused `22 passed in 0.07s`;
  first review `BLOCKED` for public factual forgeability/contradiction handling
  and insufficient associated tests; correction `PASS`; corrected focused
  `37 passed in 0.06s`; final read-only review `PASS`; exactly one final-state
  canonical invocation, `3593 passed, 5 deselected, 447 warnings in 133.58s`,
  `RC=0`; post-commit canonical rerun `NOT_RUN`.
- Left Phase B2 as future-only work: possible PyMySQL selection/pinning,
  synchronous one-shot Mac adapter, fixed loopback resolver, protected
  credential reader, independent expected DB/account/grants and data identity/
  continuity baseline readers, and fixed parameterized read-only SQL with one
  connection and no retry/reconnect/pooling. Phase B2 is not implemented or
  Production-ready; no new numeric SM-01B-02D milestone is invented.

## 2026-08-18 — MariaDB Continuity Validation Prerequisite / Phase A

- Repository-complete after documentation closeout at implementation commit
  `ccf3ce00f7f6602d2cc6a84ec5632c7088cae418`.
- Added only value-free prerequisite/readiness facts and a Mac Control Plane
  process-local composition boundary, with a non-serializable one-shot
  `HumanPresenceGrant`, prohibited direct construction, private inert Phase-A
  test issuance, canonical request binding, concurrent exactly-once use,
  consume-before-assembly, permanent consumption after assembly failure,
  redacted exceptions, and no capability invocation during composition.
- Added no driver, Production credential source or material verification, SQL,
  network connectivity, canonical target, identity/continuity baseline, real
  Production capability or authentication, consumer compatibility validation,
  mutation authority, or activation. `PRODUCTION_VALIDATION_READY=false`,
  `SHOPPING_RUNTIME_ACTIVATED=false`; historical MariaDB credential continuity
  remains unresolved.
- Preserved `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping
  secret provisioning actions, Mac AIControlCenter as sole Control Plane, and
  Ubuntu as a stateless infrastructure worker.
- Evidence: focused `13 passed in 0.07s`; final architecture review `PASS`;
  canonical `3556 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly
  once on the final reviewed implementation tree; post-commit canonical rerun
  `NOT_RUN`. Production access/authentication, runtime, Docker, Colima, and
  Notion were `NOT_PERFORMED`; secret values read `NO`.
- The next current development boundary is Phase B architecture discovery. Its
  preparation covers MariaDB driver selection and dependency pinning, a fixed
  Mac Control Plane driver boundary, the canonical loopback target/profile
  contract, protected external historical credentials, independent expected
  DB/account identity, data-identity, and historical continuity descriptors or
  baselines, no retry/reconnect/pooling semantics, and a fixed read-only SQL
  surface design. No successor `SM-01B-02D` milestone is assigned without
  repository evidence.

## 2026-08-18 — SM-01B-02D-06 MariaDB Historical Credential Continuity Validation Boundary v1

- CLOSED at implementation commit `3c93ad39586080db618ee090a7548806c024c44a`.
  Added a Mac mini M4 AIControlCenter-owned, value-free, read-only validation
  model, port, and macOS outer adapter. This is not a Production mutation
  boundary or `ControlledExecutionPort`, uses no `GovernanceMutationBudget`,
  implements no real MariaDB client or Production capability, and grants zero
  mutation, authorization, execution, retry, or rollback authority.
- Closed outcomes to `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`,
  `MALFORMED`, `UNCERTAIN`. `VALIDATED` requires `attempted_count=1` and separate
  `CONFIRMED` observations for credential acceptance, database identity,
  account identity, required grants, data identity, and data continuity;
  authentication alone is insufficient. Consumer compatibility remains
  `NOT_EVALUATED`; `UNCERTAIN` fails closed. No retry, fallback, iteration,
  guessing, rollback, or compensation exists.
- Defined the future Production capability as externally supplied,
  non-factual, non-serializable authority metadata, absent from serialized
  request/result/projection, not minted by core, and invocable at most once per
  application validation invocation.
- Preserved authorization consumption and durable SQLite, Governance execution,
  SEC-02/postconditions/audit/evidence, coordinator, config, schemas, 05
  `ContinuityDecision`, the exact six provisioning actions, and
  `SHOPPING_SECRET_PROVISIONING` as a target rather than an action.
- Recorded no Production authentication or credential validation and no
  recovery, strategy selection, mutation, materialization, cutover, retirement,
  or activation. Historical continuity remains `UNRESOLVED` and
  `SHOPPING_RUNTIME_ACTIVATED=false`; future Production validation requires
  separate explicit human authorization and the result then informs a human
  `RECOVER`/`ROTATE`/`REPLACE` decision.
- Focused validation: `33 passed in 0.08s`. Architecture review: `PASS`, all
  severities `NONE`. The canonical gate was accidentally run twice on the same
  unchanged final-reviewed tree; both runs reported `3543 passed`, `5
  deselected`, `447 warnings`, `RC=0`. This is an operational process deviation,
  not a code or architecture failure; no implementation/code/test change
  occurred between runs. Implementation push `PASS`; final Git clean and
  divergence `0 0`. Production/runtime/Docker/Colima/Notion access was not
  performed; secret values read: `NO`.

## 2026-08-18 — SM-01B-02D-05 MariaDB Credential Continuity Decision Model v1

- CLOSED at implementation commit `9f168cc475345e7d2c949f375ef5c44f2ad2fda9`.
  Added fail-closed public factual `ContinuityDecision` metadata with exactly
  `UNRESOLVED`, `STRATEGY_DECLARED`, `VALIDATION_REQUIRED`, `RESOLVED` and
  strategies `RECOVER`, `ROTATE`, `REPLACE`. `RESOLVED`, strategy selection,
  and caller-supplied `validation_confirmed` grant zero authority; trustworthy
  Production acquisition of confirmation remains separately bounded future
  validation. `mutation_authority=false`; `capability_id=null`.
- Stored and transported no credential or secret value and introduced no
  password, username, secret-derived hash/digest, private identity, recipient
  value, arbitrary path, environment value, stdout/stderr, command, argv,
  executable, callback, port, authorization, mutation budget, execution
  request, or execution receipt.
- Preserved the exact six Shopping provisioning actions and kept
  `SHOPPING_SECRET_PROVISIONING` as a target, not a seventh action. Changed
  neither `AuthorizationConsumptionPort`, durable SQLite consumption, mutation
  budgets, `ControlledExecutionPort`, SEC-02/postconditions, Governance
  audit/evidence, coordinator, adapters, config, schema, nor inspectors.
- Implemented no Production validation, recovery/rotation/replacement
  execution, `MARIADB_CREDENTIAL_ROTATE`, `MARIADB_CREDENTIAL_REPLACE`, DB
  payload/materialization, DB-dependent validation, DB/runtime cutover, or
  activation; made no claim historical credentials were recovered, validated,
  rotated, replaced, materialized, or activated.
- Preserved Mac mini M4 AIControlCenter as sole Control Plane and Ubuntu as a
  stateless worker, with no authority delegated to WordPress, WooCommerce, n8n,
  Ubuntu, or external recovery custody systems.
- Focused validation: `39 passed in 0.04s`. Canonical: `3510 passed`, `5
  deselected`, `447 warnings`, `RC=0`. Final architecture review: `PASS`;
  `CRITICAL=NONE`, `HIGH=NONE`, `MEDIUM=NONE`, `LOW=NONE`. Implementation push:
  `PASS`. Production access and Notion sync: `NOT_PERFORMED`.

## 2026-08-18 — SM-01B-02D-04B Provisioning Runtime Composition & Read-Only Postconditions v1

- CLOSED 04B at `a4cb53d5398dffdc33366ac042fdb7813f6d4577` (`feat(shopping):
  add secret provisioning readiness composition`). Added Mac-Control-Plane-owned,
  JSON-first deterministic read-only, structural, value-free readiness composition.
- Closed readiness to `READY`, `MISSING`, `BLOCKED`, `UNSAFE`, `MALFORMED`;
  configured/ready false/false, true/false, true/true, false/true map to
  `MISSING`, `BLOCKED`, `READY`, fail-closed `MALFORMED`. Malformed blocks
  overall readiness and activation.
- Preserved six actions, separate offline intake/registration, and unchanged
  Governance authorization, durable consumption, and `ControlledExecutionPort`.
  No mutation API/payload/materialization/cutover; `materialization_implemented=false`,
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- MariaDB continuity remains unresolved and blocks DB readiness/materialization,
  validation/cutover, and runtime activation. Recovery/replacement is not
  claimed; dedicated Shopping materialization architecture is future work.
- Recorded focused `47 passed`; canonical `3471 passed, 5 deselected, 447
  warnings` in approximately `133.97s`, `CANONICAL_RC=0`, `CANONICAL_GATE=PASS`;
  implementation push/clean/divergence `0 0`/closeout PASS. Production and
  Notion were not accessed; canonical was not rerun for docs closeout.

## 2026-08-18 — SM-01B-02D-04A Governed Offline Public Recipient Intake v1

- Added the exact sixth provisioning action,
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`, as a typed,
  value-redacted boundary for exactly one already-public age recipient.
- Kept intake separate from
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`; each needs a
  fresh human authorization, mutation budget, execution request, and durable
  authorization-consumption record.
- Hardened the fixed, outside-Git Mac Control Plane inbox with trusted age
  prevalidation before mutation, safe existing descriptor-relative parent
  traversal, exclusive no-follow creation, owner/mode/size checks, fresh-parent
  and created-leaf device/inode binding, and `UNCERTAIN` after any ambiguous
  post-creation outcome. No generic write/path/shell API, cleanup, retry,
  rollback, compensation, repair, or recovery was added.
- Preserved external private-identity custody, value-free evidence, Mac-only
  Control Plane authority, stateless Ubuntu, and unchanged durable
  authorization-consumption semantics
  (`CORE_GOVERNANCE_SEMANTICS_CHANGE_REQUIRED=false`).
- Recorded focused `163 passed` and canonical `3457 passed, 5 deselected, 447
  warnings in 133.23s`, `RC=0`; the warnings are not 04A failures.
  Implementation commit `6e1aa0135b652b199f05a4911c0f45817a8529f4` and Git
  closeout PASS, clean, upstream divergence `0 0`.
- Performed no real Production recipient intake, filesystem mutation,
  installation, identity creation, registration, or runtime cutover. MariaDB
  continuity remains unresolved; Notion is deferred and
  `SHOPPING_RUNTIME_ACTIVATED=false`.

## 2026-08-18 — SM-01B-02D-03 Durable Authorization Consumption & Evidence Store v1

- Closed `SM_01B_02D_03_DURABLE_AUTHORIZATION_CONSUMPTION_VALIDATED=true` at
  implementation commit `681a9e342fde47c7bcb9d3aa2d497b737a19e052`; Git closeout
  PASS, pushed, upstream divergence `0 0`.
- Added generic Mac Control Plane Governance persistence, not Shopping logic or
  Ubuntu state, without changing `AuthorizationConsumptionPort` or core
  semantics (`CORE_SEMANTICS_CHANGE_REQUIRED=false`). The Governance-owned
  SQLite path is
  `~/Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3`;
  ownership is validated, the shared parent remains unchanged, Governance is
  `0700`, the database `0600`, and Production state remains outside Git.
- Added `DURABLY_CLAIMED` before atomic final authorization/budget `CONSUMED`,
  zero invocation/completed/uncertain accounting, and `COMMITTED` receipt.
  Protected identities use value-free binding/integrity digests; no secrets persist.
- Fresh replay and stranded claims fail closed without historical-result return,
  claim stealing, lease, expiry, recovery, retry, rollback, or compensation.
  Only the same invocation with ambiguous commit acknowledgement may reconcile
  against its exact validated expected `COMMITTED` record.
- Preserved authority separation: consumption evidence and remaining-budget
  accounting grant no execution/retry authority. Preconditions must be freshly
  recollected/recompared and SEC-02 must yield `ALLOW_SINGLE_INVOCATION` before
  `ControlledExecutionPort`; replay cannot resurrect authority.
- Recorded focused `372 passed`; corrected-tree canonical `3433 passed, 5
  deselected, 447 warnings in 135.93s`, `RC=0`, exactly once after final fixture
  correction. Recorded all of `PRODUCTION_MUTATION`, `AUTHORIZATION_CONSUMED`,
  `SECRET_VALUES_READ`, `RUNTIME_INSPECTION`, `DOCKER_ACCESS`, `COLIMA_ACCESS`,
  `NOTION_SYNC`, and `SHOPPING_RUNTIME_ACTIVATED` as `false`.
- SM-01B remains incomplete; no Production provisioning occurred. SOPS/age,
  control-plane identity, recipients, payload/materialization, and activation
  remain outstanding. MariaDB credential continuity remains unresolved and is
  not recovered by SOPS+age. Offline-recovery private identity stays outside the
  Production Mac; public-recipient intake needs explicit governance. Notion is
  deferred until `SHOPPING_RUNTIME_ACTIVATED`.

## 2026-08-17 — SM-01B-02D-02B Shopping Secret Provisioning Capabilities v1

- Closed implementation, validation, and Git closeout at
  `SM_01B_02D_02B_SECRET_PROVISIONING_CAPABILITIES_VALIDATED=true`, implementation
  commit `bffe28a153eb83d3c61e04d38f2ab96892a6feb5`.
- Validated five narrow Shopping secret provisioning capabilities with explicit
  `expected_uid` injection, no ambient UID/HOME authority, a fixed trusted
  Homebrew executable boundary, and no exposed generic shell/argv execution API.
- Validated no-overwrite/no-clobber behavior, fail-closed mutation uncertainty,
  and no automatic retry, rollback, or compensation. Python does not read the
  private control-plane age identity for recipient derivation; offline recovery
  remains public-recipient-metadata only; the value-free evidence contract is
  intact.
- Recorded focused `421 passed`; canonical `3387 passed, 5 deselected, 447
  warnings in 132.49s`, `RC=0`, canonical execution count exactly `1`; Git
  closeout PASS; upstream divergence `0 0`.
- Recorded `PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
  `SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
  `COLIMA_ACCESS=false`, and `NOTION_SYNC=false`.
- Actual SOPS/age installation, age identity creation, recipient registration,
  secret materialization, and runtime activation have not occurred. Historical
  MariaDB credential continuity remains explicitly unresolved.
  `SHOPPING_RUNTIME_ACTIVATED` remains the future Production milestone. Notion
  remains deferred until after Runtime Activation.
- Set the next engineering recommendation to `SM-01B-02D-03 — Durable
  Authorization Consumption & Evidence Store v1`: generic Governance-owned,
  Mac Control Plane only, replay-safe and durable, with no Shopping business
  logic.

## 2026-08-17 — SM-01B-02D-01B Shopping Provisioning Governance Coordinator v1

Closed implementation and validation at
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

Validation recorded focused `181 passed`; canonical `3349 passed, 5
deselected, 447 warnings`, `RC=0`, canonical execution count exactly `1`.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, `MATERIALIZATION_IMPLEMENTED=false`, and
`NOTION_SYNC=false`. Historical MariaDB credential
continuity remains unresolved; `SHOPPING_RUNTIME_ACTIVATED` remains the
Production milestone.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
worker. Core has no dependency on `ops.macos`, and no generic shell or argv
execution API exists. Next engineering milestone:
`SM-01B-02D-02 — Concrete Provisioning Capabilities v1`.

## 2026-08-17 — SM-01B-02C Bounded Mutation Adapters v1

- Closed implementation and validation at
  `SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED`, implementation commit
  `5a811cb1f9c782acb4f3e537596fb47ae0c599ff`.
- Implemented bounded mutation adapter code only for the exact
  `SHOPPING_SECRET_PROVISIONING` target and five exact actions:
  `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
  `SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
  `SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
  `SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`, and
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`.
- Reused SEC-02 `ControlledExecutionPort`. Each adapter accepts only the exact
  target/action and invokes at most one narrow injected capability. Adapters
  issue and consume no authorization; do not retry, rollback, or compensate;
  and emit value-free `GovernanceExecutionReceipt` evidence using a
  deterministic injective identity namespace over the full
  `execution_request_id`. No generic shell/argv/package-manager execution
  framework or parallel governance framework was added.
- Recorded focused `128 passed`; canonical `3288 passed, 5 deselected, 447
  warnings`, `RC=0`, executed exactly once on final implementation code. Exact
  three-file implementation scope, post-canonical scope, staged scope, staged
  diff check, commit, push, and upstream alignment `0 0` all passed.
- Preserved Mac AIControlCenter as sole Control Plane, Ubuntu as a stateless
  infrastructure worker with no Shopping secret ownership, and external
  offline-recovery private custody. Historical MariaDB credential continuity
  remains unresolved; SM-01B-02C does not recover, rotate, replace, derive,
  invent, or validate historical credentials.
- Preserved `production_status=NOT_DEPLOYED`;
  `materialization_implemented=false`; `SOPS_INSTALLATION=false`;
  `AGE_INSTALLATION=false`; `AGE_KEY_GENERATION=false`;
  `OFFLINE_RECOVERY_KEY_GENERATION=false`; `SECRET_PAYLOAD_CREATION=false`;
  `SECRET_MATERIALIZATION=false`; `AUTHORIZATION_CONSUMED=false`;
  `RUNTIME_INSPECTION=false`; `PRODUCTION_MUTATION=false`;
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- Set `SM-01B-02D — Authorized Toolchain & Identity Provisioning v1` as the
  next development milestone. Adapter implementation is not authorization to
  execute adapters. Each future Production mutation requires separate human
  authorization immediately before exactly one bounded invocation, with no
  automatic retry or rollback. SM-01B overall remains incomplete.

## 2026-08-17 — SM-01B-02B Provisioning Planner v1

- Closed implementation and validation at
  `SM_01B_02B_PROVISIONING_PLANNER_VALIDATED`, implementation commit
  `2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`.
- Established a canonical provisioning definition and Draft 2020-12 schema
  defining exactly five typed actions. Core `ProvisioningPlan` is
  vendor-neutral and value-free; malformed input emits only sanitized
  `UNKNOWN_ACTION`/`MALFORMED_CONFIGURATION` evidence. The read-only macOS
  provisioning inspector performs planning only. Core imports from `ops` and
  `integrations` remain zero.
- Required future execution to reuse SEC-02 `ControlledExecutionPort`; no
  parallel governance framework may be created. Adapter implementation is not
  authorization to execute an adapter.
- Recorded final implementation validation: focused `73 passed`; canonical
  `3236 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly once on
  final implementation code. Exact six-file implementation scope,
  post-canonical scope, staged scope, staged diff check, commit, push, and
  upstream alignment all passed.
- Preserved Mac AIControlCenter as sole Control Plane and Ubuntu as a stateless
  worker with no Shopping secret ownership. Offline-recovery custody remains
  external. Historical MariaDB credential continuity remains unresolved;
  SM-01B-02B did not recover, replace, rotate, or invent credentials.
- Production remains `NOT_DEPLOYED`; `materialization_implemented=false`;
  `SOPS_INSTALLATION=false`; `AGE_INSTALLATION=false`;
  `AGE_KEY_GENERATION=false`; `OFFLINE_RECOVERY_KEY_GENERATION=false`;
  `SECRET_PAYLOAD_CREATION=false`; `SECRET_MATERIALIZATION=false`;
  `AUTHORIZATION_CONSUMED=false`; `RUNTIME_INSPECTION=false`;
  `PRODUCTION_MUTATION=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
- Set `SM-01B-02C — Bounded Mutation Adapters v1` as the next development
  milestone. SM-01B overall remains incomplete.

## 2026-08-16 — SM-01B-01 SOPS/age Secret Backend Inspection v1

- Completed implementation and validation at milestone
  `SM_01B_01_SECRET_BACKEND_INSPECTION_VALIDATED`, implementation commit
  `1ada572a75cf4313f65288e81134777948900cda`.
- Selected SOPS+age as the replaceable Shopping secret-backend architecture,
  without claiming deployment. Added canonical definition/schema, a
  vendor-neutral core port, and a read-only macOS outer adapter; core imports
  from both `ops` and `integrations` remain zero.
- Kept the Mac as sole Control Plane and Ubuntu stateless with no secret
  ownership. Defined portable injected identity custody and metadata-only
  `lstat` inspection of the identity and encrypted-payload paths; no contents,
  recipient material, HOME/environment/pwd, Keychain, runtime, Docker, Colima,
  or network state are read or discovered.
- Preserved the two-recipient metadata policy (`control-plane` and
  `offline-recovery`) and aligned JSON Schema with runtime safety validation.
- Focused final validation passed `66 passed`. Canonical regression passed
  `3205 passed, 5 deselected, 447 warnings`, `RC=0`, exactly once on final
  implementation code. Exact six-file post-canonical scope, staged scope, and
  staged diff checks passed; implementation commit/push passed with upstream
  counts `0 0`.
- Production status remains `NOT_DEPLOYED`; SOPS installation, age
  installation, key generation, encrypted payload provisioning,
  materialization, Production mutation, runtime inspection, secret-value read,
  and Keychain query did not occur. `materialization_implemented=false` and
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- Historical MariaDB credential continuity remains unresolved; the new
  architecture neither recovers nor silently replaces historical credentials.
  Runtime cutover remains blocked on an explicit continuity/recovery/rotation
  strategy.
- Set `SM-01B-02 — SOPS/age Toolchain & Identity Provisioning` as the next
  milestone. SM-01B overall is not complete.

## 2026-08-16 — SM-01A Shopping secret contract and preflight validated

- Added the value-free canonical Shopping secret contract at
  `deploy/shopping/config/secret-contract.json` and made it the single metadata
  authority; Python does not duplicate the exact canonical key table.
- Added the read-only, structurally fail-closed preflight with action-specific
  `runtime_cutover` and `bootstrap` required-key resolution, presence-only
  evaluation, distinct not-evaluated state, and fail-closed handling for
  unsupported actions, unknown supplied key names, missing names, and invalid
  contract structure.
- Preserved secret-independent read-only monitoring and plain
  `${SHOPPING_*}` Compose interpolation. No secret value was read, inspected,
  serialized, or materialized.
- Recorded that no Secret Backend or Secret Materialization exists; no
  SOPS/age/Keychain backend is implemented or selected as deployed truth.
- Focused final validation passed `111 passed, 9 warnings`. Canonical regression
  passed `3179 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly
  once on final code. Implementation commit:
  `ffdf034ed9e1587328b6ecad35a6fcbe1381d8b0`.
- Performed no Production mutation or port cutover, consumed no new Production
  authorization, queried no Keychain, and performed no Notion synchronization.
  Shopping service and WooCommerce capability remain `NOT_DEPLOYED`;
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- Set the next development milestone to
  `SM-01B — Secret Delivery Backend v1`.

## 2026-08-15 — PA-04 Notification Platform v1

- Validated PA-04 and marked it closed after Git closeout at milestone
  `NOTIFICATION_PLATFORM_V1_VALIDATED`.
- Established AIControlCenter ownership of notification intent, routing policy,
  provider selection, governance, authorization, audit, retry policy, and the
  future delivery lifecycle. Providers own transport only; n8n, OpenClaw,
  WordPress, providers, and Ubuntu own no platform-wide notification business
  logic or Production authorization.
- Established `core.notifications` as the provider-neutral boundary,
  `integrations.notifications` as replaceable observation-only adapters, and
  `ops.macos.runtime.application` as outer composition. Core import counts for
  both `ops.*` and `integrations.*` are zero.
- Separated provider status from routing status and defined no delivery
  lifecycle because execution is not implemented. Hardened normalization so
  only explicitly available/configured/available providers route; all malformed,
  contradictory, exceptional, mismatched, duplicate, or invalid observations
  fail closed. Invalid bounded identities are never echoed and become
  `UNKNOWN`.
- Recorded Telegram as the optional, `NOT_DEPLOYED` reference provider without
  inferring configuration, readiness, environment, credentials, endpoints,
  hosts, ports, authentication, or networking.
- Consolidated narrow canonical service metadata lookup in
  `core.capabilities.manifest`, including schema self-validation, manifest
  validation, unique requested identity, and fail-closed input handling.
  OpenClaw/n8n outward behavior remains unchanged; no second topology or
  lifecycle framework was created.
- Added exactly `GET /api/notifications/platform` and
  `GET /api/notifications/providers`, with no PA-04 action or execution route.
  Preserved existing GET/POST `/notifications` as **LEGACY / OUTSIDE PA-04
  SCOPE** without calling, wrapping, authorizing, expanding, or depending on it.
- Recorded 85 passing exact-code focused tests after provider identity
  hardening, canonical regression `RC=0` on exactly one PA-04 invocation, and
  passing `git diff --check`. No Production mutation, Production notification,
  external provider I/O, or PA-04 execution occurred. Legacy POST ran only in
  TestClient compatibility tests. No launchd, Docker, `runtime/current`,
  credential, Caddy, WordPress, Ubuntu, or live-provider mutation occurred. No
  Notion synchronization is claimed. OPS-01B and PA-01 through PA-03 remain
  closed and unchanged.

## 2026-08-14 — PA-03 n8n Control Plane Adapter v1

- Validated PA-03 and marked it closed after Git closeout at milestone
  `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`.
- Established n8n as a replaceable external automation capability, not the
  AIControlCenter Control Plane. AIControlCenter retains business logic,
  workflow and orchestration policy, Production authorization, governance,
  audit, deployment control, infrastructure mutation authority, and
  business/customer state.
- Established dependency direction `ops.macos.runtime.application` →
  `integrations.n8n` → `core.capabilities`, with injection into
  `core.api.create_app`; core imports neither `ops.*` nor `integrations.*`.
  Reused existing `core.capabilities` contracts and `CapabilityStatusService`
  rather than creating a second capability framework.
- Added only `GET /api/capabilities/n8n`. No POST/PUT/PATCH/DELETE capability
  implementation, workflow execution or enable/disable, webhook or credential
  creation, schedule mutation, Production authorization, or infrastructure
  mutation exists.
- Validated the canonical manifest/schema before trusting the unique optional
  n8n identity. Current truth is `NOT_DEPLOYED`, `runtime_health=false`,
  `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`. No sufficiently proven
  executable/lifecycle/log/runtime identity exists, so no PA-01
  `service_platform` lifecycle definition was added.
- Kept configuration, authentication, runtime, and transport `UNKNOWN` unless
  explicitly injected as evidence. Platform-neutral `create_app` performs no
  discovery and fails closed with value-free `UNAVAILABLE` evidence; macOS
  composition injects the adapter and projects `NOT_DEPLOYED`. No invented n8n
  endpoint, environment, or authentication convention is used.
- Kept secret/config evidence value-free: URLs, API keys, tokens, cookies,
  headers, webhook secrets, environment values, configuration contents, and
  exception messages are not projected. Shared governance now explicitly
  reports `platform_business_policy_ownership=false` for external capabilities;
  PA-02 OpenClaw remains compatible.
- Recorded focused PA-03 validation of 96 passed tests and canonical deployment
  regression `RC=0` on exactly one PA-03 canonical invocation. `git diff
  --check` passed. No Production mutation or n8n workflow, credential, Docker,
  launchd, `runtime/current`, or live-service operation occurred. No Notion
  synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
  unchanged.

## 2026-08-14 — PA-02 OpenClaw Adapter v1

- Validated PA-02 and marked it closed after Git closeout at milestone
  `OPENCLAW_ADAPTER_V1_VALIDATED`.
- Added a replaceable outer OpenClaw adapter with final dependency direction
  `ops.macos.runtime.application` → `integrations.openclaw` →
  `core.capabilities`, injected into `core.api.create_app`; core imports neither
  `ops.*` nor `integrations.*`.
- Added only `GET /api/capabilities/openclaw`. No POST/PUT/PATCH/DELETE
  capability implementation, prompt forwarding, tool/action execution,
  lifecycle execution, Production authorization, or infrastructure mutation
  exists.
- Reused the canonical optional `NOT_DEPLOYED` manifest identity without adding
  an unproven launchd/runtime/Service Platform lifecycle definition and retained
  `runtime_health=false`. The manifest is schema-validated before its unique
  OpenClaw entry is trusted.
- Kept endpoint, authentication, transport, and runtime identity
  `UNKNOWN`/unproven by default. Platform-neutral `create_app` performs no
  discovery and fails closed with value-free `UNAVAILABLE` evidence; macOS
  composition injects the adapter and projects `NOT_DEPLOYED`. No
  `OPENCLAW_ENDPOINT` or `OPENCLAW_API_KEY` convention is used.
- Kept secret/config evidence value-free: no endpoint URL, key, token, cookie,
  header, environment value, credential value, or exception message is
  projected.
- Preserved AIControlCenter authority over business logic, Production
  authorization, governance, deployment control, workflow policy,
  infrastructure mutation, audit, and business/customer state.
- Recorded focused PA-02 validation of 79 passed tests and canonical deployment
  regression `RC=0` on exactly one PA-02 canonical invocation. No Production
  mutation or additional deployment, `launchctl`, `runtime/current`,
  credential, or live-service operation occurred. No Notion synchronization is
  claimed. PA-01 and OPS-01B remain closed and unchanged; WordPress and
  unrelated Shadow maintenance remain separate future work.

## 2026-08-14 — PA-01 Control Plane Service Platform v1

- Closed PA-01 after Git closeout at milestone
  `CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`.
- Introduced Control Plane Service Platform v1. The canonical service manifest
  is the service-definition source of truth; `ServiceDefinition` is a pure core
  service-level contract; `ServiceHealth` remains sole owner of aggregate
  runtime health; and `core` has zero direct `ops.*` imports.
- Added macOS outer composition in `ops/macos/runtime/service_platform.py`.
  `inspect_platform_services()` composes `ServiceTopology.platform_services()`,
  existing `ServiceHealth` launchd/heartbeat observation, strict filesystem
  readiness, and immutable runtime/source validation.
- Kept stable owner/group names resolved only at the macOS boundary. Exact file
  type, symlink, mode, owner, and group validation remains fail-closed. Only
  `ENOENT` is missing; other filesystem/identity inspection errors fail closed
  with value-free evidence.
- Reused the authoritative immutable-source validator for canonical immutable
  `runtime/current` and Source validation without executing Production worktree
  code.
- Kept lifecycle inspect-only. Dry-run bootstrap planning metadata requires
  `NOT_DEPLOYED`, trusted launchd observation, ready filesystem, and immutable
  runtime/source preconditions. It carries no authorization and performs no
  mutation, retry, rollback, or kickstart.
- Used Application Scheduler and canonical API as reference services without
  changing their validated Production lifecycle behavior. The canonical API
  entrypoint remains `ops.macos.runtime.application:app`; Shadow remains
  separate.
- Final focused validation passed 94 tests under umask `077`. The final PA-01
  candidate passed exactly one canonical deployment-regression invocation with
  `RC=0`. `git diff --check` passed. No Production mutation occurred.
- No Notion synchronization is claimed. WordPress and Shadow maintenance
  remains deferred and separate.

## 2026-08-14 — OPS-01B Scheduler log recurrence prevention

- Added a JSON-first, fail-closed readiness contract for the Application
  Scheduler launchd stdout/stderr files and their root-owned parent directory.
- Added a provisioning primitive bounded to creating only missing
  `kyouhan:staff 0640` Scheduler log files. Its local checks are executor
  preconditions, not human authorization; the outer governed executor retains
  the human authorization boundary. Invalid existing files are never repaired
  automatically.
- Integrated the contract into the existing runtime `ServiceHealth`
  observation/readiness projection through application composition, leaving
  `core.runtime` adapter-injected and free of direct `ops.*` dependencies.
- Added `ops.macos.runtime.application:app` as the outer macOS Production API
  composition root and changed the immutable canonical runner to launch it;
  `core.api.app` remains the platform-neutral factory with a fail-closed
  default when no Scheduler log adapter is supplied.
- Made `application_scheduler_bootstrap.py` the canonical Scheduler deployment
  lifecycle gate. Dry-run and apply share log-contract and registration-probe
  eligibility checks; only apply may execute one bootstrap after those gates.
- Kept Scheduler log provisioning separate from bootstrap/kickstart; the
  provisioning primitive has no retry or rollback path, does not modify
  Scheduler business logic, and does not invoke lifecycle operations.
- Application Scheduler Production recovery was already operational before
  recurrence-prevention closeout; this validation performed no Production
  mutation and no additional activation, bootstrap, log provisioning,
  kickstart, retry, or rollback.
- Focused recurrence validation passed. Canonical deployment regression
  invocation #1 failed with 13 test failures caused by umask-sensitive
  Scheduler fixtures and a controlled-live test that hashed the independently
  mutable real-home AIControlCenter tree.
- Corrected only those test defects without weakening Product contracts. The
  corrected focused scope passed 39 tests under umask `077`, with the
  controlled live root explicitly confined to `/private/tmp`.
- Canonical deployment regression invocation #2 passed with `RC=0`. The
  closeout used exactly two canonical invocations because code/test changes
  occurred after invocation #1; no canonical test count is claimed for #2.
- Marked `OPS-01B_RECURRENCE_PREVENTION_VALIDATED_AND_CLOSED`; OPS-01B is
  closed. Deferred WordPress and Shadow work remains separate future work.

## 2026-08-13 — Bytecode-safe canonical API recovery

- Released Runtime and immutable Source `ef07532bd3d7` from commit
  `ef07532bd3d7ba91868d46375d48cac4821d6a56`; focused tests passed `49`, and
  the canonical regression passed `2954 passed, 5 deselected, 439 warnings`.
- Prevented privileged canonical refresh/bootstrap executors from generating
  project-local bytecode by setting `sys.dont_write_bytecode = True` before
  sibling imports, with regression coverage that removes external bytecode
  protection variables.
- Retired rather than repaired contaminated release `9a7216a75323`. The new
  Source passed independent identity, content, archive, Git-tree,
  immutability, and bytecode-contamination validation.
- Activated `runtime/current` once, reconciled shadow once, and performed one
  separately human-authorized canonical kickstart. Canonical and shadow now
  serve from the matching immutable Source with `GET /health = 200` and
  `POST /health = 405`; public HTTPS health and Homepage validation passed.
- A duplicate recovery request failed closed at preflight before authorization
  or mutation because canonical was already running. No second bootstrap,
  second kickstart, automatic retry, automatic rollback, ProductDraft or
  WooCommerce mutation, Ubuntu change, or in-place Source repair occurred.
- Whole-runtime health remains degraded: `/runtime/health` returns HTTP `200`
  with `healthy=false`, unavailable API/Telegram/scheduler service entries,
  and a stale scheduler heartbeat. Runtime-health reconciliation remains open.

## 2026-08-11 — SHOP-AI-01A documentation closeout

- Closed `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified
  implementation HEAD `52db3600ae76c70926e27ce930be70fe34f98452` and recorded
  the verified canonical regression `2691 passed, 5 deselected, 437 warnings`.
- Documented reuse of canonical `core/shopping/`, SHOP-02 `ProductDraft`,
  existing `ProposedFields`, immutable revisions, and canonical
  `core.providers.ProviderAdapter` under structured contract `1.0.0`.
- Documented the AI provenance-bearing `DRAFT` candidate, snapshotted source
  context, traceable provider request ID, one injected provider, bounded
  timeout, `RetryPolicy(max_attempts=1)`, and no fallback.
- Documented at-most-one provider invocation per consumed operation key within
  the injected coordinator's durability scope and concurrent duplicate
  suppression. The in-memory coordinator remains non-production; no global
  exactly-once guarantee is claimed.
- Added no runtime or test changes. Durable persistence/ledger/transaction,
  generation API or Dashboard mutation, recommendations, Commerce writes,
  Production mutation authority, automatic retry, and rollback remain absent.
- Next: `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`; separate
  future stream: `SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE`.

## 2026-08-11 — SHOP-01A closeout

- Closed SHOP-01A1 runtime reconciliation and SHOP-01A2
  repository/architecture reconciliation without restarting or replacing the
  existing SHOP-01/02/03 architecture.
- Recorded the canonical regression `2670 passed, 5 deselected, 437 warnings`
  from `ops/macos/validation/run-deployment-regression-gate.sh -q`.
- Production mutation remains disabled; no automatic retry or rollback was
  enabled.
- Final milestone: `SHOP-01A_SHOPPING_READ_ONLY_FOUNDATION_READY`.

## 2026-08-11 — SHOP-01A2 repository and architecture reconciliation

- Added the canonical repository-utilization classification without marking
  any component deprecated or removable.
- Reconciled SHOP-01A as retrospective baseline hardening over existing
  SHOP-01/02/03 history; `core/shopping/` remains the canonical domain.
- Recorded SHOP-01A1 HEAD
  `f95ba9ae2133b55db06c362df321b16785f21423` and canonical wrapper result
  `2670 passed, 5 deselected, 437 warnings` from
  `ops/macos/validation/run-deployment-regression-gate.sh -q`.
- Recorded GET-only Shopping runtime, one outbound GET attempt per invocation,
  disabled automatic read retry, and disabled Production mutation authority.
- Retained the intercepted SHOP-03 adapter as active library code while
  recording the absence of a Production write transport, Production credential
  provider, runtime/API wiring, and mutation endpoint.
- Added a `READY_FOR_FINAL_SYNC` payload; no external synchronization occurred.
- Next: `SHOP-01A3_CLOSEOUT_AND_FINAL_SYNC`.

## 2026-08-10 — SEC-02A architecture closure

- Closed the complete A0-A10 SEC-02A architecture phase at
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`; the A1-A9 canonical
  evidence chain is `VALIDATED`.
- Recorded the terminal authorization lifecycle, exact current-precondition
  match, separate consumption and invocation boundaries, one bounded
  invocation per permission, accounting-only remaining budget, and mandatory
  `STOP` behavior.
- Reaffirmed no automatic retry or rollback; adapter non-authority; READ ONLY
  Governance projection; external Mac Control Plane durable evidence;
  transient-only `/private/tmp`; canonical repository audit JSON; and mandatory
  value-free evidence.
- Reaffirmed AIControlCenter ownership of platform and Shopping business logic,
  WordPress/WooCommerce engine roles, and Ubuntu's stateless zero-authority
  Worker role. No concrete Production mutation adapter was implemented.
- Canonical full repository regression supplied for closure:
  `========= 2667 passed, 5 deselected, 437 warnings in 166.69s (0:02:46) =========`.
  Prior focused Governance regression: `265 passed in 1.45s`. Tests were not
  rerun during this documentation-only closeout.
- Git closeout is assigned to the external controller. Notion external
  synchronization has not been performed; payload status is
  `READY_FOR_FINAL_SYNC`.
- Next: `SHOP-01A_SHOPPING_PLATFORM_ARCHITECTURE_AND_READ_ONLY_FOUNDATION`.
  Production commerce writes remain separately governed and require explicit
  future authorization.

## 2026-08-10 — SEC-02A9 durable evidence and API projection validated

- Added pure immutable, caller-classified durable-storage policy with stable
  accept/reject reasons and value-free evidence enforcement.
- Added an immutable typed Governance read model and deterministic projection
  to the unchanged A6 `GovernanceApiEnvelope`; caller supplies projection time
  and safe digest/reference identities.
- Froze external operator-configured Control Plane data as durable storage,
  `/private/tmp` as transient only, and repository evidence JSON as canonical
  documentation/audit evidence rather than mutable runtime state.
- Required atomic write publication, restrictive permissions, durable
  synchronization, manifest binding, and value-free evidence; application
  source hard-codes no user-specific absolute data root.
- External validation reported `265 passed in 1.45s` for the focused Governance
  regression, validating the durable evidence policy, deterministic READ ONLY
  projection, and unchanged `GovernanceApiEnvelope` compatibility. This was
  not the full repository regression. Milestone:
  `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`.
- The projection cannot authorize, consume authorization, execute, retry, roll
  back, or persist. Added no concrete persistence adapter, writer, HTTP mutation
  route, Production mutation API, external access, or Production/provider/Ubuntu
  mutation.
  Next: `SEC-02A10 ARCHITECTURE CLOSURE REVIEW`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; architecture-ready is not claimed before A10.

## 2026-08-10 — SEC-02A8 orchestration policy and safety tests validated

- Added a pure immutable application context and deterministic decision model
  with the five frozen A8 dispositions. Decisions grant no external action and
  always prohibit automatic retry and rollback.
- Added fail-closed priority gates for failure evidence, exact lifecycle and
  receipt bindings, authorization state, current preconditions, consumption
  evidence, mutation budgets, execution outcomes, and postconditions.
- Kept authorization consumption as a distinct gate. Current preconditions
  must `MATCH` before invocation permission; consumed authorization remains
  consumed after later drift. One permission corresponds to one bounded
  invocation.
- Froze `FAILED -> STOP`, `UNCERTAIN -> STOP`, postcondition `FAIL -> STOP`,
  and failure evidence `-> STOP`. Remaining mutation count is accounting, not
  retry authority. There is no automatic retry, automatic rollback, or
  compensation authority; postcondition `PASS` permits closeout only.
- External validation reported the focused Governance result `231 passed in
  1.42s`, reaching
  `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a
  full repository regression.
- Added no port/adapter invocation, Production/Runtime/provider/Ubuntu access,
  persistence, filesystem, subprocess, network, SQLite, Git command,
  environment, secret, clock, public mutation API, retry, rollback, or
  compensation authority. Next: `SEC-02A9 DURABLE EVIDENCE AND API
  PROJECTION`. Notion
  remains `DEFERRED_UNTIL_FINAL_PHASE`; no
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## 2026-08-10 — SEC-02A7 adapter ports and compatibility mappings validated

- Added seven abstract Governance-owned typed port capabilities covering
  observations, audit/evidence persistence, one bounded controlled invocation,
  and postcondition validation. A2-A5 models remain the primary boundaries.
- Added an immutable deterministic compatibility catalog for deployment
  preflight, read-only Git evidence, Runtime identity, deployment audit,
  governance operations, bootstrap execution/evidence recovery, and Shopping.
- External validation initially reported `1 failed, 193 passed in 1.56s`. R1
  fixed the Protocol-only interface gate and classified the issue as
  `PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT`: test-inspection semantics,
  not implementation `__init__` semantics. The final focused Governance
  regression reported `194 passed in 1.53s`, validating
  `SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`; this was not a
  full repository regression.
- Added no concrete adapter, orchestration, persistence implementation,
  Production/Runtime/Ubuntu/provider access, public mutation API, retry, or
  rollback. The abstract Governance ports cannot authorize, widen scope or
  mutation budget, or decide retry or rollback. Git evidence is read-only,
  Runtime identity is observation-only, Governance Operations remains an
  operational audit/read-model, Shopping rules remain Shopping-owned, and
  Ubuntu has zero Governance authority. Next:
  `SEC-02A8 ORCHESTRATION POLICY AND SAFETY TESTS`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; no
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.

## 2026-08-10 — SEC-02A6 JSON Schema registry and contract tests

- Implemented exactly 16 standalone governance v1 JSON Schema Draft 2020-12
  resources aligned with the A2-A5 immutable projections and frozen A1 names.
- Added a deterministic local-only, read-only-copy registry with stable URN
  identifiers, exact name/resource bindings, and fail-closed unknown lookup.
- Added one synthetic valid and invalid fixture per contract and focused
  registry, schema, fixture, frozen-enum, forbidden-field, and projection-shape
  contract tests. External focused governance regression validated the
  registry and valid/invalid fixture contracts: `173 passed in 1.39s`, reaching
  `SEC-02A6_JSON_SCHEMA_REGISTRY_AND_CONTRACT_TESTS_VALIDATED`. This was not a
  full repository regression.
- Classified the prior blocker as
  `SEC-02A6-R1_CONTROLLER_REGISTRY_API_ASSUMPTION_DEFECT`: the controller
  assumed a public `registry.contract_names()` function even though the frozen
  contract required behavior, not that exact API name. It was not an A6
  contract implementation defect.
- Added no Production/Runtime access, execution adapter, provider or Ubuntu
  mutation, mutation API, retry, rollback, Git mutation, or authorization
  behavior.
- Next: `SEC-02A7 ADAPTER PORTS AND COMPATIBILITY MAPPINGS`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; no architecture-ready claim is made.

## 2026-08-10 — SEC-02A5 receipts, failure, and evidence models

- Added pure immutable authorization-consumption, execution-request,
  execution-receipt, postcondition, and failure-evidence models. They record
  caller-supplied facts only and grant no execution, retry, rollback, or new
  authorization authority.
- Added typed value-free artifact references, deterministic evidence manifests
  and lifecycle-bound evidence bundles with fail-closed duplicate and binding
  validation. No contents, paths, secrets, hashes, times, or identities are
  collected or generated.
- Added the three focused A5 test modules but did not run tests. Therefore
  `SEC-02A5_RECEIPTS_FAILURE_AND_EVIDENCE_MODELS_VALIDATED` remains the target
  milestone pending controller validation.
- This is pure domain evidence vocabulary only. It adds no adapter,
  orchestration, persistence, audit storage, public mutation API, Production,
  Runtime, provider, Ubuntu, filesystem, subprocess, network, SQLite,
  environment, secret, clock, ID, or digest capability.
- Next: `SEC-02A6 JSON SCHEMA REGISTRY AND CONTRACT TESTS`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; no SEC-02A architecture-ready claim is made.

## 2026-08-10 — SEC-02A4 mutation budget and invocation accounting

- Added pure immutable mutation-budget and explicit per-capability line-item
  models with the frozen `AVAILABLE`, `CONSUMED`, `EXHAUSTED`, and `VIOLATED`
  statuses, deterministic ordering, exact accounting, and JSON-safe projection.
- Kept irreversible authorization consumption separate from adapter invocation
  accounting. Completed, confirmed-zero-effect, and uncertain outcomes each
  account exactly one crossed boundary without granting retry or rollback.
- Added typed fail-closed A4 failures, composite-workflow isolation, explicit
  terminal safety-incident transition, and three focused test modules. Codex
  did not run tests, so
  `SEC-02A4_MUTATION_BUDGET_AND_INVOCATION_ACCOUNTING_VALIDATED` remains the
  target milestone pending external validation.
- This is pure domain work only. It adds no adapter, orchestration, persistence,
  evidence storage, public mutation API, Production, Runtime, provider, Ubuntu,
  filesystem, subprocess, network, SQLite, environment, secret, clock, ID, or
  digest capability.
- Next: `SEC-02A5 RECEIPTS FAILURE AND EVIDENCE MODELS`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; no SEC-02A architecture-ready claim is made.

## 2026-08-10 — SEC-02A3 precondition snapshot and stale semantics

- Added pure immutable governance precondition snapshots, named binding records,
  deterministic normalization/projection, and fail-closed duplicate-name
  validation. All identities, timestamps, observations, and digests remain
  caller supplied.
- Added exact authorization-bound comparison with frozen `MATCH`/`DRIFT`
  statuses and ordered category-specific reason codes. Recollection metadata
  does not cause drift; lifecycle, request, target, Git, Runtime, security,
  manifest, operational, policy, and canonical digest changes do.
- Integrated pure receipt/snapshot binding validation, drift-to-`STALE`, and
  caller-time expiry-to-`STALE` with the existing A2 transition API. Match does
  not refresh or replace authority, and the exact expiry boundary remains
  authorized.
- Added the two focused A3 test modules but did not run them. Therefore
  `SEC-02A3_PRECONDITION_SNAPSHOT_AND_STALE_SEMANTICS_VALIDATED` is the target
  milestone pending external focused-test success.
- Added no collectors, adapters, persistence, mutation accounting, Production,
  Runtime, provider, Ubuntu, network, filesystem, subprocess, environment,
  secret, internal clock, random ID, or digest-generation capability.
- Next: `SEC-02A4 MUTATION BUDGET AND INVOCATION ACCOUNTING`. Notion remains
  `DEFERRED_UNTIL_FINAL_PHASE`; no SEC-02A architecture-ready claim is made.

## 2026-08-10 — SEC-02A2 authorization domain models

- Added pure, immutable authorization request, decision, receipt, state-record,
  identity, failure, aggregate, and transition models under the Control Plane
  domain boundary.
- Encoded exactly the five frozen states and four allowed transitions, including
  terminal reuse denial, exact identity/budget/snapshot bindings, non-widening
  scope, and deterministic JSON-safe projections.
- Added focused pure tests, but Codex did not run them. Therefore
  `SEC-02A2_AUTHORIZATION_DOMAIN_MODELS_VALIDATED` remains the A2 target pending
  external test execution.
- Added no adapters, persistence, mutation accounting, precondition comparison,
  retry, rollback, public API, network, filesystem, Git subprocess, Production,
  provider, Runtime, or Ubuntu capability.
- Next: `SEC-02A3 PRECONDITION SNAPSHOT AND STALE SEMANTICS`.

## 2026-08-10 — SEC-02A1 governance domain and JSON contract freeze

- Froze the `core/governance/control_plane/` domain, application, adapter, and
  contract ownership boundary without adding implementation.
- Defined the exact authorization lifecycle, mutation-budget accounting,
  irreversible consumption boundary, execution order, durable evidence model,
  adapter safety rules, and five-layer test architecture.
- Cataloged the 16 SEC-02 v1 JSON contract names and major semantic field
  families. No JSON Schema files were created.
- Preserved mature DPL, governance-operations, shopping, audit SQLite, permit
  replay, Git evidence, runtime identity, and evidence ownership behind
  governance ports/adapters.
- Added operator policy requiring stop-without-retry-or-rollback after
  consumption and new authorization after any terminal lifecycle.
- No Production capability, Production access, Runtime access, provider access,
  Ubuntu access, source code, tests, scripts, configuration, or launchd change
  was added or performed.
- Status: `SEC_02A1_FINAL_STATUS=GOVERNANCE_DOMAIN_AND_JSON_CONTRACT_FROZEN`.
  Next: `SEC-02A2 AUTHORIZATION DOMAIN MODELS`.

## 2026-08-10 — SEC-01 production provider-secret lifecycle closeout

- Closed SEC-01 at `PRODUCTION_SECRET_LIFECYCLE_VALIDATED` on governance
  baseline `68a107432ceabf8527f0071db6b0bb7cd2bec71b`, Production Runtime
  `102b8f1fa862`, and matching immutable source.
- Validated persistent daemon delivery, restart recovery, reboot recovery
  (`VALIDATED_WITH_EVIDENCE_RECOVERY`), and isolated missing-secret fail-closed
  behavior (`PROVIDER_SECRET_MISSING_FAIL_CLOSED_VALIDATED`) through the
  installed helper's supported `--secret-root` seam.
- Validated exactly one canonical atomic storage replacement
  (`PROVIDER_SECRET_STORAGE_ROTATION_VALIDATED`) and exactly one authorized E3
  restart (`PROVIDER_SECRET_DAEMON_DELIVERY_ROTATION_VALIDATED`).
- Validated provider administration
  (`PROVIDER_SECRET_PROVIDER_LIFECYCLE_VALIDATED`) with previous credential
  revocation/deletion recorded as operator-attested. Provider admin revocation
  was not machine verified, authenticated provider validation was not performed,
  and credential identity was not proven locally. No secret value or credential
  identifier is documented.
- Validated candidate cleanup
  (`PROVIDER_SECRET_CANDIDATE_CLEANUP_VALIDATED`), removed the candidate `.next`
  file, and confirmed Production healthy after E5.
- Corrected the final quality gate without erasing the initial attempt. SEC-01
  FINAL R1 invoked raw pytest and reported 2 failed, 2338 passed, 5 deselected,
  and 62 errors. Because it bypassed the canonical deployment harness and its
  isolated test-root variables, it is classified
  `INVALID_RAW_PYTEST_GATE_INVOCATION`; it demonstrated neither an application
  regression nor a documentation-caused failure. FINAL R2 was
  `DIAGNOSED_READ_ONLY`, with no repository or Production mutation.
- Ran the canonical harness contract in FINAL R3 and R4. R3 passed 3/3
  representative selections (17 tests), led by
  `tests/deployment/test_m3_a4b2b2b_r1_existing_safe_parent.py`. Authoritative
  FINAL R4 used `ops/macos/validation/run-deployment-regression-gate.sh`, not
  raw pytest, and reported 2402 passed, 5 deselected, and 437 warnings. Warnings
  are not failures. Tests did not modify the repository; Production PID was
  unchanged, canonical secret metadata was preserved, the candidate was absent,
  and Production mutation was zero.
- Preserved fail-closed routing, no silent fallback, no business-logic
  secret-file reads, no `launchctl setenv` persistence, no plaintext plist
  secrets, explicit human authorization for Production mutation, and no
  automatic rollback after controlled mutation failure.
- Retained `SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`: D-B ran
  the restart workflow twice under an exactly-one authorization. It was not
  retroactively authorized or erased, although Production remained healthy.
- Retained `SEC-01D-C3-BOOT-PARSER-DEFECT`: greedy `usec` parsing made the
  original reboot authorization `STALE_UNCONSUMED`; C3-R1 corrected the parser
  before the authorized reboot.
- Retained `SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`: `/private/tmp` evidence was
  lost; C5-R2 used transcript-bound recovery. Exact reboot count was not
  machine-verifiable, the operator attested one reboot, boot epoch proved a
  reboot boundary, and lost C3/C4 files were not restored. Future evidence uses
  the durable Control Plane evidence root.
- Advanced to `SEC-02_CONTROL_PLANE_GOVERNANCE_AUTOMATION`; only SEC-01, not the
  wider AI Home Datacenter project, is complete.

## 2026-08-10 — AI-PROVIDER-01C-A Control Plane Workflow Integration

- Integrated canonical `BrainAgent.ask` calls with `ProviderRouter` and the
  normalized `ProviderAdapter` request/result/error boundary.
- Preserved request/config provider selection, action routing and injected
  legacy manager compatibility while prohibiting unknown-provider fallback.
- Added FakeProvider integration coverage for JSON-safe results, audit metadata,
  normalized failures and rejection of vendor response objects.
- No authenticated request or Runtime operation occurred. Production Runtime
  remains `7b171f135dc7`; 01C-B creates a Candidate Runtime and 01C-C requires
  explicit human promotion authorization. Notion is
  `DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — AI-PROVIDER-01B Authenticated OpenAI Provider Transport

- Implemented the OpenAI Responses API POST transport behind `OpenAIAdapter`
  using invocation-time `OPENAI_API_KEY` lookup and standard-library HTTP.
- Added bounded timeout/output, one-request/no-retry enforcement, normalized
  response identity and usage, sanitized failure mapping, and a JSON-only
  operational smoke command.
- Added focused mocked tests; no credential was read and no provider network
  request occurred. The external authenticated smoke remains pending.
- Production Runtime `7b171f135dc7` remains untouched. AI-PROVIDER-01C owns
  candidate Runtime integration/promotion. Notion is
  `DEFERRED_UNTIL_FINAL_PHASE`.

## 2026-08-10 — AI-PROVIDER-01A Provider Architecture and Adapter Contract

- Added normalized provider identities, request/response models, bounded timeout
  and retry policies, audit-safe errors, strict routing, a deterministic fake
  adapter and a network-free OpenAI adapter boundary.
- Removed automatic cross-provider fallback from the legacy provider manager.
- Added focused provider safety and serialization tests plus canonical
  architecture documentation.
- No credentials were installed or read, no authenticated provider call was
  made, and Production Runtime `7b171f135dc7` and PI-009 authorization remain
  unchanged. AI-PROVIDER-01B is not started. Notion sync is `PENDING`.

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
## 2026-08-06 — ACTIVATION-01B-C1 Complete

Added activation inspection policy, route-manifest and report
Schemas, canonical registry resources, synthetic fixtures,
digest-binding tests, secret-field rejection and pure validation
coverage.

Test evidence:

- Focused contract gate: `41 passed`
- Safe deployment regression: `1017 passed`
- Deprecation warnings: `9`
- Operational harness suites: `DEFERRED`

Architecture base commit:

`dc482780fdd36ba50d4947e8193380d7426d8367`

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:START -->
## 2026-08-05 — ACTIVATION-01B Architecture Freeze

### Added

- Read-only Activation Inspector architecture
- Read-only macOS inspector runbook
- Versioned policy and route-manifest design
- Canonical JSON evidence-report design
- Exact launchd and localhost boundaries
- Isolated Runtime Python version-probe contract
- Exact zero-body `POST /health` method-denial contract

### Reused

- Existing canonical JSON and SHA-256 contracts
- Existing JSON Schema Draft 2020-12 registry
- Existing bounded Git read-only evidence capability
- Existing macOS read-only adapter patterns

### Safety

- Architecture predecessor commit:
  `43975f6e26986fd91c9a715786e7c68deb63f612`
- Runtime mutations: `0`
- Service restarts: `0`
- Ubuntu changes: `0`
- Production remains `NOT_AUTHORIZED`
<!-- AICONTROLCENTER:ACTIVATION_01B_ARCHITECTURE:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## 2026-08-05 — ACTIVATION-01A

### Added

- Atomic Runtime activation contract
- Exact LaunchDaemon restart contract
- Direct-localhost post-activation validation contract
- Fail-closed activation failure conditions
- Separate rollback authorization boundary
- Canonical activation evidence requirements
- Repository `PYTHONPATH` coupling limitation

### Bound

- Source/build baseline:
  `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`
- Runtime build and smoke documentation commit:
  `180d874bcbd17f74e6b816223fe3527f36332ecf`
- Candidate Runtime: `acd80ab9f6ae`
- Active Runtime: `b9ad351a7241`
- Canonical serving target: `core.api.shadow:app`
- LaunchDaemon: `system/com.aicontrolcenter.api.shadow`

### Safety

- `runtime/current` unchanged
- Service restart count: zero
- Rollback execution count: zero
- launchd and Caddy changes: zero
- Ubuntu changes: zero
- Public opening count: zero
- Production remains `NOT_AUTHORIZED`

### Closure

- Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`
- Local and remote branch synchronization: `PASS`
- ACTIVATION-01A status: `COMPLETE`
- Production remains `NOT_AUTHORIZED`
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

## 2026-08-05 — RUNTIME-BUILD-04A build and direct shadow smoke

- Built and validated side-by-side release `acd80ab9f6ae` from
  source/documentation commit `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`.
  Dependency installation, application import, the Full Suite, source marker,
  and metadata validation passed. FastAPI was `0.139.0`, Uvicorn was `0.51.0`,
  and `jsonschema` was available.
- Direct localhost smoke used canonical target `core.api.shadow:app`, whose
  `ReadOnlyASGI` application composes internal FastAPI target
  `core.api.app:app`. GET returned 200 for `/health`, `/runtime/health`,
  `/homepage/status`, `/homepage`, `/homepage/product-management`, and
  `/datacenter/status`; `POST /health` returned 405. Exact smoke PID and
  listener cleanup passed.
- The builder produced valid structured JSON on stdout. The host wrapper found
  no canonical build-report JSON file, so the report was recovered and
  validated from the builder log. This is operational tooling debt, not a
  release failure. An optional host `rg` command was unavailable and was not a
  release defect.
- Python and dependencies are release-owned, but application source is loaded
  from the mutable repository through `PYTHONPATH`:
  `source_bundled_inside_release=false` and
  `repository_source_binding=true`. This is not yet a fully source-immutable
  application release.
- Existing active Runtime `b9ad351a7241` and `runtime/current` remained
  unchanged. Release `acd80ab9f6ae` was not activated. No service, launchd,
  Caddy, Ubuntu, public, or production change occurred. Activation, rollback,
  restart, public staging, production, and production writes remain
  `NOT_AUTHORIZED`.

## 2026-08-05 — RUNTIME-CONTRACT-04A canonical launcher target

- Source commit `637f5ee62ee7a5ac24c06afe9074811077cf0082`
  (`fix(runtime): derive serving target from canonical launchers`) makes both
  canonical launchd runners the serving-target authority. They must agree on
  one complete target: `core.api.shadow:app`.
- Recorded `core.api.app:app` as the internal FastAPI composition target. It is
  diagnostic/composition-only and cannot be selected as the direct production
  serving target. Missing, conflicting, multiple, malformed, or abbreviated
  launcher declarations fail closed.
- Restricted health endpoint discovery to valid path-shaped endpoints, removed
  duplicates, and made output deterministic. Targeted verification was 7
  passed; after harness-only failures, the successful isolated Full Suite was
  2281 passed, 5 deselected, with 437 warnings.
- Runtime current remains `b9ad351a7241`. Previously built immutable release
  `382ba887a045` was not activated, and no immutable release has been built from
  the source commit above. No build, activation, service restart, launchd or
  Caddy mutation, public opening, Ubuntu change, production write, or
  production authorization occurred. Production remains `NOT_AUTHORIZED`.

## 2026-08-04 — RUNTIME-BUILD-02A phased Runtime builder

- `5517fdb25a68c65f1bc8db03110900aa44ff173f` made an explicit mode mandatory
  and separated BUILD/VALIDATE from ACTIVATE. Build installs dependencies only
  in an owned staging release, generates and validates metadata plus the exact
  source marker, and atomically finalizes an immutable release without changing
  `runtime/current` or patching an existing finalized release.
- Activation accepts only an already finalized validated release, revalidates
  its source marker, metadata, and Runtime Python, and atomically switches
  `runtime/current`. It does not install dependencies, restart services, or call
  `launchctl`; missing or invalid modes fail closed.
- Initial targeted verification was 18 passed. The main Full Suite was 2270
  passed, 5 deselected, with 437 warnings; the standalone Full Suite was 2270
  passed, 5 deselected, with 435 warnings.

## 2026-08-04 — RUNTIME-BUILD-02B executable contract correction

- `f8f2890178c78862cff53362fd167982fa672c99` restored the canonical builder's
  Git mode from the RUNTIME-BUILD-02A regression of `100755` to `100644` back
  to `100755`; builder content remained byte-for-byte unchanged.
- Added a deterministic executable-bit regression test. Main and standalone
  targeted verification were each 19 passed. Their Full Suites were each 2271
  passed and 5 deselected, with 437 and 435 warnings respectively.
- Worktree, index, committed tree, and standalone clone all verified Git mode
  `100755`. The initial pre-staging `git ls-files` blocker was a host gate error,
  not a product defect.
- No real Runtime build or activation, `runtime/current` change, existing
  release modification, service restart, `launchctl` or Caddy operation, push,
  or production authorization occurred. Production remains `NOT_AUTHORIZED`.

## 2026-08-04 — DOCS-RECONCILE-01 verified implementation baseline

- `95f2f9d7b302428889d28e377fece3deb33eaf8e` (`TEST-INFRA-02`) replaced
  historical-host test dependencies with an immutable trusted evidence binding
  and deterministic canonical 14-artifact non-production generator. Focused
  verification was 4 generator tests and 3 factory tests; clean-room targeted
  verification was 74 passed, and its phase Full Suite was 2244 passed,
  5 deselected, with 437 warnings.
- `2bf553a733c3cb4c1d1b147f598fc7b696bd0318` (`FIX-GIT-01`) corrected the
  read-only file-backed Git identity observer with loose-ref precedence,
  exact-match `packed-refs` fallback, detached-HEAD support, and bounded
  symbolic-ref resolution. Codex-focused and host-targeted verification were
  each 27 passed; the pre-commit main Full Suite was 2257 passed, 5 deselected,
  with 437 warnings, and the standalone commit Full Suite was 2251 passed,
  5 deselected, with 435 warnings.
- `52f896f085186dc7fef65106942980d2cdaaf8ef` added the atomic immutable
  Runtime source commit marker and fail-closed activation contract. Runtime
  focused verification was 15 passed; both main and standalone clean Full
  Suites were 2257 passed and 5 deselected, with 437 and 435 warnings
  respectively.
- These were phase-specific verification gates. No push, Runtime build or
  activation, service/launchd/Caddy change, public opening, or production
  authorization occurred; production remains `NOT_AUTHORIZED`.

## 2026-08-04 — OPS-01B-R5-R3A Runtime Source Commit Marker

- Made runtime metadata generation publish both `metadata.json` and the exact
  `.aicontrolcenter-source-commit` marker through sibling temporary files,
  flushed and fsynced before `os.replace` publication.
- Added strict lowercase full-SHA validation, paired failure cleanup, and
  refusal to repair an existing immutable runtime release in place.
- Preserved metadata schema/status compatibility and the pre-activation gate;
  no runtime was built, activated, modified, or restarted.

## 2026-08-02 — SHOP-02C

- Added deterministic ProductDraft validation with canonical input/result digests and replaceable contract rules.
- Added deny-by-default authorization, HUMAN-only exact-revision review orchestration, deterministic audit events, application idempotency, and read-only projections.
- Kept ProductDraft contracts at 1.0.0 and adapters in-memory/non-production; no API mutation route, persistent storage, WooCommerce write, or production activation was added.
- Production writes remain `NOT_AUTHORIZED`; SHOP-02D read API and Dashboard projection is next.

## 2026-07-31 — M4-A3

- Added immutable test-only authorization simulation contracts and deterministic
  injected-clock/seed lifecycle simulation for five independent capabilities.
- Added canonical evidence chaining, in-memory single-use claim protection,
  negative scenarios, and live-boundary rejection.
- No real authorization, operational permit, claim, writer, monitoring,
  dispatch, notification, Ubuntu participation, command, or production
  activation occurred.
- Decision: `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`; `.env` is not
  required and the 427 warnings remain backlog.

## 2026-07-30 — M3-A4B2B2B-R4

- Added the preflight-only exact `ubuntu_participation=false` governance
  exception without weakening global unsafe-field denial.
- Added an immutable, canonical, digest-bound live permit result shared by the
  permit service and orchestrator.
- Added strict compatibility and default-deny regressions; no actual
  authorization, permit, claim, bootstrap, target, or production activation
  occurred.

## 2026-07-30 — M3-A4B2B2B-R3 Recovery-2

- Closed the first recovery's Git-evidence blocker with a fixed, bounded,
  read-only `/usr/bin/git` collector isolated in `git_readonly_evidence`.
- Added independent public audit/replay inspection, deterministic
  PRE_ACTIVATION monitoring, and canonical post-claim failure-evidence tests.
- Kept the validation runner validation-only; no actual bootstrap or activation
  ran, and fresh approval remains required.

## 2026-07-30 — M3-A4B2B2B-R3

- Added the strict local controlled operational coordinator and CLI.
- Preserved validation-only execution runner and production `NOT_AUTHORIZED`.
- Recovered the previously blocked attempt by adding the reviewed default live
  collaborator composition and pytest-only end-to-end authorization, permit,
  atomic claim, Mac bootstrap, backup/restore, and post-claim failure coverage.
- No actual operational bootstrap or managed-target creation occurred; fresh
  independent approval is required for the recovery commit.

## 2026-07-30 — M3-A4B2B2B-R1 Existing Safe Parent Compatibility

- Corrected the application-state parent from exclusive to shared ownership.
- Added immutable parent/sibling evidence and strict managed-target absence.
- Preserved existing parent metadata and siblings during success and cleanup.
- Performed no real permit issuance, claim, bootstrap or Production activation.

## M3-A4B2B1A

- Added immutable deterministic issuance-review contracts, gate, builder and validator.
- Bound readiness, authorization, executor, preflight, target/schema/plan,
  restriction, Git, test and all-zero safety evidence.
- Retained the 427-warning restriction without acknowledgement and reported
  human approvals missing.
- Performed no permit, claim, bootstrap, operational write or production authorization.

## 2026-07-30 — M3-A4B2B0 Read-Only Mac Host Preflight

- Added immutable host, target, filesystem, capacity, closure, check, finding,
  restriction and report contracts.
- Added deterministic default-deny policy and a separate standard-library
  read-only Mac collector.
- Closed M3-A4B2B0 with zero permit, authorization, bootstrap, filesystem,
  database, Ubuntu, runtime, activation or Production effects.
- Next: M3-A4B2B1 Operational Permit Issuance.

## 2026-07-30 — M3-A4B2A Controlled Mac Bootstrap Executor Validation

- Added immutable test-only bootstrap contracts, executor/adapter ports and
  canonical evidence.
- Validated synthetic single-use permit claim before mutation, restrictive
  audit/replay bootstrap, baseline backup/restore and controlled cleanup.
- Kept operational bootstrap, writers, monitoring, dispatch and Production
  activation disabled.

## 2026-07-30 — M3-A4B1 Controlled Bootstrap Authorization

- Added immutable request, approval, restriction, target, schema, plan, safety,
  decision, permit, validation, and use-claim contracts.
- Added deterministic controlled-non-production authorization and validation
  services plus an injected atomic single-use registry port.
- Preserved the exact 427-warning remediation restriction and enforced
  independent operator and approver acknowledgement.
- Validated synthetic permits and claims only; no operational permit,
  authorization, bootstrap, path, database, writer, monitoring, dispatch,
  Ubuntu, command, API-write, or Production effect occurred.
- Closed M3-A4B1. Next: M3-A4B2 Controlled Mac Operational Bootstrap.

## 2026-07-30 — M3-A4A Operational Activation Readiness Gate

- Added immutable evidence, stage, path, permission, bootstrap, rollback,
  check, finding, restriction and canonical report contracts.
- Added deterministic evidence-only readiness and plan validation with
  warnings-only restrictions and default-deny contradictions.
- Closed M3-A4A with zero writes, created paths/databases, activated writers or
  monitoring, dispatch, network, Ubuntu or Production effects.
- Bootstrap authorization remains not granted and Production activation
  remains `NOT_AUTHORIZED`.
- Next: M3-A4B Controlled Mac Operational Bootstrap.

## 2026-07-30 — M3-A3C Monitoring and Alert Operational Drill

- Added immutable drill, envelope, receipt, plan, finding, and report contracts.
- Added deterministic end-to-end M3-A3A/M3-A3B validation and an injected,
  object-scoped in-memory simulated sink with controlled failure injection.
- Validated all drill scenarios, canonical bindings, exact counts, and zero
  dispatch, delivery, notification, network, database, and persistence effects.
- Closed M3-A3C and the M3-A3 Monitoring and Alert Track. External dispatch and
  alert persistence remain not implemented; operational monitoring remains
  inactive and Production activation remains `NOT_AUTHORIZED`.
- Next: M3-A4 Controlled Operational Activation Gate.

## 2026-07-30 — M3-A3B Alert Routing and Deduplication

- Added immutable routing config, history, finding, decision and plan contracts.
- Added deterministic logical routes, cooldown and duplicate suppression,
  reminders, severity escalation bypass and recurrence handling.
- Added fail-closed history, binding, destination, secret and authorization
  validation with zero dispatch, notification and persistence activity.
- Closed M3-A3B without operational monitoring activation, databases, external
  dispatch, routing persistence or Production activation.
- Next: M3-A3C Monitoring and Alert Operational Drill.

## 2026-07-30 — M3-A3A Read-Only Operational Monitoring

- Added immutable explicit-threshold monitoring config, evidence, dimension,
  finding, decision, snapshot and alert-candidate contracts.
- Added deterministic PRE_ACTIVATION monitoring and candidate evaluation with
  stable canonical JSON, IDs, digests and deduplication keys.
- Added complete freshness, integrity, recovery, concurrency, readiness,
  regression, Git, safety and production-contradiction validation.
- Closed M3-A3A with no persistence, database, external alert dispatch,
  notification, operational writer or Production activation.
- Next: M3-A3B Alert Routing and Deduplication.

## 2026-07-30 — M3-A2C Replay-State Backup and Recovery

- Added immutable recovery contracts, replaceable ports, explicit-path online
  SQLite backup/restore services and canonical digest-bound manifests.
- Added exact event/state recovery plus post-recovery replay and independent
  connection concurrency validation.
- Added corruption, mismatch, path-security, cleanup and transaction rollback
  tests using pytest temporary databases only.
- Closed M3-A2C without an operational replay DB, backup schedule, restore,
  writer activation or raw nonce write. Production remains `NOT_AUTHORIZED`.
- Next: M3-A3 Operational Monitoring and Alerts.

## 2026-07-29 — M3-A2A Permit and Replay Read-Only Foundation

- Added immutable permit/replay configuration, path, schema, finding, report,
  event-type and derived-state contracts.
- Added deterministic URI `mode=ro` inspection for replay lifecycles,
  hash-chain integrity, privacy, Production denial and Ubuntu ownership denial.
- Defined but did not create the future Mac application-state database path.
- Closed M3-A2A with no operational database, reservations, consumptions,
  persistent nonce writes, migrations, repairs or Production activation.
- Next: M3-A2B Durable Permit Reservation and Consumption.

## 2026-07-29 — M3-A1C SQLite Backup, Restore and Recovery

- Added immutable backup, restore, manifest, receipt, finding and recovery
  report contracts.
- Added explicit-path SQLite online backup, separate-target restore and
  deterministic complete-ledger validation.
- Added fail-closed tamper, idempotency, path, compatibility and dependency
  validation plus deployment and operations documentation.
- Used only pytest temporary databases; no operational database, backup
  schedule or restore was created or performed.
- Persistent writer activation is not started and Production activation is
  `NOT_AUTHORIZED`. Next: M3-A2 Durable Permit and Replay State.

## 2026-07-29 — M3-A1B Append-Only SQLite Audit Writer

- Added a separate existing-file-only SQLite writer with serialized append,
  full-chain validation, deterministic receipts and idempotent retry.
- Enforced preconfigured WAL, schema/index/trigger validation, read-back
  verification and rollback on failure without creation, migration or repair.
- Closed M3-A1B using only pytest temporary databases; no operational database
  or Production write was created or enabled.
- Next: M3-A1C Backup, Restore and Recovery Validation.

## 2026-07-29 — M3-A1A SQLite Read-Only Integrity Foundation

- Added explicit Mac application-state path policy and deterministic,
  canonical, read-only SQLite integrity reports.
- Added schema, metadata, integrity, sequence, hash-chain, privacy and
  Production-authorization inspection without append behavior.
- Closed M3-A1A with zero operational databases, writes, migrations, repairs,
  commands, network access, Ubuntu changes or Production activations.
- Next: M3-A1B Append-Only SQLite Audit Writer.

## 2026-07-29 — M2-P3 Pilot Evidence and Rollback Validation

- Added immutable deterministic evidence and rollback contracts.
- Added fail-closed validation, evidence-derived planning and an injected
  rollback port with replay denial.
- Validated exactly one rollback in a pytest-owned temporary sandbox.
- Closed M2 without persistent-host, Production, Ubuntu, network, command,
  database or audit writes.

## 2026-07-29 — M2-P2 Controlled Sandbox Pilot Activation

- Added immutable activation contracts, deterministic canonical receipts and a
  dependency-injected activation service.
- Added fixed typed operation ordering and fail-closed one-use permit
  reservation with replay denial after success or failure.
- Validated exactly one controlled pilot in a pytest-owned temporary sandbox.
- Added six safe fixtures plus failure, binding, safety, boundary and
  compatibility coverage.
- Closed M2-P2 without persistent host activation, durable audit persistence,
  Ubuntu access or Production authorization.

## 2026-07-29 — M2-P1 Controlled Sandbox Pilot Authorization

### Added

- Immutable pilot request, operator approval, decision, permit, validation
  report and restriction contracts.
- Deterministic default-deny authorization service with exact DPL-03C and
  DPL-04D evidence binding, typed safe operations, separation of duties and a
  bounded one-use permit.
- Six secret-free fixtures and operator/deployment authorization guidance.

### Status and safety

DPL-04 is CLOSED, M2 readiness is ACCEPTED and M2-P1 is CLOSED. Pilot
authorization policy is AVAILABLE; pilot activation is NOT STARTED. No
executor, adapter, persistent audit/nonce, sandbox artifact, network, Ubuntu,
service, API write or activation operation was performed. Persistent SQLite
audit is NOT IMPLEMENTED and Production activation remains `NOT_AUTHORIZED`.
Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## 2026-07-29 — DPL-04C Durable Audit Architecture Decision

- Added immutable audit event, envelope, append, integrity and read-only query
  contracts plus the replaceable `DurableAuditPort`.
- Defined deterministic canonical JSON identities and tamper-evident hash-chain
  verification without persistence.
- Accepted a future Mac-only append-only SQLite adapter; no database, migration,
  audit write, nonce write or production activation was added.
- Closed DPL-04C and marked DPL-04D ready while M2 remains incomplete.

## 2026-07-29 — DPL-04B Mac-Only Sandbox Adapter

- Added an explicit-root, non-production `MacSandboxAdapter` implementing the
  DPL-04A executor port for safe sandbox verification, preparation and
  evidence collection.
- Added canonical immutable JSON materialization, same-root atomic replacement,
  digest read-back, deterministic/idempotent results and strict symlink/path,
  secret and executable-payload rejection.
- Preserved zero commands, network, Ubuntu, repository and production writes;
  durable audit and production activation remain unavailable.

## 2026-07-29 — DPL-04A Typed Non-Production Executor Ports

- Added schema-validated executor capability, request, validation-report and
  result contracts plus typed executor, capability-provider and policy ports.
- Restricted ownership to the Mac Control Plane and environments to
  development, test and staging; production and Ubuntu ownership are rejected.
- Added a typed operation allowlist and deny-only default composition without a
  concrete real executor, API route, runtime command or production write.

## 2026-07-29 — DPL-03D Simulation-Only Apply Composition

- Added deterministic non-production simulation, a process-local replay
  guard, typed fake executor, and versioned receipt/report contracts.
- Closed DPL-03 without real deployment, API, production, Ubuntu, network,
  subprocess, or persistent-state capability. M2 remains open.

## 2026-07-16 — PI-001 Dashboard Shadow API Integration

### Added

- Added the Dashboard Control Plane JSON contract.
- Added immutable runtime metadata with schema validation.
- Added commit-specific runtime metadata generation.
- Added runtime metadata to the Dashboard response.
- Added metadata-gated runtime activation.

### Validated

- `GET /health` returns HTTP 200.
- `GET /dashboard` returns HTTP 200.
- `POST /dashboard` returns HTTP 405.
- Runtime commit matches Git HEAD.
- Shadow API remains read-only on `127.0.0.1:18100`.


<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## 2026-07-16 — Mac Control Plane Baseline

### Added

- Commit-specific Mac Runtime
- Non-root system LaunchDaemon
- Canonical launchd manager and executor
- Transactional canonical apply
- Transactional rollback
- launchd bootout settle policy
- Restart and recovery validation
- Read-only Shadow API monitoring

### Validation

- Final commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime: `1e102c001c28`
- Observation:
  `283/283` samples passed
- Observation duration:
  `23.535` hours
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- Final restart:
  `19761 → 19842`

### Safety

- AIControlCenter runs as `kyouhan`.
- Installed plist and runner remain root-owned.
- The API remains localhost-only.
- Mutating requests remain blocked.
- Production write cutover remains disabled.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## v0.9.0

Added

- Telegram Brain
- Telegram Polling
- Command Router
- Status Action
- Provider Fallback
- Conversation Memory
- SQLite
- Storage Registry
- Backup Registry

## Unreleased

### Planned

- Brain Scheduler
- Internal Heartbeat
- Job Registry
- Scheduler API
- Automation Foundation

## Scheduler Foundation

- Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Background Service

## Sprint 21-22

Added:

- Scheduler Heartbeat
- Job Registry
- Scheduler Loop
- Job Runner
- Scheduler API
- Telegram /scheduler
- Background Scheduler Service
- MemoryManager
- Working Memory
- Long-term Memory
- Memory API
- Telegram /memory
- Memory Search
- BrainAgent Memory Context

## Knowledge Layer

- Knowledge Registry
- Markdown Loader
- Knowledge Index
- Knowledge Search
- Telegram /knowledge
- Knowledge API
- BrainAgent Knowledge Context

## Planner Agent

- PlannerAgent
- Planner API
- Telegram /plan
- PlanStore
- Plan Review

## Automation Engine

- AutomationExecutor
- SafeExecutionPolicy
- AutomationQueue
- Automation API
- Telegram /automation
- Scheduler integration

## Homepage Integration

- HomepageStatusService
- /homepage/status API
- Telegram /homepage command

## Production Hardening

- systemd Services
- Service Health
- Configuration Validation
- Graceful Shutdown
- Operations Manual

## v1.0.0

### Added

- Production-ready AIControlCenter Brain platform
- FastAPI control plane
- OpenAI and Google provider support
- Provider fallback
- BrainAgent and status actions
- Scheduler and background jobs
- Conversation, working, and long-term memory
- Knowledge indexing and search
- Planner Agent
- Safe Automation Engine
- Telegram operations interface
- Homepage status API
- systemd and launchd deployment templates
- Installation, update, and readiness automation

### Architecture

- Mac mini M4 is the final Brain runtime
- Ubuntu remains an optional storage and backup Worker
- AIControlCenter operates standalone without Ubuntu

<!-- AI_SHOPPING_PLATFORM_START -->
## 2026-07-12 AI Shopping Platform Bootstrap

### Added

- AIControlCenter Shopping domain
- Shopping health endpoint
- Shopping readiness endpoint
- Shopping capabilities endpoint
- Shopping configuration
- Shopping API schemas
- Shopping tests
- Shopping architecture documentation
- Shopping API documentation
- Shopping testing documentation
- Shopping deployment documentation
- Shopping runbook

### Safety

- Catalog writes disabled by default
- AI execution disabled by default
- Automation execution disabled by default
- Human approval required by default
- Production target set to Mac mini M4

### Validation

- Shopping targeted tests passing
- Existing API regression tests passing
- Shopping route smoke tests passing
<!-- AI_SHOPPING_PLATFORM_END -->

## 2026-07-12 API Router Cleanup

### Fixed

- Removed duplicate FastAPI router registrations
- Removed duplicate OpenAPI operation identifiers
- Added API route uniqueness regression tests

### Validation

- Shopping API routes remain available
- OpenAPI operation identifiers are unique
- Full regression suite passes

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

## 2026-07-12 Read-only Mock Product Catalog

### Added

- Product domain model
- Commerce Catalog Port
- Mock Commerce Catalog Adapter
- Paginated product list API
- Product detail API
- Product not-found response
- Product catalog unit and API tests

### Safety

- Product catalog remains read-only
- No WooCommerce write operations
- No AI execution
- No automation execution

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 — Unreleased

### Added

- WooCommerce REST Adapter
- HTTP OAuth 1.0a development authentication
- HTTPS Basic Authentication support
- Adapter Factory
- Environment-driven Catalog Adapter selection
- Shopping Integration Status API
- Product Catalog API
- Product Detail API
- Category API
- WordPress and MariaDB Docker Compose runtime
- systemd Shopping EnvironmentFile support
- Shopping deployment and operations documentation

### Fixed

- Duplicate API Router registration
- WordPress Healthcheck variable escaping
- WordPress WORDPRESS_CONFIG_EXTRA Parse Errors
- Test environment leakage from live Shopping settings
- Canonical WooCommerce signing URL and internal connection URL separation

### Security

- WooCommerce API integration is read-only
- Secret files excluded from Git
- systemd runtime Secret permissions restricted
- Public HTTPS deferred until a user-owned domain is available
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 — Unreleased

### Added

- Featured Products API
- Product Search API
- Category, price, and stock filters
- Search pagination
- Product image URL contract
- WooCommerce representative image mapping
- Image placeholder fallback
- Modular AI Shopping Storefront Plugin
- WordPress AIControlCenter API client
- WordPress Presentation Cache
- Storefront shortcode
- Responsive Storefront CSS
- External AI Shopping page

### Fixed

- Storefront Renderer search UI integration
- Search API client query serialization
- Boolean stock parameter serialization
- WooCommerce image mapping tests
- Test helper contract inconsistencies
- Trailing whitespace and blank-line issues

### Security

- Storefront does not receive WooCommerce credentials
- WordPress calls read-only AIControlCenter endpoints
- Search input is sanitized
- Rendered output is escaped
- Business Logic remains in AIControlCenter
<!-- SHOPPING_M5_END -->

## [2026-07-13] Commit 19 - Homepage Curated Sections

### Added
- Homepage curated shopping sections
- NEW ARRIVALS
- BEST SELLERS
- TOP
- DRESS
- OUTER
- BAG
- SALE

### Changed
- Renderer supports multi-section homepage
- Homepage sections powered by Shopping Search API
- Homepage displays up to 8 products per section

<!-- AI_SHOPPING_STOREFRONT_V016_CHANGELOG -->
## 2026-07-13 — AI Shopping Storefront v0.16.0

### Added

- API-driven product detail route
- Product detail renderer and template
- Orange Coco Home v5 icons and hero asset
- Related product presentation

### Changed

- Established Orange Coco v6 as the canonical storefront UI
- Updated the storefront plugin to version 0.16.0
- Improved front-page structure and responsive layout

### Fixed

- Missing products now return HTTP 404
- Product status is set before WordPress headers render

### Removed

- Legacy `orange-coco-final.css`
- Legacy `orange-coco-final.js`
- Unused Home v4 and Home v5 CSS files
- Duplicate original hero image

### Git

- Feature commit: `a4d6098`

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Unreleased — Mac Control Plane

            ### Added

            - Non-root system LaunchDaemon supervisor
            - Root-owned LaunchDaemon plist
            - Root-owned immutable runner installation
            - JSON-first supervisor status and lifecycle
            - Read-only Shadow API on `127.0.0.1:18100`

            ### Changed

            - Replaced the GUI-dependent LaunchAgent
              production design with a system LaunchDaemon.
            - Defined normal running state as port `18100`
              being owned by the active LaunchDaemon PID.
            - Restricted port-release validation to
              uninstall and bootout operations.

            ### Verified

            - Application user: `kyouhan`
            - Health response: HTTP `200`
            - Mutating request response: HTTP `405`
            - Localhost-only listener
            - Runtime and Git commit match
            - Secure plist and runner ownership
            - Automatic restart: `1661 → 1975`
            - Full Test Suite:
              313 passed, 5 deselected

            ### Pending

            - Headless reboot recovery
            - 24-hour Shadow observation
            - Ubuntu Worker read-only integration

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Unreleased — Headless Recovery

            ### Added

            - GUI-independent system LaunchDaemon recovery
            - Headless reboot recovery JSON Gate
            - System log path:
              `/var/log/aicontrolcenter`

            ### Fixed

            - Replaced GUI-dependent supervision
            - Recovered from launchd bootstrap error 5
            - Verified non-root process ownership
            - Verified Runtime and Git commit alignment

            ### Pending

            - Manager installer reconciliation
            - 24-hour Shadow observation
            - Production cutover decision

            - Verified: `2026-07-14T04:11:33+00:00`
- Commit: `aadb42089642a17f54825b850626bd43d5e22015`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/aadb42089642`
- Pre-reboot PID: `875`
- Post-reboot PID: `567`
- Process user: `kyouhan`
- Health HTTP: `200`
- Write probe HTTP: `405`
<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:END -->

<!-- AICONTROLCENTER:SHADOW_OBSERVATION:START -->
## Unreleased — Shadow Observation

### Added

- Five-minute Shadow observer
- JSON Lines operational telemetry
- CPU and RSS collection
- Runtime and Git commit validation
- Health and write-protection probes
- Observation summary Gate

### Pending

- Complete the 24-hour observation window
- Reconcile the canonical LaunchDaemon installer
- Production cutover approval

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:PI-002:START -->
## 2026-07-17 — PI-002 Ubuntu Worker Health JSON Adapter

### Added

- Versioned Ubuntu worker health JSON contract
- Bounded SSH worker transport
- Ubuntu worker health adapter
- Production worker configuration selection
- Structured worker monitoring errors
- Dashboard worker health JSON integration
- Production worker environment loader
- Immutable runtime Production Gate evidence

### Changed

- `GET /dashboard` now monitors `ubuntu-main` by default.
- The canonical runner validates worker environment ownership, group and mode.
- The worker environment contract is `root:staff 640`.

### Verified

- Implementation commit: `39dc5c3db72c9ac1592fc3920012aba3eacd23cd`
- Runtime commit matched the implementation Git HEAD.
- system LaunchDaemon ran as `kyouhan:staff`.
- `GET /health` returned HTTP `200`.
- `GET /dashboard` returned HTTP `200`.
- Dashboard returned one `ubuntu-main` worker object.
- Worker errors were returned as structured JSON.
- Full regression: `412 passed, 5 deselected`.

### Pending

- Configure the dedicated SSH identity for the LaunchDaemon worker adapter.
- Validate a successful remote `worker-health-json.sh` response.
- Resolve Python and Starlette deprecation warnings.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## 2026-07-19 — PI-003 Ubuntu Worker Minimum Closure

### Changed

- Reclassified Ubuntu as an optional on-demand infrastructure worker.
- Prioritized Mac mini standalone Production operation.
- Deferred detailed Ubuntu telemetry and lifecycle automation.

### Verified

- Ubuntu reboot automatically activated Docker.
- Immich automatically restarted after Ubuntu boot.
- Nextcloud automatically restarted after Ubuntu boot.
- Required containers use `restart: unless-stopped`.
- Ubuntu was powered off after service recovery validation.
- AIControlCenter remained `ONLINE`.
- Health endpoint returned HTTP `200`.
- Dashboard endpoint returned HTTP `200`.
- `ubuntu-main` returned structured `OPTIONAL_UNAVAILABLE` status.
- Validated implementation runtime commit: `85e0d2186dcd9338dea4288e629092bd62f882e8`.

### Deferred

- Dedicated LaunchDaemon SSH identity
- Healthy Ubuntu telemetry
- Detailed storage and backup monitoring
- Worker lifecycle automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## 2026-07-20 — PI-004 Mac Standalone Production Baseline

### Added

- Mac standalone Production service manifest.
- Homepage standalone projection contract.
- Explicit optional storage and backup metadata.

### Verified

- system LaunchDaemon automatic recovery after Mac reboot.
- immutable runtime and Git commit alignment.
- Health, Dashboard and Homepage HTTP `200`.
- Platform status `ONLINE` without Ubuntu.
- Full test suite passed.
- Final PI-004 Production evidence generated.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Mac Service Deployment Platform

### Added

- Reusable Mac service manifest schema and dependency-free validator.
- Read-only deployment plan, service inspector, and desired/actual diff JSON interfaces.
- Ollama managed-service design and rollback-aware dry-run.
- SHA-256-bound approval request with expiry and action allowlist validation.

### Safety

- Ollama installation and model download remain disabled.
- All write operations require future approval and execution tooling.
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
## PI-007 — Approved Model Lifecycle Monitoring and Governance

### Added

- Canonical model-governance registry at
  `config/model-governance.json`.
- Default-deny, read-only registry loader.
- Immutable model-governance evaluation objects.
- Compliance evaluation for approved, missing, unapproved, digest-mismatch,
  and resource-policy states.
- Read-only `GET /api/governance/models` endpoint.
- Focused registry, evaluator, Ollama adapter, and API tests.

### Production

- Source commit:
  `39fe04e3330e398f38567efa58bddb39b9893756`
- Runtime release: `39fe04e3330e`
- Previous rollback release: `3679588b760c`
- Production health: `ONLINE`
- Ollama health: `ONLINE`
- Governance mode: `read-only`
- Default policy: `DENY`
- Write operations allowed: `false`
- Rollback readiness validated without performing an actual rollback.

### Technical Debt

- Existing Starlette/httpx test-client deprecation warning remains.
- Existing timezone-naive `datetime.utcnow()` warnings remain.
- These warnings did not block PI-007 and require a separate maintenance task.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — Model Governance Audit and Dashboard Integration

### Added

- canonical immutable governance audit snapshots
- deterministic SHA-256 snapshot identity
- SQLite migration and schema controls
- append-only audit repository
- audit snapshot service
- historical audit comparison service
- read-only audit query service
- GET-only governance audit API
- Dashboard governance audit read model
- Production runtime provenance environment

### Changed

- Production runner now uses release metadata instead of mutable Git HEAD
- Production restart no longer requires a clean Git working tree
- Dashboard now exposes `model_governance_audit`

### Fixed

- rollback failure caused by runtime commit and Git HEAD coupling
- unsafe symlink replacement procedure
- false-negative Dashboard validation caused by a 5-second timeout
- invalid direct diagnostic helper import

### Production

- active commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- active runtime: `b9ad351a7241`
- rollback runtime: `0352e396f329`
- full suite: `636 passed, 5 deselected`
- Production closure gate: passed

<!-- PI-009:START -->
## PI-009 — Governance Audit Operations Visibility

### Added

- Governance operations domain, event model and projection policy.
- Append-only SQLite operations event repository.
- Read-only governance operations presentation service.
- GET-only governance operations API route.
- Fail-soft Dashboard operations panel.
- Missing-schema and missing-database UNKNOWN projections.
- Production activation and Notion handoff documents.

### Changed

- Governance audit leakage assertions are scoped to the
  `model_governance_audit` panel so unrelated operation identifiers do
  not produce false positives.

### Safety

- No write API was added.
- No automatic migration, retry, restore or remediation was added.
- Production database content and WAL content remained unchanged.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## 2026-07-22 — PI-009 Governance Operations Final Close

### Added

- Production UTC-aware SystemUTCClock adapter.
- JSON-first one-shot governance operation runner.
- Explicit Production dependency composition.
- Per-operation non-blocking execution locks.
- Ephemeral-path composition tests.

### Validated

- 14 targeted tests passed.
- 717 full-suite tests passed.
- 5 tests remained intentionally deselected.
- 427 warnings remained at the existing baseline.
- Production database and WAL were unchanged.
- No LaunchAgent was written or activated.

### Deferred to PI-010

- Explicit automated cadence policy.
- launchd installation and activation.
- First scheduled-run observation.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## 2026-07-23 — PI-010 Production Scheduler

Added explicit governance cadence, managed headless cron deployment, append-only Production audit validation, rollback backups, and uninstall/reinstall validation.

Added GovernanceAuditSnapshotExecutor for read-only JSON audit snapshots and SQLiteOnlineBackupVerifier for SQLite online backup, quick_check, row-count, and SHA-256 validation.

Both governed Production operations reached run_succeeded. The managed cron adapter remained active after rollback validation, and the full regression suite passed.

<!-- BEGIN AICONTROLCENTER SPF-002 CHANGELOG -->
## 2026-07-23 — Shopping Platform Foundation

### Added

- Shopping bounded-context architecture.
- AIControlCenter, WordPress, WooCommerce, and Ubuntu ownership matrix.
- Read-only adapter boundaries.
- Canonical `shopping.v1` JSON contract.
- SG-0 through SG-9 security gates.

### Safety

- AIControlCenter remains the Shopping Control Plane.
- WordPress remains a headless CMS.
- WooCommerce remains a replaceable commerce engine.
- Ubuntu remains a stateless infrastructure worker.
- No Shopping write capability was enabled.
<!-- END AICONTROLCENTER SPF-002 CHANGELOG -->

<!-- SPF-003:START -->
## 2026-07-23 — SPF-003 Shopping Read-Only Port Foundation

### Added

- Import-safe Shopping package boundaries.
- Seven transport-neutral read-only or compute-only Protocol interfaces.
- Provisional JSON-first Shopping contract aliases.
- Import, typing, signature, compatibility, write-deny, and side-effect tests.

### Changed

- Migrated `core/shopping/ports.py` to `core/shopping/ports/__init__.py` byte-for-byte.
- Preserved the existing `CommerceCatalogPort` import contract.

### Validation and Safety

- Targeted tests: 6 passed.
- Full regression: 747 passed with 5 deselected.
- Production infrastructure was not modified.
- Shopping write operations remain disabled.

Next milestone: **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## 2026-07-23 — SPF-004 Canonical JSON Schema v1

### Added

- 15 canonical Shopping contract schemas.
- shared schema definitions and error envelope.
- versioned `registry.json`.
- explicit Python schema registry loader.
- fail-closed contract payload validator.
- pinned `jsonschema==4.26.0` and `referencing==0.37.0`.
- six canonical schema validation tests.

### Validation

- targeted tests: 6 passed.
- full regression: 753 passed.
- remote schema references denied.
- automatic schema JSON loading during import denied.

### Fixed

Gate-harness false positives encountered during SPF-004 were classified and corrected:

- `TEST_ASSERTION_FALSE_POSITIVE_GLOBAL_PATH_BLOCK`
- `TEST_ASSERTION_FALSE_POSITIVE_STRING_PREFIX_COUNT`
- `TEST_HARNESS_EMBEDDED_NEWLINE_DEDENT_DEFECT`

No production defect was attributed to these harness failures.

<!-- SPF-005-CLOSE:BEGIN -->
## 2026-07-23 — SPF-005 Capability Registry deny-by-default

### Added
- Static immutable Shopping capability registry owned by AIControlCenter.
- Eleven canonical READ capabilities with vendor-neutral identifiers.
- Read authorization orchestration through `PolicyDecisionPort`.
- Denial and compatibility tests covering all registered reads and reserved writes.

### Security
- Unknown capabilities deny by default.
- Reserved WRITE capabilities are non-executable and denied before policy evaluation.
- Request and policy decision capability mismatches fail closed.
- Policy evaluation exceptions are normalized to `shopping.policy.evaluation_error`.
- Vendor exception messages are not exposed through authorization errors.

### Validation
- 22 targeted Shopping capability tests passed.
- 775 full regression tests passed.
- Production unchanged.
- Ubuntu unchanged.
- Shopping write operations remain disabled.

### Recovery Notes
- `TEST_HARNESS_LITERAL_INDENTATION_MISMATCH` affected an SPF-005-05 patch harness only and was recovered with AST-based source targeting.
- `POLICY_EXCEPTION_FAIL_CLOSED_HARDENING` is the actual security hardening introduced by SPF-005-05.

Implementation commit: `f807cc0dfb8a27d2bf387bdc3dd897e4fe331953`.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## 2026-07-23 — SPF-006 Read Adapter Contracts

### Added
- Commerce adapter contract conformance validation.
- CMS adapter contract conformance validation.
- JSON-first Commerce and CMS contract manifests.
- Commerce/CMS isolation and compatibility tests.

### Architecture
- `CommerceReadPort` and `CmsReadPort` remain the authoritative callable interfaces.
- Adapter implementations may not redefine platform business contracts.
- SPF-005 capability registry remains authoritative for capability bindings.
- Canonical AIControlCenter domain contracts are required across adapter boundaries.

### Safety
- Vendor DTO escape is prohibited.
- Adapter-owned policy evaluation is prohibited.
- Adapter-owned business logic is prohibited.
- WRITE-like public adapter methods are prohibited.
- Live WooCommerce and WordPress connections remain disabled.
- Production and Ubuntu were not modified.

### Validation
- Targeted: 28 passed.
- Full regression: 803 passed.

Implementation commit: `fd1bbe2ff212e9eeb442562ffeed32bed97c1072`.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## 2026-07-23 — SPF-007 Adapter Health Monitoring

### Added
- Vendor-neutral health probe normalization.
- Health states for healthy, degraded, and unavailable adapters.
- Vendor-neutral health failure taxonomy.
- Sanitized health failure detail codes.
- Stateless deterministic health aggregation.
- JSON-compatible monitoring snapshots.
- End-to-end timeout and failure compatibility tests.

### Architecture
- AIControlCenter owns adapter monitoring and routing signals.
- Health remains separate from authorization and policy evaluation.
- Aggregation precedence is UNAVAILABLE, then DEGRADED, then HEALTHY.
- Empty aggregation input fails closed as UNAVAILABLE.
- Probe retry, scheduler ownership, and persistent health state remain outside the health normalization layer.

### Safety
- Raw vendor exception text is rejected from monitoring metadata.
- Credential-bearing error payloads are prohibited.
- Shopping WRITE methods remain disabled.
- Live vendor transport remains disabled.
- Production and Ubuntu were not modified.

### Validation
- Targeted: 34 passed.
- Full regression: 837 passed.

Implementation commit: `63263b734ead4eb083f9b91923f4b41c3b644e34`.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## 2026-07-23 — SPF-008 Read-only Snapshots

### Added
- Canonical snapshot normalization contract.
- Deterministic canonical JSON serialization.
- Immutable snapshot read representation.
- Read-only snapshot query orchestration.
- Authorization-before-repository enforcement.
- Isolation and immutability validation.

### Architecture
- AIControlCenter owns snapshot governance and read orchestration.
- `SnapshotRepositoryPort` remains the authoritative repository boundary.
- Snapshot creation and persistence remain classified as writes.
- Schema validation remains deferred to SPF-009.
- Ubuntu remains free of Shopping application state.

### Safety
- Authorization denial prevents repository access.
- Authorization failures fail closed.
- Repository failures are sanitized.
- Vendor refresh, persistence, production registration, and Shopping writes remain disabled.

### Validation
- Targeted: 35 passed.
- Full regression: 872 passed.

Implementation commit: `d8859a3706a087f88be513e32097b22c9a8ec3d6`.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

### Added

- Canonical Draft 2020-12 runtime schema validator with deterministic `VALID`, `INVALID`, and `ERROR` results.
- Local-only `referencing.Registry` schema resolution with remote-reference rejection.
- Consumer-safety schema drift classifier with four explicit drift states.
- Read-only schema drift monitor using authorization-before-discovery and the authoritative `context` plus `adapter_name` discovery contract.
- Negative, isolation, immutability, sanitization, compatibility, and full-regression coverage.

### Validation

- 58 SPF-009 targeted tests passed.
- 930 full-regression tests passed with 5 deselected.
- Production, Ubuntu and platform write operations remained unchanged and disabled.

<!-- AICONTROLCENTER:SPF-010:CLOSED -->
## SPF-010 — Shopping Platform Foundation Production Readiness Closure

- Status: CLOSED
- Shopping Platform Foundation: 10/10 (100%)
- Production Readiness Gate: PASSED for the read-only Foundation.
- Closed SPF-010 and the Shopping Platform Foundation.
- Validated 233 Shopping tests.
- Full regression: 930 or more passed, 5 deselected, 0 failed, 0 errors.
- Read-only operational smoke validation: PASSED.
- AIControlCenter remains the single Control Plane on Mac mini M4.
- Ubuntu Server remains a stateless infrastructure worker only.
- Production write operations remain disabled.
- Automatic schema adoption and automatic schema migration remain disabled.
- Any future mutation or write capability requires a separate sprint and explicit production gate.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## Unreleased — SRI-03 External Read Integration

### Added

- Canonical WooCommerce CommerceReadPort integration.
- Lossless raw WooCommerce read path for canonical normalization.
- ProductSnapshot and OrderSummary canonical normalization and schema validation.
- GET-only bounded WooCommerce read transport.
- Caddy ingress configuration on the Mac Control Plane.

### Validated

- Caddy runtime and Mac LAN ingress.
- DDNS and public IPv4 consistency.
- External WAN TCP 80 through an LTE or 5G request returning HTTP 200.
- DNS A, AAAA, CNAME, and CAA issuance state.
- Authoritative ipTIME parent CAA restriction.

### Architecture decisions

- Provider-owned DDNS is not the production canonical TLS identity.
- Root cause: `PARENT_CAA_PROHIBITS_PUBLIC_CA_ISSUANCE`.
- Production TLS requires a platform-controlled DNS namespace.

### Safety

- Shopping writes remain disabled.
- Production ACME retries against the blocked ipTIME hostname are stopped.
- No Ubuntu Shopping business logic or application state was introduced.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:CHANGELOG -->
## Shopping External Read Integration Closure

### Added

- Production WooCommerce GET-only integration with protected read credential.
- Generic core/cms boundary and WordPress published post and page adapter.
- Canonical CMS models and normalization.
- ExternalReadObserver with Health, Schema, Snapshot and Drift.
- Sanitized persisted JSON operational evidence.

### Production validation

- WooCommerce products: 0.
- WooCommerce orders: 0.
- WordPress published posts: 1.
- WordPress published pages: 5.
- Full repository regression: 984 passed and 5 deselected.

### Failure prevention ledger

- F25 CLOSED: lifecycle semantics replace physical invocation count assumptions.
- F26 CLOSED: launchd authority does not require a fixed plist installation path.
- F27 CLOSED: health route ownership is explicit.
- F28 CLOSED: shared namespace permissions are not the per-service secret boundary.
- F29 CLOSED: annotation symbols are not assumed to be runtime exports.
- F30 CLOSED: domain snapshot normalization is not used for generic cross-domain observations.
- F31 CLOSED: secret absence is checked before local secret references are cleared.
- F32 CLOSED: credential prefix substrings are not treated as complete credential values.
- F33 CLOSED: staged diff hygiene is authoritative because unstaged diff checks do not include untracked file content.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## 2026-07-28 — DPL-01 Architecture and Documentation

### Added

- Canonical DPL-01 inventory, assessment, blockers and sprint plan.
- DPL architecture decision covering ownership, immutable contracts,
  read/plan/apply separation, platform boundaries and legacy Linux policy.
- Repository agent instructions preserving the approved architecture and
  production-write prohibition.

### Documented

- DPL bounded context and lifecycle.
- SRI closure baseline and current DPL program state.
- DPL-01 through DPL-08 roadmap and production authorization milestones.

No code, configuration, Compose, schema, test, runtime or production change was
performed.
<!-- AICONTROLCENTER:DPL-01:END -->

## 2026-07-29 — DPL-04D M2 Operational Readiness

### Added

- Immutable M2 evidence, check, finding, report and decision contracts.
- Pure deterministic thirteen-category readiness gate and four safe fixtures.
- M2 non-production sandbox runbook and go/no-go checklist.

### Status and safety

DPL-04A through DPL-04D and DPL-04 are CLOSED. The canonical passing fixture
records `M2 READINESS_ACCEPTED`; `M2 ACTIVATION_NOT_STARTED`. No executor,
Ubuntu, runtime, API, persistent audit, production write or activation was
performed. Production activation remains `NOT_AUTHORIZED`.

## 2026-07-29 — M3-A2B Durable Permit Reservation and Consumption

### Added

- Separate existing-file SQLite permit replay writer and immutable contracts.
- Atomic reservation, consumed and failed-closed transitions.
- Full-chain validation, deterministic receipts, idempotency and concurrency tests.
- M3-A2B operations, state-machine and closure documentation.

### Safety

All writable validation used pytest temporary databases. No operational replay
database, migration, repair, audit write, raw nonce write, Ubuntu change or
Production activation occurred.
# M3-A4B2B1B

- Added immutable human-approval, identity, restriction-acknowledgement,
  execution-window, report and issuance-result contracts.
- Added deterministic approval, identity-independence, acknowledgement and
  execution-window validators plus a synthetic-only in-memory coordinator.
- Retained the current `UNASSIGNED` independent approver snapshot as `DENIED`.
- Issued and claimed zero operational permits; authorized and executed zero
  operational bootstraps; production remains `NOT_AUTHORIZED`.
# M3-A4B2B2A

- Added immutable runtime contracts, Mac path policy, canonical live-permit
  validation, atomic adjacent claim, fail-closed runtime adapters, coordinator,
  evidence validation and strict JSON entrypoint.
- Reused validated M3-A4B2A audit/replay bootstrap capability.
- Added confined tests and operations documentation. No operational execution,
  target creation, activation or production authorization occurred.
# Unreleased

- Added M3-A4B2B2B-R2 immutable controlled operational activation
  authorization, live issuance gate and controlled runner gate.
- Preserved default deny and test/operational adapter separation; no actual
  operational execution occurred.
# M3-A4B2B2B-R5

- Added a typed, deterministic full-evidence to `warnings-427` executor
  acknowledgement projection and pre-issuance/pre-claim compatibility gates.
- Preserved the stopped pre-claim forensic authorization and permit; no actual
  bootstrap or production activation was performed.

# M3-A4B3

- Added deterministic canonical bootstrap-chain validation and root-confined
  baseline audit/replay recovery drills.
- Reused public read-only SQLite inspectors; both snapshots and restores are
  `HEALTHY` with zero events and unchanged sources.
- Added fail-closed evidence, backup, permission, symlink, schema,
  cross-service, destination, tamper, claim-reuse, and production-deny tests.
- Recorded the successful one-use permit as permanently consumed. No writer,
  monitoring, dispatch, Ubuntu, or production activation was performed.

## M3-A4C

- Added immutable controlled-activation contracts, fail-closed write and bypass
  gates, and deterministic JSON closeout.
- Closed M3 without changing operational state or authorizing runtime, Ubuntu,
  or production capability; future activation requires a separate gate.

## M4-A1

- Added modular immutable capability, state transition, policy, planning, and
  validation contracts for controlled activation architecture.
- Added five default-inactive and unauthorized capabilities with independent
  authorization, permit, claim, evidence, rollback, and dependency boundaries.
- Added deterministic canonical JSON plans and digests plus comprehensive
  default-deny and no-side-effect tests.
- Added dependency-zone policy/schema coverage and M4 operations documentation.
- No writer, monitoring runtime, dispatch, Ubuntu change, command, API write
  route, authorization, permit, claim, activation, or production transition

## M4-A1R1

- Closed M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a`
  with an immutable retained-source and disposable-working-copy contract for
  SQLite inspection and recovery tests.
- Confined SQLite database, WAL, and SHM access side effects to copied recovery
  workspaces and added byte, mode, size, mtime, and digest regression coverage.
- Preserved M3-A4B3 bindings and all cryptographic, claim, evidence, and
  fail-closed production validation semantics.
- Passed 958 deployment and 1,942 full-regression tests with zero failures, 5
  configured deselections, and 427 existing warnings. No `.env`, operational
  access/write, authorization, permit, claim, activation, writer, monitoring,
  dispatch, Ubuntu change, command, API write route, or production
  authorization was used.
  occurred. The existing 427 warnings remain separate backlog.

## M4-A2

- Added immutable typed capability authorization scope, request, approval,
  restriction, decision, evidence, validation, grant-plan, and plan contracts.
- Added canonical UTC-normalized JSON and SHA-256 request, approval, and plan
  bindings with tamper rejection and an injected deterministic clock.
- Enforced exact branch/commit, M3/M4-A1, independent identity, one-capability,
  single-use, one-hour maximum TTL, full restriction, production-denial, and
  Ubuntu-denial policies.
- Added capability-specific read-only health and separately authorized
  dependency-reference requirements without implicit escalation.
- Added a deterministic test-only planner with zero authorization, permit,
  claim, activation, writer, monitoring, dispatch, network, API write, command,
  Ubuntu, or production effects.
- Decision: `READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`; `.env` and external
  notification endpoint secrets are not required. The existing 427 warnings
  remain separate backlog.
- Passed 59 targeted, 1,016 deployment, and 2,000 full-regression tests with
  zero failures; full regression retained 5 configured deselections and 427
  existing warnings.
## 2026-07-31 — AUTO-01

- Added the AIControlCenter-owned autonomous delivery architecture: immutable
  contracts, six autonomy levels, deterministic lifecycle, sprint-manifest
  validation, canonical JSON/SHA-256, DAG planning, approval gates, retry
  classification, evidence policy and bounded executor port.
- Added manifest and roadmap JSON schemas plus focused safety tests.
- Added architecture, manifest, retry and human-approval documentation.
- No runner, subprocess, network client, operational write, authorization,
  permit, claim, monitoring, dispatch or production activation was created.
- Decision: `READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE`; production remains
  `NOT_AUTHORIZED`, `.env` is not required, and 427 warnings remain backlog.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## 2026-07-31 — Shopping-First Roadmap Reprioritization

- Closed AUTO-01 as an architecture-only foundation.
- Deferred AUTO-02, AUTO-03 and M4-A4 through M4-A6.
- Established Shopping Platform as the primary product milestone.
- Established AI Integration Platform as the second service milestone.
- Established Personal AI Assistant as the third service milestone.
- Recorded the open-source-first capability-gap policy.
- Retained production status as `NOT_AUTHORIZED`.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## 2026-07-31 — SHOP-00 Architecture Closeout

- Closed SHOP-00 Shopping Platform Reprioritization.
- Confirmed the existing SRI implementation is already in current
  history.
- Closed the duplicate WooCommerce Read Adapter scope.
- Confirmed nine Shopping GET routes and zero mutation routes.
- Selected Product Management Read Model and Dashboard as the first
  incomplete product capability.
- Retained production writes as `NOT_AUTHORIZED`.
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## 2026-07-31 — SHOP-01B Management Read Model

- Added a deterministic read-only Shopping management projection.
- Added catalog, stock and inventory summary fields.
- Added health, readiness, capability and integration projections.
- Added payload and result mutation isolation.
- Added explicit network, persistence and write-boundary tests.
- Kept Dashboard and production registration out of this task.
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## 2026-07-31 — SHOP-01C Dashboard Integration

- Added the read-only `shopping_management` Dashboard projection.
- Reused the SHOP-01B management read model.
- Added deterministic unavailable-state failure isolation.
- Protected the existing Dashboard response when no projection is
  configured.
- Added no Shopping mutation route.
- Added no direct WooCommerce dependency.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## 2026-07-31 — SHOP-01 Product Management Dashboard Closed

- Closed the read-only Product Management Dashboard vertical slice.
- Validated default Shopping projection behavior.
- Validated READY, DEGRADED and UNAVAILABLE contract boundaries.
- Confirmed Dashboard backward compatibility.
- Confirmed Shopping and Dashboard routes remain GET-only.
- Confirmed zero direct Dashboard-to-WooCommerce dependencies.
- Retained production writes as `NOT_AUTHORIZED`.
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## 2026-08-01 — SHOP-01E2 Product Compatibility Recovery

- Added a ShoppingService-to-management compatibility adapter.
- Mapped legacy product IDs into canonical `product_id`.
- Converted legacy image values into canonical image lists.
- Converted Decimal display prices into JSON numbers.
- Preserved unknown SKU, inventory, URL and update fields as null.
- Restored the default mock Dashboard management projection.
- Added no write capability or WooCommerce dependency to Dashboard.
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## 2026-08-01 — SHOP-01E3C Secure WooCommerce Runtime

- Added a protected WooCommerce read credential provider.
- Added explicit non-secret Shopping runtime profile selection.
- Prevented credential copying into process environment or plist files.
- Enforced read-only API permission and filesystem boundaries.
- Validated the canonical WooCommerce target and Dashboard projection.
- Confirmed the current Commerce Engine contains zero products and one
  category.
- Added no Shopping mutation route or production write authority.
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## 2026-08-01 — SHOP-02A Product Draft Workflow Architecture

- Added versioned ProductDraft, transition, human decision and deployment-intent JSON contracts, inventory and architecture tests.
- Closed SHOP-01E read foundation; deferred SHOP-01E3D persistent activation; completed SHOP-02A with SHOP-02B next.

## 2026-08-02 — SHOP-02B Product Draft Domain

- Implemented the immutable ProductDraft 1.0.0 domain, deterministic lifecycle evaluation and serialization, exact-revision concurrency, and canonical-JSON SHA-256 idempotency.
- Added a replaceable repository port and isolated non-production in-memory adapter with revision lineage enforcement.
- Added no mutation API, persistent storage, WooCommerce write, or production activation; writes remain `NOT_AUTHORIZED`. SHOP-02C validation and human approval service is next.
- Added no runtime, persistence, mutation route, WooCommerce request or production authorization. Catalog observation remains zero products and one category and does not gate draft development.
# SHOP-02D

- Added GET-only ProductDraft collection, current-revision, and exact-revision resources under `/shopping/product-drafts`.
- Added the failure-isolated, read-only `product_draft_review` Dashboard projection.
- Added a replaceable immutable read-source port and isolated non-production snapshot adapter; default runtime is `UNAVAILABLE`, distinct from an available empty source.
- Added no mutation routes, WooCommerce writes, persistent storage, or production activation. ProductDraft contracts remain 1.0.0 and production writes remain `NOT_AUTHORIZED`.
## 2026-08-03 — SHOP-03A Controlled Commerce Write Architecture

- Added deterministic exact-revision eligibility, explicit source freshness, deny-by-default authorization, immutable controlled plans, and successful-plan idempotency.
- Added only an isolated fake/dry-run Commerce write port adapter and detached JSON-safe preview; real WooCommerce writes remain `NOT_IMPLEMENTED` and `NOT_AUTHORIZED`.
- Kept ProductDraft contracts at 1.0.0 and added no mutation API, persistent write queue, network client, credentials, or Ubuntu dependency. SHOP-03B requires separate architecture and authorization.
# SHOP-03B1 - 2026-08-03

- Added the secret-safe credential provider and synchronous Commerce write transport ports with fail-closed defaults.
- Added the intercepted WooCommerce controlled update adapter, deterministic request/response normalization, and reconciliation evaluator.
- Preserved ProductDraft and deployment-intent 1.0.0 contracts, read/application layers, and API routes.
- Recorded 0 external requests, 0 live writes, and production activation `NOT_AUTHORIZED`.
## UI-01 internal Shopping Homepage

- Added the responsive, accessible internal `GET /homepage` operator surface.
- Consumes only same-origin `GET /dashboard` using GET, a bounded timeout, and
  safe retry; empty and unavailable sources remain distinct.
- Added no frontend framework, public exposure, authentication change, mutation
  API, ProductDraft/deployment contract change, or live Commerce write.

## UI-02 internal Product Management Console

- Added internal `GET /homepage/product-management` and package-local assets.
- Added bounded same-origin ProductDraft reads, client-side filtering, immutable
  revision detail, timeout/retry, accessibility, and distinct empty/unavailable
  states.
- Added no writes, persistence, external dependency, public exposure, contract
  change, Ubuntu change, or production activation.

## PI-009A1 — Deployment Test Gate Repair

- repaired package-relative dependency analysis for package `__init__.py`
- registered the ACTIVATION-01B activation inspector dependency zone
- synchronized dependency-policy schema classification
- permitted the existing read-only `read_ports -> audit_evidence` re-export
- added the reusable deployment regression gate runner
- canonicalized macOS temporary test-home paths
- confined controlled-bootstrap test roots to `/private/tmp`
- final deployment regression: 1133 passed, 9 warnings
- Production remains unauthorized
- remaining blocker: `RUNTIME_SOURCE_ISOLATION`

## PI-009A2 — Runtime Source Isolation Architecture

- selected immutable Git source snapshots instead of introducing a new Python
  packaging system during the Production gate
- preserved existing `runtime/current -> runtime/venvs/<runtime-id>` semantics
- defined `runtime/sources/<runtime-id>` as the matching immutable source
  artifact
- separated source-artifact creation and wrapper cutover into independent human
  authorization gates
- prohibited mutable repository source from the final production import path
- Production remains unauthorized

## PI-009A2 — Application State Isolation Repair

- added a canonical AIControlCenter application data-root resolver
- moved default conversation SQLite state behind `AICONTROLCENTER_DATA_ROOT`
- moved default scheduler SQLite state behind `AICONTROLCENTER_DATA_ROOT`
- explicit configured data roots must be absolute
- preserved development fallback to local `data/` when no data-root environment
  is configured
- validated application import from read-only source with writable state outside
  the source artifact
- existing Candidate `acd80ab9f6ae` is no longer eligible as the final
  immutable-source Production release
- Production remains unauthorized

## PI-009A2 A2.1 — Immutable Runtime Source Tooling

- added JSON-first immutable source artifact build and validation
- added exact source commit and Git tree evidence
- added Git archive and independent content SHA-256 evidence
- added atomic same-parent source publication
- added fail-closed operational-write capability
- added immutable-source launchd wrapper template
- added Python `-P` application path isolation
- removed mutable repository application cwd/PYTHONPATH from the new template
- enforced external application data-root compatibility
- validated read-only application source with external writable SQLite state
- confirmed canonical Runtime bootstrap build is clean-HEAD only
- no operational Runtime or service mutation performed

## PI-009A2 A2.2A — Runtime Candidate Build

- built Runtime Candidate `7b171f135dc7` exactly once through the canonical bootstrap
- source commit: `7b171f135dc7882546bf7f733208778f1aef4943`
- canonical build report SHA-256: `61f88c861a4ecf44a17570e46dc1608866193b987c0448e8eca747d294dfa77b`
- dependency installation passed
- application import passed
- canonical test suite passed
- Runtime metadata and source marker matched
- `pip check` passed
- temporary immutable-source/external-state execution passed
- Runtime pointer remained unchanged
- live service remained healthy without mutation
- Production remains unauthorized

## PI-009A2 A2.2B — Operational Immutable Source Artifact

- created immutable source artifact for Runtime `7b171f135dc7` exactly once
- source commit: `7b171f135dc7882546bf7f733208778f1aef4943`
- manifest SHA-256: `a74977db05ac93bfc5c9e3d621d0748822c5f7f6021f7f0d0fb7c2d3f1983626`
- archive SHA-256: `e227f823b367c7a5ded7ab8b0319a3b4213b60851dbcfabc72e15763850c466f`
- content SHA-256: `f2454fc4e90a860515caa95d7f42382d611da4cae530d534111131ce3e61e6e8`
- Git tree: `4987b22e30b51efd04eb893c4368cd85166ab335`
- source validator passed
- Runtime/source identity passed
- operational immutable-source execution smoke passed
- application state remained external
- active Runtime and live service remained unchanged
- Production remains unauthorized

## PI-009A2 A2.3 — Controlled Live Cutover

- migrated persistent SQLite state after quiescing the old writer
- switched Runtime current from `acd80ab9f6ae` to `7b171f135dc7`
- installed immutable-source wrapper
- restored LaunchDaemon exactly once
- verified immutable source cwd
- verified external operational DB state
- verified HTTP 200 / 200 / 405
- Production remains unauthorized

## PI-009 — Production Authorized

- human Production authorization accepted for Runtime `7b171f135dc7`
- source commit frozen at `7b171f135dc7882546bf7f733208778f1aef4943`
- authorized governance baseline `d3dda82e8f26b6405212071d0713a6e9acb4d6ee`
- final technical gate passed with zero blockers
- deployment regression: 2337 passed, 5 deselected
- launchd/listener/HTTP/state boundary revalidated read-only
- no Runtime activation, migration, wrapper install or service restart performed
- milestone: PI_009_PRODUCTION_AUTHORIZED

## AI-PROVIDER-01B — Authenticated OpenAI Connectivity

- implemented Responses API transport behind ProviderAdapter
- externalized OPENAI_API_KEY credential handling
- validated one authenticated OpenAI smoke request
- preserved fail-closed routing and no cross-provider fallback
- Production Runtime remained unchanged
- Production service was not mutated

## AI-PROVIDER-01C-B — Candidate Runtime and Immutable Source

- built Candidate Runtime `102b8f1fa862` exactly once from commit `102b8f1fa8628d00d25575cb94538826a1a04e10`
- created and validated the matching immutable source artifact exactly once
- passed the canonical dependency, import, test, manifest, content, and immutability gates
- passed the canonical BrainAgent workflow with FakeProvider and zero provider network calls
- did not read `OPENAI_API_KEY`, activate Production, mutate state, or restart the service
- preserved Production Runtime `7b171f135dc7`
- deferred AI-PROVIDER-01C-C promotion and Notion synchronization

## AI-PROVIDER-01 — Production Provider Workflow Validated

- promoted Production Runtime to `102b8f1fa862`
- validated immutable source and external state boundaries
- validated canonical BrainAgent provider routing
- diagnosed the initial smoke failure as a temporary harness-only defect
- completed one separately authorized corrected authenticated smoke
- no application code repair, Runtime rebuild, repromotion or restart was required
- secret exposure: none
# Unreleased

- Implemented SEC-01B generic file-per-provider validation, metadata-only JSON diagnostics, deterministic wrapper injection, environment-backed adapter consumption, and redaction tests. No live installation or Production mutation was performed.
- Repaired the SEC-01C canonical wrapper to restore dynamic immutable Runtime/source validation, external state, isolated `PYTHONPATH`, immutable cwd, and Runtime Python `-P`, without changing the secret helper. The prior attempt consumed two installs and one restart; HTTP recovery did not satisfy immutable convergence and no rollback occurred. R1 did not install or restart. Runtime `102b8f1fa862` has importable `jsonschema`; a new exact human authorization is required.
- Closed SEC-01C as `COMPLETE` at milestone `PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`. R1 converged immutable source; R2 classified the remaining workers config dependency as `VERSIONED_APPLICATION_CONFIG`; R3 froze the matching immutable binding without intended live mutation; R3Q detected drift and consumed zero edits/restarts; and separately authorized R3Q2 preserved the logical value and all other worker.env bytes while applying shell-safe quoting and exactly one restart. Final evidence validates matching immutable source/config, no mutable repository dependency, external state, HTTP `200/200/405`, and redacted `OPENAI_API_KEY` presence with zero provider calls. SEC-01 remains open; SEC-01D is next. Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## 2026-08-13 — Runtime Health Model Production Deployment

### Changed

- Reconciled Runtime Health from the legacy Linux/systemd service model to the
  authoritative Mac Control Plane service topology.
- Added explicit required/optional and lifecycle semantics for the canonical
  API, Telegram and Application Scheduler.
- Runtime Health now distinguishes `RUNNING`, `NOT_DEPLOYED` and stale
  heartbeat state rather than reporting absent Linux units as generic
  unavailable services.
- The topology source of truth is the Mac standalone Production service
  manifest and its Runtime adapter.

### Production

- Promoted immutable release `ed2424e39bb1`
  (`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`).
- Production `runtime/current` converged to the matching Runtime.
- The canonical `core.api.app:app` service converged to the matching immutable
  Source on `127.0.0.1:58081`.
- Local canonical health, Homepage status, public health, public Homepage and
  public Product Management endpoints returned HTTP 200.
- Production `/runtime/health` passed the versioned topology projection gate.

### Safety

- Candidate Runtime and Source were validated in a pinned ephemeral Shadow lane
  without requiring Production pointer activation.
- Candidate cleanup completed with one explicitly authorized SIGTERM and no
  automatic retry or rollback.
- Immutable Source remained bytecode-clean.
- ProductDraft main SQLite database content remained unchanged through
  candidate validation and Production validation.
- No Caddy, WooCommerce or Ubuntu mutation was required for this release.

### Current degraded state

The Runtime Health aggregate intentionally remains `healthy=false` because the
required dedicated Application Scheduler is not yet deployed and its persisted
heartbeat is stale. The canonical API is `RUNNING`, Telegram is optional
`NOT_DEPLOYED`, and topology status is `VALID`.

### Follow-up

- Deploy the dedicated Mac Application Scheduler and establish a fresh
  heartbeat.
- Review Shadow release alignment separately.
- Repair the Shadow explicit-release selector contract.
- Replace legacy automatic external rollback semantics with the current bounded
  governance lifecycle contract.

## 2026-08-15 — PA-05 WooCommerce Headless Adapter v1 validated

- Closed PA-05 at milestone
  `WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`.
- Preserved AIControlCenter as the sole Control Plane and `core.shopping` as
  authority for ProductDraft lifecycle, shopping policy, workflow,
  recommendation, customer automation, governance, and business logic.
  WordPress remains CMS-only; WooCommerce remains commerce-engine-only; the
  replaceable `integrations.woocommerce` adapter remains read-only.
- Kept `ops.macos.runtime.application` as the outer composition root and
  verified `CORE_OPS_IMPORT_COUNT=0` and `CORE_INTEGRATIONS_IMPORT_COUNT=0`.
- Added only `GET /shopping/providers/woocommerce`; no mutation endpoint or
  create/update/delete, execute, retry, or Production mutation action exists.
- Recorded canonical WooCommerce deployment, configuration, and authentication
  as `UNKNOWN`, catalog/API availability as unproven, and default capability
  status as fail-closed `UNAVAILABLE`. Manifest evidence requires exactly one
  validated identity; invalid, ambiguous, or unreadable lookup failures invent
  none.
- Preserved AIControlCenter-owned reserved governance facts through typed,
  boolean-only `CapabilityGovernanceExtensions`; WooCommerce extension facts
  are `commerce_engine_only=true` and `automatic_retry=false`.
- Consolidated unavailable fallbacks in `UnavailableCapabilityObserver` and
  preserved platform-neutral `create_app` plus PA-02/PA-03 outward fail-closed
  compatibility without WooCommerce, n8n, or OpenClaw discovery.
- Final focused validation passed 91 tests after the final architecture
  correction. Canonical deployment regression passed `RC=0` and was executed
  exactly once for PA-05.
- No Production WooCommerce request, external commerce I/O, WordPress,
  WooCommerce, Shopping SQLite, Docker, launchd, `runtime/current`, Caddy,
  Ubuntu, credential, database, plugin, or theme mutation occurred.
- Set the next production sprint to `SHOP-CMS-01 — WordPress + WooCommerce
  Runtime Foundation`, which will establish runtime, persistent-state, secret,
  backup, health/readiness, manifest, and activation architecture before
  storefront exposure. No deployed Production WordPress/WooCommerce runtime,
  public storefront availability, or Notion synchronization is claimed.

## 2026-08-15 — SHOP-CMS-01A Runtime Foundation validated

- Closed SHOP-CMS-01A at milestone
  `SHOPPING_RUNTIME_FOUNDATION_VALIDATED`.
- Established one Mac-owned `shopping-runtime` lifecycle and one hosted
  `woocommerce` capability. AIControlCenter remains the sole Control Plane;
  Ubuntu remains stateless with no shopping or commerce state.
- Validated stopped dedicated-Colima discovery, unavailable active default
  Docker daemon, fail-closed inspection, Mac-owned volumes, logical database
  backup, WordPress archive verification, credential separation,
  loopback-only WordPress, and no MariaDB host port.
- Recorded 72 initial focused passes. Canonical #1 (`3151 passed, 2 failed, 5
  deselected`) exposed two stale service-count expectations, not a runtime
  defect. Corrections passed 2 targeted and 47 focused compatibility tests;
  canonical #2 passed with `RC=0`. Exactly two canonical invocations were
  made. Core direct `ops` and `integrations` imports remain 0.
- Performed no Production, Docker, Colima, WordPress, WooCommerce, commerce
  database, Caddy, or Ubuntu mutation. Claimed no runtime, online WordPress,
  running MariaDB, activated WooCommerce, public storefront, active storefront
  routing, Production activation, or Notion synchronization.
- Set next phase to `SHOP-CMS-01B — bounded Production runtime activation`,
  next milestone `SHOPPING_RUNTIME_ACTIVATED`, and future storefront milestone
  `SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## 2026-08-15 — SHOP-CMS-01B activation-phase correction validated

- Corrected the bounded Docker Compose JSON parser to accept array,
  single-object, NDJSON, and empty-output observations while rejecting
  malformed, scalar, and non-object content fail-closed; valid empty output is
  now distinct from malformed inspection.
- Prevented WooCommerce readiness inference from container health. Derived
  reserved Control Plane ports from the canonical service manifest and made a
  healthy WordPress publisher on a reserved port fail readiness with
  `error_type=PortCollision`.
- Set the desired ingress/Compose contract to
  `SHOPPING_WORDPRESS_PORT=58082`, loopback-only at
  `127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`; MariaDB remains unpublished.
- Recorded the activation history: one dedicated Colima-start authorization
  was consumed exactly once and succeeded. Later read-only reconciliation
  observed stored WordPress and MariaDB containers running/healthy under
  restart policy and persistent volumes; this was not an authorized Compose
  up. The live WordPress publisher remained on reserved FastAPI port `58081`
  and was correctly classified `PortCollision`; no cutover occurred.
- Recorded that the earlier WordPress REST observation reached FastAPI and
  returned its 404, WooCommerce readiness remains unproven, and required
  bootstrap secret files were absent. Service/capability status remains
  `NOT_DEPLOYED`; `SHOPPING_RUNTIME_ACTIVATED=false`.
- Validation evidence: focused exact-code validation `77 passed, 9 warnings`;
  canonical deployment regression `3163 passed, 5 deselected, 447 warnings`,
  `RC=0`, executed exactly once after final code/test corrections; direct core
  imports of `ops` and `integrations` remain 0; implementation commit
  `9fcd02342a37a93874e912e86404f85267e2f0bb`.
- No Production port cutover or WooCommerce activation occurred. No automatic
  retry/rollback, new Production authorization, Docker Compose, WordPress,
  WooCommerce, commerce database, Caddy, or Ubuntu mutation occurred, and no
  Notion synchronization is claimed.
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

## SEC02-FS-01 — Architecture freeze

- Defined the implementation-free, create-only pre-bootstrap Mac filesystem
  authority for the fixed `governance` and `trust` directories.
- Closed the issuer-registry dependency cycle with a dedicated, fresh,
  single-attempt macOS Authorization Services approval boundary.
- Preserved bootstrap, release installation, SEC-02, Governance,
  `ControlledExecutionPort`, and WU09 semantics; canonical regression was not
  required for this documentation-only change.
- Recorded the operational observation that the current governance directory
  has mode `0755`. The frozen exact-`0700`, create-only contract classifies it
  as `UNSAFE_EXISTING`, cannot remediate it, and therefore leaves the current
  operational gate blocked pending a separate later remediation authority.
- Preserved SEC02-FS-02 as a pure plan and read-only validator Work Unit; it
  may confirm the classification but cannot operationally unblock this host.
## 2026-08-30 — SEC-02 filesystem validator and remediation contracts

- Added pure fixed passwd-derived FS-02 plans, immutable observation contracts,
  closed classification, and a Darwin read-only/no-follow adapter.
- Added an immutable governance-only `0755` to `0700` remediation planner,
  one-attempt port contract, and pure postcondition validator with focused tests.
- Defined the separate future approval boundary without a live adapter, installed
  Authorization Services right, Production access, or filesystem mutation.
## 2026-08-30 — SEC02-FS-MACRO-03B1

- Added fixed, zero-argument Authorization Services and privileged governance
  remediation ports with intercepted adapters.
- Replaced the overstated fresh-interaction label with explicit `VERIFIED`,
  `NOT_VERIFIABLE`, `DENIED`, `CANCELED`, and `ERROR` evidence semantics.
- Added one-attempt orchestration that consumes success, failure, uncertainty,
  adapter exceptions, and invalid postconditions without retry.
- Recorded `SMAppService` as the future macOS 13+ helper-management boundary;
  no live binding, right, helper, or filesystem mutation was added.
