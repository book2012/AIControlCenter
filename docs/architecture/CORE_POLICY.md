# Core Policy

Version: 1.0
Status: Active

## Objective

Keep AIControlCenter Core small, stable, reusable, and independent of business
features.

## Allowed Core Responsibilities

Core may contain:

- Application lifecycle
- Central configuration interfaces
- Shared exception types
- Stable protocols and interfaces
- Dependency registration primitives
- Common result and status models
- Cross-cutting runtime contracts
- Minimal utilities used across multiple modules

## Prohibited Core Responsibilities

Core must not contain:

- Storage migration business rules
- Homepage or WordPress business logic
- Provider-specific API implementations
- Telegram bot behavior
- Backup plans tied to a specific server
- Ubuntu-specific shell commands
- macOS-specific launchd behavior
- Feature-specific database schemas
- Feature-specific API routes
- User-facing workflow logic

## Core Change Policy

A Core change is allowed only when at least one condition is true:

1. It fixes a Core defect.
2. It introduces a reusable interface required by multiple modules.
3. It improves platform lifecycle, configuration, or runtime safety.
4. It removes duplicated cross-cutting behavior.
5. It is accompanied by tests and an architecture review.

## Core Change Review Questions

Before changing Core:

- Can this be implemented inside a module?
- Can an adapter solve the problem?
- Is the abstraction already required by at least two modules?
- Will the change create a reverse dependency?
- Is the interface stable enough for long-term use?
- Does it preserve Ubuntu Test and macOS production portability?

## Core Freeze Policy

During Storage Agent migration and production-readiness work:

- No new business capability is added to Core.
- Core refactoring must not alter production behavior.
- Directory-wide restructuring is deferred to a dedicated architecture sprint.
- Bug fixes and safety improvements remain allowed.
