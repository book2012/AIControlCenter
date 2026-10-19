# DEV order lookup and Papachichi callback recovery

## Findings

The DEV order page accepted both the public order number and a phone field, but its public lookup request sent only the order number. The backend returned only operator-confirmed orders, so the valid order in `PENDING_REVIEW` was treated as missing. The public route also exposed a basic status projection by guessable order number alone.

For Papachichi, callback acknowledgement and the bridge command shared one `try` block. If Telegram's cosmetic callback acknowledgement failed, the order command was skipped and the bot returned an ambiguous-outcome message. Other failures were silently swallowed, making the cause unobservable. The prior poller logs contained no error details, so the exact exception behind the reported click cannot be reconstructed; acknowledgement failure was one concrete path that skipped command dispatch.

## Changes

- The public lookup contract requires exactly a 10-digit public order number and a phone number; the phone is normalized and matched against the confirmed private checkout draft.
- Lookup includes only `PENDING_REVIEW` and `CONFIRMED` operator states whose checkout operation and draft are confirmed. It returns the minimal public status projection, with no phone, delivery address, name, or private case data.
- The storefront sends the phone field and explains that both values must match. Basic status display remains separate from phone-verified private order details.
- The DEV Papachichi poller acknowledges callback queries independently, dispatches the existing operator command at most once per Telegram update, and does not retry after ambiguous dispatch or reply delivery.
- Poller diagnostics record only the error class and a fixed event label; they do not log phone numbers, order numbers, callback payloads, or raw exception messages.

## Validation

Regression coverage verifies correct and incorrect phone behavior, pending-review visibility, public response redaction, UI request payload and missing-phone handling, callback acknowledgement failure isolation, single dispatch after command/result failures, and PROD route contract compatibility. These are fake-provider and local tests; no Telegram update is sent, no SMS is requested, and no order mutation is replayed.

## DEV activation result — 2026-10-19

The immutable release `b48d4826f38f120052bf6ad4b78b5cada797f4dd` is active in the DEV order API, Homepage and Papachichi bot working directory. A rollback snapshot is stored in `AIControlCenterRuntime/dev-order/backups/order-lookup-callback-b48d4826-20261019-094939`.

The exact order lookup with the screenshot's number and phone returns HTTP 200 through the local API and DEV edge with `PENDING_REVIEW`, one item and KRW 229,000. Wrong and missing phone values return 404. The response does not include phone or delivery address. The local order page and its updated JavaScript return HTTP 200 and contain the phone-bound request.

Read-only WooCommerce verification still shows the existing order as `pending`, no stock reduction metadata, and quantity 3. No order confirmation, SMS, payment, shipment or inventory action was performed. DEV API health reports `environment=DEV`, `operator_bridge=RUNNING`, `poller=EXTERNAL`, and `product_management=RUNNING`.

The fake Telegram callback suite verifies that acknowledgement failure no longer skips command dispatch, that the command is sent at most once, and that error replies/logs avoid phone and order details. The real order confirmation callback was not replayed. PROD services and records are out of scope.
