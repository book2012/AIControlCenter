# Roadmap

## Protected evidence acquisition repository validation closeout

- [x] Record `ARCHITECTURE_COMMIT=f05c652`,
  `IMPLEMENTATION_COMMIT=07bf1bd`,
  `PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_IMPLEMENTED=true`, and
  `PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_VALIDATED=true`.
- [x] Record `FOCUSED_TEST_GATE=PASS`, `FINAL_CODE_REVIEW_GATE=PASS`,
  `CANONICAL_REGRESSION_GATE=PASS`,
  `CANONICAL_RESULT="4044 passed, 5 deselected, 555 warnings"`, and
  `GIT_DIFF_CHECK_GATE=PASS`. Existing `datetime.utcnow` deprecations and
  pytest `rm_rf` cleanup warnings are non-blocking technical debt/test hygiene.
- [x] Preserve repository fail-closed durability, source/leaf contracts,
  policy, schema, codec, and tests; `DURABILITY_ZERO_INVOCATION_AUTHORITY=true`,
  `DURABILITY_RESULT_NO_CAPABILITY=true`, and
  `DURABILITY_RECEIPT_NO_CAPABILITY=true`. Durable `COMMITTED` facts and Python
  object identity grant no authority.
- [x] Preserve `PRODUCTION_HUMAN_ISSUER_AVAILABLE=false`,
  `PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE=false`,
  `PRODUCTION_ACQUISITION_AVAILABLE=false`, and
  `PRODUCTION_FILESYSTEM_IO_AVAILABLE=false`; both Production entry points
  remain fail-closed before filesystem I/O.
- [x] Preserve `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `FILESYSTEM_IO_PERFORMED=false`,
  `MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
  `CONTROLLED_EXECUTION_PORT_COUPLED=false`,
  `GOVERNANCE_CORE_CHANGED=false`, and `SEC_02_CHANGED=false`.
- [x] Preserve `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `MARIADB_CONTINUITY_RECOVERY_INTEGRATED_PROGRAM=IN_PROGRESS`,
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [ ] Next operational objective:
  `ACTUAL_HISTORICAL_EVIDENCE_ACQUISITION_AND_OFFLINE_EVALUATION`. Actual
  protected-source acquisition remains subject to separate authorization and
  has not occurred.
- [ ] Next step: `DOCUMENTATION_GIT_CLOSEOUT`.

## Offline historical evidence evaluator repository closeout

- [x] Record `IMPLEMENTATION_COMMIT=b51092f`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_IMPLEMENTED=true`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_VALIDATED=true`,
  `OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`,
  and `FINAL_OFFLINE_EVALUATOR_ARCHITECTURE_REVIEW_GATE=PASS`.
- [x] Record focused `14 passed in 0.03s`,
  `CANONICAL_REGRESSION_GATE=PASS`,
  `CANONICAL_RESULT="4018 passed, 5 deselected"`, 547 warnings,
  `CANONICAL_RC=0`, `WORKTREE_AFTER_IMPLEMENTATION_PUSH=CLEAN`, `AHEAD=0`, and
  `BEHIND=0`.
- [x] Record repository-only, value-free, fail-closed semantics;
  immutable/slotted factual inputs and results; no caller positive-result
  injection; existing `EvidenceAcquisitionCategory` reuse; provenance required
  for `EVIDENCE_COMPLETE`; and no promotion of `EVIDENCE_COMPLETE` to
  operational `RECOVER` sufficiency.
- [x] Freeze exactly five data identity categories: `WORDPRESS_IDENTITY`,
  `SITE_IDENTITY`, `APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`,
  and `CLOSED_TABLE_CHARACTERISTICS`.
- [x] Freeze exactly three continuity lineage categories: `LOGICAL_EXPORT`,
  `RECOVERY_ARTIFACT`, and `PERSISTENT_VOLUME_SNAPSHOT`.
- [x] Preserve `Source != Acquisition != Fact != OfflineEvaluation !=
  RECOVERDecision != ProductionAccess != CredentialValidation != Authorization
  != Authority`; zero mutation budget; no filesystem I/O, protected-source
  acquisition, network, MariaDB/SQL connection, or Production access; Mac-only
  Control Plane authority; Ubuntu zero authority; unchanged Governance/SEC-02;
  and uncoupled `ControlledExecutionPort`.
- [x] Preserve exactly `FILESYSTEM_IO_PERFORMED=false`,
  `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [ ] Next architecture gate, before actual acquisition: do not open or read
  actual protected evidence content. Freeze exact protected leaf metadata,
  regular non-symlink leaf, permissions no broader than `0600`, trusted
  UID/GID, stable FD/inode/device binding, TOCTOU-resistant acquisition, exact
  fixed source slot, one-shot human-authorized acquisition, maximum one
  acquisition per authorization, and no enumeration, candidates, fallback,
  retry, recovery, or authorization reuse. The current directory metadata
  snapshot is point-in-time only and supplies neither stable binding nor
  content-acquisition authority.
- [ ] No claim is made of trusted source contents acquired, protected evidence
  verified, Production readiness, MariaDB credential continuity validated, or
  Shopping runtime activation.
- [ ] Next step: final six-root-documentation review.

## Filesystem Target Metadata Snapshot repository implementation closeout

- [x] Record architecture `44f4ef0`, implementation `e9a3645`, focused
  `122 passed in 0.09s`, canonical `4004 passed, 5 deselected, 543 warnings`,
  `CANONICAL_RC=0`, and successful, clean, synchronized implementation Git
  closeout (`IMPLEMENTATION_COMMIT_RC=0`, `IMPLEMENTATION_PUSH_RC=0`,
  `WORKTREE_STATE=CLEAN`, `AHEAD=0`, `BEHIND=0`).
- [x] Mark `FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_IMPLEMENTED=true`
  and `FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_VALIDATED=true`.
- [x] Record the exact two-field request, no caller outcome/classification,
  Mac adapter observation ownership, zero observations for invalid requests,
  at most one exact-unchanged-target `os.lstat`, and consumption limited to
  `st_mode`, `st_uid`, and `st_gid`.
- [x] Record `reason` as the sole classifier input, repository-owned canonical
  mappings, and the sole positive vocabulary
  `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`; exclude `SAFE_BOUND` and
  `METADATA_SAFE_AND_STABLY_BOUND`.
- [x] Preserve the factual, point-in-time, zero-authority result and exact
  `stable_handle_bound=false`, `toctou_closed=false`, and
  `fd_inode_device_bound=false`, without claims of stable binding, TOCTOU
  closure, FD/inode/device binding, acquisition, admission, verification,
  `RECOVER` sufficiency, or Production readiness/authorization.
- [x] Preserve strict semantic separation, all mandated false/unknown
  operational state, Mac sole Control Plane, Ubuntu zero role/authority,
  unchanged Governance/SEC-02, uncoupled `ControlledExecutionPort`, and
  mutation budget zero.
- [x] Keep `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; do not decrement Macro-WU count.
- [ ] Next step: documentation Git closeout.

## Trusted Ownership Expectation repository implementation/validation closeout

- [x] Record architecture freeze `c9bc387`, implementation `220c170`, focused
  `26 passed in 0.03s`, final implementation architecture review `PASS`,
  canonical regression `PASS`, canonical
  `3882 passed, 5 deselected, 539 warnings in 136.33s`, `CANONICAL_RC=0`, and
  closed/clean/synchronized implementation Git closeout.
- [x] Mark `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_IMPLEMENTED=true` and
  `TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_VALIDATED=true`.
- [x] Record the frozen implementation semantics: existing resolved home,
  `expected_uid` from `bound_uid`, no added UID/passwd observations, exact
  `staff` policy, at most one exact group lookup using only `gr_gid`, exact
  non-negative `int`, fail closed, no retry/fallback/alternate, immutable
  slotted exact two-field value, and zero authority or filesystem/access scope.
- [x] Preserve `TRUSTED_GID_SOURCE_ESTABLISHED=false`, every required
  false/unknown operational fact: `TRUSTED_HOME_VALUE_ESTABLISHED=false`,
  `ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`,
  `FILESYSTEM_IO_PERFORMED=false`, `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; preserve Mac sole Control
  Plane, Ubuntu zero role and authority, unchanged Governance/SEC-02, uncoupled
  `ControlledExecutionPort`, mutation budget zero, `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [ ] Next separately gated repository milestone:
  `MACRO_WU_06_FILESYSTEM_TARGET_METADATA_SNAPSHOT_BOUNDARY`, separate from
  ownership expectation, concrete path, evidence acquisition, and Production
  authority. It may later define the request, snapshot, and exact-target
  single-`lstat` adapter; do not implement them in this closeout.

## Trusted Ownership Expectation Architecture Contract (historical freeze)

- [x] Complete architecture discovery and freeze the separate ownership
  expectation issuer boundary without implementing or executing it.
- [x] Freeze `expected_uid` as the already-resolved
  `ResolvedTrustedMacAccountHome.bound_uid`; prohibit resolver construction or
  execution, additional UID/passwd observations, caller UID, and ambient,
  environment, `HOME`, argv, or JSON identity authority.
- [x] Freeze the repository-owned exact Mac application-group policy
  `TRUSTED_APPLICATION_GROUP_NAME="staff"` and exactly one
  `grp.getgrnam("staff")` lookup using only `gr_gid`.
- [x] Freeze fail-closed exact-type, non-negative GID validation with no
  ambient/supplementary/passwd group authority, enumeration, candidate,
  alternate, retry, fallback, or best-effort behavior.
- [x] Freeze the ordered lookup budget: the existing resolver retains maximum
  one platform, real UID, effective UID, and bound-UID passwd observation in
  its own boundary; the issuer consumes its resolved result, makes zero
  additional UID/passwd observations, and makes at most one exact group lookup.
- [x] Freeze immutable, slotted, factual, zero-authority
  `TrustedOwnershipExpectation` with exactly `expected_uid: int` and
  `expected_gid: int`; possession and object identity grant no authority.
- [x] Preserve strict semantic separation and dependency order from concrete
  path plus ownership expectation, through a future snapshot request, to at
  most one exact-target `lstat`.
- [x] Preserve the existing single-`lstat` and TOCTOU non-claim contracts,
  Mac sole Control Plane, Ubuntu zero authority, unchanged Governance/SEC-02,
  uncoupled `ControlledExecutionPort`, mutation budget zero, and all required
  false/unknown program state and Macro-WU-06 accounting.
- [x] After architecture Git closeout, implement the separately gated
  `MACRO_WU_06_TRUSTED_OWNERSHIP_EXPECTATION_IMPLEMENTATION`. The repository
  issuer is implemented; this does not establish the trusted GID source
  operationally.

No focused or canonical validation is run for this documentation-only work.

## Concrete Protected-Evidence Filesystem Binding Architecture Contract

- [x] Discover and reuse the repository's fixed-slot, concrete-location,
  metadata outcome/reason, protected-parent, ownership, mode, symlink, and
  future FD/inode requirements.
- [x] Freeze `ConcreteProtectedEvidencePath` as lexical and zero-authority;
  possession and object identity establish neither provenance nor authority.
- [x] Separate filesystem binding, existence, inspection, safety, content
  acquisition, admission, verification, and authority.
- [x] Freeze one exact target and `0..1` total filesystem observations: one
  `lstat` only after valid request input; no `stat`, parent walk, leaf lookup,
  retry, fallback, recovery, enumeration, or candidate iteration.
- [x] Require a non-symlink directory, exact `0700`, and structurally explicit
  expected UID and GID at this layer, while prohibiting arbitrary caller or
  ambient identity as trusted authority and recording that no operational
  trusted ownership expectation issuer or trusted GID source exists; reserve
  regular-file/`0600`, non-empty content, and
  FD/inode/device binding for later leaf/acquisition boundaries.
- [x] Freeze the distinct positive snapshot concept
  `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`; prohibit positive `SAFE_BOUND` and
  `METADATA_SAFE_AND_STABLY_BOUND`; preserve point-in-time, immutable, slotted,
  zero-authority semantics, fail-closed errors, `stable_handle_bound=false`,
  `TOCTOU_CLOSED=false`, `FD_INODE_DEVICE_BOUND=false`, zero content
  opens/reads, and mutation budget 0.
- [x] Preserve no runtime resolver execution, no environment/HOME/argv/caller
  path authority, unchanged Governance/SEC-02, uncoupled
  `ControlledExecutionPort`, no external infrastructure or Production access,
  and unchanged Macro-WU-06 accounting.
- [x] Architecture-freeze the separate trusted ownership expectation boundary.
  No positive operational ownership-safe claim or binding adapter
  implementation is permitted until its separately gated implementation is
  complete; protected evidence and Production remain uninspected.

No tests or canonical validation are run for this architecture-only work.

## Concrete Protected-Evidence Path Composer Repository — documentation closeout

- [x] Record architecture contract `254241a` before implementation `2810c0c`.
- [x] Record repository implementation and validation capability as true.
- [x] Record focused `11 passed in 0.03s`, Final Architecture Review `PASS`,
  canonical regression `PASS`, canonical
  `3856 passed, 5 deselected, 535 warnings in 133.68s (0:02:13)`, and
  `CANONICAL_RC=0`.
- [x] Record implementation Git closeout `CLOSED`, clean worktree, `AHEAD=0`,
  and `BEHIND=0`.
- [x] Preserve lexical-only, zero-authority semantics: no provenance,
  authorization, capability, verification evidence, filesystem existence or
  safety evidence, `RECOVER` sufficiency, Production authorization/readiness,
  or security-boundary meaning; Python identity grants nothing and downstream
  sensitive boundaries validate independently.
- [x] Preserve trusted home, absolute/concrete path, filesystem I/O,
  protected-source access, Production access, and `RECOVER` sufficiency as
  false; offline acquisition as unknown; insufficient `RECOVER`; and no
  SM-01B-02D-06 semantics change.
- [x] Preserve Mac sole Control Plane, Ubuntu zero role and authority,
  unchanged Governance/SEC-02, and uncoupled `ControlledExecutionPort`.
- [x] Keep `MACRO_WU_06=IN_PROGRESS`, seven authoritative WUs remaining, and
  range WU06-WU12.
- [ ] Next: documentation read-only review. Actual protected evidence and
  Production remain out of scope and unaccessed.

No focused or canonical validation is rerun for this documentation-only work.

## Concrete Protected-Evidence Path Composition Architecture Contract (historical implementation next-step)

- [x] Discover the authoritative `ResolvedTrustedMacAccountHome`,
  `RuntimeHomeResolver`, suffix policy/identity/constant, and adjacent
  source/profile/location contracts without executing runtime observation.
- [x] Freeze a separate composer that consumes an already-existing resolved
  home and never executes the resolver or observes platform, UID, effective
  UID, or passwd state.
- [x] Freeze the exact repository-owned suffix and reject caller, environment,
  argv, alternate, candidate, fallback, or enumerated suffix/path authority.
- [x] Freeze exact string composition: append the suffix directly when
  `passwd_home` ends with `/`; otherwise insert exactly one `/` before it.
- [x] Preserve the passwd home and suffix unchanged; prohibit path libraries,
  joining, expansion, stripping, normalization, absolutization, resolution,
  realpath, and canonicalization.
- [x] Prohibit all filesystem observation, metadata inspection, protected-source
  access, Production access, execution, and mutation.
- [x] Freeze `ConcreteProtectedEvidencePath` as immutable and slotted with only
  `concrete_path`; preserve zero authority, reject unforgeable-provenance or
  security-boundary semantics, and require independent downstream validation.
- [x] Preserve Mac sole Control Plane, Ubuntu zero role/authority, unchanged
  Governance and SEC-02, uncoupled `ControlledExecutionPort`, all required
  false/unknown program facts, `MACRO_WU_06=IN_PROGRESS`, seven remaining WUs,
  and range WU06-WU12.
- [x] Historically, after architecture Git closeout, implement
  `MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSITION_IMPLEMENTATION` as
  repository-only and zero-authority, with no protected-source or Production
  access. Completed under architecture commit `254241a`, implementation commit
  `2810c0c`, and documentation closeout commit `94c36fb`; the current next
  repository boundary is
  `MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_FILESYSTEM_BINDING`.

No focused or canonical validation is run for this architecture-only work.

## Trusted Mac Account-Home Runtime Resolver Implementation — documentation closeout

- [x] Close only
  `MACRO_WU_06_TRUSTED_MAC_ACCOUNT_HOME_RUNTIME_RESOLVER_IMPLEMENTATION=CLOSED`, based
  on architecture contract `41963c1`, clarification `cf9c34d`, and
  implementation `288eb68`.
- [x] Freeze `RUNTIME_HOME_RESOLVER_REPOSITORY_IMPLEMENTED=true` and
  `RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true`; record focused
  `28 passed in 0.03s`, Final Architecture Review `PASS`, canonical
  `3845 passed, 5 deselected, 531 warnings`, and `CANONICAL_RC=0`.
- [x] Preserve exact-once platform observation and exact `Darwin` validation
  before UID observation; exact-once real/effective UID observations before
  root validation; reject either zero; require and bind equality; exact-once
  `pwd.getpwuid(bound_uid)`.
- [x] Require exact `str` `pw_dir` (reject subclasses), non-empty, NUL-free,
  lexically absolute POSIX form, preserved unchanged.
- [x] Preserve fail-closed behavior and prohibit retry, fallback, reconnect,
  recovery, `getpwnam`, caller/environment/HOME/argv home authority,
  `Path.home`, `expanduser`, strip, normalization, resolution/realpath/
  canonicalization, all filesystem probing and existence/type/symlink checks,
  metadata and ownership/mode inspection, and path enumeration.
- [x] Preserve immutable, slotted, exactly two-field
  `ResolvedTrustedMacAccountHome`; prohibit supported direct construction and
  arbitrary UID/home factories. Keep it zero-authority and neither unforgeable
  provenance, authorization, capability, admission/verification evidence,
  `RECOVER` sufficiency, Production authorization/readiness, nor a security
  boundary; require independent downstream validation.
- [x] Preserve exact semantic separation across policy, identity observation,
  resolver, resolved value, suffix policy/value, concrete path, existence,
  inspection, safety, acquisition, admission, verification, and authority.
- [x] Preserve Mac sole Control Plane, Ubuntu zero resolver authority, unchanged
  Governance/SEC-02, and uncoupled `ControlledExecutionPort`.
- [x] Preserve no runtime execution/trusted home/path/access claim:
  `TRUSTED_HOME_VALUE_ESTABLISHED=false`, `ABSOLUTE_PATH_ESTABLISHED=false`,
  `CONCRETE_PATH_VALUE_ESTABLISHED=false`, `FILESYSTEM_IO_PERFORMED=false`,
  `PROTECTED_SOURCE_ACCESS_PERFORMED=false`,
  `PRODUCTION_ACCESS_PERFORMED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, insufficient `RECOVER`, and no
  SM-01B-02D-06 semantic change.
