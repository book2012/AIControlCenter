"""Explicit optional-package bindings; never execute manifest-provided code paths."""
from importlib import import_module
from .composition import ModuleConfigurationError, resolve_selection

PACKAGES = {
    "shopping": "aicc_plugin_shopping",
    "creative-notes": "aicc_plugin_creative_notes",
    "personal-assistant": "aicc_plugin_personal_assistant",
}


def plugin_providers(attached, *, shopping_bindings=None, personal_assistant_status=None):
    selected = resolve_selection(attached)
    providers = {}
    for plugin_id in selected:
        def factory(plugin_id=plugin_id):
            # Import only inside the lifecycle-managed factory. Missing/incompatible
            # packages fail this plugin, without preventing core/other plugins.
            package = import_module(PACKAGES[plugin_id])
            if type(getattr(package, "PLATFORM_PLUGIN_API", None)) is not int or package.PLATFORM_PLUGIN_API != 1:
                raise ModuleConfigurationError("incompatible platform plugin API")
            if plugin_id == "shopping":
                return (package.create_shopping_preview() if shopping_bindings is None
                        else package.create_bound_shopping(shopping_bindings))
            if plugin_id == "creative-notes":
                return package.create_creative_notes_adapter()
            return package.create_personal_assistant_adapter(personal_assistant_status)
        providers[plugin_id] = factory
    return providers
