# AI Provider Adapter Architecture

Version: 1.0
Status: AI-PROVIDER-01A baseline implemented

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

Credentials are external secrets and API keys never belong in Git. The future
OpenAI credential contract names `OPENAI_API_KEY`. `OpenAIAdapter` validates
credential presence before reaching its injectable invocation boundary. The
01A adapter has no default network implementation and therefore cannot make an
authenticated call.

AI-PROVIDER-01A does not install, read or use a real provider credential and
performs no OpenAI, Claude, Anthropic or Ollama network request. It does not
create an environment file or change Production configuration. AI-PROVIDER-01B
is separately gated work for secure credential installation and authenticated
connectivity; 01A does not authorize or begin that work.

## Audit and operational safety

Audit metadata may identify provider, model, success/failure class and provider
request ID. It must not contain API keys, authorization headers, secret
environment values, unrestricted prompts or response content.

Production Runtime remains `7b171f135dc7`, sourced from authorized commit
`7b171f135dc7882546bf7f733208778f1aef4943`. No Runtime build, activation,
service mutation, wrapper change, Caddy change, Ubuntu operation or Production
data write is part of this sprint. PI-009 Production authorization remains
intact. Notion synchronization is `PENDING`.
