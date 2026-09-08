# SHOP-SERVICE-START-01G1D recovery boundary

Mutation: `SHOP-SERVICE-START-01G1D:WORDPRESS_RUNTIME_GENERATION_RECOVERY`.

This implementation does not authorize execution. No live issuance or mutation was
performed during implementation. A future explicit human authorization requires a
clean reviewed repository and fresh matching non-secret observations, both before
and after the exact interactive acknowledgement. The issuer is
`ops.macos.shopping.issue_wordpress_recovery_authorization`; the fixed operator is
`ops.macos.shopping.wordpress_recovery_operator`. Both reject CLI arguments.

The distinct 01g1d SQLite file and application identity cannot consume 01G1C records.
A recovery store admits only one record, including after expiry or consumption.
Drift denies consumption. Durable claim and committed read-back precede the sole
WordPress-only Compose attempt. Failed or uncertain execution can never become
ACCEPTED through polling; there is no mutation retry or rollback.

The failed-created WordPress declaration retains the historical sites-enabled
mount in its precondition. The desired postcondition uses sites-available and
leaves the enabled symlink image-owned. The historical 01G1C artifact digest and
authority implementation remain unchanged; its UNCERTAIN result is not upgraded.

Read-only post-validation compares two snapshots separated by one second and
requires a new healthy running generation, the pinned image, exact four mounts,
loopback binding and networks. Database identity, start, restart count and all
bound metadata, both volume identities, repository identity and trusted source
metadata must remain unchanged. Created containers may have unattached network
IDs or no active port assignment; their exact observed values are still bound,
and post-validation requires actual network IDs and loopback port assignment.

WordPress entrypoint and healthcheck startup effects may write to the existing
WordPress volume. Backup/restore and content preservation are not proven.
Production, Ubuntu and business mutation authority remain false. There is no
capability/verifier activation, authenticated read, Caddy change, loaded Apache/PHP
claim or component inventory closure.
