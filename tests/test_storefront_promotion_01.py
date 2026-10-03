"""Offline contract tests for STOREFRONT-PROMOTION-01."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront"
PLUGIN_MAIN = (PLUGIN / "ai-shopping-storefront.php").read_text()
TEMPLATES = "\n".join(
    path.read_text()
    for path in sorted((PLUGIN / "templates").glob("*.php"))
)
PRESENTATION_SOURCE = "\n".join(
    [
        PLUGIN_MAIN,
        TEMPLATES,
        (PLUGIN / "includes/class-renderer.php").read_text(),
        (PLUGIN / "includes/renderers/class-product-detail-renderer.php").read_text(),
        (PLUGIN / "assets/storefront-ui.js").read_text(),
        (PLUGIN / "assets/agachichi-v1.css").read_text(),
    ]
)
DEPLOYMENT_MANIFEST = json.loads(
    (PLUGIN / "assets/agachichi-v1/deployment-manifest.json").read_text()
)
SOURCE_MANIFEST = json.loads(
    (ROOT / DEPLOYMENT_MANIFEST["source_manifest"]).read_text()
)


def test_plugin_presentation_identifier_and_version_are_explicit():
    assert "AI_SHOPPING_STOREFRONT_PRESENTATION" in PLUGIN_MAIN
    assert "SHOP_MEDIA_003_AGACHICHI" in PLUGIN_MAIN
    assert "Version: 0.18.0" in PLUGIN_MAIN


def test_server_side_api_boundary_remains_canonical():
    assert "http://host.docker.internal:58081" in PLUGIN_MAIN
    assert "wp_remote_get" in (PLUGIN / "includes/class-api-client.php").read_text()


def test_promoted_templates_use_agachichi_branding():
    assert "agachichi" in TEMPLATES
    assert "Everyday Comfort, Playful Touch" in TEMPLATES
    assert "Orange Coco" not in TEMPLATES
    assert "orange coco" not in TEMPLATES


def test_promoted_presentation_has_no_legacy_brand_or_dev_routes():
    assert "Orange Coco" not in PRESENTATION_SOURCE
    assert "orange coco" not in PRESENTATION_SOURCE
    assert "/homepage/assets/" not in PRESENTATION_SOURCE
    assert "dev.bokstory.duckdns.org" not in PRESENTATION_SOURCE
    assert "127.0.0.1:18080" not in PRESENTATION_SOURCE


def test_browser_script_has_no_internal_api_or_privileged_access():
    browser_js = (PLUGIN / "assets/storefront-ui.js").read_text()
    assert "host.docker.internal" not in browser_js
    assert "wp-json" not in browser_js
    assert "consumer_key" not in browser_js
    assert "consumer_secret" not in browser_js
    assert "Authorization" not in browser_js


def test_deployment_manifest_is_deterministic_and_complete():
    assert DEPLOYMENT_MANIFEST["presentation_identifier"] == "SHOP_MEDIA_003_AGACHICHI"
    assert DEPLOYMENT_MANIFEST["source_manifest"] == "brands/agachichi/assets/media/SHOP_MEDIA_003.json"
    assert DEPLOYMENT_MANIFEST["media_count"] == len(DEPLOYMENT_MANIFEST["assets"])
    assert DEPLOYMENT_MANIFEST["product_media_count"] == 120
    assert DEPLOYMENT_MANIFEST["assets"] == sorted(
        DEPLOYMENT_MANIFEST["assets"],
        key=lambda asset: asset["deployed_relative_path"],
    )


def test_manifest_sha256_values_match_packaged_files():
    for asset in DEPLOYMENT_MANIFEST["assets"]:
        deployed = PLUGIN / asset["deployed_relative_path"]
        assert deployed.is_file(), deployed
        digest = hashlib.sha256(deployed.read_bytes()).hexdigest()
        assert digest == asset["sha256"], deployed


def test_only_generated_approved_source_media_are_promoted():
    source_by_id = {
        asset["product_id"]: asset
        for asset in SOURCE_MANIFEST["assets"]
    }
    product_assets = [
        asset
        for asset in DEPLOYMENT_MANIFEST["assets"]
        if asset["asset_type"] == "product"
    ]
    assert len(product_assets) == 120
    for asset in product_assets:
        source = source_by_id[asset["product_id"]]
        assert source["status"] == "GENERATED"
        assert source["target_path"] == asset["source_relative_path"]
        assert source["sha256"] == asset["sha256"]
    packaged_products = sorted(
        path.relative_to(PLUGIN / "assets/agachichi-v1/products").as_posix()
        for path in (PLUGIN / "assets/agachichi-v1/products").rglob("*.jpg")
    )
    manifest_products = sorted(
        asset["deployed_relative_path"].split("assets/agachichi-v1/products/", 1)[1]
        for asset in product_assets
    )
    assert packaged_products == manifest_products


def test_product_media_mapping_is_server_side_and_fail_safe():
    adapter = (PLUGIN / "includes/class-presentation-adapter.php").read_text()
    renderer = (PLUGIN / "includes/class-renderer.php").read_text()
    detail = (PLUGIN / "includes/renderers/class-product-detail-renderer.php").read_text()
    plugin = PLUGIN_MAIN
    assert "AI_Shopping_Agachichi_Presentation_Adapter::image_url" in renderer
    assert "AI_Shopping_Agachichi_Presentation_Adapter::image_url" in detail
    assert "get_product" in plugin
    assert "search" in plugin
    assert "$product['image_url']" not in renderer
    assert "$product['image_url']" not in detail
    assert "return null;" in adapter


def test_existing_public_storefront_security_boundary_is_not_replaced():
    migration = (ROOT / "tests/test_public_storefront_migration_02.py").read_text()
    assert "reverse_proxy 127.0.0.1:58081" in migration
    assert "wp_remote_get" in migration
