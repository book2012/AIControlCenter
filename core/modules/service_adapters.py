"""Compatibility facades; no optional plugin is imported until requested."""
def create_creative_notes_adapter():
    from aicc_plugin_creative_notes import create_creative_notes_adapter as factory
    return factory()


def create_personal_assistant_adapter(status_service=None):
    from aicc_plugin_personal_assistant import create_personal_assistant_adapter as factory
    return factory(status_service)


def __getattr__(name):
    if name in {"CREATIVE_NOTES_URL", "CREATIVE_NOTES_PROJECT"}:
        from aicc_plugin_creative_notes import adapter
        return getattr(adapter, name)
    raise AttributeError(name)
