from core.agent.router import AgentActionRouter
from core.memory.conversation import ConversationMemory
from core.memory.manager import MemoryManager
from core.knowledge.search import KnowledgeSearch
from core.config.settings import Settings, load_settings
from core.providers import (
    ProviderError,
    ProviderMessage,
    ProviderRequest,
    ProviderRouter,
)
from core.providers.manager import ProviderManager
from core.providers.openai_adapter import OpenAIAdapter


class BrainAgent:
    def __init__(
        self,
        providers: ProviderManager | None = None,
        memory: ConversationMemory | None = None,
        router: AgentActionRouter | None = None,
        memory_manager: MemoryManager | None = None,
        knowledge: KnowledgeSearch | None = None,
        provider_router: ProviderRouter | None = None,
        settings: Settings | None = None,
    ):
        self.providers = providers
        self.settings = settings or load_settings()
        self.provider_router = provider_router or self._default_provider_router()
        self.memory = memory or ConversationMemory()
        self.router = router or AgentActionRouter()
        self.memory_manager = memory_manager or MemoryManager()
        self.knowledge = knowledge or KnowledgeSearch()

    def _default_provider_router(self) -> ProviderRouter:
        router = ProviderRouter()
        router.register(
            OpenAIAdapter(
                credential_lookup=lambda _variable_name: self.settings.openai.api_key,
            )
        )
        return router

    def _provider_model(self, provider: str) -> str:
        models = {
            "openai": self.settings.openai.model,
            "google": self.settings.google.model,
        }
        return models.get(provider, "provider-managed")

    def _invoke_provider(self, prompt: str, provider: str | None) -> dict:
        selected_provider = provider or self.settings.ai.provider
        try:
            response = self.provider_router.invoke(
                ProviderRequest(
                    provider=selected_provider,
                    model=self._provider_model(selected_provider),
                    messages=(ProviderMessage(role="user", content=prompt),),
                )
            )
        except ProviderError as exc:
            return {
                "ok": False,
                "provider": selected_provider,
                "result": None,
                "error": exc.to_dict()["error"],
                "metadata": {
                    "provider": exc.provider,
                    "model": exc.model,
                    "result_class": exc.code.value,
                    "request_id": exc.provider_request_id,
                },
                "attempts": [exc.audit_metadata()],
            }

        normalized = response.to_dict()
        return {
            "ok": True,
            "provider": response.provider,
            "result": normalized,
            "metadata": {
                "provider": response.provider,
                "model": response.model,
                "result_class": "provider_response",
                "request_id": response.provider_request_id,
            },
            "attempts": [response.audit_metadata()],
        }

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

        if self.providers is not None:
            return self.providers.chat(prompt=prompt, provider=provider)

        return self._invoke_provider(prompt, provider)

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
