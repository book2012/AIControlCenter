"""Explicit alternative factory. The legacy app and deployment are unchanged."""
from core.modules.composition import create_module_app, load_selection


def create_app(*, manifest_path=None):
    attached = load_selection(manifest_path) if manifest_path is not None else ()
    providers = {}
    if "shopping" in attached:
        # Import only the selected implementation, never disabled domain code.
        from core.modules.shopping import create_shopping_preview
        providers["shopping"] = create_shopping_preview
    return create_module_app(attached, providers=providers)


def create_managed_validation_app(*, manifest_path=None, shopping_bindings=None, personal_assistant_status=None):
    """Explicit validation factory, not an alternative production launch target."""
    from core.modules.lifecycle import create_managed_app
    attached = load_selection(manifest_path) if manifest_path is not None else ()
    providers = {}
    if "shopping" in attached:
        if shopping_bindings is None:
            from core.modules.shopping import create_shopping_preview
            providers["shopping"] = create_shopping_preview
        else:
            from core.modules.shopping_bindings import create_bound_shopping
            providers["shopping"] = lambda: create_bound_shopping(shopping_bindings)
    if "creative-notes" in attached:
        from core.modules.service_adapters import create_creative_notes_adapter
        providers["creative-notes"] = create_creative_notes_adapter
    if "personal-assistant" in attached:
        from core.modules.service_adapters import create_personal_assistant_adapter
        providers["personal-assistant"] = lambda: create_personal_assistant_adapter(personal_assistant_status)
    return create_managed_app(attached, providers=providers)
