<?php

if (!defined('ABSPATH')) {
    exit(1);
}

if (!class_exists('WooCommerce')) {
    fwrite(STDERR, "WooCommerce is not active.\n");
    exit(1);
}

global $wpdb;

$user = get_user_by('login', getenv('SHOPPING_ADMIN_USER'));

if (!$user) {
    fwrite(STDERR, "Admin user was not found.\n");
    exit(1);
}

$description = 'AIControlCenter Read Only';

$existing = $wpdb->get_row(
    $wpdb->prepare(
        "SELECT key_id
         FROM {$wpdb->prefix}woocommerce_api_keys
         WHERE description = %s
         AND user_id = %d",
        $description,
        $user->ID
    )
);

if ($existing) {
    fwrite(STDERR, "A key with this description already exists.\n");
    exit(2);
}

$consumer_key = 'ck_' . wc_rand_hash();
$consumer_secret = 'cs_' . wc_rand_hash();

$result = $wpdb->insert(
    "{$wpdb->prefix}woocommerce_api_keys",
    [
        'user_id'         => $user->ID,
        'description'     => $description,
        'permissions'     => 'read',
        'consumer_key'    => wc_api_hash($consumer_key),
        'consumer_secret' => $consumer_secret,
        'truncated_key'   => substr($consumer_key, -7),
    ],
    [
        '%d',
        '%s',
        '%s',
        '%s',
        '%s',
        '%s',
    ]
);

if (!$result) {
    fwrite(STDERR, "Failed to insert WooCommerce API key.\n");
    exit(1);
}

echo "WOOCOMMERCE_CONSUMER_KEY={$consumer_key}\n";
echo "WOOCOMMERCE_CONSUMER_SECRET={$consumer_secret}\n";
