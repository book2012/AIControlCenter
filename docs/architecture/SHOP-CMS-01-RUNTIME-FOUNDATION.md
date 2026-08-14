# SHOP-CMS-01 — WordPress + WooCommerce Runtime Foundation

Status: **VALIDATED AND CLOSED — Phase A**

Milestone: `SHOPPING_RUNTIME_FOUNDATION_VALIDATED`

SHOP-CMS-01A established and validated versioned, read-only-first IaC and
inspection contracts. It did not authorize or perform Production activation.

## Discovered topology

The repository already contained one Compose project, `ai-shopping`, at `deploy/shopping/compose.yaml`; it was hardened in place. Its long-running services are `wordpress` (`shopping-wordpress`) and `database` (`shopping-db`). A one-shot `wordpress-cli` bootstrap is isolated behind the explicit `activation` profile. MariaDB 11.4.12 and WordPress PHP 8.3 Apache images are digest pinned; the bootstrap CLI base is also digest pinned. Both long-running services use `unless-stopped`, both have healthchecks, and WordPress waits for a healthy database.

`shopping_internal` is an internal network shared by WordPress and MariaDB. The database publishes no host port. `shopping_external` is the WordPress-side egress/host-edge network. WordPress publishes only `127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`; Host Caddy remains the sole intended public edge. The only repository bind mount is the storefront plugin, read-only. No shopping path or state is assigned to Ubuntu.

The dedicated Colima contract is `aicontrolcenter-commerce`, Docker context `colima-aicontrolcenter-commerce`, arm64/vz/virtiofs, 4 CPUs, 6 GiB memory, 80 GiB disk, Kubernetes and network address disabled, and automatic activation disabled. On 2026-08-15 discovery found the profile stopped. The active Docker context was `default`, whose daemon socket was unavailable. Consequently container, Compose-project, network and volume truth was unavailable; no runtime is claimed. Host listeners were Caddy on 58080/58443 and the canonical FastAPI upstream on loopback 58081. No observed database/storefront port was listening.

## Persistence and recovery model

Application state remains Mac-owned inside the dedicated Colima profile:

| Purpose | Compose target | Durable identity | Restore target |
|---|---|---|---|
| WordPress core/configuration, plugins/themes installed at activation, uploads | `/var/www/html` | `ai-shopping-wordpress` named volume | same named volume and target |
| WooCommerce product/order/customer records | `/var/lib/mysql` through MariaDB | `ai-shopping-database` named volume | logical MariaDB import into the same database volume |
| Repository storefront plugin | `/var/www/html/wp-content/plugins/ai-shopping-storefront` read-only bind | tracked repository path | Git checkout, not backup state |

The physical named-volume mountpoints cannot be truthfully resolved while the profile is stopped and are intentionally not guessed. Named volumes are acceptable only with stable names and the documented backup contract: a database-consistent logical export plus a WordPress-volume archive, checksums, metadata, and read-only verification. Raw database volume copying is not the primary database backup. Backup sources and restore targets must be resolved via Docker volume inspection in the dedicated context immediately before a separately authorized operation.

`ops/macos/shopping/runtime_inspector.py storage` reports readiness without exposing mountpoints or values. `backup-plan` and `restore-plan` describe future mutation but execute none. Restore requires an exact target, independent authorization, and read-only reconciliation; it never follows automatically from a failed activation.

## Secrets

`deploy/shopping/.env.example` defines names for the loopback port, database name/user/password/root password, site URL/title, and WordPress admin user/password/email. Compose references substitutions only. Local `deploy/shopping/.env`, `.env.admin`, and `.env.woocommerce` are ignored. The broader repository also ignores `configs/secrets/*.env` while allowing examples. Existing WordPress application-password and WooCommerce consumer credential conventions are environment/secret-file based. No value was read, copied, printed, or committed. Docker secrets are not currently evidenced.

Before activation, credentials must be delivered through a permission-restricted untracked file and checked for presence and file permissions without printing values. WooCommerce read credentials remain separate from the WordPress bootstrap administrator credential.

## Ownership and canonical identity

The independently operated unit is modeled once in ServiceTopology with
`service_id=shopping-runtime`, `runtime=docker-compose-on-colima`,
`supervisor=docker-compose`, `production_status=NOT_DEPLOYED`,
`lifecycle=not_deployed`, `owner=aicontrolcenter`,
`ubuntu_dependency=false`, and `state_policy=mac-owned-docker-volumes`.
WordPress and MariaDB are stack components, not independent lifecycle
services. WooCommerce is a WordPress-hosted capability, not a daemon or
independent lifecycle.

