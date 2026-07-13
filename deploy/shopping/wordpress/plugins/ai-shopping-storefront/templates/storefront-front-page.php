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
    <div class="orange-coco-header__top">
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
                <span aria-hidden="true">⌕</span>
            </button>

            <a
                class="orange-coco-instagram-link"
                href="#orange-coco-instagram"
                aria-label="Instagram"
            >
                ◎
            </a>

        </div>
    </div>

    <div class="orange-coco-header__navigation">
        <nav
            class="orange-coco-nav"
            aria-label="상품 및 고객 메뉴"
        >
            <a href="<?php echo esc_url($category_url()); ?>">
                ALL
            </a>

            <a
                href="<?php
                echo esc_url(
                    $category_url('women-outer')
                );
                ?>"
            >
                OUTER
            </a>

            <a
                href="<?php
                echo esc_url(
                    $category_url('women-dresses')
                );
                ?>"
            >
                DRESS
            </a>

            <div class="orange-coco-nav__group">
                <button type="button">
                    TOP
                </button>

                <div class="orange-coco-nav__submenu">
                    <a
                        href="<?php
                        echo esc_url(
                            $category_url('women-tops')
                        );
                        ?>"
                    >
                        TOP
                    </a>

                    <a
                        href="<?php
                        echo esc_url(
                            $category_url('women-knitwear')
                        );
                        ?>"
                    >
                        KNIT
                    </a>

                    <a
                        href="<?php
                        echo esc_url(
                            $category_url(
                                'women-shirts-blouses'
                            )
                        );
                        ?>"
                    >
                        BLOUSE
                    </a>
                </div>
            </div>

            <div class="orange-coco-nav__group">
                <button type="button">
                    BOTTOM
                </button>

                <div class="orange-coco-nav__submenu">
                    <a
                        href="<?php
                        echo esc_url(
                            $category_url('women-pants')
                        );
                        ?>"
                    >
                        PANTS
                    </a>

                    <a
                        href="<?php
                        echo esc_url(
                            $category_url('women-skirts')
                        );
                        ?>"
                    >
                        SKIRT
                    </a>
                </div>
            </div>

            <a
                href="<?php
                echo esc_url(
                    $category_url('women-bags')
                );
                ?>"
            >
                BAG
            </a>

            <a
                href="<?php
                echo esc_url(
                    $category_url('women-shoes')
                );
                ?>"
            >
                SHOES
            </a>

            <a
                href="<?php
                echo esc_url(
                    $category_url('women-accessories')
                );
                ?>"
            >
                ACC
            </a>

            <a
                href="<?php
                echo esc_url(
                    $category_url('men')
                );
                ?>"
            >
                MEN
            </a>

            <span
                class="orange-coco-nav__divider"
                aria-hidden="true"
            ></span>

            <a
                class="orange-coco-nav__commerce"
                href="<?php echo esc_url($cart_url); ?>"
            >
                CART
            </a>

            <a
                class="orange-coco-nav__commerce"
                href="<?php echo esc_url($checkout_url); ?>"
            >
                CHECKOUT
            </a>

            <a
                class="orange-coco-nav__commerce"
                href="<?php echo esc_url($account_url); ?>"
            >
                MY ACCOUNT
            </a>
        </nav>
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

<section class="orange-coco-info">
    <div class="orange-coco-info__grid">
        <article class="orange-coco-info__item">
            <span class="orange-coco-info__icon" aria-hidden="true">
                ◉
            </span>

            <div>
                <h3>매장 위치</h3>
                <p>오프라인 매장 안내</p>
                <a href="#store-location">위치 보기</a>
            </div>
        </article>

        <article class="orange-coco-info__item">
            <span class="orange-coco-info__icon" aria-hidden="true">
                ◌
            </span>

            <div>
                <h3>상품 문의</h3>
                <p>빠른 문의와 예약 상담</p>
                <a href="#contact">문의하기</a>
            </div>
        </article>

        <article
            id="orange-coco-instagram"
            class="orange-coco-info__item"
        >
            <span class="orange-coco-info__icon" aria-hidden="true">
                ◎
            </span>

            <div>
                <h3>INSTAGRAM</h3>
                <p>Orange Coco 스타일 소식</p>
                <a href="#" rel="noopener">바로가기</a>
            </div>
        </article>

        <article class="orange-coco-info__item">
            <span class="orange-coco-info__icon" aria-hidden="true">
                ◫
            </span>

            <div>
                <h3>영업 시간 안내</h3>
                <p>평일 11:00–20:00<br>주말 11:00–19:00</p>
                <a href="#business-hours">안내 보기</a>
            </div>
        </article>
    </div>
</section>

<footer class="orange-coco-footer">
    <div class="orange-coco-footer__inner">
        <div class="orange-coco-footer__brand">
            <strong>orange coco</strong>

            <p>
                Simple, Natural, Timeless.
            </p>
        </div>

        <div class="orange-coco-footer__information">
            <article class="orange-coco-footer__item">
                <span aria-hidden="true">◉</span>

                <div>
                    <h3>매장 위치</h3>
                    <p>오프라인 매장 안내</p>
                    <a href="#store-location">위치 보기</a>
                </div>
            </article>

            <article class="orange-coco-footer__item">
                <span aria-hidden="true">◌</span>

                <div>
                    <h3>상품 문의</h3>
                    <p>문의 및 예약 상담</p>
                    <a href="#contact">문의하기</a>
                </div>
            </article>

            <article
                id="orange-coco-instagram"
                class="orange-coco-footer__item"
            >
                <span aria-hidden="true">◎</span>

                <div>
                    <h3>INSTAGRAM</h3>
                    <p>새로운 스타일 소식</p>
                    <a href="#" rel="noopener">바로가기</a>
                </div>
            </article>

            <article class="orange-coco-footer__item">
                <span aria-hidden="true">◫</span>

                <div>
                    <h3>영업시간</h3>
                    <p>평일 11:00–20:00</p>
                    <a href="#business-hours">안내 보기</a>
                </div>
            </article>
        </div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
