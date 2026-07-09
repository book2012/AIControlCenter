from uuid import uuid4


class PlannerAgent:
    def create_plan(self, goal: str):
        steps = [
            {
                "order": 1,
                "name": "Understand goal",
                "action": "analyze",
                "status": "pending",
            },
            {
                "order": 2,
                "name": "Check current system state",
                "action": "/status",
                "status": "pending",
            },
            {
                "order": 3,
                "name": "Prepare execution strategy",
                "action": "plan",
                "status": "pending",
            },
        ]

        return {
            "id": str(uuid4()),
            "goal": goal,
            "status": "draft",
            "steps": steps,
            "executable": False,
        }
