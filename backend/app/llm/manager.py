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

    # Default cascade used when the requested provider isn't "openai" (which uses
    # settings.LLM_FALLBACK_ORDER instead) or has no chain of its own configured.
    # "mock" is always appended as the guaranteed last resort if missing.
    DEFAULT_CHAIN_ORDER = ["openai", "groq", "gemini", "anthropic", "ollama"]

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

    def _build_chain(self, preferred_provider: Optional[str]) -> List[str]:
        """
        Builds the full ordered fallback chain for a requested provider: the
        requested provider first, then every other registered provider as a
        cascading safety net, always ending in "mock" as the guaranteed
        last resort. This is what makes "all providers auto-recover when
        down" true regardless of which provider the user picked.
        """
        provider_name = (preferred_provider or settings.LLM_PROVIDER or settings.DEFAULT_LLM_PROVIDER).lower()

        if provider_name == "openai":
            rest = [p.strip().lower() for p in settings.LLM_FALLBACK_ORDER.split(",") if p.strip()]
        else:
            rest = [p for p in self.DEFAULT_CHAIN_ORDER if p != provider_name]

        chain = [provider_name] + [p for p in rest if p != provider_name and p in self._providers]
        if provider_name not in self._providers:
            # Unknown provider name: still try it first (get_provider() falls back to
            # ollama/mock internally), then run the full default cascade behind it.
            chain = [provider_name] + [p for p in self.DEFAULT_CHAIN_ORDER if p in self._providers]
        if "mock" not in chain:
            chain.append("mock")
        return chain

    async def generate_with_fallback(
        self,
        preferred_provider: Optional[str],
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Executes generation against the requested provider, automatically
        cascading through every remaining provider (ending in mock) if it's
        unreachable, rate-limited, or errors out.
        """
        chain = self._build_chain(preferred_provider)
        requested = chain[0]
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
                        f"Primary provider '{requested}' failed: {last_err}. "
                        f"Gracefully routed to fallback '{hop_name}' (hop {hop_index + 1}/{len(chain)})."
                    )
                return resp
            except Exception as hop_err:
                last_err = hop_err
                continue

        # Unreachable in practice: "mock" never raises, so the loop always returns above.
        raise last_err or RuntimeError("All LLM providers exhausted with no error captured.")

    async def stream_with_fallback(
        self,
        preferred_provider: Optional[str],
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        result_meta: Optional[dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streams token generation from the first healthy provider in the full
        fallback chain, so an offline/down provider is skipped automatically
        instead of only falling back once to mock.

        If `result_meta` is passed, it's populated in-place with
        {"provider": <hop actually used>, "is_fallback": bool, "requested_provider": <original>}
        once resolved, so callers (e.g. the SSE endpoint) can report the real
        serving provider back to the client after the stream completes.
        """
        chain = self._build_chain(preferred_provider)
        requested = chain[0]
        requested_status_message = ""

        for hop_index, hop_name in enumerate(chain):
            hop_provider = self.get_provider(hop_name)
            health = await hop_provider.check_health()
            if not health.is_available:
                if hop_index == 0:
                    requested_status_message = health.status_message
                continue

            if result_meta is not None:
                result_meta["provider"] = hop_name
                result_meta["is_fallback"] = hop_index > 0
                result_meta["requested_provider"] = requested

            if hop_index > 0:
                yield (
                    f"[Notice: Provider '{requested}' is offline ({requested_status_message}). "
                    f"Routed to fallback '{hop_name}'.]\n\n"
                )

            async for token in hop_provider.stream_generate(
                messages, system_prompt, model=model if hop_index == 0 else None, **kwargs
            ):
                yield token
            return

        # Every provider reported unhealthy (should not happen since mock is always
        # available) — stream from mock as the unconditional last resort.
        if result_meta is not None:
            result_meta["provider"] = "mock"
            result_meta["is_fallback"] = True
            result_meta["requested_provider"] = requested
        async for token in self.get_provider("mock").stream_generate(messages, system_prompt, **kwargs):
            yield token

# Global singleton instance
llm_manager = LLMManager()
