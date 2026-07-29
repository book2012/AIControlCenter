# DPL-04B Mac-Only Sandbox Adapter

`MacSandboxAdapter` implements the DPL-04A `NonProductionExecutorPort`. It
materializes audit-ready canonical JSON only inside an explicitly injected
sandbox root. No default live root is composed; a missing or unsafe root is
denied.

The adapter accepts only development, test and staging requests owned by
`mac-control-plane`. Each request is revalidated against its injected DPL-03C
authorization and DPL-04A capability, including authorization, package, plan,
target, operation, actor and environment bindings. Production authorization is
always false.

Supported operations are `VERIFY_SANDBOX_TARGET`, `PREPARE_SANDBOX` and
`COLLECT_EXECUTION_EVIDENCE`. Preparation and collection use a fixed
request-derived directory below the injected root, canonical JSON, same-root
atomic replacement and SHA-256 read-back verification. Repeating identical
content is idempotent; conflicting immutable content is denied.

Absolute paths, parent traversal, symlink roots or components, repository
roots, protected system roots, secret-bearing fields and executable payload
fields are rejected. The adapter never deletes, creates executable files,
invokes a shell or subprocess, accesses a network, changes environment
variables, calls a service manager, or touches Ubuntu.

An allowed result means only that sandbox artifacts were materialized. It does
not mean infrastructure or services were deployed. Repository, production,
Ubuntu, network and runtime-command counters remain zero. Evidence is returned
to the caller only; durable audit and nonce persistence are outside DPL-04B.
Production activation remains unauthorized, M2 remains incomplete, and
DPL-04C is the next separately gated step.
