# SHOP-SERVICE-START-01G1G

Implementation baseline: `48bddf729f362e25f96eb110c53abff6bc4f46ae` (clean).
Implementation only; no live observation, authorization issuance or operator execution.

Separate zero-argument entry points are
`ops.macos.shopping.issue_wordpress_existing_generation_start_authorization` and
`ops.macos.shopping.wordpress_existing_generation_start_operator`.
The sole mutation is:

```
docker --context colima-aicontrolcenter-commerce start 0636d4cad86d31f0119ccadb1c83ef59ea4b2192bdd74b3f459c2947d24f2a0e
```

The issuer requires a trusted macOS account, expected clean current Git HEAD,
independently reviewed artifact SHA-256, two stable observations and exact ACK:
`AUTHORIZE SHOP-SERVICE-START-01G1G:WORDPRESS_EXISTING_GENERATION_START`.
Review identity uses the F0 inventory and byte/mode hashing pattern with isolated
schema `SHOP-SERVICE-START-01G1G:reviewed-artifact:v1`. A computed digest does not
prove review. Authority roots include core, ops, integrations, config, configs,
requirements.txt and deploy/shopping/compose.yaml. No review is claimed here.

The dedicated `wordpress-existing-generation-start-01g1g-authorization.sqlite3`
store in the trusted account's Library/Application Support/AIControlCenter/authorization
uses the F0 ownership, schema, durable claim/commit and receipt checks. Any existing
row prevents reissuance, including expired or consumed rows. Retain the store;
deleting it to obtain another attempt is outside this contract. Authority expires
within ten minutes and permits one use, durably consumed before mutation.

Preconditions bind exact context endpoint and socket metadata, clean HEAD, artifact,
compose digest, exact created/non-running WordPress ID with restart policy no and
restart count zero. The database must be exact ID
`434c15132d947937481b635cf7caabf76c640e8875186eb656b5332a7563d323`,
running, healthy and restart count zero. Its start timestamp, ai-shopping-database
volume identity and attachment remain bound throughout. A created WordPress container
may have no Health state yet. No environment or healthcheck logs are read.

After durable consumption the operator rechecks bindings and expiry, then invokes
start once with a 30-second timeout and discarded standard streams. It validates
running WordPress with the same ID, restart policy no and restart count zero, plus
unchanged database, storage, repository and socket observations. Read-only polling
allows 460 seconds for WordPress health convergence (60-second start period plus
20 times the 15-second interval and 5-second timeout), checking continuity each time.
Only successful start and healthy validated postconditions yield ACCEPTED.
Timeout, nonzero, ambiguous consumption or failed postconditions yield UNCERTAIN.
Precondition or authorization failure before an attempt yields BLOCKED; a consumed
row remains burned even when the final precondition check blocks execution.

No automatic retry or rollback, recreation, database/volume/network mutation,
Ubuntu or business authority is provided. General lifecycle authority remains false;
the exact mutation binding grants only this single start. Existing 01G1C, 01G1D,
01G1F and 01G1F0 contracts remain unchanged. External administrators must avoid
concurrent changes: Docker does not offer an atomic conditional start. Metadata
continuity does not prove backup or database content preservation.
