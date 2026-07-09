from core.knowledge.search import KnowledgeSearch


def test_knowledge_search():
    search = KnowledgeSearch()

    results = search.search("AIControlCenter")

    assert isinstance(results, list)


def test_knowledge_search_status():
    search = KnowledgeSearch()

    status = search.status()

    assert status["ready"] is True
    assert status["documents"] >= 1
