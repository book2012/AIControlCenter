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
    private const REGISTRATION_PUBLIC_KEY = 'OYh42Nj3arnQL3oqfcX_-oKRVK_SktTxnyPvXWX4G8c';
    private const REGISTRATION_AUDIENCE = 'dev.bokstory.duckdns.org/aicc-account-registration';

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
        update_user_meta($customer_id, 'billing_phone', self::$verified_phone);
        update_user_meta($customer_id, 'billing_address_1', $address);
        update_user_meta($customer_id, 'billing_address_2', $detail);
        update_user_meta($customer_id, 'shipping_first_name', $name);
        update_user_meta($customer_id, 'shipping_address_1', $address);
        update_user_meta($customer_id, 'shipping_address_2', $detail);
    }
}
AICC_Agachichi_Account::boot();
