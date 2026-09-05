import time
import json
import httpx
from typing import List, Optional, AsyncGenerator
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse, ProviderHealthStatus

class OllamaProvider(BaseLLMProvider):
    """
    Local LLM Provider for Ollama.
    Mandatory for local demo and offline evaluation.
    """
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.2"):
        super().__init__(name="ollama", default_model=default_model)
        self.base_url = base_url.rstrip("/")

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
        start_time = time.time()
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages, system_prompt),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

                data = resp.json()
                content = data.get("message", {}).get("content", "")
                latency = round((time.time() - start_time) * 1000, 2)

                return LLMResponse(
                    content=content,
                    provider="ollama",
                    model=target_model,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    latency_ms=latency
                )
        except Exception as e:
            raise RuntimeError(f"Failed connecting to local Ollama at {self.base_url}: {str(e)}")

    async def stream_generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": self._format_messages(messages, system_prompt),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        yield f"[Error: Ollama HTTP {response.status_code}]"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_data = json.loads(line)
                            token = chunk_data.get("message", {}).get("content", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"[Connection error to local Ollama: {str(e)}]"

    async def check_health(self) -> ProviderHealthStatus:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    models_data = resp.json().get("models", [])
                    model_names = [m.get("name", "") for m in models_data]
                    return ProviderHealthStatus(
                        provider="ollama",
                        is_available=True,
                        status_message="Local Ollama is running and responsive.",
                        available_models=model_names,
                        latency_ms=latency
                    )
                return ProviderHealthStatus(
                    provider="ollama",
                    is_available=False,
                    status_message=f"Ollama returned HTTP {resp.status_code}",
                    latency_ms=latency
                )
        except Exception as e:
            return ProviderHealthStatus(
                provider="ollama",
                is_available=False,
                status_message=f"Ollama offline at {self.base_url}. (Run 'ollama serve' or start Docker)",
                latency_ms=0.0
            )
