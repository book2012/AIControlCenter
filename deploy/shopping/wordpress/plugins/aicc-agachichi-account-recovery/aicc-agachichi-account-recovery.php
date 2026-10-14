<?php
/**
 * Plugin Name: AIControlCenter Agachichi Account Recovery Bridge
 * Description: DEV-only, narrowly scoped account identity and password adapter.
 * Version: 0.1.0
 */
if (!defined('ABSPATH')) { exit; }

const AICC_RECOVERY_ROLE = 'aicc_recovery_service';
const AICC_RECOVERY_CAP = 'aicc_manage_account_recovery';
const AICC_RECOVERY_NAMESPACE = 'aicc-account-recovery/v1';

function aicc_recovery_is_dev(): bool {
    return strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST)) === 'dev.bokstory.duckdns.org';
}

function aicc_recovery_activate(): void {
    if (!aicc_recovery_is_dev()) { return; }
    $role = get_role(AICC_RECOVERY_ROLE);
    if (!$role) {
        add_role(AICC_RECOVERY_ROLE, 'AIControlCenter Account Recovery Service', array(
            AICC_RECOVERY_CAP => true,
        ));
        return;
    }
    $role->add_cap(AICC_RECOVERY_CAP);
}
register_activation_hook(__FILE__, 'aicc_recovery_activate');

function aicc_recovery_allow_application_password($available, $user): bool {
    if (!aicc_recovery_is_dev() || !($user instanceof WP_User)) {
        return (bool) $available;
    }
    if (in_array(AICC_RECOVERY_ROLE, (array) $user->roles, true)) {
        return true;
    }
    return (bool) $available;
}
add_filter('wp_is_application_passwords_available_for_user', 'aicc_recovery_allow_application_password', 10, 2);

function aicc_recovery_denied() {
    return new WP_Error('aicc_recovery_denied', 'Account recovery bridge unavailable.', array('status' => 403));
}

function aicc_recovery_permission($request) {
    if (!aicc_recovery_is_dev() || $request->get_method() !== 'POST') {
        return aicc_recovery_denied();
    }
    $user = wp_get_current_user();
    if (!($user instanceof WP_User)
        || !in_array(AICC_RECOVERY_ROLE, (array) $user->roles, true)
        || !current_user_can(AICC_RECOVERY_CAP)) {
        return aicc_recovery_denied();
    }
    if (strlen((string) $request->get_body()) > 4096) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 413));
    }
    return true;
}

function aicc_recovery_input($request, array $required) {
    $content_type = strtolower((string) $request->get_header('content-type'));
    if (strpos($content_type, 'application/json') !== 0) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    $data = $request->get_json_params();
    if (!is_array($data) || array_diff(array_keys($data), $required)
        || array_diff($required, array_keys($data))) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    foreach ($data as $value) {
        if (!is_string($value) || preg_match('//u', $value) !== 1 || strlen($value) > 1024
            || preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $value) === 1) {
            return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
        }
    }
    return $data;
}

function aicc_recovery_valid_phone($phone): bool {
    return is_string($phone) && preg_match('/\A\+8210[0-9]{8}\z/D', $phone) === 1;
}

function aicc_recovery_customer($user): bool {
    return $user instanceof WP_User && in_array('customer', (array) $user->roles, true)
        && get_user_meta($user->ID, 'billing_phone', true) !== '';
}

function aicc_recovery_public_account($user): array {
    return array(
        'match' => true,
        'account_ref' => 'woo-customer:' . (int) $user->ID,
        'login_id' => (string) $user->user_login,
        'full_name' => (string) get_user_meta($user->ID, 'first_name', true),
        'phone' => (string) get_user_meta($user->ID, 'billing_phone', true),
    );
}

function aicc_recovery_lookup_id($request) {
    $data = aicc_recovery_input($request, array('name', 'phone'));
    if (is_wp_error($data)) { return $data; }
    if ($data['name'] === '' || strlen($data['name']) > 100 || !aicc_recovery_valid_phone($data['phone'])) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    $users = get_users(array(
        'role' => 'customer',
        'number' => 3,
        'fields' => 'all',
        'meta_query' => array(array(
            'key' => 'billing_phone', 'value' => $data['phone'], 'compare' => '=',
        )),
    ));
    if (!is_array($users) || count($users) > 2) {
        return new WP_REST_Response(array('match' => false), 200, array('Cache-Control' => 'no-store'));
    }
    $matches = array();
    foreach ($users as $user) {
        if (aicc_recovery_customer($user)
            && get_user_meta($user->ID, 'billing_phone', true) === $data['phone']
            && get_user_meta($user->ID, 'first_name', true) === $data['name']) {
            $matches[] = $user;
        }
    }
    if (count($matches) !== 1) {
        return new WP_REST_Response(array('match' => false), 200, array('Cache-Control' => 'no-store'));
    }
    return new WP_REST_Response(aicc_recovery_public_account($matches[0]), 200,
        array('Cache-Control' => 'no-store'));
}

