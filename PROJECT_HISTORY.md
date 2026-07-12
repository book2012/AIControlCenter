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

<!-- SHOPPING_M4_START -->

## Shopping Platform M4 History

AI Shopping Platform was introduced as a service layer on top of the completed AI Home Datacenter Platform.

During M4:

- WordPress and WooCommerce were deployed in the Ubuntu virtual validation environment.
- AIControlCenter remained the sole business-logic and orchestration layer.
- WooCommerce was connected through a read-only Adapter.
- External HTTP development access was established through ipTIME DDNS and port forwarding.
- Public TLS using the ipTIME hostname was rejected by the parent-domain CAA policy.
- Production HTTPS was deferred until a user-owned domain is available.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## Shopping Platform M5 History

M5 introduced the first external AI Shopping Storefront.

The Storefront was implemented as a modular WordPress Presentation Plugin.

WordPress displays Featured Products, categories, search results, price filters, stock filters, pagination, and product images.

AIControlCenter continues to own product selection, search validation, Commerce Adapter access, and future recommendation logic.

The implementation was validated through the external ipTIME DDNS development address while Production HTTPS remains deferred to a user-owned domain.
<!-- SHOPPING_M5_END -->
