<?php
/**
 * Plugin Name: AIControlCenter Shopping Read
 * Description: Fixed, capability-authenticated published product projection.
 * Version: 1.0.0
 */
if (!defined('ABSPATH')) { exit; }

// Provisioning is deliberately absent. Future CAS must write this option with
// autoload=false. Do not register_setting, expose via REST/admin, or log it.
const AICC_SHOPPING_READ_OPTION = 'aicontrolcenter_shopping_read_verifier_v1';

function aicc_shopping_read_denied() {
    return new WP_Error('aicc_read_denied', 'Shopping read unavailable.', array('status' => 403));
}

function aicc_shopping_read_permission($request) {
    if ($request->get_method() !== 'GET') { return aicc_shopping_read_denied(); }
    $headers = $request->get_header_as_array('authorization');
    if (!is_array($headers) || count($headers) !== 1 || !is_string($headers[0]) ||
        preg_match('/\ABearer ([0-9a-f]{64})\z/D', $headers[0], $matches) !== 1) {
        return aicc_shopping_read_denied();
    }
    $verifier = get_option(AICC_SHOPPING_READ_OPTION, null);
    if (!is_string($verifier) || preg_match('/\A[0-9a-f]{64}\z/D', $verifier) !== 1) {
        return aicc_shopping_read_denied();
    }
    // Explicitly reject the verifier as bearer, even before digest comparison.
    if (hash_equals($verifier, $matches[1]) || !hash_equals($verifier, hash('sha256', $matches[1]))) {
        return aicc_shopping_read_denied();
    }
    return true;
}

function aicc_shopping_read_integer($value, $max) {
    if (is_int($value)) { return $value >= 1 && $value <= $max; }
    return is_string($value) && preg_match('/\A[1-9][0-9]{0,4}\z/D', $value) === 1 && (int)$value <= $max;
}

function aicc_shopping_read_products($request) {
    if (aicc_shopping_read_permission($request) !== true) { return aicc_shopping_read_denied(); }
    $query = $request->get_query_params();
    // No alternate input channel or generic proxy parameters.
    if (!is_array($query) || array_diff(array_keys($query), array('page', 'page_size')) ||
        $request->get_body() !== '') {
        return new WP_Error('aicc_invalid_query', 'Invalid shopping query.', array('status' => 400));
    }
    $page = $query['page'] ?? 1;
    $page_size = $query['page_size'] ?? 20;
    if (!aicc_shopping_read_integer($page, 10000) || !aicc_shopping_read_integer($page_size, 20)) {
        return new WP_Error('aicc_invalid_query', 'Invalid shopping query.', array('status' => 400));
    }
    if (!function_exists('wc_get_products') || !class_exists('WC_Product')) {
        return new WP_Error('aicc_engine_unavailable', 'Shopping read unavailable.', array('status' => 503));
    }
    $page = (int)$page;
    $page_size = (int)$page_size;
    try {
        $products = wc_get_products(array(
            'status' => 'publish', 'limit' => $page_size + 1,
            'offset' => ($page - 1) * $page_size,
            'orderby' => 'ID', 'order' => 'ASC', 'return' => 'objects',
            'aicc_shopping_read_public_only' => true,
        ));
        if (!is_array($products) || count($products) > $page_size + 1) { throw new RuntimeException(); }
        $items = array();
        $previous = 0;
        foreach ($products as $product) {
            if (!($product instanceof WC_Product)) { throw new RuntimeException(); }
            $id = $product->get_id();
            // Defense in depth if another plugin tampers with the supported query.
            if (!is_int($id) || $id <= $previous || $product->get_status() !== 'publish' ||
                get_post_field('post_password', $id, 'raw') !== '') { throw new RuntimeException(); }
            $previous = $id;
            $name = html_entity_decode(wp_strip_all_tags($product->get_name()), ENT_QUOTES | ENT_HTML5, 'UTF-8');
            $name = preg_replace('/[\x00-\x1F\x7F<>]/u', '', $name);
            if (!is_string($name)) { throw new RuntimeException(); }
            // Bound Unicode code points, without relying on optional mbstring.
            preg_match('/\A.{0,200}/us', $name, $bounded);
            $name = $bounded[0] ?? '';
            // Reflections of credentials/headers must never enter a response.
            $authorization = $request->get_header_as_array('authorization')[0];
            $verifier = get_option(AICC_SHOPPING_READ_OPTION, null);
            if (strpos($name, substr($authorization, 7)) !== false ||
                (is_string($verifier) && strpos($name, $verifier) !== false) ||
                strpos($name, 'Authorization') !== false || strpos($name, 'Bearer ') !== false) {
                throw new RuntimeException();
            }
            $items[] = array('id' => $id, 'name' => $name);
        }
        $has_more = count($items) > $page_size;
        return new WP_REST_Response(array('items' => array_slice($items, 0, $page_size),
            'page' => $page, 'page_size' => $page_size, 'has_more' => $has_more), 200,
            array('Cache-Control' => 'no-store'));
    } catch (Throwable $ignored) {
        return new WP_Error('aicc_engine_unavailable', 'Shopping read unavailable.', array('status' => 503));
    }
}

// WooCommerce's supported CPT data-store query extension, scoped to our flag.
// Filter before pagination, so protected products do not create gaps or leak counts.
add_filter('woocommerce_product_data_store_cpt_get_products_query', function($query, $vars) {
    if (!empty($vars['aicc_shopping_read_public_only'])) {
        $query['has_password'] = false;
        $query['post_status'] = 'publish';
    }
    return $query;
}, 10, 2);

add_action('rest_api_init', function() {
    register_rest_route('aicontrolcenter/v1', '/shopping/products', array(
        'methods' => 'GET',
        'permission_callback' => 'aicc_shopping_read_permission',
        'callback' => 'aicc_shopping_read_products',
    ));
});