- [x] Keep `MACRO_WU_06=IN_PROGRESS`, seven authoritative WUs remaining, and
  WU06-WU12; actual historical evidence acquisition and offline evaluation are
  still required before Macro-WU06 closure.
- [x] Historical next step: read-only architecture discovery/freeze for composing
  `ResolvedTrustedMacAccountHome` and the frozen exact protected-evidence suffix
  into distinct zero-authority `ConcreteProtectedEvidencePath`. Do not inspect
  existence or metadata, call `stat`/`lstat`, access/acquire protected evidence,
  grant authority, or access Production. This composer work later completed
  under commits `254241a`, `2810c0c`, and `94c36fb`; the current next repository
  boundary is `MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_FILESYSTEM_BINDING`.

No focused or canonical validation is rerun for this documentation-only work.

## Trusted Mac Account-Home Runtime Resolver Architecture Contract

- [x] Pass architecture discovery and require a distinct runtime resolution
  boundary without implementing or executing it.
- [x] Freeze exact ordering: exactly one `platform.system()` observation and
  exact returned value `Darwin` validation; one real UID and one effective UID
  observation; no identity binding until both succeed; non-root equality
  validation; then exactly one bound-UID passwd lookup.
- [x] Freeze fail-closed behavior with no retry, fallback, reconnect, recovery,
  alternate account lookup, `getpwnam`, or caller/environment/argv identity or
  home input.
- [x] Require `pw_dir` to be present, a non-empty NUL-free string, and lexically
  absolute as a POSIX path while preserving the string unchanged.
- [x] Prohibit stripping, expansion, normalization, resolution,
  canonicalization, metadata inspection, existence/type checks, symlink or
  ownership/mode inspection, enumeration, and every filesystem probe.
- [x] Freeze immutable zero-authority `ResolvedTrustedMacAccountHome` with only
  bound UID and validated passwd-derived home string; establish no downstream
  path, filesystem, evidence, `RECOVER`, Production, readiness, or authority
  fact.
- [x] Preserve strict semantic separation, Mac sole Control Plane, Ubuntu zero
  resolver role and authority, unchanged Governance/SEC-02, and no
  `ControlledExecutionPort` coupling.
- [x] Preserve resolver/trusted-home/path/access facts as false, offline
  acquisition as unknown, insufficient `RECOVER`, no SM-01B-02D-06 semantic
  change, `MACRO_WU_06=IN_PROGRESS`, seven remaining WUs, and range WU06-WU12.
- [ ] Next step: read-only architecture review. Resolver implementation remains
  separately gated and unavailable.

No focused or canonical validation is run for this architecture-only work.

## Trusted Mac Account-Home Repository Policy Implementation — documentation closeout

- [x] Preserve chronology: architecture contract/freeze
  `d9def864c83e3660ce9e6afa646ee4f5851934b3`, followed by implementation and Git
  closeout `d07054901b5c3eccac401e90afa4126a9bda9515`.
- [x] Implement symbolic, zero-authority Darwin-only/non-root policy with real
  UID from `os.getuid()`, effective UID from `os.geteuid()`, required equality,
  and future lookup rule `pwd.getpwuid(bound_uid).pw_dir`.
- [x] Preserve zero runtime UID/passwd lookup execution and no runtime home
  resolver, trusted home value, absolute/concrete path, filesystem I/O,
  protected-source/Production access, metadata inspection, evidence acquisition,
  admission, verification, or authority.
- [x] Preserve policy != runtime identity observation != resolver != trusted
  home != suffix != absolute path composition != existence != inspection !=
  safety != acquisition != admission != verification != authority.
- [x] Record focused `6 passed in 0.06s`, Final Architecture Review `PASS`,
  canonical `3817 passed, 5 deselected, 527 warnings in 133.93s`,
  `CANONICAL_RC=0`, and successful clean/synchronized Git closeout.
- [x] Preserve all required false/unknown downstream facts,
  `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, Mac sole Control Plane, Ubuntu
  zero authority, `MACRO_WU_06=IN_PROGRESS`, seven remaining authoritative WUs,
  and range WU06-WU12.
- [ ] Next repository activity: read-only architecture discovery/freeze for the
  runtime trusted Mac account-home resolver boundary; do not describe or treat
  the resolver as implemented.
- [ ] Next Production-relevant milestone: Macro-WU06 Actual Historical Evidence
  Acquisition + Offline Evaluation. Production validation and Shopping runtime
  activation remain unestablished.

No focused or canonical validation is rerun for this documentation-only work.

## Trusted Mac Account-Home Policy Architecture Contract

- [x] Freeze a Darwin-only, non-root process identity policy.
- [x] Define `os.getuid()` as real UID and `os.geteuid()` as effective UID;
  require equality and bind the single equal UID as account identity.
- [x] Freeze the future lookup rule as `pwd.getpwuid(bound_uid).pw_dir` without
  executing it or implementing a runtime resolver.
- [x] Reject `HOME`, `Path.home`, `expanduser`, caller/argv home or path,
  fallback, enumeration, and candidate iteration as authority.
- [x] Keep existing Governance, bootstrap, Shopping, and runtime home patterns
  as design evidence only; preserve unchanged Governance/SEC-02 and no
  `ControlledExecutionPort` coupling.
- [x] Preserve the exact suffix as relative to a future trusted home while
  establishing no trusted home, absolute/concrete path, filesystem I/O,
  protected-source/Production access, downstream evidence fact, or authority.
- [x] Preserve Mac sole Control Plane, stateless zero-authority Ubuntu,
  insufficient `RECOVER`, `MACRO_WU_06=IN_PROGRESS`, seven remaining
  authoritative WUs, and range WU06-WU12.
- [x] Subsequently implement and Git-close the symbolic, zero-authority
  repository-owned trusted Mac account-home policy. Runtime account-home
  resolution remains a distinct future boundary; neither the contract nor the
  implementation establishes a trusted home value or concrete protected-evidence
  path.

No focused or canonical validation is run for this architecture-only work.

## Authoritative Mac Protected Evidence Suffix Policy Implementation — documentation closeout

- [x] Establish the exact suffix architecture contract first at
  `e1e66ac17b3506a4bff4bd0a9322fc7360ca6536`.
- [x] Implement and Git-close
  `MACRO_WU_06_AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY_IMPLEMENTATION`
  at `6c7b18ab942024120b06d1eb0235c7b67b7916df`.
- [x] Own exactly the relative suffix
  `Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`
  without establishing an absolute/concrete path or runtime home resolver.
- [x] Preserve strict identity/value/resolution/path/existence/inspection/safety/
  acquisition/admission/verification/authority separation and every caller,
  environment/HOME, argv, fallback, enumeration, and iteration prohibition.
- [x] Preserve zero filesystem I/O, zero protected-source/Production access, no
  MariaDB/SQL/PyMySQL or Docker/Colima mutation, no Ubuntu authority, unchanged
  Governance/SEC-02, no `ControlledExecutionPort`, and isolated legacy observer.
- [x] Record focused `6 passed in 0.06s`, Final Architecture Review `PASS`,
  canonical `3811 passed, 5 deselected, 523 warnings in 134.83s`, and
  `CANONICAL_RC=0`; warnings were non-failing.
- [x] Keep every required downstream fact false/unestablished,
  `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`, insufficient `RECOVER`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- [x] Keep Mac AIControlCenter sole Control Plane, Ubuntu stateless with zero
  Control Plane authority, `MACRO_WU_06=IN_PROGRESS`, seven authoritative WUs
  remaining, and range WU06-WU12.
- [ ] Next repository activity: architecture-discover/freeze the trusted Mac
  account-home resolution boundary before any concrete path composition or
  runtime resolver.
- [ ] Next Production-relevant milestone: complete actual historical evidence
  acquisition and offline evaluation under Macro-WU06.

No focused or canonical validation is rerun for this documentation-only work.

## Protected External Evidence Exact Suffix Architecture Contract

- [x] Resolve
  `NO_REPOSITORY_OWNED_PROTECTED_EXTERNAL_EVIDENCE_SPECIFIC_EXACT_SUFFIX_CONTRACT`
  with a dedicated repository architecture contract.
- [x] Establish the exact relative suffix
  `Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`
  for future composition with `TRUSTED_MAC_ACCOUNT_HOME`.
- [x] Preserve suffix-policy identity != exact suffix value != runtime home
  resolution != concrete path != existence != inspection != safety !=
  acquisition != admission != verification != authority.
- [x] Preserve all caller/environment/HOME/argv/fallback/enumeration/iteration
  path-authority prohibitions and zero authority.
- [x] Preserve Mac sole Control Plane, stateless zero-authority Ubuntu,
  unchanged Governance/SEC-02 semantics, and no `ControlledExecutionPort`
  coupling.
- [x] Preserve all false/unknown downstream evidence, Production, and runtime
  facts; keep `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [x] Subsequently completed repository milestone:
  `MACRO_WU_06_AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY_IMPLEMENTATION`.
  This did not implement a trusted account-home resolver.

No focused or canonical validation is run for this architecture-only work.

## Authoritative Mac Base Path Policy Implementation — documentation closeout

- [x] Close `MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION` as a
  repository-only implementation/documentation submilestone; keep
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [x] Record symbolic-only policy identity, repository-owned value-free policy,
  immutable closed mapping from `ProtectedExternalEvidenceBaseLocationIdentity`,
  and canonical factory accepting no caller path, home, or suffix input.
- [x] Record no runtime home resolver; no production/source use of `Path.home`,
  `HOME`, `os.environ`, `os.getenv`, `sys.argv`, `pwd.getpwuid`, `os.getuid`, or
  `os.getgid`; zero filesystem I/O; and no filesystem, metadata, content, or
  Production adapter.
- [x] Preserve zero authorization/capability/execution/mutation/retry/reconnect/
  rollback/acquisition/admission/verification authority; unchanged Governance
  core and SEC-02 semantics; and no `ControlledExecutionPort` coupling.
- [x] Preserve policy identity != exact suffix policy != runtime home resolution
  != concrete path != existence != inspection != safety != acquisition !=
  admission != verification != authority. Establish no exact suffix, directory,
  path, source existence, metadata fact, or Production access.
- [x] Record commit `ab9de4a08c35de3805983346cf7f1a6d9accccdb`, push `PASS`,
  `AHEAD=0`, `BEHIND=0`, focused `6 passed in 0.05s`, architecture review `PASS`,
  canonical `3805 passed, 5 deselected, 519 warnings`, and `CANONICAL_RC=0`;
  warnings are non-failing.
- [x] Preserve `BASE_PATH_POLICY_LAYER_REQUIRED=true`,
  `AUTHORITATIVE_BASE_PATH_POLICY_DEFINED=true`, every required false/unknown
  downstream fact, `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- [x] Subsequently establish the exact relative protected-evidence suffix in a
  dedicated architecture contract without adding a concrete path or runtime
  resolver.

No focused or canonical validation is rerun for this documentation-only work.

## Protected External Evidence Source Access and Metadata Inspection Boundary — documentation closeout

- [x] Close the named boundary as a repository implementation submilestone only;
  preserve `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.
- [x] Preserve Mac sole Control Plane, stateless zero-authority Ubuntu, and the
  repository-owned, path-free, zero-authority request boundary with symbolic
  identity only and `mutation_budget=0`.
- [x] Preserve exact request-instance binding (not dataclass equality),
  pre-consumption same-source/different-request and cross-source rejection,
  non-consuming mismatch, at-most-once original success, rejected reuse, and
  exactly-once concurrent consumption.
- [x] Keep inert test provenance and inert `SAFE_BOUND` distinct from operational
  evidence; preserve no supported `HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION`
  issuer and false operational metadata/path issuer and Production inspection
  availability flags.
- [x] Keep legacy `observe_fixed_protected_source` isolated/unreachable; preserve
  no caller path/callback, HOME/environment, argv, fallback, enumeration, or
  iteration authority; unchanged Governance/SEC-02; no `ControlledExecutionPort`.
- [x] Record commit `daff799d35709da31434ebb280e0771073b12b52`, push `PASS`,
  focused `27 passed`, review `PASS`, canonical
  `3799 passed, 5 deselected, 515 warnings`, and `CANONICAL_RC=0`; warnings are
  not failures.
- [x] Record no Production/protected-source access, metadata inspection, content
  acquisition, or MariaDB/SQL/PyMySQL/Docker/Colima/Ubuntu activity.
- [x] Freeze `BASE_PATH_POLICY_LAYER_REQUIRED=YES`, proposed
  `AuthoritativeMacProtectedEvidenceBasePathPolicy` and
  `AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity`; retain the existing
  base-location identity as symbolic-only input.
- [x] Preserve repository policy != runtime account-home resolution != concrete
  path != existence != inspection != safety. Permit a future trusted
  `pwd.getpwuid(os.getuid()).pw_dir` resolver only after exact suffix policy;
  select no suffix/path now.
- [x] Preserve all frozen false/unknown path, existence, metadata, acquisition,
  path-authority, `RECOVER`, Production-readiness, and runtime facts.
- [x] Subsequently completed:
  `MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION`, repository-only,
  value-free, zero filesystem I/O, zero
  Production/protected-source access, no path resolution, source-existence check,
  metadata inspection, or runtime resolver. The exact protected-evidence suffix remains unresolved and
  must not be guessed.

No focused or canonical validation is rerun for this documentation-only work.

## Protected External Evidence Concrete Source Location Descriptor — documentation closeout

- [x] Implement exactly four closed symbolic Concrete Source Location identities
  with immutable one-to-one mapping from the four Fixed Source Slot identities.
- [x] Preserve descriptor/path/existence/metadata/acquisition/admission/
  verification/authority separation and symbolic-only base identity.
- [x] Preserve every path-authority prohibition and classify reverse lookup only
  as deterministic closed-mapping traversal for canonical profile recovery.
- [x] Reuse Fixed Source Slot protection requirements as future policy only,
  without claiming operational satisfaction.
- [x] Pass focused validation: `7 passed in 0.06s`.
- [x] Pass authoritative final architecture review.
- [x] Run canonical exactly once: `3772 passed, 5 deselected, 511 warnings in
  134.12s (0:02:14)`, `CANONICAL_RC=0`; no correction or rerun followed.
- [x] Complete implementation Git closeout at
  `c3760d2fd9bb0810d3e285ec203b40e5b7b77814`, `AHEAD=0`, `BEHIND=0`.
- [x] Preserve all governance, architecture, Shopping, Control Plane, no-activity,
  and Macro-WU-06 facts; do not start or imply Macro-WU-07.
- [x] Complete exact-six-document documentation Git closeout at `7826c16c530ae696691b9476ddcec0bb4bd5768d` with normal push and `AHEAD=0`, `BEHIND=0`.

No focused or canonical validation is rerun for this documentation-only work.

## Protected External Evidence Fixed Source Slot — prior documentation closeout

- [x] Implement exactly four symbolic
  `ProtectedExternalEvidenceFixedSourceSlotIdentity` values and the immutable,
  repository-owned, one-to-one mapping from
  `ProtectedExternalEvidenceSourceProfileIdentity`; preserve
  `CALLER_SLOT_SELECTION_ALLOWED=false` and `CALLER_PATH_INJECTION_ALLOWED=false`.
- [x] Preserve the complete semantic chain through Fixed Source Slot Identity,
  Concrete Source Location, Source Existence, Metadata Safety, Content
  Acquisition, Admission, Verification, and Authority; keep Fixed Source Slot
  Identity symbolic only and all required downstream facts false or unknown.
- [x] Record protection requirements strictly as future policy and preserve all
  Mac ownership, mode, leaf, uid/gid, binding, authorization, one-shot,
  no-fallback, no-enumeration, no-environment-authority, and no-secret-transport,
  logging, or hashing requirements without claiming operational satisfaction.
- [x] Pass focused validation: `40 passed in 0.14s`.
- [x] Pass authoritative final architecture review.
- [x] Run canonical exactly once: `3765 passed, 5 deselected, 507 warnings in
  134.47s`, `CANONICAL_RC=0`; no code/test correction followed and canonical was
  not rerun.
- [x] Complete implementation commit
  `7ccebffcce281590d57f4f8fc93d9e53032bb822`, implementation push, and Git
  closeout with `AHEAD=0`, `BEHIND=0`.
- [x] Preserve all architecture, governance, exact-six-action, target-only
  provisioning, macro-program, and operational no-activity facts; Macro-WU-06
  remains `IN_PROGRESS` and Macro-WU-07 has not started.
- [x] Complete exact-six-document documentation Git closeout.

No focused or canonical validation is rerun for this documentation-only work.

## Protected External Evidence Source Profile — prior documentation closeout

- [x] Complete protected source profile discovery/freeze.
- [x] Complete exact four-file implementation of four closed symbolic
  `ProtectedExternalEvidenceSourceProfileIdentity` values and immutable,
  repository-owned, one-to-one `BUNDLE_TO_PROTECTED_SOURCE_PROFILE_MAPPING`
  from the existing four `EvidenceReferenceIdentityClass` bundle identities;
  keep caller selection closed.
- [x] Preserve `repository_only=true`, `value_free=true`, `fail_closed=true`,
  `zero_authority=true`, and
  `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`.
- [x] Preserve `EvidenceAcquisitionCategory` != source bundle identity !=
  protected source profile identity != concrete source location != source
  existence != metadata safety != acquisition != admission != verification !=
  authority.
- [x] Preserve false concrete-location, source-existence, historical-evidence,
  metadata-safety, acquired-content, admission, verification, and authority
  facts; preserve `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN` and
  `PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`.
- [x] Pass focused `37 passed in 0.13s` and authoritative final architecture
  review `PASS`.
- [x] Run canonical exactly once after review: `3753 passed, 5 deselected, 503
  warnings`, `CANONICAL_RC=0`; make no later code/test correction and do not
  rerun canonical.
- [x] Complete implementation commit
  `a206a6aad23ba79a548bf3f7498a4c3883fec067`, normal push, implementation Git
  closeout, and verify `AHEAD=0`, `BEHIND=0`.
- [x] Preserve Mac AIControlCenter as sole Control Plane and Ubuntu as a
  stateless infrastructure worker with no Control Plane authority.
- [x] Preserve all governance, exact-six-action, target-only provisioning, and
  operational no-activity facts.
- [x] Record that actual historical evidence acquisition and offline evaluation
  have not occurred and evidence existence, concrete location, and metadata
  safety are not established.
