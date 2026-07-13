<?php
/**
 * Plugin Name: AI Shopping Storefront
 * Description: Presentation adapter for the AIControlCenter Shopping API.
 * Version: 0.16.0
 * Requires PHP: 8.1
 */

if (!defined('ABSPATH')) {
    exit;
}

define(
    'AI_SHOPPING_STOREFRONT_VERSION',
    '0.16.0'
);

define(
    'AI_SHOPPING_STOREFRONT_FILE',
    __FILE__
);

define(
    'AI_SHOPPING_STOREFRONT_DIR',
    plugin_dir_path(__FILE__)
);

define(
    'AI_SHOPPING_STOREFRONT_URL',
    plugin_dir_url(__FILE__)
);

require_once AI_SHOPPING_STOREFRONT_DIR
    . 'includes/class-cache.php';

require_once AI_SHOPPING_STOREFRONT_DIR
    . 'includes/class-api-client.php';

require_once AI_SHOPPING_STOREFRONT_DIR
    . 'includes/class-renderer.php';

require_once AI_SHOPPING_STOREFRONT_DIR
    . 'includes/class-shortcodes.php';
require_once AI_SHOPPING_STOREFRONT_DIR
    . 'includes/renderers/class-product-detail-renderer.php';

final class AI_Shopping_Storefront_Plugin
{
    private static ?AI_Shopping_API_Client $client = null;
    private static ?AI_Shopping_Product_Detail_Renderer $product_renderer = null;

    private const API_BASE_OPTION =
        'ai_shopping_api_base_url';

    private const DEFAULT_API_BASE =
        'http://host.docker.internal:8000';

    public static function boot(): void
    {
        add_action(
            'plugins_loaded',
            [self::class, 'initialize']
        );

        add_action(
            'init',
            [self::class, 'register_product_route']
        );

        add_filter(
            'query_vars',
            [self::class, 'register_query_vars']
        );

        add_action(
            'wp_enqueue_scripts',
            [self::class, 'enqueue_assets']
        );

        add_filter(
            'body_class',
            [self::class, 'body_classes']
        );

        add_filter(
            'template_include',
            [self::class, 'storefront_template'],
            99
        );


        add_action(
            'template_redirect',
            [self::class, 'redirect_legacy_storefront']
        );
    }

    public static function activate(): void
    {
        self::register_product_route();

        if (!get_option(self::API_BASE_OPTION)) {
            add_option(
                self::API_BASE_OPTION,
                self::DEFAULT_API_BASE
            );
        }

        flush_rewrite_rules();
    }

    public static function initialize(): void
    {
        $api_base = get_option(
            self::API_BASE_OPTION,
            self::DEFAULT_API_BASE
        );

        $cache = new AI_Shopping_Cache(
            30
        );

        $client = new AI_Shopping_API_Client(
            (string) $api_base,
            $cache
        );

        self::$client = $client;
        self::$product_renderer =
            new AI_Shopping_Product_Detail_Renderer();

        $renderer = new AI_Shopping_Renderer();

        $shortcodes = new AI_Shopping_Shortcodes(
            $client,
            $renderer
        );

        $shortcodes->register();
    }

    public static function storefront_template(
        string $template
    ): string {
        $product_id = get_query_var(
            'ai_shopping_product_id'
        );

        if ($product_id !== '') {
            $product_template =
                AI_SHOPPING_STOREFRONT_DIR
                . 'templates/product-detail.php';

            if (is_readable($product_template)) {
                return $product_template;
            }
        }

        if (is_front_page()) {
            $storefront_template =
                AI_SHOPPING_STOREFRONT_DIR
                . 'templates/storefront-front-page.php';

            if (is_readable($storefront_template)) {
                return $storefront_template;
            }
        }

        return $template;
    }

    public static function register_product_route(): void
    {
        add_rewrite_rule(
            '^product/([^/]+)/?$',
            'index.php?ai_shopping_product_id=$matches[1]',
            'top'
        );
    }

    public static function register_query_vars(
        array $query_vars
    ): array {
        $query_vars[] = 'ai_shopping_product_id';

        return $query_vars;
    }

    public static function render_product_page(): string
    {
        $product_id = sanitize_text_field(
            (string) get_query_var(
                'ai_shopping_product_id'
            )
        );

        if (
            $product_id === ''
            || self::$client === null
            || self::$product_renderer === null
        ) {
            return '';
        }

        $response = self::$client->get_product(
            $product_id
        );

        if (
            empty($response['success'])
            || empty($response['data'])
            || !is_array($response['data'])
        ) {
            global $wp_query;

            if ($wp_query instanceof WP_Query) {
                $wp_query->set_404();
            }

            status_header(404);
            nocache_headers();

            return self::$product_renderer->not_found(
                $product_id
            );
        }

        $product = $response['data'];

        $related_response = self::$client->search(
            [
                'category' => (
                    $product['category'] ?? ''
                ),
                'page' => 1,
                'page_size' => 8,
            ]
        );

        $related = [];

        if (
            !empty($related_response['success'])
            && !empty(
                $related_response['data']['items']
            )
        ) {
            foreach (
                $related_response['data']['items']
                as $candidate
            ) {
                if (
                    ($candidate['id'] ?? '')
                    === $product_id
                ) {
                    continue;
                }

                $related[] = $candidate;
            }
        }

        return self::$product_renderer->render(
            $product,
            array_slice($related, 0, 4)
        );
    }

    public static function body_classes(
        array $classes
    ): array {
        if (is_front_page()) {
            $classes[] = 'orange-coco-front-page';
        }

        return $classes;
    }

    public static function redirect_legacy_storefront(): void
    {
        if (
            is_page('ai-shopping')
            && !is_front_page()
        ) {
            wp_safe_redirect(
                home_url('/'),
                301
            );

            exit;
        }
    }

    public static function enqueue_assets(): void
    {
        wp_enqueue_style(
            'ai-shopping-storefront',
            AI_SHOPPING_STOREFRONT_URL
                . 'assets/storefront.css',
            [],
            AI_SHOPPING_STOREFRONT_VERSION
        );

        wp_enqueue_style(
            'orange-coco-v6',
            AI_SHOPPING_STOREFRONT_URL
                . 'assets/orange-coco-v6.css',
            ['ai-shopping-storefront'],
            AI_SHOPPING_STOREFRONT_VERSION
        );

        wp_enqueue_script(
            'ai-shopping-storefront-ui',
            AI_SHOPPING_STOREFRONT_URL
                . 'assets/storefront-ui.js',
            [],
            AI_SHOPPING_STOREFRONT_VERSION,
            true
        );
    }
}

register_activation_hook(
    __FILE__,
    [
        AI_Shopping_Storefront_Plugin::class,
        'activate',
    ]
);

AI_Shopping_Storefront_Plugin::boot();
