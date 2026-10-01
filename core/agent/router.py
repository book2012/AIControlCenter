from core.agent.actions.status_action import StatusAction


class AgentActionRouter:
    def __init__(self, actions=None, shopping_tools=None):
        self.actions = actions or [
            StatusAction(),
        ]
        self.shopping_tools = shopping_tools

    def route(self, message: str):
        for action in self.actions:
            if action.matches(message):
                return action.run(message)

        return None

    def route_tool(self, name, arguments):
        if self.shopping_tools is None:
            raise ValueError("agent_shopping_tools_unavailable")
        return self.shopping_tools.invoke(name, arguments)
