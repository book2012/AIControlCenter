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
        ?array $search_result = null
    ): string {
        ob_start();
        ?>
        <section class="ai-shopping-storefront">
            <header class="ai-shopping-storefront__header">
                <p class="ai-shopping-storefront__eyebrow">
                    AI Home Datacenter Commerce
                </p>

                <h2>
                    <?php echo esc_html($title); ?>
                </h2>

                <p>
                    AIControlCenter가 선택하고 검색한 상품을 표시합니다.
                </p>
            </header>

            <?php
            if (
                empty($featured['success'])
                || empty($categories['success'])
            ) {
                echo $this->notice(
                    '쇼핑 데이터를 불러오지 못했습니다.'
                );
            } else {
                echo $this->categories(
                    $categories['data']['items'] ?? []
                );

                echo $this->search_form(
                    $categories['data']['items'] ?? [],
                    $search_filters
                );

                if ($search_result !== null) {
                    echo $this->search_results(
                        $search_result
                    );
                }

                echo $this->featured_section(
                    $featured['data']['items'] ?? []
                );
            }
            ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    public function categories(
        array $categories
    ): string {
        if (!$categories) {
            return '';
        }

        ob_start();
        ?>
        <nav
            class="ai-shopping-storefront__categories"
            aria-label="상품 카테고리"
        >
            <?php foreach ($categories as $category) : ?>
                <?php
                $category_id = (string) (
                    $category['id'] ?? ''
                );

                $url = add_query_arg(
                    [
                        'ai_shop_search' => '1',
                        'ai_shop_category' => $category_id,
                    ]
                );
                ?>

                <a
                    class="ai-shopping-storefront__category"
                    href="<?php echo esc_url($url); ?>"
                >
                    <?php
                    echo esc_html(
                        (string) (
                            $category['name'] ?? ''
                        )
                    );
                    ?>

                    <small>
                        <?php
                        echo esc_html(
                            (string) (
                                $category['count'] ?? 0
                            )
                        );
                        ?>
                    </small>
                </a>
            <?php endforeach; ?>
        </nav>
        <?php

        return (string) ob_get_clean();
    }

    private function search_form(
        array $categories,
        array $filters
    ): string {
        $selected_category = (string) (
            $filters['category'] ?? ''
        );

        $selected_stock = '';

        if (
            array_key_exists('in_stock', $filters)
            && $filters['in_stock'] === true
        ) {
            $selected_stock = 'true';
        } elseif (
            array_key_exists('in_stock', $filters)
            && $filters['in_stock'] === false
        ) {
            $selected_stock = 'false';
        }

        ob_start();
        ?>
        <form
            class="ai-shopping-search"
            method="get"
            action=""
        >
            <input
                type="hidden"
                name="ai_shop_search"
                value="1"
            >

            <div class="ai-shopping-search__field ai-shopping-search__field--wide">
                <label for="ai-shop-q">
                    상품 검색
                </label>

                <input
                    id="ai-shop-q"
                    type="search"
                    name="ai_shop_q"
                    value="<?php
                    echo esc_attr(
                        (string) (
                            $filters['q'] ?? ''
                        )
                    );
                    ?>"
                    placeholder="상품명 또는 설명"
                >
            </div>

            <div class="ai-shopping-search__field">
                <label for="ai-shop-category">
                    카테고리
                </label>

                <select
                    id="ai-shop-category"
                    name="ai_shop_category"
                >
                    <option value="">
                        전체
                    </option>

                    <?php foreach ($categories as $category) : ?>
                        <?php
                        $category_id = (string) (
                            $category['id'] ?? ''
                        );
                        ?>

                        <option
                            value="<?php echo esc_attr($category_id); ?>"
                            <?php
                            selected(
                                $selected_category,
                                $category_id
                            );
                            ?>
                        >
                            <?php
                            echo esc_html(
                                (string) (
                                    $category['name'] ?? ''
                                )
                            );
                            ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="ai-shopping-search__field">
                <label for="ai-shop-min-price">
                    최소 가격
                </label>

                <input
                    id="ai-shop-min-price"
                    type="number"
                    min="0"
                    step="1"
                    name="ai_shop_min_price"
                    value="<?php
                    echo esc_attr(
                        $filters['minimum_price'] ?? ''
                    );
                    ?>"
                >
            </div>

            <div class="ai-shopping-search__field">
                <label for="ai-shop-max-price">
                    최대 가격
                </label>

                <input
                    id="ai-shop-max-price"
                    type="number"
                    min="0"
                    step="1"
                    name="ai_shop_max_price"
                    value="<?php
                    echo esc_attr(
                        $filters['maximum_price'] ?? ''
                    );
                    ?>"
                >
            </div>

            <div class="ai-shopping-search__field">
                <label for="ai-shop-stock">
                    재고
                </label>

                <select
                    id="ai-shop-stock"
                    name="ai_shop_in_stock"
                >
                    <option
                        value=""
                        <?php selected($selected_stock, ''); ?>
                    >
                        전체
                    </option>

                    <option
                        value="true"
                        <?php selected($selected_stock, 'true'); ?>
                    >
                        재고 있음
                    </option>

                    <option
                        value="false"
                        <?php selected($selected_stock, 'false'); ?>
                    >
                        품절
                    </option>
                </select>
            </div>

            <div class="ai-shopping-search__actions">
                <button type="submit">
                    검색
                </button>

                <a href="<?php
                echo esc_url(
                    remove_query_arg(
                        [
                            'ai_shop_search',
                            'ai_shop_q',
                            'ai_shop_category',
                            'ai_shop_min_price',
                            'ai_shop_max_price',
                            'ai_shop_in_stock',
                            'ai_shop_page',
                        ]
                    )
                );
                ?>">
                    초기화
                </a>
            </div>
        </form>
        <?php

        return (string) ob_get_clean();
    }

    private function search_results(
        array $result
    ): string {
        if (empty($result['success'])) {
            return $this->notice(
                '검색 결과를 불러오지 못했습니다.'
            );
        }

        $data = $result['data'] ?? [];
        $items = $data['items'] ?? [];
        $total = (int) ($data['total'] ?? 0);

        ob_start();
        ?>
        <section class="ai-shopping-search-results">
            <header class="ai-shopping-section-header">
                <h3>검색 결과</h3>

                <p>
                    총 <?php echo esc_html((string) $total); ?>개
                </p>
            </header>

            <?php echo $this->products($items); ?>

            <?php
            echo $this->pagination(
                (int) ($data['page'] ?? 1),
                (int) ($data['page_size'] ?? 12),
                $total
            );
            ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    private function featured_section(
        array $products
    ): string {
        ob_start();
        ?>
        <section class="ai-shopping-featured">
            <header class="ai-shopping-section-header">
                <h3>추천 상품</h3>
            </header>

            <?php echo $this->products($products); ?>
        </section>
        <?php

        return (string) ob_get_clean();
    }

    public function products(
        array $products
    ): string {
        if (!$products) {
            return $this->notice(
                '표시할 상품이 없습니다.'
            );
        }

        ob_start();
        ?>
        <div class="ai-shopping-storefront__grid">
            <?php foreach ($products as $product) : ?>
                <?php
                echo $this->product_card(
                    $product
                );
                ?>
            <?php endforeach; ?>
        </div>
        <?php

        return (string) ob_get_clean();
    }

    private function pagination(
        int $page,
        int $page_size,
        int $total
    ): string {
        $total_pages = max(
            1,
            (int) ceil(
                $total / max(1, $page_size)
            )
        );

        if ($total_pages <= 1) {
            return '';
        }

        ob_start();
        ?>
        <nav
            class="ai-shopping-pagination"
            aria-label="검색 결과 페이지"
        >
            <?php if ($page > 1) : ?>
                <a href="<?php
                echo esc_url(
                    add_query_arg(
                        'ai_shop_page',
                        $page - 1
                    )
                );
                ?>">
                    이전
                </a>
            <?php endif; ?>

            <span>
                <?php
                echo esc_html(
                    $page . ' / ' . $total_pages
                );
                ?>
            </span>

            <?php if ($page < $total_pages) : ?>
                <a href="<?php
                echo esc_url(
                    add_query_arg(
                        'ai_shop_page',
                        $page + 1
                    )
                );
                ?>">
                    다음
                </a>
            <?php endif; ?>
        </nav>
        <?php

        return (string) ob_get_clean();
    }

    private function product_card(
        array $product
    ): string {
        $slug = sanitize_title(
            (string) (
                $product['slug'] ?? ''
            )
        );

        $url = home_url(
            '/product/' . $slug . '/'
        );

        $description = wp_trim_words(
            wp_strip_all_tags(
                (string) (
                    $product['description'] ?? ''
                )
            ),
            22
        );

        $price = number_format_i18n(
            (float) (
                $product['price'] ?? 0
            )
        );

        ob_start();
        ?>
        <article class="ai-shopping-product-card">
            <p class="ai-shopping-product-card__category">
                <?php
                echo esc_html(
                    (string) (
                        $product['category']
                        ?? 'Uncategorized'
                    )
                );
                ?>
            </p>

            <h3>
                <a href="<?php echo esc_url($url); ?>">
                    <?php
                    echo esc_html(
                        (string) (
                            $product['name'] ?? ''
                        )
                    );
                    ?>
                </a>
            </h3>

            <p class="ai-shopping-product-card__description">
                <?php echo esc_html($description); ?>
            </p>

            <footer class="ai-shopping-product-card__footer">
                <strong>
                    <?php echo esc_html($price); ?>원
                </strong>

                <span>
                    <?php
                    echo !empty($product['in_stock'])
                        ? '재고 있음'
                        : '품절';
                    ?>
                </span>
            </footer>
        </article>
        <?php

        return (string) ob_get_clean();
    }

    private function notice(
        string $message
    ): string {
        return sprintf(
            '<div class="ai-shopping-storefront__notice">%s</div>',
            esc_html($message)
        );
    }
}
