# Project History

AIControlCenter became the Brain.

Ubuntu became an optional Worker.

Implemented

- BrainAgent
- Provider Manager
- Telegram
- Dashboard
- Conversation Memory
- SQLite
- Command Router

## Sprint 21-22

Scheduler Foundation completed.

Memory Manager completed.

AIControlCenter now has:

- Heartbeat
- Scheduled Job Registry
- Background Scheduler
- Conversation Memory
- Working Memory
- Long-term Memory
- Memory API

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Service Layer

AI Shopping Platform development started after the infrastructure
platform reached production-ready status.

Shopping is implemented as a service layer inside AIControlCenter.

The architectural ownership is:

- WordPress provides the shopping homepage and CMS
- WooCommerce provides the commerce engine
- AIControlCenter owns Shopping business logic and AI workflow
- AI Agent generates content and performs approved updates
- n8n executes external automation
- Mac mini M4 is the final production Control Plane
- Ubuntu remains an infrastructure worker

Development currently runs in a virtual environment.

The same source code will later be deployed to Mac mini M4 using
production-specific configuration.
<!-- AI_SHOPPING_PLATFORM_END -->
