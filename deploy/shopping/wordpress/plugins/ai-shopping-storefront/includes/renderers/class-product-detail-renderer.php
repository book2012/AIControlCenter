<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Product_Detail_Renderer
{
    public function render(
        array $product,
        array $related_products = []
    ): string {
        $product_id = (string) (
            $product['id'] ?? ''
        );

        $name = (string) (
            $product['name'] ?? ''
        );

        $category = (string) (
            $product['category'] ?? ''
        );

        $description = (string) (
            $product['description'] ?? ''
        );

        $image_url = esc_url(
            (string) (
                $product['image_url'] ?? ''
            )
        );

        $price = number_format_i18n(
            (float) (
                $product['price'] ?? 0
            )
        );

        $currency = (string) (
            $product['currency'] ?? 'KRW'
        );

        $in_stock = !empty(
            $product['in_stock']
        );

        $kakao_url = (string) apply_filters(
            'ai_shopping_kakao_inquiry_url',
            '#',
            $product
        );

        $instagram_url = (string) apply_filters(
            'ai_shopping_instagram_inquiry_url',
            '#',
            $product
        );

        ob_start();
        ?>
        <main
            class="orange-coco-product-page"
            data-product-id="<?php
            echo esc_attr($product_id);
            ?>"
        >
            <section class="orange-coco-product-detail">
                <div class="orange-coco-product-detail__gallery">
                    <?php if ($image_url !== '') : ?>
                        <figure
                            class="orange-coco-product-detail__main-image"
                        >
                            <img
                                src="<?php echo $image_url; ?>"
                                alt="<?php echo esc_attr($name); ?>"
                                loading="eager"
                                decoding="async"
                            >
                        </figure>
                    <?php else : ?>
                        <div
                            class="orange-coco-product-detail__placeholder"
                        >
                            orange coco
                        </div>
                    <?php endif; ?>
                </div>

                <div class="orange-coco-product-detail__summary">
                    <?php if ($category !== '') : ?>
                        <p
                            class="orange-coco-product-detail__category"
                        >
                            <?php echo esc_html($category); ?>
                        </p>
                    <?php endif; ?>

                    <h1>
                        <?php echo esc_html($name); ?>
                    </h1>

                    <p
                        class="orange-coco-product-detail__price"
                    >
                        <?php echo esc_html($price); ?>원
                    </p>

                    <p
                        class="orange-coco-product-detail__stock <?php
                        echo $in_stock
                            ? 'is-in-stock'
                            : 'is-out-of-stock';
                        ?>"
                    >
                        <?php
                        echo $in_stock
                            ? '구매 문의 가능'
                            : '현재 품절';
                        ?>
                    </p>

                    <?php if ($description !== '') : ?>
                        <div
                            class="orange-coco-product-detail__story"
                        >
                            <p
                                class="orange-coco-product-detail__eyebrow"
                            >
                                STYLE STORY
                            </p>

                            <?php
                            echo wp_kses_post(
                                wpautop(
                                    esc_html($description)
                                )
                            );
                            ?>
                        </div>
                    <?php endif; ?>

                    <div
                        class="orange-coco-product-detail__options"
                    >
                        <fieldset>
                            <legend>COLOR</legend>

                            <button
                                type="button"
                                class="is-selected"
                                aria-pressed="true"
                            >
                                IVORY
                            </button>

                            <button
                                type="button"
                                aria-pressed="false"
                            >
                                BEIGE
                            </button>

                            <button
                                type="button"
                                aria-pressed="false"
                            >
                                BLACK
                            </button>
                        </fieldset>

                        <fieldset>
                            <legend>SIZE</legend>

                            <button
                                type="button"
                                aria-pressed="false"
                            >
                                S
                            </button>

                            <button
                                type="button"
                                class="is-selected"
                                aria-pressed="true"
                            >
                                M
                            </button>

                            <button
                                type="button"
                                aria-pressed="false"
                            >
                                L
                            </button>
                        </fieldset>
                    </div>

                    <div
                        class="orange-coco-product-detail__actions"
                    >
                        <button
                            type="button"
                            class="orange-coco-product-detail__wishlist"
                            data-product-id="<?php
                            echo esc_attr($product_id);
                            ?>"
                        >
                            관심상품
                        </button>

                        <a
                            class="orange-coco-product-detail__inquiry"
                            href="<?php
                            echo esc_url($kakao_url);
                            ?>"
                            data-product-id="<?php
                            echo esc_attr($product_id);
                            ?>"
                        >
                            카카오 구매 문의
                        </a>

                        <a
                            class="orange-coco-product-detail__instagram"
                            href="<?php
                            echo esc_url($instagram_url);
                            ?>"
                            data-product-id="<?php
                            echo esc_attr($product_id);
                            ?>"
                        >
                            Instagram 문의
                        </a>
                    </div>

                    <dl
                        class="orange-coco-product-detail__meta"
                    >
                        <div>
                            <dt>상품번호</dt>
                            <dd>
                                <?php
                                echo esc_html($product_id);
                                ?>
                            </dd>
                        </div>

                        <div>
                            <dt>통화</dt>
                            <dd>
                                <?php
                                echo esc_html($currency);
                                ?>
                            </dd>
                        </div>
                    </dl>
                </div>
            </section>

            <?php if ($related_products) : ?>
                <section
                    class="orange-coco-related-products"
                >
                    <header>
                        <h2>You May Also Like</h2>
                    </header>

                    <div
                        class="orange-coco-related-products__grid"
                    >
                        <?php
                        foreach (
                            array_slice(
                                $related_products,
                                0,
                                4
                            )
                            as $related
                        ) :
                            $related_id = rawurlencode(
                                (string) (
                                    $related['id'] ?? ''
                                )
                            );

                            $related_url = home_url(
                                '/product/'
                                . $related_id
                                . '/'
                            );

                            $related_image = esc_url(
                                (string) (
                                    $related['image_url']
                                    ?? ''
                                )
                            );
                            ?>
                            <article
                                class="orange-coco-related-card"
                            >
                                <a
                                    href="<?php
                                    echo esc_url(
                                        $related_url
                                    );
                                    ?>"
                                >
                                    <?php
                                    if (
                                        $related_image !== ''
                                    ) :
                                        ?>
                                        <img
                                            src="<?php
                                            echo $related_image;
                                            ?>"
                                            alt="<?php
                                            echo esc_attr(
                                                (string) (
                                                    $related['name']
                                                    ?? ''
                                                )
                                            );
                                            ?>"
                                            loading="lazy"
                                            decoding="async"
                                        >
                                    <?php endif; ?>

                                    <h3>
                                        <?php
                                        echo esc_html(
                                            (string) (
                                                $related['name']
                                                ?? ''
                                            )
                                        );
                                        ?>
                                    </h3>

                                    <p>
                                        <?php
                                        echo esc_html(
                                            number_format_i18n(
                                                (float) (
                                                    $related['price']
                                                    ?? 0
                                                )
                                            )
                                        );
                                        ?>원
                                    </p>
                                </a>
                            </article>
                        <?php endforeach; ?>
                    </div>
                </section>
            <?php endif; ?>
        </main>
        <?php

        return (string) ob_get_clean();
    }

    public function not_found(
        string $product_id
    ): string {
        ob_start();
        ?>
        <main class="orange-coco-product-page">
            <section
                class="orange-coco-product-not-found"
            >
                <p>PRODUCT NOT FOUND</p>

                <h1>
                    상품을 찾을 수 없습니다.
                </h1>

                <p>
                    상품번호:
                    <?php echo esc_html($product_id); ?>
                </p>

                <a href="<?php echo esc_url(home_url('/')); ?>">
                    쇼핑 계속하기
                </a>
            </section>
        </main>
        <?php

        return (string) ob_get_clean();
    }
}
