<?php

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Manifest-backed presentation mapping for the accepted agachichi lookbook.
 *
 * This class never changes product data and never accepts an API image URL.
 * It only maps an approved demo product to a packaged plugin asset.
 */
final class AI_Shopping_Agachichi_Presentation_Adapter
{
    public const PRESENTATION_IDENTIFIER =
        'SHOP_MEDIA_003_AGACHICHI';

    private const MANIFEST_RELATIVE_PATH =
        'assets/agachichi-v1/deployment-manifest.json';

    private static ?array $manifest_assets = null;

    public static function presentation_identifier(): string
    {
        return self::PRESENTATION_IDENTIFIER;
    }

    public static function image_url(array $product): ?string
    {
        $product_id = (string) ($product['id'] ?? '');
        $category = self::category_key(
            (string) ($product['category'] ?? '')
        );

        if (
            ($product['source'] ?? '') !== 'demo'
            || $category === ''
            || !preg_match(
                '/^oc-demo-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/',
                $product_id
            )
        ) {
            return null;
        }

        $asset = self::manifest_assets()[$product_id] ?? null;

        if (
            !is_array($asset)
            || !isset($asset['deployed_relative_path'])
            || strpos(
                (string) $asset['deployed_relative_path'],
                'assets/agachichi-v1/products/' . $category . '/'
            ) !== 0
        ) {
            return null;
        }

        return esc_url(
            AI_SHOPPING_STOREFRONT_URL
            . ltrim((string) $asset['deployed_relative_path'], '/')
        );
    }

    public static function hero_url(): ?string
    {
        $manifest_path = AI_SHOPPING_STOREFRONT_DIR
            . self::MANIFEST_RELATIVE_PATH;

        if (!is_readable($manifest_path)) {
            return null;
        }

        $manifest = json_decode(
            (string) file_get_contents($manifest_path),
            true
        );

        foreach (($manifest['assets'] ?? []) as $asset) {
            if (
                ($asset['asset_type'] ?? '') !== 'hero'
                || ($asset['media_id'] ?? '') !== 'hero-agachichi'
                || ($asset['deployed_relative_path'] ?? '')
                    !== 'assets/agachichi-v1/hero-agachichi.jpg'
                || !preg_match(
                    '/^[a-f0-9]{64}$/',
                    (string) ($asset['sha256'] ?? '')
                )
            ) {
                continue;
            }

            return esc_url(
                AI_SHOPPING_STOREFRONT_URL
                . $asset['deployed_relative_path']
            );
        }

        return null;
    }

    public static function tags(array $product): array
    {
        $category = self::category_key(
            (string) ($product['category'] ?? '')
        );

        $tags = [
            'top' => ['#상의', '#데일리', '#미니멀'],
            'bottom' => ['#팬츠', '#클래식', '#심플'],
            'outer' => ['#아우터', '#소프트', '#가을무드'],
            'dress' => ['#원피스', '#페미닌', '#데일리룩'],
            'bag' => ['#가방', '#미니멀', '#데일리백'],
            'acc' => ['#액세서리', '#포인트', '#데일리'],
        ][$category] ?? ['#아가치치', '#데일리'];

        $name = (string) ($product['name'] ?? '');

        if (strpos($name, '블라우스') !== false) {
            $tags[0] = '#블라우스';
        } elseif (strpos($name, '셔츠') !== false) {
            $tags[0] = '#셔츠';
        }

        if (
            strpos($name, '오버핏') !== false
            || strpos($name, '와이드') !== false
        ) {
            $tags[1] = '#오버핏';
        } elseif (
            strpos($name, '니트') !== false
            || strpos($name, '가디건') !== false
        ) {
            $tags[1] = '#니트';
        }

        return $tags;
    }

    private static function category_key(string $category): string
    {
        $category = strtolower(trim($category));

        return [
            'women-tops' => 'top',
            'women-bottoms' => 'bottom',
            'women-outer' => 'outer',
            'women-dresses' => 'dress',
            'women-bags' => 'bag',
            'women-accessories' => 'acc',
        ][$category] ?? $category;
    }

    private static function manifest_assets(): array
    {
        if (self::$manifest_assets !== null) {
            return self::$manifest_assets;
        }

        $manifest_path = AI_SHOPPING_STOREFRONT_DIR
            . self::MANIFEST_RELATIVE_PATH;

        if (!is_readable($manifest_path)) {
            return self::$manifest_assets = [];
        }

        $manifest = json_decode(
            (string) file_get_contents($manifest_path),
            true
        );

        if (
            !is_array($manifest)
            || ($manifest['presentation_identifier'] ?? '')
                !== self::PRESENTATION_IDENTIFIER
            || !is_array($manifest['assets'] ?? null)
        ) {
            return self::$manifest_assets = [];
        }

        $assets = [];

        foreach ($manifest['assets'] as $asset) {
            $product_id = (string) ($asset['product_id'] ?? '');
            $deployed_path = (string) (
                $asset['deployed_relative_path'] ?? ''
            );

            if (
                !preg_match(
                    '/^oc-demo-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/',
                    $product_id
                )
                || !preg_match(
                    '/^assets\/agachichi-v1\/products\/'
                    . '(top|bottom|outer|dress|bag|acc)\/'
                    . preg_quote($product_id, '/') . '\.jpg$/',
                    $deployed_path
                )
                || !preg_match(
                    '/^[a-f0-9]{64}$/',
                    (string) ($asset['sha256'] ?? '')
                )
                || isset($assets[$product_id])
            ) {
                continue;
            }

            $assets[$product_id] = $asset;
        }

        return self::$manifest_assets = $assets;
    }
}
