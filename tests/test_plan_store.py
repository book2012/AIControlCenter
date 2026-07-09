from core.agent.planner_agent import PlannerAgent
from core.agent.plan_store import PlanStore


def test_plan_store_save_get():
    store = PlanStore()
    plan = PlannerAgent().create_plan("Check status")

    store.save(plan)

    assert store.get(plan["id"])["goal"] == "Check status"


def test_plan_store_list():
    store = PlanStore()
    plan = PlannerAgent().create_plan("Check status")

    store.save(plan)

    assert len(store.list()) == 1
