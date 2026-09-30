# SHOP_AI_001C-C5-C3C LIVE READ_HEALTH

## Status

Candidate implementation for the permanent non-production
Twilio authenticated READ_HEALTH runtime.

The live provider observation has already been proven manually
through the AIControlCenter control-plane boundary with:

- HTTP status 200
- exact Service SID binding
- normalized status HEALTHY
- one HTTP GET
- no retry
- no fallback
- no SMS
- no provider write
- no deployment
- Ubuntu untouched

## Scope

This runtime enables only:

- provider: `twilio.verify.v2`
- operation: `READ_HEALTH`
- method: `GET`
- endpoint shape: `/v2/Services/{ServiceSid}`
- activation: `AUTHENTICATED_READ_ONLY`

`READ_EVIDENCE` remains live-disabled in this milestone.

Provider writes and SMS remain disabled.

## Credential Boundary

Credential flow remains:

`SecretReference`
→ `SecretResolverPort`
→ `EphemeralSecretLease`
→ Twilio-specific authenticated transport boundary.

The macOS reader is allowlist-bound to explicitly configured
generic-password service identifiers.

Secret values must not cross the transport boundary as logs,
exceptions, result models, durable state, documentation, or Git
content.

## Authorization

Authorization occurs before any credential resolution.

The provider-specific capability remains:

- authority-owned
- exact-request bound
- short-lived
- one-shot
- fail-closed

Denied authorization performs zero credential resolution and zero
provider network work.

## Network Policy

The permanent READ_HEALTH runtime permits:

- host: `verify.twilio.com`
- HTTPS only
- GET only
- one request
- no redirect following
- bounded response size

It does not implement:

- POST
- PUT
- PATCH
- DELETE
- retry
- fallback
- SMS
- production activation

## Production Gate

This file does not declare the Shopping Platform production-ready.

Before this milestone is closed:

1. focused tests must pass,
2. the full SHOP_AI file-isolated regression gate must pass,
3. dirty worktree preservation must pass,
4. the protected B2S artifact must remain unchanged,
5. code must be committed,
6. canonical documentation must be updated,
7. the branch must be pushed normally without force.
