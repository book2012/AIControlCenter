from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.agent.planner_agent import PlannerAgent
from core.agent.plan_store import PlanStore


router = APIRouter()

planner = PlannerAgent()
store = PlanStore()


class PlanRequest(BaseModel):
    goal: str


@router.post("/planner/plan")
def create_plan(request: PlanRequest):
    plan = planner.create_plan(request.goal)
    return store.save(plan)


@router.get("/planner/plans")
def list_plans():
    return {
        "plans": store.list()
    }


@router.get("/planner/plans/{plan_id}")
def get_plan(plan_id: str):
    try:
        return store.get(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plan not found") from exc
