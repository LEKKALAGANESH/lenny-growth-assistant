import asyncio
import time
from typing import List, Optional, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus

class MockLocalProvider(BaseLLMProvider):
    """
    High-fidelity simulated local provider for automated testing and
    zero-dependency evaluation fallback.
    """
    def __init__(self, name: str = "mock", default_model: str = "mock-growth-model"):
        super().__init__(name=name, default_model=default_model)

    def _synthesize_response(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        last_query = messages[-1].content.lower() if messages else ""

        if "founder mode" in last_query or "chesky" in last_query:
            return (
                "According to Brian Chesky on Lenny's Podcast [EP-142 • Brian Chesky @ 00:02:11], "
                "Founder Mode means being deeply involved in the details rather than delegating everything to professional managers. "
                "At Airbnb, Chesky instituted twice-yearly coordinated releases and combined product management with product marketing."
            )
        elif "plg" in last_query or "product-led" in last_query or "elena" in last_query:
            return (
                "As Elena Verna explains in Lenny's Podcast [EP-118 • Elena Verna @ 00:00:36], "
                "Product-Led Growth is not just a freemium pricing tier; it is a go-to-market motion where the product drives acquisition, activation, retention, and monetization."
            )
        elif "high agency" in last_query or "shreyas" in last_query or "lno" in last_query:
            return (
                "Shreyas Doshi discusses High Agency and the LNO Framework in [EP-95 • Shreyas Doshi @ 00:00:41]. "
                "The LNO framework divides tasks into Leverage (10x return), Neutral (diminishing return), and Overhead (maintain baseline), advising PMs to protect 40% of their calendar for Leverage work."
            )
        elif "pmf" in last_query or "sean ellis" in last_query or "north star" in last_query:
            return (
                "Sean Ellis notes in [EP-77 • Sean Ellis @ 00:00:41] that if more than 40% of surveyed users would be 'very disappointed' without the product, you have achieved Product-Market Fit."
            )
        else:
            return (
                "Based on Lenny's Podcast transcripts, here is the grounded synthesis for your inquiry. "
                "The advice emphasizes customer validation, weekly experimentation loops, and product excellence."
            )

    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        content = self._synthesize_response(messages, system_prompt)
        latency = round((time.time() - start_time) * 1000, 2)

        return LLMResponse(
            content=content,
            provider=self.name,
            model=model or self.default_model,
            prompt_tokens=50,
            completion_tokens=len(content.split()),
            latency_ms=latency
        )

    async def stream_generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        content = self._synthesize_response(messages, system_prompt)
        words = content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)

    async def check_health(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            provider=self.name,
            is_available=True,
            status_message="Mock provider ready for offline test/demo mode.",
            available_models=[self.default_model]
        )
