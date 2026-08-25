# Macro-WU09 MariaDB Loopback Port Deployment Freeze

## Scope and current decision

This document freezes the implementation-scope architecture for
`MARIADB_LOOPBACK_PORT_DEPLOYMENT`. It grants no authorization, capability, or
Production authority and records no live runtime observation.

Repository truth identifies the existing Compose project `ai-shopping`,
database service `database`, container `shopping-db`, container port `3306`,
and Docker network `ai-shopping-internal`. The database currently publishes no
host port. No repository-owned numeric MariaDB host port exists.

The future external binding contract is:

`127.0.0.1:<assigned-numeric-host-port> -> database:3306`

The numeric host port must be reviewed and assigned in a later implementation
work unit. It is not selected or guessed here. Therefore
`LOOPBACK_BINDING_GATE=BLOCKED_NUMERIC_HOST_PORT_UNASSIGNED` and
`NUMERIC_HOST_PORT_GATE=BLOCKED_NUMERIC_HOST_PORT_UNASSIGNED`.

## Reconciled architecture

Directly publishing the database service remains rejected. Recreating that
service is coupled to unresolved `SHOPPING_DB_NAME`, `SHOPPING_DB_USER`,
`SHOPPING_DB_PASSWORD`, and `SHOPPING_DB_ROOT_PASSWORD` runtime material and
cannot be proven credential-blind. Therefore:

- `DIRECT_DATABASE_RECREATE_GATE=BLOCKED_SECRET_RUNTIME_COUPLING`
- `SECRET_RUNTIME_COUPLING_GATE=BLOCKED`
- `DATABASE_CONTAINER_MUTATION_REQUIRED=false`

The preferred architecture is a completely separate, credential-blind,
stateless infrastructure module containing only service
`mariadb-loopback-adapter`. Its dedicated Compose project identity is
`ai-shopping-mariadb-loopback`. It connects to the already-existing Docker
network `ai-shopping-internal` by declaring that network external. It must
never create, delete, recreate, or mutate the network.

The dedicated Compose file must not include `database`, `wordpress`, or
`wordpress-cli`; must not reference `SHOPPING_DB_NAME`, `SHOPPING_DB_USER`,
`SHOPPING_DB_PASSWORD`, or `SHOPPING_DB_ROOT_PASSWORD`; and must not load the
main Shopping Compose package as a base, include, or merged configuration.
This isolation prevents unresolved database and WordPress runtime material in
`deploy/shopping/compose.yaml` from participating in WU09 configuration
resolution.

The adapter contains no credentials, business logic, MariaDB authentication
logic, SQL, Governance authority, or Production authorization authority. It
mounts no database or WordPress volume. Its reviewed image and fixed argv must
implement byte-transparent TCP forwarding without a management listener or
broader exposure.

Accordingly:

- `DEDICATED_LOOPBACK_ADAPTER_GATE=PREFERRED`
- `PREFERRED_ARCHITECTURE=DEDICATED_CREDENTIAL_BLIND_STATELESS_LOOPBACK_ADAPTER`
- `MAIN_COMPOSE_ISOLATION_GATE=PASS`
- `DEDICATED_COMPOSE_PACKAGE_GATE=PASS`
- `DEDICATED_PROJECT_IDENTITY_GATE=PASS`
- `EXTERNAL_INTERNAL_NETWORK_REUSE_GATE=PASS`
- `NETWORK_MUTATION_REQUIRED=false`

## Secret-management decoupling

`deploy/shopping/config/secret-contract.json` has the exact ordered action set
`runtime_cutover`, `bootstrap`. `ops/macos/shopping/secret_preflight.py`
explicitly validates that exact ordered set. Adding a WU09 action would require
secret-preflight code and test changes and would incorrectly couple a
credential-blind transport deployment to SM-01 secret management.

