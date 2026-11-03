"""Optional AIControlCenter plugin; importing starts no services."""
PLATFORM_PLUGIN_API = 1

from .adapter import create_personal_assistant_adapter
