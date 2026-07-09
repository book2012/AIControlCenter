from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.automation.queue import AutomationQueue


router = APIRouter()

queue = AutomationQueue()


class AutomationRequest(BaseModel):
    action: str


@router.get("/automation")
def list_automation():
    return {
        "items": queue.list()
    }


@router.post("/automation")
def submit_automation(request: AutomationRequest):
    item = queue.submit(request.action)
    return queue.run(item["id"])


@router.get("/automation/{item_id}")
def get_automation(item_id: str):
    try:
        return queue.get(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Automation item not found") from exc
