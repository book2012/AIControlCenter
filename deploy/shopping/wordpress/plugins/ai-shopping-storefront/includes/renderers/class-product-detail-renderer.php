<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Product_Detail_Renderer
{
    private const LABELS = [
        'top' => '상의', 'bottom' => '하의', 'outer' => '아우터', 'dress' => '원피스',
        'bag' => '가방', 'acc' => '액세서리', 'women-tops' => '상의',
        'women-bottoms' => '하의', 'women-outer' => '아우터', 'women-dresses' => '원피스',
        'women-bags' => '가방', 'women-accessories' => '액세서리',
    ];

    public function render(array $product, array $related_products = [], bool $order_preview_enabled = false): string
    {
        unset($related_products);
        $product_id = (string) ($product['id'] ?? '');
        $name = (string) ($product['name'] ?? '');
        $category = (string) ($product['category'] ?? '');
        $description = (string) ($product['description'] ?? '');
        $image_url = AI_Shopping_Agachichi_Presentation_Adapter::image_url($product);
        $price = $this->price_label($product);
        $in_stock = !empty($product['in_stock']);
        $order_enabled = $order_preview_enabled && $in_stock;
        ob_start();
        ?>
        <section id="detail-view" class="product-detail" aria-labelledby="detail-name">
            <a id="back-to-list" class="text-button back-link" href="<?php echo esc_url($this->return_url()); ?>"><?php echo esc_html($this->return_label()); ?></a>
            <div class="detail-feedback"><p id="detail-status" role="status" aria-live="polite"></p><button id="detail-retry" class="text-button" type="button" hidden>다시 시도</button></div>
            <div id="detail-content" class="detail-layout" data-product-id="<?php echo esc_attr($product_id); ?>" aria-busy="false">
                <div class="product-photo detail-photo" id="detail-photo">
                    <?php if ($image_url !== null) : ?><img id="detail-image" width="800" height="1200" decoding="async" src="<?php echo esc_url($image_url); ?>" alt="<?php echo esc_attr($name); ?>"><?php else : ?><span class="photo-fallback">이미지 준비 중입니다.</span><?php endif; ?>
                </div>
                <div class="detail-copy">
                    <p class="eyebrow">상품 미리보기</p>
                    <p id="detail-category" class="product-category"><?php echo esc_html($this->label($category) ?: $category); ?></p>
                    <h1 id="detail-name"><?php echo esc_html($name); ?></h1>
                    <p id="detail-price" class="detail-price"><?php echo esc_html($price); ?></p>
                    <p id="detail-availability" class="availability"><?php echo esc_html($in_stock ? '재고 있음' : '품절'); ?></p>
                    <section id="variant-section" class="variant-section" aria-labelledby="variant-title"><h2 id="variant-title">SIZE</h2><div id="detail-variants"><?php echo $this->variants($product['variants'] ?? []); ?></div></section>
                    <section id="order-section" aria-labelledby="order-title">
                        <h2 id="order-title">주문 요청</h2><label for="order-quantity">수량</label><input id="order-quantity" type="number" min="1" max="1000" value="1">
                        <button id="order-submit" class="inquiry-primary" type="button" aria-describedby="order-status"<?php echo $order_enabled ? '' : ' disabled'; ?>>주문하기</button>
                        <p id="order-status" role="status" aria-live="polite"><?php echo esc_html($order_enabled ? '주문 후 운영자가 확인합니다. 결제·배송 확정은 별도입니다.' : '주문 기능 준비 중입니다.'); ?></p>
                        <button id="order-check" type="button" disabled>주문 상태 확인</button><button id="order-new" type="button" disabled>새 주문 요청</button>
                    </section>
                    <section id="inquiry-section" class="inquiry-section" aria-labelledby="inquiry-title">
                        <h2 id="inquiry-title">상품 문의</h2><label for="inquiry-message">문의내용</label><textarea id="inquiry-message" maxlength="1000" rows="4" placeholder="궁금한 내용을 남겨주세요."></textarea><button id="inquiry-submit" class="inquiry-primary" type="button">상품 문의하기</button><p id="inquiry-status" role="status" aria-live="polite"></p>
                        <div id="inquiry-result" hidden><p>문의가 생성되었습니다.</p><p>문의번호: <strong id="inquiry-id"></strong></p><button id="inquiry-copy" type="button">문의내용 복사</button><button id="inquiry-kakao" type="button" hidden>카카오 오픈채팅</button><button id="inquiry-instagram" type="button" hidden>인스타그램</button></div>
                    </section>
                    <p class="detail-notice"><?php echo esc_html($order_enabled ? 'DEV 주문 요청 · 결제·배송 확정은 별도입니다.' : '상품 미리보기 · 현재 구매는 지원하지 않습니다.'); ?></p>
                    <section id="description-section" class="description-section" aria-labelledby="description-title"><h2 id="description-title">상품 설명</h2><p id="detail-description"><?php echo esc_html($description !== '' ? $description : '등록된 상품 설명이 없습니다.'); ?></p></section>
                </div>
            </div>
        </section>
        <?php
        return (string) ob_get_clean();
    }

    public function not_found(string $product_id): string
    {
        ob_start();
        ?>
        <section id="detail-view" class="product-detail" aria-labelledby="detail-name"><a class="text-button back-link" href="<?php echo esc_url(home_url('/')); ?>">← 홈으로</a><div class="detail-feedback"><p id="detail-status" role="status" aria-live="polite">상품이 없거나 현재 공개되지 않았습니다.</p></div><div class="detail-copy"><h1 id="detail-name">상품을 찾을 수 없습니다</h1><p class="field-note">상품번호: <?php echo esc_html($product_id); ?></p></div></section>
        <?php
        return (string) ob_get_clean();
    }

    private function variants($variants): string
    {
        if (!is_array($variants) || !$variants) { return '<p class="variant-empty">판매 옵션 준비 중입니다.</p>'; }
        $controls = [];
        foreach ($variants as $variant) {
            if (!is_array($variant)) { continue; }
            $id = sanitize_text_field((string) ($variant['id'] ?? ''));
            $label = sanitize_text_field((string) ($variant['label'] ?? ''));
            if ($id === '' || $label === '') { continue; }
            $controls[] = '<button type="button" class="variant-option" data-variant-id="' . esc_attr($id) . '" aria-pressed="false"' . (!empty($variant['available']) ? '' : ' disabled') . '>' . esc_html($label) . '</button>';
        }
        return $controls ? '<div class="variant-options" role="group" aria-label="사이즈 선택">' . implode('', $controls) . '</div>' : '<p class="variant-empty">판매 옵션 준비 중입니다.</p>';
    }

    private function price_label(array $product): string
    {
        $amount = number_format_i18n((float) ($product['price'] ?? 0), 0);
        return (($product['currency'] ?? 'KRW') === 'KRW') ? $amount . '원' : (string) ($product['currency'] ?? 'KRW') . ' ' . $amount;
    }

    private function label(string $category): string
    {
        return self::LABELS[strtolower(trim($category))] ?? '';
    }

    private function return_url(): string
    {
        $raw = isset($_GET['return_to']) ? wp_unslash($_GET['return_to']) : '';
        if (!is_string($raw) || $raw === '') { return add_query_arg('ai_shop_search', '1', home_url('/')); }
        $url = wp_validate_redirect($raw, '');
        if ($url === '') { return add_query_arg('ai_shop_search', '1', home_url('/')); }
        $parts = wp_parse_url($url);
        $home = wp_parse_url(home_url('/'));
        if (($parts['host'] ?? '') !== ($home['host'] ?? '') || !in_array($parts['path'] ?? '/', [$home['path'] ?? '/', '/'], true)) {
            return add_query_arg('ai_shop_search', '1', home_url('/'));
        }
        return $url;
    }

    private function return_label(): string
    {
        $url = $this->return_url();
        return strpos($url, 'ai_shop_search=1') !== false ? '← 상품 목록으로' : '← 홈으로';
    }
}
