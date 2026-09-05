from typing import Dict, List, Optional, AsyncGenerator
from app.core.config import settings
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus
from app.llm.ollama_provider import OllamaProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.groq_provider import GroqProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.mock_provider import MockLocalProvider

class LLMManager:
    """
    Central LLM Orchestration Gateway.
    Handles dynamic model selection, multi-provider registration,
    runtime switching, health diagnostics, and resilient fallback execution.
    """
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        # Local Ollama Provider (Default for submission demo)
        self._providers["ollama"] = OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            default_model=settings.OLLAMA_MODEL
        )

        # Anthropic Cloud Provider
        self._providers["anthropic"] = AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY
        )

        # OpenAI Cloud Provider
        self._providers["openai"] = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY
        )

        # Groq Cloud Provider (OpenAI-compatible, used as fallback #1)
        self._providers["groq"] = GroqProvider(
            api_key=settings.GROQ_API_KEY
        )

        # Gemini Cloud Provider (used as fallback #2)
        self._providers["gemini"] = GeminiProvider(
            api_key=settings.GEMINI_API_KEY
        )

        # Mock / Test Provider
        self._providers["mock"] = MockLocalProvider()

    def register_provider(self, name: str, provider: BaseLLMProvider) -> None:
        self._providers[name.lower()] = provider

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        target = (name or settings.DEFAULT_LLM_PROVIDER).lower()
        if target in self._providers:
            return self._providers[target]
        # Fallback to default or mock
        return self._providers.get("ollama", self._providers["mock"])

    async def list_providers_status(self) -> List[ProviderHealthStatus]:
        statuses = []
        for name, provider in self._providers.items():
            try:
                status = await provider.check_health()
                statuses.append(status)
            except Exception as e:
                statuses.append(
                    ProviderHealthStatus(
                        provider=name,
                        is_available=False,
                        status_message=f"Healthcheck error: {str(e)}"
                    )
                )
        return statuses

    async def generate_with_fallback(
        self,
        preferred_provider: Optional[str],
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Executes generation with automatic fallback to alternate provider
        if the primary provider is unreachable or throws an error.
        """
        provider_name = (preferred_provider or settings.LLM_PROVIDER or settings.DEFAULT_LLM_PROVIDER).lower()

        # OpenAI -> Groq -> Gemini automatic fallback chain: only engaged when the caller
        # is targeting "openai" (explicitly, or via LLM_PROVIDER/DEFAULT_LLM_PROVIDER), so
        # the pre-existing ollama/anthropic single-hop fallback below is untouched.
        if provider_name == "openai":
            chain = ["openai"] + [
                p.strip().lower() for p in settings.LLM_FALLBACK_ORDER.split(",") if p.strip()
            ]
            last_err: Optional[Exception] = None
            for hop_index, hop_name in enumerate(chain):
                hop_provider = self.get_provider(hop_name)
                try:
                    resp = await hop_provider.generate(
                        messages=messages,
                        system_prompt=system_prompt,
                        model=model if hop_index == 0 else None,
                        **kwargs
                    )
                    if hop_index > 0:
                        resp.is_fallback = True
                        resp.fallback_reason = (
                            f"Primary provider 'openai' failed: {last_err}. "
                            f"Gracefully routed to fallback '{hop_name}'."
                        )
                    return resp
                except Exception as hop_err:
                    last_err = hop_err
                    continue
            # Entire chain exhausted: last-resort mock fallback (mirrors the safety net
            # the ollama/anthropic path below already relies on).
            resp = await self.get_provider("mock").generate(
                messages=messages, system_prompt=system_prompt, **kwargs
            )
            resp.is_fallback = True
            resp.fallback_reason = (
                f"All providers in fallback chain {chain} failed: {last_err}. "
                f"Gracefully routed to fallback 'mock'."
            )
            return resp

        primary_provider = self.get_provider(provider_name)

        try:
            return await primary_provider.generate(
                messages=messages,
                system_prompt=system_prompt,
                model=model,
                **kwargs
            )
        except Exception as primary_err:
            # Determine fallback candidate
            fallback_name = "mock"
            if provider_name == "ollama" and settings.ANTHROPIC_API_KEY:
                fallback_name = "anthropic"
            elif provider_name == "anthropic" and settings.OPENAI_API_KEY:
                fallback_name = "openai"

            fallback_provider = self.get_provider(fallback_name)
            resp = await fallback_provider.generate(
                messages=messages,
                system_prompt=system_prompt,
                **kwargs
            )
            resp.is_fallback = True
            resp.fallback_reason = (
                f"Primary provider '{provider_name}' failed: {str(primary_err)}. "
                f"Gracefully routed to fallback '{fallback_name}'."
            )
            return resp

    async def stream_with_fallback(
        self,
        preferred_provider: Optional[str],
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streams token generation with graceful fallback error reporting.
        """
        provider_name = (preferred_provider or settings.DEFAULT_LLM_PROVIDER).lower()
        primary_provider = self.get_provider(provider_name)

        health = await primary_provider.check_health()
        if not health.is_available:
            # Yield helpful diagnostic message, then stream from mock fallback
            yield f"[Notice: Provider '{provider_name}' is offline ({health.status_message}). Routing to fallback engine...]\n\n"
            fallback_provider = self.get_provider("mock")
            async for token in fallback_provider.stream_generate(messages, system_prompt, **kwargs):
                yield token
            return

        async for token in primary_provider.stream_generate(messages, system_prompt, model=model, **kwargs):
            yield token

# Global singleton instance
llm_manager = LLMManager()
