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
            <a href="<?php echo esc_url($category_url()); ?>">
                ALL
            </a>

            <a href="<?php echo esc_url(
                $category_url('new')
            ); ?>">
                NEW
            </a>

            <a href="<?php echo esc_url(
                $category_url('women-tops')
            ); ?>">
                TOP
            </a>

            <a href="<?php echo esc_url(
                $category_url('women-bottoms')
            ); ?>">
                BOTTOM
            </a>

            <a href="<?php echo esc_url(
                $category_url('women-dresses')
            ); ?>">
                DRESS
            </a>

            <a href="<?php echo esc_url(
                $category_url('women-outer')
            ); ?>">
                OUTER
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
            <a
                class="orange-coco-header-action-link"
                href="<?php echo esc_url($account_url); ?>"
            >
                My account
            </a>

            <a
                class="orange-coco-header-action-link"
                href="<?php echo esc_url($cart_url); ?>"
            >
                Cart
            </a>

            <button
                class="orange-coco-icon-button"
                id="orange-coco-search-open"
                type="button"
                aria-label="검색 열기"
            >
                <svg
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                >
                    <circle cx="11" cy="11" r="6"></circle>
                    <path d="m16 16 4 4"></path>
                </svg>
            </button>

            <a
                class="orange-coco-icon-button"
                href="https://www.instagram.com/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
            >
                <svg
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                >
                    <rect
                        x="3"
                        y="3"
                        width="18"
                        height="18"
                        rx="5"
                    ></rect>
                    <circle cx="12" cy="12" r="4"></circle>
                    <circle
                        cx="17.4"
                        cy="6.6"
                        r="1"
                        class="orange-coco-instagram-dot"
                    ></circle>
                </svg>
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

<footer
    class="orange-coco-footer"
    aria-label="Orange Coco 고객 안내"
>
    <div class="orange-coco-footer__grid">
        <article class="orange-coco-footer-card">
            <span class="orange-coco-footer-card__icon">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                        d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"
                    ></path>
                    <circle cx="12" cy="10" r="2.5"></circle>
                </svg>
            </span>

            <div>
                <h2>매장 위치</h2>
                <p>
                    경기도 남양주시 다산동 4002-1<br>
                    플루리움, 에시앙 원앙관 1층 153호
                </p>

                <a href="<?php echo esc_url(
                    home_url('/location/')
                ); ?>">
                    위치 보기
                </a>
            </div>
        </article>

        <article class="orange-coco-footer-card">
            <span class="orange-coco-footer-card__icon">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                        d="M21 11.5a8.5 8.5 0 0 1-9 8.5 10 10 0 0 1-4-.8L3 21l1.7-4.4A8.5 8.5 0 1 1 21 11.5Z"
                    ></path>
                    <path d="M8 12h.01M12 12h.01M16 12h.01"></path>
                </svg>
            </span>

            <div>
                <h2>문의하기</h2>
                <p>
                    상품, 재고 및 방문 관련 문의를<br>
                    편리하게 남겨주세요.
                </p>

                <a href="<?php echo esc_url(
                    home_url('/contact/')
                ); ?>">
                    문의하기
                </a>
            </div>
        </article>

        <article class="orange-coco-footer-card">
            <span class="orange-coco-footer-card__icon">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="12" cy="12" r="9"></circle>
                    <path
                        d="M9.8 9a2.3 2.3 0 1 1 3.2 2.1c-.7.3-1 1-1 1.7"
                    ></path>
                    <path d="M12 16.5h.01"></path>
                </svg>
            </span>

            <div>
                <h2>자주하는 질문</h2>
                <p>
                    배송, 교환, 매장 이용에 대한<br>
                    답변을 확인하세요.
                </p>

                <a href="<?php echo esc_url(
                    home_url('/faq/')
                ); ?>">
                    FAQ 보기
                </a>
            </div>
        </article>

        <article class="orange-coco-footer-card">
            <span class="orange-coco-footer-card__icon">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="12" cy="12" r="9"></circle>
                    <path d="M12 7v5l3.5 2"></path>
                </svg>
            </span>

            <div>
                <h2>영업시간 안내</h2>
                <p>
                    매일 10:00 ~ 18:00<br>
                    방문 전 문의를 권장합니다.
                </p>

                <a href="<?php echo esc_url(
                    home_url('/business-hours/')
                ); ?>">
                    안내 보기
                </a>
            </div>
        </article>
    </div>

    <p class="orange-coco-footer__copyright">
        &copy; <?php echo esc_html(wp_date('Y')); ?>
        Orange Coco
    </p>
</footer>

<?php wp_footer(); ?>
</body>
</html>
