<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Renderer
{
    public function storefront(
        array $featured,
        array $categories,
        string $title,
        array $search_filters = [],
        ?array $search_result = null,
        array $homepage_sections = []
    ): string {
        $hero_url = AI_Shopping_Agachichi_Presentation_Adapter::hero_url();

        ob_start();
        ?>
        <section class="ai-shopping-storefront">
            <header class="agachichi-hero" aria-labelledby="agachichi-hero-title">
                <div class="agachichi-hero__copy">
                    <p class="agachichi-eyebrow">agachichi</p>
                    <h1 id="agachichi-hero-title">
                        매일 편하게,<br><em>조금 더 사랑스럽게.</em>
                    </h1>
                    <p class="agachichi-hero__description">
                        Everyday Comfort, Playful Touch
                    </p>
                    <a
                        class="agachichi-text-link"
                        href="<?php echo esc_url(add_query_arg(
                            [
                                'ai_shop_search' => '1',
                                'ai_shop_category' => 'new',
                                'ai_shop_page' => '1',
                            ],
                            home_url('/')
                        )); ?>"
                    >
                        NEW EDIT <span aria-hidden="true">↗</span>
                    </a>
                </div>
                <?php if ($hero_url !== null) : ?>
                    <figure class="agachichi-hero__photo">
                        <img
                            src="<?php echo esc_url($hero_url); ?>"
                            alt="따뜻한 부티크에서 agachichi 스타일을 둘러보는 여성 모델"
                            width="1536"
                            height="1024"
                            fetchpriority="high"
                        >
                    </figure>
                <?php endif; ?>
            </header>

            <?php
            if (
                empty($featured['success'])
                || empty($categories['success'])
            ) {
                echo $this->notice('쇼핑 데이터를 불러오지 못했습니다.');
            } else {
                echo $this->categories($categories['data']['items'] ?? []);

                if ($search_result !== null) {
                    echo $this->search_form(
                        $categories['data']['items'] ?? [],
                        $search_filters
                    );
                    echo $this->search_results($search_result);
                } elseif (!empty($homepage_sections)) {
                    echo $this->homepage_sections($homepage_sections);
                } else {
                    echo $this->featured_section(
                        $featured['data']['items'] ?? []
                    );
                }
            }
            ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    private function categories(array $categories): string
    {
        if (!$categories) {
            return '';
        }

        $active_category = isset($_GET['ai_shop_category'])
            ? sanitize_text_field(wp_unslash($_GET['ai_shop_category']))
            : '';

        ob_start();
        ?>
        <nav class="agachichi-filter-rail" aria-label="상품 카테고리">
            <a
                href="<?php echo esc_url(add_query_arg(
                    ['ai_shop_search' => '1', 'ai_shop_page' => '1'],
                    home_url('/')
                )); ?>"
                <?php if ($active_category === '') : ?>aria-current="page"<?php endif; ?>
            >ALL</a>
            <?php foreach ($categories as $category) : ?>
                <?php
                $category_id = (string) ($category['id'] ?? '');
                $url = add_query_arg(
                    [
                        'ai_shop_search' => '1',
                        'ai_shop_category' => $category_id,
                        'ai_shop_page' => '1',
                    ],
                    home_url('/')
                );
                ?>
                <a
                    href="<?php echo esc_url($url); ?>"
                    <?php if ($category_id === $active_category) : ?>aria-current="page"<?php endif; ?>
                >
                    <?php echo esc_html((string) ($category['name'] ?? '')); ?>
                </a>
            <?php endforeach; ?>
        </nav>
        <?php

        return (string) ob_get_clean();
    }

    private function search_form(array $categories, array $filters): string
    {
        ob_start();
        ?>
        <form
            id="ai-shopping-search"
            class="agachichi-search-panel"
            method="get"
            action="<?php echo esc_url(home_url('/')); ?>"
            role="search"
        >
            <input type="hidden" name="ai_shop_search" value="1">
            <label for="ai-shop-q">상품 검색</label>
            <div class="agachichi-search-panel__fields">
                <input
                    id="ai-shop-q"
                    type="search"
                    name="ai_shop_q"
                    value="<?php echo esc_attr((string) ($filters['q'] ?? '')); ?>"
                    maxlength="200"
                    placeholder="상품명이나 떠오르는 단어를 입력하세요"
                >
                <button type="submit">검색</button>
            </div>
            <select name="ai_shop_category" aria-label="카테고리">
                <option value="">전체 카테고리</option>
                <?php foreach ($categories as $category) : ?>
                    <?php $category_id = (string) ($category['id'] ?? ''); ?>
                    <option
                        value="<?php echo esc_attr($category_id); ?>"
                        <?php selected((string) ($filters['category'] ?? ''), $category_id); ?>
                    >
                        <?php echo esc_html((string) ($category['name'] ?? '')); ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </form>
        <?php

        return (string) ob_get_clean();
    }

    private function search_results(array $result): string
    {
        if (empty($result['success'])) {
            return $this->notice('검색 결과를 불러오지 못했습니다.');
        }

        $data = $result['data'] ?? [];

        ob_start();
        ?>
        <section class="agachichi-collection" aria-labelledby="search-title">
            <header class="agachichi-collection__heading">
                <h2 id="search-title">상품 둘러보기</h2>
                <p><?php echo esc_html((string) ($data['total'] ?? 0)); ?>개</p>
            </header>
            <?php echo $this->products($data['items'] ?? []); ?>
            <?php
            echo $this->pagination(
                (int) ($data['page'] ?? 1),
                (int) ($data['page_size'] ?? 12),
                (int) ($data['total'] ?? 0)
            );
            ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    private function featured_section(array $products): string
    {
        ob_start();
        ?>
        <section class="agachichi-collection" aria-labelledby="featured-title">
            <header class="agachichi-collection__heading">
                <div>
                    <p class="agachichi-eyebrow">agachichi</p>
                    <h2 id="featured-title">피드</h2>
                </div>
            </header>
            <?php echo $this->products($products); ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    private function homepage_sections(array $sections): string
    {
        ob_start();

        foreach ($sections as $section) {
            $payload = $section['payload'] ?? [];
            $items = $payload['data']['items'] ?? [];

            if (empty($payload['success']) || empty($items)) {
                continue;
            }

            $section_id = sanitize_html_class(
                (string) ($section['id'] ?? 'section')
            );
            $section_category = sanitize_text_field(
                (string) ($section['category'] ?? $section_id)
            );
            ?>
            <section
                id="agachichi-<?php echo esc_attr($section_id); ?>"
                class="agachichi-collection"
                data-home-section="<?php echo esc_attr($section_id); ?>"
            >
                <header class="agachichi-collection__heading">
                    <h2><?php echo esc_html((string) ($section['title'] ?? '')); ?></h2>
                    <a
                        class="agachichi-text-link"
                        href="<?php echo esc_url(add_query_arg(
                            [
                                'ai_shop_search' => '1',
                                'ai_shop_category' => $section_category,
                            ],
                            home_url('/')
                        )); ?>"
                    >
                        모두 보기 <span aria-hidden="true">↗</span>
                    </a>
                </header>
                <?php echo $this->products($items); ?>
            </section>
            <?php
        }

        return (string) ob_get_clean();
    }

    private function products(array $products): string
    {
        if (!$products) {
            return $this->empty_products();
        }

        ob_start();
        ?>
        <div class="agachichi-product-grid">
            <?php foreach ($products as $product) : ?>
                <?php echo $this->product_card($product); ?>
            <?php endforeach; ?>
        </div>
        <?php

        return (string) ob_get_clean();
    }

    private function pagination(int $page, int $page_size, int $total): string
    {
        $total_pages = max(1, (int) ceil($total / max(1, $page_size)));

        if ($total_pages <= 1) {
            return '';
        }

        ob_start();
        ?>
        <nav class="agachichi-pagination" aria-label="검색 결과 페이지">
            <?php if ($page > 1) : ?>
                <a href="<?php echo esc_url(add_query_arg('ai_shop_page', $page - 1)); ?>">← 이전</a>
            <?php endif; ?>
            <span><?php echo esc_html($page . ' / ' . $total_pages); ?></span>
            <?php if ($page < $total_pages) : ?>
                <a href="<?php echo esc_url(add_query_arg('ai_shop_page', $page + 1)); ?>">다음 →</a>
            <?php endif; ?>
        </nav>
        <?php

        return (string) ob_get_clean();
    }

    private function product_card(array $product): string
    {
        $product_id = (string) ($product['id'] ?? '');
        $slug = sanitize_title((string) ($product['slug'] ?? $product_id));
        $url = home_url('/product/' . rawurlencode($slug) . '/');
        $image_url = AI_Shopping_Agachichi_Presentation_Adapter::image_url($product);
        $tags = implode(
            ' ',
            AI_Shopping_Agachichi_Presentation_Adapter::tags($product)
        );

        ob_start();
        ?>
        <article
            class="agachichi-product-card"
            data-product-id="<?php echo esc_attr($product_id); ?>"
        >
            <a
                class="agachichi-product-card__link"
                href="<?php echo esc_url($url); ?>"
                aria-label="상품 이미지와 해시태그 미리보기"
            >
                <div class="agachichi-product-card__photo">
                    <?php if ($image_url !== null) : ?>
                        <img
                            src="<?php echo esc_url($image_url); ?>"
                            alt="<?php echo esc_attr((string) ($product['name'] ?? '')); ?>"
                            width="800"
                            height="1200"
                            loading="lazy"
                            decoding="async"
                        >
                    <?php else : ?>
                        <span class="agachichi-product-card__fallback">
                            이미지 준비 중입니다.
                        </span>
                    <?php endif; ?>
                </div>
                <div class="agachichi-product-card__caption">
                    <p><?php echo esc_html($tags); ?></p>
                </div>
            </a>
        </article>
        <?php

        return (string) ob_get_clean();
    }

    private function empty_products(): string
    {
        return '<div class="agachichi-empty"><p>조건에 맞는 상품이 없습니다.</p></div>';
    }

    private function notice(string $message): string
    {
        return sprintf(
            '<div class="agachichi-notice">%s</div>',
            esc_html($message)
        );
    }
}
