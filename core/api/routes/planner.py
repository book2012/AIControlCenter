from fastapi import APIRouter
from pydantic import BaseModel

from core.agent.planner_agent import PlannerAgent


router = APIRouter()

planner = PlannerAgent()


class PlanRequest(BaseModel):
    goal: str


@router.post("/planner/plan")
def create_plan(request: PlanRequest):
    return planner.create_plan(request.goal)
