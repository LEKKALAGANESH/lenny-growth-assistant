import time
import json
import httpx
from typing import List, Optional, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus

class OpenAIProvider(BaseLLMProvider):
    """Cloud LLM provider for OpenAI GPT-4o / GPT-4o-mini."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-4o"):
        super().__init__(name="openai", default_model=default_model)
        self.api_key = api_key
        # Subclasses (e.g. GroqProvider) override these to reuse this OpenAI-compatible
        # chat-completions implementation against a different endpoint/provider.
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.env_var_name = "OPENAI_API_KEY"

    def _format_messages(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> List[dict]:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError(f"{self.env_var_name} is not configured in .env")

        start_time = time.time()
        target_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages, system_prompt),
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"{self.name} API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})
            latency = round((time.time() - start_time) * 1000, 2)

            return LLMResponse(
                content=content,
                provider=self.name,
                model=target_model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
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
        if not self.api_key:
            yield f"[Error: {self.env_var_name} is missing. Please configure it in .env or switch to Ollama]"
            return

        target_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages, system_prompt),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", self.base_url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"[{self.name} Error HTTP {resp.status_code}]"
                        return

                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            if raw_json == "[DONE]":
                                break
                            try:
                                event = json.loads(raw_json)
                                delta = event.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    yield token
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield f"[{self.name} connection error: {str(e)}]"

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                provider=self.name,
                is_available=False,
                status_message="API Key not configured."
            )
        return ProviderHealthStatus(
            provider=self.name,
            is_available=True,
            status_message="Configured and ready.",
            available_models=["gpt-4o", "gpt-4o-mini"]
        )