- [x] Keep this submilestone inside authoritative Macro-WU-06; preserve
  `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; retain authoritative Macro-WU-07 as
  the later factual `RECOVER_EVIDENCE_SUFFICIENT` decision.
- [x] Complete exact-six-document documentation Git closeout.

No focused or canonical validation is rerun for this documentation-only work.

## MariaDB Continuity Evidence Source Binding — prior documentation closeout

- [x] Freeze four closed typed protected-source bundle identities and exactly
  twelve total unique `EvidenceAcquisitionCategory` mappings.
- [x] Preserve immutable `MappingProxyType` `CATEGORY_TO_BUNDLE_MAPPING` and
  `CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`.
- [x] Close caller bundle/category construction: `_canonical_bundle` accepts
  identity only, derives exclusively from the mapping, and no helper accepts
  caller-supplied category tuples.
- [x] Keep `ProtectedSourceBundlePolicy` direct caller construction impossible,
  canonical instances frozen, exact identity/category cardinality unchanged,
  and no permanent Git-state test.
- [x] Preserve classification != bundle identity != location != existence !=
  metadata safety != acquisition != admission != verification != authority.
- [x] Record WU-11 final focused `26 passed in 0.11s` and authoritative final
  architecture review `PASS` after all corrections.
- [x] Record WU-12 canonical exactly once:
  `3742 passed, 5 deselected, 499 warnings`, `CANONICAL_RC=0`; warnings
  non-failing, no subsequent correction,
  and no rerun.
- [x] Record implementation commit
  `795d93c6e9f577a0e222c9617c23468b354d7a5b`, normal push `PASS`, `AHEAD=0`,
  `BEHIND=0`, and implementation Git closeout `PASS`.
- [x] Keep local `SOURCE_BINDING WU-10/WU-11/WU-12` inside authoritative
  Macro-WU-06; do not confuse them with integrated-program Macro-WUs.
- [x] Preserve `MACRO_WU_06=IN_PROGRESS`,
  `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
  `AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`; Macro-WU-07 remains the later
  factual `RECOVER_EVIDENCE_SUFFICIENT` decision.
- [x] Record that no actual historical evidence acquisition or offline evidence
  evaluation is complete and Macro-WU-06 is not closed.
- [x] Preserve repository-only, value-free, fail-closed, zero-I/O,
  zero-authority, no-Production-access semantics; all required governance flags,
  exact six Shopping actions, target-only `SHOPPING_SECRET_PROVISIONING`, and
  operational no-activity truth.
- [x] Complete exact-six-document Git closeout.

No focused or canonical validation is rerun for this documentation-only work.

## MariaDB Continuity Integrated WU-09 — documentation closeout

- [x] `MARIADB_CONTINUITY_INTEGRATED_WU_07_DISCOVERY_RECONCILE_GATE=PASS`.
- [x] `MARIADB_CONTINUITY_INTEGRATED_WU_07_IMPLEMENTATION_GATE=PASS`.
- [x] `MARIADB_CONTINUITY_INTEGRATED_WU_07_FOCUSED_GATE=PASS`.
- [x] `FOCUSED_RESULT=17 passed in 0.07s`.
- [x] `MARIADB_CONTINUITY_INTEGRATED_WU_07_FINAL_ARCHITECTURE_REVIEW_GATE=PASS`.
- [x] `MARIADB_CONTINUITY_INTEGRATED_WU_08_CANONICAL_GATE=PASS`.
- [x] `CANONICAL_RESULT=3733 passed, 5 deselected, 495 warnings`.
- [x] `CANONICAL_RC=0`.
- [x] `IMPLEMENTATION_GIT_CLOSEOUT=PASS`.
- [x] `IMPLEMENTATION_COMMIT=63370cfdf4ea0c80ca54395dd5913317ba529dca`.
- [x] `GIT_PUSH=PASS`; implementation closeout divergence was `AHEAD=0`, `BEHIND=0`.
- [x] Preserve the closed twelve-category repository-only Evidence Acquisition Descriptor Contract.
- [x] Preserve descriptor/source/existence/acquisition/admission/verification/authority separation.
- [x] Preserve fail-closed, value-free, zero-authority, zero-I/O, zero-network, zero-SQL semantics.
- [x] Preserve Mac AIControlCenter as sole Control Plane and Ubuntu as stateless infrastructure worker.
- [x] Preserve `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- [x] Preserve the exact six Shopping actions and target-only `SHOPPING_SECRET_PROVISIONING`.
- [x] Preserve `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.
- [x] Preserve `ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`, and `STRATEGY_EXECUTED=false`.
- [x] Preserve `PRODUCTION_VALIDATION_READY=false` and `SHOPPING_RUNTIME_ACTIVATED=false`.
- [x] Preserve `PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
  `SECRET_VALUES_READ=NO`, `SQL_EXECUTION=NOT_PERFORMED`,
  `PYMYSQL_ACTIVITY=NONE`, and `NOTION_SYNC=NOT_PERFORMED`.
- [ ] Complete exact-six-document Git closeout.

No focused or canonical validation is rerun for this documentation-only work.

## MariaDB Continuity Phase B2B-1D Package-4 — documentation closeout candidate

- [x] Discovery and Architecture Freeze `PASS`.
- [x] Exact four-file implementation; focused `8 passed in 0.05s`; self-review
  and Final Architecture Review `PASS`.
- [x] Classify sandbox canonical (`2 failed, 3722 passed, 5 deselected, 481
  warnings`, `RC=1`) as two unrelated audit-SQLite environment failures.
- [x] Confirm writable host preflight and authoritative host canonical (`3724
  passed, 5 deselected, 487 warnings`, `RC=0`).
- [x] Confirm no post-review correction and no post-host-pass canonical rerun.
- [x] Complete implementation Git closeout and normal push at
  `9f63463dc9f1c48fdda0ceaba698fead6dd3fab2`; verify current HEAD/upstream
  alignment and divergence `0 0`.
- [ ] Complete exact-six-document Git closeout.

Package-4 is only a repository-only, value-free, zero-authority, zero-I/O,
zero-network, fail-closed external evidence admission and verification boundary
contract. All presentation/admission/verification and downstream fact/authority
layers remain separate. No ingestion, retrieval, authoritative verification,
Production access, MariaDB/credential validation, SQL, activation, or historical
evidence is claimed. Unavailable auth-plugin/PyMySQL evidence, incomplete
five/three categories, insufficient `RECOVER`, unauthorized ROTATE/REPLACE,
unexecuted strategy, false readiness/runtime, Mac sole Control Plane, stateless
Ubuntu, factual-only legacy readiness, unchanged Phase-06 semantics and exact
six actions, and target-only provisioning remain frozen.
Documentation Git closeout remains pending, so Package-4 is not `CLOSED`.

## MariaDB Continuity Phase B2B-1D Package-3 — documentation closeout candidate

- [x] Implement
  `PHASE_B2B_1D_PACKAGE_3_EXTERNAL_EVIDENCE_ATTESTATION_REFERENCE_CONTRACT` at
  `1f9790fe1c96a6c20135508e4bcfbfce5d897546`; pass implementation Git closeout
  and push; verify clean worktree and divergence `0 0`.
- [x] Pass Architecture Freeze; record initial focused `8 passed in 0.05s` and
  review #1 `BLOCKED` on the incorrect canonical
  `VERIFIED_EXTERNAL_REFERENCE` default.
- [x] Correct canonical state to `VERIFICATION_REQUIRED`; pass focused `9 passed
  in 0.05s`, review #2, and canonical #1 (`3716 passed, 5 deselected, 475
  warnings`, `RC=0`).
- [x] Correct trailing EOF blank lines in exactly two files after preflight
  blocked; preserve semantics (`NO_CHANGE`), reconcile architecture, preserve
  all prior gates, and pass corrected canonical (`3716 passed, 5 deselected,
  479 warnings`, `RC=0`).
- [x] Record late focused on the identical committed snapshot as `9 passed in
  0.04s`; record canonical after implementation Git closeout as `NOT_RUN`.
- [x] Freeze repository-only, immutable, fail-closed, value-free,
  zero-authority, zero-I/O, zero-network semantics; accept no evidence values,
  positive caller facts, or arbitrary reference strings.
- [x] Keep `VERIFIED_EXTERNAL_REFERENCE` reference-local with zero promotion;
  directly reuse `EvidenceRequirementCategory`, `VerificationState`,
  `DataIdentityCategory`, and `ContinuityEvidenceCategory`.
- [x] Preserve unavailable/incomplete/insufficient evidence, unauthorized
  ROTATE/REPLACE, unexecuted strategy, false Production readiness/runtime, Mac
  sole Control Plane, stateless Ubuntu, factual-only legacy readiness, exact six
  Shopping actions, target-only `SHOPPING_SECRET_PROVISIONING`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- [ ] Pass final documentation review for exactly these six root documents.
- [ ] Complete documentation Git closeout for exactly these six documents.

Package-3 implementation and validation are complete. Repository milestone
closure remains pending the final two documentation gates. No actual historical
evidence or sufficient `RECOVER` evidence is claimed; Production readiness and
Shopping runtime remain false.

### Next step

`PHASE_B2B_1D_PACKAGE_3_FINAL_DOCUMENTATION_REVIEW`

## MariaDB Continuity Phase B2B-1D Package-2 — documentation closeout candidate

- [x] Implement `PHASE_B2B_1D_PACKAGE_2_EXTERNAL_EVIDENCE_REFERENCE_MANIFEST`
  at `0c6cf471da9e918e798f8a71fb2d28a4afc98d46`; implementation and Git
  closeout `PASS`.
- [x] Complete focused validation: `29 passed in 0.05s`; complete final
  architecture review: `PASS`; run canonical exactly once afterward: `3707
  passed, 5 deselected, 471 warnings`, `RC=0`. Warnings are not failures; no
  focused or canonical rerun followed Git closeout.
- [x] Add repository-only, immutable, fail-closed, value-free, zero-authority
  representation of seven independent facts: requirement, reference state,
  existence, provenance validity, authority, compatibility, and reference-local
  readiness.
- [x] Freeze `VerificationState` as `UNAVAILABLE`, `REFERENCED_UNVERIFIED`,
  `VERIFICATION_REQUIRED`, and `VERIFIED_EXTERNAL_REFERENCE`; keep verified
  reference and `reference_readiness_established` local-only and non-authoritative.
- [x] Add exactly five non-B1 evidence requirements while directly reusing all
  five frozen `DataIdentityCategory` and all three frozen
  `ContinuityEvidenceCategory` values, with no duplicate enums.
- [x] Freeze value-free manifest prohibitions on caller supply, assertions,
  secrets/hashes/free text/SQL, I/O, network, and Production access; preserve
  projection authorization/capability/execution/mutation/retry/reconnect/rollback
  authority as false.
- [x] Preserve unresolved/unavailable/incomplete evidence state and
  `RECOVER_EVIDENCE_INSUFFICIENT`; keep human `RECOVER` selected under zero
  authority, ROTATE/REPLACE unauthorized, and strategy unexecuted.
- [x] Preserve fixed SQL unavailable, numeric loopback port unassigned, target
  undeployed, concrete credential path undefined, and credential reader absent.
- [x] Preserve no Production/MariaDB/secret/SQL/PyMySQL-install/Notion activity,
  Production readiness and Shopping runtime false, Mac sole Control Plane,
  stateless Ubuntu, factual-only legacy readiness, unchanged exact six Shopping
  actions, target-only `SHOPPING_SECRET_PROVISIONING`, and
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
- [ ] Pass final documentation review for exactly these six root documents.
- [ ] Commit and normally push exactly these six documents; verify clean Git
  and upstream divergence `0 0`.

Package-2 is not yet closed. The last two gates self-activate closure without a
second SHA-recording documentation mutation. Production validation and strategy
execution remain unauthorized.

### Next work after Package-2 closeout

Proceed only to the next MariaDB continuity evidence/strategy boundary.
`RECOVER` remains selected but its evidence remains insufficient; do not
silently authorize ROTATE, REPLACE, Production access, or execution.

## MariaDB Continuity Phase B2B-1D Package-1 — documentation closeout candidate

- [x] Implement at `cacc659fd518c751544a8062ce0c36813f1c7bcc`; Git closeout
  `PASS`; focused `79 passed in 0.20s`; architecture review #3 `PASS`.
- [x] Run canonical exactly once: `3678 passed, 5 deselected, 467 warnings in
  133.11s`, `RC=0`; no rerun without code/test change.
- [x] Add repository-safe, value-free, zero-authority auth-plugin evidence,
  compatibility-proof, Mac-owned identity, complete five-category data
  identity, exact three-category lineage/provenance, insufficient-`RECOVER`
  human decision, and fixed closed profile architecture.
- [x] Keep auth unresolved; PyMySQL uninstalled/unimported and compatibility
  unproven; fixed SQL unavailable/prohibited; Production mutation zero; one
  future attempt per non-reusable authorization; no retry/reconnect/rollback.
- [x] Add no aggregate readiness authority; preserve Phase-A legacy DTO,
  exact six actions, target-only `SHOPPING_SECRET_PROVISIONING`, Mac ownership,
  stateless Ubuntu, `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, and runtime
  false/not-performed truth.
- [ ] Pass final documentation review for exactly these six docs.
- [ ] Commit and normally push exactly these six docs; verify clean Git and
  upstream divergence `0 0`.

Package-1 is not authoritatively `CLOSED`; the two remaining gates self-activate
closure without a second edit or predeclared SHA. Production validation must
not start.

### Next B2B-1D architecture/evidence boundary

Resolve authoritative historical auth-plugin evidence; exact PyMySQL `1.2.0`
compatibility proof; trusted database/account/grants identity; complete five
data-identity categories; complete three continuity categories with independent
historical provenance; then fixed SQL/profile architecture, concrete target and
credential acquisition boundaries, and one-shot composition. Do not freeze a
further decomposition here. Only later may explicit human authorization permit
one Production MariaDB validation.

## MariaDB Continuity Phase B2B-1C — documentation closeout candidate

- [x] Complete implementation at
  `d4802054366178c6e3282ad089e393726f2d9309` with `9 files changed`, `91
  insertions`, and `4 deletions`.
- [x] Complete focused validation: `42 passed in 0.16s`.
- [x] Complete final architecture review: `PASS`.
- [x] Run canonical exactly once after final architecture review: `3674 passed,
  5 deselected, 463 warnings in 134.93s`, `CANONICAL_RC=0`; do not rerun absent
  code/test changes.
- [x] Complete implementation Git closeout: `PASS`.
- [x] Declare exactly `PyMySQL==1.2.0` while preserving
  `PYMYSQL_INSTALLED=NO`, `driver_imported=false`,
  `PYMYSQL_COMPATIBILITY_ESTABLISHED=false`, `AUTH_PLUGIN_STATE=UNRESOLVED`,
  and driver readiness false.
- [x] Preserve the symbolic credential boundary and its fixed-source,
  permission, trusted-owner, future FD/inode, single post-consumption
  acquisition, no-fallback, no-enumeration, no-ambient-authority, and
  no-secret-transport/hash requirements.
- [x] Preserve the frozen B1 `ContinuityEvidenceCategory` values exactly and
  `independent_historical_provenance_required=true`.
- [x] Add no database connection, SQL, retry, reconnect, pooling,
  `ControlledExecutionPort` use, Governance semantics change, or Production
  authority.
- [x] Preserve Mac Control Plane ownership, stateless Ubuntu,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping actions,
  target-only `SHOPPING_SECRET_PROVISIONING`, and all runtime false/not-performed
  facts.
- [ ] Pass final documentation review for this exact six-document state.
- [ ] Create and normally push its containing documentation commit, then verify
  clean Git status and upstream divergence `0 0`.

Phase status: implementation, focused validation, final architecture review,
canonical-once validation, and implementation Git closeout are complete. This
exact state is only the documentation closeout candidate; the entire
`PHASE_B2B_1C` is not yet authoritatively closed. It becomes `CLOSED` after the
two remaining gates above pass. That rule self-activates closure, so no second
documentation mutation is required merely to record the documentation commit
SHA.

Production validation must not start. The next milestone after authoritative
B2B-1C closure remains a separate architecture/discovery boundary, not a
Production invocation.

## MariaDB Continuity Phase B2B-1A — final closure candidate

- [x] Close implementation at `aa049e2940707ff9209a730ecfbcc5f705062171`
  with exactly 16 new files and 924 insertions of repository-only, value-free
  prerequisite contracts.
- [x] Correct blocked review findings: `node.module` import-root detection;
  external Git closeout for exact untracked scope; direct frozen B1
  `DataIdentityCategory` and `ContinuityEvidenceCategory` reuse; explicit enum
  identity/type tests.
- [x] Close focused validation (`49 passed in 0.14s`) and architecture review #2
  (`PASS`).
- [x] Run canonical exactly once after final architecture `PASS`: `3673 passed,
  5 deselected, 459 warnings in 134.90s`, `RC=0`; no rerun without code/test
  changes.
- [x] Close implementation Git state (`PASS`).
- [x] Preserve runtime false/unavailable facts, no Production/MariaDB/SQL/
  Docker/Colima/secret/Notion access, no PyMySQL install or requirements change,
  unassigned port, undeployed target, `PRODUCTION_VALIDATION_READY=false`, and
  `SHOPPING_RUNTIME_ACTIVATED=false`.
