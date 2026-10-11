# Shared Telegram DEV relay activation

Authorized by user continuation on 2026-10-12 after explicit shared-PROD activation question. Scope is the DEV forwarding path in the existing single consumer.

Base: PROD 63e0f104457201bcd9ad8fcce7fdffde9fa2ce37. Added private bridge codec/server, forwarding client, receiver composition for disposable tests, and bridge tests. Existing PROD runtime source changes only the DEV handler selection and existing-cursor prerequisite. No order, stock, payment, customer or frontend business modules are updated. DEV remains pinned independently at ab434b9; frontend PROD remains 8d6f508.

One getUpdates consumer and the existing file lease remain. HMAC-authenticated Unix-socket requests bind DEV, allowlisted actor/chat, update ID, timestamp and nonce. Receiver has its own durable claim journal; no automatic replay after unknown outcomes, and no embedded-handler fallback in enabled mode. Existing PROD default/prefix routing remains. New private matching key config is copied from DEV without displaying credentials.

Before switching: backup current manifest, LaunchAgent and SQLite router using SQLite backup, require existing cursor and no unresolved claims, exact operator/bot binding equality, DEV receiver health and SMS-disabled check. Materialize clean pushed Git archive. Restart only PROD API/shared consumer LaunchAgent; do not restart frontend, Woo containers or Caddy. Preserve the existing cursor/journal rather than restoring over new messages.

Rollback: stop the new consumer, restore prior LaunchAgent and runtime manifest, remove the newly created relay config, then start prior service. Preserve current router DB/cursor; its snapshot is inspection evidence, not an instruction to reset consumed messages.

Tests: 96 bridge, durable ledger, Telegram, PROD guest-runtime/customer-isolation/Woo-port and order-admin regressions pass on this exact old-PROD-based branch. No real commerce mutations or external messages in tests. Live Telegram human-command confirmation remains distinct from a local authenticated read-only diagnostic.

## 2026-10-12 — Shared DEV relay activated

Shared consumer active at 0289213a1ae1aff007edcf9972a0ba7c26651a57; independently pinned DEV API ab434b9. Authenticated local read-only 주문목록 roundtrip passed without advancing the existing DEV cursor or sending a diagnostic Telegram message. DEV receiver and PROD poller/product management RUNNING; DEV/PROD API and PROD storefront return HTTP 200. PROD business modules remain based on 63e0f104; presentation stays 8d6f508; SMS disabled. Existing router/cursor preserved. Backup: prod-commerce/backups/dev-relay-20261012-064125. Actual human Telegram command and full order workflow remain to verify.

## 2026-10-12 — One Telegram greeting across DEV forwarding

Live operator DEV response confirmed the shared forwarding path but exposed duplicated greeting/environment headers. Environment routers now preserve an existing identical header instead of adding another. Nested-router replay and ordinary PROD/DEV reply regressions pass (97 targeted tests on isolated relay branch). Historical DEV fixtures 33/34 have shipment/delivery rows but no payment row; no payment or shipment state was changed.

## 2026-10-12 — Actor-scoped DEV conversation routing

The shared consumer remembers each authorized operator conversation environment for 30 minutes. Explicit DEV/PROD prefixes override it; plain replies stay in the chosen environment. Expired conversations request an explicit environment without executing a change. Only forwarding/routing modules are updated on the old-PROD-based branch. DEV Qwen conversation modules remain independently deployed.

## Activation checkpoint — 2026-10-12 07:29 KST

DEV API bb6f09fea12614758f769dcd5247fbc72efffda2 is active with operator_conversation=QWEN_DEV, operator_bridge=RUNNING, poller=EXTERNAL and codex_website_drafts=ENABLED. Shared relay e18d885770f7b97448bfb850ccda76d65ea577ab preserves PROD business base/frontend and enables actor-scoped environment memory. Live authenticated local Qwen order-list and unprefixed task-list roundtrips passed; neither bot cursor advanced and no diagnostic Telegram message was sent. Local model allocation ~3.86 GB at context 8192. Existing real order/payment/stock data was not changed.

Backups: DEV LaunchAgent com.aicontrolcenter.dev-order-api.plist.backup-20261012-072833; shared prod-commerce/backups/conversation-scope-20261012-072905. Human natural-dialogue/confirmation, timed live reminders and a real requested homepage draft remain acceptance checks. No actual customer order mutation is claimed from the local diagnostic.
