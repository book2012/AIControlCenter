<?php

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Server-rendered presentation adapter for the accepted DEV storefront.
 *
 * This class only projects read responses into the DEV presentation contract.
 * Catalog policy, commerce state, and mutations remain in AIControlCenter.
 */
final class AI_Shopping_Renderer
{
    private const HOME_FILTERS = [
        ['all', '전체', ''], ['hot', 'HOT', ''], ['sale', 'SALE', ''],
        ['update', 'UPDATE', ''], ['top', 'TOP', 'women-tops'],
        ['bottom', 'BOTTOM', 'women-bottoms'], ['outer', 'OUTER', 'women-outer'],
        ['dress', 'DRESS', 'women-dresses'], ['bag', 'BAG', 'women-bags'],
        ['acc', 'ACC', 'women-accessories'], ['men', 'MEN', 'men'],
    ];

    private const LABELS = [
        'new' => '신상품', 'best' => '인기 상품', 'sale' => '할인 상품',
        'top' => '상의', 'bottom' => '하의', 'outer' => '아우터', 'dress' => '원피스',
        'bag' => '가방', 'acc' => '액세서리', 'women-tops' => '상의',
        'women-bottoms' => '하의', 'women-outer' => '아우터', 'women-dresses' => '원피스',
        'women-bags' => '가방', 'women-accessories' => '액세서리',
    ];

    public function storefront(
        array $home_result,
        array $categories,
        string $title,
        array $search_filters = [],
        ?array $search_result = null,
        array $homepage_sections = []
    ): string {
        unset($title, $homepage_sections);
        $category_items = $this->category_items($categories);
        if ($search_result !== null) {
            return $this->search_page($category_items, $search_filters, $search_result);
        }
        return $this->home_page($category_items, $search_filters, $home_result);
    }

    private function home_page(array $categories, array $state, array $result): string
    {
        unset($categories);
        $collection = (string) ($state['collection'] ?? '');
        $page = max(1, (int) ($state['page'] ?? 1));
        $success = !empty($result['success']);
        $data = $success && is_array($result['data'] ?? null) ? $result['data'] : [];
        $items = $this->catalog_items($data['items'] ?? []);
        $total = (int) ($data['total'] ?? 0);
        ob_start();
        ?>
        <section class="hero" aria-labelledby="hero-title">
            <div class="hero-copy">
                <p class="eyebrow">agachichi</p>
                <h1 id="hero-title">매일 편하게,<br><em>조금 더 사랑스럽게.</em></h1>
            </div>
            <?php $hero_url = AI_Shopping_Agachichi_Presentation_Adapter::hero_url(); ?>
            <?php if ($hero_url !== null) : ?>
                <figure class="hero-photo">
                    <img src="<?php echo esc_url($hero_url); ?>" alt="따뜻한 조명의 부티크에서 크림색과 오렌지색 옷을 둘러보는 여성 모델" width="1536" height="1024" fetchpriority="high">
                </figure>
            <?php endif; ?>
        </section>
        <nav class="filter-rail" aria-label="피드 필터"><?php echo $this->home_filters($state); ?></nav>
        <div class="feed-heading"><h1 id="feed-title">피드</h1><p id="feed-count"><?php echo esc_html('상품 ' . $total . '개'); ?></p></div>
        <p id="feed-status" class="home-status" role="status" aria-live="polite"><?php
            if (!$success) {
                echo esc_html('상품을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.');
            } elseif (!$items) {
                echo esc_html($collection === 'sale'
                    ? 'SALE 상품이 없습니다. 현재 canonical 할인 데이터가 없습니다.'
                    : ($collection === 'hot' ? 'HOT 상품이 없습니다. 명시된 HOT 컬렉션이 없습니다.' : '조건에 맞는 상품이 없습니다.'));
            }
        ?></p>
        <ul id="home-feed" class="product-grid unified-feed" aria-label="전체 상품 피드" aria-busy="false"><?php echo $this->cards($items, $this->home_url($state)); ?></ul>
        <div class="browse-link-wrap">
            <?php if ($success && count($items) === 24 && $total > ($page * 24)) : ?>
                <a id="feed-load-more" class="browse-link" href="<?php echo esc_url($this->home_url(array_merge($state, ['page' => $page + 1]))); ?>">더 보기 · 다음 피드 <span aria-hidden="true">↗</span></a>
            <?php endif; ?>
            <?php if (!$success) : ?><button id="home-retry" class="text-button" type="button">다시 시도</button><?php endif; ?>
            <a id="browse-all" class="browse-link" href="<?php echo esc_url($this->listing_url([])); ?>">전체 상품 둘러보기 · 검색 <span aria-hidden="true">↗</span></a>
        </div>
        <?php
        return (string) ob_get_clean();
    }

