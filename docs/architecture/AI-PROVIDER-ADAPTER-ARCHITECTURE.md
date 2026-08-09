# AI Provider Adapter Architecture

Version: 1.1
Status: AI-PROVIDER-01B repository implementation ready for authenticated smoke

## Decision

AIControlCenter is the sole owner of AI provider governance, provider routing,
policy, request/response normalization and audit-safe failure classification.
Business logic depends on the `ProviderAdapter` contract through the
`ProviderRouter`; it does not depend on OpenAI, Claude, Ollama or other vendor
SDK behavior.

```text
AIControlCenter business logic
    -> ProviderRouter
        -> ProviderAdapter
            -> OpenAIAdapter
            -> future ClaudeAdapter
            -> future OllamaAdapter
            -> FakeProviderAdapter (tests only)
```

The implementation extends the existing `core/providers` subsystem rather than
creating a parallel provider stack. Legacy provider entry points remain for
compatibility, but routing is now explicit and does not fall back to another
provider.

## Contract

`ProviderRequest` contains a normalized provider identity, model, ordered
messages, optional instructions, JSON-safe metadata, a positive timeout and a
bounded retry policy. Its default retry policy is exactly one attempt.

`ProviderResponse` contains normalized content, provider and model identity,
status and finish information, optional upstream request identity, optional
usage, and allowlisted audit-safe metadata. Provider content is returned to the
caller but is not included in `audit_metadata()`.

`ProviderError` supplies stable JSON/API error codes for unavailable providers,
missing credentials, invalid requests, timeouts, rate limits, upstream errors
and internal adapter errors. Router-specific duplicate and unknown-provider
errors also fail closed. Error strings, representations and serialized forms
are built from safe fixed messages and allowlisted metadata, never caught
upstream exception text.

## Routing policy

- Selection is explicit and lookup is deterministic.
- Duplicate registration is rejected.
- Unknown providers are rejected.
- No silent provider substitution is permitted.
- No paid-provider fallback is permitted.
- Vendor SDK code does not belong in the router.
- Retries must be explicitly bounded; the 01A baseline performs no retry loop.

## Credentials and provider boundaries

The OpenAI Responses API at `https://api.openai.com/v1/responses` is the OpenAI
transport boundary. Its standard-library HTTP implementation remains behind
`OpenAIAdapter` and the vendor-neutral `ProviderAdapter` contract. Each invoke
performs one POST with an explicit model, explicit input, bounded timeout and
bounded output. Automatic retry is disabled, and cross-provider fallback
remains prohibited.

`OPENAI_API_KEY` is external secret configuration. The adapter reads it only at
invocation time and supplies it to the transport as Bearer authentication. The
value is never cached, serialized, logged, returned or persisted; secret values
never belong in Git. Provider success is reduced to `ProviderResponse` content,
request identity and normalized usage. Failures use fixed, audit-safe provider
errors without unrestricted upstream bodies.

AI-PROVIDER-01B repository tests use mocked transports and make no provider
network request. The exactly-one-request authenticated smoke is pending and is
performed outside Codex by a human-controlled process. This document does not
claim that external smoke has passed.

## Audit and operational safety

Audit metadata may identify provider, model, success/failure class and provider
request ID. It must not contain API keys, authorization headers, secret
environment values, unrestricted prompts or response content.

Production Runtime remains `7b171f135dc7`, sourced from authorized commit
`7b171f135dc7882546bf7f733208778f1aef4943`. No Runtime build, activation,
service mutation, wrapper change, Caddy change, Ubuntu operation or Production
data write is part of this sprint. PI-009 Production authorization remains
intact. AI-PROVIDER-01C will handle candidate Runtime integration and promotion.
Notion synchronization is `DEFERRED_UNTIL_FINAL_PHASE`.
