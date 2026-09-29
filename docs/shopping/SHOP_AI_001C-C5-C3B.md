# SHOP_AI_001C-C5-C3B — Offline Secret Delivery / Read Transport Composition

## Status

ARCHITECTURE CANDIDATE — OFFLINE ONLY.

C5-C3B does not grant live authenticated provider access.

It defines the provider-specific secret-delivery and authenticated-read
transport composition boundary required before C5-C3C.

## Control Plane ownership

AIControlCenter on the Mac mini remains the sole Control Plane.

Ubuntu remains a stateless infrastructure worker and receives no provider
credentials, secret-resolution authority, transport authority, or business
logic.

The generic C5-B ProviderNetworkAuthorizationGate remains OFFLINE_DENY_ONLY.

The C5-C3A TwilioAuthenticatedReadAuthority remains the only provider-specific
trusted read authorization authority.

## Credential flow

The only permitted conceptual credential path is:

    SecretReference
        -> Mac Secret Resolver
        -> EphemeralSecretLease
        -> Twilio-specific authenticated-read transport factory
        -> authenticated-read transport

Generic business logic may never resolve provider secrets.

The provider adapter may never persist or expose resolved credentials.

## Twilio credential shape

Twilio Verify v2 uses HTTPS and HTTP Basic authentication.

The provider-specific authentication contract is modeled as two independent
secret references:

- API key SID reference
- API key secret reference

The actual API key SID and API key secret are not part of application config,
JSON, database state, logs, audit records, fixtures, CLI arguments, or Git.

C5-C3B models references only.

## SecretReference boundary

A SecretReference is metadata, not a secret.

A reference may identify which Mac-side secret should later be resolved, but
must contain no credential value.

References are safe to pass through Control Plane composition only when their
existing bounded contract validates them.

C5-C3B does not introduce an alternate secret-reference type if an existing
platform SecretReference contract is available.

## Mac Secret Resolver boundary

The Mac Secret Resolver is injected behind the existing resolver port.

C5-C3B must not implement or invoke real Keychain access.

For C5-C3B tests, the resolver may be represented only by an inert/fake
implementation that proves interface compatibility.

Resolution must remain impossible from generic business or provider-neutral
authorization code.

## EphemeralSecretLease boundary

Resolved secret material must exist only inside an EphemeralSecretLease.

The lease must remain:

- short-lived
- in-memory only
- nonserializable
- nonloggable
- nonpersisted
- provider-transport scoped

The raw value must not be exposed through repr, str, JSON, audit, exception,
database, fixture, or CLI output.

C5-C3B does not create a real credential lease from Keychain.

## Transport factory boundary

Only the Twilio-specific authenticated-read transport factory may receive the
ephemeral leases needed to construct a future authenticated transport.

C5-C3B validates the factory/composition contract offline.

The C5-C3B production candidate must not:

- import or instantiate a Twilio SDK client
- import requests/httpx/urllib network clients
- open sockets
- perform DNS
- call HTTPS
- resolve Keychain
- send SMS
- perform POST/PUT/PATCH/DELETE
- retry
- use provider fallback

No transport constructed in C5-C3B may be network-enabled.

## Authorization ordering

A future C5-C3C live read must satisfy this sequence:

    exact C5-C3A authorization
        -> validated secret references
        -> Mac secret resolution
        -> ephemeral leases
        -> provider-specific transport construction
        -> exactly one allowlisted GET

Credential resolution must never occur before authorization succeeds.

A denied, expired, reused, forged, or binding-mismatched capability must result
in zero credential resolution and zero transport construction.

## GET-only scope

Future authenticated operations remain limited to:

- READ_HEALTH
- READ_EVIDENCE

No C5-C3B component enables READ_LOOKUP, START_CHALLENGE, VERIFY_CHALLENGE, SMS,
or provider writes.

C5-C2 request normalization and C5-C3A exact capability binding remain
authoritative.

## Failure semantics

Transport construction and secret-delivery failures must expose bounded reason
codes only.

Raw exception text, credential material, secret leases, provider payloads,
phone numbers, OTP values, and arbitrary URLs must never cross the boundary.

Future live timeout, connection loss, malformed provider response, or uncertain
provider result remain UNKNOWN_OUTCOME and must not invent terminal C4 truth.

## Persistence

C5-C3B adds no database schema and no durable credential state.

SecretReference metadata is configuration/Control Plane metadata only.

EphemeralSecretLease content is never persisted.

VerificationReconciliationService remains the sole durable C4 reconciliation
writer.

## Milestone separation

C5-C3B:
    architecture + offline secret-delivery / transport composition contract
    + fake/inert validation

C5-C3C:
    separately approved Mac secret resolution + real authenticated GET

C5-D:
    separately approved controlled non-production provider writes / SMS

Approval for C5-C3C does not authorize C5-D.

## C5-C3B production gate

C5-C3B is complete only when:

- existing SecretReference contract is reused
- existing SecretResolverPort boundary is reused where applicable
- existing EphemeralSecretLease contract is reused
- provider-specific transport factory boundary is isolated
- credential resolution ordering is authorization-first
- fake resolver/factory tests pass
- no real secret is created or resolved
- no Keychain access exists
- no network implementation exists
- no Twilio SDK activation exists
- no SMS path exists
- C5-B OFFLINE_DENY_ONLY remains unchanged
- C5-C3A authority remains unchanged
- focused tests pass
- reviewed patch is frozen
- real-repo full SHOP_AI regression runs once after exact patch application

C5-C3B completion does not grant live provider authorization.
