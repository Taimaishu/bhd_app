"""Export finding drafts to bhd-cli format."""
import json
from typing import Any, Dict, List

from ...core.entities import FindingDraft


class BHDCLIExporter:
    """Export findings to bhd-cli compatible format."""

    # Map internal lowercase enums to bhd-cli capitalized format
    IMPACT_MAP = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical"
    }

    LIKELIHOOD_MAP = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "very_high": "Very High"
    }

    @staticmethod
    def finding_draft_to_bhd_cli(draft: FindingDraft) -> Dict[str, Any]:
        """Convert FindingDraft to bhd-cli finding format.

        Maps internal lowercase impact/likelihood to bhd-cli capitalized format.
        """
        # Map assistant fields to bhd-cli fields
        return {
            "title": draft.title,
            "description": draft.description,
            "affected_target": draft.affected_asset,
            "evidence": "\n".join(draft.evidence_refs),
            "impact_level": BHDCLIExporter.IMPACT_MAP[draft.impact],
            "likelihood": BHDCLIExporter.LIKELIHOOD_MAP[draft.likelihood],
            "remediation": draft.remediation,
            "business_impact": draft.business_impact,
            # Additional metadata
            "_assistant_metadata": {
                "playbook_id": draft.playbook_id,
                "generated_by": "bhd-assist",
                "version": draft.metadata.get("playbook_version", "unknown")
            }
        }

    @staticmethod
    def export_json(
        drafts: List[FindingDraft],
        output_path: str
    ) -> None:
        """Export finding drafts to JSON file."""
        findings = [
            BHDCLIExporter.finding_draft_to_bhd_cli(draft)
            for draft in drafts
        ]

        export_data = {
            "findings": findings,
            "export_metadata": {
                "generated_by": "bhd-assist",
                "format_version": "1.0",
                "bhd_cli_compatible": True
            }
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, sort_keys=True)

    @staticmethod
    def to_bhd_cli_import_format(drafts: List[FindingDraft]) -> str:
        """Convert drafts to bhd-cli import JSON format."""
        findings = [
            BHDCLIExporter.finding_draft_to_bhd_cli(draft)
            for draft in drafts
        ]

        return json.dumps(
            {"findings": findings},
            indent=2,
            sort_keys=True
        )
