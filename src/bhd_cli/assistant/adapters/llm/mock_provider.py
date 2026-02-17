"""Mock LLM provider for testing."""
from typing import Any, Dict

from ...core.ports import ILLMPort


class MockLLMProvider(ILLMPort):
    """Mock LLM provider for testing and development."""

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON output conforming to schema."""
        # Mock implementation returns a minimal valid response
        return {
            "status": "mock_response",
            "message": "This is a mock LLM response",
            "schema_validated": True
        }

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # Mock: Simple blocked keyword check
        blocked_keywords = ["exploit", "attack", "hack", "crack"]
        text_lower = text.lower()
        return not any(keyword in text_lower for keyword in blocked_keywords)


class LLMProviderInterface(ILLMPort):
    """Interface stub for real LLM provider integration."""

    def __init__(self, provider_name: str, api_key: str = None):
        """Initialize LLM provider.

        Args:
            provider_name: Name of provider (e.g., 'anthropic', 'openai')
            api_key: API key for the provider
        """
        self.provider_name = provider_name
        self.api_key = api_key
        # TODO: Initialize actual provider client

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON output conforming to schema."""
        # TODO: Implement actual LLM call with schema validation
        raise NotImplementedError("Real LLM provider not implemented yet")

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # TODO: Implement safety check with LLM provider
        raise NotImplementedError("Safety validation not implemented yet")
