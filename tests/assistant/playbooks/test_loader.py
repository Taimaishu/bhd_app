"""Tests for playbook loader."""
import pytest
from pathlib import Path

from bhd_cli.assistant.playbooks.loader import PlaybookLoader


@pytest.fixture
def playbooks_dir():
    """Get playbooks directory."""
    return Path(__file__).parent.parent.parent.parent / "src" / "bhd_cli" / "assistant" / "playbooks" / "library"


@pytest.fixture
def schemas_dir():
    """Get schemas directory."""
    return Path(__file__).parent.parent.parent.parent / "src" / "bhd_cli" / "assistant" / "playbooks" / "schemas"


@pytest.fixture
def loader(playbooks_dir, schemas_dir):
    """Create playbook loader."""
    return PlaybookLoader(playbooks_dir, schemas_dir)


def test_loader_loads_playbook(loader):
    """Test that loader can load a playbook."""
    playbook = loader.load_playbook("idor_validation")

    assert playbook["id"] == "idor_validation"
    assert playbook["version"] == "1.0.0"
    assert "steps" in playbook
    assert "evidence_objects" in playbook
    assert "finding_template" in playbook
    assert "safety_constraints" in playbook


def test_loader_validates_playbook(loader):
    """Test that loader validates playbook structure."""
    playbook = loader.load_playbook("idor_validation")

    # Should have required fields
    assert "id" in playbook
    assert "version" in playbook
    assert "name" in playbook
    assert "type" in playbook
    assert "test_types" in playbook


def test_loader_lists_playbooks(loader):
    """Test that loader can list all playbooks."""
    playbooks = loader.list_playbooks()

    assert len(playbooks) >= 5  # At least our 5 starter playbooks
    assert all("id" in p for p in playbooks)
    assert all("version" in p for p in playbooks)

    # Check deterministic ordering (sorted by ID)
    ids = [p["id"] for p in playbooks]
    assert ids == sorted(ids)


def test_loader_filters_by_test_type(loader):
    """Test that loader can filter playbooks by test type."""
    web_playbooks = loader.list_playbooks({"test_type": "web"})

    assert all("web" in p["test_types"] for p in web_playbooks)

    ics_playbooks = loader.list_playbooks({"test_type": "ics"})

    assert all("ics" in p["test_types"] for p in ics_playbooks)


def test_loader_renders_checklist(loader):
    """Test that loader renders human-readable checklist."""
    playbook = loader.load_playbook("idor_validation")
    checklist = loader.render_checklist(playbook)

    assert "IDOR" in checklist
    assert "Step 1" in checklist
    assert "Safety Constraints" in checklist
    assert "Evidence to Collect" in checklist
    assert "DO NOT" in checklist


def test_loader_creates_evidence_plan(loader):
    """Test that loader creates evidence plan."""
    playbook = loader.load_playbook("idor_validation")
    evidence_plan = loader.create_evidence_plan(playbook)

    assert evidence_plan.playbook_id == "idor_validation"
    assert evidence_plan.id is not None
    assert len(evidence_plan.evidence_items) > 0


def test_loader_creates_finding_draft(loader):
    """Test that loader creates finding draft skeleton."""
    playbook = loader.load_playbook("idor_validation")
    finding = loader.create_finding_draft(
        playbook,
        affected_asset="webapp.example.com",
        evidence_refs=["evidence_1", "evidence_2"]
    )

    assert "IDOR" in finding.title or "Insecure Direct Object Reference" in finding.title
    assert finding.affected_asset == "webapp.example.com"
    assert len(finding.evidence_refs) == 2
    assert finding.playbook_id == "idor_validation"
    assert finding.id is not None
    assert finding.status == "draft"
    assert finding.impact in ["low", "medium", "high", "critical"]
    assert finding.likelihood in ["low", "medium", "high", "very_high"]


def test_playbook_has_safety_constraints(loader):
    """Test that all playbooks have safety constraints."""
    playbooks = loader.list_playbooks()

    for pb_info in playbooks:
        playbook = loader.load_playbook(pb_info["id"])
        assert "safety_constraints" in playbook
        assert len(playbook["safety_constraints"]) >= 3, f"{pb_info['id']} needs at least 3 safety constraints"

        # Check for DO NOT constraints
        constraints_text = " ".join(playbook["safety_constraints"])
        assert "DO NOT" in constraints_text, f"{pb_info['id']} missing 'DO NOT' constraints"


def test_playbook_version_format(loader):
    """Test that playbook versions follow semver."""
    playbooks = loader.list_playbooks()

    for pb_info in playbooks:
        version = pb_info["version"]
        parts = version.split(".")
        assert len(parts) == 3, f"{pb_info['id']} version must be X.Y.Z format"
        assert all(part.isdigit() for part in parts), f"{pb_info['id']} version parts must be numbers"
