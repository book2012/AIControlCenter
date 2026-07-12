from pathlib import Path


START = "<!-- SHOPPING_M5_START -->"
END = "<!-- SHOPPING_M5_END -->"


def update_section(path: Path, body: str) -> None:
    if not path.exists():
        print(f"SKIPPED: {path}")
        return

    content = path.read_text(encoding="utf-8")
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

    path.write_text(
        content.rstrip() + "\n",
        encoding="utf-8",
    )

    print(f"UPDATED: {path}")


sections = {
    Path("README.md"): """
## AI Shopping Platform — M5 Storefront

AI Shopping Platform now provides an external Storefront powered by AIControlCenter.

Implemented:

- Featured Products
- Product Search
- Category Filter
- Price Filter
- Stock Filter
- Pagination
- Product Image and Placeholder
- Modular WordPress Presentation Plugin
- External Storefront page

Storefront:

http://bokstory.iptime.org:58088/ai-shopping/

WordPress remains the Presentation Layer.
AIControlCenter owns all Shopping business logic.
""",
    Path("MASTER.md"): """
## Shopping Platform M5 Status

Milestone:

AI Shopping Storefront Foundation

State:

- Featured Product API implemented
- Product Search API implemented
- Product image contract implemented
- Storefront Plugin active
- External Storefront reachable
- Search and filters connected to AIControlCenter
- M5 Production Gate and Git closeout in progress

Next milestone:

M6 AI Product Generation and Approval Foundation
""",
    Path("ROADMAP.md"): """
## Shopping Platform Service Roadmap

### M5 — AI Shopping Storefront Foundation

- [x] Featured Products API
- [x] Product Search API
- [x] Category Navigation
- [x] Price Filters
- [x] Stock Filter
- [x] Pagination
- [x] Product Image Support
- [x] Placeholder Fallback
- [x] WordPress Presentation Plugin
- [x] External Storefront
- [ ] Final Documentation and Git Closeout

### M6 — AI Product Generation

- [ ] Product Draft Model
- [ ] AI Product Generator
- [ ] AI Description Writer
- [ ] AI SEO Writer
- [ ] AI Category Suggestion
- [ ] Approval Workflow
- [ ] Controlled WooCommerce Write
- [ ] Audit Log

### M7 — Shopping Operations

- [ ] Order Read Integration
- [ ] Customer Read Integration
- [ ] Inventory Monitoring
- [ ] Shopping Dashboard
- [ ] Notifications
- [ ] n8n Automation
""",
    Path("TODO.md"): """
## Shopping Platform Next Tasks

- Complete M5 Git closeout
- Define AI Product Draft schema
- Implement AI Product Generator in read-only draft mode
- Add approval state machine
- Add audit event model
- Design controlled WooCommerce write gate
- Add Shopping Dashboard Storefront status
- Acquire user-owned Production domain
- Configure public HTTPS
- Validate Mac mini M4 ARM64 deployment
""",
    Path("CHANGELOG.md"): """
## Shopping Platform M5 — Unreleased

### Added

- Featured Products API
- Product Search API
- Category, price, and stock filters
- Search pagination
- Product image URL contract
- WooCommerce representative image mapping
- Image placeholder fallback
- Modular AI Shopping Storefront Plugin
- WordPress AIControlCenter API client
- WordPress Presentation Cache
- Storefront shortcode
- Responsive Storefront CSS
- External AI Shopping page

### Fixed

- Storefront Renderer search UI integration
- Search API client query serialization
- Boolean stock parameter serialization
- WooCommerce image mapping tests
- Test helper contract inconsistencies
- Trailing whitespace and blank-line issues

### Security

- Storefront does not receive WooCommerce credentials
- WordPress calls read-only AIControlCenter endpoints
- Search input is sanitized
- Rendered output is escaped
- Business Logic remains in AIControlCenter
""",
    Path("PROJECT_HISTORY.md"): """
## Shopping Platform M5 History

M5 introduced the first external AI Shopping Storefront.

The Storefront was implemented as a modular WordPress Presentation Plugin.

WordPress displays Featured Products, categories, search results, price filters, stock filters, pagination, and product images.

AIControlCenter continues to own product selection, search validation, Commerce Adapter access, and future recommendation logic.

The implementation was validated through the external ipTIME DDNS development address while Production HTTPS remains deferred to a user-owned domain.
""",
    Path("docs/ARCHITECTURE.md"): """
## Shopping Storefront Layer

WooCommerce provides Commerce data.

AIControlCenter consumes and normalizes Commerce data through the WooCommerce Adapter.

AIControlCenter exposes Featured, Search, Category, and Product APIs.

The WordPress AI Shopping Storefront Plugin consumes these APIs and renders the external customer-facing page.

No Shopping recommendation, pricing, inventory, AI, or workflow logic is implemented inside WordPress.
""",
}

for target, body in sections.items():
    update_section(target, body)