    private function search_page(array $categories, array $filters, array $result): string
    {
        $success = !empty($result['success']);
        $data = $success && is_array($result['data'] ?? null) ? $result['data'] : [];
        $items = $this->catalog_items($data['items'] ?? []);
        $total = (int) ($data['total'] ?? 0);
        $page = max(1, (int) ($filters['page'] ?? 1));
        $page_size = max(1, (int) ($data['page_size'] ?? 12));
        $pages = max(1, (int) ceil($total / $page_size));
        $category_slug = (string) ($filters['category_slug'] ?? '');
        $category_label = $category_slug === '' ? '전체 상품' : ($this->category_label($category_slug) ?: '선택한 카테고리');
        $query = (string) ($filters['q'] ?? '');
        ob_start();
        ?>
        <div id="listing-view"><section class="collection" id="collection" aria-labelledby="collection-title">
            <div class="collection-heading"><h1 id="collection-title">상품 둘러보기</h1><p id="product-count"><?php echo esc_html($success ? '상품 ' . $total . '개' : '상품을 불러오지 못했습니다'); ?></p></div>
            <?php echo $this->search_form($filters); ?>
            <nav class="category-nav" id="category-nav" aria-label="상품 카테고리"><?php echo $this->category_links($categories, $category_slug, $query); ?></nav>
            <p id="category-status" class="field-note" role="status"><?php echo esc_html((string) ($filters['category_status'] ?? '')); ?></p>
            <div class="tag-strip"><p class="tag-caption" id="mood-caption">이런 검색어는 어때요?</p><div class="tags" role="group" aria-labelledby="mood-caption">
                <?php foreach (['블라우스', '미니멀', '내추럴', '주말', '출근'] as $mood) : ?><a data-query="<?php echo esc_attr($mood); ?>" href="<?php echo esc_url($this->listing_url(['category' => $category_slug, 'q' => $mood])); ?>">#<?php echo esc_html($mood); ?></a><?php endforeach; ?>
            </div><p class="field-note">검색어 예시이며, 상품 속성 필터가 아닙니다.</p></div>
            <p id="active-conditions" class="active-conditions" role="status" aria-live="polite"><?php echo esc_html('카테고리: ' . $category_label . ($query !== '' ? ' · 검색어: ‘' . $query . '’' : '')); ?></p>
            <div class="catalog-feedback"><p id="catalog-status" role="status" aria-live="polite"><?php
                if (!$success) { echo esc_html('상품을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.'); }
                elseif (!$items) { echo esc_html('조건에 맞는 상품이 없습니다. 검색어나 페이지를 바꿔 보세요.'); }
            ?></p><?php if (!$success) : ?><button id="retry" class="text-button" type="button">다시 시도</button><?php endif; ?><?php if ($category_slug !== '' || $query !== '') : ?><a id="clear-filters" class="text-button" href="<?php echo esc_url($this->listing_url([])); ?>">검색·카테고리 초기화</a><?php endif; ?></div>
            <p id="catalog-note" class="field-note">상품 미리보기</p>
            <ul id="product-grid" class="product-grid" aria-label="상품 목록" aria-busy="false"><?php echo $this->cards($items, $this->listing_url($filters)); ?></ul>
            <?php echo $this->pagination($filters, $page, $pages, $success && ($pages > 1 || $page > 1)); ?>
        </section></div>
        <?php
        return (string) ob_get_clean();
    }

    private function search_form(array $filters): string
    {
        $category = (string) ($filters['category_slug'] ?? '');
        $query = (string) ($filters['q'] ?? '');
        ob_start();
        ?>
        <form id="search-panel" class="search-panel" role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>">
            <input type="hidden" name="ai_shop_search" value="1"><input id="search-category" type="hidden" name="ai_shop_category" value="<?php echo esc_attr($category); ?>">
            <label for="search-input">상품 검색</label><div class="search-fields"><input id="search-input" name="ai_shop_q" type="search" value="<?php echo esc_attr($query); ?>" maxlength="200" placeholder="상품명이나 떠오르는 단어를 입력하세요" autocomplete="off"><button class="solid-button" type="submit">검색</button></div>
            <p id="search-context" class="field-note"><?php echo esc_html(($this->category_label($category) ?: '전체 상품') . ' 안에서 검색합니다.'); ?></p>
        </form>
        <?php
        return (string) ob_get_clean();
    }

    private function category_items(array $response): array
    {
        $items = $response['data']['items'] ?? [];
        if (!is_array($items)) { return []; }
        $result = [];
        foreach ($items as $item) {
            if (!is_array($item)) { continue; }
            $slug = sanitize_title((string) ($item['slug'] ?? ''));
            $id = sanitize_text_field((string) ($item['id'] ?? ''));
            if ($slug === '' || $id === '' || $slug === 'hot') { continue; }
            $item['slug'] = $slug; $item['id'] = $id;
            $item['label'] = $this->category_label($slug) ?: sanitize_text_field((string) ($item['name'] ?? $slug));
            $result[] = $item;
        }
        return $result;
    }

    private function category_links(array $categories, string $current, string $query): string
    {
        $links = [sprintf('<a href="%s" data-category=""%s>전체 상품</a>', esc_url($this->listing_url(['q' => $query])), $current === '' ? ' aria-current="page"' : '')];
        foreach ($categories as $category) {
            $slug = (string) $category['slug'];
            $links[] = sprintf('<a href="%s" data-category="%s" data-category-id="%s"%s>%s</a>', esc_url($this->listing_url(['category' => $slug, 'q' => $query])), esc_attr($slug), esc_attr((string) $category['id']), $slug === $current ? ' aria-current="page"' : '', esc_html((string) $category['label']));
        }
        return implode("\n", $links);
    }

