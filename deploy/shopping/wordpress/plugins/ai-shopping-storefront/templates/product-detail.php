<?php

if (!defined('ABSPATH')) {
    exit;
}

$product_page =
    AI_Shopping_Storefront_Plugin::render_product_page();

get_header();
?>

<div class="orange-coco-product-shell">
    <?php
    echo wp_kses_post($product_page);
    ?>
</div>

<?php
get_footer();
