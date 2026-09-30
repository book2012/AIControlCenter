# SHOP_AI_001C-C5-C3C0

## Status

Offline authenticated-read runtime integration.

This stage does not grant live Twilio authorization.

## Control Plane ownership

AIControlCenter on the Mac remains the sole authority.

Ubuntu owns no provider authorization, credential resolution,
business logic, provider state, or application state.

## Execution order

The provider-specific runtime MUST execute in this order:

1. validate a bounded Twilio authenticated-read request;
2. consume the AIControlCenter-issued one-shot capability;
3. stop immediately when authorization is denied;
4. resolve only the provider-specific SecretReference values;
5. receive EphemeralSecretLease objects;
6. consume each lease once;
7. execute exactly one injected offline GET attempt;
8. normalize the provider observation before it crosses the adapter;
9. return only ProviderReadResult.

Authorization MUST occur before any secret resolution.

## Provider scope

Provider source:

`twilio.verify.v2`

Allowed operations:

- READ_HEALTH
- READ_EVIDENCE

Allowed HTTP method:

- GET

Write operations remain forbidden.

## Resource binding

READ_HEALTH:

`/v2/Services/{ServiceSid}`

READ_EVIDENCE:

`/v2/Services/{ServiceSid}/Verifications/{VerificationSid}`

Request resource identity is derived from the already authorized
TwilioAuthenticatedReadRequest. Callers cannot inject another URL.

## Secret boundary

Existing contracts are reused:

`SecretReference -> SecretResolverPort -> EphemeralSecretLease`

The provider-specific transport is the only secret consumer.

Generic shopping/business services never receive secret values.

Lease material MUST NOT be serialized, persisted, logged, returned,
included in exceptions, or copied.

## Offline executor

C5-C3C0 accepts only an injected offline GET executor.

The runtime contains no requests/httpx/socket/urllib/Twilio SDK
networking implementation.

Maximum attempts: 1.

Automatic retry: disabled.

Fallback: disabled.

## Failure policy

Authorization rejection occurs before secret resolution.

Secret resolution failure is fail-closed.

Lease consumption failure is fail-closed.

Offline executor failure is fail-closed and is never retried.

Normalization failure is fail-closed.

All adapter exceptions use bounded reason codes only.

## C5-B preservation

The generic C5-B ProviderNetworkAuthorizationGate remains
OFFLINE_DENY_ONLY.

C5-C3C0 does not add an allow path to that generic gate.

## C4 preservation

C5-C3C0 does not mutate C4 durable state.

VerificationReconciliationService remains the sole durable
reconciliation writer.

UNKNOWN_OUTCOME remains evidence and cannot be heuristically converted
into terminal verification truth.

## Explicit exclusions

C5-C3C0 performs no:

- external provider network call;
- real credential resolution;
- macOS Keychain access;
- Twilio SMS send;
- POST/PUT/PATCH/DELETE;
- retry or fallback;
- production provider activation;
- database migration;
- dashboard/API route activation;
- deployment;
- Ubuntu mutation.

## Live boundary

C5-C3C live authenticated GET remains a separately approval-gated
milestone.

Before live activation, authority registry lifecycle and issuance
identity uniqueness require an explicit production-hardening review.
