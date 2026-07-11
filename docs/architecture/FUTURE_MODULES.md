# Future Modules

Version: 1.0
Status: Planning Reference

## Purpose

Reserve logical ownership for future capabilities without adding them to Core.

This document is not an implementation commitment or release schedule.

## Infrastructure Modules

### Ubuntu Datacenter Control

Potential responsibilities:

- Connectivity checks
- Wake-on-LAN
- SSH execution
- Approved script execution
- Service status
- Safe shutdown
- Audit logging

### Docker Control

Potential responsibilities:

- Compose project inventory
- Service status
- Controlled start and stop
- Health reporting
- Update preview

### Backup Orchestration

Potential responsibilities:

- Backup policy
- Backup scheduling
- Verification
- Retention reporting
- Restore rehearsal

## AI Integrations

### Model Router

Potential responsibilities:

- Provider selection
- Fallback
- Cost policy
- Privacy policy
- Local-versus-cloud routing

### MCP Integration

Potential responsibilities:

- MCP server registration
- Capability discovery
- Permission policy
- Audit logging

### Voice and Vision

Potential responsibilities:

- Speech input and output
- Image understanding
- Camera or media ingestion

These capabilities must remain optional integrations.

## Automation Modules

### WordPress

Potential responsibilities:

- Draft creation
- Content publishing
- Media upload
- Approval workflow

### Shopping Automation

Potential responsibilities:

- Product collection
- Description generation
- Price and inventory workflows
- Human approval gates

### SEO

Potential responsibilities:

- Metadata generation
- Keyword workflow
- Content review
- Publishing reports

## Personal AI Modules

Personal AI remains separated from business and datacenter automation.

Potential modules:

- Calendar
- Email
- Finance
- Family
- Health

Each requires a separate privacy and permission review.

## Platform Growth Rules

A future module must:

1. Have a clear owner and boundary.
2. Avoid expanding Core business responsibilities.
3. Define public interfaces.
4. Include tests.
5. Include configuration documentation.
6. Include operational documentation.
7. Include security and rollback considerations.
8. Be portable between supported runtime environments where applicable.
