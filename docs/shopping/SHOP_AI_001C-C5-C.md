# SHOP_AI_001C-C5-C — Provider-Specific Authenticated Read-Only Integration

## Architecture freeze

Provider: **Twilio Verify v2**.

This document freezes the provider-specific authenticated read design. It is
an offline architecture contract only. It does not authorize live provider
access and makes no production-ready claim.

- The Mac mini `AIControlCenter` remains the sole Control Plane.
- Ubuntu is untouched and remains an optional stateless infrastructure worker.
- `SHOP_AI_001C-C5-B` `OFFLINE_DENY_ONLY` remains unchanged.
- C5-C1 and C5-C2 are fully offline.
- C5-C1/C2 perform no network access, credential resolution, Keychain access,
  SMS delivery, or Twilio SDK import/use.

## Future read-only surface

The only future Twilio Verify v2 provider operations in scope are:

```text
GET /v2/Services/{ServiceSid}
GET /v2/Services/{ServiceSid}/Verifications/{VerificationSid}
```

The method and path are fixed to these authenticated read surfaces. `POST`,
`PUT`, `PATCH`, and `DELETE` are prohibited. `VerificationCheck` is out of
scope and must not be implemented or called.

No retry, fallback, route, schema, migration, or deployment is introduced by
this milestone.

## Future authentication boundary

The future C5-C3 live-read path is explicitly approval-gated and is not
enabled here:

```text
SecretReference
  -> Mac Secret Resolver
  -> EphemeralSecretLease
  -> Twilio-specific transport (future C5-C3 only)
```

Secret references remain value-free metadata. C5-C1/C2 do not resolve or
consume credentials, create a lease, construct a transport, or make a
provider request. A live authenticated read in C5-C3 requires separate
approval.

## Adapter and evidence boundary

The Twilio-specific adapter is the only future component permitted to handle
raw provider response data. Raw `to` and the raw provider payload must never
leave the adapter, appear in logs, errors, durable state, routes, tests, or
public contracts.

Only bounded normalized status/evidence may cross the provider boundary, such
as an allowlisted operation, provider source, observed timestamp, bounded
provider verification identifier where required, bounded expiry metadata where
required, and an allowlisted evidence code. The adapter must discard all
other provider fields before returning.

Provider observations are evidence, not locally invented verification truth.
In particular, `404`, `429`, `5xx`, timeout, malformed response, and unknown
outcome must remain bounded non-terminal outcomes. They must not be converted
into a successful, failed, expired, approved, or otherwise terminal
verification state. Unknown or malformed input fails closed.

`UNKNOWN_OUTCOME` remains blocked from C4 terminal admission. No provider
adapter may bypass that gate or write durable state.

## Durable ownership and non-activation

`VerificationReconciliationService` remains the sole durable writer. The
provider-specific adapter has no SQLite, persistence, migration, or
reconciliation authority; it may only provide bounded evidence through the
existing admission boundary.

This freeze authorizes no credentials, Keychain access, network call, SMS,
Twilio SDK, provider activation, production deployment, production migration,
or production route. C5-C3 live authenticated read remains a separately
approved future milestone.

RESULT: APPLIED
