class PlanStore:
    def __init__(self):
        self.plans = {}

    def save(self, plan):
        self.plans[plan["id"]] = plan
        return plan

    def get(self, plan_id: str):
        return self.plans[plan_id]

    def list(self):
        return list(self.plans.values())
