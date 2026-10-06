# Temporary size previews (DEV)
User requested arbitrary sizes on all uploaded products. The 17 stock-pending products receive presentation-only S/M/L (clothing) or FREE (bags/accessories) in a separate DEV JSON manifest. Both existing coats retain their confirmed canonical S/M/L and M/L sizes.

The UI labels the new sizes temporary and actual sizing pending. A separate size-preview-option selector maintains its own aria-pressed state; it never synchronizes to a provider variation ID or quote. Color-to-thumbnail and quantity/cart/order behavior remain unchanged. Inventory stays pending/zero; no WooCommerce, API, Telegram or PROD write.

Validate all 19 PDPs, preserve canonical variants and catalog bytes, run color/cart/chat browser regression, commit/push and activate only the immutable homepage DEV release. Rollback uses the previous homepage current manifest; keep the order API PID/config/poller unchanged.

Validation: 33 Python tests and the 15-check color/cart browser regression passed, including selecting temporary M while preserving the selected color and disabled purchase controls. No external provider requests or SMS.