- [x] Preserve B2A/B1/Phase A history, Mac Control Plane ownership, stateless
  Ubuntu, `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six Shopping
  actions, and target-only `SHOPPING_SECRET_PROVISIONING`.
- [x] Preserve the prior reviewed documentation snapshot and its documentation
  Git closeout evidence at `099258ce3470f57e9260a1f671b404ed9d42a623`.
- [x] Establish the self-activating closure rule for this exact six-document
  `FINAL CLOSURE CANDIDATE`: its containing commit must be committed, normally
  pushed, then verified with clean Git status and upstream divergence `0 0`.

Phase status: implementation `CLOSED`; focused validation `CLOSED`; architecture
review `CLOSED`; canonical validation `CLOSED`; implementation Git closeout
`CLOSED`. While uncommitted, this exact reconciliation is the `FINAL CLOSURE
CANDIDATE`; `099258ce3470f57e9260a1f671b404ed9d42a623` is prior documentation
evidence, not its commit. `PHASE_B2B_1A=CLOSED` becomes authoritative only when
the commit containing this exact reconciliation is committed, normally pushed,
followed by clean Git status, and followed by upstream divergence `0 0`. Passing
those checks makes documentation Git and repository closeout `CLOSED` under this
rule without requiring a second documentation mutation.

### Next boundary

`PHASE_B2B_1B_CONCRETE_READINESS_DISCOVERY`

It must begin read-only and implies no PyMySQL installation, requirements
change, Production access, MariaDB authentication, credential acquisition, SQL
execution, numeric loopback-port deployment, or runtime activation.

## MariaDB Continuity Phase B2A — documentation closeout complete

- [x] Close implementation at `6063ce08b62e99331f5d442afc9d2a71703bcabf`.
- [x] Close validation: initial focused `21 passed in 0.35s`; first final review
  `BLOCKED`; corrected focused `31 passed in 0.13s`; final read-only review #2
  `PASS`; canonical exactly once on final reviewed state, `3624 passed, 5
  deselected, 455 warnings in 134.66s`, `RC=0`; both post-commit reruns
  `NOT_RUN`.
- [x] Add value-free contracts only; keep canonical truth separate from
  constructible observation states exactly `CONFIRMED`, `REJECTED`,
  `NOT_EVALUATED`, and `UNCERTAIN`; derive completion only when all six facts
  are confirmed; grant zero authorization, capability, execution, mutation,
  retry, reconnect, and rollback authority.
- [x] Add one-slot metadata validation: `0700` non-symlink directory parent and
  non-empty regular non-symlink leaf no broader than `0600`, both with expected
  uid/gid; closed reasons; contradiction rejection; inert manual positives;
  separate trusted `observe_fixed_protected_source`; no value read,
  enumeration, or fallback.
- [x] Preserve Mac-owned `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE` with no
  numeric loopback port, no deployment, and no readiness.
- [x] Define only the future PyMySQL `1.2.0` synchronous one-shot contract,
  unresolved auth plugin and one future connection maximum per authorization;
  add no import/install, requirements change, network, SQL, retry, reconnect,
  or pooling.
- [x] Limit implementation to
  `core/secrets/mariadb_continuity_observations.py`, the three continuity files
  under `ops/macos/shopping/`, and their four matching test files.
- [x] Record normal push, clean Git, and divergence `0 0`; record the duplicate
  closeout stale-HEAD rejection as successful protection that created no second
  commit, push, or implementation change.
- [x] Preserve runtime truth: Production access, authentication, SQL, Docker,
  Colima, and Notion `NOT_PERFORMED`; values read `NO`; PyMySQL installed and
  requirements changed `NO`; auth plugin unresolved; port unassigned;
  `PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
- [x] Preserve Mac as sole Control Plane, Ubuntu as stateless worker,
  `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six historical
  Shopping actions, and target-only `SHOPPING_SECRET_PROVISIONING`.
- [x] Complete Phase B2A documentation closeout and final read-only review at
  `cfb1d7eae4b9676373ba31c485330b8449cd90f3`.

Phase status: `PHASE_B2A_IMPLEMENTATION_STATUS=CLOSED`,
`PHASE_B2A_VALIDATION_STATUS=CLOSED`,
`PHASE_B2A_DOCUMENTATION_STATUS=CLOSED`,
`PHASE_B2A_REPOSITORY_STATUS=CLOSED`.

### Next boundary after completed Phase B2A repository closeout

`PHASE_B2B_CONCRETE_INTEGRATION_DISCOVERY`

Phase B2B is not implemented. No PyMySQL installation,
requirements change, numeric MariaDB port, deployed target, credential
availability, authentication, SQL, Production readiness, or Shopping runtime
activation is claimed.

## MariaDB Continuity Phase B1 — implementation and validation complete

- [x] Close Phase B1 at implementation commit
  `acdbd859872b842691c293b5e094472b344d304b`.
- [x] Enforce factual one-shot state flow `NEW -> AUTHORIZED -> CONSUMED ->
  PRE_ATTEMPT -> ATTEMPT_INITIATED -> TERMINAL`; preserve
  `attempted_count=0` for pre-attempt termination and `attempted_count=1` after
  initiation; prohibit skipped/reverse/repeated/post-terminal transitions and
  a second attempt. `AUTHORIZED` grants no authority.
- [x] Freeze the value-free source categories as `CREDENTIAL_SOURCE`,
  `EXPECTED_IDENTITY_DESCRIPTOR`, `DATA_IDENTITY_BASELINE`, and
  `DATA_CONTINUITY_BASELINE`; keep all four current availability facts false
  and reject unsupported positive or contradictory public construction.
- [x] Preserve the Mac-owned external fixed credential slot outside Git with
  `0700` parent, `0600` regular non-symlink file, explicit trusted uid/gid, no
  ambient `HOME`/UID authority, no env/argv/JSON secret/Governance transport,
  no secret log/hash, fallback, enumeration, or candidate iteration, and one
  acquisition maximum only after capability consumption. No credential was
  read or verified.
- [x] Define `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`, owner
  `MAC_CONTROL_PLANE`, with `canonical_target_contract_defined=true`,
  `numeric_loopback_port_assigned=false`, `target_deployed=false`, and derived
  `production_target_ready=false`. Add no caller host/port/DSN/URL/database/
  username and assign no numeric MariaDB port.
- [x] Add no PyMySQL, driver, SQL, network, filesystem credential reader,
  environment/argv credential transport, retry, reconnect, pooling, Production
  access, or MariaDB authentication. Keep `PRODUCTION_VALIDATION_READY=false`
  and `SHOPPING_RUNTIME_ACTIVATED=false`; Production/authentication/runtime/
  Docker/Colima/Notion `NOT_PERFORMED`, secret values read `NO`, PyMySQL
  installed `NO`, requirements changed `NO`.
- [x] Preserve `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, Mac
  AIControlCenter as sole Control Plane, Ubuntu as stateless worker, and the
  exact six actions: `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
  `SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
  `SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
  `SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
  `SHOPPING_SECRET_PROVISIONING` remains target-only.
- [x] Record initial focused `22 passed in 0.07s`; first architecture review
  `BLOCKED` for public factual forgeability/contradiction handling and missing
  associated coverage; correction `PASS`; corrected focused `37 passed in
  0.06s`; final read-only review `PASS`; canonical exactly once after final
  reviewed code/test state,
  `3593 passed, 5 deselected, 447 warnings in 133.58s`, `RC=0`; post-commit
  canonical rerun `NOT_RUN`.

### Phase B2 — future development boundary

- [ ] Select and pin a PyMySQL dependency.
- [ ] Build a synchronous one-shot Mac driver adapter.
- [ ] Resolve the fixed loopback target.
- [ ] Implement the protected credential source reader.
- [ ] Implement independent expected DB/account/grants, data identity, and
  continuity lineage baseline readers.
- [ ] Define fixed parameterized read-only SQL, one connection only, with no
  retry, reconnect, or pooling.

Phase B2 is not implemented and is not Production-ready. No new numeric
SM-01B-02D milestone identifier is assigned without repository evidence.

## MariaDB Continuity Validation Prerequisite / Phase A

- [x] Close Phase A as repository-complete after documentation closeout at
  implementation commit `ccf3ce00f7f6602d2cc6a84ec5632c7088cae418`.
- [x] Provide only value-free prerequisite/readiness facts and a Mac Control
  Plane process-local composition boundary with non-serializable one-shot human
  presence, canonical binding, concurrent exactly-once consumption before
  assembly, permanent consumption after failure, redacted exceptions, and no
  capability invocation.
- [x] Preserve `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`, the exact six
  Shopping secret provisioning actions, Mac AIControlCenter as sole Control
  Plane, and Ubuntu as a stateless infrastructure worker.
- [x] Record focused `13 passed in 0.07s`, final architecture review `PASS`, and
  canonical `3556 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly
  once on the final reviewed implementation tree. Post-commit canonical rerun:
  `NOT_RUN`.
- [x] Record Production access/authentication, runtime inspection, Docker,
  Colima, and Notion as `NOT_PERFORMED`, with secret values read `NO`.

Phase A is not Production validation readiness. It added no driver, Production
credential source/material verification, SQL, connectivity, canonical target,
identity/continuity baseline, real Production capability/authentication,
consumer compatibility validation, mutation authority, or activation.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`;
historical MariaDB credential continuity remains unresolved.

## Phase B architecture discovery

The next development boundary is Phase B preparation, without Production
invocation. No successor `SM-01B-02D` identifier is assigned by repository
evidence. Phase B must separately resolve:

- [ ] MariaDB driver selection and dependency pinning.
- [ ] A fixed Mac Control Plane driver boundary.
- [ ] A canonical loopback target/profile contract.
- [ ] A protected external historical credential source.
- [ ] An independent expected database/account identity descriptor.
- [ ] An independent data-identity baseline.
- [ ] An independent historical data-continuity baseline.
- [ ] No retry, reconnect, or pooling semantics.
- [ ] A fixed read-only SQL surface design.

Actual Production validation readiness must not be claimed until every
prerequisite is truthfully available.

## SM-01A — Shopping Secret Contract & Fail-Closed Preflight v1

Status: **IMPLEMENTATION AND VALIDATION COMPLETE**

- [x] Establish `deploy/shopping/config/secret-contract.json` as the single,
  value-free canonical Shopping secret-metadata authority.
- [x] Implement the Python preflight as a read-only JSON consumer without an
  exact duplicate key table.
- [x] Separate `runtime_cutover` and `bootstrap` required-key resolution.
- [x] Validate structure fail-closed and evaluate presence only; reject
  unsupported actions, unknown supplied names, and missing required names.
- [x] Keep not-evaluated distinct from pass/fail and grant no authorization.
- [x] Keep read-only monitoring independent of secret material and retain
  plain `${SHOPPING_*}` Compose interpolation.
- [x] Complete focused validation: `111 passed, 9 warnings`.
- [x] Complete exactly one final-code canonical regression: `3179 passed, 5
  deselected, 447 warnings`, `RC=0`.
- [x] Close implementation at commit
  `ffdf034ed9e1587328b6ecad35a6fcbe1381d8b0` with no Production mutation,
  secret-value read, backend/materialization, or Notion synchronization.

## SM-01B — Secret Delivery Backend v1

- [x] `SM-01B-01 — SOPS/age Secret Backend Inspection v1`: implementation and
  validation complete at `SM_01B_01_SECRET_BACKEND_INSPECTION_VALIDATED`.
- [x] Select SOPS+age as the replaceable backend architecture while keeping
  deployed truth `NOT_DEPLOYED`.
- [x] Preserve Mac Control Plane ownership, value-free monitoring, portable
  identity custody outside the repository, offline recovery recipient policy,
  and no Ubuntu secret ownership.
- [x] Keep core vendor-neutral with zero imports from `ops` and `integrations`;
  isolate SOPS+age metadata-only inspection in the macOS outer adapter.
- [x] Close `SM-01B-02B — Provisioning Planner v1` at
  `SM_01B_02B_PROVISIONING_PLANNER_VALIDATED`, implementation commit
  `2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`.
- [x] Define exactly five typed actions in the canonical provisioning
  definition and Draft 2020-12 schema; keep core `ProvisioningPlan`
  vendor-neutral and value-free.
- [x] Emit only sanitized `UNKNOWN_ACTION` or `MALFORMED_CONFIGURATION`
  evidence for malformed input; keep the read-only macOS inspector planning
  only and core import counts from `ops` and `integrations` at zero.
- [x] Record focused `73 passed` and canonical `3236 passed, 5 deselected, 447
  warnings`, `RC=0`, executed exactly once on final implementation code; exact
  six-file implementation scope, post-canonical scope, staged scope, staged
  diff check, commit, push, and upstream alignment all passed.
- [x] Close `SM-01B-02C — Bounded Mutation Adapters v1` at
  `SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED`, implementation commit
  `5a811cb1f9c782acb4f3e537596fb47ae0c599ff`.
