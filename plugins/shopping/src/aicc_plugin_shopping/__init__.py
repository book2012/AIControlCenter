"""Optional AIControlCenter plugin; importing starts no services."""
PLATFORM_PLUGIN_API = 1

from .preview import create_shopping_preview
from .bindings import ShoppingBindings, create_bound_shopping
