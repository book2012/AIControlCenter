"""Optional-package composition. Legacy app and deployment remain unchanged."""
from core.modules.composition import create_module_app, load_selection
from core.modules.plugin_loader import plugin_providers


def create_app(*, manifest_path=None):
    attached = load_selection(manifest_path) if manifest_path is not None else ()
    return create_module_app(attached, providers=plugin_providers(attached))


def create_managed_validation_app(*, manifest_path=None, shopping_bindings=None, personal_assistant_status=None):
    """Explicit validation factory; no live connections or deployment defaults."""
    from core.modules.lifecycle import create_managed_app
    attached = load_selection(manifest_path) if manifest_path is not None else ()
    return create_managed_app(attached, providers=plugin_providers(attached,
        shopping_bindings=shopping_bindings, personal_assistant_status=personal_assistant_status))
