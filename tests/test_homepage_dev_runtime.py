import json
from pathlib import Path
import plistlib

import pytest

from core.homepage.managed_runtime import (
    HOST,
    LAUNCHD_LABEL,
    PORT,
    ReleaseManifestError,
    build_plan,
    status_contract,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
PLIST = ROOT / "ops/macos/launchd/com.aicontrolcenter.homepage-dev.plist"
WRAPPER = ROOT / "ops/macos/launchd/run-homepage-dev-immutable-release.sh"


def write_release(root: Path, *, commit: str = "a" * 40) -> Path:
    release = root / "releases" / commit
    release.mkdir(parents=True)
    (release / "core/homepage").mkdir(parents=True)
    (release / "core/homepage/preview.py").write_text("# release-owned\n")
    (release / "core/homepage/__init__.py").write_text("")
    manifest = {
        "schema_version": 1,
        "environment": "dev",
        "service": "homepage",
        "git_commit": commit,
        "release_path": str(release.absolute()),
        "created_at": "2026-10-03T00:00:00Z",
        "source_clean": True,
        "source_provenance": {
            "method": "git_archive",
            "archived_revision": commit,
            "working_tree_clean": True,
        },
        "presentation_identifier": "SHOP_MEDIA_003_AGACHICHI",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "current.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (release / ".aicontrolcenter-release.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return release


def test_loopback_and_exact_port_are_contract_constants():
    assert HOST == "127.0.0.1"
    assert PORT == 18080


def test_status_contract_is_json_first_and_managed(tmp_path):
    release = write_release(tmp_path / "homepage-dev")
    result = status_contract(release.parent.parent)
    assert result == {
        "schema_version": 1,
        "environment": "dev",
        "service": "homepage",
        "host": "127.0.0.1",
        "port": 18080,
        "release": {
            "git_commit": "a" * 40,
            "path": str(release.absolute()),
            "presentation_identifier": "SHOP_MEDIA_003_AGACHICHI",
        },
        "runtime": {"managed": True, "healthy": True},
        "validation": {"valid": True},
    }


def test_missing_or_invalid_manifest_fails_closed(tmp_path):
    root = tmp_path / "homepage-dev"
    root.mkdir()
    invalid = validate_contract(root)
    assert invalid["valid"] is False
    assert status_contract(root)["runtime"]["healthy"] is False
    with pytest.raises(ReleaseManifestError):
        from core.homepage.managed_runtime import validate_release
        validate_release(root)


def test_release_commit_and_path_validation(tmp_path):
    root = tmp_path / "homepage-dev"
    release = write_release(root)
    manifest_path = root / "current.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["release_path"] = str(root / "releases" / ("b" * 40))
    manifest_path.write_text(json.dumps(manifest))
    assert validate_contract(root)["valid"] is False
    assert not (root / "releases" / ("b" * 40)).exists()
    assert release.exists()


def test_launchd_candidate_contract_and_future_wrapper():
    data = plistlib.loads(PLIST.read_bytes())
    assert data["Label"] == LAUNCHD_LABEL
    assert data["RunAtLoad"] is True
    assert data["KeepAlive"] is True
    assert data["ProcessType"] == "Background"
    assert data["ThrottleInterval"] == 10
    assert data["UserName"] == "kyouhan"
    assert data["GroupName"] == "staff"
    assert data["ProgramArguments"] == [
        "/bin/bash",
        "/usr/local/libexec/aicontrolcenter/run-homepage-dev-immutable-release.sh",
    ]
    assert data["StandardOutPath"].startswith("/var/log/aicontrolcenter/")
    assert data["StandardErrorPath"].startswith("/var/log/aicontrolcenter/")

    wrapper = WRAPPER.read_text()
    assert "127.0.0.1" in wrapper and "18080" in wrapper
    assert "--reload" not in wrapper and "reload=True" not in wrapper
    assert "PYTHONPATH=\"$RELEASE_PATH\"" in wrapper
    assert "exec /usr/bin/env -i" in wrapper
    assert "launchctl" not in wrapper


def test_managed_runtime_never_uses_working_tree_or_other_authority():
    managed = (ROOT / "core/homepage/managed_runtime.py").read_text()
    wrapper = WRAPPER.read_text()
    assert "working_tree_source\": False" in managed
    assert "--reload" not in managed and "reload=True" not in managed
    assert "0.0.0.0" not in managed + wrapper
    assert "58081" not in managed + wrapper
    assert "launchctl" not in managed + wrapper
    assert "caddy" not in managed.lower() + wrapper.lower()
    assert "woocommerce" not in managed.lower() + wrapper.lower()
    assert "ubuntu" not in managed.lower() + wrapper.lower()


def test_plan_is_read_only_and_requires_clean_head():
    result = build_plan(ROOT, Path("/tmp/aicontrolcenter-homepage-dev-releases"))
    assert result["mode"] == "plan_only"
    assert result["execute"] is False
    assert result["approved"] is result["source_clean"]
    assert result["materialization"]["method"] == "git_archive"
    assert result["materialization"]["working_tree_source"] is False
