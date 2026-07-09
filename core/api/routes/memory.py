from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.memory.manager import MemoryManager


router = APIRouter()

memory = MemoryManager()


class WorkingMemoryRequest(BaseModel):
    key: str
    value: str


class LongTermMemoryRequest(BaseModel):
    content: str
    source: str = "manual"
    metadata: dict = {}


@router.get("/memory")
def memory_status():
    return memory.status()


@router.get("/memory/sessions")
def memory_sessions():
    return {
        "sessions": memory.list_sessions()
    }


@router.get("/memory/sessions/{session_id}")
def memory_session(session_id: str):
    try:
        return memory.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.get("/memory/working")
def working_memory_list():
    return {
        "items": memory.list_working()
    }


@router.get("/memory/working/{key}")
def working_memory_get(key: str):
    item = memory.get_working(key)

    if not item:
        raise HTTPException(status_code=404, detail="Working memory key not found")

    return item


@router.post("/memory/working")
def working_memory_set(request: WorkingMemoryRequest):
    return memory.set_working(
        key=request.key,
        value=request.value,
    )


@router.get("/memory/long-term")
def long_term_list():
    return {
        "items": memory.list_long_term()
    }


@router.get("/memory/long-term/search")
def long_term_search(q: str):
    return {
        "query": q,
        "items": memory.search_long_term(q),
    }


@router.get("/memory/long-term/{item_id}")
def long_term_get(item_id: str):
    item = memory.get_long_term(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Long-term memory item not found")

    return item


@router.post("/memory/long-term")
def long_term_add(request: LongTermMemoryRequest):
    return memory.add_long_term(
        content=request.content,
        source=request.source,
        metadata=request.metadata,
    )
