<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Shortcodes
{
    private AI_Shopping_API_Client $client;
    private AI_Shopping_Renderer $renderer;

    public function __construct(
        AI_Shopping_API_Client $client,
        AI_Shopping_Renderer $renderer
    ) {
        $this->client = $client;
        $this->renderer = $renderer;
    }

    public function register(): void
    {
        add_shortcode(
            'ai_shopping_storefront',
            [$this, 'storefront']
        );
    }

    public function storefront(
        array $attributes = []
    ): string {
        $attributes = shortcode_atts(
            [
                'limit' => 8,
                'title' => '추천 상품',
            ],
            $attributes,
            'ai_shopping_storefront'
        );

        $limit = min(
            20,
            max(
                1,
                absint($attributes['limit'])
            )
        );

        $categories = $this->client->categories();
        $search_filters = $this->search_filters();
        $search_result = null;
        $homepage_sections = [];

        if ($this->has_search_request()) {
            $search_result = $this->client->search(
                $search_filters
            );
        } else {
            $homepage_sections = $this->homepage_sections(
                min(8, $limit)
            );
        }

        return $this->renderer->storefront(
            $this->client->featured_products(
                $limit
            ),
            $categories,
            sanitize_text_field(
                $attributes['title']
            ),
            $search_filters,
            $search_result,
            $homepage_sections
        );
    }

    private function homepage_sections(
        int $limit
    ): array {
        $definitions = [
            [
                'id' => 'new',
                'title' => 'NEW ARRIVALS',
                'category' => 'new',
            ],
            [
                'id' => 'best',
                'title' => 'BEST SELLERS',
                'category' => 'best',
            ],
            [
                'id' => 'top',
                'title' => 'TOP',
                'category' => 'women-tops',
            ],
            [
                'id' => 'dress',
                'title' => 'DRESS',
                'category' => 'women-dresses',
            ],
            [
                'id' => 'outer',
                'title' => 'OUTER',
                'category' => 'women-outer',
            ],
            [
                'id' => 'bag',
                'title' => 'BAG',
                'category' => 'women-bags',
            ],
            [
                'id' => 'sale',
                'title' => 'SALE',
                'category' => 'sale',
            ],
        ];

        $sections = [];

        foreach ($definitions as $definition) {
            $sections[] = [
                'id' => $definition['id'],
                'title' => $definition['title'],
                'payload' => $this->client->search(
                    [
                        'category' => $definition['category'],
                        'page' => 1,
                        'page_size' => $limit,
                    ]
                ),
            ];
        }

        return $sections;
    }

    private function has_search_request(): bool
    {
        return isset($_GET['ai_shop_search']);
    }

    private function search_filters(): array
    {
        $query = isset($_GET['ai_shop_q'])
            ? sanitize_text_field(
                wp_unslash($_GET['ai_shop_q'])
            )
            : '';

        $category = isset($_GET['ai_shop_category'])
            ? sanitize_text_field(
                wp_unslash(
                    $_GET['ai_shop_category']
                )
            )
            : '';

        $minimum_price = $this->optional_float(
            'ai_shop_min_price'
        );

        $maximum_price = $this->optional_float(
            'ai_shop_max_price'
        );

        $in_stock = null;

        if (isset($_GET['ai_shop_in_stock'])) {
            $raw_stock = sanitize_text_field(
                wp_unslash(
                    $_GET['ai_shop_in_stock']
                )
            );

            if ($raw_stock === 'true') {
                $in_stock = true;
            } elseif ($raw_stock === 'false') {
                $in_stock = false;
            }
        }

        $page = isset($_GET['ai_shop_page'])
            ? max(
                1,
                absint($_GET['ai_shop_page'])
            )
            : 1;

        return [
            'q' => $query,
            'category' => $category,
            'minimum_price' => $minimum_price,
            'maximum_price' => $maximum_price,
            'in_stock' => $in_stock,
            'page' => $page,
            'page_size' => 12,
        ];
    }

    private function optional_float(
        string $key
    ): ?float {
        if (
            !isset($_GET[$key])
            || $_GET[$key] === ''
        ) {
            return null;
        }

        $value = sanitize_text_field(
            wp_unslash($_GET[$key])
        );

        if (!is_numeric($value)) {
            return null;
        }

        return max(
            0,
            (float) $value
        );
    }
}
