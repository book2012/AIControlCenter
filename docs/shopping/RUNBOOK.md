# Shopping Platform Runbook

## Health Check

curl -fsS http://127.0.0.1:8000/shopping/health

## Readiness Check

curl -fsS http://127.0.0.1:8000/shopping/readiness

## Capabilities Check

curl -fsS http://127.0.0.1:8000/shopping/capabilities

## Expected Safe State

- Status ONLINE
- Readiness READY
- Write mode read_only
- Catalog write false
- AI execution false
- Automation execution false
- Approval required true

## Invalid Configuration Response

When Shopping configuration is unsafe or unsupported, readiness must
return NOT_READY.

## Recovery Procedure

1. Disable Shopping write operations.
2. Restore read_only mode.
3. Disable AI execution.
4. Disable automation execution.
5. Restart AIControlCenter.
6. Check health.
7. Check readiness.
8. Run targeted tests.
9. Run full regression tests.
10. Review logs before enabling additional capabilities.

<!-- SHOPPING_M4_START -->

## M4 Runbook

### Runtime Status

systemctl is-active aicontrolcenter-api.service

docker inspect   --format '{{.Name}} | {{.State.Status}} | {{if .State.Health}}{{.State.Health.Status}}{{end}}'   shopping-db   shopping-wordpress

### API Validation

curl http://127.0.0.1:8000/shopping/health
curl http://127.0.0.1:8000/shopping/readiness
curl http://127.0.0.1:8000/shopping/integrations
curl 'http://127.0.0.1:8000/shopping/products?page=1&page_size=20'
curl http://127.0.0.1:8000/shopping/categories

### External UI

http://bokstory.iptime.org:58088

Chrome may force a cached HTTPS policy.
Use the explicit http:// URL or clear the browser HSTS policy.

### Forbidden Recovery Commands

Do not run:

docker compose down -v
docker volume rm ai-shopping-database
docker volume rm ai-shopping-wordpress
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Storefront Runbook

### Check Plugin

docker exec shopping-wordpress   test -f   /var/www/html/wp-content/plugins/ai-shopping-storefront/ai-shopping-storefront.php

### Check External Page

curl -I   http://bokstory.iptime.org:58088/ai-shopping/

### Clear Storefront Cache

wp transient delete --all

Use the existing WordPress CLI container command and database environment.

### Check WordPress Errors

docker logs --since 5m shopping-wordpress

Look for:

- PHP Fatal
- PHP Parse
- Uncaught Exception
- TypeError
- ArgumentCountError

### Safe Recovery

Recreate only the WordPress service.

Never remove the WordPress or MariaDB persistent volumes during routine recovery.
<!-- SHOPPING_M5_END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## SHOP-01 Product Management Read Model and Dashboard

SHOP-01 is closed.

Completed capabilities:

- deterministic Shopping management read model
- product and inventory summary
- normalized operator-facing product list
- health, readiness, capability and integration projection
- optional `shopping_management` Dashboard dependency
- `GET /dashboard.shopping_management` JSON projection
- deterministic `UNAVAILABLE` failure envelope
- internal error-detail suppression
- source and result mutation isolation
- existing Dashboard compatibility
- default-configuration read-only operational observation

Architecture boundaries remain unchanged:

- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns management projections and workflow logic.
- The Dashboard does not import WooCommerce adapters.
- No local product truth was created.
- No Shopping mutation route was added.
- Production writes remain `NOT_AUTHORIZED`.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01D-CLOSEOUT:END -->
