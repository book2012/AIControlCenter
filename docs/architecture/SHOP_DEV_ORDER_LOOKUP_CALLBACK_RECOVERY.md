# DEV order lookup and Papachichi callback recovery

## Findings

The DEV order page accepted both the public order number and a phone field, but its public lookup request sent only the order number. The backend returned only operator-confirmed orders, so the valid order in `PENDING_REVIEW` was treated as missing. The public route also exposed a basic status projection by guessable order number alone.

For Papachichi, callback acknowledgement and the bridge command shared one `try` block. If Telegram's cosmetic callback acknowledgement failed, the order command was skipped and the bot returned an ambiguous-outcome message. Other failures were silently swallowed, making the cause unobservable.

## Changes

- The public lookup contract requires exactly a 10-digit public order number and a phone number; the phone is normalized and matched against the confirmed private checkout draft.
- Lookup includes only `PENDING_REVIEW` and `CONFIRMED` operator states whose checkout operation and draft are confirmed. It returns the minimal public status projection, with no phone, delivery address, name, or private case data.
- The storefront sends the phone field and explains that both values must match. Basic status display remains separate from phone-verified private order details.
- The DEV Papachichi poller acknowledges callback queries independently, dispatches the existing operator command at most once per Telegram update, and does not retry after ambiguous dispatch or reply delivery.
- Poller diagnostics record only the error class and a fixed event label; they do not log phone numbers, order numbers, callback payloads, or raw exception messages.

## Validation

Regression coverage verifies correct and incorrect phone behavior, pending-review visibility, public response redaction, UI request payload and missing-phone handling, callback acknowledgement failure isolation, single dispatch after command/result failures, and PROD route contract compatibility. These are fake-provider and local tests; no Telegram update is sent, no SMS is requested, and no order mutation is replayed.

DEV rollout is performed using immutable release artifacts. The DEV order record `2610192105` remains read-only during verification: check status and stock only. PROD services and records are out of scope.