- [x] Implement code-only adapters behind SEC-02 `ControlledExecutionPort`
  for exact target `SHOPPING_SECRET_PROVISIONING` and the five exact Shopping
  provisioning actions: `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
  `SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
  `SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
  `SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`, and
  `SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`. Each accepts
  only the exact target/action, invokes at most one narrow injected capability,
  emits value-free
  `GovernanceExecutionReceipt` evidence with a deterministic injective
  namespace over the full `execution_request_id`, and has no authorization,
  retry, rollback, compensation, generic shell/argv/package-manager framework,
  or parallel governance framework.
- [x] Record focused `128 passed` and canonical `3288 passed, 5 deselected, 447
  warnings`, `RC=0`, executed exactly once on final implementation code; exact
  three-file implementation scope, post-canonical scope, staged scope, staged
  diff check, commit, push, and upstream alignment `0 0` all passed.
- [x] Validate `SM-01B-02D-01A — Generic Governance Authorization Consumption
  Boundary v1` implementation at commit
  `01e57cabd39cbc594f128e06527332b3c515c249`; documentation closeout remains
  pending until this change is committed.
- [x] Resolve the SM-01B-02D-00 blocker through the generic SEC-02
  `AuthorizationConsumptionPort`, immutable command/result, and only
  `consume_once`; consumption is Governance, not Shopping-specific.
- [x] Require `AUTHORIZED` authorization, `AVAILABLE` mutation budget, exact
  lifecycle/authorization/target/action-scope/mutation-budget bindings, and a
  matching zero-invocation budget line item; return only consumed evidence and
  an exact-bound request that grants no execution authority.
- [x] Record focused `114 passed` and canonical `3331 passed, 5 deselected,
  447 warnings`, `RC=0`, canonical execution count exactly `1`.
- [x] Close `SM-01B-02D-01B — Shopping Provisioning Governance Coordinator
  v1` at
  `SM_01B_02D_01B_SHOPPING_PROVISIONING_GOVERNANCE_COORDINATOR_VALIDATED`,
  implementation commit `8229288d68d46383082cec48ffc726bd0dbee09a`.
- [x] Enforce planner -> explicit human-authorized lifecycle -> read-only
  precondition -> SEC-02 `ALLOW_AUTHORIZATION_CONSUMPTION` ->
  `AuthorizationConsumptionPort.consume_once` -> fresh read-only precondition
  -> SEC-02 `ALLOW_SINGLE_INVOCATION` -> exactly one of five bounded
  `ControlledExecutionPort` adapters -> read-only postcondition -> closeout or
  stop.
- [x] Record that consumption evidence grants no execution authority;
  `READY`/`BLOCKED`/`MALFORMED` cause zero consumption and zero invocation;
  post-consumption drift stops with consumed authorization and zero invocation;
  `FAILED`/`UNCERTAIN` stop after one attempt; and there is no automatic retry,
  rollback, or compensation.
- [x] Record focused `181 passed` and canonical `3349 passed, 5 deselected,
  447 warnings`, `RC=0`, canonical execution count exactly `1`.
- [x] Close `SM-01B-02D-02B — Shopping Secret Provisioning Capabilities v1`
  at `SM_01B_02D_02B_SECRET_PROVISIONING_CAPABILITIES_VALIDATED=true`, implementation
  commit `bffe28a153eb83d3c61e04d38f2ab96892a6feb5`.
- [x] Validate five narrow capabilities with explicit `expected_uid` injection,
  no ambient UID/HOME authority, a fixed trusted Homebrew executable boundary,
  no generic shell/argv API, no-overwrite/no-clobber behavior, fail-closed
  mutation uncertainty, and no automatic retry, rollback, or compensation.
- [x] Keep Python from reading the private control-plane age identity for
  recipient derivation; keep offline recovery public-recipient-metadata only
  and preserve the value-free evidence contract.
- [x] Record focused `421 passed`; canonical `3387 passed, 5 deselected, 447
  warnings in 132.49s`, `RC=0`, canonical execution count exactly `1`; Git
  closeout PASS; upstream divergence `0 0`.
- [x] Record `PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
  `SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
  `COLIMA_ACCESS=false`, and `NOTION_SYNC=false`.
- [x] Close `SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store
  v1` at `SM_01B_02D_03_DURABLE_AUTHORIZATION_CONSUMPTION_VALIDATED=true`, commit
  `681a9e342fde47c7bcb9d3aa2d497b737a19e052`: generic Mac Control Plane
  Governance, unchanged `AuthorizationConsumptionPort`,
  `CORE_SEMANTICS_CHANGE_REQUIRED=false`, no Shopping logic or Ubuntu state.
- [x] Persist externally at
  `~/Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3`
  with ownership validation, unchanged shared parent, Governance `0700`, and
  database `0600`; enforce durable claim, atomic consumption, value-free replay
  protection, fail-closed fresh replay/stranded claims, and exact same-invocation
  ambiguous-commit reconciliation only.
- [x] Preserve execution-authority separation and record focused `372 passed`,
  corrected-tree canonical `3433 passed, 5 deselected, 447 warnings in 135.93s`,
  `RC=0`, exactly once after final fixture correction; Git closeout PASS,
  pushed, divergence `0 0`.
- [x] Complete and validate `SM-01B-02D-04A — Governed Offline Public Recipient
  Intake v1` at implementation commit
  `6e1aa0135b652b199f05a4911c0f45817a8529f4`: add the sixth exact action,
  preserve external private-identity custody, separate intake from later
  registration authorization, and bind the fixed Mac inbox mutation to trusted
  descriptor/inode evidence. Focused `163 passed`; canonical `3457 passed, 5
  deselected, 447 warnings in 133.23s`, `RC=0`; Git closeout PASS, clean,
  divergence `0 0`.
- [x] Land the 04A documentation closeout and mark `SM-01B-02D-04A` CLOSED.
- [x] Close `SM-01B-02D-04B — Provisioning Runtime Composition & Read-Only
  Postconditions v1` at `a4cb53d5398dffdc33366ac042fdb7813f6d4577`:
  Mac-Control-Plane-owned JSON-first deterministic, read-only, value-free
  composition; closed `READY`/`MISSING`/`BLOCKED`/`UNSAFE`/`MALFORMED`
  vocabulary and fail-closed contradictory configured/readiness state.
- [x] Preserve six actions, separate offline intake/registration, unchanged
  Governance/durable-consumption/`ControlledExecutionPort`, and
  `materialization_implemented=false`; no payload, materialization, cutover, or
  activation. MariaDB continuity remains blocking; dedicated Shopping
  materialization architecture is future work.
- [x] Record focused `47 passed`; canonical `3471 passed, 5 deselected, 447
  warnings` in approximately `133.97s`, `CANONICAL_RC=0`,
  `CANONICAL_GATE=PASS`; implementation push/clean/divergence `0 0`/closeout
  PASS. Production access and Notion sync were not performed; canonical was not
  rerun for documentation closeout.
- [x] Close `SM-01B-02D-05 — MariaDB Credential Continuity Decision Model v1`
  at implementation commit `9f168cc475345e7d2c949f375ef5c44f2ad2fda9`.
  Preserve exact fail-closed factual states `UNRESOLVED`, `STRATEGY_DECLARED`,
  `VALIDATION_REQUIRED`, `RESOLVED` and strategies `RECOVER`, `ROTATE`,
  `REPLACE`; `RESOLVED`, strategy selection, and caller-supplied
  `validation_confirmed` grant zero authority. Trustworthy Production
  acquisition of confirmation remains a separately bounded future validation
  concern; `mutation_authority=false`, `capability_id=null`.
- [x] Preserve zero credential/secret values and zero new credential,
  identity, recipient, path, environment, process, execution, authorization,
  or mutation surfaces; preserve the exact six provisioning actions and keep
  `SHOPPING_SECRET_PROVISIONING` a target rather than a seventh action.
- [x] Keep authorization consumption/durable SQLite, mutation budgets,
  `ControlledExecutionPort`, SEC-02/postconditions, Governance audit/evidence,
  coordinator, adapters, config, schema, and inspectors unchanged. Implement
  no Production validation, recovery/rotation/replacement, payload,
  materialization, DB-dependent validation, cutover, or activation, and claim
  no historical credential recovery, validation, rotation, replacement,
  materialization, or activation.
- [x] Record focused `39 passed in 0.04s`; canonical `3510 passed`, `5
  deselected`, `447 warnings`, `RC=0`; final architecture review `PASS` with
  `CRITICAL=NONE`, `HIGH=NONE`, `MEDIUM=NONE`, `LOW=NONE`; implementation push
  `PASS`; Production access and Notion sync `NOT_PERFORMED`.
- [x] Close `SM-01B-02D-06 — MariaDB Historical Credential Continuity
  Validation Boundary v1` at implementation commit
  `3c93ad39586080db618ee090a7548806c024c44a`: Mac mini M4
  AIControlCenter-owned, value-free and read-only; no Production mutation
  boundary, `ControlledExecutionPort`, mutation budget, real MariaDB client, or
  real Production capability; factual results/evidence grant zero authority.
- [x] Implement exact outcomes `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`,
  `MALFORMED`, `UNCERTAIN`; require `attempted_count=1` and separate confirmed
  credential acceptance, expected database/account identities, required grants,
  data identity, and data continuity for `VALIDATED`. Keep consumer compatibility
  `NOT_EVALUATED`, uncertainty fail-closed, and prohibit retry, fallback,
  iteration, guessing, rollback, and compensation.
- [x] Preserve 05 `ContinuityDecision`, Governance/SEC-02/postconditions/audit,
  config, schemas, coordinator, durable authorization consumption, and the exact
  six actions. Define only an externally supplied, non-factual, non-serializable
  future capability, absent from serialized facts and invocable at most once.
- [x] Record focused `33 passed in 0.08s`; architecture review `PASS` with all
  severities `NONE`; canonical accidentally executed twice on the same unchanged
  final-reviewed tree, both `3543 passed, 5 deselected, 447 warnings`, `RC=0`.
  Record the duplicate as an operational process deviation, not a code or
  architecture failure, with no code/test change between runs. Push `PASS`;
  final Git clean/divergence `0 0`; no Production/runtime/Docker/Colima/Notion
  access and no secret-value read.
- [ ] Complete Phase B architecture discovery before considering any real
  Production validation. Until every prerequisite is truthfully available,
  continuity remains `UNRESOLVED`; do not select `RECOVER`, `ROTATE`, or
  `REPLACE`.
- [ ] After all readiness gates pass, execute each Production mutation under
  its own explicit human authorization: SOPS installation, age installation,
  control-plane identity creation, each public-recipient registration/intake
  write, each secret payload/materialization mutation, and later runtime cutover
  remain separately bounded; no authorization covers multiple mutations or
  grants retry authority.
- [ ] `SHOPPING_RUNTIME_ACTIVATED`
- [ ] `SHOPPING_STOREFRONT_ONLINE_READ_ONLY` (only after runtime activation)

SM-01B overall remains incomplete. Mac AIControlCenter remains the sole Control
Plane; Ubuntu remains a stateless worker with no Shopping secret ownership.
Offline-recovery private custody remains external. SM-01B-02D-06 provides the
completed read-only validation boundary but performed no Production validation;
it does not recover, rotate, replace, derive, invent, authenticate with, or
resolve historical MariaDB credentials. Authorization-consumption and 06
validation evidence grant no execution authority.
Actual SOPS/age installation, age identity creation, recipient registration,
secret materialization, and runtime activation have not occurred. Notion
remains deferred until after Runtime Activation.
Production remains `PRODUCTION_STATUS_NOT_DEPLOYED=true`;
`MATERIALIZATION_IMPLEMENTED=false`;
`SOPS_INSTALLATION=false`; `AGE_INSTALLATION=false`;
`AGE_KEY_GENERATION=false`; `OFFLINE_RECOVERY_KEY_GENERATION=false`;
`SECRET_PAYLOAD_CREATION=false`; `SECRET_MATERIALIZATION=false`;
`AUTHORIZATION_CONSUMED=false`; `SECRET_VALUES_READ=false`;
`RUNTIME_INSPECTION=false`; `DOCKER_ACCESS=false`; `COLIMA_ACCESS=false`;
`PRODUCTION_MUTATION=false`; `NOTION_SYNC=false`;
`SHOPPING_RUNTIME_ACTIVATED=false`.
Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
worker. Core has no dependency on `ops.macos`, and no generic shell or argv
execution API exists. This validation activity recorded
`MATERIALIZATION_IMPLEMENTED=false`.

## PA-04 — Notification Platform v1

- [x] Validate and close PA-04 after Git closeout at milestone
  `NOTIFICATION_PLATFORM_V1_VALIDATED`.
- [x] Keep notification intent, routing, provider choice, governance,
  authorization, audit, retry policy, and future delivery lifecycle in
  AIControlCenter; providers own transport only.
- [x] Establish `core.notifications` as provider-neutral,
  `integrations.notifications` as observation-only adapters, and
  `ops.macos.runtime.application` as outer composition; verify zero core
  imports from both `ops.*` and `integrations.*`.
- [x] Separate provider and routing statuses; define no actual delivery
  lifecycle while provider execution is absent.
- [x] Normalize all observations fail-closed, route only explicit
  `AVAILABLE`/configured/available evidence, and harden provider identities to
  `^[a-z0-9][a-z0-9._-]{0,63}$` with literal `UNKNOWN` for invalid input.
- [x] Record Telegram as optional and `NOT_DEPLOYED`, with no inferred
  readiness, configuration, environment, credential, endpoint, host, port,
  authentication, or network convention.
- [x] Reuse narrow `core.capabilities.manifest` lookup in OpenClaw and n8n while
  preserving PA-02/PA-03 outward behavior and avoiding a second topology or
  lifecycle framework.
- [x] Add exactly GET `/api/notifications/platform` and
  `/api/notifications/providers`, with no PA-04 mutation, delivery, retry,
  transport, Production authorization, or infrastructure operation.
- [x] Preserve GET/POST `/notifications` unchanged as **LEGACY / OUTSIDE PA-04
  SCOPE**; defer migration/deprecation to separately governed future work.
- [x] Record 85 passing exact-code focused tests after identity hardening and
  canonical regression `RC=0` on exactly one PA-04 invocation.

No Production mutation, Production notification, external provider I/O, or
PA-04 notification execution occurred. Legacy POST ran only through TestClient
compatibility tests. No launchd, Docker, `runtime/current`, credential, Caddy,
WordPress, Ubuntu, or live-provider mutation occurred. `git diff --check`
passed. No Notion synchronization is claimed. OPS-01B and PA-01 through PA-03
remain closed and unchanged.

## PA-03 — n8n Control Plane Adapter v1

- [x] Establish n8n as a replaceable external automation capability while
  retaining all Control Plane and business/customer authority in
  AIControlCenter.
- [x] Preserve dependency direction `ops.macos.runtime.application` →
  `integrations.n8n` → `core.capabilities`, with injection into
  `core.api.create_app` and no `ops.*` or `integrations.*` imports from core.
- [x] Reuse existing `core.capabilities` contracts and
  `CapabilityStatusService`; create no second capability framework.
- [x] Add only GET `/api/capabilities/n8n`, with no mutating method, workflow
  execution or enable/disable, webhook or credential creation, schedule
  mutation, Production authorization, or infrastructure mutation.
- [x] Validate the canonical manifest/schema before trusting the unique optional
  n8n identity: `NOT_DEPLOYED`, `runtime_health=false`,
  `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`.
- [x] Omit a PA-01 `service_platform` lifecycle definition because no
  sufficiently proven executable, lifecycle, log, or runtime identity exists.
- [x] Keep configuration, authentication, runtime, and transport `UNKNOWN`
  unless explicitly injected; invent no endpoint/environment/auth convention.
- [x] Keep platform-neutral `create_app` discovery-free and fail-closed with
  value-free `UNAVAILABLE` evidence; inject the adapter only at macOS outer
  composition and truthfully project `NOT_DEPLOYED`.
- [x] Keep secret/config evidence value-free and explicitly project
  `platform_business_policy_ownership=false` for external capabilities while
  preserving PA-02 OpenClaw compatibility.
- [x] Pass focused PA-03 validation with 96 tests and canonical deployment
  regression with `RC=0` on exactly one PA-03 canonical invocation.
- [x] Close PA-03 after Git closeout at milestone
  `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`.

PA-03 is validated. `git diff --check` passed; no Production mutation or n8n
workflow, credential, Docker, launchd, `runtime/current`, or live-service
operation occurred. No Notion synchronization is claimed. OPS-01B, PA-01, and
PA-02 remain closed and unchanged.

## PA-02 — OpenClaw Adapter v1

- [x] Discover existing manifest identity, adapter/API/config conventions, and
  local OpenClaw presence using read-only commands only.
- [x] Add a vendor-neutral capability observation port and AIControlCenter-owned
  facade with an outer `integrations.openclaw` adapter.
- [x] Project fail-closed, JSON-compatible status through GET-only
  `/api/capabilities/openclaw` with value-free secret/config evidence.
- [x] Preserve the existing optional `NOT_DEPLOYED`, `runtime_health=false`
  service topology and avoid an unproven Service Platform lifecycle identity.
- [x] Exclude prompts, tools, actions, Production authorization, deployment
  governance, infrastructure mutation, and business/customer state.
- [x] Pass focused PA-02 validation with 79 tests and canonical deployment
  regression with `RC=0` on exactly one PA-02 canonical invocation.
- [x] Close PA-02 after Git closeout at milestone
  `OPENCLAW_ADAPTER_V1_VALIDATED`.

PA-02 is validated. `git diff --check` passed; no Production mutation or
additional deployment, `launchctl`, `runtime/current`, credential, or
live-service operation occurred. No Notion synchronization is claimed. PA-01
and OPS-01B remain closed and unchanged. WordPress and unrelated Shadow
maintenance remain separate future work.

## PA-01 — Control Plane Service Platform v1

- [x] Introduce Control Plane Service Platform v1 with the canonical service
  manifest as the service-definition source of truth.
- [x] Keep `ServiceDefinition` pure core, `ServiceHealth` sole owner of
  aggregate runtime health, and `core` free of direct `ops.*` imports.
- [x] Compose macOS inspection in `ops/macos/runtime/service_platform.py` from
  `ServiceTopology.platform_services()`, existing launchd/heartbeat
  observation, strict filesystem readiness, and immutable runtime/source
  validation.
- [x] Resolve stable owner/group names only at the macOS boundary. Validate
  exact file type, symlink, mode, owner, and group fail-closed; treat only
  `ENOENT` as missing and use value-free evidence for other inspection errors.
- [x] Reuse the authoritative immutable-source validator without executing
  Production worktree code.
- [x] Keep lifecycle inspect-only. Limit bootstrap planning metadata to
  `NOT_DEPLOYED` with trusted launchd observation, ready filesystem, and
  immutable runtime/source preconditions. Dry-run has no authorization and no
  mutation, retry, rollback, or kickstart.
- [x] Preserve validated Application Scheduler and canonical API Production
  lifecycle behavior; keep `ops.macos.runtime.application:app` canonical and
  Shadow separate.
- [x] Pass 94 focused tests under umask `077` and exactly one final-candidate
  canonical deployment-regression invocation with `RC=0`.
- [x] Pass `git diff --check`; confirm no Production mutation.
- [x] Close PA-01 after Git closeout at milestone
  `CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`.

No Notion synchronization is claimed. WordPress and Shadow maintenance remains
deferred and separate.

## Canonical API recovery and runtime-health follow-up

- [x] Remediate privileged canonical refresh/bootstrap bytecode creation by
  disabling bytecode before project-local imports.
- [x] Pass focused regression (`49 passed`) and canonical regression (`2954
  passed, 5 deselected, 439 warnings`).
- [x] Build and independently validate Runtime/immutable Source
  `ef07532bd3d7` exactly once from commit
  `ef07532bd3d7ba91868d46375d48cac4821d6a56`.
- [x] Activate `runtime/current` once, reconcile shadow once, and recover the
  canonical API with exactly one separately authorized kickstart.
- [x] Validate canonical and shadow immutable Source CWD, `200/405` health
  method behavior, launchd running state, and public HTTPS API/Homepage ingress.
- [x] Verify duplicate recovery fails closed before authorization or mutation
  after the expected failed-state precondition is no longer true.
- [ ] Reconcile degraded whole-runtime health: `/runtime/health` currently
  returns HTTP `200` with `healthy=false`, unavailable API, Telegram, and
  scheduler entries, plus a stale scheduler heartbeat.
- [ ] Establish a fresh scheduler heartbeat and independently verify each
  unavailable service through a separately scoped, read-only-first operational
  investigation. Do not infer mutation authority from this roadmap item.

Canonical API/Homepage recovery is complete. Whole-runtime health debt remains
open and blocks any claim that the entire platform Runtime is healthy.

## SHOP-AI ProductDraft generation stream

- [x] `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified HEAD
  `52db3600ae76c70926e27ce930be70fe34f98452`.
- [x] Reuse SHOP-02 `ProductDraft`, existing `ProposedFields`, immutable
  revisions, and canonical `ProviderAdapter`; candidate remains `DRAFT`.
- [x] Contract `1.0.0`; one injected provider, one attempt, bounded timeout, no
  fallback; scoped at-most-one invocation with a non-production in-memory
  coordinator.
- [ ] `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`.
- [ ] First bound: architecture/discovery of existing durable persistence and
  transaction conventions before implementation.
- [ ] Add durable ProductDraft persistence, durable generation ledger, and a
  transactional revision + audit + operation Unit of Work on the Mac Control
  Plane; no ProductDraft or AI application state on Ubuntu.
- [ ] `SHOP-REC-01A_RECOMMENDATION_ARCHITECTURE` as a separate future stream.

## SHOP-01A retrospective reconciliation

- [x] SHOP-01A1 read-only runtime reconciled at
  `f95ba9ae2133b55db06c362df321b16785f21423`.
- [x] Canonical wrapper regression: `2670 passed, 5 deselected, 437 warnings`
  using `ops/macos/validation/run-deployment-regression-gate.sh -q`.
- [x] SHOP-01A2 repository utilization and SHOP-01/02/03 architecture history
  reconciled without replacing `core/shopping/` or enabling writes.
- [x] Single-attempt WooCommerce reads and disabled Production mutation
  authority recorded.
- [x] `SHOP-01A3_CLOSEOUT_AND_FINAL_SYNC_PREPARATION`: documentation closeout
  prepared without commit, push, external synchronization, or Production
  access.

Terminal milestone: `SHOP-01A_SHOPPING_READ_ONLY_FOUNDATION_READY`.

## Next bounded Shopping milestone

- [x] `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION`.
- [ ] Reuse existing SHOP-02 `ProductDraft` work; do not restart the Shopping
  architecture.
- [ ] Continue with `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`;
  keep recommendation work separate and Production mutation disabled.

## Current architecture milestone

