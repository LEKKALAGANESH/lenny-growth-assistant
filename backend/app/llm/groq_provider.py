from typing import Optional
from app.llm.openai_provider import OpenAIProvider

class GroqProvider(OpenAIProvider):
    """
    Groq Cloud LLM provider. Groq's chat completions API is OpenAI-compatible
    (identical request/response schema), so this just reuses OpenAIProvider's
    HTTP logic pointed at Groq's base URL with a Groq model default.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = "llama-3.3-70b-versatile"):
        super().__init__(api_key=api_key, default_model=default_model)
        self.name = "groq"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.env_var_name = "GROQ_API_KEY"

    async def check_health(self):
        status = await super().check_health()
        if status.is_available:
            status.available_models = [self.default_model, "llama-3.1-8b-instant"]
        return status
