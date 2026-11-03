from copy import deepcopy
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from core.modules.plugin_catalog import ROOT, PLUGIN_IDS, PluginManifestError, load_catalog, validate_manifest
from core.modules.composition import create_module_app
from core.modules.lifecycle import create_managed_app
from fastapi import FastAPI


def manifest():
    return json.loads((ROOT / "shopping/manifest.json").read_text())


def test_all_plugin_manifests_describe_separate_responsibilities():
    entries = load_catalog()
    assert [x["plugin_id"] for x in entries] == list(PLUGIN_IDS)
    assert all(x["manifest_status"] == "VALID" for x in entries)
    assert all(x["module_id"] == x["plugin_id"] for x in entries)
    assert all(x["data_deletion_on_detach"] is False for x in entries)
    assert any(c["readiness"] == "NOT_CONNECTED" for x in entries for c in x["components"])


def test_catalog_does_not_attach_or_claim_ready():
    with TestClient(create_module_app()) as client:
        response = client.get("/platform/plugins")
        assert response.status_code == 200
        value = response.json()
        assert value["catalog_is_authorization"] is False
        assert all(x["attachment_state"] == "DETACHED" for x in value["plugins"])
        assert all(x["operational_readiness"] == "NOT_VERIFIED_BY_CATALOG" for x in value["plugins"])
        assert client.post("/platform/plugins", json={"attach": "shopping"}).status_code == 405
        assert client.get("/extensions/shopping/health").status_code == 404


def test_catalog_distinguishes_bad_metadata_from_runtime_state(tmp_path):
    from core.modules.plugin_catalog import add_plugin_catalog_route
    app = FastAPI()
    add_plugin_catalog_route(app, lambda: [{"module_id": "shopping", "state": "ATTACHED"}], root=tmp_path)
    result = TestClient(app).get("/platform/plugins").json()["plugins"]
    assert result[0]["manifest_status"] == "UNAVAILABLE"
    assert result[0]["attachment_state"] == "ATTACHED"
    assert result[0]["operational_readiness"] == "NOT_VERIFIED_BY_CATALOG"


@pytest.mark.parametrize("field,value", [
    ("plugin_id", "../shopping"), ("module_id", "personal-assistant"),
    ("schema_version", True), ("plugin_version", "bad"),
    ("control_plane", "plugin-owned"), ("data_deletion_on_detach", True),
    ("requires", ["shopping"]), ("source_paths", ["../../private"]),
    ("components", []), ("display_name", ""),
])
def test_invalid_manifest_cannot_change_contract(field, value):
    data = manifest()
    data[field] = value
    with pytest.raises(PluginManifestError):
        validate_manifest(data, "shopping")


def test_unknown_executable_field_rejected():
    data = manifest()
    data["entrypoint"] = "os.system"
    with pytest.raises(PluginManifestError):
        validate_manifest(data, "shopping")


def test_duplicate_components_rejected():
    data = manifest()
    data["components"].append(deepcopy(data["components"][0]))
    with pytest.raises(PluginManifestError):
        validate_manifest(data, "shopping")


def test_duplicate_json_and_unregistered_directories_are_not_discovered(tmp_path):
    folder = tmp_path / "shopping"
    folder.mkdir()
    (folder / "manifest.json").write_text('{"schema_version":1,"schema_version":1}')
    other = tmp_path / "rogue"
    other.mkdir()
    (other / "manifest.json").write_text('{"entrypoint":"os.system"}')
    entries = load_catalog(tmp_path)
    assert len(entries) == 3
    assert all(x["manifest_status"] == "UNAVAILABLE" for x in entries)
    assert not any(x["plugin_id"] == "rogue" for x in entries)


def test_managed_catalog_follows_attach_detach_without_losing_manifest():
    def provider():
        return FastAPI()
    app = create_managed_app(["shopping"], providers={"shopping": provider})
    with TestClient(app) as client:
        first = client.get("/platform/plugins").json()["plugins"][0]
        assert first["attachment_state"] == "ATTACHED"
        client.portal.call(app.state.module_manager.detach, "shopping")
        second = client.get("/platform/plugins").json()["plugins"][0]
        assert second["attachment_state"] == "DETACHED"
        assert second["components"] == first["components"]
        assert second["source_paths"] == first["source_paths"]
