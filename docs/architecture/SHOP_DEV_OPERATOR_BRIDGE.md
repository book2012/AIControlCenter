# Private DEV Telegram command bridge

Stage 5-1 preparation, 2026-10-11 (Asia/Seoul). This feature does not activate the shared PROD consumer.

## Boundary

The existing one Bot API consumer remains the ingress. After separate authorization to deploy its updated composition, its durable environment router can forward DEV commands over a fixed private Unix socket to the independently pinned DEV API release. PROD commands retain their existing handler. No public webhook, HTTP route, new getUpdates consumer, fallback redispatch or generic command execution is introduced.

DEV socket: /Users/kyouhan/AIControlCenterRuntime/dev-order/data/operator-dev.sock. Parent must be private (0700); socket is 0600. HMAC-SHA256 uses a separate 32-byte private key, never the bot token. Request binds DEV, update ID, numeric chat/user, non-bot assertion, timestamp, random nonce and text. Receiver independently verifies signature, 60-second freshness, operator allowlist and DEV-only target before parsing commands. Response signature binds nonce, update ID, environment and reply.

Receiver claims update ID and original actor/text digest before invoking a handler. Concurrent/restarted completed requests return the same result; mismatched IDs are denied; interrupted/unknown claims require inspection and never redispatch. Client attempts once. Existing stock/payment/cancellation/return guards remain authoritative. Outgoing Telegram notifications are still owned by existing outboxes, not by the bridge.

## Preparation and activation

Both ends use private JSON: enabled (boolean), environment (DEV), hmac_key_hex (64 lowercase hex). DEV filename is operator-bridge.private.json; shared consumer filename is dev-operator-bridge.private.json in its existing private directory. Neither file is committed. Absent/disabled configuration preserves existing behavior.

DEV receiver requires AICC_EXTERNAL_TELEGRAM_CONSUMER=1. Shared consumer bridge mode requires its existing bot_cursor row; it never seeds zero or resets consumed updates. Once enabled, a failed DEV bridge never falls back to the embedded older handler.

Before activation: clean pushed Git archive, separate release pins, matching private keys, allowlist verification, existing cursor backup, socket ownership check, health and read-only DEV list command verification. Update shared consumer only with explicit PROD activation authorization. Do not repoint the entire PROD runtime to a DEV feature release implicitly.

After an unclean exit a stale socket is deliberately not unlinked automatically. Confirm no live owner before operator-controlled stale socket cleanup. Capture ambiguous command claims for inspection; never reset their journal.

## Verification and current limit

Disposable Unix sockets/fake handlers cover HMAC/actor/target rejection, bounds, expiry, duplicate and concurrent requests, restart, changed payload, unknown outcomes, signed receipt mismatch, actor/confirmation-guard propagation, disabled startup and no-retry client behavior. No live Telegram/SMS sends or PROD writes.

The DEV receiver is activated on API release ab434b9 with RUNNING health and rejected an unsigned socket probe. Shared bot forwarding composition remains unactivated; no PROD configuration was written. SMS stays held.

## Personal assistant capacity observation

Mac M4 has 24 GiB unified memory. Existing qwen3:4b Q4_K_M loaded on Ollama 0.32.1 with a 2048-token context at 2,865,674,321 bytes GPU/model allocation (~2.87 GB, 2.67 GiB). A local explicit ChatML no-thinking prefill smoke test returned a short Korean reply in 0.71 seconds. This is a smoke measurement, not a sustained concurrency benchmark.

The installed model template always opens a think block; think=false and /no_think alone produced truncated reasoning in the initial tests. Personal assistant should use a separately scoped validated template/prefill, serialize inference with shopping use and bound history/context. Do not replace the shopping model or global template silently. Use a different Telegram bot credential, fixed personal-user allowlist and separate conversation storage; personal conversation must not have commerce mutation tools.

Validation: 184 targeted order, Telegram, cancellation, return, guest-runtime and isolation regressions passed; diff whitespace and Python syntax checks passed. Socket probes use disposable fake providers. No external Telegram/SMS sends or PROD writes.
