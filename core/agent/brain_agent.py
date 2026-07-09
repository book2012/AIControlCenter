from core.memory.conversation import ConversationMemory
from core.providers.manager import ProviderManager


class BrainAgent:
    def __init__(
        self,
        providers: ProviderManager | None = None,
        memory: ConversationMemory | None = None,
    ):
        self.providers = providers or ProviderManager()
        self.memory = memory or ConversationMemory()

    def ask(self, prompt: str, provider: str | None = None):
        return self.providers.chat(
            prompt=prompt,
            provider=provider,
        )

    def ask_with_memory(
        self,
        prompt: str,
        provider: str | None = None,
        session_id: str | None = None,
    ):
        if session_id:
            session = self.memory.get(session_id)
        else:
            session = self.memory.create()

        session.add("user", prompt)

        result = self.ask(prompt, provider=provider)

        content = ""
        if result.get("ok") and result.get("result"):
            content = result["result"].get("content", "")

        session.add("assistant", content)

        return {
            "session": session.to_dict(),
            "response": result,
        }
