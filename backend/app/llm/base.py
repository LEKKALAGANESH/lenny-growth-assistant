from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProviderHealthStatus(BaseModel):
    provider: str
    is_available: bool
    status_message: str
    available_models: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers (Ollama, Anthropic, OpenAI, Local)."""

    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generates a complete single response."""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streams token chunks asynchronously."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealthStatus:
        """Checks if the provider is reachable and active."""
        pass
