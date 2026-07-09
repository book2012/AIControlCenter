from core.agent.actions.status_action import StatusAction


class AgentActionRouter:
    def __init__(self, actions=None):
        self.actions = actions or [
            StatusAction(),
        ]

    def route(self, message: str):
        for action in self.actions:
            if action.matches(message):
                return action.run(message)

        return None
