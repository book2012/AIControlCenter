<?php
/**
 * Plugin Name: AICC Agachichi Account
 * Description: DEV WooCommerce account presentation, verified-phone registration, and profile fields.
 * Version: 0.6.7
 * Requires PHP: 8.1
 */
if (!defined('ABSPATH')) { exit; }

final class AICC_Agachichi_Account {
    private static ?string $verified_phone = null;
    private static bool $unknown_login = false;
    private const REGISTRATION_PUBLIC_KEY = 'OYh42Nj3arnQL3oqfcX_-oKRVK_SktTxnyPvXWX4G8c';
    private const REGISTRATION_AUDIENCE = 'dev.bokstory.duckdns.org/aicc-account-registration';

    public static function boot(): void {
        if (strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST)) !== 'dev.bokstory.duckdns.org') { return; }
        add_action('init', [self::class, 'ensure_pages'], 20);
        add_action('wp_enqueue_scripts', [self::class, 'assets']);
        add_action('wp_ajax_aicc_account_navigation', [self::class, 'account_navigation']);
        add_action('wp_ajax_nopriv_aicc_account_navigation', [self::class, 'account_navigation']);
        add_action('wp_ajax_aicc_check_username', [self::class, 'check_username']);
        add_action('wp_ajax_nopriv_aicc_check_username', [self::class, 'check_username']);
        add_action('wp_ajax_aicc_checkout_profile', [self::class, 'checkout_profile']);
        add_action('admin_post_aicc_delete_account', [self::class, 'delete_account']);
        add_filter('woocommerce_locate_template', [self::class, 'account_template'], 20, 3);
        add_filter('gettext_woocommerce', [self::class, 'translate_orders_empty_state'], 10, 3);
        add_filter('woocommerce_account_menu_items', [self::class, 'account_menu_items']);
        add_filter('body_class', [self::class, 'body_classes']);
        add_action('wp_body_open', [self::class, 'storefront_header'], 5);
        add_action('wp_footer', [self::class, 'storefront_footer'], 5);
        add_shortcode('aicc_agachichi_register', [self::class, 'registration_page']);
        add_shortcode('aicc_agachichi_signup_complete', [self::class, 'signup_complete_page']);
        add_filter('woocommerce_registration_errors', [self::class, 'validate'], 99, 3);
        add_action('woocommerce_created_customer', [self::class, 'save'], 10, 1);
        add_action('woocommerce_before_customer_login_form', [self::class, 'intro']);
        add_action('woocommerce_login_form_end', [self::class, 'login_signup_link']);
        add_action('woocommerce_login_form', [self::class, 'login_return_field']);
        add_filter('woocommerce_login_redirect', [self::class, 'login_redirect'], 10, 2);
        add_action('woocommerce_login_failed', [self::class, 'login_failed']);
    }

    public static function storefront_header(): void {
        $account_page = function_exists('is_account_page') && is_account_page();
        $is_registration = is_page('register');
        $is_signup_complete = is_page('signup-complete');
        if (!$account_page && !$is_registration && !$is_signup_complete) { return; }
        $logged_in = is_user_logged_in();
        $is_login = $account_page && !$logged_in && !$is_registration;
        $login_state = $is_login ? ' class="header-login is-active" aria-current="page"' : ' class="header-login"';
        $account_link = $logged_in
            ? '<a class="header-orders" href="/my-account/orders/">주문내역</a><a class="header-profile" href="/my-account/">내 정보</a>'
            : '<a class="header-orders" href="/homepage/storefront/my-orders" aria-label="비회원 주문 조회">비회원 주문 조회</a>';
        $auth_link = $logged_in
            ? '<a class="header-logout" href="' . esc_url(wp_logout_url(home_url('/homepage/storefront/'))) . '" data-aicc-confirm="로그아웃하시겠습니까?" aria-label="로그아웃">LOG OUT</a>'
            : '<a' . $login_state . ' href="/my-account/" aria-label="로그인">LOGIN</a>';
        echo '<header class="store-header aicc-account-store-header"><a class="wordmark" href="/homepage/storefront/">agachichi<span>Everyday Comfort, Playful Touch</span></a><nav class="header-actions" aria-label="주요 메뉴"><a class="header-search" href="/homepage/storefront/search">검색</a>' . $auth_link . '<a class="header-cart" href="/homepage/storefront/cart">장바구니</a>' . $account_link . '</nav></header>';
    }

    public static function storefront_footer(): void {
        $account_page = function_exists('is_account_page') && is_account_page();
        if (!$account_page && !is_page('register') && !is_page('signup-complete')) { return; }
        echo '<footer class="aicc-account-store-footer"><a class="wordmark" href="' . esc_url(home_url('/homepage/storefront/')) . '">agachichi</a><p>Everyday Comfort, Playful Touch</p></footer>';
    }

    public static function translate_orders_empty_state(string $translation, string $text, string $domain): string {
        if (!function_exists('is_account_page') || !is_account_page()
            || !function_exists('is_wc_endpoint_url') || !is_wc_endpoint_url('orders')) { return $translation; }
        return match ($text) {
            'No order has been made yet.' => '아직 주문내역이 없습니다.',
            'Browse products' => '상품 둘러보기',
            default => $translation,
        };
    }

    public static function body_classes(array $classes): array {
        if (is_page('register') || is_page('signup-complete')) { $classes[] = 'woocommerce-account'; }
        if (function_exists('is_account_page') && is_account_page() && is_user_logged_in()
            && function_exists('is_wc_endpoint_url')) {
            if (!is_wc_endpoint_url()) { $classes[] = 'aicc-account-dashboard-view'; }
            if (is_wc_endpoint_url('orders')) { $classes[] = 'aicc-account-orders-view'; }
        }
        return $classes;
    }

    public static function assets(): void {
        $account_page = function_exists('is_account_page') && is_account_page();
        if (!$account_page && !is_page('register') && !is_page('signup-complete')) { return; }
        $base = plugin_dir_url(__FILE__);
        wp_enqueue_style('aicc-agachichi-account', $base . 'assets/account.css', [], '0.6.7');
        wp_enqueue_script('aicc-agachichi-account', $base . 'assets/account.js', [], '0.6.7', true);
        wp_localize_script('aicc-agachichi-account', 'AICCAccountConfig', [
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'usernameNonce' => wp_create_nonce('aicc_check_username'),
        ]);
    }

    public static function account_navigation(): void {
        nocache_headers();
        $authenticated = is_user_logged_in();
        wp_send_json_success([
            'authenticated' => $authenticated,
            'logoutUrl' => $authenticated ? wp_logout_url(home_url('/homepage/storefront/')) : '',
        ]);
    }

    public static function account_template(string $template, string $template_name, string $template_path): string {
        if ($template_name !== 'myaccount/dashboard.php' || !is_user_logged_in()) { return $template; }
        $custom = plugin_dir_path(__FILE__) . 'templates/myaccount/dashboard.php';
        return is_file($custom) ? $custom : $template;
    }

    public static function account_menu_items(array $items): array {
        $labels = [
            'dashboard' => '내 정보',
            'orders' => '주문내역',
            'edit-account' => '내 정보 수정',
            'edit-address' => '배송지 관리',
        ];
        return array_intersect_key($labels, $items);
    }

    public static function delete_account(): void {
        if (!is_user_logged_in()) { wp_safe_redirect(wc_get_page_permalink('myaccount')); exit; }
        check_admin_referer('aicc_delete_account');
        $user_id = get_current_user_id();
        $user = get_userdata($user_id);
        if (!$user || !in_array('customer', (array) $user->roles, true) || user_can($user, 'manage_options')) {
            wp_safe_redirect(add_query_arg('account_error', 'not-eligible', wc_get_page_permalink('myaccount')));
            exit;
        }
        $customer = new WC_Customer($user_id);
        if (!$customer->delete_and_reassign(0)) {
            wp_safe_redirect(add_query_arg('account_error', 'delete-failed', wc_get_page_permalink('myaccount')));
            exit;
        }
        wp_logout();
        wp_safe_redirect(home_url('/homepage/storefront/?account=deleted'));
        exit;
    }

    public static function check_username(): void {
        check_ajax_referer('aicc_check_username', 'nonce');
        $raw_username = sanitize_text_field(wp_unslash($_POST['username'] ?? ''));
        $username = sanitize_user($raw_username, true);
        if ($username !== $raw_username || !preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{3,19}$/', $username)) {
            wp_send_json_success(['available' => false, 'message' => '아이디는 영문 또는 숫자로 시작하는 4~20자로 입력해 주세요.']);
        }
        if (username_exists($username)) {
            wp_send_json_success(['available' => false, 'message' => '이미 사용 중인 아이디입니다.']);
        }
        wp_send_json_success(['available' => true, 'message' => '사용할 수 있는 아이디입니다.']);
    }

    public static function checkout_profile(): void {
        nocache_headers();
        if (!is_user_logged_in()) {
            wp_send_json_error(['message' => 'LOGIN_REQUIRED'], 401);
        }
        $customer_id = get_current_user_id();
        $name = get_user_meta($customer_id, 'billing_first_name', true);
        if (!is_string($name) || $name === '') { $name = get_user_meta($customer_id, 'first_name', true); }
        $phone = self::canonical_phone((string) get_user_meta($customer_id, 'billing_phone', true));
        $postcode = preg_replace('/\\D+/', '', (string) get_user_meta($customer_id, 'shipping_postcode', true));
        if (!is_string($postcode) || strlen($postcode) !== 5) { $postcode = ''; }
        wp_send_json_success([
            'recipient' => sanitize_text_field((string) $name),
            'phone' => $phone,
            'postcode' => $postcode,
            'address1' => sanitize_text_field((string) get_user_meta($customer_id, 'shipping_address_1', true)),
            'address2' => sanitize_text_field((string) get_user_meta($customer_id, 'shipping_address_2', true)),
        ]);
    }

    public static function intro(): void {
        if (self::$unknown_login) {
            echo '<dialog class="aicc-signup-dialog" id="aicc-signup-dialog" aria-labelledby="aicc-signup-dialog-title"><button type="button" class="aicc-dialog-close" aria-label="닫기">×</button><p class="aicc-dialog-eyebrow">AGACHICHI MEMBERSHIP</p><h2 id="aicc-signup-dialog-title">아직 회원이 아니신가요?</h2><p>간단한 정보와 휴대폰 인증으로 회원가입을 시작할 수 있어요.</p><div class="aicc-dialog-actions"><a class="aicc-account-button" href="' . esc_url(self::registration_url()) . '">회원가입하기</a><button type="button" class="aicc-dialog-later">나중에</button></div></dialog>';
        }
    }

    public static function registration_url(): string {
        return trailingslashit(wc_get_page_permalink('myaccount')) . 'register/';
    }

    public static function login_return_field(): void {
        $return = sanitize_text_field(wp_unslash($_GET['redirect'] ?? ''));
        if (wp_parse_url($return, PHP_URL_PATH) === '/homepage/storefront/checkout') {
            echo '<input type="hidden" name="aicc_checkout_return" value="/homepage/storefront/checkout">';
        }
    }

    public static function login_redirect(string $redirect, $user): string {
        $return = sanitize_text_field(wp_unslash($_POST['aicc_checkout_return'] ?? ''));
        if ($return === '/homepage/storefront/checkout') { return home_url($return); }
        return $redirect;
    }

    public static function login_signup_link(): void {
        echo '<p class="aicc-login-signup">아직 회원이 아니신가요? <a href="' . esc_url(self::registration_url()) . '">회원가입</a></p><p class="aicc-guest-order-link"><a href="/homepage/storefront/my-orders">비회원 주문 조회 · 휴대폰 인증</a></p>';
    }

    public static function login_failed(): void {
        $identity = sanitize_text_field(wp_unslash($_POST['username'] ?? ''));
        if ($identity === '') { return; }
        $user = is_email($identity) ? get_user_by('email', $identity) : get_user_by('login', $identity);
        self::$unknown_login = !$user;
    }

    public static function registration_page(): string {
        if (is_user_logged_in()) {
            return '<div class="woocommerce"><p class="woocommerce-info">이미 로그인되어 있습니다. <a href="' . esc_url(wc_get_page_permalink('myaccount')) . '">내 계정으로 이동</a></p></div>';
        }
        if (isset($_POST['aicc_registration_submit'])) {
            $nonce = sanitize_text_field(wp_unslash($_POST['aicc_registration_nonce'] ?? ''));
            if (!wp_verify_nonce($nonce, 'aicc_registration')) {
                wc_add_notice('회원가입 요청을 확인할 수 없습니다. 페이지를 새로고침해 주세요.', 'error');
            } else {
                $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
                $raw_username = sanitize_text_field(wp_unslash($_POST['username'] ?? ''));
                $username = sanitize_user($raw_username, true);
                $username_valid = true;
                if ($username !== $raw_username || !preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]{3,19}$/', $username)) {
                    wc_add_notice('아이디는 영문 또는 숫자로 시작하는 4~20자의 영문, 숫자, 점, 밑줄, 하이픈으로 입력해 주세요.', 'error');
                    $username_valid = false;
                } elseif (username_exists($username)) {
                    wc_add_notice('이미 사용 중인 아이디입니다. 다른 아이디를 입력해 주세요.', 'error');
                    $username_valid = false;
                }
                $password = (string) ($_POST['password'] ?? '');
                $confirm = (string) ($_POST['password_confirm'] ?? '');
                if (!$username_valid) {
                    // Keep the submitted form visible with its existing validation notices.
                } elseif ($password !== $confirm) {
                    wc_add_notice('비밀번호가 서로 일치하지 않습니다.', 'error');
                } elseif (strlen($password) < 8) {
                    wc_add_notice('비밀번호는 8자 이상 입력해 주세요.', 'error');
                } else {
                    $name = sanitize_text_field(wp_unslash($_POST['aicc_full_name'] ?? ''));
                    $nickname = sanitize_text_field(wp_unslash($_POST['aicc_nickname'] ?? ''));
                    $customer_id = wc_create_new_customer($email, $username, $password, [
                        'first_name' => $name,
                        'display_name' => $nickname,
                    ]);
                    if (is_wp_error($customer_id)) {
                        foreach ($customer_id->get_error_messages() as $message) { wc_add_notice($message, 'error'); }
                    } else {
                        wc_set_customer_auth_cookie($customer_id);
                        wp_safe_redirect(self::signup_complete_url());
                        exit;
                    }
                }
            }
        }
        ob_start();
        echo '<div class="woocommerce aicc-register-page"><header class="aicc-register-heading"><p class="aicc-dialog-eyebrow">AGACHICHI MEMBERSHIP</p><h1>회원가입</h1></header>';
        wc_print_notices();
        echo '<form method="post" class="register aicc-registration-form">';
        wp_nonce_field('aicc_registration', 'aicc_registration_nonce');
        self::fields();
        echo '<p class="aicc-account-hint">비밀번호는 8자 이상 입력해 주세요.</p><button class="aicc-account-button aicc-register-submit" type="submit" name="aicc_registration_submit" value="1">회원가입</button></form><p class="aicc-register-login">이미 회원이신가요? <a href="' . esc_url(wc_get_page_permalink('myaccount')) . '">로그인</a></p></div>';
        return (string) ob_get_clean();
    }

    public static function signup_complete_url(): string {
        return trailingslashit(wc_get_page_permalink('myaccount')) . 'signup-complete/';
    }

    public static function signup_complete_page(): string {
        if (!is_user_logged_in()) {
            return '<div class="woocommerce aicc-signup-complete"><p>가입 완료 정보를 확인할 수 없습니다. <a href="' . esc_url(wc_get_page_permalink('myaccount')) . '">로그인</a>해 주세요.</p></div>';
        }
        $user = wp_get_current_user();
        $products = do_shortcode('[products limit="4" columns="2" orderby="date" order="DESC"]');
        if (trim(wp_strip_all_tags($products)) === '') {
            $products = '<p class="aicc-recommend-empty">새로운 상품을 준비하고 있어요. <a href="/homepage/storefront/search">상품 둘러보기</a></p>';
        }
        return '<section class="woocommerce aicc-signup-complete" aria-labelledby="aicc-signup-complete-title">'
            . '<p class="aicc-dialog-eyebrow">AGACHICHI MEMBERSHIP</p>'
            . '<h1 id="aicc-signup-complete-title">회원가입을 축하합니다!</h1>'
            . '<p class="aicc-signup-complete-copy">아가치치의 회원이 되신 것을 환영합니다.</p>'
            . '<p class="aicc-signup-id">가입 아이디 <strong>' . esc_html($user->user_login) . '</strong></p>'
            . '<a class="aicc-account-button aicc-home-button" href="/homepage/storefront/">홈으로 가기</a>'
            . '<section class="aicc-recommendations" aria-labelledby="aicc-recommendations-title"><h2 id="aicc-recommendations-title">회원님을 위한 추천 상품</h2>' . $products . '</section>'
            . '</section>';
    }

    public static function ensure_pages(): void {
        if (strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST)) !== 'dev.bokstory.duckdns.org') { return; }
        $parent_id = function_exists('wc_get_page_id') ? (int) wc_get_page_id('myaccount') : 0;
        if ($parent_id < 1) { return; }
        $pages = [
            ['register', '회원가입', '[aicc_agachichi_register]'],
            ['signup-complete', '가입 완료', '[aicc_agachichi_signup_complete]'],
        ];
        foreach ($pages as [$slug, $title, $content]) {
            $existing = get_posts([
                'post_type' => 'page', 'post_parent' => $parent_id, 'name' => $slug,
                'post_status' => 'publish', 'numberposts' => 1,
            ]);
            if ($existing) { continue; }
            wp_insert_post([
                'post_title' => $title,
                'post_name' => $slug,
                'post_parent' => $parent_id,
                'post_content' => $content,
                'post_status' => 'publish',
                'post_type' => 'page',
            ]);
        }
    }

    public static function activate(): void {
        self::ensure_pages();
    }

    public static function fields(): void {
        wp_nonce_field('aicc_signup', 'aicc_signup_nonce');
        echo '<fieldset class="aicc-signup-fields"><legend class="aicc-visually-hidden">회원 정보</legend>';
        echo '<label class="aicc-account-label" for="aicc_signup_username">아이디 <span aria-hidden="true">*</span></label><div class="aicc-username-row"><input class="aicc-account-input" id="aicc_signup_username" name="username" type="text" autocomplete="username" minlength="4" maxlength="20" pattern="[A-Za-z0-9][A-Za-z0-9._-]{3,19}" required placeholder="영문·숫자 4~20자" value="' . esc_attr(sanitize_user(wp_unslash($_POST['username'] ?? ''), true)) . '" aria-describedby="aicc-username-status"><button type="button" class="aicc-account-button" id="aicc-check-username">중복 확인</button></div><span id="aicc-username-status" role="status" aria-live="polite"></span>';
        echo '<label class="aicc-account-label" for="aicc_signup_email">이메일 주소 <span aria-hidden="true">*</span></label><input class="aicc-account-input" id="aicc_signup_email" name="email" type="email" autocomplete="email" required maxlength="190">';
        echo '<label class="aicc-account-label" for="aicc_signup_password">비밀번호 <span aria-hidden="true">*</span></label><input class="aicc-account-input" id="aicc_signup_password" name="password" type="password" autocomplete="new-password" minlength="8" required>';
        echo '<label class="aicc-account-label" for="aicc_signup_password_confirm">비밀번호 확인 <span aria-hidden="true">*</span></label><input class="aicc-account-input" id="aicc_signup_password_confirm" name="password_confirm" type="password" autocomplete="new-password" minlength="8" required aria-describedby="aicc-password-status"><span id="aicc-password-status" role="status" aria-live="polite"></span>';
        self::input('aicc_full_name', '이름', 'text', true, '홍길동', 'autocomplete="name"');
        self::input('aicc_nickname', '닉네임', 'text', true, '사용할 닉네임', 'autocomplete="nickname"');
        self::input('aicc_phone', '휴대폰 번호', 'tel', true, '01012345678', 'autocomplete="tel"');
        echo '<div class="aicc-phone-actions"><button type="button" class="aicc-account-button" id="aicc-send-code">인증번호 받기</button><span id="aicc-phone-status" role="status" aria-live="polite"></span></div>';
        echo '<label class="aicc-account-label" for="aicc_phone_code">인증번호</label><div class="aicc-phone-actions"><input id="aicc_phone_code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="10"><button type="button" class="aicc-account-button" id="aicc-check-code">인증 확인</button></div>';
        echo '<label class="aicc-account-consent"><input type="checkbox" id="aicc-phone-consent"><span>회원가입을 위한 휴대폰 본인 확인에 동의합니다.</span></label>';
        echo '<input type="hidden" name="aicc_phone_ticket" id="aicc_phone_ticket" value="">';
        echo '<label class="aicc-account-label" for="aicc_postcode">우편번호 <span aria-hidden="true">*</span></label><div class="aicc-address-row"><input class="aicc-account-input" id="aicc_postcode" name="aicc_postcode" type="text" inputmode="numeric" autocomplete="postal-code" placeholder="주소 검색으로 입력" readonly required><button type="button" class="aicc-account-button" id="aicc-address-search">주소 검색</button></div>';
        self::input('aicc_address', '집 주소', 'text', true, '도로명 주소', 'autocomplete="street-address" readonly');
        self::input('aicc_address_detail', '상세 주소', 'text', false, '동·호수 등', 'autocomplete="address-line2"');
        echo '<dialog class="aicc-postcode-dialog" id="aicc-postcode-dialog" aria-labelledby="aicc-postcode-title"><div class="aicc-postcode-head"><h2 id="aicc-postcode-title">주소 검색</h2><button type="button" id="aicc-address-close" aria-label="주소 검색 닫기">×</button></div><div id="aicc-postcode-frame"></div></dialog>';
        echo '<p class="aicc-account-hint">휴대폰 인증을 완료한 뒤 이메일과 비밀번호를 입력해 주세요.</p></fieldset>';
    }

    private static function input(string $name, string $label, string $type, bool $required, string $placeholder, string $autocomplete): void {
        $id = esc_attr($name);
        echo '<label class="aicc-account-label" for="' . $id . '">' . esc_html($label) . ($required ? ' <span aria-hidden="true">*</span>' : '') . '</label>';
        echo '<input class="aicc-account-input" id="' . $id . '" name="' . $id . '" type="' . esc_attr($type) . '" placeholder="' . esc_attr($placeholder) . '" ' . $autocomplete . ($required ? ' required' : '') . ' maxlength="190">';
    }

    public static function validate($errors, $username, $email) {
        if (!isset($_POST['aicc_signup_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['aicc_signup_nonce'])), 'aicc_signup')) {
            $errors->add('aicc_signup_nonce', '회원가입 요청을 확인할 수 없습니다. 페이지를 새로고침해 주세요.');
            return $errors;
        }
        if ($errors->get_error_codes()) { return $errors; }
        $name = sanitize_text_field(wp_unslash($_POST['aicc_full_name'] ?? ''));
        $nickname = sanitize_text_field(wp_unslash($_POST['aicc_nickname'] ?? ''));
        $phone = sanitize_text_field(wp_unslash($_POST['aicc_phone'] ?? ''));
        $address = sanitize_text_field(wp_unslash($_POST['aicc_address'] ?? ''));
        $ticket = sanitize_text_field(wp_unslash($_POST['aicc_phone_ticket'] ?? ''));
        $postcode = preg_replace('/\\D+/', '', sanitize_text_field(wp_unslash($_POST['aicc_postcode'] ?? '')));
        if ($name === '' || $nickname === '' || $phone === '' || $address === '' || !preg_match('/^[0-9]{5}$/', (string) $postcode)) {
            $errors->add('aicc_signup_fields', '이름, 닉네임, 휴대폰 번호, 집 주소를 입력해 주세요.');
            return $errors;
        }
        if (strlen($ticket) > 512 || !preg_match('/^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$/', $ticket)) {
            $errors->add('aicc_signup_phone', '회원가입 전에 휴대폰 인증을 완료해 주세요.');
            return $errors;
        }
        $claims = self::verified_ticket($ticket, $phone);
        if ($claims === null) {
            $errors->add('aicc_signup_phone', '휴대폰 인증을 확인하지 못했습니다. 인증을 다시 진행해 주세요.');
            return $errors;
        }
        self::prune_used_tickets();
        $option = 'aicc_dev_signup_ticket_' . $claims['nonce'];
        if (!add_option($option, (string) $claims['exp'], '', false)) {
            $errors->add('aicc_signup_phone', '이미 사용한 인증입니다. 휴대폰 인증을 다시 진행해 주세요.');
            return $errors;
        }
        self::$verified_phone = $claims['phone'];
        return $errors;
    }

    private static function verified_ticket(string $ticket, string $phone): ?array {
        if (strlen($ticket) > 512 || !preg_match('/^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$/', $ticket)) { return null; }
        [$encoded, $signed] = explode('.', $ticket, 2);
        $decode = static function (string $value): string|false {
            $padded = strtr($value, '-_', '+/') . str_repeat('=', (4 - strlen($value) % 4) % 4);
            return base64_decode($padded, true);
        };
        $payload = $decode($encoded);
        $signature = $decode($signed);
        $public = $decode(self::REGISTRATION_PUBLIC_KEY);
        if (!is_string($payload) || !is_string($signature) || !is_string($public)
            || strlen($signature) !== SODIUM_CRYPTO_SIGN_BYTES
            || strlen($public) !== SODIUM_CRYPTO_SIGN_PUBLICKEYBYTES
            || !sodium_crypto_sign_verify_detached($signature, $payload, $public)) { return null; }
        $claims = json_decode($payload, true);
        if (!is_array($claims) || ($claims['v'] ?? null) !== 1
            || ($claims['aud'] ?? null) !== self::REGISTRATION_AUDIENCE
            || !is_int($claims['exp'] ?? null) || $claims['exp'] <= time() || $claims['exp'] > time() + 360
            || !is_string($claims['nonce'] ?? null) || !preg_match('/^[A-Za-z0-9_-]{22}$/', $claims['nonce'])
            || !is_string($claims['phone'] ?? null)) { return null; }
        $submitted = self::canonical_phone($phone);
        if ($submitted === '' || !hash_equals($claims['phone'], $submitted)) { return null; }
        return $claims;
    }

    private static function canonical_phone(string $phone): string {
        $trimmed = trim($phone);
        $digits = preg_replace('/\\D+/', '', $trimmed);
        if (!is_string($digits)) { return ''; }
        if (str_starts_with($trimmed, '+')) { $canonical = '+' . $digits; }
        elseif (str_starts_with($digits, '82')) { $canonical = '+' . $digits; }
        elseif (str_starts_with($digits, '0')) { $canonical = '+82' . substr($digits, 1); }
        else { return ''; }
        return preg_match('/^\\+8210[0-9]{8}$/', $canonical) ? $canonical : '';
    }

    private static function prune_used_tickets(): void {
        global $wpdb;
        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s AND CAST(option_value AS UNSIGNED) < %d",
            $wpdb->esc_like('aicc_dev_signup_ticket_') . '%', time() - 3600
        ));
    }

    public static function save(int $customer_id): void {
        if (self::$verified_phone === null) { return; }
        $name = sanitize_text_field(wp_unslash($_POST['aicc_full_name'] ?? ''));
        $nickname = sanitize_text_field(wp_unslash($_POST['aicc_nickname'] ?? ''));
        $address = sanitize_text_field(wp_unslash($_POST['aicc_address'] ?? ''));
        $detail = sanitize_text_field(wp_unslash($_POST['aicc_address_detail'] ?? ''));
        update_user_meta($customer_id, 'first_name', $name);
        update_user_meta($customer_id, 'billing_first_name', $name);
        update_user_meta($customer_id, 'nickname', $nickname);
        wp_update_user(['ID' => $customer_id, 'display_name' => $nickname]);
        update_user_meta($customer_id, 'billing_phone', self::$verified_phone);
        $postcode = preg_replace('/\\D+/', '', sanitize_text_field(wp_unslash($_POST['aicc_postcode'] ?? '')));
        update_user_meta($customer_id, 'billing_postcode', $postcode);
        update_user_meta($customer_id, 'shipping_postcode', $postcode);
        update_user_meta($customer_id, 'billing_address_1', $address);
        update_user_meta($customer_id, 'billing_address_2', $detail);
        update_user_meta($customer_id, 'shipping_first_name', $name);
        update_user_meta($customer_id, 'shipping_address_1', $address);
        update_user_meta($customer_id, 'shipping_address_2', $detail);
    }
}
register_activation_hook(__FILE__, [AICC_Agachichi_Account::class, 'activate']);
AICC_Agachichi_Account::boot();
