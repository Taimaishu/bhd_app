"""Mock LLM provider for testing."""
import json
from typing import Any, Dict

from ...core.ports import ILLMPort


class MockLLMProvider(ILLMPort):
    """Mock provider that returns deterministic responses for testing."""

    def __init__(self, should_fail: bool = False, fail_attempts: int = 0):
        self.should_fail = should_fail
        self.fail_attempts = fail_attempts
        self.attempt_count = 0
        self.last_prompt = None
        self.last_schema = None

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate mock structured output."""
        self.last_prompt = prompt
        self.last_schema = schema
        self.attempt_count += 1

        # Simulate failures for first N attempts
        if self.attempt_count <= self.fail_attempts:
            raise ValueError(f"Mock failure (attempt {self.attempt_count})")

        if self.should_fail:
            raise RuntimeError("Mock provider configured to fail")

        # Return a valid hypothesis structure
        return {
            "id": "mock123456789abc",
            "related_observations": ["obs-1", "obs-2"],
            "title": "Mock Hypothesis: Service Exposure Risk",
            "description": "Analysis indicates potential service exposure based on open ports and service detection results. This warrants validation to confirm actual risk level.",
            "risk_tags": ["exposure", "network", "validation-needed"],
            "confidence": 0.75,
            "rationale": "Based on observations obs-1 and obs-2 showing open administrative services, this hypothesis suggests potential unauthorized access risk if proper authentication controls are not in place.",
            "requires_validation": True
        }

    def validate_safety(self, text: str) -> bool:
        """Mock safety validation."""
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
        """Mock is always available."""
        return not self.should_fail