    private function home_filters(array $state): string
    {
        $active = (string) ($state['collection'] ?? '');
        if (!in_array($active, ['hot', 'sale', 'update'], true)) {
            $active = 'all';
            foreach (self::HOME_FILTERS as $filter) { if ($filter[2] !== '' && $filter[2] === ($state['category_slug'] ?? '')) { $active = $filter[0]; break; } }
        }
        $links = [];
        foreach (self::HOME_FILTERS as $filter) {
            [$key, $label, $slug] = $filter; $args = [];
            if (in_array($key, ['hot', 'sale', 'update'], true)) { $args['ai_shop_collection'] = $key; }
            elseif ($slug !== '') { $args['ai_shop_category'] = $slug; }
            $links[] = sprintf('<a href="%s" data-feed-filter="%s" data-feed-kind="%s"%s>%s</a>', esc_url(add_query_arg($args, home_url('/'))), esc_attr($key), in_array($key, ['hot', 'sale', 'update'], true) ? 'collection' : 'category', $key === $active ? ' aria-current="page"' : '', esc_html($label));
        }
        return implode("\n", $links);
    }

    private function cards(array $products, string $back): string
    {
        $cards = [];
        foreach ($products as $product) {
            if (!is_array($product)) { continue; }
            $id = sanitize_text_field((string) ($product['id'] ?? ''));
            if ($id === '') { continue; }
            $image_url = AI_Shopping_Agachichi_Presentation_Adapter::image_url($product);
            $href = add_query_arg('return_to', $back, home_url('/product/' . rawurlencode($id) . '/'));
            $tags = implode(' ', AI_Shopping_Agachichi_Presentation_Adapter::tags($product));
            ob_start();
            ?>
            <li class="product-card" data-product-id="<?php echo esc_attr($id); ?>"><a class="product-link" href="<?php echo esc_url($href); ?>" aria-label="상품 이미지와 해시태그 미리보기"><div class="product-photo">
                <?php if ($image_url !== null) : ?><img width="800" height="1200" loading="lazy" decoding="async" src="<?php echo esc_url($image_url); ?>" alt="<?php echo esc_attr((string) ($product['name'] ?? '')); ?>"><?php else : ?><span class="photo-fallback">이미지 준비 중입니다.</span><?php endif; ?>
            </div><div class="product-caption"><p class="product-tags"><?php echo esc_html($tags); ?></p></div></a></li>
            <?php
            $cards[] = (string) ob_get_clean();
        }
        return implode("\n", $cards);
    }

    private function pagination(array $filters, int $page, int $pages, bool $visible): string
    {
        $base = ['category' => (string) ($filters['category_slug'] ?? ''), 'q' => (string) ($filters['q'] ?? '')];
        ob_start();
        ?>
        <nav class="pagination" aria-label="상품 목록 페이지"<?php echo $visible ? '' : ' hidden'; ?>>
            <?php if ($page > 1) : ?><a id="previous-page" class="text-button" href="<?php echo esc_url($this->listing_url(array_merge($base, ['page' => max(1, $page - 1)]))); ?>">← 이전</a><?php endif; ?>
            <span id="page-label" aria-live="polite"><?php echo esc_html($page . ' / ' . $pages . ' 페이지'); ?></span>
            <?php if ($page < $pages) : ?><a id="next-page" class="text-button" href="<?php echo esc_url($this->listing_url(array_merge($base, ['page' => $page + 1]))); ?>">다음 →</a><?php endif; ?>
        </nav>
        <?php
        return (string) ob_get_clean();
    }

    private function catalog_items($items): array
    {
        if (!is_array($items)) { return []; }
        return array_values(array_filter($items, static fn($item): bool => is_array($item)));
    }

    private function home_url(array $state): string
    {
        $args = []; $collection = (string) ($state['collection'] ?? '');
        if (in_array($collection, ['hot', 'sale', 'update'], true)) { $args['ai_shop_collection'] = $collection; }
        elseif (($state['category_slug'] ?? '') !== '') { $args['ai_shop_category'] = (string) $state['category_slug']; }
        if ((int) ($state['page'] ?? 1) > 1) { $args['ai_shop_page'] = (int) $state['page']; }
        return add_query_arg($args, home_url('/'));
    }

    private function listing_url(array $filters): string
    {
        $args = ['ai_shop_search' => '1']; $category = (string) ($filters['category_slug'] ?? $filters['category'] ?? ''); $query = (string) ($filters['q'] ?? ''); $page = (int) ($filters['page'] ?? 1);
        if ($category !== '') { $args['ai_shop_category'] = $category; }
        if ($query !== '') { $args['ai_shop_q'] = $query; }
        if ($page > 1) { $args['ai_shop_page'] = $page; }
        return add_query_arg($args, home_url('/'));
    }

    private function category_label(string $value): string
    {
        return self::LABELS[strtolower(trim($value))] ?? '';
    }
}
