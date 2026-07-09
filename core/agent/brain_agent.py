from core.agent.router import AgentActionRouter
from core.memory.conversation import ConversationMemory
from core.memory.manager import MemoryManager
from core.knowledge.search import KnowledgeSearch
from core.providers.manager import ProviderManager


class BrainAgent:
    def __init__(
        self,
        providers: ProviderManager | None = None,
        memory: ConversationMemory | None = None,
        router: AgentActionRouter | None = None,
        memory_manager: MemoryManager | None = None,
        knowledge: KnowledgeSearch | None = None,
    ):
        self.providers = providers or ProviderManager()
        self.memory = memory or ConversationMemory()
        self.router = router or AgentActionRouter()
        self.memory_manager = memory_manager or MemoryManager()
        self.knowledge = knowledge or KnowledgeSearch()

    def ask(self, prompt: str, provider: str | None = None):
        action_result = self.router.route(prompt)

        if action_result:
            summary = action_result.get("summary", {})
            content = ""

            if summary.get("ok") and summary.get("result"):
                content = summary["result"].get("content", "")

            return {
                "ok": True,
                "type": "action",
                "action": action_result["action"],
                "content": content,
                "result": action_result,
            }

        return self.providers.chat(
            prompt=prompt,
            provider=provider,
        )

    def ask_with_memory_context(
        self,
        prompt: str,
        provider: str | None = None,
    ):
        memories = self.memory_manager.search_long_term(prompt)

        memory_text = "\n".join(
            f"- {item['content']}"
            for item in memories[:5]
        )

        if memory_text:
            enriched_prompt = (
                "Use the following long-term memory when useful.\n\n"
                f"{memory_text}\n\n"
                f"User question:\n{prompt}"
            )
        else:
            enriched_prompt = prompt

        result = self.ask(enriched_prompt, provider=provider)

        return {
            "prompt": prompt,
            "memory_count": len(memories),
            "response": result,
        }


    def ask_with_knowledge_context(
        self,
        prompt: str,
        provider: str | None = None,
    ):
        docs = self.knowledge.search(prompt)

        context = "\n".join(
            f"- {d['name']}"
            for d in docs[:5]
        )

        enriched = prompt

        if context:
            enriched = (
                "Relevant project knowledge:\n"
                f"{context}\n\n"
                f"{prompt}"
            )

        result = self.ask(enriched, provider=provider)

        return {
            "knowledge_count": len(docs),
            "response": result,
        }

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
        if result.get("ok"):
            if result.get("type") == "action":
                content = result.get("content", "")
            elif result.get("result"):
                content = result["result"].get("content", "")

        session.add("assistant", content)

        return {
            "session": session.to_dict(),
            "response": result,
        }
