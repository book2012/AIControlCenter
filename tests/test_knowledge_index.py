from core.knowledge.index import KnowledgeIndex


def test_knowledge_index_build():
    index = KnowledgeIndex()

    result = index.build()

    assert result["documents"] >= 1
    assert "README.md" in result["items"]


def test_knowledge_index_status():
    index = KnowledgeIndex()

    index.build()
    status = index.status()

    assert status["ready"] is True
    assert status["documents"] >= 1