WU09 must not invoke Shopping Secret Preflight and must not add an action or
key to the Shopping Secret Contract. `SHOPPING_MARIADB_PORT`, if used as a
derived process-local Compose input, is non-secret runtime configuration and
is not a Shopping secret-management item. Therefore:

- `SECRET_CONTRACT_DECOUPLING_GATE=PASS`
- `SECRET_PREFLIGHT_DECOUPLING_GATE=PASS`
- `SECRET_CONTRACT_CHANGE_REQUIRED=false`
- `SECRET_PREFLIGHT_CHANGE_REQUIRED=false`
- `CREDENTIAL_ACCESS_REQUIRED=false`
- `CREDENTIAL_PROVISIONING_REQUIRED=false`
- `MARIADB_CONNECTION_REQUIRED=false`
- `SQL_REQUIRED=false`

## JSON-first runtime configuration

The sole durable authority for WU09 non-secret transport configuration must be
`config/shopping-mariadb-loopback.json`. The later implementation must define
and validate a value-free schema before accepting an assigned numeric host
port. Once reviewed and assigned, the same JSON document may contain only:

- schema version;
- service identity `mariadb-loopback-adapter`;
- bind host `127.0.0.1`;
- the assigned numeric host port;
- database target host `database`;
- target port `3306`; and
- external network identity `ai-shopping-internal`.

No credential name or value may appear. The deployment wrapper must validate
the reviewed JSON and derive the bounded Compose/environment input from it
without reading secret material. `deploy/shopping/.env.example` is excluded:
it would duplicate configuration authority and is not needed for this design.
Until the numeric value is assigned, the architecture remains value-free and
deployment remains blocked.

`JSON_FIRST_RUNTIME_CONFIG_GATE=PASS`

## Frozen future mutation target and production boundary

The exact future Production mutation target is the single dedicated stateless
Compose service `mariadb-loopback-adapter` in project
`ai-shopping-mariadb-loopback`, defined only by
`deploy/shopping/mariadb-loopback/compose.yaml`. The mutation is exactly one
bounded create-or-recreate invocation for that service. The already-existing
external network `ai-shopping-internal`, `database`, `wordpress`,
`wordpress-cli`, Caddy, Colima lifecycle, volumes, Ubuntu, and all other
services are excluded mutation targets.

Production execution requires one fresh human authorization for one exact
bounded mutation, fresh read-only precondition recollection, an SEC-02
authorization-consumption decision and durable consumption, fresh
preconditions again, `SEC-02 ALLOW_SINGLE_INVOCATION`, and exactly one bounded
adapter invocation. A failed, rejected, or uncertain invocation consumes the
authorization and ends the attempt. There is no retry, authorization reuse,
automatic rollback, compensation, or claim recovery. A desired-state package
never constitutes activation authorization.

Before later authorization, read-only checks must establish repository and
deployed revision identity, worktree cleanliness, the assigned non-reserved
numeric host port, listener availability, exact project/service/image/argv,
the loopback-only publisher, and external-network identity. They must fail
closed and must not inspect container environment values, use `docker exec`,
connect to MariaDB, authenticate, or execute SQL.

After the single mutation attempt, separate read-only reconciliation may
report adapter targeting, state, publisher, and network attachment. It must
not connect to the forwarded port. Postcondition failure grants no retry,
rollback, compensation, recovery, credential action, or follow-on
authorization.

## Exact proposed implementation scope

The later implementation work unit is limited to:

- `config/shopping-mariadb-loopback.json`: sole JSON-first authority for the
  reviewed non-secret transport facts;
- `deploy/shopping/mariadb-loopback/compose.yaml`: dedicated one-service
  Compose package, dedicated project identity, loopback-only publisher, and an
  external reference to `ai-shopping-internal`;
- `ops/macos/shopping/mariadb_loopback_port_deployment.py`: fail-closed Mac-only
  wrapper that validates JSON, derives transient Compose input without secret
  reads or Shopping Secret Preflight, fixes the project/file/service target,
  and permits one invocation with no retry; and
