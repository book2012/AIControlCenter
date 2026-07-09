from fastapi import APIRouter
from pydantic import BaseModel

from core.agent.brain_agent import BrainAgent


router = APIRouter()

agent = BrainAgent()


class AskRequest(BaseModel):
    prompt: str
    provider: str | None = None


@router.post("/agents/brain/ask")
def ask_brain(request: AskRequest):
    return agent.ask(
        prompt=request.prompt,
        provider=request.provider,
    )
