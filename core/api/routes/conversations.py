from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.agent.brain_agent import BrainAgent
from core.memory.sqlite_store import SQLiteConversationStore


router = APIRouter()

agent = BrainAgent()
store = SQLiteConversationStore()


class AskRequest(BaseModel):
    prompt: str
    provider: str | None = None


@router.post("/conversations")
def create_conversation():
    return store.create_session()


@router.get("/conversations")
def list_conversations():
    return {
        "conversations": store.list_sessions()
    }


@router.get("/conversations/{session_id}")
def get_conversation(session_id: str):
    try:
        return store.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc


@router.post("/conversations/{session_id}/ask")
def ask_conversation(session_id: str, request: AskRequest):
    try:
        session = store.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc

    store.add_message(session["id"], "user", request.prompt)

    response = agent.ask(
        prompt=request.prompt,
        provider=request.provider,
    )

    content = ""
    if response.get("ok") and response.get("result"):
        content = response["result"].get("content", "")

    store.add_message(session["id"], "assistant", content)

    return {
        "session": store.get_session(session["id"]),
        "response": response,
    }