- [x] A0-A10 SEC-02A architecture phase complete:
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`.
- [x] A1-A9 canonical evidence chain: `VALIDATED`.
- [x] Canonical full repository regression recorded exactly as
  `========= 2667 passed, 5 deselected, 437 warnings in 166.69s (0:02:46) =========`.
- [x] Prior focused Governance regression recorded as `265 passed in 1.45s`.
- [ ] External controller Git closeout.
- [ ] Notion actual external synchronization; documentation payload is
  `READY_FOR_FINAL_SYNC`.

## Next production-development milestone

- [x] `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION`, reusing the
  existing SHOP-02 `ProductDraft` domain and the completed read-only Shopping
  foundation rather than restarting the architecture.
- [ ] `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION` next.
- [ ] Keep Production commerce writes separately governed and blocked pending
  explicit future authorization.

## SEC-02 governance Control Plane

- [x] SEC-02A9 durable evidence policy and deterministic READ ONLY API
  projection validated by the focused Governance regression, `265 passed in
  1.45s`; milestone
  `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`. This was not the
  full repository regression.
- [x] SEC-02A10 architecture closure review; milestone
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`.
- [x] SEC-02A8 pure orchestration policy and safety tests: focused Governance
  regression `231 passed in 1.42s`; milestone
  `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a
  full repository regression.
- [x] SEC-02A7 adapter ports and compatibility mappings: abstract Governance
  ports and immutable declarative mappings validated by the focused Governance
  regression, `194 passed in 1.53s`; milestone
  `SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`.
- [x] SEC-02A6 JSON Schema registry and contract tests: exactly 16 Draft
  2020-12 schemas and their registry/valid-invalid fixture contracts validated
  by the focused governance regression, `173 passed in 1.39s`; milestone
  `SEC-02A6_JSON_SCHEMA_REGISTRY_AND_CONTRACT_TESTS_VALIDATED`.
- [x] SEC-02A5 receipts, failure, and evidence models included in the validated
  A1-A9 canonical evidence chain.
- [ ] Notion actual external synchronization (`READY_FOR_FINAL_SYNC`).

The A7 initial result was `1 failed, 193 passed in 1.56s`. R1 fixed the
Protocol-only interface gate and classified the failure as
`PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT`: test-inspection semantics, not
implementation `__init__` semantics. The final A7 result was not a full
repository regression. A7 adds no concrete Production adapter; adapters cannot
authorize, widen scope or mutation budget, or decide retry or rollback. Git
evidence remains read-only, Runtime identity observation-only, Governance
Operations operational audit/read-model only, Shopping rules Shopping-owned,
and Ubuntu a stateless Worker with zero Governance authority.

A8 invokes no port or adapter. Authorization consumption is a distinct gate;
current preconditions must `MATCH` before one bounded invocation permission,
and consumed authorization remains consumed after later drift. `FAILED`,
`UNCERTAIN`, postcondition `FAIL`, and failure evidence stop. Remaining
mutation count is not retry authority. There is no automatic retry, automatic
rollback, compensation authority, Production/provider/Ubuntu mutation, or
public mutation API. SEC-02A architecture readiness is now claimed only at the
A10 reusable-architecture boundary; none of these exclusions changed.

A9 requires operator-configured external Control Plane durable storage, atomic
write publication, restrictive permissions, durable synchronization, manifest
binding, and value-free evidence. `/private/tmp` is transient only; repository
or immutable source cannot own mutable runtime evidence, and application source
hard-codes no user-specific absolute data root. The compatible
`GovernanceApiEnvelope` projection cannot authorize, consume authorization,
execute, retry, roll back, or persist. No HTTP mutation route, concrete evidence
persistence adapter, or Production/provider/Ubuntu mutation was added.

The A6 R1 blocker was `SEC-02A6-R1_CONTROLLER_REGISTRY_API_ASSUMPTION_DEFECT`, a
controller assumption of a public `registry.contract_names()` API where the
frozen contract specified behavior, not that exact function name; it was not an
A6 contract implementation defect. The focused result is not a full repository
regression. SEC-02A6 adds no Production or Runtime access, execution adapter,
provider or Ubuntu mutation, orchestration, persistence, audit storage, public
mutation API, retry, or rollback. The later A10 closure claims reusable
architecture readiness without changing those A6 limits.

## AI provider architecture

- [x] AI-PROVIDER-01A: vendor-neutral contract, strict router, normalized errors,
  network-free OpenAI boundary and deterministic fake adapter.
- [ ] AI-PROVIDER-01B: Responses API repository transport and smoke CLI are
  implemented; human-controlled authenticated smoke is pending.
- [ ] AI-PROVIDER-01C: candidate Runtime integration and promotion.
- [x] AI-PROVIDER-01C-A: canonical Control Plane `BrainAgent.ask` workflow
  integration through `ProviderRouter` (repository only; no authenticated call).
- [ ] AI-PROVIDER-01C-B: create a new Candidate Runtime.
- [ ] AI-PROVIDER-01C-C: Production promotion only after explicit human
  authorization.
- [ ] Synchronize the provider architecture record to Notion
  (`DEFERRED_UNTIL_FINAL_PHASE`).

Production Runtime remains `7b171f135dc7`; PI-009 authorization remains intact.

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

- [x] C1 contract foundation
- [x] C2 immutable models and pure evaluator
- [x] C3 bounded macOS adapters
- [x] C4 JSON runner and integration
- [ ] Controlled read-only operational validation
- [ ] Human authorization review
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

- [x] Command execution port
- [x] HTTP transport port
- [x] `launchctl print` adapter
- [x] `lsof -F` listener adapter
- [x] Runtime filesystem adapter
- [x] Isolated Runtime Python probe
- [x] Exact localhost HTTP transport
- [x] Bounded parser tests
- [ ] C4 JSON runner and orchestration integration
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

- [x] Immutable models
- [x] Pure fail-closed evaluator
- [x] Deterministic report generation
- [x] Host-dependency prohibition tests
- [ ] C3 bounded macOS read-only adapters
<!-- AICONTROLCENTER:ACTIVATION_01B_C2:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:START -->
## ACTIVATION-01B-C1 Contract Foundation

Status: `COMPLETE`

- [x] Inspection policy Schema
- [x] Route-manifest Schema
- [x] Inspection-report Schema
- [x] Registry resources and bindings
- [x] Synthetic fixtures
- [x] Canonical digest bindings
- [x] Secret-field rejection
- [x] Pure-validation tests
- [x] Focused contract gate
- [x] Safe deployment regression
- [ ] Operational test-root harness stabilization
- [ ] C2 immutable models and pure evaluator

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01B_C1_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01A:START -->
## ACTIVATION-01A — Architecture and Runbook Only

Status: `COMPLETE`

Contract documentation commit: `d14058553baa1dfc45e027a59ff580013584913b`

- [x] Atomic activation contract
- [x] Exact service restart contract
- [x] Post-activation localhost validation contract
- [x] Fail-closed failure conditions
- [x] Separate rollback authorization boundary
- [x] Evidence requirements
- [x] Production authorization boundary
- [x] Repository `PYTHONPATH` limitation
- [x] Documentation commit and remote synchronization

No operational activation is authorized.

## ACTIVATION-01B — Read-Only Activation Inspector

Status: `ARCHITECTURE_FROZEN`

- [x] Repository capability inventory
- [x] Targeted reusable-component review
- [x] Architecture document
- [x] macOS read-only runbook
- [x] Host command allowlist
- [x] Runtime Python probe hardening
- [x] HTTP method-denial probe hardening
- [x] CLI status and exit-code semantics
- [x] No-mutation test strategy
- [ ] Versioned activation policy schema
- [ ] Versioned localhost route-manifest schema
- [ ] Activation inspection report schema
- [ ] Registered contract fixtures
- [ ] Pure models and evaluation service
- [ ] Bounded macOS adapters
- [ ] Canonical JSON CLI
- [ ] Fixture-based no-mutation test suite
- [ ] Read-only real-host validation
- [ ] Implementation documentation closeout

Production remains `NOT_AUTHORIZED`.
<!-- AICONTROLCENTER:ACTIVATION_01A:END -->

M4-A3 is closed after deterministic test-only lifecycle and live-boundary
isolation validation. Next is `M4-A4_READ_ONLY_OPERATIONAL_OBSERVATION` under
separate architecture and authorization gates. No M4-A3 artifact is
operationally valid. Production remains `NOT_AUTHORIZED`, Ubuntu remains
excluded, and the 427 warnings remain backlog.

M3-A4B2B2B-R4 closes strict-live contract compatibility only. Next is fresh
independent approval bound to R4 and a separately authorized Mac bootstrap.
M3-A4B3 remains blocked until actual bootstrap succeeds. Production remains
`NOT_AUTHORIZED`.

Recovery-2 completes reviewed evidence only. Actual managed targets remain
absent; next is fresh independent approval bound to the final R3 commit before
any authorized Mac bootstrap. Production remains `NOT_AUTHORIZED`.

The blocked R3 attempt is recovered with reviewed live composition and
pytest-only controlled orchestration. The actual operation remains
`NOT EXECUTED`; next is fresh independent approval bound to the recovery
commit before any authorized Mac bootstrap.

## M3-A4B2B2B-R1 closure

Existing safe parent compatibility is complete. Shared siblings remain outside
deployment ownership. Next: M3-A4B2B2B fresh approval and authorized Mac
bootstrap; Production remains `NOT_AUTHORIZED`.

## Current milestone

- M3-A4A CLOSED
- M3-A4B1 CLOSED
- M3-A4B2A CLOSED
- M3-A4B2B0 CLOSED
- M3-A4B2B1A CLOSED after validation
- Next: M3-A4B2B1B Operator Approval and Operational Permit Issuance

## M3-A4B2B0 Closure and M3-A4B2B1

M3-A4B2B0 is closed after deterministic read-only Mac host preflight
validation. Operational permit and authorization remain absent, bootstrap has
not executed, targets remain uncreated, and Production remains
`NOT_AUTHORIZED`. Next: M3-A4B2B1 Operational Permit Issuance.

## M3-A4B2A Closure and M3-A4B2B

M3-A4B2A is closed after controlled executor validation beneath pytest-owned
temporary roots. Synthetic permit consumption, audit/replay bootstrap,
baseline backup/restore and cleanup are validated. Operational permit issuance
and bootstrap remain absent; Production activation remains `NOT_AUTHORIZED`.
Next: M3-A4B2B Authorized Mac Operational Bootstrap Execution.

## M3-A4B1 Closure and M3-A4B2

M2, M3-A1, M3-A2, M3-A3, M3-A4A and M3-A4B1 are closed. Controlled bootstrap
authorization capability is available and synthetic one-use permit validation
is complete. No operational permit was issued, bootstrap was not authorized or
executed, operational targets remain absent, and Production activation is
`NOT_AUTHORIZED`. Next: M3-A4B2 Controlled Mac Operational Bootstrap.

## M3-A2A Closure and M3-A2B

M2 controlled pilot validation, M3-A1 and M3-A2A are closed. Read-only
permit/replay integrity inspection is available, while the operational
database, durable reservation, consumption and persistent nonce writes remain
absent. Production activation is `NOT_AUTHORIZED`. Next: M3-A2B Durable Permit
Reservation and Consumption.

## M3-A1C Closure and M3-A2

M2 controlled pilot validation and M3-A1A through M3-A1C are closed after
pytest-only backup, restore and recovery validation. Operational database,
backup schedule, restore and persistent writer activation remain absent.
Production activation is `NOT_AUTHORIZED`. Next: M3-A2 Durable Permit and
Replay State.

## M3-A1B Closure and M3-A1C

M2 controlled pilot validation, M3-A1A and M3-A1B are CLOSED. The append-only
SQLite writer is implemented and validated only with pytest temporary
databases. The operational database does not exist, operational writer
activation is not started, persistent Production audit writes are not enabled,
and Production activation remains `NOT_AUTHORIZED`. Next: M3-A1C Backup,
Restore and Recovery Validation.

## M2-P3 Closure and M3-A1

M2-P1 through M2-P3 are CLOSED after one controlled pytest activation and one
controlled pytest rollback. Persistent host activation is NOT STARTED,
persistent host rollback and persistent SQLite audit are NOT IMPLEMENTED and
Production activation remains `NOT_AUTHORIZED`. Next: M3-A1 Durable SQLite
Audit Adapter.

## M2-P1 Closure and M2-P2

M2-P1 Controlled Non-Production Sandbox Pilot Authorization is CLOSED. Pilot
authorization policy is AVAILABLE; pilot activation is NOT STARTED. Persistent
SQLite audit is NOT IMPLEMENTED and Production activation remains
`NOT_AUTHORIZED`. Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence.

## DPL-04C Closure

DPL-04C is complete. The Mac Control Plane owns durable deployment audit, with
pure canonical event and hash-chain contracts behind a replaceable port. The
future append-only SQLite adapter is selected but not implemented. DPL-04A,
DPL-04B and DPL-04C are closed; DPL-04D is ready. M2 remains incomplete and
production activation is `NOT_AUTHORIZED`.

## DPL-04B Closure

DPL-04B is complete. The Mac-only adapter can materialize deterministic
manifest and evidence JSON only under an explicit, confined non-production
sandbox root. Default composition remains deny-only; command execution,
durable audit and production activation remain prohibited. DPL-04C is next.

## DPL-04A Closure

DPL-04A is complete. Typed executor contracts and ports are limited to
non-production Mac Control Plane targets and use a deny-only default
composition. No concrete real executor or production activation is authorized.
DPL-04B is next.

## DPL-03 Closure

DPL-03A through DPL-03D are complete subject to repository validation.
DPL-03D is simulation-only and does not authorize or perform production
deployment. M2 remains incomplete; DPL-04 is the next separately gated
milestone.

## Complete

- Core Runtime
- Dashboard
- BrainAgent
- Telegram
- Conversation Memory
- SQLite
- Command Router

## Current

Doctor

## Next

Logs

Backup Verify

Worker Health

Backup Execute

Homepage

Mac mini Production

## Sprint 21

- [ ] Brain Scheduler
- [ ] Heartbeat
- [ ] Job Registry
- [ ] Scheduler API
- [ ] Job Runner

## Sprint 22

- [x] Memory Manager
- [x] Working Memory
- [x] Long-term Memory
- [x] Memory API
- [x] Telegram Memory Commands

## Sprint 23

- [ ] Knowledge Registry
- [ ] Markdown Loader
- [ ] Knowledge Search
- [ ] Knowledge API
- [ ] Telegram /knowledge
- [ ] BrainAgent Knowledge Context

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Roadmap

### S0 Control Plane Baseline

Status: In Progress

- Shopping domain bootstrap
- Health API
- Readiness API
- Capabilities API
- Virtual environment tests
- Documentation
- Git Production Gate

### S1 Read-only Product Catalog

- Commerce Catalog Port
- Mock Product Adapter
- Product list API
- Product detail API
- Pagination
- Schema validation

### S2 WordPress and WooCommerce Virtual Environment

- WordPress container
- WooCommerce installation
- Test catalog
- REST API credentials
- AIControlCenter read-only adapter

### S3 AI Product Workflow

- Product generator
- SEO writer
- Product description generator
- Category generator
- Human approval
- Audit history

### S4 Controlled Publishing

- Authentication
- Authorization
- Idempotency
- Controlled WooCommerce writes
- Rollback
- Audit logging

### S5 Shopping Homepage

- WordPress theme
- Homepage
- Category pages
- Product pages
- Shopping Assistant integration

### S6 Production Hardening

- ARM64 validation
- Mac mini deployment
- Restart recovery
- Monitoring
- Backup
- Runbook
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## Shopping Platform Roadmap

### M4 — Live WooCommerce Control Plane

- [x] Shopping domain bootstrap
- [x] WordPress runtime
- [x] WooCommerce runtime
- [x] Product API
- [x] Category API
- [x] Integration API
- [x] Adapter Factory
- [x] systemd Secret integration
- [ ] Final Production Gate and Git closeout

### M5 — Shopping Experience

- [ ] Shopping Homepage
- [ ] Product detail experience
- [ ] Shopping Dashboard widgets
- [ ] Search and filtering

### M6 — AI Commerce

- [ ] AI Product Generator
- [ ] AI SEO Writer
- [ ] AI Category Generator
- [ ] AI Price Recommendation
- [ ] Approval workflow

### Production Blocker

A user-owned domain is required for public HTTPS.
The current ipTIME DDNS hostname cannot receive a certificate because of its parent-domain CAA policy.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform Service Roadmap

### M5 — AI Shopping Storefront Foundation

- [x] Featured Products API
- [x] Product Search API
- [x] Category Navigation
- [x] Price Filters
- [x] Stock Filter
- [x] Pagination
- [x] Product Image Support
- [x] Placeholder Fallback
- [x] WordPress Presentation Plugin
- [x] External Storefront
- [ ] Final Documentation and Git Closeout

### M6 — AI Product Generation

- [ ] Product Draft Model
- [ ] AI Product Generator
- [ ] AI Description Writer
- [ ] AI SEO Writer
- [ ] AI Category Suggestion
- [ ] Approval Workflow
- [ ] Controlled WooCommerce Write
- [ ] Audit Log

### M7 — Shopping Operations

- [ ] Order Read Integration
- [ ] Customer Read Integration
- [ ] Inventory Monitoring
- [ ] Shopping Dashboard
- [ ] Notifications
- [ ] n8n Automation
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ROADMAP -->
## Shopping Platform Baseline

Status: Completed

Completed:

- Orange Coco Storefront
- Shopping API integration
- Category, search and product APIs
- Product detail page
- Responsive homepage
- HTTP 404 contract
- Git baseline commit

Next:

- Mac mini Production Control Plane
- WordPress and WooCommerce migration
- AIControlCenter launchd runtime
- Production domain and HTTPS
- Wishlist and checkout improvements
- AI recommendation and product creation

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Mac Control Plane Roadmap

            ### Completed

            - [x] Mac Foundation Gate
            - [x] Git and SSH control
            - [x] Runtime Contract
            - [x] Python 3.12 production runtime
            - [x] Full Test Suite
            - [x] Read-only Health Gate
            - [x] Shadow read-only ASGI layer
            - [x] LaunchAgent architecture evaluation
            - [x] LaunchAgent rejected for headless production
            - [x] Non-root system LaunchDaemon
            - [x] Secure plist and runner ownership
            - [x] Automatic restart validation
            - [x] Localhost-only listener validation
            - [x] Health HTTP `200`
            - [x] Write probe HTTP `405`

            ### Current Sprint

            - [ ] Headless reboot recovery
            - [ ] Verify service before GUI login
            - [ ] Verify PID change after reboot
            - [ ] Verify process user `kyouhan`
            - [x] Verify Runtime commit preservation

            ### Next Sprint

            - [ ] 24-hour Shadow observation
            - [ ] CPU and memory baseline
            - [ ] restart-count monitoring
            - [ ] log-growth monitoring
            - [ ] Ubuntu Worker JSON read-only connection
            - [x] Mac Dashboard Shadow connection
            - [ ] Cutover and rollback runbook

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Mac Control Plane Roadmap Update

            - [x] Non-root LaunchDaemon
            - [x] Automatic restart
            - [x] Headless reboot recovery
            - [x] Health HTTP 200
            - [x] Write protection HTTP 405
            - [x] Localhost-only listener
            - [ ] Reconcile manager installer with plist
            - [ ] Complete 24-hour Shadow observation
            - [ ] Validate Ubuntu Worker JSON APIs
            - [ ] Complete cutover and rollback runbooks

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
## Shadow Observation Sprint

- [x] Headless reboot recovery
- [x] Read-only observer architecture
- [x] JSON Lines observation contract
- [x] Five-minute sampling definition
- [ ] Complete 24-hour observation window
- [ ] Review CPU and RSS baseline
- [ ] Review PID transitions
- [ ] Review log growth
- [ ] Approve or reject production cutover

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Foundation

Status: **Complete**

- [x] Commit-specific Runtime
- [x] Non-root system LaunchDaemon
- [x] Headless reboot recovery
- [x] Read-only Shadow API
- [x] Localhost-only listener
- [x] 24-hour observation
- [x] Canonical installation manager
- [x] Transactional apply
- [x] Transactional rollback
- [x] launchd settle policy
- [x] Final apply validation
- [x] Final restart validation
- [x] Documentation closeout

### Next Program Phase

- [ ] AIControlCenter REST API consolidation
- [x] Dashboard integration
- [ ] Homepage integration
- [ ] Ubuntu Worker read-only JSON APIs
- [ ] n8n read-only workflows
- [ ] Production cutover design and approval
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

### PI-001 Dashboard Shadow API Integration

- [x] Dashboard Control Plane JSON contract
- [x] Immutable Runtime metadata
- [x] Runtime metadata schema validation
- [x] Metadata-gated Runtime activation
- [x] `GET /health` returns HTTP `200`
- [x] `GET /dashboard` returns HTTP `200`
- [x] `POST /dashboard` returns HTTP `405`
- [x] Runtime commit matches Git HEAD

Production Runtime: `ba8d2c977257`

<!-- AICONTROLCENTER:PI-002:START -->
### PI-002 Ubuntu Worker Health JSON Adapter

Status: **Complete — Structured Monitoring Gate**

- [x] Define worker health JSON schema
- [x] Implement bounded SSH transport
- [x] Implement Ubuntu health JSON adapter
- [x] Add Production worker configuration
- [x] Add structured failure continuity
- [x] Connect `ubuntu-main` to the Production Dashboard
- [x] Validate immutable runtime deployment
- [x] Validate system LaunchDaemon operation
- [x] Validate Health and Dashboard HTTP `200`
- [x] Validate full regression suite
- [ ] Configure dedicated SSH identity for the service process
- [ ] Validate successful remote worker telemetry

Next milestone: Ubuntu Worker Healthy Telemetry.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
### PI-003 Ubuntu Worker Minimum Closure

Status: **Complete**

- [x] Confirm Ubuntu is an optional worker
- [x] Confirm Docker boot activation
- [x] Confirm Immich automatic recovery
- [x] Confirm Nextcloud automatic recovery
- [x] Confirm `unless-stopped` restart policies
- [x] Power off Ubuntu after validation
- [x] Validate Mac Control Plane standalone operation
- [x] Validate Health HTTP `200`
- [x] Validate Dashboard HTTP `200`
- [x] Validate structured optional-worker failure

### PI-004 Mac Standalone Production Baseline

Status: **Next**

- [ ] Inventory Mac mini services
- [ ] Validate Mac reboot recovery
- [ ] Define service deployment manifest
- [ ] Deploy Homepage on the Mac mini
- [ ] Validate local AI runtime and provider health
- [ ] Validate automation service deployment
- [ ] Add install, update and rollback automation
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
### PI-004 Mac Standalone Production Baseline

Status: **Complete**

- [x] Inventory Mac services
- [x] Create Mac Production service manifest
- [x] Confirm Homepage as embedded API
- [x] Align Homepage optional-worker contract
- [x] Validate immutable runtime deployment
- [x] Validate Mac reboot recovery
- [x] Run full test suite
- [x] Generate Production evidence

### PI-005 Mac Service Deployment Platform

Status: **Next**

- [ ] Define reusable service manifest schema
- [ ] Define install, update, restart and rollback interfaces
- [ ] Deploy Ollama as a managed Mac service
- [ ] Integrate Ollama health and model inventory
- [ ] Define n8n deployment contract
- [ ] Define OpenClaw adapter boundary
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Complete

- [x] Service manifest schema
- [x] JSON manifest validator
- [x] Read-only deployment plan
- [x] Mac service inspector
- [x] Desired/actual deployment diff
- [x] Ollama managed-service design
- [x] Dry-run and rollback plan
- [x] Installation approval gate
- [x] Full test and Production evidence

Next: PI-006 approved Ollama native deployment.
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

Status: **Production Complete — Final Documentation Commit Pending**

Completed milestones:

- architecture and ownership boundary
- canonical default-deny registry
- read-only registry loader
- governance evaluator
- read-only governance API
- full test suite and immutable runtime deployment
- Production operational validation
- rollback-readiness validation

Deferred beyond PI-007:

- approved model onboarding
- model download or deletion workflows
- write-operation authorization
- resource enforcement
- automated remediation
- model lifecycle audit UI

Any write-capable model lifecycle feature requires a separate Product Increment
and explicit Production approval.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008 — COMPLETE

Model Governance Audit and Dashboard Integration has completed the Production gate.

Completed scope:

- audit schema and immutable snapshots
- SQLite append-only persistence
- comparison and query services
- read-only API
- Dashboard integration
- runtime provenance
- Git-independent Production runner
- Production deployment
- rollback compatibility
- documentation closure

Next production milestone:

PI-009 should focus on operational observability for governance audit history, bounded Dashboard latency, backup verification, and alerting while preserving the read-only-first policy.

Write operations remain out of scope until monitoring, audit history, backup, and operational alerting are stable.

<!-- PI-009:START -->
## PI-009 Roadmap Status

### Completed

- Domain and event contracts.
- SQLite persistence adapter.
- Application service and projections.
- GET-only API integration.
- Fail-soft Dashboard integration.
- Regression and database-safety validation.
- Repository documentation handoff.

### Pending Production Gate

- Review and approve production migration.
- Review and approve scheduler activation.
- Synchronize the PI-009 Notion handoff.
- Execute post-activation operational validation.
- Confirm rollback readiness.

PI-010 must not depend on activated PI-009 scheduling until these
production gates are complete.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Completion and PI-010 Transition

### PI-009 — Governance Operations

- [x] Domain contracts
- [x] SQLite append-only repository
- [x] Application dispatch service
- [x] Read-only API and Dashboard projection
- [x] Production schema migration
- [x] Verified Production backup
- [x] Manual operation validation
- [x] Production UTC clock adapter
- [x] JSON-first one-shot runner
- [x] Full regression
- [x] Documentation close

### PI-010 — Controlled Scheduler Policy and Activation

- [ ] Approve explicit cadence for each operation
- [ ] Render disabled launchd definitions
- [ ] Validate temporary plist artifacts
- [ ] Obtain explicit installation approval
- [ ] Install and activate under controlled gate
- [ ] Observe the first operation executions
- [ ] Validate audit projection and logs
- [ ] Document unload and rollback procedures
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 — Governance Operations Scheduling

Status: CLOSED — 2026-07-23

Completed explicit cadence, JSON one-shot execution, dedicated governance runtime capabilities, headless Production scheduling, authoritative run_succeeded validation, rollback protection, regression, and documentation close.

Next milestone: Shopping Platform Foundation.

<!-- BEGIN AICONTROLCENTER SPF-002 ROADMAP -->
## Shopping Platform Foundation

Status: In Progress

| Task | Scope | Status |
| --- | --- | --- |
| SPF-001 | Repository and branch baseline | CLOSED |
| SPF-002 | Architecture and ownership foundation | CLOSED |
| SPF-003 | Package and read-only port skeleton | NEXT |
| SPF-004 | Canonical JSON Schema v1 | QUEUED |
| SPF-005 | Deny-by-default capability registry | QUEUED |
| SPF-006 | Read adapter contracts | QUEUED |
| SPF-007 | Adapter health monitoring | QUEUED |
| SPF-008 | Read-only snapshot retrieval | QUEUED |
| SPF-009 | Validation and schema drift detection | QUEUED |
| SPF-010 | Regression and operational close | QUEUED |

Write progression:
Monitoring → Validation → Reconciliation → Approval → Dry Run → Canary Write → Production Write.
<!-- END AICONTROLCENTER SPF-002 ROADMAP -->

<!-- SPF-003:START -->
## Shopping Platform Foundation Progress — 2026-07-23

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [ ] SPF-004 Canonical JSON Schema v1
- [ ] SPF-005 Capability registry deny-by-default
- [ ] SPF-006 Read adapter contracts
- [ ] SPF-007 Adapter health monitoring
- [ ] SPF-008 Read-only snapshots
- [ ] SPF-009 Validation and schema drift
- [ ] SPF-010 Regression, operational validation, and documentation closure

SPF-003 implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## Shopping Platform Foundation Progress

Completed:

- SPF-001 Repository and branch baseline
- SPF-002 Architecture foundation
- SPF-003 Package and read-only port skeleton
- SPF-004 Canonical JSON Schema v1

Next production task:

- **SPF-005 Capability Registry — deny by default**

Remaining after SPF-004:

- SPF-005 Capability Registry
- SPF-006 Read Adapter Contracts
- SPF-007 Adapter Health Monitoring
- SPF-008 Read-Only Snapshots
- SPF-009 Validation and Schema Drift
- SPF-010 Regression, Operational Validation and Documentation Closure

An internal read-only Homepage Preview is now architecturally unblocked, but it must remain fixture or controlled read-only until the required adapter and monitoring gates are complete.

<!-- SPF-005-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [ ] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **5/10 — 50%**.

Next production milestone: SPF-006 establishes replaceable read adapter contracts without enabling Shopping writes.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [ ] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **6/10 — 60%**.

Next production milestone: SPF-007 introduces observable adapter health and controlled live read integration without enabling Shopping writes.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [ ] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **7/10 — 70%**.

Next production milestone: SPF-008 introduces controlled read-only snapshot boundaries without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## Shopping Platform Foundation Progress

- [x] SPF-001 Repository and branch baseline
- [x] SPF-002 Architecture foundation
- [x] SPF-003 Package and read-only port skeleton
- [x] SPF-004 Canonical JSON Schema v1
- [x] SPF-005 Capability Registry deny-by-default
- [x] SPF-006 Read Adapter Contracts
- [x] SPF-007 Adapter Health Monitoring
- [x] SPF-008 Read-only Snapshots
- [ ] SPF-009 Validation and Schema Drift
- [ ] SPF-010 Regression, Operational Validation, and Documentation Closure

Current completion: **8/10 — 80%**.

Next production milestone: SPF-009 validates canonical contracts and detects schema drift without enabling Shopping writes or moving application state to Ubuntu.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- [x] SPF-009 — Validation and Schema Drift.
  - Runtime validator CLOSED.
  - Drift classifier CLOSED.
  - Authorization-first read-only schema drift monitoring CLOSED.
  - Negative/isolation/full regression CLOSED at 930 passed, 5 deselected.
- [ ] SPF-010 — Regression, operational validation and documentation closure.
- Foundation progress after SPF-009: **9/10 = 90%**.

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
- Foundation roadmap milestone: COMPLETE.
- Next production milestone: post-Foundation read-only external integration and monitoring.
- Write enablement is not part of Foundation closure and requires a future explicit milestone.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## SRI — Shopping External Read Integration

### Current sprint — SRI-03

SRI-03 implements the real external WooCommerce READ path while AIControlCenter remains the single Control Plane.

### Next milestone — Controlled Production DNS

1. Inventory a platform-controlled domain and DNS provider.
2. Select the canonical Shopping production hostname.
3. Configure or validate the A record against the current public IPv4.
4. Keep AAAA absent until IPv6 ingress is validated.
5. Validate CAA permits the selected public CA.
6. Reconfirm external HTTP ingress.
7. Validate staging TLS.
8. Perform one controlled Production TLS issuance.
9. Make Caddy reboot-safe with certificate storage continuity.
10. Connect the real WooCommerce upstream.
11. Create a dedicated WooCommerce READ-only credential.
12. Execute one canonical production GET.
13. Run Shopping and full regression suites.
14. Complete Git documentation and Notion closure.

### Following milestones

- SRI-04 — WordPress CMS real READ adapter
- SRI-05 — Health Schema Snapshot and Drift operational integration
- SRI-06 — Final regression and operational closure

After SRI closes the next program is DPL — Deployment Package.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:ROADMAP -->
## SRI Closure and Next Program

### Shopping External Read Integration

- SRI-01 external integration inventory: CLOSED.
- SRI-02 production read policy: CLOSED.
- SRI-03 WooCommerce production READ integration: CLOSED.
- SRI-04 WordPress CMS production READ integration: CLOSED.
- SRI-05 Health, Schema, Snapshot and Drift integration: CLOSED.
- SRI-06 regression, documentation, Git and handoff closure: final release baseline.

### Next program

DPL, Deployment Package, is the next production program.
DPL consumes the SRI architecture without moving business logic or application state to Ubuntu.
Codex performs implementation under Architect-owned specifications and acceptance gates.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## DPL — Deployment Package Program

- [x] DPL-01 — Inventory, ownership, architecture decisions, blockers and
  sprint plan.
- [x] DPL-02 — Versioned package/report JSON Schemas and registry; read-only
  inventory, validation, diff, dry-run, readiness and audit.
- [ ] DPL-03 — Enforced read/plan/apply package and dependency separation.
- [ ] DPL-04 — Launchd-native Mac inventory and health inspection.
- [ ] DPL-05 — Canonical Host Caddy, Colima, Compose and Commerce ingress
  validation.
- [ ] DPL-06 — Typed Ubuntu read-only action contract and deny-by-default
  policy; activation separately gated.
- [ ] DPL-07 — Immutable evidence, compatibility and release-candidate
  validation.
- [ ] DPL-08 — Regression, operational documentation and production
  authorization review.

### Production milestones

1. Read-only contract milestone: DPL-02 schemas and reports accepted.
2. Architecture boundary milestone: DPL-03 dependency rules enforced.
3. Mac readiness milestone: DPL-04 and DPL-05 pass without mutation.
4. Optional worker contract milestone: DPL-06 typed allowlist accepted.
5. Release candidate milestone: DPL-07 evidence and compatibility pass.
6. Authorization milestone: DPL-08 review completes.

No milestone itself authorizes production activation. Apply and production
writes require a separate explicit authorization.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL-04 Closure and Next Milestone

DPL-04A through DPL-04D are CLOSED and DPL-04 is CLOSED.
M2 is `READINESS_ACCEPTED`; activation is `ACTIVATION_NOT_STARTED`.
M2-P1 is CLOSED and pilot authorization policy is AVAILABLE. The next milestone
is M2-P2 Controlled Sandbox Pilot Activation and Evidence. Persistent SQLite
audit implementation is required before any broader mutable deployment.
Production activation remains `NOT_AUTHORIZED`.

## M3 Permit Replay

- [x] M3-A2A — Read-only permit/replay foundation.
- [x] M3-A2B — Durable reservation, consumption and failed-closed writer.
- [x] M3-A2C — Replay-state backup, recovery and concurrency validation.

M3-A2C validation used pytest temporary databases only and proved
post-recovery concurrency. Operational replay DB, backup schedule, restore and
writer activation remain absent; raw nonce writes remain zero. Production
activation is `NOT_AUTHORIZED`.

- [x] M3-A3A — Read-only operational monitoring foundation.
- [x] M3-A3B — Alert routing and deduplication.
- [x] M3-A3C — Monitoring and Alert Operational Drill.

M3-A3A, M3-A3B and M3-A3C are closed, and the M3-A3 Monitoring and Alert Track
is closed. The end-to-end monitoring drill and simulated logical delivery are
validated. M3-A3B provides deterministic logical routing, deduplication, reminders,
recurrence and severity escalation. External dispatch and alert-routing
persistence are not implemented; operational monitoring, databases and writers
remain inactive. Production activation is `NOT_AUTHORIZED`. Next: M3-A4
Controlled Operational Activation Gate.

- [x] M3-A4A — Read-Only Operational Activation Readiness Gate.
- [ ] M3-A4B — Controlled Mac Operational Bootstrap.

M3-A4A is closed. The activation readiness gate and controlled bootstrap plan
are available without authorization or execution. Operational databases are
not created; writers and monitoring are not activated; external dispatch is
not implemented; bootstrap authorization is not granted; Production activation
is `NOT_AUTHORIZED`.
# Current milestone

- M3-A4B2B1A — CLOSED
- M3-A4B2B1B — CLOSED after validation
- Human approval gate — AVAILABLE
- Synthetic dual-identity approval and in-memory permit issuance — VALIDATED
- Current recommended review — DENIED; independent approver `UNASSIGNED`
- Operational permit/claim/bootstrap execution — zero
- Production activation — `NOT_AUTHORIZED`
- Next: M3-A4B2B1C Independent Approver Action and Live Permit Issuance
# M3-A4B2B2A closure

- CLOSED: authorized Mac bootstrap execution capability and atomic test claim.
- NOT EXECUTED: controlled operational bootstrap.
- NEXT: M3-A4B2B2B Fresh Permit and Authorized Mac Bootstrap Execution.
# Next deployment task

M3-A4B2B2B Fresh Approval and Authorized Mac Bootstrap. Production activation
remains `NOT_AUTHORIZED`.
# R5 closure

M3-A4B2B2B-R5 adds the deterministic warning acknowledgement projection and
pre-issuance compatibility gate. Next is fresh approval and separately
authorized current-user Mac bootstrap; M3-A4B3 remains blocked until success.

# M3-A4B3 closure

- CLOSED: complete bootstrap evidence chain and exact commit binding.
- CLOSED: audit/replay `HEALTHY`, zero events, two isolated baseline restores.
- CLOSED: source immutability and negative recovery validation.
- PERMANENTLY CONSUMED: the successful one-use permit.
- INACTIVE: writers, monitoring, dispatch, and Ubuntu.
- `NOT_AUTHORIZED`: production.
- NEXT: `M3-A4C_ACTIVATION_VALIDATION_AND_CLOSEOUT`.

# M3-A4C — CLOSED

- Decision: `READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`.
- No writer, monitoring, dispatch, Ubuntu, or production activation.
- Next: `M4_CONTROLLED_ACTIVATION_ARCHITECTURE` with a separate gate.
- Separate backlog: the existing 427 deprecation warnings.

# M4-A1 — CLOSED

- COMPLETE: typed registry for five default-inactive, unauthorized capabilities.
- COMPLETE: deterministic immutable state transitions and architecture planner.
- COMPLETE: independent capability gates and explicit dependency policy.
- PROHIBITED: implicit escalation, Ubuntu ownership/delegation, and production.
- NO CHANGE: writers, monitoring runtime, dispatch, and external notification
  remain inactive; no operational authorization exists.
- Decision: `READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.
- Next: `M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.

# M4-A2 — CLOSED

- COMPLETE: immutable typed scope, request, approval, restriction, evidence,
  validation, grant-plan, plan, and decision contracts.
- COMPLETE: deterministic canonical JSON and SHA-256 digest/tamper binding.
- COMPLETE: independent identity policy and injected-clock, timezone-aware,
  maximum-one-hour single-use window validation.
- COMPLETE: capability-specific restrictions and separate dependency
  references without implicit authorization.
- NO CHANGE: no authorization, permit, claim, writer, monitoring, dispatch,
  Ubuntu, command, API write route, or production activation.
- Decision: `READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`.
- Production: `NOT_AUTHORIZED`.
- `.env`: not required.
- Next: `M4-A3_TEST_ONLY_AUTHORIZATION_SIMULATION`.
- Separate backlog: 427 existing deprecation warnings.
- Separate backlog: 427 existing deprecation warnings.

# M4-A1R1 — CLOSED

- BASELINE: M4-A1 commit `b719aa445af864c907ac5d384c2c8347d2d6688a`.
- COMPLETE: immutable retained SQLite source and disposable inspection/recovery
  working-copy contract.
- COMPLETE: WAL/SHM side effects confined to working copies; retained bytes,
  modes, sizes, mtimes, and digests unchanged.
- NO CHANGE: actual operational state, cryptographic/evidence semantics,
  writers, monitoring, dispatch, Ubuntu, commands, API routes, and production.
- `.env`: not required.
- Decision: `READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.
- Production: `NOT_AUTHORIZED`.
- Next: `M4-A2_CAPABILITY_AUTHORIZATION_CONTRACTS`.
# AUTO autonomous delivery roadmap

