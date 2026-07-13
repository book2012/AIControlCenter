<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_API_Client
{
    private string $base_url;

    private AI_Shopping_Cache $cache;

    public function __construct(
        string $base_url,
        AI_Shopping_Cache $cache
    ) {
        $this->base_url = untrailingslashit(
            esc_url_raw($base_url)
        );

        $this->cache = $cache;
    }

    public function featured_products(
        int $limit = 6
    ): array {
        return $this->get(
            '/shopping/featured-products',
            [
                'limit' => min(
                    20,
                    max(1, $limit)
                ),
            ]
        );
    }

    public function categories(): array
    {
        return $this->get(
            '/shopping/categories'
        );
    }

    public function search(
        array $filters
    ): array {
        $allowed = [
            'q',
            'category',
            'minimum_price',
            'maximum_price',
            'in_stock',
            'page',
            'page_size',
        ];

        $query = [];

        foreach ($allowed as $key) {
            if (!array_key_exists($key, $filters)) {
                continue;
            }

            $value = $filters[$key];

            if ($value === '' || $value === null) {
                continue;
            }

            if (is_bool($value)) {
                $query[$key] = $value
                    ? 'true'
                    : 'false';

                continue;
            }

            $query[$key] = $value;
        }

        return $this->get(
            '/shopping/search',
            $query
        );
    }


    public function get_product(
        string $product_id
    ): array {
        return $this->get(
            '/shopping/products/' . rawurlencode($product_id)
        );
    }

    private function get(
        string $path,
        array $query = []
    ): array {
        $cache_key = $path
            . ':'
            . wp_json_encode($query);

        $cached = $this->cache->get(
            $cache_key
        );

        if ($cached !== null) {
            return $cached;
        }

        $url = add_query_arg(
            $query,
            $this->base_url . $path
        );

        $response = wp_remote_get(
            $url,
            [
                'timeout' => 5,
                'redirection' => 0,
                'headers' => [
                    'Accept' => 'application/json',
                ],
            ]
        );

        if (is_wp_error($response)) {
            return [
                'success' => false,
                'error' => $response->get_error_message(),
            ];
        }

        $status = wp_remote_retrieve_response_code(
            $response
        );

        $body = wp_remote_retrieve_body(
            $response
        );

        $payload = json_decode(
            $body,
            true
        );

        if (
            $status !== 200
            || !is_array($payload)
        ) {
            return [
                'success' => false,
                'error' => 'Invalid AIControlCenter response.',
                'status' => $status,
            ];
        }

        $result = [
            'success' => true,
            'data' => $payload,
        ];

        $this->cache->set(
            $cache_key,
            $result
        );

        return $result;
    }
}
