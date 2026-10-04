"""Focused contracts for STOREFRONT-PROD-RUNTIME-ISOLATION-01."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from core.shopping.storefront_prod_runtime import (
    ACCEPTED_GIT_COMMIT,
    PLUGIN_VERSION,
    PRESENTATION_IDENTIFIER,
    ReleaseManifestError,
    plan_contract,
    validate_contract,
    validate_release,
)


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy/shopping/compose.yaml"
CLI = ROOT / "scripts/storefront_prod_runtime.py"
PLUGIN = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront"


def _manifest(release: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "environment": "prod",
        "service": "storefront",
        "git_commit": ACCEPTED_GIT_COMMIT,
        "plugin_version": PLUGIN_VERSION,
        "presentation_identifier": PRESENTATION_IDENTIFIER,
        "release_path": str(release.absolute()),
        "created_at": "2026-10-04T00:00:00Z",
        "source_clean": True,
        "source_provenance": {
            "method": "git_archive",
            "archived_revision": ACCEPTED_GIT_COMMIT,
            "working_tree_clean": True,
        },
    }


def _write_release(root: Path) -> Path:
    release = root / "releases" / ACCEPTED_GIT_COMMIT / "ai-shopping-storefront"
    release.mkdir(parents=True)
    (release / "ai-shopping-storefront.php").write_text("<?php\n")
    manifest = _manifest(release)
    (root / "current.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (release / ".aicontrolcenter-release.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n"
    )
    return release


def test_compose_uses_required_external_read_only_release_path():
    compose = COMPOSE.read_text()
    assert "AICONTROLCENTER_STOREFRONT_PROD_PLUGIN_PATH:?" in compose
    assert ":/var/www/html/wp-content/plugins/ai-shopping-storefront:ro" in compose
    assert "./wordpress/plugins/ai-shopping-storefront" not in compose
    assert compose.count("/var/www/html/wp-content/plugins/ai-shopping-storefront:ro") == 2


def test_release_is_commit_addressed_and_validates(tmp_path):
    root = tmp_path / "storefront-prod"
    release = _write_release(root)
    assert release == root / "releases" / ACCEPTED_GIT_COMMIT / "ai-shopping-storefront"
    assert validate_release(root).release_path == str(release.absolute())
    assert validate_contract(root)["valid"] is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("environment", "dev"),
        ("service", "homepage"),
        ("git_commit", "not-a-commit"),
        ("plugin_version", "0.17.0"),
        ("presentation_identifier", "SHOP_MEDIA_002_ORANGE_COCO"),
    ],
)
def test_invalid_manifest_fields_fail_closed(tmp_path, field, value):
    root = tmp_path / "storefront-prod"
    _write_release(root)
    manifest_path = root / "current.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ReleaseManifestError):
        validate_release(root)


def test_symlinked_root_and_release_directory_fail_closed(tmp_path):
    actual = tmp_path / "actual"
    release = _write_release(actual)
    root_link = tmp_path / "storefront-prod"
    root_link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ReleaseManifestError):
        validate_release(root_link)

    for child in release.iterdir():
        child.unlink()
    release.rmdir()
    release.symlink_to(PLUGIN, target_is_directory=True)
    with pytest.raises(ReleaseManifestError):
        validate_release(actual)


def test_escape_and_inconsistent_marker_fail_closed(tmp_path):
    root = tmp_path / "storefront-prod"
    release = _write_release(root)
    manifest_path = root / "current.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["release_path"] = str(tmp_path / "outside")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ReleaseManifestError):
        validate_release(root)

    manifest_path.write_text(json.dumps(_manifest(release)))
    marker = release / ".aicontrolcenter-release.json"
    inconsistent = json.loads(marker.read_text())
    inconsistent["plugin_version"] = "0.17.0"
    marker.write_text(json.dumps(inconsistent))
    with pytest.raises(ReleaseManifestError):
        validate_release(root)


def test_missing_plugin_entrypoint_fails_closed(tmp_path):
    root = tmp_path / "storefront-prod"
    release = _write_release(root)
    (release / "ai-shopping-storefront.php").unlink()
    with pytest.raises(ReleaseManifestError):
        validate_release(root)


def test_plan_is_read_only_execute_false_and_has_no_lifecycle_operation():
    result = plan_contract(ROOT, Path("/tmp/aicontrolcenter-storefront-prod-releases"))
    assert result["mode"] == "plan_only"
    assert result["execute"] is False
    assert result["release_path"].endswith(
        f"releases/{ACCEPTED_GIT_COMMIT}/ai-shopping-storefront"
    )
    assert result["plugin_version"] == "0.18.0"
    assert result["presentation_identifier"] == "SHOP_MEDIA_003_AGACHICHI"
    source = CLI.read_text() + "\n" + (ROOT / "core/shopping/storefront_prod_runtime.py").read_text()
    assert 'add_parser("apply"' not in source
    assert "def apply" not in source
    assert "docker" not in source.lower()
    assert "reload=True" not in source


def test_cli_is_json_only_and_has_only_read_commands():
    result = subprocess.run(
        [sys.executable, str(CLI), "status", "--release-root", str(Path("/tmp/missing-storefront"))],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["validation"]["valid"] is False
    assert "apply" not in CLI.read_text()


def test_presentation_security_and_caddy_topology_contracts_remain_untouched():
    promotion = (ROOT / "tests/test_storefront_promotion_01.py").read_text()
    migration = (ROOT / "tests/test_public_storefront_migration_02.py").read_text()
    assert "SHOP_MEDIA_003_AGACHICHI" in promotion
    assert "Version: 0.18.0" in promotion
    assert "reverse_proxy 127.0.0.1:58082" in migration
    assert "reverse_proxy 127.0.0.1:18080" in migration
    assert not re.search(r"caddy.*(reload|stop|restart)", CLI.read_text(), re.I)
