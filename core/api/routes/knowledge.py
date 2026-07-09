from fastapi import APIRouter

from core.knowledge.search import KnowledgeSearch


router = APIRouter()

knowledge = KnowledgeSearch()


@router.get("/knowledge")
def knowledge_status():
    return knowledge.status()


@router.get("/knowledge/search")
def knowledge_search(q: str):
    return {
        "query": q,
        "results": knowledge.search(q),
    }
