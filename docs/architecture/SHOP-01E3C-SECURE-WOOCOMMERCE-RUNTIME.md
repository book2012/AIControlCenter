# SHOP-01E3C — Secure WooCommerce Read Runtime

## Status

IMPLEMENTED

## Decision

AIControlCenter loads the WooCommerce read credential directly from a
protected Mac Control Plane file.

The credential is not stored in Git, plist files, shell history or
Ubuntu.

## Credential Boundary

Canonical path role:

`secrets/woocommerce/shopping-woocommerce-read.env`

Required controls:

- file mode `0600`
- direct parent mode `0700`
- current-user ownership
- no symlink
- exact credential keys
- API permission marked read-only

## Runtime Activation

The non-secret runtime selector is:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

Persistent activation is not authorized by this task.

## Operational Validation

- canonical site target confirmed
- WooCommerce authenticated GET returned HTTP 200
- public Store API returned HTTP 200
- Dashboard management projection returned `READY`
- product total: zero
- product category total: one
- write operations: zero

## Next Product Task

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`

## Deferred Deployment Task

`SHOP-01E3D_READ_ONLY_PROFILE_ACTIVATION`
