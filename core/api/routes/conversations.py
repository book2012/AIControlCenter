from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.agent.brain_agent import BrainAgent


router = APIRouter()

agent = BrainAgent()


class AskRequest(BaseModel):
    prompt: str
    provider: str | None = None


@router.post("/conversations")
def create_conversation():
    session = agent.memory.create()
    return session.to_dict()


@router.get("/conversations")
def list_conversations():
    return {
        "conversations": agent.memory.list()
    }


@router.get("/conversations/{session_id}")
def get_conversation(session_id: str):
    try:
        return agent.memory.get(session_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc


@router.post("/conversations/{session_id}/ask")
def ask_conversation(session_id: str, request: AskRequest):
    try:
        return agent.ask_with_memory(
            prompt=request.prompt,
            provider=request.provider,
            session_id=session_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
