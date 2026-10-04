<?php

if (!defined('ABSPATH')) {
    exit;
}
?>
<!doctype html>
<html <?php language_attributes(); ?>><head>
    <meta charset="<?php bloginfo('charset'); ?>"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light">
    <meta name="description" content="agachichi — Everyday Comfort, Playful Touch. 상품을 둘러보는 미리보기 공간입니다."><title>agachichi | Everyday Comfort, Playful Touch</title>
    <?php wp_head(); ?>
</head><body <?php body_class(); ?>><?php wp_body_open(); ?>
<a class="skip-link" href="#main-content">본문 바로가기</a>
<header class="store-header">
    <a class="wordmark" id="store-home-link" href="<?php echo esc_url(home_url('/')); ?>" aria-label="agachichi 홈">agachichi<span>Everyday Comfort, Playful Touch</span></a>
    <a class="header-search" href="<?php echo esc_url(add_query_arg('ai_shop_search', '1', home_url('/'))); ?>" aria-label="상품 검색">검색 <span aria-hidden="true">↗</span></a>
    <p class="preview-notice">상품 미리보기 · 현재 구매는 지원하지 않습니다.</p>
</header>
<main id="main-content" tabindex="-1"><?php echo do_shortcode('[ai_shopping_storefront limit="24" title=""]'); ?></main>
<footer class="store-footer"><a class="wordmark" href="<?php echo esc_url(home_url('/')); ?>">agachichi</a><p>Everyday Comfort, Playful Touch</p><span>상품 미리보기 · 현재 구매는 지원하지 않습니다.</span></footer>
<?php wp_footer(); ?></body></html>
