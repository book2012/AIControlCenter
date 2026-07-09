from core.commands.router import CommandRouter


class AutomationExecutor:
    def __init__(self):
        self.router = CommandRouter()

    def execute(self, action: str):
        return {
            "action": action,
            "result": self.router.route(action),
            "executed": True,
        }
