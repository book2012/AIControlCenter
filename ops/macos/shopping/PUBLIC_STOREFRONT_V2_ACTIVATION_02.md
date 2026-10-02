# Public Storefront V2 Activation-02

Activation-02 is the successor edge-cutover lane for the already-running
`aicontrolcenter-commerce` generation. It is a new authority and does not read,
reuse, or mutate Activation-01 durable records.

Authority identity:

- `PUBLIC-STOREFRONT-V2-ACTIVATION-02`
- `PUBLIC-STOREFRONT-V2-ACTIVATION-02:ONE_SHOT_CADDY_V2_CUTOVER`
- one use, ten-minute lifetime
- human acknowledgement: `AUTHORIZE PUBLIC-STOREFRONT-V2-ACTIVATION-02`

The issuer is TTY-only and binds a clean candidate HEAD, reviewed activation
bundle digest, reviewed Caddy artifacts, a Running/PASS Colima profile, and the
exact observed WordPress and database generations. The generation binding
contains container ID, creation time, image reference and ID, Compose
project/service, running/healthy state, restart policy, ports, required mounts,
and network membership. Named volumes and network IDs are rebound as continuity
evidence. This is metadata continuity only; it makes no claim about content or
backup integrity.

The operator performs read-only observation before consumption and freshly
re-observes the complete binding after durable consumption. Any drift burns the
authority and stops. The only permitted mutation is one `caddy reload`; there
is no Colima lifecycle command, WordPress start/restart/stop, Compose command,
database or volume mutation, WooCommerce write, DNS action, Ubuntu access, or
automatic retry. Caddy must already be PRE_V2 and its trusted executable,
listeners, and normal `lsof -d txt -Fn` executable mappings must be proven.

After reload, the observer must prove exact equality with the reviewed V2
adaptation and the closed storefront boundary: public WordPress root on
`127.0.0.1:58082`, Shopping GET allowlist on `127.0.0.1:58081`, no public Basic
Auth, preserved dev Basic Auth, denied management and WordPress private
namespaces, the raw `rest_route` ambiguity guard, no shopping writes, and
unchanged WordPress/database generations. Outputs are fixed flags only and are
secret-blind and value-bounded.
