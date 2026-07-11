# AIControlCenter Architecture Constitution

Version: 1.0
Status: Active

## Purpose

This document defines the architectural principles of AIControlCenter.

AIControlCenter is the control-plane application of AI Home Datacenter.

The application is currently developed and tested in an Ubuntu virtual
environment. Its final production runtime is the Mac mini M4.

The Ubuntu server continues to run native datacenter services such as storage,
backup, Immich, Nextcloud, and Plex.

## Environment Model

### Ubuntu Datacenter Server

Native responsibilities:

- Storage
- Backup
- Immich
- Nextcloud
- Plex
- Private cloud
- Media services

### Ubuntu Test Server Environment

Temporary responsibilities:

- AIControlCenter development
- Automated testing
- Integration testing
- Migration preview
- Pilot migration
- macOS deployment preparation

### Mac mini Production Control Server

Final responsibilities:

- AIControlCenter production runtime
- AI orchestration
- Automation
- Scheduling
- Monitoring
- Provider integrations
- Ubuntu Datacenter control

## Constitutional Principles

### 1. Core Is Stable

Core contains only platform-level responsibilities.

Business features do not belong in Core.

### 2. New Features Become Modules

Storage, homepage, knowledge, memory, planning, and future capabilities are
implemented as modules.

### 3. External Systems Are Integrations

OpenAI, Claude, Google, Telegram, GitHub, Notion, and other external systems
are isolated behind integration adapters.

### 4. Infrastructure Is Isolated

SSH, remote execution, backup, power management, Wake-on-LAN, Docker control,
and operating-system functions belong to infrastructure boundaries.

### 5. Core Does Not Import Feature Modules

Modules may depend on stable Core interfaces.

Core must not depend on feature modules.

### 6. No Circular Dependencies

Circular imports and circular service dependencies are prohibited.

### 7. Every Module Owns Its Domain

A module owns its configuration contract, application logic, tests, and
documentation.

It must not modify another module's private state directly.

### 8. Interfaces Before Implementations

Cross-module communication should use explicit interfaces, service contracts,
events, or application APIs.

### 9. Testability Is Mandatory

Every new feature requires appropriate unit tests and integration tests.

### 10. Maintainability Beats Convenience

Long-term stability, portability, documentation, and reproducibility take
priority over short-term implementation speed.

## Architecture Gate

Every proposed feature must answer:

1. Is this truly a Core responsibility?
2. Does it belong to an existing module?
3. Does it require a new module?
4. Is it an external integration?
5. Is it infrastructure-specific?
6. Can it be tested without production data?
7. Does it work in Ubuntu Test and Mac production environments?
8. Does it require a documented migration or rollback plan?

A feature that unnecessarily expands Core must be redesigned before
implementation.
