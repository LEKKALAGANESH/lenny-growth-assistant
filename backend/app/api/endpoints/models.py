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
                "description": "High-throughput multimodal frontier model.",
                "models": ["gpt-4o", "gpt-4o-mini"]
            }
        ]
    }
