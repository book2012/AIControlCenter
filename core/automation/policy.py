class SafeExecutionPolicy:
    def __init__(self):
        self.allowed = {
            "/status",
            "/doctor",
            "/scheduler",
            "/memory",
            "/knowledge",
            "/backup verify",
        }

        self.blocked_prefixes = [
            "/backup run",
            "/backup confirm",
            "/backup plan",
        ]

    def check(self, action: str):
        if action in self.allowed:
            return {
                "allowed": True,
                "reason": "allowed_read_only_command",
            }

        for prefix in self.blocked_prefixes:
            if action.startswith(prefix):
                return {
                    "allowed": False,
                    "reason": "blocked_requires_human_confirmation",
                }

        return {
            "allowed": False,
            "reason": "unknown_or_unsafe_command",
        }
