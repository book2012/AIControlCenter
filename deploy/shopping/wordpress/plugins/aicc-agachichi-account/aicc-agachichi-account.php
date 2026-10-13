<?php
/**
 * Plugin Name: AICC Agachichi Account
 * Description: DEV WooCommerce account presentation, verified-phone registration, and profile fields.
 * Version: 0.1.0
 * Requires PHP: 8.1
 */
if (!defined('ABSPATH')) { exit; }

final class AICC_Agachichi_Account {
    private static ?string $verified_phone = null;
    private const VERIFY_URL = 'http://host.docker.internal:18445/__order-dev/account/registration-ticket/consume';

    public static function boot(): void {
        if (strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST)) !== 'dev.bokstory.duckdns.org') { return; }
        add_action('wp_enqueue_scripts', [self::class, 'assets']);
        add_action('woocommerce_register_form_start', [self::class, 'fields']);
        add_filter('woocommerce_registration_errors', [self::class, 'validate'], 99, 3);
        add_action('woocommerce_created_customer', [self::class, 'save'], 10, 1);
        add_action('woocommerce_before_customer_login_form', [self::class, 'intro']);
    }

    public static function assets(): void {
        if (!function_exists('is_account_page') || !is_account_page()) { return; }
        $base = plugin_dir_url(__FILE__);
        wp_enqueue_style('aicc-agachichi-account', $base . 'assets/account.css', [], '0.1.0');
        wp_enqueue_script('aicc-agachichi-account', $base . 'assets/account.js', [], '0.1.0', true);
    }

    public static function intro(): void {
        echo '<div class="aicc-account-intro"><a href="/" class="aicc-account-brand">agachichi</a><p>Everyday Comfort, Playful Touch</p></div>';
    }

    public static function fields(): void {
        wp_nonce_field('aicc_signup', 'aicc_signup_nonce');
        echo '<fieldset class="aicc-signup-fields"><legend>간단 회원가입</legend>';
        self::input('aicc_full_name', '이름', 'text', true, '홍길동', 'autocomplete="name"');
        self::input('aicc_nickname', '닉네임', 'text', true, '사용할 닉네임', 'autocomplete="nickname"');
        self::input('aicc_phone', '휴대폰 번호', 'tel', true, '01012345678', 'autocomplete="tel"');
        echo '<div class="aicc-phone-actions"><button type="button" class="aicc-account-button" id="aicc-send-code">인증번호 받기</button><span id="aicc-phone-status" role="status" aria-live="polite"></span></div>';
        echo '<label class="aicc-account-label" for="aicc_phone_code">인증번호</label><div class="aicc-phone-actions"><input id="aicc_phone_code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="10"><button type="button" class="aicc-account-button" id="aicc-check-code">인증 확인</button></div>';
        echo '<label class="aicc-account-consent"><input type="checkbox" id="aicc-phone-consent"><span>회원가입을 위한 휴대폰 본인 확인에 동의합니다.</span></label>';
        echo '<input type="hidden" name="aicc_phone_ticket" id="aicc_phone_ticket" value="">';
        self::input('aicc_address', '집 주소', 'text', true, '도로명 주소', 'autocomplete="street-address"');
        self::input('aicc_address_detail', '상세 주소', 'text', false, '동·호수 등', 'autocomplete="address-line2"');
        echo '<p class="aicc-account-hint">이메일과 비밀번호는 아래 입력란을 사용해 주세요.</p></fieldset>';
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
        if ($name === '' || $nickname === '' || $phone === '' || $address === '') {
            $errors->add('aicc_signup_fields', '이름, 닉네임, 휴대폰 번호, 집 주소를 입력해 주세요.');
            return $errors;
        }
        if (!preg_match('/^[A-Za-z0-9_-]{43}$/', $ticket)) {
            $errors->add('aicc_signup_phone', '회원가입 전에 휴대폰 인증을 완료해 주세요.');
            return $errors;
        }
        $response = wp_remote_post(self::VERIFY_URL, [
            'timeout' => 8,
            'redirection' => 0,
            'headers' => ['Content-Type' => 'application/json', 'Cache-Control' => 'no-store'],
            'body' => wp_json_encode(['ticket' => $ticket, 'phone' => $phone]),
        ]);
        if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
            $errors->add('aicc_signup_phone', '휴대폰 인증을 확인하지 못했습니다. 인증을 다시 진행해 주세요.');
            return $errors;
        }
        $result = json_decode(wp_remote_retrieve_body($response), true);
        if (!is_array($result) || ($result['verified'] ?? false) !== true || !isset($result['phone'])) {
            $errors->add('aicc_signup_phone', '휴대폰 인증을 확인하지 못했습니다. 인증을 다시 진행해 주세요.');
            return $errors;
        }
        self::$verified_phone = sanitize_text_field($result['phone']);
        return $errors;
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
        update_user_meta($customer_id, 'billing_phone', self::$verified_phone);
        update_user_meta($customer_id, 'billing_address_1', $address);
        update_user_meta($customer_id, 'billing_address_2', $detail);
        update_user_meta($customer_id, 'shipping_first_name', $name);
        update_user_meta($customer_id, 'shipping_address_1', $address);
        update_user_meta($customer_id, 'shipping_address_2', $detail);
    }
}
AICC_Agachichi_Account::boot();
