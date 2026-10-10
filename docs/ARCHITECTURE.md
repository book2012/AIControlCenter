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


### Production guest customer isolation implementation (2026-10-07)

Implemented an explicit production guest API factory in core/shopping/guest_runtime.py. Each normalized Korean mobile number maps to a distinct durable internal customer; customers do not sign up or log in to WooCommerce. Twilio Verify alone provides trusted phone evidence; the factory seeds no synthetic verification. Per-phone and global quotas, browser challenge binding, unknown-outcome no-resend rules, restart-safe identity and suspended-customer denial protect verification. Separate durable Mac storage and a PROD HTTPS origin are mandatory.

Checkout and order lookup resolve the authenticated customer's verified phone rather than a fixed test phone. A private-draft prewrite guard checks explicit confirmation, customer/session ownership, lines, quantities and refreshed server quote before invoking the injected governed writer. The API does not register a direct order POST or DEV fixture endpoint. Shipping/tax policy, PROD catalog/provider mapping and writer remain explicit injected ports. Transaction SMS workers are absent by design; chat and web order lookup remain the customer communication path.

Private fulfillment/order presentation was extracted to Core with compatibility aliases for DEV. Telegram routing chooses DEV/PROD before invoking a handler, verifies numeric sender/chat authority, labels replies and durably pins update IDs to environments. Completed update replay returns its original reply even if the default environment changes; ambiguous updates are not automatically redispatched. This dispatcher is intended for one bot consumer, not two competing getUpdates pollers.

Two-customer integration tests use real Core sessions, durable order ledger and drafts with fake OTP/provider ports. They exercise owned lookup, foreign draft denial, idempotent confirmation, changed quote/CSRF rejection, unknown writer outcome, anonymous origin-bound inquiry, restart and operator environment replay. No real SMS or order was generated. Current deployed DEV/PROD and Telegram poller are unchanged: this code is a tested deployment candidate, not a live PROD cutover. Remaining activation work is PROD SKU/variant mapping, private Woo credentials/customer mapping, explicit shipping policy, browser API/presentation binding and the single-bot dispatcher cutover; retain backups and rollback.

Validation: 240 scoped regression tests and both isolated Chrome checkout harnesses passed before final credential-binding checks; production customer scenarios use only fake providers. No live SMS/provider request or deployed runtime mutation.


### 2026-10-10 — Guest browser transport and customer chat notices
Homepage commerce, checkout, lookup and shared chat select same-origin `/shopping` on `bokstory.duckdns.org`; DEV retains `/__order-dev`. Production composition now provides explicit CMS-to-commerce product panels/cart metadata, customer-owned after-sales routes and private inquiry history. Bindings must be explicitly supplied; no DEV fixture mapping is inferred.

Customer chat accepts `주문 123`, `배송 123`, `입금 123`, `거래안내 123`. Verified customer/session and CSRF are required; lookup checks the order's private phone binding. Deterministic messages cover received/confirmed, private bank instructions while awaiting deposit, paid, shipped with carrier/tracking, and delivered. Every message starts `안녕하세요 agachichi 입니다`. Notices are rendered without saving them to browser storage. Order lookup shows the same notices. Reading notices never writes an order, confirms payment, changes stock, calls a carrier or dispatches SMS. Transaction SMS stays disabled pending later sender configuration; existing OTP is unchanged.

Validation: 90 targeted regression tests passed; isolated real Chrome dedicated checkout passed for DEV and production hostname transport (the production hostname resolves only to loopback), including authenticated shipping notice and no storage persistence. Guest checkout/Telegram fake harness also passed. No live provider requests or PROD activation occurred. Real production catalog/customer/shipping policy/provider writer mapping and single Telegram consumer integration remain prerequisites for PROD cutover.


### 2026-10-10 — Authorized production composition and cutover candidate
User explicitly requested immediate PROD deployment. Observed PROD Woo had zero products/orders, USD currency and taxes disabled. Database and wp-content backups were completed privately before mutation. Nineteen approved upload products were copied by stable CMS/SKU bindings into new production product/variation IDs, preserving current option stock, visibility and prices; Woo currency is KRW. No DEV customer, order, verification, session, inquiry or ledger database was copied.

Explicit Mac production Woo ports validate ai-shopping container identity and aicc_shopping DB, deny DEV endpoints and invoke bounded Woo REST controllers locally under existing CMS authority. Orders require customer-bound confirmed draft, ledger permit, refresh quote, exact lines/amount/address/customer receipt validation and private delivery digest. Internal Woo customers are distinct by Core customer; customers do not sign up. Shipping is explicitly included (zero extra fee), matching this approved version; transaction SMS remains off. Atomic serialized Woo stock reduction occurs only after authorized Telegram confirmation, with replay receipts.

Production composition provides separate durable state, existing Twilio Verify through multi-customer Core verification, bank instructions on owned chat/web lookup, local AI inquiries and private history. One durable Telegram consumer uses default PROD and explicit 개발/DEV prefixes for isolated DEV commands; operator allowlists and update-to-environment pins precede writes. DEV external-consumer mode retains its web API and notification queue without competing getUpdates. Product price/SALE/hide/stock commands maintain separate PROD projection.

Validation: 96 focused regression/production port tests pass; real Chrome production transport and guest/Telegram fake harness pass with zero external provider writes. Staged real production catalog, cart panel and homepage/product/checkout/lookup pages respond successfully. Actual customer OTP and live order/shipping remain user smoke tests, never fabricated verification.

### 2026-10-10 desktop storefront alignment

HOT and UPDATE now share the same bounded four-column feed container and photo ratios. Desktop branding uses a 38px wordmark; existing mobile branding remains responsive. Presentation-only release; commerce data and operator state are unchanged.

2026-10-10: DEV-first presentation preview combines aligned HOT/UPDATE grids, enlarged desktop branding and pale butter-yellow background (#FFFBEF). PROD remains on 927bdfd pending visual acceptance.

2026-10-10: DEV logo/header background now shares the pale butter-yellow page background; production activation remains pending.

2026-10-10: DEV bold product tags and up to six deduplicated common product-name keywords between categories and feed; links use canonical search. No search-frequency analytics are claimed.
