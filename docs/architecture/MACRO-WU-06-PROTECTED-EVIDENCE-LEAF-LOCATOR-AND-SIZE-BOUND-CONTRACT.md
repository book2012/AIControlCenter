# MACRO-WU-06 Protected-Evidence Leaf Locator and Size-Bound Architecture Contract

## Status and scope

This architecture-only freeze closes exactly these two repository-policy
blockers:

- `NO_REPOSITORY_OWNED_EXACT_LEAF_LOCATOR_POLICY`
- `NO_REPOSITORY_OWNED_PROTECTED_EVIDENCE_SIZE_LIMIT`

It establishes the future exact protected-evidence leaf locator, leaf-mode,
content-size, stable-read, and authorization-cardinality policies. It performs
no filesystem I/O, protected-source access, content acquisition, evidence
admission or verification, Production access, or implementation change.

## Strict separation

```text
ConcreteProtectedEvidencePath
!= ProtectedExternalEvidenceFixedSourceSlotIdentity
!= ProtectedExternalEvidenceConcreteSourceLocationIdentity
!= ProtectedEvidenceLeafBasename
!= ConcreteProtectedEvidenceLeafPath
!= StableProtectedEvidenceLeafBinding
!= ProtectedEvidenceContentAcquisition
!= EvidenceAdmission
!= EvidenceVerification
!= RECOVERDecision
!= ProductionAccess
!= Authorization
!= Authority
```

`ConcreteProtectedEvidencePath` remains the protected parent/root directory. It
is not a leaf path. No value or result named above is promoted into another
boundary merely by construction, possession, or Python object identity.

## Exact repository-owned leaf basenames

The repository owns exactly this one-to-one mapping:

```text
AUTH_PLUGIN_PROTECTED_EVIDENCE_LOCATION
  -> auth-plugin.evidence

PYMYSQL_PROTECTED_EVIDENCE_LOCATION
  -> pymysql-1.2.0-compatibility.evidence

DATA_IDENTITY_PROTECTED_EVIDENCE_LOCATION
  -> data-identity.evidence

CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_LOCATION
  -> continuity-lineage.evidence
```

These exact basenames are identifiers only. They make no claim about
serialization format, content, validity, provenance, integrity, or authority.
Caller path selection is false. Caller basename selection is false. Caller
location selection is false.

The future locator permits no normalization, `resolve`, `realpath`,
`expanduser`, environment or `HOME` authority, candidate iteration, directory
enumeration, fallback, alternate source, or retry.

## Exact lexical leaf-path composition

Future repository composition is lexical only:

```text
ConcreteProtectedEvidencePath.concrete_path
+ "/"
+ exact repository-owned basename
```

No filesystem I/O occurs during composition. The resulting
`ConcreteProtectedEvidenceLeafPath` remains a zero-authority lexical value; it
does not establish existence, metadata safety, stable binding, content
acquisition, evidence status, authorization, or authority.

## Exact leaf-mode policy

The future already-open leaf must satisfy exactly this bitmask policy:

```python
stat.S_IMODE(mode) & ~0o600 == 0
```

For ordinary permission bits, the accepted modes are exactly `0000`, `0200`,
`0400`, and `0600`. Execute, group, other, setuid, setgid, sticky, or any
permission bit outside `0600` is rejected. This policy must not be described or
implemented as the numerically different comparison `mode <= 0600`.

This permission rule does not by itself establish correct type, ownership,
stable binding, readable content, or evidence validity.

## Exact content-size policy

```text
MAX_PROTECTED_EVIDENCE_CONTENT_BYTES=1048576
```

The limit applies independently to each protected evidence leaf:

```text
0 bytes               -> CONTENT_EMPTY
1..1048576 bytes      -> size-policy eligible only
>1048576 bytes        -> CONTENT_SIZE_LIMIT_EXCEEDED
```

No truncated content may be returned as success. The size ceiling is only an
acquisition safety and resource bound. It establishes no evidence validity,
provenance, integrity, admission, verification, `RECOVER` sufficiency, or
authority.

## Stable content-read model

Future content acquisition must read from the same already-verified leaf file
descriptor. Its required sequence is:

```text
pre-read fstat
-> bounded read of at most MAX_PROTECTED_EVIDENCE_CONTENT_BYTES + 1
-> reject oversize
-> post-read fstat
```

The pre-read and post-read observations must agree exactly on all of:

```text
st_dev
st_ino
st_size
st_mtime_ns
st_ctime_ns
```

Malformed or changing metadata fails closed. Acquisition must neither switch
to a pathname nor reopen the leaf between verification and reading. A stable
same-FD read does not establish external immutable-evidence verification,
immutable storage, provenance, integrity, admission, verification, `RECOVER`
sufficiency, or authority.

## Authorization cardinality

The repository freezes four distinct protected evidence source locations and
four distinct exact leaf basenames. Therefore:

```text
four protected evidence source acquisitions
= four fresh human authorizations
= four independent durable consume-once records
= four independent one-shot acquisition invocations
```

One authorization may bind exactly one source location, one leaf, one
acquisition request, and one acquisition attempt. One authorization must not
span multiple leaves.

Multiple evidence categories mapped to one source bundle do not create
additional acquisition attempts for that same leaf. They neither multiply nor
share authorization across distinct leaves.

## Preserved governance and authority boundaries

No Governance core semantics change. No SEC-02 behavior changes.
`ControlledExecutionPort` remains uncoupled. Acquisition-specific
authorization consumption remains a future separate boundary, using existing
durable SQLite semantics only as a structural precedent.

This contract grants no Production mutation authority. Mutation budget remains
exactly `0`. Mac AIControlCenter remains the sole Control Plane. Ubuntu remains
a stateless, zero-authority infrastructure worker and owns no AI workloads,
business logic, application state, or Control Plane authority.

## Preserved operational state

```text
FILESYSTEM_IO_PERFORMED=false
PROTECTED_SOURCE_ACCESS_PERFORMED=false
PRODUCTION_ACCESS_PERFORMED=false
RECOVER_EVIDENCE_SUFFICIENT=false
OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```

No protected evidence, Production system, MariaDB instance, Python runtime,
test suite, canonical workflow, or Ubuntu worker is accessed by this
architecture freeze.

## Next step

`NEXT_STEP=FINAL_ARCHITECTURE_REVIEW`. This contract is not activation
authorization and does not authorize implementation, acquisition, evidence
admission, verification, a `RECOVER` decision, or Production access.
