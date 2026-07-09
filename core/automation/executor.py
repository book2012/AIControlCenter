from core.automation.policy import SafeExecutionPolicy
from core.commands.router import CommandRouter


class AutomationExecutor:
    def __init__(
        self,
        router: CommandRouter | None = None,
        policy: SafeExecutionPolicy | None = None,
    ):
        self.router = router or CommandRouter()
        self.policy = policy or SafeExecutionPolicy()

    def execute(self, action: str):
        decision = self.policy.check(action)

        if not decision["allowed"]:
            return {
                "action": action,
                "executed": False,
                "blocked": True,
                "reason": decision["reason"],
            }

        return {
            "action": action,
            "result": self.router.route(action),
            "executed": True,
            "blocked": False,
        }
