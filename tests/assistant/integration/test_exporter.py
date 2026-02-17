"""Tests for bhd-cli exporter."""
import pytest

from bhd_cli.assistant.core.entities import FindingDraft
from bhd_cli.assistant.integration.bhd_cli.exporter import BHDCLIExporter


def test_exporter_maps_impact_correctly():
    """Test that exporter maps lowercase impact to capitalized impact_level."""
    impact_mappings = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical"
    }

    for internal_impact, expected_bhd_cli in impact_mappings.items():
        draft = FindingDraft(
            id="test-finding-1",
            title="Test Finding",
            affected_asset="test-asset",
            description="Test description",
            impact=internal_impact,
            likelihood="medium",
            evidence_refs=["evidence-1"],
            remediation="Test remediation",
            business_impact="Test business impact"
        )

        result = BHDCLIExporter.finding_draft_to_bhd_cli(draft)

        assert result["impact_level"] == expected_bhd_cli, (
            f"Expected impact_level={expected_bhd_cli} for impact={internal_impact}, "
            f"got {result['impact_level']}"
        )


def test_exporter_maps_likelihood_correctly():
    """Test that exporter maps lowercase likelihood to capitalized format."""
    likelihood_mappings = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "very_high": "Very High"
    }

    for internal_likelihood, expected_bhd_cli in likelihood_mappings.items():
        draft = FindingDraft(
            id="test-finding-1",
            title="Test Finding",
            affected_asset="test-asset",
            description="Test description",
            impact="medium",
            likelihood=internal_likelihood,
            evidence_refs=["evidence-1"],
            remediation="Test remediation",
            business_impact="Test business impact"
        )

        result = BHDCLIExporter.finding_draft_to_bhd_cli(draft)

        assert result["likelihood"] == expected_bhd_cli, (
            f"Expected likelihood={expected_bhd_cli} for likelihood={internal_likelihood}, "
            f"got {result['likelihood']}"
        )


def test_exporter_maps_all_fields():
    """Test that exporter maps all FindingDraft fields correctly."""
    draft = FindingDraft(
        id="finding-123",
        title="SQL Injection Vulnerability",
        affected_asset="api.example.com",
        description="SQL injection in login endpoint",
        impact="high",
        likelihood="very_high",
        evidence_refs=["request-1", "response-1", "screenshot-1"],
        remediation="Use parameterized queries",
        business_impact="Unauthorized data access",
        playbook_id="sql_injection_validation",
        metadata={"playbook_version": "1.0.0"}
    )

    result = BHDCLIExporter.finding_draft_to_bhd_cli(draft)

    # Check required bhd-cli fields
    assert result["title"] == "SQL Injection Vulnerability"
    assert result["description"] == "SQL injection in login endpoint"
    assert result["affected_target"] == "api.example.com"
    assert result["impact_level"] == "High"
    assert result["likelihood"] == "Very High"
    assert result["remediation"] == "Use parameterized queries"
    assert result["business_impact"] == "Unauthorized data access"
    assert result["evidence"] == "request-1\nresponse-1\nscreenshot-1"

    # Check metadata
    assert result["_assistant_metadata"]["playbook_id"] == "sql_injection_validation"
    assert result["_assistant_metadata"]["generated_by"] == "bhd-assist"
    assert result["_assistant_metadata"]["version"] == "1.0.0"


def test_exporter_handles_empty_evidence():
    """Test that exporter handles empty evidence_refs list."""
    draft = FindingDraft(
        id="finding-123",
        title="Test Finding",
        affected_asset="test-asset",
        description="Test description",
        impact="low",
        likelihood="low",
        evidence_refs=[],
        remediation="Test remediation",
        business_impact="Test business impact"
    )

    result = BHDCLIExporter.finding_draft_to_bhd_cli(draft)

    assert result["evidence"] == ""
