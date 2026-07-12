from pathlib import Path


START = "<!-- SHOPPING_M4_START -->"
END = "<!-- SHOPPING_M4_END -->"


def update_section(path: Path, body: str) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else ""

    section = f"{START}\n{body.rstrip()}\n{END}"

    if START in content and END in content:
        before = content.split(START, 1)[0].rstrip()
        after = content.split(END, 1)[1].lstrip()

        content = "\n\n".join(
            part
            for part in (before, section, after)
            if part
        )
    else:
        content = content.rstrip()

        if content:
            content += "\n\n"

        content += section

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content.rstrip() + "\n",
        encoding="utf-8",
    )

    print(f"UPDATED: {path}")


updates = {
    Path("docs/shopping/README.md"): """
## M4 — Live WooCommerce Control Plane

Status: Implementation complete. Production Gate closeout in progress.

### Runtime

- Control Plane: AIControlCenter
- CMS: WordPress
- Commerce Engine: WooCommerce
- Development runtime: Ubuntu virtual validation environment
- Production target: Mac mini M4
- External development URL: http://bokstory.iptime.org:58088
- Commerce write mode: Read-only

### Implemented

- Shopping domain
- Product list API
- Product detail API
- Category API
- Integration status API
- Mock Commerce Adapter
- WooCommerce REST Adapter
- Adapter Factory
- Environment-driven Adapter selection
- HTTP OAuth 1.0a development authentication
- HTTPS Basic Authentication support
- systemd EnvironmentFile integration
- Docker Compose WordPress and MariaDB runtime

### Architecture Rule

WordPress and WooCommerce do not own AI or business logic.
AIControlCenter remains the single Shopping Control Plane.
""",
    Path("docs/shopping/API.md"): """
## M4 Shopping API

### Endpoints

- GET /shopping/health
- GET /shopping/readiness
- GET /shopping/capabilities
- GET /shopping/integrations
- GET /shopping/products
- GET /shopping/products/{product_id}
- GET /shopping/categories

### Product Query Parameters

- page: minimum 1
- page_size: 1 to 100

### Adapter Selection

- SHOPPING_CATALOG_ADAPTER=mock
- SHOPPING_CATALOG_ADAPTER=woocommerce

### Read-only Policy

M4 exposes catalog read operations only.
Product, category, order, customer, pricing, and inventory writes remain disabled.
""",
    Path("docs/shopping/ARCHITECTURE.md"): """
## M4 Architecture

AIControlCenter
    |
    +-- ShoppingSettings
    |
    +-- ShoppingService
    |
    +-- Adapter Factory
            |
            +-- MockCommerceCatalogAdapter
            |
            +-- WooCommerceRESTAdapter
                    |
                    +-- WordPress and WooCommerce

### URL Separation

- Canonical signing URL: external WordPress URL
- Internal connection URL: localhost WordPress port
- External development UI: http://bokstory.iptime.org:58088
- Internal REST connection: http://127.0.0.1:8088

### Security

- WooCommerce API Key is read-only.
- Secret files are excluded from Git.
- systemd runtime Secret permissions are 600 root:root.
- Production requires a user-owned domain and HTTPS.
- iptime.org CAA policy prevents certificate issuance for the current DDNS hostname.
""",
    Path("docs/shopping/TESTING.md"): """
## M4 Testing

Required Shopping tests:

.venv/bin/python -m pytest \
  tests/test_shopping_api.py \
  tests/test_shopping_catalog.py \
  tests/test_shopping_categories.py \
  tests/test_shopping_settings.py \
  tests/test_shopping_factory.py \
  tests/test_woocommerce_adapter.py \
  -q

Production Gate:

.venv/bin/python -m pytest -m "not integration" -q

Tests must not inherit live WooCommerce settings.
API unit tests explicitly use the Mock adapter.
""",
    Path("docs/shopping/DEPLOYMENT.md"): """
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
""",
    Path("docs/shopping/RUNBOOK.md"): """
## M4 Runbook

### Runtime Status

systemctl is-active aicontrolcenter-api.service

docker inspect \
  --format '{{.Name}} | {{.State.Status}} | {{if .State.Health}}{{.State.Health.Status}}{{end}}' \
  shopping-db \
  shopping-wordpress

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
""",
    Path("docs/shopping/SECURITY.md"): """
## M4 Security

- Catalog integration is read-only.
- WooCommerce credentials must never be committed.
- Repository Secret files:
  - deploy/shopping/.env
  - deploy/shopping/.env.admin
  - deploy/shopping/.env.woocommerce
- Runtime Secret:
  - /etc/aicontrolcenter/shopping.env
- HTTP OAuth is permitted only for the local development connection.
- Production requires HTTPS and API Key rotation.
- No real customer, payment, or order data is allowed in the HTTP development environment.
""",
}

for target, body in updates.items():
    update_section(target, body)
