# SEC-02 live security packaging foundation

Status: repository implemented; native source not type-checked on this host;
temporary package layout validated; unsigned; unregistered; non-operational.

## Frozen identity and layout

The app bundle ID is `com.aicontrolcenter.app`. The helper bundle ID and Mach
service are `com.aicontrolcenter.sec02-remediation-helper`; the LaunchDaemon
plist is `com.aicontrolcenter.sec02-remediation-helper.plist`. These repository
names do not establish a Team ID or signing authority.

The only accepted layout is:

```
AIControlCenter.app/Contents/Info.plist
AIControlCenter.app/Contents/MacOS/AIControlCenter
AIControlCenter.app/Contents/MacOS/SEC02GovernanceRemediationHelper
AIControlCenter.app/Contents/Library/LaunchDaemons/com.aicontrolcenter.sec02-remediation-helper.plist
```

The validator rejects placeholders, identifier/executable substitution,
malformed plists, arbitrary destinations, and layout drift. Raw strings never
confer signing readiness.

## Native boundaries

The source fixes `SMAppService.daemon(plistName:)` to the bundled plist and
does not expose registration or unregistration. The signing resolver inspects
signed artifacts and designated requirements, rejects ad-hoc identity,
wildcards, bundle/Team mismatch, and keeps app/helper roles distinct. Only its
role-bound output can configure mutual XPC requirements.

The helper protocol has exactly two zero-argument methods:

1. `provisionPreBootstrapRemediationJournal()`
2. `restrictGovernanceDirectoryMode0755To0700()`

They have typed results and no selector, path, mode, identity, command, or
payload. Each has a distinct control-plane authorization path; one
authorization cannot invoke both.

## Secure Enclave and enrollment

The fixed key tag is
`com.aicontrolcenter.sec02.fresh-human-presence.p256.v1`. Source fixes Secure
Enclave P-256, `WhenUnlockedThisDeviceOnly`, `userPresence`, and
`privateKeyUsage`. It contains no application password, reusable `LAContext`,
software Production fallback, or private-key export. Only public-key bytes are
SHA-256 fingerprinted.

`PRE_BOOTSTRAP_FRESH_HUMAN_KEY_PROVISIONING_AUTHORITY` is a distinct future
purpose. In its separately authorized ceremony, the signed adapter creates the
exact tagged key and persists only the public verification identity/fingerprint
in a purpose-bound record. That record grants no execution authority, is not an
ordinary issuer, cannot be caller-selected or silently replaced, and cannot
authorize journal provisioning, helper registration, or remediation.

## Journal crash and replay contract

`ABSENT` permits one create attempt whose transaction initializes a minimal
receipt: schema/version, purpose, provisioning replay fingerprint, and terminal
state. No raw authorization persists. `SAFE_EXISTING` plus the exact completed
receipt is read-only recognition. `UNSAFE_EXISTING`, `AMBIGUOUS`, and receipt
mismatch fail closed. There is no repair, retry mutation, delete/recreate,
claim stealing, lease expiry, or reset.

## Remaining Production ceremony DAG

1. `C2-1 AUTHORITATIVE_RELEASE_SIGNING_PREREQUISITE`: operator obtains an
   authoritative Developer identity and Team ID.
2. `C2-2 FRESH_HUMAN_SECURE_ENCLAVE_KEY_PROVISIONING`: one authorization and
   one exact key-provisioning/enrollment mutation.
3. `C2-3 SIGNED_HELPER_PACKAGE_AND_REGISTRATION`: sign, resolve mutual
   requirements, then separately authorize registration/approval.
4. `C2-4 PRODUCTION_JOURNAL_PROVISIONING`: one separate authorization and
   exact create-only journal mutation.
5. `03B5 GOVERNANCE_DIRECTORY_REMEDIATION`: fresh separate authorization for
   the exact `0755 -> 0700` mutation.

Repository implemented, source typechecked, package build validated, signed,
registered, and operational are distinct states and must never be collapsed.
