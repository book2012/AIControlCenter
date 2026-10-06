# Architecture

Mac mini M4

└── AIControlCenter
    ├── FastAPI
    ├── BrainAgent
    ├── ProviderManager
    ├── CommandRouter
    ├── Dashboard
    ├── Notification
    ├── Telegram
    └── Conversation Memory

Ubuntu Worker (Optional)

└── Docker
└── Storage
└── Backup
└── Immich
└── Nextcloud
└── Plex

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Service Layer

Architecture flow:

WordPress
to WooCommerce
to REST API
to AIControlCenter Shopping Domain
to AI Agent, Scheduler, n8n and Notifications

Responsibilities:

- WordPress owns presentation and CMS
- WooCommerce owns commerce data
- AIControlCenter owns business logic
- AI Agent owns content generation tasks
- n8n executes automation workflows

The current development runtime is virtual.

The final production runtime is Mac mini M4.

Ubuntu must not contain Shopping business logic, AI logic or
application state.

Detailed documentation:

docs/shopping/ARCHITECTURE.md
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## AI Shopping Platform Service Layer

WordPress
    CMS

WooCommerce
    Commerce Engine

AIControlCenter
    Business Logic
    REST API
    Adapter Factory
    AI Services
    Workflow and Approval

Ubuntu
    Temporary virtual deployment validation

Mac mini M4
    Final Control Plane and Production Runtime

Ubuntu does not own Shopping business logic or AI application state.
The final Shopping service runs under AIControlCenter on Mac mini M4.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Storefront Layer

WooCommerce provides Commerce data.

AIControlCenter consumes and normalizes Commerce data through the WooCommerce Adapter.

AIControlCenter exposes Featured, Search, Category, and Product APIs.

The WordPress AI Shopping Storefront Plugin consumes these APIs and renders the external customer-facing page.

No Shopping recommendation, pricing, inventory, AI, or workflow logic is implemented inside WordPress.
<!-- SHOPPING_M5_END -->

<!-- AI_SHOPPING_STOREFRONT_V016_ARCHITECTURE -->
## Shopping Presentation Architecture

Browser → WordPress Storefront Plugin → AIControlCenter Shopping API → WooCommerce

Responsibilities:

- AIControlCenter owns shopping business logic and orchestration.
- WordPress owns CMS and storefront presentation.
- WooCommerce acts as the commerce engine.
- Product pages consume JSON APIs.
- Missing products return HTTP 404.
- Ubuntu remains an infrastructure worker.
- Mac mini remains the Production Control Plane.

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## Mac Control Plane Runtime

Mac mini M4

- Supervisor:
  `system/com.aicontrolcenter.api.shadow`
- Runner ownership: `root:wheel`
- Application user: `kyouhan`
- Runtime commit: `1e102c001c28`
- Runtime path: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/1e102c001c28`
- Endpoint: `127.0.0.1:18100`
- Mode: `shadow-read-only`

Operational contracts:

- Repository commit:
  `1e102c001c28108bee9583294abee77ce7d43643`
- Health: HTTP `200`
- Mutating methods: HTTP `405`
- Automatic restart:
  `19761 → 19842`
- Transactional canonical apply: enabled
- Transactional rollback: enabled
- launchd bootout settle interval: 2 seconds

Ubuntu remains an optional stateless worker and
does not own AIControlCenter business logic or
application state.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->


### DEV customer order lookup (2026-10-06)

ORDER beside cart opens the existing customer portal. A POST lookup requires an authenticated OTP session, origin/CSRF, order number, and matching verified/draft phone; the former bulk-list endpoint is disabled in live DEV composition. Private delivery, confirmation, manual deposit, and fulfillment status remain separate. Authorized Telegram operators can use `입금확인 #15` / `입금상태 #15`; this records a manual deposit acknowledgment, not bank polling or a Woo payment/refund.

The existing immutable Woo order number is returned as `order_number`. A private SMS outbox watches new confirmed orders, suppresses historical backfill, and claims once before Twilio Messaging. Ambiguous/crashed sends stay UNKNOWN for manual reconciliation; ACCEPTED means provider accepted, not handset delivery. SMS does not block Telegram polling. DEV-only private `order-notification.private.json` needs bank name/account/holder and Twilio account/token/Messaging Service SID; disabled or incomplete configuration queues without sending. Existing one-number DEV verification is retained; no PROD migration or mutation.

Validation: 135 scoped regressions and real Chrome customer lookup/mobile checks passed. Full historical suite has the same 368 failures and 411 errors on unchanged c839a94; this task adds four passing tests. Chat consultation launcher is orange (#c65300) with white text.
