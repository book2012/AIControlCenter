<?php
/**
 * Plugin Name: AI Shopping Storefront
 * Description: Presentation adapter for the AIControlCenter Shopping API.
 * Version: 0.3.0
 * Requires PHP: 8.1
 */

if (!defined('ABSPATH')) {
    exit;
}

define(
    'AI_SHOPPING_STOREFRONT_VERSION',
    '0.3.0'
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

final class AI_Shopping_Storefront_Plugin
{
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
            'wp_enqueue_scripts',
            [self::class, 'enqueue_assets']
        );
    }

    public static function activate(): void
    {
        if (!get_option(self::API_BASE_OPTION)) {
            add_option(
                self::API_BASE_OPTION,
                self::DEFAULT_API_BASE
            );
        }
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

        $renderer = new AI_Shopping_Renderer();

        $shortcodes = new AI_Shopping_Shortcodes(
            $client,
            $renderer
        );

        $shortcodes->register();
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
