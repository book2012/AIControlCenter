from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy/shopping/compose.yaml"
ENV_EXAMPLE = ROOT / "deploy/shopping/.env.example"
DOCKERIGNORE = ROOT / "deploy/shopping/.dockerignore"
DOCKERFILE = ROOT / "deploy/shopping/bootstrap/Dockerfile"
SCRIPT = ROOT / "deploy/shopping/bootstrap/bootstrap-commerce.sh"


def test_dockerignore_is_deny_by_default() -> None:
    lines = [
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert lines == [
        "**",
        "!bootstrap/",
        "!bootstrap/**",
        "!cache/",
        "!cache/woocommerce.zip",
    ]


def test_bootstrap_dockerfile_is_local_and_one_shot() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    assert re.fullmatch(
        r"FROM wordpress:cli@sha256:[0-9a-f]{64}",
        first_line,
    ) is not None
    assert "COPY cache/woocommerce.zip /opt/aicontrolcenter/woocommerce.zip" in text
    assert "COPY bootstrap/bootstrap-commerce.sh /usr/local/bin/bootstrap-commerce" in text
    assert "ENTRYPOINT [\"/usr/local/bin/bootstrap-commerce\"]" in text
    assert "http://" not in text
    storefront_https = "ADD --checksum=sha256:163b5bf217dad76a823432d8c01598ab3dc3f15cbdd69067b98f5a6ddf05c1c4 --chmod=0444 https://downloads.wordpress.org/theme/storefront.4.6.2.zip /opt/aicontrolcenter/storefront.zip"
    https_lines = [line.strip() for line in text.splitlines() if "https://" in line]
    assert https_lines == [storefront_https]


def test_bootstrap_script_is_idempotent_and_does_not_trace_secrets() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    result = subprocess.run(
        ["/bin/sh", "-n", str(SCRIPT)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "set -x" not in text
    assert "wp core is-installed" in text
    assert "wp core install" in text
    assert "wp plugin is-installed \"$WOO_SLUG\"" in text
    assert "wp plugin is-active \"$WOO_SLUG\"" in text
    assert "wp theme is-installed \"$STOREFRONT_SLUG\"" in text
    assert "wp theme is-active \"$STOREFRONT_SLUG\"" in text
    for line in text.splitlines():
        if "printf" in line:
            assert "SHOPPING_ADMIN_PASSWORD" not in line
            assert "WORDPRESS_DB_PASSWORD" not in line


def test_compose_bootstrap_contract_is_explicit() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    required = [
        "image: aicontrolcenter/wordpress-cli-bootstrap:local",
        "pull_policy: build",
        "dockerfile: bootstrap/Dockerfile",
        "user: \"33:33\"",
        "HOME: \"/tmp\"",
        "condition: service_healthy",
        "ai-shopping-storefront:ro",
    ]
    for marker in required:
        assert marker in text


def test_env_example_has_bootstrap_keys_once() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    keys = re.findall(
        r"^[ \t]*(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=",
        text,
        flags=re.MULTILINE,
    )
    for key in [
        "SHOPPING_SITE_URL",
        "SHOPPING_SITE_TITLE",
        "SHOPPING_ADMIN_USER",
        "SHOPPING_ADMIN_PASSWORD",
        "SHOPPING_ADMIN_EMAIL",
    ]:
        assert keys.count(key) == 1

def test_runtime_images_are_digest_pinned() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert re.search(
        r"mariadb:11\.4\.12@sha256:[0-9a-f]{64}",
        text,
    ) is not None
    assert re.search(
        r"wordpress:php8\.3-apache@sha256:[0-9a-f]{64}",
        text,
    ) is not None

def test_bootstrap_admin_password_uses_prompt_without_direct_printf_secret_reference() -> None:
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1]
        / "deploy/shopping/bootstrap/bootstrap-commerce.sh"
    ).read_text(encoding="utf-8")

    assert "--admin_password=" not in script
    assert script.count("--prompt=admin_password") == 1
    assert "WP_ADMIN_PASSWORD_STDIN=\"$SHOPPING_ADMIN_PASSWORD\"" in script
    assert "\"$WP_ADMIN_PASSWORD_STDIN\" | wp core install" in script
    for line in script.splitlines():
        if "printf" in line:
            assert "SHOPPING_ADMIN_PASSWORD" not in line

def test_storefront_bootstrap_installs_pinned_theme_before_activation():
    with open("deploy/shopping/bootstrap/bootstrap-commerce.sh", encoding="utf-8") as handle:
        source = handle.read()

    assert "STOREFRONT_VERSION=\"4.6.2\"" in source
    install = "wp theme install \"$STOREFRONT_PACKAGE_PATH\" --path=\"$WP_PATH\" --quiet"
    active_check = "if wp theme is-active \"$STOREFRONT_SLUG\" --path=\"$WP_PATH\" >/dev/null 2>&1; then"
    final_assertion = "wp theme is-active \"$STOREFRONT_SLUG\" --path=\"$WP_PATH\" >/dev/null 2>&1"

    assert install in source
    assert source.index(install) < source.index(active_check)
    activation = "wp theme activate \"$STOREFRONT_SLUG\" --path=\"$WP_PATH\" --quiet"
    install_position = source.index(install)
    initial_check_position = source.index(active_check, install_position)
    activation_position = source.index(activation, initial_check_position)
    terminal_assertion_position = source.index(final_assertion, activation_position)
    assert install_position < initial_check_position < activation_position < terminal_assertion_position
    assert source.count(activation) == 1
    assert "STOREFRONT_ACTIVATION_ATTEMPT" not in source
    assert "sleep 1" not in source
    assert "wp theme get \"$STOREFRONT_SLUG\" --field=version --path=\"$WP_PATH\"" in source
    assert "Storefront theme version mismatch" in source
    assert "storefront plugin" not in source


def test_woocommerce_bootstrap_verifies_tracked_zip_sha256_before_install() -> None:
    import hashlib
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    script_path = repo / "deploy/shopping/bootstrap/bootstrap-commerce.sh"
    package_path = repo / "deploy/shopping/cache/woocommerce.zip"
    source = script_path.read_text(encoding="utf-8")
    expected = hashlib.sha256(package_path.read_bytes()).hexdigest()
    literal = "WOOCOMMERCE_PACKAGE_SHA256=\"" + expected + "\""
    assert literal in source
    verify_position = source.index("WOOCOMMERCE_PACKAGE_ACTUAL_SHA256=")
    install_position = source.index("wp plugin install")
    assert verify_position < install_position
    assert "sha256sum /opt/aicontrolcenter/woocommerce.zip | cut -c 1-64" in source
