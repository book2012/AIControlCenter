from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.providers.manager import ProviderManager


router = APIRouter()

manager = ProviderManager()


class ChatRequest(BaseModel):
    prompt: str


@router.get("/providers")
def providers():
    return manager.health()


@router.get("/providers/{name}")
def provider(name: str):
    try:
        return manager.get(name).health()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.post("/providers/{name}/chat")
def provider_chat(name: str, request: ChatRequest):
    try:
        return manager.get(name).chat(request.prompt)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc
