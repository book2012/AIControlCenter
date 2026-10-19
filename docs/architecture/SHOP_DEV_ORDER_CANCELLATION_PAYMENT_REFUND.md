# DEV order cancellation, payment and refund account

This DEV-only workflow supports customer cancellation requests while an order is
awaiting review or confirmed, provided it has not shipped and no other active
case exists. Customer requests are reviewed by an operator before WooCommerce
cancellation.

The order page shows deposit/payment status as a separate stage. Operators can
record manual deposit confirmation. A paid pre-shipment cancellation requires
an approved refund case; WooCommerce cancellation restores stock only when the
order stock was previously reduced and verified.

For a paid, unshipped refund request, the customer supplies refund bank details
under a separate required consent. DEV stores the details encrypted with a
local 32-byte key and binds the record to the refund case. Admin access is
limited to an approved case after cancellation is recorded. Rejected cases and
completed refund records erase the encrypted destination. The actual bank
transfer remains manual; recording a refund requires evidence of the completed
transfer.

The DEV notice identifies collection purpose, limited access, and deletion
trigger. This is test-environment copy and is not a production privacy notice.
No PROD service, customer, order, product, or payment state is changed.

Validation covers API and store behavior, manual refund deletion, admin access,
customer order UI, and synthetic DEV WooCommerce stock concurrency. The
synthetic probe creates private fixture products and orders and deletes them
afterward; it sends no messages.
