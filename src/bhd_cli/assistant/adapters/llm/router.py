"""LLM provider router with fallback logic."""
import logging
from typing import Any, Dict, List, Optional

from ...core.ports import ILLMPort
from .ollama import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


logger = logging.getLogger(__name__)


class LLMRouter(ILLMPort):
    """Routes LLM requests with fallback support."""

    def __init__(self, provider_order: Optional[List[str]] = None):
        """
        Initialize router with provider order.

        Args:
            provider_order: List of provider names in order of preference
                          Default: ["ollama", "openai", "anthropic"]
        """
        self.provider_order = provider_order or ["ollama", "openai", "anthropic"]
        self.providers: Dict[str, ILLMPort] = {}
        self.last_used_provider: Optional[str] = None

        # Initialize providers
        self._init_providers()

    def _init_providers(self):
        """Initialize available providers."""
        # Try Ollama (local)
        try:
            ollama = OllamaProvider()
            if ollama.is_available():
                self.providers["ollama"] = ollama
                logger.info("Ollama provider initialized")
        except Exception as e:
            logger.debug(f"Ollama provider not available: {e}")

        # Try OpenAI (cloud)
        try:
            openai = OpenAIProvider()
            if openai.is_available():
                self.providers["openai"] = openai
                logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.debug(f"OpenAI provider not available: {e}")

        # Try Anthropic (cloud)
        try:
            anthropic = AnthropicProvider()
            if anthropic.is_available():
                self.providers["anthropic"] = anthropic
                logger.info("Anthropic provider initialized")
        except Exception as e:
            logger.debug(f"Anthropic provider not available: {e}")

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON with fallback support."""
        last_error = None

        for provider_name in self.provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                logger.debug(f"Provider {provider_name} not available, skipping")
                continue

            try:
                logger.info(f"Attempting generation with {provider_name}")
                result = provider.generate_structured(prompt, schema, temperature)
                self.last_used_provider = provider_name
                logger.info(f"Successfully generated with {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                last_error = e
                continue

        # All providers failed
        if last_error:
            raise RuntimeError(
                f"All LLM providers failed. Last error: {last_error}"
            )
        else:
            raise RuntimeError(
                "No LLM providers available. Configure at least one of: "
                "Ollama (local), OpenAI API key, or Anthropic API key"
            )

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # Use first available provider for safety check
        for provider_name in self.provider_order:
            provider = self.providers.get(provider_name)
            if provider:
                return provider.validate_safety(text)
        return True  # If no provider available, allow (policy guard will still check)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())

    def get_last_used_provider(self) -> Optional[str]:
        """Get name of last successfully used provider."""
        return self.last_used_provider
