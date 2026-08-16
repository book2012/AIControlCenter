# SM-01 — Shopping Secret Management

Status: **SM-01A IMPLEMENTATION AND VALIDATION COMPLETE**

Current milestone: `SM-01A — Shopping Secret Contract & Fail-Closed Preflight
v1`

Next development milestone: `SM-01B — Secret Delivery Backend v1`

This architecture separates metadata, evaluation, delivery, materialization,
and mutation authority. After SM-01A, only layers 1 and 2 exist.

## 1. Secret Contract — implemented

`deploy/shopping/config/secret-contract.json` is the single canonical metadata
authority. It is JSON-first and value-free. Python does not duplicate its exact
canonical key table.

The current `runtime_cutover` action requires:

- `SHOPPING_WORDPRESS_PORT`
- `SHOPPING_DB_NAME`
- `SHOPPING_DB_USER`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`

The current `bootstrap` action requires:

- `SHOPPING_WORDPRESS_PORT`
- `SHOPPING_DB_NAME`
- `SHOPPING_DB_USER`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`
- `SHOPPING_SITE_URL`
- `SHOPPING_SITE_TITLE`
- `SHOPPING_ADMIN_USER`
- `SHOPPING_ADMIN_PASSWORD`
- `SHOPPING_ADMIN_EMAIL`

The current secret-classified names are:

- `SHOPPING_ADMIN_PASSWORD`
- `SHOPPING_DB_PASSWORD`
- `SHOPPING_DB_ROOT_PASSWORD`

Classification is metadata, not a stored value. The contract contains no
secret material and grants no activation or mutation authority.

## 2. Secret Preflight — implemented

`ops/macos/shopping/secret_preflight.py` is a read-only consumer and validator
of the canonical JSON contract. It performs structural fail-closed validation,
resolves required names for the requested action, and evaluates name presence
only. Values are never inspected or serialized.

Unsupported actions, unknown supplied key names, invalid contract structure,
and missing required keys produce non-success. Not-evaluated is a separate
state, not a synonym for pass or fail. The preflight performs no authorization,
mutation, secret materialization, Keychain query, or Docker, Colima, runtime,
WordPress, WooCommerce, MariaDB, Caddy, or Ubuntu access.

Compose intentionally remains plain `${SHOPPING_*}` interpolation. This keeps
read-only runtime observation independent of secret material. Neither
`.env.admin` nor `.env.woocommerce` is a runtime authority.

## 3. Secret Backend — not implemented

SM-01A implements and selects no delivery backend. SOPS, age, and Keychain are
not implemented or selected as deployed truth. A future backend must be
replaceable and remain owned by the Mac Control Plane. Ubuntu must not own,
persist, select, or govern Shopping secrets.

`SM-01B — Secret Delivery Backend v1` is the next development milestone.

## 4. Secret Materialization — not implemented

No component currently transforms backend-held material into process,
container, file, or command input. SM-01A reads no secret value and defines no
materialization lifecycle. Presence-only preflight must remain value-free even
after a backend is introduced.

## 5. Authorization / Mutation — not implemented by SM-01A

A valid contract or successful preflight is not authorization. A desired-state
package is not activation authority. Any future Production mutation requires
explicit human authorization immediately before execution. One authorization
maps to one exact, bounded invocation. There is no automatic retry or rollback.

AIControlCenter on the Mac mini M4 remains the sole Control Plane and owns
governance, policy, orchestration, approval, authorization, audit, deployment
control, and business logic. Ubuntu remains an optional stateless
infrastructure worker and owns no AI workload, application state, Shopping
secret, or Control Plane authority. Host Caddy remains the only public edge;
WordPress remains the CMS Engine and WooCommerce the Commerce Engine.

## Runtime and activation truth

The desired WordPress binding remains
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`, and desired
`SHOPPING_WORDPRESS_PORT` remains `58082`. MariaDB remains unpublished.
Shopping service and WooCommerce capability status remain `NOT_DEPLOYED`.

`SHOPPING_RUNTIME_ACTIVATED=false`

SM-01A performed no Production shopping runtime activation, port cutover,
secret delivery, backend selection, materialization, or new Production
authorization. `SHOPPING_STOREFRONT_ONLINE_READ_ONLY` remains future work after
runtime activation.

## SM-01A validation record

- Focused final validation: `111 passed, 9 warnings`
- Canonical regression: `3179 passed, 5 deselected, 447 warnings`, `RC=0`,
  executed exactly once on final code
- Implementation commit: `ffdf034ed9e1587328b6ecad35a6fcbe1381d8b0`
- Production mutation: false
- Secret values read: false
- Keychain query: false
- Secret backend/materialization: false
- Notion synchronization: false
