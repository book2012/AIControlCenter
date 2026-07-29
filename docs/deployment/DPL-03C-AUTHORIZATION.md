# DPL-03C Deterministic Approval and Authorization

DPL-03C separates human approval evidence from execution authorization.
An `ApprovalDecision` never authorizes execution. Only the pure authorization
service may materialize an `ExecutionAuthorization`, and only from a valid,
approved, verified, unexpired decision and an unused nonce.

Every request, decision, and authorization binds the immutable package digest,
DPL-03B plan digest, Mac Control Plane target identity, a non-production
environment, the exact action scope, requester, designated approver, explicit
timestamps, a caller-supplied nonce, and a maximum of one use. Canonical JSON
and caller-supplied timestamps and nonces make IDs and digests deterministic.

Validation is default-deny. Production, mismatched bindings, rejected or
expired evidence, future issuance, replay, requester/approver identity
collision, non-ready plans, CRITICAL risk, command payloads, secrets, absolute
paths, traversal, and unavailable evidence or replay ports cannot produce an
authorization. Errors use stable reason codes and do not reflect secret input.

No custom cryptography is claimed or implemented. Approval evidence is trusted
only when a caller provides a verifier port. The replay guard is also a pure
port; DPL-03C supplies no durable nonce store, audit database, runtime adapter,
or production persistence.

An authorization is an unconsumed, bounded capability contract. DPL-03C does
not invoke or include an executor and does not call its typed consumption port.
`executor_invoked` and all production and Ubuntu mutation counters remain zero.
Production activation and production writes remain prohibited.

DPL-03D is the next step: design a separately reviewed consumption boundary
without weakening the Control Plane, production, replay, or audit constraints.
