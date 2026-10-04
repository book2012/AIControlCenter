<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Shortcodes
{
    private AI_Shopping_API_Client $client;
    private AI_Shopping_Renderer $renderer;

    public function __construct(AI_Shopping_API_Client $client, AI_Shopping_Renderer $renderer)
    {
        $this->client = $client;
        $this->renderer = $renderer;
    }

    public function register(): void
    {
        add_shortcode('ai_shopping_storefront', [$this, 'storefront']);
    }

    public function storefront(array $attributes = []): string
    {
        $attributes = shortcode_atts(['limit' => 24, 'title' => ''], $attributes, 'ai_shopping_storefront');
        $categories = $this->client->categories();
        $search_filters = $this->search_filters($categories);
        $search_result = null;
        $home_result = $this->has_search_request()
            ? ['success' => true, 'data' => ['items' => [], 'total' => 0]]
            : $this->home_result($categories, $search_filters, min(24, max(1, absint($attributes['limit']))));

        if ($this->has_search_request()) {
            $search_result = $this->client->search([
                'q' => $search_filters['q'],
                'category' => $search_filters['category'],
                'page' => $search_filters['page'],
                'page_size' => 12,
            ]);
        }

        return $this->renderer->storefront(
            $home_result,
            $categories,
            sanitize_text_field($attributes['title']),
            $search_filters,
            $search_result
        );
    }

    private function home_result(array $categories, array $filters, int $page_size): array
    {
        $collection = $filters['collection'];
        if (in_array($collection, ['hot', 'sale'], true)) {
            return ['success' => true, 'data' => ['items' => [], 'total' => 0, 'page' => $filters['page'], 'page_size' => $page_size]];
        }
        $category = '';
        if ($collection === 'update') {
            $category = 'new';
        } elseif ($filters['category'] !== '') {
            $category = $filters['category'];
        }
        if ($category !== '') {
            foreach (($categories['data']['items'] ?? []) as $item) {
                if (is_array($item) && (($item['slug'] ?? '') === $category || ($item['id'] ?? '') === $category)) {
                    $category = (string) ($item['id'] ?? $category);
                    break;
                }
            }
        }
        return $this->client->search([
            'category' => $category,
            'page' => $filters['page'],
            'page_size' => $page_size,
        ]);
    }

    private function has_search_request(): bool
    {
        return isset($_GET['ai_shop_search']);
    }

    private function search_filters(array $categories): array
    {
        $query = isset($_GET['ai_shop_q']) ? sanitize_text_field(wp_unslash($_GET['ai_shop_q'])) : '';
        $category_slug = isset($_GET['ai_shop_category']) ? sanitize_title(wp_unslash($_GET['ai_shop_category'])) : '';
        $category_id = '';
        foreach (($categories['data']['items'] ?? []) as $item) {
            if (is_array($item) && (($item['slug'] ?? '') === $category_slug || ($item['id'] ?? '') === $category_slug)) {
                $category_id = (string) ($item['id'] ?? '');
                break;
            }
        }
        $page = isset($_GET['ai_shop_page']) ? max(1, absint($_GET['ai_shop_page'])) : 1;
        return [
            'q' => $query,
            'category' => $category_id,
            'category_slug' => $category_slug,
            'collection' => isset($_GET['ai_shop_collection']) ? sanitize_key(wp_unslash($_GET['ai_shop_collection'])) : '',
            'page' => $page,
        ];
    }
}
