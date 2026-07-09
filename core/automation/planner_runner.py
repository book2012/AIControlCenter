from core.automation.executor import AutomationExecutor


class PlannerAutomationRunner:
    def __init__(self, executor: AutomationExecutor | None = None):
        self.executor = executor or AutomationExecutor()

    def run_plan(self, plan):
        results = []

        for step in plan.get("steps", []):
            action = step.get("action")

            if not action or not action.startswith("/"):
                results.append({
                    "step": step.get("order"),
                    "action": action,
                    "executed": False,
                    "reason": "not_executable_command",
                })
                continue

            results.append({
                "step": step.get("order"),
                **self.executor.execute(action),
            })

        return {
            "plan_id": plan.get("id"),
            "goal": plan.get("goal"),
            "executed_steps": results,
        }
