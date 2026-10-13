<?php
/** Branded WooCommerce account dashboard with recent orders and account actions. */
if (!defined('ABSPATH')) { exit; }
$current_user = wp_get_current_user();
$orders = wc_get_orders([
    'customer' => get_current_user_id(),
    'limit' => 5,
    'orderby' => 'date',
    'order' => 'DESC',
]);
?>
<div class="aicc-member-dashboard">
    <?php if (isset($_GET['account_error'])) : ?>
        <p class="woocommerce-error" role="alert">회원 탈퇴를 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.</p>
    <?php endif; ?>
    <section class="aicc-dashboard-orders" aria-labelledby="aicc-dashboard-orders-title">
        <div class="aicc-dashboard-heading">
            <div><p class="aicc-dialog-eyebrow">MY ORDERS</p><h1 id="aicc-dashboard-orders-title">주문내역</h1></div>
            <a href="<?php echo esc_url(wc_get_endpoint_url('orders', '', wc_get_page_permalink('myaccount'))); ?>">전체 주문내역</a>
        </div>
        <?php if ($orders) : ?>
            <div class="aicc-orders-table-wrap"><table class="aicc-orders-table">
                <thead><tr><th scope="col">주문번호</th><th scope="col">주문일</th><th scope="col">상태</th><th scope="col">결제금액</th><th scope="col">상세</th></tr></thead>
                <tbody><?php foreach ($orders as $order) : ?>
                    <tr>
                        <td data-label="주문번호">#<?php echo esc_html($order->get_order_number()); ?></td>
                        <td data-label="주문일"><?php echo esc_html($order->get_date_created() ? wc_format_datetime($order->get_date_created(), 'Y-m-d') : ''); ?></td>
                        <td data-label="상태"><?php echo esc_html(wc_get_order_status_name($order->get_status())); ?></td>
                        <td data-label="결제금액"><?php echo wp_kses_post($order->get_formatted_order_total()); ?></td>
                        <td data-label="상세"><a href="<?php echo esc_url($order->get_view_order_url()); ?>">주문 보기</a></td>
                    </tr>
                <?php endforeach; ?></tbody>
            </table></div>
        <?php else : ?>
            <p class="aicc-no-orders">아직 주문내역이 없습니다. 마음에 드는 상품을 찾아보세요.</p>
        <?php endif; ?>
    </section>

    <section class="aicc-dashboard-profile" aria-labelledby="aicc-dashboard-profile-title">
        <p class="aicc-dialog-eyebrow">MY INFORMATION</p><h2 id="aicc-dashboard-profile-title">내 정보</h2>
        <p><?php echo esc_html($current_user->display_name); ?> · <?php echo esc_html($current_user->user_email); ?></p>
        <div class="aicc-dashboard-links">
            <a class="aicc-account-button" href="<?php echo esc_url(wc_get_endpoint_url('edit-account', '', wc_get_page_permalink('myaccount'))); ?>">내 정보 수정</a>
            <a class="aicc-account-button" href="<?php echo esc_url(wc_get_endpoint_url('edit-address', '', wc_get_page_permalink('myaccount'))); ?>">배송지 수정</a>
        </div>
    </section>

    <section class="aicc-dashboard-withdraw" aria-labelledby="aicc-withdraw-title">
        <h2 id="aicc-withdraw-title">회원 탈퇴</h2>
        <p>탈퇴하면 계정에 다시 로그인할 수 없습니다. 이미 접수된 주문 기록은 관련 처리에 필요한 기간 동안 보관될 수 있습니다.</p>
        <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" data-aicc-confirm="정말 회원 탈퇴하시겠습니까? 탈퇴 후에는 계정에 로그인할 수 없습니다.">
            <input type="hidden" name="action" value="aicc_delete_account">
            <?php wp_nonce_field('aicc_delete_account'); ?>
            <button class="aicc-withdraw-button" type="submit">회원 탈퇴</button>
        </form>
    </section>
</div>
