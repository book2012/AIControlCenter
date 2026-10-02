# PUBLIC-STOREFRONT-V2-ACTIVATION-01

This is the one-shot Mac Control Plane activation boundary for the reviewed
`public-storefront-migration/v2` Caddy state. It is distinct from every older
Colima, WordPress-start, WordPress-recovery, and Caddy observation record. Its
durable SQLite store is:

`~/Library/Application Support/AIControlCenter/authorization/public-storefront-v2-activation-01-authorization.sqlite3`

The authority is maximum-use one, bound at issuance to the candidate's exact
40-hex HEAD, a deterministic digest over this closed activation mechanism and
the reviewed runtime artifacts, the exact reviewed artifact identities, the
`aicontrolcenter-commerce` profile, the Caddy V2 digest, and ports 58081, 58082,
and 18080. Ubuntu authority, business mutation, WooCommerce writes, DNS,
database recreation, and volume recreation are permanently false.

The combined TTY boundary displays and independently binds the exact candidate
HEAD and bundle SHA before the final exact acknowledgement, then issues and
immediately runs the fixed lane. The operator source must be a clean isolated
candidate; the real worktree is only the fixed runtime target and is not
required to be clean.

## Two evidence phases

Phase A is pre-mutation host-only authorization binding. It requires the clean
candidate identity and reviewed artifact digests, exact profile and profile
digest, Colima `Broken`, proven Colima/Lima ownership of the stale
`127.0.0.1:58082` forward, reviewed existing generation IDs, exact named
volumes, ports 58081/58082/18080, effective Caddy `PRE_V2`, and all denied
authority flags. It deliberately performs no Docker container or volume
inspection, because the Docker endpoint is not observable while Colima is
Broken.

After durable claim, exactly one authorized Colima repair may be attempted.
Only if it returns success does Phase B prove profile `Running`, Docker API
reachability, the exact existing MariaDB and WordPress IDs, exact named volume
attachments, MariaDB healthy with no published host port, and no recreation.
Any mismatch fails closed before WordPress start. The only permitted start is
`docker ... container start <exact-existing-wordpress-id>`; Compose-up,
container create/recreate/remove, and volume create/remove are absent.

Only after Phase B may the exact existing WordPress container be started. The
lane then proves WordPress health, `127.0.0.1:58082->80/tcp`, Colima-managed
forwarding, and WordPress server-side connectivity to
`host.docker.internal:58081`.

Before reload, the exact desired Caddy digest, offline validation, bounded
public GET policy, preserved development Basic Auth, private/REST/management
denials, and no browser-to-Woo path are required. Exactly one graceful Caddy
reload may be attempted. Afterward, a local Caddy admin/attestor observation
must prove the loaded V2 document: production host and root upstream,
bounded Shopping upstream, loaded public/private/REST/raw-query matchers,
development host and Basic Auth, and no public Basic Auth.

The public post-checks are read-only HTTPS GETs plus offline Caddy validation.
Product detail is sampled only by first listing bounded `/shopping/products`
and then requesting a returned public product ID; a valid empty catalog is
accepted without a detail sample. Query-style REST aliases are each tested
with GET and must fail closed. The proof is named `direct_browser_woo_denied`,
and `PUBLIC_COMMERCE_WRITE_REQUEST=NOT_PERFORMED` because no write method is
sent. The offline marker is `REST_ROUTE_LIVE_PROOF_IMPLEMENTATION=READY`; the
live boolean is emitted only after activation. Storefront rendering uses the repository-owned
`.ai-shopping-storefront` marker. No Woo credentials or response bodies are
emitted.

The result separately records `COLIMA_REPAIR_ATTEMPTED`,
`WORDPRESS_START_ATTEMPTED`, and `CADDY_RELOAD_ATTEMPTED`. A failed or
ambiguous operation consumes the one-shot authority and is never retried or
automatically rolled back.
