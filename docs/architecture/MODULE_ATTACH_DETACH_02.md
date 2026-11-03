# MODULE-ATTACH-DETACH-02 — managed lifecycle and explicit service bindings

Date: 2026-11-03 (Asia/Seoul)
Status: code and isolated integration validation complete for the scope below.
Not production-activated. Full independent service migration is NOT complete.

## Current ownership
AI Home Datacenter is the umbrella. AIControlCenter/Mac retains platform policy,
authorization, audit, deployment and orchestration. Modules consume explicit ports.
Ubuntu remains the optional infrastructure worker; no application logic is moved.

| Module | Authoritative source / owner | Implemented attachment | Remaining live connection |
| --- | --- | --- | --- |
| Shopping | Existing core/shopping domain and separately recorded DEV/PROD releases; Atelier theme in AgachichiCommerce | Explicit existing ShoppingRuntime, OrderService, CustomerSessionBoundary and NotificationPlatform injection; isolated mock default | Reviewed real bindings, existing authorities, lifecycle ownership and authenticated E2E; write paths remain disabled |
| Creative Notes | Sites project appgprj_6ad80723fd208191b3617a9dac8ca392, version 10 observed through Sites metadata | External service reference adapter; no private note reads | Per-account authenticated service integration, not owner-token reuse |
| Personal Assistant | Existing integrations/openclaw adapter and core capability status service | Replaceable status-service injection via outer composition | Verified deployment/configuration, authenticated provider transport and execution policy |

Creative Notes is already separately hosted at
https://bok-creative-notes.kyouhan.chatgpt.site. Its version-10 metadata confirms
service ownership; it does not prove private API connectivity or new account tests.
The historical submission ZIP is packaging/legal/review material, not backend source.
No Site source, data, audience, OAuth configuration, credentials or deployment was changed.

## Lifecycle implementation
core/modules/lifecycle.py provides ModuleManager and ModuleInstance.
- Default state is DETACHED. Factories are selected explicitly and instantiated lazily.
- Factories construct adapters only; resources must be acquired in start and released
  in close. Hooks may be async. Sub-application ASGI lifespan hooks are NOT automatically
  invoked: the instance start/close contract owns lifecycle explicitly.
- Attach serializes transitions; repeated attach constructs only one active instance.
- Every admitted HTTP request holds a lease through completion, including streamed
  response work. Module-owned background tasks must also hold manager.lease(module_id).
- Detach closes admission first (DRAINING), waits for leases, then invokes close.
  New requests get 503 while draining; detached module requests get 404.
- Timeout leaves admission closed and active resources intact; no forced data loss,
  process kill or hidden retry. After work finishes, the trusted operator can retry detach.
- Start failure invokes cleanup. Cleanup failure is STOP_FAILED and blocks reattach
  until explicit cleanup succeeds. Attach cancellation cleans partially started resources;
  request cancellation releases its lease. Detach cancellation does not reopen admission.
- Attached dependents prevent parent detach; shutdown drains in reverse dependency order.
- Module exceptions remain scoped; platform health and other module routes continue.
- There is no HTTP attach/detach administrative endpoint. Only trusted in-process
  operator code may call the manager. Public requests cannot mutate selection.

This is cooperative single-process lifecycle management. Hooks must not block the
event loop or ignore cancellation. It is not OS process isolation, a distributed
lock, hard timeout enforcement or a multi-worker hot-reload system. Production
lifecycle remains under existing governed deployment control. Legacy bots/jobs
outside leases are not implicitly stopped by disconnecting a new adapter.

## Runtime entry points
1. core.api.modular:create_app — phase-01 startup-only preview, unchanged default.
2. core.api.modular:create_managed_validation_app — explicit managed validation shell.
3. integrations.module_composition:create_validation_app — outer OpenClaw provider
   composition, depending inward on the core contracts.

config/modules/all-adapters.json selects all three adapters. These are adapter
attachments, not a claim that all live operations are available. The Notes adapter
reports authenticated_api=NOT_CONNECTED; the assistant reports execution disabled;
Shopping defaults to an isolated mock catalog. No environment flag silently enables
live access. Selection manifests contain no credentials or executable import paths.
The existing core/api/app.py and launchd/Caddy/DNS entry points remain unchanged.

## Shopping authorization and read scope
core/modules/shopping_bindings.py accepts only explicit existing domain objects.
It reuses the catalog GET contract and session GET route. Selected routers are
included through FastAPI so dependency overrides bind to the new application;
raw route reuse would lose the existing session authority injection.
- Operator order reads require an injected authorizer to return exactly True for
  orders.read on every request. No authorizer, an exception, or truthy non-bool denies
  access BEFORE OrderService is called. This is operator scope, not a new customer
  ownership authority. Existing provider/OrderService rules still apply.
- Notification readiness requires notifications.status.read; no message is sent.
- Session GET reuses the existing cookie/origin/session boundary. No boundary means
  no session route, not a permissive fallback. No new identity verifier is supplied.
- Private responses are no-store; Decimal money stays exact text. Fixed errors do
  not include provider exceptions, customer data, credentials or DB paths.
- Inquiry/token fallback, operator ProductDraft reads and session/order mutations are
  not exposed by wholesale legacy-router imports. The managed shell also rejects
  non-read methods and WebSockets. This is a read integration, NOT full checkout.

## Actual dependency repair
TwilioOfflineAuthenticatedReadTransport previously imported an ops-owned pure
composition class. Moved that pure, offline composition into core/shopping/adapters
and left compatibility re-exports in the original ops path. Strict type identity,
authorization-first behavior, CONTRACT_ONLY, no network/no retry and secret-reference
semantics remain the same. Core no longer imports that host-specific ops module.
New module-core AST checks reject ops/integrations imports at any indentation.
OpenClaw provider selection now lives in integrations/module_composition.py.

## Verification
Final suites total 514 passed; fixture/in-process only:
- Managed modules + module bindings + OpenClaw/notification + Twilio offline suites: 137.
- Existing customer session API: 101 (fresh process).
- Existing order core: 9 (fresh process).
- Catalog/runtime/capability regressions: 199.
- Existing owned inquiry API: 68 (fresh process).

The first combined run exposed the route-override defect (fixed), the existing
core-to-ops import (fixed), and test collection contamination: order-core tests
import the legacy app, while session tests explicitly forbid that import. Those
suites are run in independent processes to preserve their documented isolation;
no assertion or security check was weakened. Final runs are green. Existing
TestClient and datetime deprecation warnings remain.

No production access, live port, real order/payment, private notes, SMS, Telegram,
Ubuntu operation, runtime credential-file read, token use or data migration was performed. Adapter status
is composition evidence and does not substitute for upstream operational checks.

## Production / full migration gate still open
Do not replace the existing service with the validation shell. It does not include
all current governance/operator APIs. Full source/package extraction and independent
installation, real authority injection, durable DB ownership, existing background
job enrollment, multi-worker coordination, authenticated E2E, backup/restore and
controlled rollback remain separate work. No full separation or production completion
is claimed. A generic request to finish does not provide missing per-account OAuth
sessions or prove deployment authorization in the existing governance system.
