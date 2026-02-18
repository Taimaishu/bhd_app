"""OpenAI provider (cloud)."""
import json
import os
from typing import Any, Dict

from ...core.ports import ILLMPort


class OpenAIProvider(ILLMPort):
    """OpenAI provider using API."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        timeout: int = 60
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")
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
            import openai
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)

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
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # OpenAI has built-in safety, but do basic check
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
        """Check if OpenAI is available."""
        return bool(self.api_key)
