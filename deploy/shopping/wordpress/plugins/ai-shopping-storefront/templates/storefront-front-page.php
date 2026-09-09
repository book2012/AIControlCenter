<?php

if (!defined('ABSPATH')) {
    exit;
}

$category_url = static function (
    string $category = ''
): string {
    $args = [
        'ai_shop_search' => '1',
        'ai_shop_page' => '1',
    ];

    if ($category !== '') {
        $args['ai_shop_category'] = $category;
    }

    return add_query_arg(
        $args,
        home_url('/')
    );
};

$cart_url = function_exists('wc_get_cart_url')
    ? wc_get_cart_url()
    : home_url('/cart/');

$checkout_url = function_exists('wc_get_checkout_url')
    ? wc_get_checkout_url()
    : home_url('/checkout/');

$account_url = function_exists('wc_get_page_permalink')
    ? wc_get_page_permalink('myaccount')
    : home_url('/my-account/');
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <?php wp_head(); ?>
</head>

<body <?php body_class('orange-coco-front-page'); ?>>
<?php wp_body_open(); ?>

<header class="orange-coco-header">
    <div class="orange-coco-header__inner">
        <button
            class="orange-coco-header__mobile-button"
            type="button"
            aria-label="메뉴 열기"
            aria-expanded="false"
        >
            <span></span>
            <span></span>
            <span></span>
        </button>

        <nav
            class="orange-coco-nav"
            aria-label="상품 카테고리"
        >
            <a href="<?php echo esc_url($category_url('new')); ?>">
                NEW
            </a>
            <a href="<?php echo esc_url($category_url('women-tops')); ?>">
                TOPS
            </a>
            <a href="<?php echo esc_url($category_url('women-bottoms')); ?>">
                BOTTOMS
            </a>
            <a href="<?php echo esc_url($category_url('women-dresses')); ?>">
                DRESSES
            </a>
            <a href="<?php echo esc_url($category_url('women-outer')); ?>">
                OUTERWEAR
            </a>
            <a href="<?php echo esc_url($category_url('men')); ?>">
                MEN
            </a>
            <a href="<?php echo esc_url($category_url('women-accessories')); ?>">
                ACCESSORIES
            </a>
        </nav>

        <a
            class="orange-coco-logo"
            href="<?php echo esc_url(home_url('/')); ?>"
            aria-label="Orange Coco 홈"
        >
            orange coco
        </a>

        <div class="orange-coco-header__actions">
            <button
                class="orange-coco-icon-button"
                id="orange-coco-search-open"
                type="button"
                aria-label="검색 열기"
            >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="11" cy="11" r="6"></circle>
                    <path d="m16 16 4 4"></path>
                </svg>
            </button>
            <a
                class="orange-coco-header-action-link"
                href="<?php echo esc_url($account_url); ?>"
            >
                ACCOUNT
            </a>
            <a
                class="orange-coco-header-action-link"
                href="<?php echo esc_url($cart_url); ?>"
            >
                BAG
            </a>
        </div>
    </div>
</header>

<main
    id="orange-coco-main"
    class="orange-coco-main"
>
    <?php
    echo do_shortcode(
        '[ai_shopping_storefront limit="10" title=""]'
    );
    ?>
</main>

<footer
    class="orange-coco-footer"
    aria-label="Orange Coco 고객 안내"
>
    <div class="orange-coco-footer__inner">
        <div class="orange-coco-footer__brand">
            <a
                class="orange-coco-footer__brand-link"
                href="<?php echo esc_url(home_url('/')); ?>"
            >
                Orange Coco
            </a>
            <p>
                Everyday pieces for your moment.
            </p>
        </div>

        <nav
            class="orange-coco-footer__links"
            aria-label="Footer navigation"
        >
            <a href="<?php echo esc_url(home_url('/')); ?>">
                SHOP
            </a>
            <a href="<?php echo esc_url($account_url); ?>">
                ACCOUNT
            </a>
            <a href="<?php echo esc_url($cart_url); ?>">
                BAG
            </a>
        </nav>

        <p class="orange-coco-footer__copyright">
            &copy; <?php echo esc_html(wp_date('Y')); ?>
            Orange Coco
        </p>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
