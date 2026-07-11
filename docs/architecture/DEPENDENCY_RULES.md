# Dependency Rules

Version: 1.0
Status: Active

## Allowed Dependency Direction

Preferred direction:

Transport
then Application modules
then Domain interfaces
then Infrastructure and integration adapters

Shared platform services may be used through stable interfaces.

## Core Rule

Core must not import feature modules.

Allowed direction:

- Module depends on a Core interface

Not allowed:

- Core depends on Storage
- Core depends on Homepage
- Core depends on provider implementations

## API Rule

API routes may:

- Validate requests
- Resolve dependencies
- Call application services
- Serialize responses

API routes must not:

- Execute shell commands directly
- Open feature databases directly
- Implement migration rules
- Contain retry or rollback business logic

## Command Router Rule

Command routers dispatch commands.

They must not become a second application service layer containing duplicated
business logic.

## Module Rule

Modules must not access another module's private storage directly.

Cross-module operations require:

- Public service contract
- Protocol or interface
- Application event
- Explicit orchestration service

## Integration Rule

External SDKs and HTTP clients remain inside integration adapters.

Feature modules depend on provider interfaces, not concrete SDK clients.

## Infrastructure Rule

Operating-system and remote-host behavior must be isolated.

Examples:

- SSH commands
- subprocess execution
- systemd
- launchd
- Wake-on-LAN
- Filesystem mount inspection

Business modules must not scatter operating-system calls throughout the code.

## Database Rule

Each persistent feature must clearly define:

- Database owner
- Schema owner
- Transaction boundary
- Migration owner
- Backup policy
- Rollback policy

Production and test database paths must never be implicitly shared.

## Configuration Rule

Configuration priority:

1. Defaults
2. Environment profile
3. Environment variables
4. Explicit runtime arguments

Modules consume typed settings or configuration contracts.

They should not read unrelated environment variables throughout business code.

## Test Rule

Unit tests must avoid:

- Production storage paths
- Real destructive shell commands
- Live provider credentials
- Uncontrolled network calls

Integration tests must use isolated environments.

## Portability Rule

Linux-specific and macOS-specific behavior must use adapters.

Application-level features must be deployable to:

- Ubuntu Test Server Environment
- Mac mini Production Control Server

## Circular Dependency Rule

Circular imports are prohibited.

A detected circular dependency is an architecture defect and must be resolved
through interface extraction, eventing, or orchestration.
