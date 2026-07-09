from fastapi import APIRouter, HTTPException

from core.memory.manager import MemoryManager


router = APIRouter()

memory = MemoryManager()


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
