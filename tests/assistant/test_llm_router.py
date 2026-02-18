"""Tests for LLM provider router."""
import pytest

from bhd_cli.assistant.adapters.llm.router import LLMRouter
from bhd_cli.assistant.adapters.llm.mock_provider import MockLLMProvider


def test_router_fallback():
    """Test that router falls back when first provider fails."""
    # Create router with manual provider setup
    router = LLMRouter(provider_order=["mock1", "mock2"])

    # Manually add providers
    router.providers["mock1"] = MockLLMProvider(should_fail=True)
    router.providers["mock2"] = MockLLMProvider(should_fail=False)

    schema = {
        "type": "object",
        "required": ["id", "title"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"}
        }
    }

    result = router.generate_structured("test prompt", schema)

    # Should have used mock2 after mock1 failed
    assert router.get_last_used_provider() == "mock2"
    assert "id" in result


def test_router_no_providers_available():
    """Test router behavior when no providers available."""
    router = LLMRouter(provider_order=["nonexistent"])

    schema = {"type": "object"}

    with pytest.raises(RuntimeError, match="No LLM providers available"):
        router.generate_structured("test prompt", schema)


def test_router_all_providers_fail():
    """Test router behavior when all providers fail."""
    router = LLMRouter(provider_order=["mock1", "mock2"])

    router.providers["mock1"] = MockLLMProvider(should_fail=True)
    router.providers["mock2"] = MockLLMProvider(should_fail=True)

    schema = {"type": "object"}

    with pytest.raises(RuntimeError, match="All LLM providers failed"):
        router.generate_structured("test prompt", schema)


def test_router_provider_order():
    """Test that router respects provider order."""
    router = LLMRouter(provider_order=["mock2", "mock1"])

    router.providers["mock1"] = MockLLMProvider(should_fail=False)
    router.providers["mock2"] = MockLLMProvider(should_fail=False)

    schema = {"type": "object"}

    result = router.generate_structured("test prompt", schema)

    # Should use mock2 first (as specified in order)
    assert router.get_last_used_provider() == "mock2"