- `tests/test_macro_wu09_mariadb_loopback_port_deployment.py`: tests for schema
  validation, main-Compose and secret-management isolation, credential
  blindness, project/service/network boundaries, loopback-only binding,
  exact targeting, and fail-closed single-invocation behavior.

Any need to add another file or modify the main Shopping Compose file, its
`.env.example`, the Shopping Secret Contract, Shopping Secret Preflight,
database, WordPress, Governance core, SEC-02, or `ControlledExecutionPort`
requires a new architecture review.

## Separation and unchanged authority

WU09 provisions only the credential-blind transport adapter. WU10 remains
separately unauthorized and owns any future credential-slot provisioning
boundary. WU11 remains separately unauthorized and owns any future one-shot
read-only connection, authentication, or SQL validation boundary.

AIControlCenter on the Mac remains the sole Control Plane. Ubuntu remains a
stateless, zero-authority infrastructure worker and has no role in this command
path. Governance core and SEC-02 are unchanged. `ControlledExecutionPort`
remains uncoupled. No Production access or mutation occurred, and no
Production authorization was consumed by this architecture reconciliation.

## Reconciliation decision record

- `WU09_DISCOVERY_GATE=PASS`
- `WU09_ARCHITECTURE_RECONCILIATION_GATE=PASS`
- `WU09_IMPLEMENTATION_SCOPE_RECONCILIATION_GATE=PASS`
- `MAIN_COMPOSE_ISOLATION_GATE=PASS`
- `SECRET_CONTRACT_DECOUPLING_GATE=PASS`
- `SECRET_PREFLIGHT_DECOUPLING_GATE=PASS`
- `DEDICATED_COMPOSE_PACKAGE_GATE=PASS`
- `DEDICATED_PROJECT_IDENTITY_GATE=PASS`
- `EXTERNAL_INTERNAL_NETWORK_REUSE_GATE=PASS`
- `NETWORK_MUTATION_REQUIRED=false`
- `DATABASE_CONTAINER_MUTATION_REQUIRED=false`
- `SECRET_CONTRACT_CHANGE_REQUIRED=false`
- `SECRET_PREFLIGHT_CHANGE_REQUIRED=false`
- `CREDENTIAL_ACCESS_REQUIRED=false`
- `CREDENTIAL_PROVISIONING_REQUIRED=false`
- `MARIADB_CONNECTION_REQUIRED=false`
- `SQL_REQUIRED=false`
- `JSON_FIRST_RUNTIME_CONFIG_GATE=PASS`
- `NUMERIC_HOST_PORT_GATE=BLOCKED_NUMERIC_HOST_PORT_UNASSIGNED`
- `LOOPBACK_BINDING_GATE=BLOCKED_NUMERIC_HOST_PORT_UNASSIGNED`
- `EXACT_FUTURE_MUTATION_TARGET=ai-shopping-mariadb-loopback/mariadb-loopback-adapter`
- `PROPOSED_IMPLEMENTATION_SCOPE=config/shopping-mariadb-loopback.json,deploy/shopping/mariadb-loopback/compose.yaml,ops/macos/shopping/mariadb_loopback_port_deployment.py,tests/test_macro_wu09_mariadb_loopback_port_deployment.py`
- `WU10_SEPARATION_GATE=PASS`
- `WU11_SEPARATION_GATE=PASS`
- `GOVERNANCE_UNCHANGED_GATE=PASS`
- `SEC_02_UNCHANGED_GATE=PASS`
- `CONTROLLED_EXECUTION_PORT_UNCOUPLED_GATE=PASS`
- `MAC_CONTROL_PLANE_GATE=PASS`
- `UBUNTU_ZERO_AUTHORITY_GATE=PASS`
- `PRODUCTION_ACCESS_PERFORMED=false`
- `PRODUCTION_MUTATION_PERFORMED=false`
- `PRODUCTION_AUTHORIZATION_CONSUMED=false`
