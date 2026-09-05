import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.llm.base import ChatMessage
from app.llm.manager import LLMManager
from app.core.config import settings


def _make_manager_with_failing_openai(monkeypatch, also_fail_groq: bool = False):
    """Builds a fresh LLMManager and monkeypatches provider.generate() so specific
    hops raise or succeed, without hitting any live API or requiring real keys."""
    from app.llm.base import LLMResponse
    manager = LLMManager()

    async def failing_generate(*args, **kwargs):
        raise RuntimeError("simulated provider failure")

    def make_ok_generate(provider_name):
        async def ok_generate(*args, **kwargs):
            return LLMResponse(content="ok", provider=provider_name, model="test-model")
        return ok_generate

    manager.get_provider("openai").generate = failing_generate
    if also_fail_groq:
        manager.get_provider("groq").generate = failing_generate
    else:
        manager.get_provider("groq").generate = make_ok_generate("groq")
    manager.get_provider("gemini").generate = make_ok_generate("gemini")
    return manager


@pytest.mark.anyio
async def test_groq_fallback_triggers_when_openai_fails(monkeypatch):
    manager = _make_manager_with_failing_openai(monkeypatch)
    messages = [ChatMessage(role="user", content="What is Founder Mode?")]

    resp = await manager.generate_with_fallback(preferred_provider="openai", messages=messages)

    assert resp.is_fallback is True
    assert resp.provider == "groq"


@pytest.mark.anyio
async def test_gemini_fallback_triggers_when_openai_and_groq_fail(monkeypatch):
    manager = _make_manager_with_failing_openai(monkeypatch, also_fail_groq=True)
    messages = [ChatMessage(role="user", content="What is Founder Mode?")]

    resp = await manager.generate_with_fallback(preferred_provider="openai", messages=messages)

    assert resp.is_fallback is True
    assert resp.provider == "gemini"


@pytest.mark.anyio
async def test_fallback_order_respects_llm_fallback_order_setting(monkeypatch):
    # Reverse the order: gemini before groq. Both groq and gemini would succeed if
    # called, so the response provider tells us which one the chain tried first.
    monkeypatch.setattr(settings, "LLM_FALLBACK_ORDER", "gemini,groq")
    manager = _make_manager_with_failing_openai(monkeypatch, also_fail_groq=False)
    messages = [ChatMessage(role="user", content="What is Founder Mode?")]

    resp = await manager.generate_with_fallback(preferred_provider="openai", messages=messages)

    assert resp.provider == "gemini"


@pytest.mark.anyio
async def test_openai_primary_used_when_it_succeeds(monkeypatch):
    manager = LLMManager()

    from app.llm.base import LLMResponse

    async def fake_generate(*args, **kwargs):
        return LLMResponse(content="ok", provider="openai", model="gpt-4o")

    manager.get_provider("openai").generate = fake_generate
    messages = [ChatMessage(role="user", content="hi")]

    resp = await manager.generate_with_fallback(preferred_provider="openai", messages=messages)

    assert resp.provider == "openai"
    assert resp.is_fallback is False
