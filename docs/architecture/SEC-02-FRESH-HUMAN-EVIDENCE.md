# SEC-02 Fresh Human Evidence Foundation

## R2-C1 native algorithm and key identity freeze

The sole protocol algorithm identifier is
`SECURE_ENCLAVE_P256_SHA256_USER_PRESENCE_V1` in Python and Swift. It is distinct
from the low-level encoding: ECDSA P-256, SHA-256, X9.62/DER signature encoding.
The enrolled public identity is only SHA-256 over the 65-byte ANSI X9.63
uncompressed P-256 public representation (`04 || X || Y`), formatted as exactly
64 lowercase hexadecimal characters. Private-key export is absent. Fixed-tag
lookup inspects all results and accepts only exactly one permanent private P-256
Secure Enclave key with the exact reviewed user-presence/private-key-use access
control. Software, ambiguous, or otherwise unsafe matches fail closed.

## Composite authorization correction

The Production eligibility model is a strict conjunction:

`valid exact bounded Authorization Services right + independently VERIFIED exact FreshHumanEvidenceV1 + successful durable one-attempt claim = eligibility for one bounded helper attempt`

Authorization Services success does not establish fresh-human verification and
may truthfully remain `FreshApprovalEvidence.NOT_VERIFIABLE`. Fresh-human evidence
does not grant execution, provisioning, retry, rollback, root, or Production
authority. The legacy `authorize_remediation_attempt()` still requires
`FreshApprovalEvidence.VERIFIED`; only the purpose-specific composite boundary
separates bounded-right validation from fresh-human verification. No presentation
field is mutated or synthesized.

Bounded Authorization Services presentation validation is not attempt authority,
and successful `FreshHumanEvidenceV1` verification is not attempt authority. The
bounded validator returns only `VALID`/`DENIED` disposition. Only after exact FHE
verification and `claim_once(AuthorizationReplayKey)` both succeed may the sole
exact remediation attempt be created directly in its claimed state.

Status: `REPOSITORY_IMPLEMENTED`, `SOURCE_IMPLEMENTED`, `TYPECHECKED`, and
`OPERATIONALLY_VALIDATED=false`.

SEC02-FS-MACRO-03B4R2-B freezes this exact order:

`exact eligibility -> bounded Authorization Services presentation validation -> derive AuthorizationReplayKey -> issue exact FreshHumanChallengeV1 -> obtain fresh user-presence-backed signature -> verify exact FreshHumanEvidenceV1 -> durable journal claim_once(AuthorizationReplayKey) -> create claimed exact attempt -> exactly one bounded helper attempt -> terminal durable evidence`

The immutable challenge uses the existing RFC 8785/JCS implementation and
binds schema, exact `GOVERNANCE_DIRECTORY_MODE_0755_TO_0700` purpose, the sole
governance-directory `0755 -> 0700` mutation, immutable request identity,
`AuthorizationReplayKey`, a verifier-issued 32-byte nonce, and a timezone-aware
bounded validity interval. Verification is typed as `VERIFIED`, `DENIED`,
`EXPIRED`, `NOT_READY`, or `ERROR`; only the exact enum value `VERIFIED` may
precede the durable claim.

Evidence contains only the challenge, signature, public-key fingerprint, and
algorithm/version. It contains no password, biometric data, raw Local
Authentication credential, `AuthorizationRef`, external form, reusable
`LAContext`, or generic token. Evidence grants no remediation, journal
provisioning, execution, retry, rollback, generic privilege, or Production
infrastructure authority. `PreBootstrapRemediationAttemptJournal.claim_once`
remains the sole durable one-attempt authority; there is no second journal or
TTL/lease retry model.

The selected future native mechanism is a Secure Enclave P-256 signing key with
`SecAccessControl` `userPresence` and `privateKeyUsage`, signing the canonical
challenge bytes. Native signing and verification ports are source-implemented
and type-checked. No key exists, no Keychain mutation or signature operation was
performed, and no authentication dialog ran.

An authenticated `LAContext` must never be cached, persisted, transferred, or
reused. The preferred protected-key operation supplies no reusable
authentication context. If UI integration later makes a context unavoidable,
it must be new per exact request, keep reuse duration at zero, be invalidated
after the terminal result, and never satisfy another request. Operational
freshness is not claimed until live validation exists.

Peer signing now requires opaque, purpose-specific, role-bound resolved values.
Raw strings, missing/malformed/permissive requirements, swapped roles, and
inappropriate identical requirements cannot make Production ready. Concrete
client and helper requirements remain absent and `NOT_READY`.

Production remediation remains unavailable. Remaining blockers are live Secure
Enclave key provisioning and custody, one-use user-presence validation, trusted
public-key enrollment, concrete resolved mutual XPC signing requirements,
authorized helper packaging/registration, journal provisioning ceremony, and
separately authorized end-to-end Production validation.
# 03B4R2-C provisioning boundary

The fixed-tag Secure Enclave source and distinct `PRE_BOOTSTRAP_FRESH_HUMAN_KEY_PROVISIONING_AUTHORITY` ceremony are defined in `SEC-02-LIVE-SECURITY-PACKAGING.md`. They have not been invoked.
