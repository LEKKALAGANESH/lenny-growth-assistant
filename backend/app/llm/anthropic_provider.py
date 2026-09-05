import time
import json
import httpx
from typing import List, Optional, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus

class AnthropicProvider(BaseLLMProvider):
    """Cloud LLM provider for Anthropic Claude 3.5 Sonnet / Haiku."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(name="anthropic", default_model=default_model)
        self.api_key = api_key

    def _format_messages(self, messages: List[ChatMessage]) -> List[dict]:
        return [{"role": msg.role, "content": msg.content} for msg in messages if msg.role in ["user", "assistant"]]

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
            raise ValueError("ANTHROPIC_API_KEY is not configured in .env")

        start_time = time.time()
        target_model = model or self.default_model
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Anthropic API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            latency = round((time.time() - start_time) * 1000, 2)

            return LLMResponse(
                content=content,
                provider="anthropic",
                model=target_model,
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
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
            yield "[Error: ANTHROPIC_API_KEY is missing. Please configure it in .env or switch to Ollama]"
            return

        target_model = model or self.default_model
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", "https://api.anthropic.com/v1/messages", headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"[Anthropic Error HTTP {resp.status_code}]"
                        return

                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            if raw_json == "[DONE]":
                                break
                            try:
                                event = json.loads(raw_json)
                                if event.get("type") == "content_block_delta":
                                    delta = event.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        yield delta.get("text", "")
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield f"[Anthropic connection error: {str(e)}]"

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                provider="anthropic",
                is_available=False,
                status_message="API Key not configured."
            )
        return ProviderHealthStatus(
            provider="anthropic",
            is_available=True,
            status_message="Configured and ready.",
            available_models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
        )
