#!/bin/sh
set -eu
umask 077

WP_PATH="/var/www/html"
WOO_PACKAGE="/opt/aicontrolcenter/woocommerce.zip"
WOO_SLUG="woocommerce"
STOREFRONT_SLUG="ai-shopping-storefront"
STOREFRONT_VERSION="4.6.2"
STOREFRONT_PACKAGE_PATH="/opt/aicontrolcenter/storefront.zip"
STOREFRONT_PACKAGE_SHA256="163b5bf217dad76a823432d8c01598ab3dc3f15cbdd69067b98f5a6ddf05c1c4"

: "${WORDPRESS_DB_HOST:?WORDPRESS_DB_HOST is required}"
: "${WORDPRESS_DB_NAME:?WORDPRESS_DB_NAME is required}"
: "${WORDPRESS_DB_USER:?WORDPRESS_DB_USER is required}"
: "${WORDPRESS_DB_PASSWORD:?WORDPRESS_DB_PASSWORD is required}"
: "${SHOPPING_SITE_URL:?SHOPPING_SITE_URL is required}"
: "${SHOPPING_SITE_TITLE:?SHOPPING_SITE_TITLE is required}"
: "${SHOPPING_ADMIN_USER:?SHOPPING_ADMIN_USER is required}"
: "${SHOPPING_ADMIN_PASSWORD:?SHOPPING_ADMIN_PASSWORD is required}"
: "${SHOPPING_ADMIN_EMAIL:?SHOPPING_ADMIN_EMAIL is required}"

printf "%s\n" "[BOOTSTRAP][01/07] configuration contract verified"

if wp core is-installed --path="$WP_PATH" >/dev/null 2>&1; then
    printf "%s\n" "[BOOTSTRAP][02/07] WordPress core already installed"
else
    WP_ADMIN_PASSWORD_STDIN="$SHOPPING_ADMIN_PASSWORD"
  printf "%s\n" "$WP_ADMIN_PASSWORD_STDIN" | wp core install \
        --path="$WP_PATH" \
        --url="$SHOPPING_SITE_URL" \
        --title="$SHOPPING_SITE_TITLE" \
        --admin_user="$SHOPPING_ADMIN_USER" \
        --prompt=admin_password \
        --admin_email="$SHOPPING_ADMIN_EMAIL" \
        --skip-email \
        --quiet
    printf "%s\n" "[BOOTSTRAP][02/07] WordPress core installed"
fi

wp core is-installed --path="$WP_PATH" >/dev/null 2>&1
printf "%s\n" "[BOOTSTRAP][03/07] WordPress core installation verified"

if wp plugin is-installed "$WOO_SLUG" --path="$WP_PATH" >/dev/null 2>&1; then
    printf "%s\n" "[BOOTSTRAP][04/07] WooCommerce already installed"
else
    WOOCOMMERCE_PACKAGE_SHA256="6e58fc3ba9b18d1c9aee6b0227d3c3c09e4fe2c1332823bd2e0ac54ffcff64a9"
    WOOCOMMERCE_PACKAGE_ACTUAL_SHA256="$(sha256sum /opt/aicontrolcenter/woocommerce.zip | cut -c 1-64)"
    if [ "$WOOCOMMERCE_PACKAGE_ACTUAL_SHA256" != "$WOOCOMMERCE_PACKAGE_SHA256" ]; then
        printf "%s\n" "[BOOTSTRAP][FAIL] WooCommerce package integrity verification failed" >&2
        exit 1
    fi

    wp plugin install "$WOO_PACKAGE" --path="$WP_PATH" --quiet
    printf "%s\n" "[BOOTSTRAP][04/07] WooCommerce installed from tracked package"
fi

if wp plugin is-active "$WOO_SLUG" --path="$WP_PATH" >/dev/null 2>&1; then
    printf "%s\n" "[BOOTSTRAP][05/07] WooCommerce already active"
else
    wp plugin activate "$WOO_SLUG" --path="$WP_PATH" --quiet
    printf "%s\n" "[BOOTSTRAP][05/07] WooCommerce activated"
fi

if wp theme is-installed "$STOREFRONT_SLUG" --path="$WP_PATH" >/dev/null 2>&1; then
    printf "%s\n" "[BOOTSTRAP][06/07] Storefront theme already installed"
else
    STOREFRONT_PACKAGE_ACTUAL_SHA256="$(sha256sum "$STOREFRONT_PACKAGE_PATH" | cut -c 1-64)"
if [ "$STOREFRONT_PACKAGE_ACTUAL_SHA256" != "$STOREFRONT_PACKAGE_SHA256" ]; then
    printf "%s\n" "[BOOTSTRAP][FAIL] Storefront package integrity verification failed" >&2
    exit 1
fi
wp theme install "$STOREFRONT_PACKAGE_PATH" --path="$WP_PATH" --quiet
    printf "%s\n" "[BOOTSTRAP][06/07] Storefront theme installed"
fi

STOREFRONT_INSTALLED_VERSION="$(wp theme get "$STOREFRONT_SLUG" --field=version --path="$WP_PATH")"
if [ "$STOREFRONT_INSTALLED_VERSION" != "$STOREFRONT_VERSION" ]; then
    printf "%s\n" "[BOOTSTRAP][FAIL] Storefront theme version mismatch" >&2
    exit 1
fi

if wp theme is-active "$STOREFRONT_SLUG" --path="$WP_PATH" >/dev/null 2>&1; then
    printf "%s\n" "[BOOTSTRAP][06/07] Storefront theme already active"
else
    STOREFRONT_ACTIVATION_ATTEMPT=1
    STOREFRONT_ACTIVATION_MAX_ATTEMPTS=3
    while [ "$STOREFRONT_ACTIVATION_ATTEMPT" -le "$STOREFRONT_ACTIVATION_MAX_ATTEMPTS" ]; do
        STOREFRONT_ACTIVATION_RC=0
        wp theme activate "$STOREFRONT_SLUG" --path="$WP_PATH" --quiet || STOREFRONT_ACTIVATION_RC=$?
        if wp theme is-active "$STOREFRONT_SLUG" --path="$WP_PATH" >/dev/null 2>&1; then
            break
        fi
        if [ "$STOREFRONT_ACTIVATION_ATTEMPT" -ge "$STOREFRONT_ACTIVATION_MAX_ATTEMPTS" ]; then
            printf "%s\n" "[BOOTSTRAP][FAIL] Storefront activation postcondition failed after bounded attempts rc=$STOREFRONT_ACTIVATION_RC" >&2
            exit 1
        fi
        sleep 1
        STOREFRONT_ACTIVATION_ATTEMPT=$((STOREFRONT_ACTIVATION_ATTEMPT + 1))
    done
    wp theme is-active "$STOREFRONT_SLUG" --path="$WP_PATH" >/dev/null 2>&1
    printf "%s\n" "[BOOTSTRAP][06/07] Storefront theme activated"
fi

wp plugin is-active "$WOO_SLUG" --path="$WP_PATH" >/dev/null 2>&1
wp theme is-active "$STOREFRONT_SLUG" --path="$WP_PATH" >/dev/null 2>&1

printf "%s\n" "[BOOTSTRAP][07/07] Commerce bootstrap completed"
