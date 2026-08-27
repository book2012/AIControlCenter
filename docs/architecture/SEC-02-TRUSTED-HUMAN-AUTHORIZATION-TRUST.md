# SEC-02 Trusted Human Authorization Trust Architecture Freeze

Status: **FROZEN**
Precision gate: `SEC02_TRUST_FREEZE_PRECISION_GATE=PASS`

## 1. Purpose and authority boundary

This architecture layer authenticates Production human authorization artifacts before existing SEC-02 governance objects are accepted as trusted facts. It establishes authenticity and immutable bindings only. It does not create execution authority.

This layer MUST NOT:

- create execution authority;
- bypass durable `consume_once`;
- bypass fresh post-consumption precondition observation;
- bypass SEC-02 `ALLOW_SINGLE_INVOCATION`;
- modify existing SEC-02 semantics;
- modify `ControlledExecutionPort` semantics;
- provide WU09-specific issuer semantics;
- provide a generic executor; or
- store Production private signing material.

The architectural separation is strict:

```text
parse != verify
verify != consume
consume != execute
```

Parsing produces no trust decision. Verification produces no consumption or execution authority. Consumption produces no execution result. Execution remains bounded by the existing SEC-02 decision and `ControlledExecutionPort` contract.

Requester, approver, and operator MUST be pairwise distinct. Issuer, intake service identity, operator, and executor service identity MUST remain distinct where applicable.

Unsigned, malformed, unverified, unknown-key, revoked-key, expired, noncanonical, ambiguous-identity, or binding-mismatched artifacts grant zero authority and fail closed.

## 2. Signed authorization envelope

One immutable, complete authorization grant envelope is signed once. The protected signed object contains every verifier-driving datum and every immutable binding required to establish the authorization facts. It includes, at minimum:

- `envelope_version`;
- `key_id`;
- `issuer_id`;
- `algorithm`;
- the authorization request;
- the approved decision;
- the complete authorization receipt;
- the mutation budget;
- the execution intent;
- the expected operator identity;
- `lifecycle_id`;
- `request_id`;
- `decision_id`;
- `authorization_id`;
- `mutation_budget_id`;
- `execution_request_id`;
- `claim_id`;
- `action_type`;
- `target`;
- `plan_digest`;
- the expected precondition snapshot digest;
- the approved scope;
- expiry; and
- the allowed invocation count.

The mutation budget MUST contain exactly one line item. That line item MUST name one exact, explicit action type, MUST set `allowed_count=1`, and MUST have all invocation, completed, and uncertain counters set to zero at intake.

Any missing, duplicated, altered, ambiguous, or inconsistent binding causes verification or intake to deny the artifact. Verification MUST cover the complete protected object, not a subset assembled after parsing.

## 3. Canonicalization profile

Canonicalization MUST use a dedicated RFC 8785 JSON Canonicalization Scheme (JCS) implementation. `json.dumps(sort_keys=True)` is not sufficient and MUST NOT be treated as RFC 8785 canonicalization.

AIControlCenter strict profile v1 requires:

- strict UTF-8;
- rejection of duplicate JSON object keys before ordinary object construction;
- prohibition of floating-point values;
- integers restricted to the safe supported range;
- rejection of invalid Unicode;
- no Unicode normalization;
- explicit, field-specific ASCII schemas or patterns for authority identifier fields; and
- profile validation and canonical re-encoding validation of the raw signed JSON.

The implementation MUST retain sufficient raw input information to reject duplicate keys and noncanonical encodings before ordinary object construction discards that evidence. Successful parsing alone does not establish canonical form or trust.

## 4. Signed bytes and cryptographic profile

The domain separator is exactly:

```text
AICONTROLCENTER-SEC02-AUTHORIZATION-V1
```

The signed byte sequence is exactly:

```text
ASCII("AICONTROLCENTER-SEC02-AUTHORIZATION-V1")
+ NUL byte
+ RFC8785 canonical protected-object bytes
```

Algorithm negotiation is prohibited. The only accepted algorithm is Ed25519.

- Signature encoding: canonical unpadded base64url.
- Decoded signature length: exactly 64 bytes.
- Public-key encoding: canonical unpadded base64url.
- Decoded public-key length: exactly 32 bytes.

Production code is verify-only. Production private-key signing APIs and Production private signing material are prohibited. Synthetic private keys are permitted only in tests and fixtures.

The future implementation dependency candidate is `cryptography==50.0.0`. It MUST be pinned and reviewed before implementation acceptance; naming it here is not implementation approval.

## 5. Trust root and path authority

The logical trust registry path is:

```text
<trusted_passwd_home>/Library/Application Support/AIControlCenter/governance/trust/sec02-human-issuers.v1.json
```

No username may be hard-coded. Path resolution is Darwin-only and MUST bind the process identity and trusted home as follows:

1. Require real UID to equal effective UID.
2. Require the bound UID to be non-root.
3. Resolve the account with `pwd.getpwuid(bound_uid)`.
4. Use only the passwd-record home directory.
5. Reject `HOME`, environment variables, command-line arguments, and caller-provided paths as sources of path authority.

The trust registry is immutable and versioned, read-only to feature runtime code, and contains public verification material only. It MUST contain no private material.

Each registry entry MUST bind:

- `schema_version`;
- `registry_version`;
- `key_id`;
- `issuer_id`;
- `issuer_type`;
- the public Ed25519 key;
- the algorithm;
- status, exactly `ACTIVE` or `REVOKED`;
- `not_before`;
- `not_after`;
- optional `revocation_effective_at`; and
- the registry digest.

Active issuer keys require both `not_before` and `not_after`. Non-expiring active keys are prohibited. Unknown, revoked, or expired keys cause `DENY`. Expired artifacts also cause `DENY`.

