from core.agent.planner_agent import PlannerAgent
from core.automation.planner_runner import PlannerAutomationRunner


def test_planner_automation_runner():
    plan = PlannerAgent().create_plan("Check status")

    result = PlannerAutomationRunner().run_plan(plan)

    assert result["plan_id"] == plan["id"]
    assert len(result["executed_steps"]) >= 1
