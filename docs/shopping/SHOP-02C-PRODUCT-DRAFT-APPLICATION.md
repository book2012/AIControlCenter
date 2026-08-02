# SHOP-02C ProductDraft Application Services

Status: COMPLETE

SHOP-02C layers pure application services over the immutable ProductDraft 1.0.0 domain. Validation hashes canonical domain JSON, produces stable findings and result digests, and binds results to one revision. Replaceable authorization is deny-by-default. REQUEST_REVIEW uses the existing lifecycle policy; APPROVE, REJECT, and REVOKE require an explicitly allowed, exact-resource authorization decision and a HUMAN actor.

Audit events contain references and deterministic digests rather than secrets. Audit and idempotency adapters are isolated in-memory test implementations and are not production storage. Idempotency binds the first canonical command and result, replays an identical command, and rejects key reuse with a different digest. Approval never transfers to a superseding revision, and revocation replaces the active approval decision.

There are no API mutation routes, WooCommerce writes, network clients, persistent stores, background activation, or Ubuntu dependencies. Production writes remain `NOT_AUTHORIZED`. SHOP-02D ProductDraft read API and Dashboard projection is next.