## 6. Filesystem policy

The trust-root path is outside Git and exists only on the Mac Control Plane. Absence, ambiguity, or any policy mismatch fails closed.

The verifier and intake path MUST enforce all of these protections:

- no path component may be a symbolic link;
- the trust directory MUST be a real directory with exact mode `0700`;
- the registry MUST be a regular, non-symlink file with exact mode `0600`;
- directory and registry ownership MUST match the exact preconfigured Control Plane UID and GID;
- registry size MUST be bounded;
- the registry MUST be opened without following symbolic links;
- the opened file MUST pass `fstat` validation;
- validation and reading MUST remain bound to the same file descriptor, inode, and device identity; and
- feature access MUST be read-only.

Path-string checks alone are insufficient. The open file identity is authoritative only after the complete path and descriptor policy succeeds.

## 7. Initial bootstrap, rotation, and revocation

Trust-root creation is a separate, out-of-band, dual-control administrative ceremony. The SEC-02 authorization-artifact intake path cannot self-authorize trust initialization. An uninitialized trust root grants zero authority.

Trust registry mutation is never performed by:

- feature code;
- authorization artifact intake;
- `ControlledExecutionPort`;
- SQLite authorization consumption;
- Docker;
- Ubuntu; or
- ordinary WU09 code.

Rotation requires explicit, out-of-band, dual-control, atomic registry replacement. There is no discovery, fetch, auto-enrollment, automatic key-trust expansion, fallback key, or alternate-key selection.

Revocation likewise requires explicit registry replacement. An artifact verified at or after its key's revocation effective time fails closed. An unconsumed authorization is not grandfathered by earlier verification and MUST fail when the applicable registry state makes its key revoked.

## 8. Operator identity

The operator identity model is `MAC_LOCAL_OPERATOR_V1`.

Operator identity MUST be obtained from a trusted Mac runtime identity observer. Caller-provided JSON identity, command-line arguments, environment values, and free-form text cannot establish operator authority.

The observed operator MUST exactly equal the signed expected operator. An ambiguous, unavailable, or otherwise unobservable identity fails closed. The operator remains distinct from requester and approver, and from issuer, intake service identity, and executor service identity where applicable.

## 9. Control Plane placement

The Mac mini M4 remains the sole Control Plane and the sole:

- trust registry reader;
- verifier;
- intake owner;
- orchestrator; and
- durable authorization consumption host.

Ubuntu has zero trust material, zero verification authority, zero authorization intake authority, zero consumption authority, and zero orchestration authority. No part of this trust layer may be delegated to Ubuntu, Docker, a Linux systemd Control Plane artifact, or a generic remote-command path.

## 10. Existing governance reuse and post-consumption flow

The implementation MUST reuse, unchanged:

```text
core.governance.control_plane.adapters.sqlite.SQLiteAuthorizationConsumptionAdapter
```

After successful trusted intake, the only permitted flow is:

```text
verified immutable facts
-> existing SEC-02 orchestration
-> consume_once
-> fresh read-only preconditions
-> exact comparison
-> SEC-02
-> require ALLOW_SINGLE_INVOCATION
-> exactly one bounded ControlledExecutionPort invocation
```

Trusted intake does not replace or weaken any step. Durable consumption occurs before the fresh precondition observation and comparison. Execution is permitted only when the existing SEC-02 governance decision is exactly `ALLOW_SINGLE_INVOCATION`, and then only for one bounded `ControlledExecutionPort` invocation.

`FAILED` or `UNCERTAIN` permanently consumes the authorization. There is no retry, claim stealing, recovery, authorization reuse, or second invocation.

The freeze records:

```text
GOVERNANCE_CORE_CHANGE_REQUIRED=NO
SEC_02_CHANGE_REQUIRED=NO
CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGE_REQUIRED=NO
WU09_FILES_CHANGE_REQUIRED_NOW=NO
```

## 11. Future generic implementation scope

The generic trust layer may later be implemented in these files:

```text
core/governance/control_plane/trust/__init__.py
core/governance/control_plane/trust/models.py
core/governance/control_plane/trust/canonical.py
core/governance/control_plane/trust/verification.py
core/governance/control_plane/trust/intake.py
core/governance/control_plane/trust/operator_identity.py
core/governance/control_plane/trust/path_policy.py

core/governance/control_plane/contracts/schemas/v1/governance-signed-authorization-envelope.json
core/governance/control_plane/contracts/schemas/v1/governance-trusted-issuer-registry.json

tests/governance/control_plane/trust/test_canonical.py
tests/governance/control_plane/trust/test_verification.py
tests/governance/control_plane/trust/test_intake.py
tests/governance/control_plane/trust/test_operator_identity.py
tests/governance/control_plane/trust/test_path_policy.py
tests/governance/control_plane/trust/fixtures/

requirements.txt
```

These paths describe future generic implementation scope only. They are not authorized for modification by this documentation-only freeze.

## 12. WU09 deferral

WU09 Production composition is deferred until the generic trust layer validates. The following files MUST NOT be modified as part of this freeze or before that validation gate permits composition:

```text
core/governance/control_plane/application/wu09_image_preload_coordinator.py
ops/macos/shopping/wu09_image_preload.py
tests/test_macro_wu09_pinned_image_preload.py
```

This layer provides no WU09-specific issuer semantics, and no WU09 Production composition is implemented now.

## 13. Freeze acceptance

This document freezes the SEC-02 trusted-human authorization trust architecture. Implementation remains future work and requires its own dependency review, generic trust-layer validation, tests, and authorization. This freeze does not authorize Production access, Production mutation, authorization consumption, trust-registry initialization or mutation, staging, commit, push, or activation.

The freeze acceptance gates are satisfied when this document alone is changed and the required documentation-only Git validations pass.
