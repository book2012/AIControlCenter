"""Optional assistant plugin; domain imports require no host or HTTP framework."""
PLATFORM_PLUGIN_API = 1

def __getattr__(name):
    if name == "create_personal_assistant_adapter":
        from .adapter import create_personal_assistant_adapter
        return create_personal_assistant_adapter
    raise AttributeError(name)
