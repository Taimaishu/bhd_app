"""Ports/interfaces for adapters (hexagonal architecture)."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .entities import (
    AssistanceLevel,
    DecisionLogEntry,
    EvidencePlan,
    FindingDraft,
    Observation
)


class IStoragePort(ABC):
    """Interface for storage operations."""

    @abstractmethod
    def save_observation(self, observation: Observation) -> str:
        """Save an observation and return its ID."""
        pass

    @abstractmethod
    def load_observations(self, session_id: str) -> List[Observation]:
        """Load observations for a session."""
        pass

    @abstractmethod
    def save_finding_draft(self, draft: FindingDraft) -> str:
        """Save a finding draft and return its ID."""
        pass


class ILLMPort(ABC):
    """Interface for LLM provider."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Generate structured JSON output conforming to schema."""
        pass

    @abstractmethod
    def validate_safety(self, text: str) -> bool:
        """Check if text passes safety validation."""
        pass


class IParserPort(ABC):
    """Interface for tool output parsers."""

    @abstractmethod
    def can_parse(self, tool_name: str, output: str) -> bool:
        """Check if this parser can handle the given tool output."""
        pass

    @abstractmethod
    def parse(self, tool_name: str, output: str) -> List[Observation]:
        """Parse tool output into observations."""
        pass


class IPolicyGuard(ABC):
    """Interface for policy enforcement."""

    @abstractmethod
    def check_content(self, content: str, context: Dict[str, Any]) -> bool:
        """Check if content passes policy rules."""
        pass

    @abstractmethod
    def get_assistance_level(self) -> AssistanceLevel:
        """Get current assistance level."""
        pass

    @abstractmethod
    def log_decision(self, entry: DecisionLogEntry) -> None:
        """Log a decision to the decision log."""
        pass


class IPlaybookRepository(ABC):
    """Interface for playbook storage and retrieval."""

    @abstractmethod
    def load_playbook(self, playbook_id: str) -> Dict[str, Any]:
        """Load a playbook by ID."""
        pass

    @abstractmethod
    def list_playbooks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List available playbooks with optional filters."""
        pass

    @abstractmethod
    def select_playbook(
        self,
        observations: List[Observation],
        test_type: str
    ) -> Optional[str]:
        """Select appropriate playbook based on observations and test type."""
        pass
