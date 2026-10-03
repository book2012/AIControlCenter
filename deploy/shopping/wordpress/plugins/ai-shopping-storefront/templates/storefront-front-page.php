<?php

if (!defined('ABSPATH')) {
    exit;
}

$category_url = static function (string $category = ''): string {
    $args = [
        'ai_shop_search' => '1',
        'ai_shop_page' => '1',
    ];

    if ($category !== '') {
        $args['ai_shop_category'] = $category;
    }

    return add_query_arg($args, home_url('/'));
};

$search_url = add_query_arg(
    ['ai_shop_search' => '1'],
    home_url('/')
);

$cart_url = function_exists('wc_get_cart_url')
    ? wc_get_cart_url()
    : home_url('/cart/');

$account_url = function_exists('wc_get_page_permalink')
    ? wc_get_page_permalink('myaccount')
    : home_url('/my-account/');
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light">
    <meta name="description" content="agachichi — Everyday Comfort, Playful Touch.">
    <title>agachichi | Everyday Comfort, Playful Touch</title>
    <?php wp_head(); ?>
</head>

<body <?php body_class('agachichi-front-page'); ?>>
<?php wp_body_open(); ?>

<a class="agachichi-skip-link" href="#agachichi-main">본문 바로가기</a>

<header class="agachichi-header">
    <div class="agachichi-header__inner">
        <button
            class="agachichi-menu-button"
            type="button"
            aria-label="메뉴 열기"
            aria-expanded="false"
            aria-controls="agachichi-navigation"
        >
            <span></span><span></span><span></span>
        </button>

        <nav
            id="agachichi-navigation"
            class="agachichi-navigation"
            aria-label="상품 카테고리"
        >
            <a href="<?php echo esc_url($category_url('new')); ?>">NEW</a>
            <a href="<?php echo esc_url($category_url('women-tops')); ?>">TOPS</a>
            <a href="<?php echo esc_url($category_url('women-bottoms')); ?>">BOTTOMS</a>
            <a href="<?php echo esc_url($category_url('women-dresses')); ?>">DRESSES</a>
            <a href="<?php echo esc_url($category_url('women-outer')); ?>">OUTERWEAR</a>
            <a href="<?php echo esc_url($category_url('women-bags')); ?>">BAGS</a>
            <a href="<?php echo esc_url($category_url('women-accessories')); ?>">ACCESSORIES</a>
        </nav>

        <a
            class="agachichi-wordmark"
            href="<?php echo esc_url(home_url('/')); ?>"
            aria-label="agachichi 홈"
        >
            agachichi
            <span>Everyday Comfort, Playful Touch</span>
        </a>

        <div class="agachichi-header__actions">
            <a class="agachichi-header-link" href="<?php echo esc_url($search_url); ?>">
                SEARCH <span aria-hidden="true">↗</span>
            </a>
            <a class="agachichi-header-link" href="<?php echo esc_url($account_url); ?>">
                ACCOUNT
            </a>
            <a class="agachichi-header-link" href="<?php echo esc_url($cart_url); ?>">
                BAG
            </a>
        </div>
    </div>
    <p class="agachichi-preview-notice">
        상품 미리보기 · 현재 구매는 지원하지 않습니다.
    </p>
</header>

<main id="agachichi-main" class="agachichi-main" tabindex="-1">
    <?php echo do_shortcode('[ai_shopping_storefront limit="10" title=""]'); ?>
</main>

<footer class="agachichi-footer" aria-label="agachichi 고객 안내">
    <div class="agachichi-footer__inner">
        <div>
            <a
                class="agachichi-footer__brand"
                href="<?php echo esc_url(home_url('/')); ?>"
            >
                agachichi
            </a>
            <p>Everyday Comfort, Playful Touch</p>
        </div>

        <nav class="agachichi-footer__links" aria-label="Footer navigation">
            <a href="<?php echo esc_url(home_url('/')); ?>">SHOP</a>
            <a href="<?php echo esc_url($account_url); ?>">ACCOUNT</a>
            <a href="<?php echo esc_url($cart_url); ?>">BAG</a>
        </nav>

        <p class="agachichi-footer__copyright">
            &copy; <?php echo esc_html(wp_date('Y')); ?> agachichi
        </p>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
