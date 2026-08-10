# Provider Secret Delivery

SEC-01A selected **Protected File-Per-Provider Secrets with Deterministic Wrapper Injection**. This is the canonical provider credential architecture.

## Responsibility boundaries

Storage is external mutable application state under `/Users/kyouhan/Library/Application Support/AIControlCenter/secrets`. The directory is `kyouhan:staff` mode `0700`; each credential is a regular, non-symlink file owned by `kyouhan:staff` mode `0600`. OpenAI uses `openai-api-key`. Credentials never belong in Git, Runtime/source artifacts, SQLite, plist files, `worker.env`, reports, or logs.

Delivery belongs to the installed macOS wrapper boundary. The generic `provider-secret-delivery.py` helper maps the active provider explicitly, validates storage, sets the canonical process environment variable, and directly executes the immutable Runtime command. OpenAI maps to `OPENAI_API_KEY`; Claude is reserved as `ANTHROPIC_API_KEY`; Ollama has no credential. Only the selected credential is mandatory.

Consumption belongs to provider adapters through `EnvironmentCredentialSource`. BrainAgent, ProviderRouter, and business logic do not know paths and do not retrieve, serialize, or pass credential values.

## Validation and startup

A credential file contains one non-empty UTF-8 value with no leading or trailing whitespace and at most one terminal newline. Missing, unreadable, symlinked, non-regular, wrongly owned, incorrectly permissioned, empty, or malformed mandatory storage fails startup with a constant redacted error. An inactive remote provider is optional, and local-only Ollama startup requires no credential.

`provider-secret-delivery.py validate --provider NAME` is read-only and emits schema-versioned JSON metadata. It never includes a value, hash, byte-derived identity, Authorization header, or secret-bearing error. Its `exec` action emits no JSON and passes the credential only in the child process environment.

Every restart or reboot reconstructs delivery from the current external file without an interactive shell, repository working directory, `launchctl setenv`, or plaintext plist value. A running process does not poll or hot-reload credentials.

## Rotation and audit

Rotation prepares a mode-`0600` `kyouhan:staff` replacement outside the secret directory, validates it without value exposure, atomically replaces the stable provider file, and adopts it through one separately authorized restart. Audit metadata is limited to provider, environment-variable name, file basename, validation classes, metadata compliance, outcome, and authorization identity.

SEC-01B changes repository representations only. The live wrapper and Production Runtime `102b8f1fa862` remain unchanged. SEC-01C requires explicit human authorization for helper/wrapper installation and any service restart. Notion synchronization is `DEFERRED_UNTIL_FINAL_PHASE`.
