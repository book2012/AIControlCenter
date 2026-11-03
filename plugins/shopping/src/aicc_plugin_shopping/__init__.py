"""Optional shopping plugin. Domain imports require no host or HTTP framework."""
PLATFORM_PLUGIN_API = 1
__all__ = ("create_shopping_preview", "ShoppingBindings", "create_bound_shopping")


def __getattr__(name):
    if name == "create_shopping_preview":
        from .preview import create_shopping_preview
        return create_shopping_preview
    if name in {"ShoppingBindings", "create_bound_shopping"}:
        from .bindings import ShoppingBindings, create_bound_shopping
        return {"ShoppingBindings": ShoppingBindings, "create_bound_shopping": create_bound_shopping}[name]
    if name == "ShoppingService":
        from .catalog_service import ShoppingService
        return ShoppingService
    if name == "CatalogSettings":
        from .catalog_settings import CatalogSettings
        return CatalogSettings
    raise AttributeError(name)
