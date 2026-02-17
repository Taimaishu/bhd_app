"""Core domain entities for the assistant - schema-compliant."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AssistanceLevel(Enum):
    """Assistance levels controlling what guidance is provided."""
    VALIDATION_ONLY = 0  # Production: validation/evidence only, no exploitation
    LAB_TRAINING = 1     # Lab/training: broader guidance, still no weaponized exploits
    # LEVEL_2 not implemented


class PlaybookType(Enum):
    """Types of playbooks."""
    VALIDATION = "validation"
    EVIDENCE_COLLECTION = "evidence_collection"
    VERIFICATION = "verification"


class ObservationCategory(Enum):
    """Observation categories (from schema)."""
    SERVICE = "service"
    PORT = "port"
    TECHNOLOGY = "technology"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    EXPOSURE = "exposure"
    CONFIGURATION = "configuration"
    PROTOCOL = "protocol"
    OTHER = "other"


@dataclass
class Observation:
    """Normalized observation from tool output or manual input.

    Schema-compliant with observation.schema.json
    """
    id: str  # Deterministic UUID or hash-based ID
    source_artifact: str  # Reference to ingested artifact ID
    category: ObservationCategory
    tags: List[str]
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]  # Structured extracted data
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict."""
        return {
            "id": self.id,
            "source_artifact": self.source_artifact,
            "category": self.category.value if isinstance(self.category, ObservationCategory) else self.category,
            "tags": self.tags,
            "confidence": self.confidence,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }


@dataclass
class Hypothesis:
    """Reasoning layer hypothesis.

    Schema-compliant with hypothesis.schema.json
    """
    id: str
    related_observations: List[str]  # IDs of related observations
    title: str
    description: str
    risk_tags: List[str]
    confidence: float  # 0.0 to 1.0
    rationale: str  # Why this hypothesis was formed
    requires_validation: bool = True

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict."""
        return {
            "id": self.id,
            "related_observations": self.related_observations,
            "title": self.title,
            "description": self.description,
            "risk_tags": self.risk_tags,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "requires_validation": self.requires_validation
        }


@dataclass
class EvidencePlan:
    """Plan for what evidence to collect.

    Schema-compliant with evidence.schema.json
    """
    id: str
    playbook_id: str
    evidence_items: List[Dict[str, Any]]  # Must match evidence.schema.json structure

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict."""
        return {
            "id": self.id,
            "playbook_id": self.playbook_id,
            "evidence_items": self.evidence_items
        }


@dataclass
class FindingDraft:
    """Draft finding ready for export to bhd-cli.

    Schema-compliant with finding_draft.schema.json
    """
    id: str
    title: str
    affected_asset: str
    description: str
    impact: str  # low, medium, high, critical
    likelihood: str  # low, medium, high, very_high
    evidence_refs: List[str]
    remediation: str
    business_impact: str
    risk_tags: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, validated, closed
    playbook_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate enum values
        valid_impacts = ["low", "medium", "high", "critical"]
        valid_likelihoods = ["low", "medium", "high", "very_high"]
        valid_statuses = ["draft", "validated", "closed"]

        if self.impact not in valid_impacts:
            raise ValueError(f"impact must be one of {valid_impacts}")
        if self.likelihood not in valid_likelihoods:
            raise ValueError(f"likelihood must be one of {valid_likelihoods}")
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict."""
        return {
            "id": self.id,
            "title": self.title,
            "affected_asset": self.affected_asset,
            "description": self.description,
            "impact": self.impact,
            "likelihood": self.likelihood,
            "evidence_refs": self.evidence_refs,
            "risk_tags": self.risk_tags,
            "remediation": self.remediation,
            "business_impact": self.business_impact,
            "status": self.status
        }


@dataclass
class ExportBundle:
    """Export bundle for bhd-cli integration.

    Schema-compliant with bundle.schema.json
    """
    bundle_version: str = "1.0"
    engagement_id: str = ""
    generated_at: Optional[datetime] = None
    findings: List[FindingDraft] = field(default_factory=list)
    artifacts_manifest: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict."""
        return {
            "bundle_version": self.bundle_version,
            "engagement_id": self.engagement_id,
            "generated_at": self.generated_at.isoformat() if self.generated_at else datetime.utcnow().isoformat(),
            "findings": [f.to_dict() for f in self.findings],
            "artifacts_manifest": self.artifacts_manifest
        }


@dataclass
class DecisionLogEntry:
    """Entry in the decision log."""
    timestamp: datetime
    event_type: str  # e.g., "playbook_selected", "policy_blocked", "finding_drafted"
    assistance_level: AssistanceLevel
    details: Dict[str, Any]
    redacted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "assistance_level": self.assistance_level.name,
            "details": self.details,
            "redacted": self.redacted
        }
