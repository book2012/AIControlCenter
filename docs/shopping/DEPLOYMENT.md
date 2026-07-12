# Shopping Platform Deployment

## Current Environment

Virtual development environment

## Production Target

Mac mini M4

## Deployment Principle

Development and production use the same application source code.

Environment differences are managed through configuration.

## Shopping Environment Variables

SHOPPING_ENABLED

SHOPPING_ENVIRONMENT

SHOPPING_RUNTIME

SHOPPING_DEPLOYMENT_TARGET

SHOPPING_WRITE_MODE

SHOPPING_APPROVAL_REQUIRED

SHOPPING_AUTOMATION_ENABLED

SHOPPING_AI_ENABLED

## Safe Development Defaults

SHOPPING_ENABLED=true

SHOPPING_ENVIRONMENT=development

SHOPPING_RUNTIME=virtual

SHOPPING_DEPLOYMENT_TARGET=mac-mini-m4

SHOPPING_WRITE_MODE=read_only

SHOPPING_APPROVAL_REQUIRED=true

SHOPPING_AUTOMATION_ENABLED=false

SHOPPING_AI_ENABLED=false

## Future Mac mini Validation

- ARM64 compatibility
- AIControlCenter startup
- Shopping health
- Shopping readiness
- Service restart
- Mac reboot recovery
- Secrets validation
- Backup validation
- Rollback validation

<!-- SHOPPING_M4_START -->

## M4 Deployment

### Docker Runtime

- WordPress host port: 8088
- MariaDB host port: not exposed
- Persistent database volume: ai-shopping-database
- Persistent WordPress volume: ai-shopping-wordpress
- Caddy is deferred until a user-owned domain is available

### External Development Access

WAN TCP 58088
to Ubuntu 192.168.1.7 TCP 8088
to shopping-wordpress TCP 80

### systemd Runtime

Environment file:

/etc/aicontrolcenter/shopping.env

Required permissions:

600 root:root
<!-- SHOPPING_M4_END -->
