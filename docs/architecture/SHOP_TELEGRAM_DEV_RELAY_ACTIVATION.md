# Shared Telegram DEV relay activation

Authorized by user continuation on 2026-10-12 after explicit shared-PROD activation question. Scope is the DEV forwarding path in the existing single consumer.

Base: PROD 63e0f104457201bcd9ad8fcce7fdffde9fa2ce37. Added private bridge codec/server, forwarding client, receiver composition for disposable tests, and bridge tests. Existing PROD runtime source changes only the DEV handler selection and existing-cursor prerequisite. No order, stock, payment, customer or frontend business modules are updated. DEV remains pinned independently at ab434b9; frontend PROD remains 8d6f508.

One getUpdates consumer and the existing file lease remain. HMAC-authenticated Unix-socket requests bind DEV, allowlisted actor/chat, update ID, timestamp and nonce. Receiver has its own durable claim journal; no automatic replay after unknown outcomes, and no embedded-handler fallback in enabled mode. Existing PROD default/prefix routing remains. New private matching key config is copied from DEV without displaying credentials.

Before switching: backup current manifest, LaunchAgent and SQLite router using SQLite backup, require existing cursor and no unresolved claims, exact operator/bot binding equality, DEV receiver health and SMS-disabled check. Materialize clean pushed Git archive. Restart only PROD API/shared consumer LaunchAgent; do not restart frontend, Woo containers or Caddy. Preserve the existing cursor/journal rather than restoring over new messages.

Rollback: stop the new consumer, restore prior LaunchAgent and runtime manifest, remove the newly created relay config, then start prior service. Preserve current router DB/cursor; its snapshot is inspection evidence, not an instruction to reset consumed messages.

Tests: 96 bridge, durable ledger, Telegram, PROD guest-runtime/customer-isolation/Woo-port and order-admin regressions pass on this exact old-PROD-based branch. No real commerce mutations or external messages in tests. Live Telegram human-command confirmation remains distinct from a local authenticated read-only diagnostic.