The canonical capability manifest records `capability_id=woocommerce`,
`host_service_id=shopping-runtime`, `kind=wordpress-plugin-commerce-engine`,
`production_status=NOT_DEPLOYED`, and `activation_authorized=false`. PA-05
reads this capability registry and remains fail closed. The service manifest
intentionally contains no `wordpress`, `shopping-db`, or `woocommerce`
service identity. ServiceTopology remains lifecycle truth; the capability
manifest adds capability truth and links to it rather than duplicating it.

The Mac mini M4 owns the shopping runtime. AIControlCenter remains the sole
Control Plane and retains ProductDraft lifecycle, product policy, AI
generation, recommendations, workflow, customer automation, analytics,
notification, authorization, governance, audit, orchestration, and deployment
control. WordPress remains CMS capability. WooCommerce remains
commerce-engine capability and owns provider-side commerce records only.
Ubuntu remains a stateless infrastructure worker and owns no WordPress,
WooCommerce, commerce database, customer/order, shopping application, or
Control Plane state.

## Health and readiness

The JSON inspector uses fixed read-only commands: Colima status and, only when the profile is available, `docker --context ... compose ps --all --format json`. Missing Colima, inaccessible Docker, malformed JSON, missing services, stopped services, or unhealthy services all fail closed. Runtime readiness requires healthy WordPress and database observations. WooCommerce readiness remains false until a separately configured read-only capability observation proves plugin/API and catalog readability; container health alone is insufficient.

The inspector contains no start, stop, restart, pull, build, create, delete, exec, network mutation, volume mutation, WordPress mutation, database mutation, Caddy mutation, Ubuntu transport, retry, or rollback surface.

## Future bounded activation

One human authorization must map to one bounded mutation invocation and exact
scope. There is no automatic retry or rollback. A successful mutation must not
be retried because reconciliation or observation failed; the next action is
read-only reconciliation before any new authorization or mutation.

SHOP-CMS-01B — bounded Production runtime activation — is next. Its planned
sequence is:

1. preflight and secret/storage readiness;
2. dedicated Colima profile activation;
3. read-only reconciliation;
4. separately authorized image/runtime provisioning if required;
5. bounded WordPress + MariaDB startup;
6. read-only health validation;
7. separately authorized WordPress/WooCommerce bootstrap;
8. WooCommerce API/catalog readiness validation.

The next runtime milestone is `SHOPPING_RUNTIME_ACTIVATED`. The future
storefront milestone is `SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

The `wordpress-cli` bootstrap profile is excluded from normal Compose startup.
Storefront activation has no automatic retry loop. Theme activation performs
one bounded invocation followed by validation. Running bootstrap installs
WordPress, WooCommerce, and the theme and is a distinct future mutation
requiring explicit authorization.

## Future public routing

The active Caddy configuration is unchanged: ingress health remains local, and the default handler continues to reverse proxy to the canonical FastAPI service at `127.0.0.1:58081`. A later separately reviewed change may add a narrowly scoped storefront hostname or path reverse proxy to the loopback WordPress port. It must validate WordPress canonical URL/proxy headers and preserve `/`, `/healthz`, `/__aicontrolcenter_ingress_health`, and `/homepage/product-management`. No Caddy reload is authorized by this phase.

## Phase A validation closeout

Initial focused SHOP-CMS-01 validation passed 72 tests. Canonical regression
invocation #1 reported `3151 passed, 2 failed, 5 deselected`; both failures
were stale `service_count` expectations caused by intentional ServiceTopology
expansion from 8 to 9, not a Production/runtime defect. The tests were
corrected to invariant-based manifest/service identity assertions. Corrected
targeted tests passed 2 tests, and focused compatibility after correction
passed 47 tests. Canonical regression invocation #2 passed with `RC=0`.
SHOP-CMS-01A used exactly two canonical regression invocations.
`git diff --check` passed. Direct core imports of outer `ops` and
`integrations` packages both remain 0.

No Production activation or runtime mutation occurred:

- `PRODUCTION_MUTATION=false`
- `DOCKER_MUTATION=false`
- `COLIMA_MUTATION=false`
- `WORDPRESS_MUTATION=false`
- `WOOCOMMERCE_MUTATION=false`
- `COMMERCE_DB_MUTATION=false`
- `CADDY_MUTATION=false`
- `UBUNTU_MUTATION=false`

The dedicated Colima profile was observed stopped, the active default Docker
daemon was unavailable, and no shopping runtime/container availability or
storefront listener was claimed. WordPress is not claimed online, MariaDB is
not claimed running, WooCommerce is not claimed activated, storefront routing
is not claimed active, and no Notion synchronization is claimed. Active Caddy
and canonical FastAPI public behavior remained unchanged.
