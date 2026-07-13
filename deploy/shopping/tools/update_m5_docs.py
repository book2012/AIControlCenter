from pathlib import Path


START = "<!-- SHOPPING_M5_START -->"
END = "<!-- SHOPPING_M5_END -->"


def update_section(path: Path, body: str) -> None:
    content = (
        path.read_text(encoding="utf-8")
        if path.exists()
        else ""
    )

    section = f"{START}\n{body.rstrip()}\n{END}"

    if START in content and END in content:
        before = content.split(START, 1)[0].rstrip()
        after = content.split(END, 1)[1].lstrip()

        content = "\n\n".join(
            part
            for part in (
                before,
                section,
                after,
            )
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
## M5 — AI Shopping Storefront Foundation

Status: Implementation complete. Production Gate and Git closeout in progress.

### Implemented

- Featured Products API
- Product Search API
- Category navigation
- Minimum and maximum price filters
- Stock availability filter
- Search pagination
- Product image URL support
- Image placeholder fallback
- Modular WordPress Presentation Plugin
- WordPress shortcode
- AIControlCenter API client
- WordPress transient cache
- External Storefront page

### Storefront URL

http://bokstory.iptime.org:58088/ai-shopping/

### Architecture Rule

AIControlCenter owns product selection, search, filtering, validation, and future recommendation logic.

WordPress only renders AIControlCenter responses.
""",
    Path("docs/shopping/API.md"): """
## M5 Storefront APIs

### Featured Products

GET /shopping/featured-products

Query:

- limit: 1 to 20

Response includes:

- items
- total
- available_catalog_total
- limit
- strategy

Current deterministic strategy:

in_stock_first

### Product Search

GET /shopping/search

Query parameters:

- q
- category
- minimum_price
- maximum_price
- in_stock
- page
- page_size

AIControlCenter validates price ranges and pagination.

### Image Field

Product responses include:

image_url

The value is null when WooCommerce has no representative image.
""",
    Path("docs/shopping/ARCHITECTURE.md"): """
## M5 Storefront Architecture

WooCommerce
    |
    v
WooCommerceRESTAdapter
    |
    v
ShoppingService
    |
    +-- Featured Products
    +-- Search
    +-- Categories
    +-- Image URL normalization
    |
    v
AIControlCenter REST API
    |
    v
AI Shopping Storefront Plugin
    |
    +-- API Client
    +-- Cache
    +-- Shortcodes
    +-- Renderer
    +-- CSS
    |
    v
WordPress Presentation Layer

### WordPress Responsibilities

- User input rendering
- Input sanitization
- API request forwarding
- Short-lived response cache
- HTML and CSS rendering
- Error fallback messages

### Forbidden WordPress Responsibilities

- Product recommendation decisions
- Price calculation
- Inventory policies
- AI provider calls
- Order automation
- Approval workflows
""",
    Path("docs/shopping/STOREFRONT.md"): """
# AI Shopping Storefront

## Plugin Location

deploy/shopping/wordpress/plugins/ai-shopping-storefront

## Plugin Structure

ai-shopping-storefront.php

includes/class-api-client.php
includes/class-cache.php
includes/class-renderer.php
includes/class-shortcodes.php

assets/storefront.css

## Shortcode

[ai_shopping_storefront limit="6" title="AI 추천 상품"]

## Storefront Page

Slug:

ai-shopping

External URL:

http://bokstory.iptime.org:58088/ai-shopping/

## Internal API URL

http://host.docker.internal:8000

## Features

- Featured Products
- Product Search
- Category selection
- Price filtering
- Stock filtering
- Pagination
- Product image rendering
- Placeholder fallback
- Mobile responsive layout

## Cache

WordPress transient cache is used only as a short Presentation Cache.

The default cache lifetime is 30 seconds.

Business state is not stored in WordPress.
""",
    Path("docs/shopping/TESTING.md"): """
## M5 Testing

### Shopping Tests

.venv/bin/python -m pytest \
  tests/test_shopping_api.py \
  tests/test_shopping_catalog.py \
  tests/test_shopping_categories.py \
  tests/test_shopping_featured.py \
  tests/test_shopping_search.py \
  tests/test_shopping_settings.py \
  tests/test_shopping_factory.py \
  tests/test_woocommerce_adapter.py \
  -q

### Full Non-integration Suite

.venv/bin/python -m pytest -m "not integration" -q

### PHP Syntax Validation

docker exec shopping-wordpress php -l \
  /var/www/html/wp-content/plugins/ai-shopping-storefront/ai-shopping-storefront.php

All files in the plugin includes directory must also pass php -l.

### External Validation

- Storefront HTTP 200
- Search form exists
- Search result section exists
- Product image or Placeholder exists
- No recent PHP Fatal or Parse Error
""",
    Path("docs/shopping/DEPLOYMENT.md"): """
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
""",
    Path("docs/shopping/RUNBOOK.md"): """
## M5 Storefront Runbook

### Check Plugin

docker exec shopping-wordpress \
  test -f \
  /var/www/html/wp-content/plugins/ai-shopping-storefront/ai-shopping-storefront.php

### Check External Page

curl -I \
  http://bokstory.iptime.org:58088/ai-shopping/

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
""",
    Path("docs/shopping/SECURITY.md"): """
## M5 Storefront Security

- WordPress API requests use the internal Docker host gateway.
- WooCommerce Consumer credentials are not available to the WordPress Plugin.
- The Plugin calls AIControlCenter public read endpoints only.
- Search input is sanitized before forwarding.
- Output is escaped before rendering.
- API redirection is disabled in the Plugin client.
- WordPress Presentation Cache stores only read responses.
- No customer, order, payment, or write credentials are exposed to Storefront.
""",
}

for target, body in updates.items():
    update_section(target, body)