function aicc_recovery_lookup_password($request) {
    $data = aicc_recovery_input($request, array('login_id', 'name', 'phone'));
    if (is_wp_error($data)) { return $data; }
    if ($data['login_id'] === '' || strlen($data['login_id']) > 100
        || $data['name'] === '' || strlen($data['name']) > 100
        || !aicc_recovery_valid_phone($data['phone'])) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    $user = get_user_by('login', $data['login_id']);
    if (!aicc_recovery_customer($user)
        || get_user_meta($user->ID, 'billing_phone', true) !== $data['phone']
        || get_user_meta($user->ID, 'first_name', true) !== $data['name']) {
        return new WP_REST_Response(array('match' => false), 200, array('Cache-Control' => 'no-store'));
    }
    return new WP_REST_Response(aicc_recovery_public_account($user), 200,
        array('Cache-Control' => 'no-store'));
}

function aicc_recovery_resolve_ref($account_ref) {
    if (!is_string($account_ref)
        || preg_match('/\Awoo-customer:([1-9][0-9]{0,9})\z/D', $account_ref, $matches) !== 1) {
        return null;
    }
    $user = get_user_by('id', (int) $matches[1]);
    if (!aicc_recovery_customer($user)
        || 'woo-customer:' . (int) $user->ID !== $account_ref) {
        return null;
    }
    return $user;
}

function aicc_recovery_verify_account($request) {
    $data = aicc_recovery_input($request, array('account_ref', 'phone'));
    if (is_wp_error($data)) { return $data; }
    if (!aicc_recovery_valid_phone($data['phone'])
        || !is_string($data['account_ref'])
        || preg_match('/\Awoo-customer:[1-9][0-9]{0,9}\z/D', $data['account_ref']) !== 1) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    $user = aicc_recovery_resolve_ref($data['account_ref']);
    if (!$user || get_user_meta($user->ID, 'billing_phone', true) !== $data['phone']) {
        return new WP_REST_Response(array('match' => false), 200, array('Cache-Control' => 'no-store'));
    }
    return new WP_REST_Response(aicc_recovery_public_account($user), 200,
        array('Cache-Control' => 'no-store'));
}

function aicc_recovery_change_password($request) {
    $data = aicc_recovery_input($request, array('account_ref', 'new_password'));
    if (is_wp_error($data)) { return $data; }
    $password_length = preg_match_all('/./us', $data['new_password']);
    if (!is_string($data['account_ref'])
        || preg_match('/\Awoo-customer:[1-9][0-9]{0,9}\z/D', $data['account_ref']) !== 1
        || !is_int($password_length) || $password_length < 8 || $password_length > 128
        || strpos($data['new_password'], chr(0)) !== false) {
        return new WP_Error('aicc_recovery_invalid', 'Invalid recovery request.', array('status' => 400));
    }
    $user = aicc_recovery_resolve_ref($data['account_ref']);
    if (!$user) {
        return new WP_REST_Response(array('changed' => false, 'account_ref' => $data['account_ref']),
            200, array('Cache-Control' => 'no-store'));
    }
    wp_set_password($data['new_password'], $user->ID);
    if (class_exists('WP_Session_Tokens')) {
        WP_Session_Tokens::get_instance($user->ID)->destroy_all();
    }
    clean_user_cache($user->ID);
    $updated = get_user_by('id', $user->ID);
    $changed = $updated instanceof WP_User
        && wp_check_password($data['new_password'], $updated->user_pass, $user->ID);
    return new WP_REST_Response(array(
        'changed' => $changed,
        'account_ref' => $data['account_ref'],
    ), 200, array('Cache-Control' => 'no-store'));
}

add_action('rest_api_init', function() {
    if (!aicc_recovery_is_dev()) { return; }
    $routes = array(
        '/lookup-id' => 'aicc_recovery_lookup_id',
        '/lookup-password' => 'aicc_recovery_lookup_password',
        '/verify-account' => 'aicc_recovery_verify_account',
        '/change-password' => 'aicc_recovery_change_password',
    );
    foreach ($routes as $route => $callback) {
        register_rest_route(AICC_RECOVERY_NAMESPACE, $route, array(
            'methods' => 'POST',
            'permission_callback' => 'aicc_recovery_permission',
            'callback' => $callback,
        ));
    }
});
