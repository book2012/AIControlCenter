"""PROD-only WooCommerce account presentation contract tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront"
MAIN = (PLUGIN / "ai-shopping-storefront.php").read_text()
ACCOUNT = (PLUGIN / "includes/class-account-presentation.php").read_text()
CSS = (PLUGIN / "assets/account-presentation.css").read_text()
JS = (PLUGIN / "assets/account-presentation.js").read_text()
CADDY = (ROOT / "ops/macos/caddy/Caddyfile").read_text()


def test_account_presentation_is_strictly_production_host_scoped():
    assert "private const PROD_HOST = 'agachichi.duckdns.org';" in ACCOUNT
    assert "if ($host !== self::PROD_HOST)" in ACCOUNT
    assert "AI_Shopping_Account_Presentation::boot();" in MAIN
    assert "includes/class-account-presentation.php" in MAIN
    assert "document_title_parts" in ACCOUNT
    assert "$parts['site'] = 'agachichi';" in ACCOUNT


def test_login_and_logout_use_woocommerce_account_endpoints():
    assert "woocommerce_before_customer_login_form" in ACCOUNT
    assert "is_user_logged_in()" in ACCOUNT
    assert "wc_get_account_endpoint_url('customer-logout')" in ACCOUNT
    assert "wp_nonce_url(" in ACCOUNT
    assert "data-aicc-prod-logout" in ACCOUNT
    assert "로그아웃하시겠습니까?" in JS
    assert "wp-admin/admin-ajax.php" not in ACCOUNT + JS
    assert "wp_ajax_aicc_account" not in ACCOUNT
    assert "@wordpress_namespace path /wp-admin /wp-admin/*" in CADDY


def test_prod_customer_signup_and_dev_phone_verification_are_not_enabled():
    for forbidden in (
        "woocommerce_created_customer",
        "aicc_check_username",
        "aicc_account_registration",
        "REGISTRATION_PUBLIC_KEY",
        "Twilio",
        "회원가입",
    ):
        assert forbidden not in ACCOUNT
    assert "/my-account/register/" not in ACCOUNT


def test_prod_account_is_branded_responsive_and_has_no_theme_shell():
    assert "agachichi" in ACCOUNT
    assert "aicc-prod-account" in ACCOUNT
    assert ".site-header" in CSS and ".site-footer" in CSS
    assert "@media(max-width:520px)" in CSS
    assert "@media(prefers-color-scheme:dark)" in CSS
    assert "aicc-prod-account-heading" in CSS
    assert "aicc-prod-guest-order" in CSS


def test_login_navigation_and_guest_order_paths_are_explicit():
    for route in (
        "/my-account/",
        "/my-account/orders/",
        "/homepage/storefront/search",
        "/homepage/storefront/cart",
        "/homepage/storefront/my-orders",
    ):
        assert route in ACCOUNT
    assert "AGACHICHI MEMBERS" in ACCOUNT
    assert "로그인" in ACCOUNT
    assert "비회원 주문 조회" in ACCOUNT
