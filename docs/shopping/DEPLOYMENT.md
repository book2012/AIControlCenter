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

<!-- SHOPPING_M5_START -->

## M5 Storefront Deployment

### Plugin Bind Mount

Host:

deploy/shopping/wordpress/plugins/ai-shopping-storefront

Container:

/var/www/html/wp-content/plugins/ai-shopping-storefront

The mount is read-only.

### Host API Access

WordPress uses:

host.docker.internal

Docker Compose must define:

host.docker.internal:host-gateway

### Deployment Target

Current:

Ubuntu virtual deployment validation environment

Final:

Mac mini M4 AIControlCenter Production Runtime

### HTTPS

Current ipTIME DDNS is development-only HTTP.

A user-owned domain is required before public Production deployment.
<!-- SHOPPING_M5_END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->
