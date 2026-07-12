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
