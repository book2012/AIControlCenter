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
