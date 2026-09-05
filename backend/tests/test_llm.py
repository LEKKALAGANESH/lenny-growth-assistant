import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.llm.base import ChatMessage
from app.llm.mock_provider import MockLocalProvider
from app.llm.manager import LLMManager

@pytest.mark.anyio
async def test_mock_provider_generate():
    provider = MockLocalProvider()
    messages = [ChatMessage(role="user", content="What is Founder Mode according to Brian Chesky?")]
    response = await provider.generate(messages)
    
    assert response.content is not None
    assert "Brian Chesky" in response.content
    assert "Founder Mode" in response.content
    assert response.provider == "mock"
    assert response.latency_ms >= 0

@pytest.mark.anyio
async def test_mock_provider_streaming():
    provider = MockLocalProvider()
    messages = [ChatMessage(role="user", content="Explain Elena Verna PLG frameworks")]
    
    chunks = []
    async for chunk in provider.stream_generate(messages):
        chunks.append(chunk)
        
    full_text = "".join(chunks)
    assert len(chunks) > 1
    assert "Elena Verna" in full_text
    assert "Product-Led Growth" in full_text

@pytest.mark.anyio
async def test_llm_manager_get_and_register():
    manager = LLMManager()
    
    mock_prov = manager.get_provider("mock")
    assert mock_prov.name == "mock"

    custom_mock = MockLocalProvider(name="custom_test")
    manager.register_provider("custom_test", custom_mock)
    assert manager.get_provider("custom_test").name == "custom_test"

@pytest.mark.anyio
async def test_llm_manager_fallback_on_error():
    manager = LLMManager()
    messages = [ChatMessage(role="user", content="What did Shreyas Doshi say about High Agency?")]
    
    # Requesting a provider that fails (e.g. anthropic when key is missing) should fallback gracefully
    response = await manager.generate_with_fallback(
        preferred_provider="anthropic",
        messages=messages
    )
    assert response.content is not None
    assert "Shreyas Doshi" in response.content or "High Agency" in response.content
    assert response.is_fallback is True
    assert "Gracefully routed to fallback" in (response.fallback_reason or "")

@pytest.mark.anyio
async def test_llm_manager_stream_fallback():
    manager = LLMManager()
    messages = [ChatMessage(role="user", content="What is the Sean Ellis PMF survey rule?")]
    
    stream_output = []
    async for chunk in manager.stream_with_fallback(preferred_provider="anthropic", messages=messages):
        stream_output.append(chunk)
        
    full_stream = "".join(stream_output)
    assert len(stream_output) > 0
    assert "Notice: Provider 'anthropic' is offline" in full_stream or "Sean Ellis" in full_stream

@pytest.mark.anyio
async def test_provider_health_check():
    manager = LLMManager()
    statuses = await manager.list_providers_status()
    
    assert len(statuses) >= 3
    provider_names = [s.provider for s in statuses]
    assert "ollama" in provider_names
    assert "anthropic" in provider_names
    assert "mock" in provider_names
