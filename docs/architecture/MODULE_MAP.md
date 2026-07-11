# Module Map

Version: 1.0
Status: Initial Baseline

## Current Logical Architecture

The current repository stores many components below core.

This document defines logical ownership without requiring an immediate
directory migration.

## Platform Core

Current candidates:

- core/config
- core/runtime
- Shared interfaces and exceptions identified during dependency audit

Responsibilities:

- Configuration contracts
- Environment validation
- Lifecycle
- Runtime health
- Shared interfaces

## Product Modules

### Agent and Planning

Current paths:

- core/agent
- core/task
- core/session

Responsibilities:

- Agent behavior
- Planning
- Task registration and execution
- Session context

### Automation

Current path:

- core/automation

Responsibilities:

- Automation planning
- Queueing
- Execution policy
- Controlled execution

### Backup

Current path:

- core/backup

Responsibilities:

- Backup planning
- Confirmation
- Execution
- Verification

### Datacenter and Storage

Current paths:

- core/datacenter
- Storage-related API routes
- Storage Agent components identified during final review

Responsibilities:

- Storage registry
- Backup registry
- Storage inventory
- Data migration
- Datacenter resource models

### Knowledge

Current path:

- core/knowledge

Responsibilities:

- Knowledge loading
- Registry
- Indexing
- Search

### Memory

Current path:

- core/memory

Responsibilities:

- Working memory
- Conversation memory
- Long-term memory
- Memory persistence

### Homepage

Current path:

- core/homepage

Responsibilities:

- Homepage status
- Future WordPress and homepage automation

### Monitoring and Doctor

Current paths:

- core/monitoring
- core/doctor
- core/worker_status

Responsibilities:

- Health snapshots
- Diagnostic checks
- Managed target status

### Dashboard

Current path:

- core/dashboard

Responsibilities:

- Aggregated control-center presentation models
- Dashboard API services

### Notification

Current path:

- core/notification

Responsibilities:

- Internal notification contracts
- Notification dispatch orchestration

## Integrations

### AI Providers

Current path:

- core/providers

Implementations:

- OpenAI
- Claude
- Google
- Ollama

Long-term logical location:

- integrations/ai/providers

### Telegram

Current path:

- core/adapters/telegram

Long-term logical location:

- integrations/telegram

## Infrastructure

### Execution and Managed Targets

Current path:

- core/worker

Responsibilities:

- Local runner
- SSH runner
- Remote runner
- Worker client
- Ubuntu managed-target adapter

The word worker describes an execution-target abstraction.

It does not mean that Ubuntu is the permanent AIControlCenter production host.

### Power

Current path:

- core/power

Responsibilities:

- Managed-target power policy
- Wake and shutdown orchestration

### Scheduler

Current path:

- core/scheduler

Classification:

- Shared platform service

The scheduler executes registered jobs without owning feature business logic.

## Interfaces

### API

Current path:

- core/api

Responsibilities:

- HTTP transport
- Input validation
- Response serialization
- Delegation to application services

API routes must not own business logic.

### Commands

Current path:

- core/commands

Responsibilities:

- Command transport and routing
- Delegation to modules

Command routers must not directly implement domain behavior.

## Deferred Physical Refactoring

No directory move is approved by this document.

Physical restructuring requires:

- Dependency graph
- Import migration plan
- Compatibility shims where required
- Full test execution
- Rollback procedure
