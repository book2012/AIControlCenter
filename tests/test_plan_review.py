from core.agent.planner_agent import PlannerAgent
from core.agent.plan_review import PlanReviewService


def test_plan_review_approved():
    plan = PlannerAgent().create_plan("Check system status")
    review = PlanReviewService().review(plan)

    assert review["status"] == "approved"
    assert review["executable"] is True


def test_plan_review_format_text():
    plan = PlannerAgent().create_plan("Check system status")
    text = PlanReviewService().format_text(plan)

    assert "Plan Review" in text
    assert "Executable" in text
