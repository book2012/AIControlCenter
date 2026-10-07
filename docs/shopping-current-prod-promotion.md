# Current storefront PROD promotion — 2026-10-07

User approved promotion of the current version. Authorization is recorded; no further permission is required for this same scope. This is a technical readiness blocker, not an authorization blocker.

## Observed state

- Candidate application commit: 7a247b2a00bdf8bf95d55fd2069e7b996cdb5b24.
- DEV homepage/order API application: a099771aa2840d0e41ce53fe53f4fcded6ee6a98; DEV HTTPS facade: 7a247b2.
- PROD edge host bokstory.duckdns.org currently targets API 58081 and WordPress 58082.
- PROD WordPress plugin is pinned to immutable release ee229261459e24d1a2d73b39bbbb8e2fa4042ba9.
- The current browser suite covers a fake customer in isolated DEV; it does not establish production multi-customer readiness.

## Why direct activation is blocked

`ops/macos/shopping/dev_order_runtime.py` explicitly requires environment DEV, isolated aicc-order-dev containers and a loopback Woo facade. It seeds synthetic customer verification evidence which must never migrate. `dev_guest_phone.py` permits one test_phone and binds every authenticated browser to one guest_customer_id. `dev_guest_checkout.py` constructs shipping drafts from that fixed phone and uses a fixed Woo customer. Routing PROD to this service would mix environment and customer authority. Changing DEV labels or removing guards does not make it production ready.

## Required implementation before cutover

1. Build a separate PROD composition and private state root. Reuse Core ledger, verification, session and draft APIs; exclude synthetic session endpoints and fixtures. Derive a distinct internal customer and verified phone binding for each customer without public signup. Bind checkout, lookup and aftersales access to that customer/session.
2. Use a production Woo adapter and stable SKU mapping to new PROD IDs, including variant IDs. Copy approved product presentation/media/options/prices only; preserve existing live orders and customers. Do not migrate DEV databases or numeric IDs. Current temporary stock values must be represented honestly until real stock is confirmed.
3. Separate PROD Telegram ownership and polling. The same bot cannot have two simultaneous getUpdates pollers. Choose one environment-aware dispatcher or distinct bots; never move the existing bot to PROD leaving DEV commands ambiguous.
4. Keep transaction SMS disabled per user request. Reuse existing Twilio Verify credentials only through production customer verification binding, quotas and per-customer limits; no sender purchases or Messaging Service setup.
5. Test two distinct customers end-to-end, denial of cross-customer lookup, duplicate confirmation, stock contention, payment/shipping transitions and Telegram environment routing. Use fakes until the final live smoke test is explicitly distinguishable as a real transaction.
6. Snapshot PROD DB/media/config privately, stage an immutable release on separate loopback ports, run local smoke checks, then change only the exact PROD host routes. Retain a configuration rollback and original service; never point PROD at DEV endpoints.

## Scope and closure

Current work preserves PROD routes and data and records the candidate and blocker. No production activation has occurred. This is not a completed PROD deployment. The next implementation milestone is production multi-customer composition, not Twilio transaction SMS.
