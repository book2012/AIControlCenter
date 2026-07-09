from core.automation.policy import SafeExecutionPolicy


class AutomationExecutor:
    def __init__(
        self,
        router=None,
        policy: SafeExecutionPolicy | None = None,
    ):
        self.router = router
        self.policy = policy or SafeExecutionPolicy()

    def _router(self):
        if self.router is None:
            from core.commands.router import CommandRouter
            self.router = CommandRouter()
        return self.router

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
            "result": self._router().route(action),
            "executed": True,
            "blocked": False,
        }
