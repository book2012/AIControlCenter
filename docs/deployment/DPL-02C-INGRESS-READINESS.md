# DPL-02C — Canonical ingress readiness

DPL-02C is ready for review. The repository now owns one versioned ingress
contract at `config/deployment/ingress.json` and a deterministic read-only
service that correlates Host Caddy, the Mac Colima Commerce contract, and
Compose desired state.

Host Caddy remains the sole public edge. Its loopback upstream must use the
canonical `SHOPPING_WORDPRESS_PORT` identity and value. The Colima Commerce
binding and Compose WordPress binding must use the same source; WordPress may
publish only to loopback. MariaDB must publish no host port. The Mac Control
Plane owns the runtime, Ubuntu ownership is prohibited, WordPress is the CMS
Engine, WooCommerce is the Commerce Engine, and AIControlCenter owns business
logic.

`READY` means every required assertion is proven. Any mismatch is
`NOT_READY`; partial missing evidence is `DEGRADED`, wholly missing evidence is
`UNAVAILABLE`, and a malformed canonical contract is `INVALID`. The service
does not repair or activate configuration.

Evidence references contain repository-relative identities only. Parser and
adapter exception details are replaced with fixed messages so secrets cannot
enter reports, errors, or warnings. Inputs are copied, output ordering is
stable, and all adapters are file readers only. No Caddy, Docker, Compose,
Colima, network, launchd, SSH, Ubuntu, production, or write operation occurs.

DPL-02C excludes live runtime observation, activation, reload, restart,
network probing, and production-generated evidence. DPL-02 remains open.
DPL-02D must integrate the remaining deployment-package readiness workflow
without weakening approval, authorization, audit, or read/apply boundaries.
