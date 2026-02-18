"""Anthropic provider (cloud)."""
import json
import os
from typing import Any, Dict

from ...core.ports import ILLMPort


class AnthropicProvider(ILLMPort):
    """Anthropic Claude provider using API."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-3-5-haiku-20241022",
        timeout: int = 60
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (set ANTHROPIC_API_KEY env var)")
        self.model = model
        self.timeout = timeout

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON output conforming to schema."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)

        system_prompt = f"""You are a security analysis assistant. You MUST respond with ONLY valid JSON that matches this schema:

{json.dumps(schema, indent=2)}

Rules:
- Output ONLY the JSON object, no markdown, no explanations
- Follow the schema exactly
- All required fields must be present
- Do not include exploit code, payloads, or bypass instructions
- Focus on validation, evidence collection, and risk assessment
"""

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            return json.loads(content)

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Anthropic response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {e}")

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # Anthropic has built-in safety, but do basic check
        dangerous_patterns = [
            "exploit code",
            "payload generation",
            "bypass authentication",
            "reverse shell",
            "backdoor",
            "malware"
        ]
        text_lower = text.lower()
        return not any(pattern in text_lower for pattern in dangerous_patterns)

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return bool(self.api_key)
