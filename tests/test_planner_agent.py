from core.agent.planner_agent import PlannerAgent


def test_planner_agent_create_plan():
    planner = PlannerAgent()

    plan = planner.create_plan("Check AIControlCenter status")

    assert plan["goal"] == "Check AIControlCenter status"
    assert plan["status"] == "draft"
    assert plan["executable"] is False
    assert len(plan["steps"]) >= 1
