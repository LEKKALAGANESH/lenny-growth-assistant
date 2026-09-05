import time
import json
import httpx
from typing import List, Optional, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus

class GeminiProvider(BaseLLMProvider):
    """Cloud LLM provider for Google Gemini (Generative Language API)."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-flash-latest"):
        super().__init__(name="gemini", default_model=default_model)
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _format_contents(self, messages: List[ChatMessage]) -> List[dict]:
        # Gemini uses "user"/"model" roles and a "parts" list instead of OpenAI's
        # "user"/"assistant" + plain "content" string.
        contents = []
        for msg in messages:
            if msg.role not in ("user", "assistant"):
                continue
            role = "model" if msg.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        return contents

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
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        start_time = time.time()
        target_model = model or self.default_model
        url = f"{self.base_url}/{target_model}:generateContent?key={self.api_key}"
        payload = {
            "contents": self._format_contents(messages),
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"gemini API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            candidates = data.get("candidates", [])
            content = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                content = "".join(p.get("text", "") for p in parts)

            usage = data.get("usageMetadata", {})
            latency = round((time.time() - start_time) * 1000, 2)

            # Normalized to the exact same LLMResponse shape every other provider returns.
            return LLMResponse(
                content=content,
                provider="gemini",
                model=target_model,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
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
            yield "[Error: GEMINI_API_KEY is missing. Please configure it in .env or switch to Ollama]"
            return

        target_model = model or self.default_model
        url = f"{self.base_url}/{target_model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = {
            "contents": self._format_contents(messages),
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code != 200:
                        yield f"[gemini Error HTTP {resp.status_code}]"
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        raw_json = line[6:].strip()
                        try:
                            event = json.loads(raw_json)
                            candidates = event.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                token = "".join(p.get("text", "") for p in parts)
                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"[gemini connection error: {str(e)}]"

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                provider="gemini",
                is_available=False,
                status_message="API Key not configured."
            )
        return ProviderHealthStatus(
            provider="gemini",
            is_available=True,
            status_message="Configured and ready.",
            available_models=["gemini-flash-latest", "gemini-2.5-pro"]
        )