- [x] AUTO-01: immutable contracts, lifecycle, manifests, deterministic DAG,
  approval/retry/evidence policy, schemas and bounded executor port.
- [ ] AUTO-02: separately gated persistent Codex runner, terminal independence
  and recovery architecture.

AUTO-01 is architecture-only. Human approval remains mandatory for L4/L5 and
post-claim recovery. Persistent state and launchd are future work. Production
is `NOT_AUTHORIZED`.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Reprioritized Delivery Sequence

### Closed

- AUTO-01 — Autonomous Delivery Controller Architecture

### Deferred

- AUTO-02 — Persistent Codex Runner and Recovery
- AUTO-03 — M4 Master Manifest and Approval Gates
- M4-A4 — Read-Only Operational Observation
- M4-A5 — Separately Authorized Controlled Pilot
- M4-A6 — Evidence, Recovery and M4 Closeout

### Active Product Track

1. SHOP-00 — Shopping Platform Architecture Reprioritization
2. SHOP-01 — WooCommerce Read Adapter
3. SHOP-02 — Normalized Product Domain
4. SHOP-03 — Product Management API and Dashboard
5. Shopping draft, approval and controlled-write vertical slice
6. AI Integration Platform
7. Personal AI Assistant

The 427 existing deprecation warnings remain a separate remediation
backlog.
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


