from fastapi import APIRouter
from app.core.config import settings
from app.llm.manager import llm_manager

router = APIRouter(prefix="/models", tags=["Model Intelligence"])

@router.get("")
async def list_models():
    """
    Lists available LLM providers, model options, active health status,
    and system defaults.
    """
    statuses = await llm_manager.list_providers_status()
    
    return {
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "default_model": settings.OLLAMA_MODEL,
        "providers": [s.model_dump() for s in statuses],
        "supported_providers": [
            {
                "id": "ollama",
                "label": "Ollama (Local LLM - Offline / Demo)",
                "description": "Local zero-cost privacy-first inference running on your machine.",
                "models": ["llama3.2", "mistral", "qwen2.5", "llama3"]
            },
            {
                "id": "anthropic",
                "label": "Anthropic Claude (Cloud)",
                "description": "State-of-the-art reasoning for complex growth synthesis.",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            },
            {
                "id": "openai",
                "label": "OpenAI GPT-4o (Cloud)",
                "description": "High-throughput multimodal frontier model. Default primary provider.",
                "models": ["gpt-4o", "gpt-4o-mini"]
            },
            {
                "id": "groq",
                "label": "Groq (Cloud - Fast Inference)",
                "description": "OpenAI-compatible ultra-low-latency inference. Automatic fallback #1 if OpenAI is unavailable.",
                "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
            },
            {
                "id": "gemini",
                "label": "Google Gemini (Cloud)",
                "description": "Google's frontier multimodal model. Automatic fallback #2 if OpenAI and Groq are unavailable.",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash"]
            }
        ]
    }
