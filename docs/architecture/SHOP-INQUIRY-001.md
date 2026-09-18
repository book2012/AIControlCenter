# SHOP_INQUIRY_001

SHOP_INQUIRY_001 makes AIControlCenter the owner of read-only product inquiry
state. The inquiry API resolves the canonical product and optional variant
through the Shopping service before creating a service-owned `AG-INQ-*` ID.

The application uses the existing SQLite application-state pattern for the
default runtime repository. The dev preview uses an in-memory implementation
so tests remain isolated. Kakao OpenChat is trusted configuration only; it is
returned as an enabled handoff channel and never owns inquiry state or delivery
status. No WooCommerce write, cart, checkout, payment, or inquiry delivery
operation is performed.
