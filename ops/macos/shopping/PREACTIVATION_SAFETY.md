# Repository preactivation controls

This configuration is implementation-only desired state. No activation authority
is granted. Host Caddy remains the sole public edge, the Mac owns the Control
Plane, and WordPress/MariaDB remain engines. Production and Ubuntu are excluded.

The zero-argument observer produces fresh, value-free evidence. Its PASS scope is
**repository controls and local container topology**, not deployed security or
activation approval. `activation_status` remains BLOCKED pending effective
runtime attestation. No mutable status snapshot is part of this implementation.
The observer reads fixed local Docker metadata once per target, using the existing
trusted Mac account resolver; it never reads environment variables, logs, secrets,
WordPress options, HTTP responses or subprocess stderr.

## Public edge and compatibility

The private Control Plane Shopping REST namespace
`/wp-json/aicontrolcenter/v1/shopping` and all descendants (including the registered
`products` endpoint) are denied publicly with 403 before the sole WordPress
reverse proxy to `127.0.0.1:58082`. Caddy's path matcher normalizes decoded paths,
case, repeated slashes and dot segments. There is no global encoded-URI denial.

The parsed query matcher denies `rest_route` values naming the namespace root or
its descendants, inspecting all repeated values and decoding query keys/values.
A raw-query regular expression additionally fails closed **only for this private
namespace** for case variants, optional leading slashes, percent-encoded ASCII
spellings (including nested percent escapes), PHP dot/space key aliases and
semicolon separator ambiguity. It is anchored to a query key and namespace
boundary; unrelated query values and similarly named namespaces remain eligible.
The regex uses literal/encoded character alternatives, reviewed by synthetic tests.
These conservative private-route cases are denials, not claims that every such
spelling is accepted by WordPress.

Ordinary WordPress/WooCommerce storefront query and mutation flows are not
intentionally disabled by this control. Search, sorting, product attributes,
cart, checkout and WooCommerce AJAX requests remain eligible for the proxy,
including POST/PUT and other methods. There is no global query or method deny.
Synthetic policy tests and Caddy adaptation establish repository intent and
handler ordering only; they do not execute live requests or prove effective
runtime behavior. Activation remains **BLOCKED** until effective runtime
attestation; repository desired state is not live proof.

Caddy configuration semantics: [ordered route](https://caddyserver.com/docs/caddyfile/directives/route),
[request matchers](https://caddyserver.com/docs/caddyfile/matchers), and
[logging output](https://caddyserver.com/docs/caddyfile/directives/log).

## Logging and the remaining activation gate

`config/deployment/shopping-logging-policy.json` is a versioned policy, not a
runtime snapshot. It prohibits Authorization capture, tracing/APM, plugin secret
logging and non-generic exception projection. Caddy log sinks discard records.
The proposed WordPress deployment mounts a dedicated Apache virtual host with
null log sinks and no .htaccess overrides, and PHP configuration disabling
error logging/display and exception arguments. WordPress debug settings are
explicit, including an empty WORDPRESS_DEBUG input and a fail-closed check.

The persistent WordPress volume may contain an older wp-config; Compose inputs
cannot prove its effective constants. Likewise, source configuration cannot prove
loaded Apache modules/vhosts, PHP ini/extensions, active plugins/mu-plugins/drop-ins,
or loaded Caddy routes/loggers. An authoritative value-free observation of these
**effective** controls is still missing. No bearer request or live activation is
safe on the strength of this observer's readiness PASS. This task deliberately
adds no remote attestation subsystem or runtime mutation to solve that gap.

## Maintenance

The policy binds the complete reviewed Caddy, ingress, Compose, Colima, logging,
plugin and transport source files with SHA-256 identities. Missing files or any
unreviewed addition/change blocks readiness. When one changes, review its full
semantics, update its digest in the same policy change, and run the focused and
related ingress/control-plane-read tests. These digests identify repository source;
they do not identify or attest deployed artifacts. The fixed artifact allowlist
prevents the policy from selecting arbitrary local paths.

Repository-wide machine-specific paths predate this change, including protected
project documentation. This task removes the observer's machine identity only;
removing the existing repository-wide references conflicts with the instruction
not to update README/CHANGELOG/MASTER/ROADMAP and needs a separately scoped task.
