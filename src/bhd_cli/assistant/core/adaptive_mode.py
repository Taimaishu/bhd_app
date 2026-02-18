"""ADAPTIVE mode - context-aware assistance level evaluation."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any


class Environment(Enum):
    """Environment context."""
    PROD_CLIENT = "prod_client"
    LAB = "lab"
    CTF = "ctf"


class TargetOwner(Enum):
    """Target ownership context."""
    SELF = "self"
    CLIENT = "client"
    UNKNOWN = "unknown"


class EffectiveAssistLevel(Enum):
    """Effective assistance level after context evaluation."""
    STANDARD = "standard"  # Validation/evidence only, safe testing guidance
    DEEP_LAB = "deep_lab"  # Broader guidance in lab environments


@dataclass
class AssistContext:
    """Context for assistance level evaluation."""
    environment: Environment
    authorization: bool  # User assertion of written authorization
    target_owner: TargetOwner
    requested_level: EffectiveAssistLevel = EffectiveAssistLevel.STANDARD

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "authorization": self.authorization,
            "target_owner": self.target_owner.value,
            "requested_level": self.requested_level.value
        }


@dataclass
class AssistEvaluation:
    """Result of assistance level evaluation."""
    effective_level: EffectiveAssistLevel
    reasons: List[str]  # List of reasons why level was chosen/clamped
    context: AssistContext

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effective_level": self.effective_level.value,
            "reasons": self.reasons,
            "context": self.context.to_dict()
        }


def evaluate_assist_level(context: AssistContext) -> AssistEvaluation:
    """
    Evaluate effective assistance level based on context.

    Rules:
    - Default to STANDARD
    - Allow DEEP_LAB only if:
        - environment in {lab, ctf}
        - AND authorization == True
        - AND target_owner == self
    - Otherwise clamp to STANDARD and explain why
    """
    reasons = []

    # If not requesting deep_lab, just return standard
    if context.requested_level == EffectiveAssistLevel.STANDARD:
        reasons.append("requested_level=standard")
        return AssistEvaluation(
            effective_level=EffectiveAssistLevel.STANDARD,
            reasons=reasons,
            context=context
        )

    # User requested deep_lab - check if allowed
    if context.environment not in {Environment.LAB, Environment.CTF}:
        reasons.append(f"clamped: environment={context.environment.value} (requires lab or ctf)")
        return AssistEvaluation(
            effective_level=EffectiveAssistLevel.STANDARD,
            reasons=reasons,
            context=context
        )

    if not context.authorization:
        reasons.append("clamped: authorization=false")
        return AssistEvaluation(
            effective_level=EffectiveAssistLevel.STANDARD,
            reasons=reasons,
            context=context
        )

    if context.target_owner != TargetOwner.SELF:
        reasons.append(f"clamped: target_owner={context.target_owner.value} (requires self)")
        return AssistEvaluation(
            effective_level=EffectiveAssistLevel.STANDARD,
            reasons=reasons,
            context=context
        )

    # All conditions met for deep_lab
    reasons.append("deep_lab_enabled: environment=lab/ctf, authorized=true, target_owner=self")
    return AssistEvaluation(
        effective_level=EffectiveAssistLevel.DEEP_LAB,
        reasons=reasons,
        context=context
    )
