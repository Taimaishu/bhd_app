"""Ollama provider for local LLM inference."""
import json
import os
from typing import Any, Dict, Optional

import requests

from ...core.ports import ILLMPort


class OllamaProvider(ILLMPort):
    """Local Ollama provider using HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:1b",
        timeout: int = 120
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON output conforming to schema."""
        # Build system prompt with schema requirement
        system_prompt = f"""You are a security analysis assistant. You MUST respond with ONLY valid JSON that matches this schema:

{json.dumps(schema, indent=2)}

Rules:
- Output ONLY the JSON object, no markdown, no explanations
- Follow the schema exactly
- All required fields must be present
- Do not include exploit code, payloads, or bypass instructions
- Focus on validation, evidence collection, and risk assessment
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "temperature": temperature,
            "format": "json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            # Parse the response
            response_text = result.get("response", "")
            return json.loads(response_text)

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Ollama response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}")

    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        # Basic safety check - look for obvious weaponized content
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
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
