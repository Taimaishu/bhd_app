"""Playbook loader and validator."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..core.entities import EvidencePlan, FindingDraft


class PlaybookLoader:
    """Loads and validates playbooks from YAML files."""

    def __init__(self, playbooks_dir: Path, schemas_dir: Path):
        self.playbooks_dir = playbooks_dir
        self.schemas_dir = schemas_dir
        self._playbook_cache: Dict[str, Dict[str, Any]] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load JSON schemas for validation."""
        playbook_schema_path = self.schemas_dir / "playbook.schema.json"
        evidence_schema_path = self.schemas_dir / "evidence.schema.json"

        with open(playbook_schema_path) as f:
            self.playbook_schema = json.load(f)

        with open(evidence_schema_path) as f:
            self.evidence_schema = json.load(f)

    def load_playbook(self, playbook_id: str) -> Dict[str, Any]:
        """Load a playbook by ID from YAML file."""
        if playbook_id in self._playbook_cache:
            return self._playbook_cache[playbook_id]

        # Try to find playbook file
        playbook_file = None
        for file_path in self.playbooks_dir.rglob("*.yaml"):
            if file_path.stem == playbook_id or playbook_id in str(file_path):
                playbook_file = file_path
                break

        if not playbook_file:
            raise FileNotFoundError(f"Playbook {playbook_id} not found")

        with open(playbook_file) as f:
            playbook_data = yaml.safe_load(f)

        # Basic validation
        if not self._validate_playbook(playbook_data):
            raise ValueError(f"Playbook {playbook_id} failed validation")

        self._playbook_cache[playbook_id] = playbook_data
        return playbook_data

    def _validate_playbook(self, playbook_data: Dict[str, Any]) -> bool:
        """Validate playbook against schema (basic validation)."""
        required_fields = ["id", "version", "name", "type", "test_types", "steps",
                          "evidence_objects", "finding_template", "safety_constraints"]

        for field in required_fields:
            if field not in playbook_data:
                return False

        # Validate version format
        version = playbook_data.get("version", "")
        if not isinstance(version, str) or len(version.split(".")) != 3:
            return False

        return True

    def list_playbooks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List all available playbooks with optional filters."""
        playbooks = []

        for file_path in self.playbooks_dir.rglob("*.yaml"):
            try:
                with open(file_path) as f:
                    playbook_data = yaml.safe_load(f)

                if self._validate_playbook(playbook_data):
                    # Apply filters if provided
                    if filters:
                        test_type_filter = filters.get("test_type")
                        if test_type_filter:
                            if test_type_filter not in playbook_data.get("test_types", []):
                                continue

                    playbooks.append({
                        "id": playbook_data["id"],
                        "name": playbook_data["name"],
                        "version": playbook_data["version"],
                        "type": playbook_data["type"],
                        "test_types": playbook_data["test_types"],
                        "description": playbook_data.get("description", "")
                    })
            except Exception:
                # Skip invalid playbooks
                continue

        # Sort by ID for deterministic ordering
        return sorted(playbooks, key=lambda p: p["id"])

    def render_checklist(self, playbook_data: Dict[str, Any]) -> str:
        """Render human-readable checklist from playbook."""
        lines = []
        lines.append(f"# {playbook_data['name']}")
        lines.append(f"Version: {playbook_data['version']}")
        lines.append("")

        if "description" in playbook_data:
            lines.append(f"**Description:** {playbook_data['description']}")
            lines.append("")

        lines.append("## Safety Constraints (DO NOT)")
        for constraint in playbook_data.get("safety_constraints", []):
            lines.append(f"- ❌ {constraint}")
        lines.append("")

        lines.append("## Validation Steps")
        for step in playbook_data.get("steps", []):
            lines.append(f"### Step {step['step_number']}: {step['action']}")
            lines.append(f"{step['description']}")
            if "expected_outcome" in step:
                lines.append(f"**Expected Outcome:** {step['expected_outcome']}")
            if "tools" in step:
                lines.append(f"**Tools:** {', '.join(step['tools'])}")
            lines.append("")

        lines.append("## Evidence to Collect")
        for evidence in playbook_data.get("evidence_objects", []):
            required = "✅ Required" if evidence.get("required", False) else "⭕ Optional"
            lines.append(f"- **{evidence['id']}** ({evidence['type']}) - {required}")
            lines.append(f"  {evidence['description']}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _map_evidence_type(playbook_type: str) -> str:
        """Map playbook schema evidence types to evidence.schema.json types.

        Playbook YAML uses: request_response, screenshot, config, banner, log, timestamp
        EvidencePlan uses: request_response_pair, screenshot, configuration_snapshot,
                          banner_capture, network_trace, log_entry, metadata, other
        """
        type_map = {
            "request_response": "request_response_pair",
            "screenshot": "screenshot",
            "config": "configuration_snapshot",
            "banner": "banner_capture",
            "log": "log_entry",
            "timestamp": "metadata"
        }
        return type_map.get(playbook_type, "other")

    def create_evidence_plan(self, playbook_data: Dict[str, Any]) -> EvidencePlan:
        """Create evidence plan from playbook."""
        # Generate deterministic ID
        import hashlib
        plan_id = hashlib.sha256(f"{playbook_data['id']}:{playbook_data['version']}".encode()).hexdigest()[:16]

        # Map evidence types from playbook schema to evidence schema
        evidence_items = []
        for evidence in playbook_data["evidence_objects"]:
            mapped_evidence = evidence.copy()
            mapped_evidence["type"] = self._map_evidence_type(evidence["type"])
            evidence_items.append(mapped_evidence)

        return EvidencePlan(
            id=plan_id,
            playbook_id=playbook_data["id"],
            evidence_items=evidence_items
        )

    def create_finding_draft(
        self,
        playbook_data: Dict[str, Any],
        affected_asset: str,
        evidence_refs: List[str]
    ) -> FindingDraft:
        """Create finding draft skeleton from playbook template."""
        import hashlib
        from datetime import datetime

        # Generate deterministic ID
        finding_id = hashlib.sha256(
            f"{playbook_data['id']}:{affected_asset}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        template = playbook_data["finding_template"]

        # Map impact levels to lowercase for schema compliance
        impact_map = {
            "Critical": "critical",
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "low"
        }

        likelihood_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low"
        }

        return FindingDraft(
            id=finding_id,
            title=template["title"],
            description=template["description"],
            affected_asset=affected_asset,
            evidence_refs=evidence_refs,
            impact=impact_map.get(template["impact_level"], "medium"),
            likelihood=likelihood_map.get(template["likelihood"], "medium"),
            remediation=template["remediation"],
            business_impact=template["business_impact"],
            risk_tags=[],
            status="draft",
            playbook_id=playbook_data["id"],
            metadata={
                "playbook_version": playbook_data["version"],
                "generated_by": "bhd-assist"
            }
        )