Product delivery sequence:

1. SHOP-01 — Product Management Read Model and Dashboard
2. SHOP-02 — Product Draft Workflow
3. SHOP-03 — Human Approval Workflow
4. SHOP-04 — Controlled WooCommerce Write
5. SHOP-05 — Order and Customer Read Integration
6. SHOP-06 — Shopping MVP Validation and Release
7. AI-01 — Shopping AI Integration

SHOP-01 must extend the existing Dashboard and Shopping APIs rather
than introduce a new frontend framework.
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

## Product Draft Sequence

- SHOP-01E read foundation — CLOSED.
- SHOP-01E3D persistent activation — DEFERRED.
- SHOP-02A Product Draft workflow architecture — COMPLETE.
- SHOP-02B Product Draft domain implementation — COMPLETE; contract 1.0.0 with a non-production in-memory adapter and no external writes.
- SHOP-02C Product Draft validation and human approval application service — COMPLETE; deny-by-default, HUMAN-only, exact-revision-bound, and in-memory only.
- SHOP-02D Product Draft read API and Dashboard projection — NEXT; production writes remain `NOT_AUTHORIZED`.

The zero-product, one-category WooCommerce observation does not block this sequence.
# Shopping sequence update

SHOP-02D is complete: GET-only ProductDraft reads and the `product_draft_review` Dashboard projection use a replaceable read source with explicit empty-versus-unavailable semantics. No mutation route, WooCommerce write, or persistent ProductDraft store exists. Production writes remain `NOT_AUTHORIZED`. Next: SHOP-03 controlled WooCommerce write architecture.

SHOP-03A is complete: immutable approved-revision eligibility, exact authorization, controlled-plan idempotency, deterministic preview, and an isolated fake/dry-run adapter are implemented. ProductDraft contracts remain 1.0.0; real WooCommerce writes are `NOT_IMPLEMENTED`, production writes are `NOT_AUTHORIZED`, and SHOP-03B requires separate authorization.
# Shopping controlled deployment roadmap

- SHOP-03B1: controlled live adapter contract and credential boundary — complete in intercepted validation mode; external requests 0, live writes 0.
- SHOP-03B2: one-product controlled pilot — next, contingent on separate exact product, revision, intent, and execution-time authorization.
## Shopping operator UI

- **UI-01 complete:** internal read-only `GET /homepage`, backed only by
  same-origin `GET /dashboard`.
- **UI-02 complete:** internal read-only Product Management Console at
  `GET /homepage/product-management`.
- **OPS-01 next:** staging Caddy, authentication, and monitoring; UI-02 adds no
  public opening or authentication change.

## PI-009A2 — Immutable Runtime Source Isolation

Priority: Production blocker

Goal:

Remove AIControlCenter runtime dependence on the mutable Git working tree.

Target architecture:

`runtime/venvs/<runtime-id>`
provides the immutable Python dependency environment.

`runtime/sources/<runtime-id>`
provides the immutable application-source snapshot.

The runtime wrapper must derive both artifacts from the same approved runtime
identity and must not use the repository root as the application PYTHONPATH.

Production authorization remains blocked until source isolation is validated.

## PI-009A2 Execution Plan

1. A2.1 — implement and test immutable source builder/validator and repository
   wrapper template
2. A2.2 — explicitly authorize and create one immutable source artifact
3. validate source artifact read-only
4. A2.3 — explicitly authorize wrapper cutover and one service kickstart
5. prove loaded application source is inside the immutable Runtime artifact
6. rerun PI-009 Technical Production Authorization Review

Production remains blocked until
`RUNTIME_SOURCE_ISOLATION_VERIFIED`.

### PI-009A2 New Candidate Requirement

The former Candidate cannot complete source isolation because its application
state defaults are repository-relative.

Execution plan:

1. commit state-isolation repair
2. complete immutable source artifact tooling on the repaired source
3. build a new Runtime Candidate from the repaired commit
4. validate new Candidate plus immutable source artifact
5. authorize operational source artifact creation
6. authorize wrapper cutover
7. rerun PI-009 Production Authorization Review

### PI-009A2 A2.1 Complete

The next Runtime Candidate will use the A2.1 completion commit as its immutable
source identity because the canonical bootstrap build contract is HEAD-only.

Next steps:

1. authorize one new Runtime Candidate build
2. build Candidate with canonical bootstrap
3. validate Candidate metadata and full test gate
4. create matching immutable source artifact under separate authorization
5. validate source/state identity
6. authorize immutable-source wrapper cutover
7. rerun PI-009 Production Authorization Review

### PI-009A2 A2.2A Complete

New Runtime Candidate `7b171f135dc7` is validated.

Next:

1. human-authorized operational immutable source artifact creation
2. operational source artifact validation
3. human-authorized immutable wrapper cutover
4. one launchd kickstart
5. final PI-009 Production Authorization Review

### PI-009A2 A2.2B Complete

Runtime `7b171f135dc7` and its immutable source artifact are operationally
validated as a matched pair.

Next:

1. freeze A2.3 live-cutover evidence
2. human-authorized Runtime pointer switch
3. install immutable-source live wrapper
4. exactly one launchd kickstart
5. validate immutable live execution
6. run final PI-009 Production Authorization Review

### PI-009A2 A2.3 Complete

Remaining Production path:

1. final deployment regression gate
2. final operational validation
3. PI-009 human Production authorization

### PI-009 Production Authorization Complete

The immutable AIControlCenter Runtime has passed the final technical gate and
received explicit human Production authorization.

Milestone:

`PI_009_PRODUCTION_AUTHORIZED`

Next platform milestone:

`AI-PROVIDER-01 — Secure Provider Integration`

### AI-PROVIDER-01B Complete

Authenticated OpenAI connectivity validated.

Next:

AI-PROVIDER-01C — Production Workflow Integration and Candidate Runtime Promotion

### AI-PROVIDER-01C-B Complete

Candidate Runtime and immutable source `102b8f1fa862` are validated without
Production activation. The network-free canonical workflow passed with the
fake provider and zero provider calls.

Next gated milestone:

AI-PROVIDER-01C-C — separately authorized Production promotion

### AI-PROVIDER-01 Complete

Provider architecture, OpenAI transport, BrainAgent integration, immutable
Runtime promotion and authenticated Production-artifact workflow validation are
complete.

Next operational priority:

`SEC-01 — Production Secret Injection & Rotation`

Then:

`OPS-01 — Production Observability & Health`

Notion remains deferred until the final phase.
# Security delivery roadmap

## SEC-02 — Control Plane Governance Automation (active)

- [x] A0 — authoritative governance capability inventory.
- [x] A1 — governance domain and JSON contract freeze:
  `SEC_02A1_FINAL_STATUS=GOVERNANCE_DOMAIN_AND_JSON_CONTRACT_FROZEN`.
- [ ] A2 — pure authorization domain models and focused tests implemented;
  target `SEC-02A2_AUTHORIZATION_DOMAIN_MODELS_VALIDATED` awaits external tests.
- [ ] A3 — pure precondition snapshot and stale semantics implemented; target
  `SEC-02A3_PRECONDITION_SNAPSHOT_AND_STALE_SEMANTICS_VALIDATED` awaits external
  focused tests.
- [ ] A4 — mutation budget and invocation accounting (next).
- [ ] A5 — receipt, failure, and evidence domain models.
- [ ] A6 — v1 JSON Schema implementation and registry.
- [ ] A7 — application ports and orchestration.
- [ ] A8 — compatibility adapters for existing bounded capabilities.
- [x] A9 — durable evidence policy and deterministic READ ONLY API projection
  validated by the focused Governance regression, `265 passed in 1.45s`; not
  the full repository regression.
- [ ] A10 — architecture closure review (next).

A3 is pure domain only. It is not Production mutation implementation, did not
execute tests or Production validation, and does not claim the SEC-02A
architecture-closure milestone. Next is
`SEC-02A4 MUTATION BUDGET AND INVOCATION ACCOUNTING`.

- SEC-01B: repository implementation and fake-secret validation.
- SEC-01C: `COMPLETE` — Production daemon secret delivery validated against matching immutable source/config (`PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`).
- SEC-01D: next — Secret Lifecycle & Recovery Validation.
- SEC-01: remains open pending its later independently authorized phases.
- Notion sync: `DEFERRED_UNTIL_FINAL_PHASE`.
- SEC-01C-R1 historical gate: the repository immutable-source wrapper repair was validated after the prior attempt consumed two installs and one restart, recovered HTTP without immutable convergence, and did not roll back. At R1 closeout, live replacement and one restart still required new exact human authorization; Runtime `102b8f1fa862` had importable `jsonschema`.
- SEC-01C-R2 through R3Q2: R2 found the mutable workers config dependency; R3 froze its immutable binding without intended mutation; R3Q stopped on precondition drift with zero attempts; and separately authorized R3Q2 made one representation-only correction and one restart, validating no mutable repository dependency, HTTP `200/200/405`, and secret presence without provider calls.

## Security roadmap closeout

- [x] SEC-01 — Production provider-secret lifecycle:
  `PRODUCTION_SECRET_LIFECYCLE_VALIDATED`.
- [x] SEC-01D — restart recovery, reboot recovery with evidence recovery,
  missing-secret fail-closed behavior, both rotation paths, provider lifecycle,
  and candidate cleanup.
- [x] SEC-01 FINAL quality gate — R1 retained as
  `INVALID_RAW_PYTEST_GATE_INVOCATION`; R2 diagnosed read-only; R3 passed 3/3
  representative selections (17 tests); authoritative canonical-harness R4
  passed 2402 tests with 5 deselected and 437 non-failing warnings, with no
  repository modification by tests or Production mutation.
- [ ] `SEC-02_CONTROL_PLANE_GOVERNANCE_AUTOMATION` — active Control Plane
  security/governance milestone; A0 and A1 complete, A2 next.

The three permanent exception records remain
`SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`,
`SEC-01D-C3-BOOT-PARSER-DEFECT`, and
`SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`. SEC-01 completion neither authorizes a
Production mutation nor completes the wider project.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## OPS-01A — Runtime Health Service Topology Reconciliation — COMPLETE

Production milestone:

`AIControlCenter_RUNTIME_HEALTH_MODEL_PRODUCTION_DEPLOYED`

Immutable release `ed2424e39bb1` is active on the canonical Mac Control Plane
API.

Completed:

- [x] Replace the legacy Linux/systemd Runtime Health projection with the Mac
  Production service-topology contract.
- [x] Model required versus optional services explicitly.
- [x] Validate the candidate Runtime and immutable Source independently from the
  Production `runtime/current` pointer.
- [x] Validate canonical and public HTTP operation after Production promotion.
- [x] Preserve immutable Source integrity and ProductDraft persistent state.
- [x] Confirm that `healthy=false` correctly represents the currently missing
  required Application Scheduler rather than a canonical API failure.

OPS-01B final milestone:

`OPS-01B_RECURRENCE_PREVENTION_VALIDATED_AND_CLOSED`

Goals:

- deploy the dedicated Application Scheduler on the Mac Control Plane;
- expose its launchd lifecycle through the authoritative service manifest;
- produce a fresh durable heartbeat;
- converge Runtime Health from truthful degraded state to `healthy=true`.

OPS-01B recurrence prevention added a reusable,
fail-closed Scheduler log readiness contract consumed by the existing runtime
`ServiceHealth` observation through an injected adapter and by the canonical
deployment lifecycle gate, `application_scheduler_bootstrap.py`. Dry-run and
apply share read-only eligibility checks, including service registration; apply
alone may issue one bootstrap. Missing-file provisioning remains separate.
Executor preconditions do not attest to human authorization; that decision
remains with the outer governed executor immediately before one bounded
Production invocation. There is no kickstart, retry, rollback, or automatic
remediation.

The immutable Production API entrypoint is now the outer macOS composition
`ops.macos.runtime.application:app`; `core.api.app` remains platform-neutral
and has no direct `ops.*` dependency.

Application Scheduler Production recovery was already operational before this
closeout. Focused recurrence validation passed. Canonical deployment regression
invocation #1 failed with 13 test failures caused by umask-sensitive Scheduler
fixtures and a controlled-live test that hashed the independently mutable
real-home AIControlCenter tree. The defects were corrected only in tests,
without weakening Product contracts. The corrected focused scope passed 39
tests under umask `077`, with the controlled live root explicitly confined to
`/private/tmp`. Canonical deployment regression invocation #2 passed with
`RC=0`. Exactly two canonical invocations were made because code/test changes
occurred after invocation #1; no canonical test count is claimed for #2.

No Production mutation occurred during recurrence-prevention validation. No
additional activation, bootstrap, log provisioning, kickstart, retry, or
rollback was performed. OPS-01B recurrence prevention is validated and
OPS-01B is closed.

Separate maintenance work:

- Shadow `:18100` release alignment;
- explicit candidate/release selector for Shadow tooling;
- removal of legacy automatic external rollback semantics.

No Notion synchronization is claimed. WordPress and Shadow work remain
deferred as separate future work.

## PA-05 — WooCommerce Headless Adapter v1

Status: **VALIDATED**

Milestone: `WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`

- [x] Preserve AIControlCenter as sole Control Plane and `core.shopping` as
  owner of ProductDraft lifecycle, product policy, workflow, recommendation,
  customer automation, governance, and shopping business logic.
- [x] Preserve WordPress as CMS-only and WooCommerce as
  commerce-engine-only.
- [x] Keep `integrations.woocommerce` replaceable and read-only, with
  `ops.macos.runtime.application` as the outer composition root.
- [x] Verify `CORE_OPS_IMPORT_COUNT=0` and
  `CORE_INTEGRATIONS_IMPORT_COUNT=0`.
- [x] Fail closed to `UNAVAILABLE` while WooCommerce deployment,
  configuration, authentication, and catalog/API availability remain
  `UNKNOWN` or unproven.
- [x] Emit no invented `canonical_manifest` evidence for missing, duplicate,
  malformed, schema-invalid, or unreadable lookups; require exactly one
  successfully returned identity for validated evidence.
- [x] Preserve AIControlCenter-owned reserved governance facts through typed,
  boolean-only extensions; record `commerce_engine_only=true` and
  `automatic_retry=false` for WooCommerce.
- [x] Consolidate fallbacks in `UnavailableCapabilityObserver` and keep
  platform-neutral `create_app` free of WooCommerce, n8n, and OpenClaw
  discovery, preserving PA-02/PA-03 outward fail-closed compatibility.
- [x] Expose only `GET /shopping/providers/woocommerce`, with no mutation
  endpoint or product, order, inventory, customer, coupon, execute, retry, or
  Production mutation action.
- [x] Pass 91 focused tests after the final architecture correction and one
  PA-05 canonical deployment regression with `RC=0`.
- [x] Perform no Production WooCommerce request, external commerce I/O, or
  WordPress, WooCommerce, Shopping SQLite, Docker, launchd,
  `runtime/current`, Caddy, Ubuntu, credential, database, plugin, or theme
  mutation.

## Next production sprint — SHOP-CMS-01

`SHOP-CMS-01 — WordPress + WooCommerce Runtime Foundation` will establish the
actual runtime, persistent-state, secret, backup, health/readiness, manifest,
and activation architecture before public storefront exposure. The Production
WordPress/WooCommerce runtime is not yet claimed deployed, public storefront
availability is not yet claimed, and no Notion synchronization is claimed.

## SHOP-CMS-01A — Runtime Foundation Phase A

Status: **VALIDATED AND CLOSED**

Milestone: `SHOPPING_RUNTIME_FOUNDATION_VALIDATED`

- [x] Model one Mac-owned, Ubuntu-independent `shopping-runtime` lifecycle
  (`docker-compose-on-colima`, `NOT_DEPLOYED`).
- [x] Model WooCommerce as the hosted `wordpress-plugin-commerce-engine`
  capability with activation unauthorized, not an independent daemon.
- [x] Preserve AIControlCenter as sole Control Plane; WordPress as CMS;
  WooCommerce as commerce engine/provider-record owner; Ubuntu as stateless.
- [x] Validate fail-closed discovery/readiness, named-volume and backup/restore
  contracts, secret separation, loopback WordPress exposure, no MariaDB host
  port, and bounded mutation governance.
- [x] Complete validation: 72 initial focused passes; canonical #1 `3151
  passed, 2 failed, 5 deselected` with only two stale service-count tests;
  corrected targeted 2 passed; focused compatibility 47 passed; canonical #2
  `RC=0`; exactly two canonical invocations.
- [x] Preserve zero direct core imports of outer `ops` and `integrations`.
- [x] Perform no Production/runtime mutation and claim no runtime/storefront
  availability or Notion synchronization.

## Next phase — SHOP-CMS-01B

`SHOP-CMS-01B — bounded Production runtime activation`

1. Preflight and secret/storage readiness.
2. Dedicated Colima profile activation.
3. Read-only reconciliation.
4. Separately authorized image/runtime provisioning if required.
5. Bounded WordPress + MariaDB startup.
6. Read-only health validation.
7. Separately authorized WordPress/WooCommerce bootstrap.
8. WooCommerce API/catalog readiness validation.

Next runtime milestone: `SHOPPING_RUNTIME_ACTIVATED`.

Future storefront milestone: `SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## SHOP-CMS-01B — Activation phase current state

Status: **IN PROGRESS / NOT ACTIVATED**

- [x] Keep `SHOPPING_RUNTIME_FOUNDATION_VALIDATED` achieved.
- [x] Validate bounded Compose JSON array, object, NDJSON, and empty-output
  parsing with fail-closed malformed/scalar/non-object handling.
- [x] Set desired loopback WordPress binding to `58082`, keep MariaDB
  unpublished, derive reserved ports from the canonical service manifest, and
  classify a healthy publisher on a reserved port as `PortCollision`.
- [x] Consume exactly one dedicated Colima-start authorization; observe stored
  WordPress/MariaDB containers and volumes during later read-only
  reconciliation without treating restart-policy effects as Compose-up
  authorization.
- [ ] Perform a separately human-authorized WordPress port cutover from the
  conflicting live `58081` binding to desired `58082`.
- [ ] Reconcile the cutover read-only and prove WordPress application
  readiness.
- [ ] Supply controlled bootstrap secrets and separately authorize
  WooCommerce bootstrap; prove namespace/API/catalog readiness independently
  of container health.
- [ ] Achieve `SHOPPING_RUNTIME_ACTIVATED`.
- [ ] Begin `SHOP-STOREFRONT-01` only after runtime activation.

The service manifest and WooCommerce capability remain `NOT_DEPLOYED`. No
port cutover, Compose mutation, WooCommerce activation, automatic retry or
rollback, new Production authorization, Caddy mutation, Ubuntu mutation, or
Notion synchronization occurred during the correction closeout.
