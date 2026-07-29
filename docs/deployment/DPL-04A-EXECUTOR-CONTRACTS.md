# DPL-04A Non-Production Executor Contracts and Ports

AIControlCenter on the Mac mini M4 owns these contracts, policy validation,
authorization binding and future orchestration. Ubuntu remains an optional
stateless infrastructure worker and cannot own executor policy.

`core.deployment.executor_contracts` defines schema-validated capability,
request, result and validation-report contracts. Only development, test and
staging are accepted, and `mac-control-plane` is the sole target owner. The
typed operation allowlist contains sandbox verification, package/plan/
authorization validation, sandbox preparation, simulation and evidence
collection. It contains no command or real mutation operation.

`core.deployment.executor_ports` defines the non-production executor,
capability-provider and policy-validator ports. Ports express dependency
boundaries; they are not adapters. DPL-04A supplies no real executor or adapter.
Its dependency-injected default composition is deny-only and returns a result
with zero production writes, Ubuntu changes, network accesses, runtime commands
and real executor invocations. It performs no persistent write and never falls
back to execution.

Production authorization remains false. DPL-04A does not complete DPL-04 or M2.
DPL-04B is the next separately reviewed step and must preserve explicit
authorization, non-production-only scope, typed operations and default denial.

Closure documentation is recorded in README, CHANGELOG, MASTER and ROADMAP.
Repository automation follows the feature-branch-only autonomous Git workflow
defined in `AGENTS.md`.
