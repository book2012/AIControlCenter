<?php
/**
 * Production-only account page presentation.
 *
 * This layer changes presentation and session navigation only. It does not
 * enable customer registration or phone verification.
 */
if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Account_Presentation
{
    private const PROD_HOST = 'agachichi.duckdns.org';

    public static function boot(): void
    {
        $host = strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST));
        if ($host !== self::PROD_HOST) {
            return;
        }

        add_action('wp_enqueue_scripts', [self::class, 'enqueue_assets']);
        add_filter('body_class', [self::class, 'body_classes']);
        add_filter('document_title_parts', [self::class, 'document_title_parts']);
        add_action('wp_body_open', [self::class, 'render_header'], 5);
        add_action('wp_footer', [self::class, 'render_footer'], 5);
        add_action('woocommerce_before_customer_login_form', [self::class, 'render_login_heading'], 5);
    }

    private static function is_account_page(): bool
    {
        return function_exists('is_account_page') && is_account_page();
    }

    public static function enqueue_assets(): void
    {
        if (!self::is_account_page()) {
            return;
        }

        wp_enqueue_style(
            'aicc-prod-account-presentation',
            AI_SHOPPING_STOREFRONT_URL . 'assets/account-presentation.css',
            [],
            AI_SHOPPING_STOREFRONT_VERSION
        );
        wp_enqueue_script(
            'aicc-prod-account-presentation',
            AI_SHOPPING_STOREFRONT_URL . 'assets/account-presentation.js',
            [],
            AI_SHOPPING_STOREFRONT_VERSION,
            true
        );
    }

    public static function body_classes(array $classes): array
    {
        if (self::is_account_page()) {
            $classes[] = 'aicc-prod-account';
        }
        return $classes;
    }

    public static function document_title_parts(array $parts): array
    {
        if (!self::is_account_page()) {
            return $parts;
        }

        $parts['title'] = is_user_logged_in() ? '내 계정' : '로그인';
        $parts['site'] = 'agachichi';
        return $parts;
    }

    public static function render_header(): void
    {
        if (!self::is_account_page()) {
            return;
        }

        $logged_in = is_user_logged_in();
        $logout_url = $logged_in
            ? esc_url(wp_nonce_url(wc_get_account_endpoint_url('customer-logout'), 'customer-logout'))
            : '';
        $auth_link = $logged_in
            ? '<a class="header-logout" href="' . $logout_url . '" data-aicc-prod-logout>LOG OUT</a>'
            : '<a class="header-login is-active" href="/my-account/" aria-current="page">LOGIN</a>';
        $account_links = $logged_in
            ? '<a class="header-orders" href="/my-account/orders/">주문내역</a><a class="header-profile" href="/my-account/">내 정보</a>'
            : '<a class="header-orders" href="/homepage/storefront/my-orders">주문내역</a>';

        echo '<header class="aicc-prod-account-header"><a class="aicc-prod-wordmark" href="/homepage/storefront/">agachichi<span>Everyday Comfort, Playful Touch</span></a><nav class="aicc-prod-account-nav" aria-label="주요 메뉴"><a href="/homepage/storefront/search">검색</a>'
            . $auth_link
            . '<a href="/homepage/storefront/cart">장바구니</a>'
            . $account_links
            . '</nav></header>';
    }

    public static function render_footer(): void
    {
        if (!self::is_account_page()) {
            return;
        }

        echo '<footer class="aicc-prod-account-footer"><a href="/homepage/storefront/">agachichi</a><p>Everyday Comfort, Playful Touch</p></footer>';
    }

    public static function render_login_heading(): void
    {
        echo '<header class="aicc-prod-account-heading"><p>AGACHICHI MEMBERS</p><h1>로그인</h1><span>계정에 로그인해 주문 내역을 확인하세요.</span></header>';
        echo '<p class="aicc-prod-guest-order"><a href="/homepage/storefront/my-orders">비회원 주문 조회 · 휴대폰 인증</a></p>';
    }

}
