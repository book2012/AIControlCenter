"""Compatibility facade for the optional shopping plugin package."""
def create_shopping_preview():
    from aicc_plugin_shopping import create_shopping_preview as factory
    return factory()
