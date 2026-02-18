"""Policy guard implementation."""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.entities import AssistanceLevel, DecisionLogEntry
from ..core.ports import IPolicyGuard


class PolicyGuard(IPolicyGuard):
    """Enforces policy rules and logs decisions."""

    # Patterns that should ALWAYS be blocked regardless of assistance level
    ALWAYS_BLOCKED_PATTERNS = [
        r"\bexploit\s+code\b",
        r"\bpayload\s+generation\b",
        r"\bbypass\s+(authentication|authorization)\b",
        r"\bpersistence\s+mechanism\b",
        r"\bprivilege\s+escalation\s+step",
        r"\bexfiltration\s+method\b",
        r"\bweaponized?\s+(script|tool|payload)\b",
        r"\breverser?\s+shell\b",
        r"\bbackdoor\b",
        r"\bmalware\b",
        r"\bransomware\b",
        r"\bcrypto\s?locker\b",
        r"\bdenial\s+of\s+service\b",
        r"\bdos\s+attack\b",
        r"\bddos\b",
    ]

    # Additional patterns blocked at VALIDATION_ONLY level (Level 0)
    # ADAPTIVE mode: reduced false positives while still blocking weaponized content
    VALIDATION_ONLY_BLOCKED_PATTERNS = [
        r"\bhow\s+to\s+exploit.*step-by-step\b",  # More specific
        r"\bexecution\s+step.*exploit.*code\b",   # Require "code"
        r"\battack\s+vector.*implement.*payload\b",  # Require "payload"
        r"\binjection\s+payload.*example\b",      # Require "example"
    ]

    def __init__(
        self,
        assistance_level: AssistanceLevel = AssistanceLevel.VALIDATION_ONLY,
        profile_path: Optional[Path] = None,
        decision_log_path: Optional[Path] = None
    ):
        self.assistance_level = assistance_level
        self.profile_path = profile_path
        self.decision_log_path = decision_log_path or Path("decision_log.jsonl")

        # Load profile if Level 1 requested
        if assistance_level == AssistanceLevel.LAB_TRAINING:
            if not profile_path or not profile_path.exists():
                raise ValueError(
                    "LAB_TRAINING level requires explicit profile file. "
                    "Create a profile.json with 'assistance_level': 1"
                )
            self._validate_profile(profile_path)

    def _validate_profile(self, profile_path: Path) -> None:
        """Validate profile file for Level 1."""
        try:
            with open(profile_path) as f:
                profile = json.load(f)
            if profile.get("assistance_level") != 1:
                raise ValueError("Profile must explicitly set assistance_level: 1")
        except Exception as e:
            raise ValueError(f"Invalid profile file: {e}")

    def check_content(self, content: str, context: Dict[str, Any]) -> bool:
        """Check if content passes policy rules."""
        content_lower = content.lower()

        # Check always-blocked patterns
        for pattern in self.ALWAYS_BLOCKED_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                self.log_decision(DecisionLogEntry(
                    timestamp=datetime.utcnow(),
                    event_type="policy_blocked",
                    assistance_level=self.assistance_level,
                    details={
                        "reason": "always_blocked_pattern",
                        "pattern": pattern,
                        "context": context
                    },
                    redacted=True
                ))
                return False

        # Check level-specific patterns
        if self.assistance_level == AssistanceLevel.VALIDATION_ONLY:
            for pattern in self.VALIDATION_ONLY_BLOCKED_PATTERNS:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    self.log_decision(DecisionLogEntry(
                        timestamp=datetime.utcnow(),
                        event_type="policy_blocked",
                        assistance_level=self.assistance_level,
                        details={
                            "reason": "validation_only_blocked_pattern",
                            "pattern": pattern,
                            "context": context
                        },
                        redacted=True
                    ))
                    return False

        return True

    def get_assistance_level(self) -> AssistanceLevel:
        """Get current assistance level."""
        return self.assistance_level

    def log_decision(self, entry: DecisionLogEntry) -> None:
        """Log a decision to the decision log (append-only JSONL)."""
        # Redact sensitive information
        log_entry = entry.to_dict()
        if entry.redacted:
            # Redact details, keep only metadata
            log_entry["details"] = {
                k: "[REDACTED]" if k not in ["reason", "event"] else v
                for k, v in log_entry["details"].items()
            }

        # Append to JSONL file
        with open(self.decision_log_path, "a") as f:
            f.write(json.dumps(log_entry, sort_keys=True) + "\n")

    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate that data conforms to schema (basic validation)."""
        # Simple schema validation - in production, use jsonschema library
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False

        properties = schema.get("properties", {})
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False

        return True
