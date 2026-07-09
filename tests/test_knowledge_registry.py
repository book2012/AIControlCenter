from core.knowledge.registry import KnowledgeRegistry


def test_registry_register():
    registry = KnowledgeRegistry()

    registry.register("README", "README.md")

    assert registry.count() == 1


def test_registry_status():
    registry = KnowledgeRegistry()

    registry.register("README", "README.md")

    status = registry.status()

    assert status["documents"] == 1


def test_registry_unregister():
    registry = KnowledgeRegistry()

    registry.register("README", "README.md")
    registry.unregister("README")

    assert registry.count() == 0
