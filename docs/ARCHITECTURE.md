# Architecture

Mac mini M4

└── AIControlCenter
    ├── FastAPI
    ├── BrainAgent
    ├── ProviderManager
    ├── CommandRouter
    ├── Dashboard
    ├── Notification
    ├── Telegram
    └── Conversation Memory

Ubuntu Worker (Optional)

└── Docker
└── Storage
└── Backup
└── Immich
└── Nextcloud
└── Plex

<!-- AI_SHOPPING_PLATFORM_START -->
## AI Shopping Platform Service Layer

Architecture flow:

WordPress
to WooCommerce
to REST API
to AIControlCenter Shopping Domain
to AI Agent, Scheduler, n8n and Notifications

Responsibilities:

- WordPress owns presentation and CMS
- WooCommerce owns commerce data
- AIControlCenter owns business logic
- AI Agent owns content generation tasks
- n8n executes automation workflows

The current development runtime is virtual.

The final production runtime is Mac mini M4.

Ubuntu must not contain Shopping business logic, AI logic or
application state.

Detailed documentation:

docs/shopping/ARCHITECTURE.md
<!-- AI_SHOPPING_PLATFORM_END -->

<!-- SHOPPING_M4_START -->

## AI Shopping Platform Service Layer

WordPress
    CMS

WooCommerce
    Commerce Engine

AIControlCenter
    Business Logic
    REST API
    Adapter Factory
    AI Services
    Workflow and Approval

Ubuntu
    Temporary virtual deployment validation

Mac mini M4
    Final Control Plane and Production Runtime

Ubuntu does not own Shopping business logic or AI application state.
The final Shopping service runs under AIControlCenter on Mac mini M4.
<!-- SHOPPING_M4_END -->
