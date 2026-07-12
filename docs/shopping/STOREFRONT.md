<!-- SHOPPING_M5_START -->

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
<!-- SHOPPING_M5_END -->
