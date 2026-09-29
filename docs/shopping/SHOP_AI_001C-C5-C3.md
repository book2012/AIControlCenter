# SHOP_AI_001C-C5-C3 — Provider-Specific Authenticated Read Integration

## C5-C3A architecture freeze

Status: ARCHITECTURE CANDIDATE — OFFLINE ONLY

C5-C3A defines the trusted authorization boundary required before a
provider-specific authenticated read can exist.

This milestone authorizes no provider network call, credential resolution,
Keychain access, Twilio SDK activation, SMS, deployment, production
activation, schema change, migration, or Ubuntu mutation.

## Control Plane ownership

AIControlCenter on the Mac mini remains the sole Control Plane.

C5-B `ProviderNetworkAuthorizationGate` remains provider-neutral and
`OFFLINE_DENY_ONLY`. It MUST NOT gain an allow path, trusted capability issuer,
caller-injected authority, provider credential, provider transport, or network
authority.

C5-C3 introduces a separate Twilio-specific trusted authorization boundary
owned exclusively by AIControlCenter.

Conceptual authority:

    AIControlCenter
      -> TwilioAuthenticatedReadAuthority
           -> issue opaque capability
           -> verify exact binding
           -> expire capability
           -> consume capability once
      -> future Twilio authenticated-read transport

The provider-specific authority does not replace or weaken the generic C5-B
deny-only gate.

## Provider and operation scope

Provider source is exactly:

    twilio.verify.v2

C5-C3 authenticated-read authorization may cover only:

    READ_HEALTH
    READ_EVIDENCE

No write operation is legal in C5-C3.

The following remain forbidden:

    START_CHALLENGE
    VERIFY_CHALLENGE
    POST
    PUT
    PATCH
    DELETE
    SMS send
    provider fallback
    automatic retry

## Exact resource binding

Every issued capability is bound to one exact request.

Required bindings:

- provider source: `twilio.verify.v2`
- one allowed read operation
- request identity
- correlation identity
- exact Twilio Verify Service SID
- exact Verification SID when operation is READ_EVIDENCE
- no Verification SID when operation is READ_HEALTH
- issue timestamp
- expiry timestamp
- opaque issuance identity

The existing strict SID contracts remain authoritative:

- Service SID: `VA` followed by exactly 32 hexadecimal characters
- Verification SID: `VE` followed by exactly 32 hexadecimal characters

Caller-controlled host, base URL, HTTP method, arbitrary path, query
parameters, credentials, or destination values are not part of the capability.

## Trusted capability model

The capability must be opaque.

Normal callers may possess a capability object but may not create a trusted
capability by constructing, copying, deserializing, subclassing, forging, or
supplying capability-shaped data.

Trust comes from AIControlCenter authority ownership, not from capability
fields supplied by a caller.

The trusted authority maintains the authoritative issuance record.

A future verifier accepts only a capability that:

1. was issued by the same trusted AIControlCenter authority;
2. has not expired;
3. has not previously been consumed;
4. matches provider source exactly;
5. matches operation exactly;
6. matches request and correlation identity exactly;
7. matches Service SID exactly;
8. matches Verification SID presence and value exactly.

A mismatch fails closed.

## Lifetime and one-shot semantics

Capabilities are short-lived and one-shot.

C5-C3A freezes a maximum capability lifetime of 60 seconds.

The production implementation must support injected time for deterministic
tests. Wall-clock access must not be scattered through business logic.

Verification consumes the capability exactly once.

A consumed capability cannot be reused.

There is no automatic retry and no second authorization attempt after
consumption.

The C5-C3A issuance/consumption registry is Control Plane runtime state only.
It is not provider state, business-domain persistence, SQLite authority, or
Ubuntu state.

No capability is written to database storage.

## Fail-closed reason contract

Authorization failures expose only bounded reason codes.

Required categories include:

- CAPABILITY_REQUIRED
- CAPABILITY_UNTRUSTED
- CAPABILITY_EXPIRED
- CAPABILITY_ALREADY_USED
- PROVIDER_BINDING_REJECTED
- OPERATION_BINDING_REJECTED
- IDENTITY_BINDING_REJECTED
- SERVICE_BINDING_REJECTED
- VERIFICATION_BINDING_REJECTED
- INVALID_REQUEST

Failure messages must not contain secrets, raw provider payloads, raw phone
numbers, OTP values, credentials, arbitrary URLs, SDK objects, or unbounded
exception text.

## Audit and privacy boundary

Safe audit metadata may contain only bounded values such as:

- provider source
- operation
- request identity
- correlation identity
- bounded reason code
- bounded opaque issuance reference
- issue / expiry / observation timestamps

The following must never enter logs, audit records, repr output, exceptions,
JSON, database storage, fixtures, CLI arguments, or Git:

- Twilio credential values
- SecretReference resolved values
- EphemeralSecretLease contents
- raw phone number
- OTP
- OTP hash or HMAC
- raw Twilio response
- raw provider `to`
- SDK objects
- bearer/basic-auth material

## C5-C2 evidence compatibility

C5-C2 provider response normalization remains authoritative.

Provider observations remain evidence, not locally invented domain truth.

Provider status such as `approved`, `failed`, or `expired` does not directly
write C4 lifecycle state.

`UNKNOWN_OUTCOME` remains blocked from terminal C4 admission.

`VerificationReconciliationService` remains the sole durable reconciliation
writer.

The Twilio-specific authorization authority has no C4 persistence authority.

## Runtime composition boundary

C5-C3A is offline.

Its runtime composition may construct only pure authorization/value objects.

It must not construct or invoke:

- Secret Resolver
- Keychain client
- EphemeralSecretLease
- Twilio SDK
- HTTP client
- provider transport
- SMS transport
- database writer
- deployment operation

A future transport is permitted only after later milestones have independently
passed their production gates.

## Future milestone separation

C5-C3A:
    architecture + trusted authorization contract, offline only

C5-C3B:
    SecretReference -> Mac Secret Resolver -> EphemeralSecretLease contract
    and authenticated-read transport composition, still offline/fake validated

C5-C3C:
    separately and explicitly approved live authenticated GET against an
    allowlisted non-production Twilio Verify resource

C5-C3C approval does not imply permission for SMS or provider writes.

## Production gate

C5-C3A is complete only when:

- C5-B OFFLINE_DENY_ONLY remains unchanged
- provider-specific authority is isolated from generic C5-B authorization
- caller-forged capabilities fail closed
- resource and identity bindings are exact
- expiration is enforced
- one-shot consumption is enforced
- privacy tests pass
- no provider network implementation exists
- no credential resolver exists
- no Keychain access exists
- no SMS path exists
- full SHOP_AI regression passes
- Git scope is exact
- documentation evidence is recorded

C5-C3A completion is not production activation and does not grant live
authorization.
