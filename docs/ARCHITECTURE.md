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


### DEV Verify clock-skew repair (2026-10-06)

Twilio recorded the user's recent authentication SMS as DELIVERED while the local challenge was START_UNKNOWN. Read-only provider Date samples were about two seconds ahead of the Mac clock. The DEV adapter now waits at most five seconds for small future provider timestamps, preserving the original signed-in provider receipt time and strict Core no-future checks. Larger skew or a clock that fails to advance remains denied. Both start/check are covered by a fake provider full trusted-receipt regression. An expired UNKNOWN browser cookie no longer blocks a fresh explicitly requested challenge; previous unknown evidence remains quarantined and is never replayed. Existing rate limits, OTP ownership, and PROD prohibitions stay in force. Error messages distinguish rate limits, DEV phone restrictions, and inspection. Bank fields are populated privately; existing Twilio account credentials were reused with user authorization. Transactional order SMS still requires a configured Messaging Service sender.


### DEV Telegram fulfillment and shipment SMS (2026-10-07 KST)

Operator commands: `주문내역` / `주문목록` show every order with all items, price, payment, shipment and tracking. A phone number alone or `01012345678 주문상태` lists all matching orders. `입금확인 #15` manually acknowledges payment and displays 배송준비; this does not poll a bank or charge/refund through Woo. `배송 #15 CJ대한통운 1234567890` requires confirmed order and paid acknowledgment, records 배송중 and an atomic private shipping notice. `배송완료 #15` displays 배송완료 and retains the existing 14-day aftersales window. Phone-based actions require a unique matching order or explicit order number, never implicitly change multiple orders. Carrier/tracking becomes immutable after first shipment; replay cannot downgrade completion or reset the return window.

The DEV Telegram transport prefixes every outbound message with `안녕하세요 agachichi 입니다` and splits complete lists below Telegram UTF-16 length limits. Core/PROD transport is unchanged. Confirmation and shipping SMS use the same greeting. Shipping notices share the fulfillment transaction/database, are claimed once, and recover ambiguous sends as UNKNOWN without automatic retry. Existing shipped orders are seeded HISTORICAL; pending shipping notices are suppressed after delivery completion so late configuration does not send obsolete shipping-start SMS. Verified fixed DEV phone ownership remains mandatory. Sender configuration is still disabled until a Twilio Messaging Service/SMS-capable sender is supplied; bank fields and existing credentials are preserved. No live SMS, shipment, payment, stock or PROD mutation is used for tests.

Validation: 146 scoped tests passed, including full state transitions, complete 27-order lists, exact phone ownership and ambiguous selection, immutable shipment replay, one-shot shipping SMS, timeout/restart safety and UTF-16 chunking. Chrome browser regression covers the customer page and checkout.


### DEV dedicated checkout page (2026-10-07 KST)

Product and cart checkout move to `/homepage/storefront/checkout`. Only closed, bounded product/variant/quantity lines move through per-tab sessionStorage; phone, OTP, name and address are never stored there or in URLs. The public HTML is no-store/noindex and displays no private order data. A responsive form separates phone verification, delivery and final review, with a desktop side summary/mobile stacked layout and formatted KRW amounts. Existing server quotes, OTP/CSRF/origin checks, authoritative final stock/price validation and explicit one-shot confirmation remain unchanged. Completed purchases deduct only their matching cart quantities; reload resumes the durable operation status without automatic order POST. Empty/corrupt selection fails safely with a cart link. Failed phone requests re-enable the request button while server duplicate/rate-limit protections stay in force. Product-panel inline order forms stay hidden. Existing legacy isolated preview remains compatible. Twilio transaction sender setup remains deferred; no PROD or live test orders/SMS.

Validation: real Chrome verifies single/cart transfer, desktop/mobile form, failed-SMS retry controls, authenticated delivery, explicit single confirmation, reload recovery, empty selection and no PII in storage. Existing guest checkout and order lifecycle regressions remain passing.


### DEV commerce connection recovery (2026-10-07)

The isolated WooCommerce HTTPS facade on loopback 18446 had stopped while the order API remained running, causing product and cart embeds to return 503. Manage the facade with a per-user launchd agent pinned to an immutable Git release, RunAtLoad and KeepAlive, private logs, and an explicit executable environment. Startup checks the isolated DEV container project, volumes and network before opening the listener. No product/order mutation, credential changes, Twilio activation, PROD/Caddy changes or Ubuntu access. Verify provider-backed product/cart embeds after activation; regression covers release pinning and invalid launch paths.


### Current-version PROD promotion assessment (2026-10-07)

The user authorized current-version promotion. Read-only observation found that the live DEV order composition remains fixed-phone/fixed-customer and seeds synthetic evidence; it cannot be wired to PROD. Current PROD routes and data remain unchanged. `docs/shopping-current-prod-promotion.md` records the exact candidate, observed runtime, customer/ledger separation, SKU-based product migration, single Telegram poller requirement, deferred transaction SMS, staging/backup/rollback and required multi-customer tests. This is a technical blocker rather than a renewed permission requirement; production deployment is not complete.
