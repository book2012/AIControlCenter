"""Read-only plugin boundary catalog; metadata grants no activation authority."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

PLUGIN_IDS = ("shopping", "creative-notes", "personal-assistant")
ROOT = Path(__file__).resolve().parents[2] / "plugins"
CORE_SERVICES = ("authorization", "approval", "audit", "deployment-control",
                 "secret-injection", "ai-provider-routing", "scheduling", "notification-routing")
READINESS = {"VALIDATION_ONLY", "BINDING_REQUIRED", "SEPARATE_PRODUCT", "NOT_CONNECTED",
             "REFERENCE_ONLY", "EXTERNAL_SERVICE"}
FIELDS = {"schema_version", "plugin_version", "plugin_id", "module_id", "display_name",
          "purpose", "components", "source_paths", "data_owner", "detach_effect", "requires",
          "control_plane", "lifecycle", "data_deletion_on_detach"}


class PluginManifestError(ValueError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PluginManifestError("duplicate field")
        result[key] = value
    return result


def validate_manifest(value, plugin_id):
    def text(v):
        return type(v) is str and 0 < len(v) <= 1024
    def slug(v):
        return type(v) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", v) is not None
    if (type(value) is not dict or set(value) != FIELDS
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or plugin_id not in PLUGIN_IDS or value["plugin_id"] != plugin_id
            or value["module_id"] != plugin_id or value["control_plane"] != "AIControlCenter"
            or value["lifecycle"] != "MANAGED_ADAPTER"
            or value["data_deletion_on_detach"] is not False):
        raise PluginManifestError("invalid plugin identity or contract")
    if (not text(value["plugin_version"])
            or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value["plugin_version"]) is None
            or any(not text(value[k]) for k in ("display_name", "purpose", "data_owner", "detach_effect"))):
        raise PluginManifestError("invalid plugin metadata")
    requirements = value["requires"]
    if (type(requirements) is not list or any(type(x) is not str or x not in PLUGIN_IDS or x == plugin_id for x in requirements)
            or len(requirements) != len(set(requirements))):
        raise PluginManifestError("invalid plugin requirements")
    paths = value["source_paths"]
    if type(paths) is not list or not paths or any(not text(x) or x.startswith("/") or ".." in x.split("/") for x in paths):
        raise PluginManifestError("invalid descriptive source paths")
    components = value["components"]
    if type(components) is not list or not components:
        raise PluginManifestError("invalid component list")
    ids = []
    for item in components:
        if (type(item) is not dict or set(item) != {"id", "label", "readiness"}
                or not slug(item["id"]) or not text(item["label"])
                or type(item["readiness"]) is not str or item["readiness"] not in READINESS):
            raise PluginManifestError("invalid component metadata")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise PluginManifestError("duplicate component")
    return deepcopy(value)


def load_catalog(root=ROOT):
    entries = []
    for plugin_id in PLUGIN_IDS:
        try:
            path = Path(root) / plugin_id / "manifest.json"
            value = validate_manifest(json.loads(path.read_text(), object_pairs_hook=_unique), plugin_id)
            value["manifest_status"] = "VALID"
        except (OSError, UnicodeError, ValueError, TypeError, KeyError):
            # Optional metadata failure must not prevent core startup or activate anything.
            value = {"plugin_id": plugin_id, "module_id": plugin_id, "manifest_status": "UNAVAILABLE"}
        entries.append(value)
    return entries


def add_plugin_catalog_route(app, state_reader, *, root=ROOT):
    entries = load_catalog(root)

    @app.get("/platform/plugins")
    def plugins():
        states = {item["module_id"]: item for item in state_reader()}
        result = []
        for entry in entries:
            value = deepcopy(entry)
            state = states.get(entry["module_id"], {})
            value["attachment_state"] = state.get("state", "UNKNOWN")
            value["operational_readiness"] = "NOT_VERIFIED_BY_CATALOG"
            result.append(value)
        return {"schema_version": 1, "platform": "AI Home Datacenter",
                "control_plane": "AIControlCenter", "shared_services": list(CORE_SERVICES),
                "catalog_is_authorization": False, "plugins": result}
