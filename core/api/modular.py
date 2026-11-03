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
