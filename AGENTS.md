# Repository Agent Instructions

## Architecture Invariants

- Mac mini M4 is the always-on Brain and single Control Plane.
- AIControlCenter owns governance, policy, orchestration, approval,
  authorization, audit, deployment control and business logic.
- Ubuntu is an optional stateless infrastructure worker and must not own AI
  workloads, business logic, application state or Control Plane authority.
- Host Caddy is the only public edge.
- WordPress is the CMS Engine and WooCommerce is the Commerce Engine.
- JSON-first, read-only-first and Git-first are mandatory.
- Production writes require explicit authorization; they are currently
  prohibited.

## DPL Safety

- Keep read, plan and apply boundaries strict.
- Do not route DPL through `UbuntuWorkerClient.execute` or generic remote
  commands.
- Treat Linux systemd Control Plane artifacts as `LEGACY_UNSUPPORTED`.
- Do not interpret a desired-state package as activation authorization.

## Change Discipline

- Preserve stronger task-specific restrictions.
- Never display or commit secrets.
- Do not access production or Ubuntu unless a task explicitly authorizes it.
- Verify the Git baseline and working-tree scope before and after changes.

## AUTONOMOUS CODEX GIT WORKFLOW

- Codex performs architecture, implementation, tests, documentation, staging,
  commit, push and final Git verification.
- Automatic Git operations are allowed only on approved feature branches.
  Direct pushes to `main`, `master` and production branches are prohibited.
- Force push, `reset --hard`, `clean`, `stash`, `rebase` and `merge` are
  prohibited unless separately authorized.
- Unexpected dirty files are a blocker, and failed tests are a commit blocker.
- README, CHANGELOG, MASTER, ROADMAP and applicable architecture documentation
  must be updated before sprint closure.
- A Git commit must contain only current-task files.
- Every push must be followed by repository-clean and upstream-sync
  validation.
- Credentials and secrets must never be printed.
- Production activation requires a separate authorization gate.
