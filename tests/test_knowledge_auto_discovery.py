from core.knowledge.index import KnowledgeIndex


def test_knowledge_auto_discovery_has_docs():
    index = KnowledgeIndex()

    discovered = index.discover()

    names = [item["name"] for item in discovered]

    assert "README.md" in names
    assert any(name.endswith(".md") for name in names)


def test_knowledge_index_contains_docs_dir():
    index = KnowledgeIndex()

    result = index.build()

    assert result["documents"] >= 1
