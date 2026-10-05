<?php
// Explicit DEV-only provisioning; never loaded by production WordPress.
error_reporting(0);
register_shutdown_function(function(){ $e=error_get_last();if($e&&in_array($e["type"],[E_ERROR,E_PARSE,E_CORE_ERROR,E_COMPILE_ERROR])) {fwrite(STDERR,$e["message"]);}});
$cfg=json_decode(file_get_contents('php://stdin'),true);
if (($cfg['environment']??'')!=='DEV' || getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev') {exit(2);}
if (!empty($cfg['install_only'])) {define('WP_INSTALLING',true);}
require '/var/www/html/wp-load.php';
require_once ABSPATH.'wp-admin/includes/upgrade.php';
require_once ABSPATH.'wp-admin/includes/plugin.php';
add_filter('pre_wp_mail',fn()=>false);
if (!is_blog_installed()) {
 wp_install('AIControlCenter DEV Commerce',$cfg['admin_username'],'dev-admin@example.invalid',false,'',$cfg['admin_password']);
}
if (!empty($cfg['install_only'])) {echo json_encode(['installed'=>true]);return;}
update_option('home','https://localhost:18446');update_option('siteurl','https://localhost:18446');
update_option('woocommerce_currency','KRW');update_option('woocommerce_default_country','KR');
update_option('woocommerce_calc_taxes','no');update_option('blog_public',0);
update_option('permalink_structure','/%postname%/');
activate_plugin('woocommerce/woocommerce.php');
if (!class_exists('WooCommerce')) {require_once WP_PLUGIN_DIR.'/woocommerce/woocommerce.php';}
WC_Install::install();if(!did_action('woocommerce_init')){WC_Post_Types::register_taxonomies();WC_Post_Types::register_post_types();WC()->init();}flush_rewrite_rules();
$mu=WPMU_PLUGIN_DIR;if(!is_dir($mu)){wp_mkdir_p($mu);}
file_put_contents($mu.'/aicc-dev-no-email.php',"<?php if (getenv('WORDPRESS_DB_NAME')==='aicc_order_dev') { add_filter('pre_wp_mail',fn()=>false); }");
$sku='aicc-dev-oc-demo-top-0001';$id=wc_get_product_id_by_sku($sku);
$demo=$cfg['demo_product'];
if (!$id) {
 $product=new WC_Product_Variable();$product->set_name($demo['name']);$product->set_sku($sku);
 $product->set_description($demo['description']);$product->set_status('publish');
 $attribute=new WC_Product_Attribute();$attribute->set_name('Size');
 $attribute->set_options(array_column($demo['variants'],'label'));$attribute->set_visible(true);$attribute->set_variation(true);
 $product->set_attributes([$attribute]);$id=$product->save();
 foreach ($demo['variants'] as $option) {
  $variant=new WC_Product_Variation();$variant->set_parent_id($id);$variant->set_attributes(['size'=>$option['label']]);
  $variant->set_regular_price($demo['price']);$variant->set_manage_stock(true);$variant->set_stock_quantity($option['available']?20:0);
  $variant->set_stock_status($option['available']?'instock':'outofstock');$variant->set_status('publish');$variant->save();
 }
 WC_Product_Variable::sync($id);
}
WC_Product_Variable::sync($id);wc_delete_product_transients($id);
$username='aicc-dev-test-customer';$customer=get_user_by('login',$username);
if (!$customer) {$cid=wp_create_user($username,$cfg['customer_password'],'dev-customer@example.invalid');if(is_wp_error($cid)){exit(3);} $customer=get_user_by('id',$cid);$customer->set_role('customer');}
$api=get_user_by('login','aicc-dev-order-api');
if (!$api) {$aid=wp_create_user('aicc-dev-order-api',$cfg['api_password'],'dev-api@example.invalid');if(is_wp_error($aid)){exit(4);} $api=get_user_by('id',$aid);$api->set_role('shop_manager');}
$key=$cfg['existing_consumer_key'];$secret=$cfg['existing_consumer_secret'];
global $wpdb;$keyhash=wc_api_hash($key);
$found=$wpdb->get_var($wpdb->prepare("SELECT key_id FROM {$wpdb->prefix}woocommerce_api_keys WHERE consumer_key=%s",$keyhash));
if (!$found) {$wpdb->insert($wpdb->prefix.'woocommerce_api_keys',['user_id'=>$api->ID,'description'=>'AIControlCenter isolated DEV order','permissions'=>'read_write','consumer_key'=>$keyhash,'consumer_secret'=>$secret,'truncated_key'=>substr($key,-7)]);}
$variants=[];foreach(wc_get_product($id)->get_children() as $vid){$v=wc_get_product($vid);$variants[]=['id'=>$vid,'label'=>implode(' / ',$v->get_attributes()),'available'=>$v->is_in_stock()];}
echo json_encode(['product_id'=>$id,'variants'=>$variants,'customer_id'=>$customer->ID,'consumer_key'=>$key,'consumer_secret'=>$secret],JSON_UNESCAPED_UNICODE)."\n";
