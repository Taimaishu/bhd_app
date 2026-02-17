"""Tests for JSON storage adapter."""
import pytest
from datetime import datetime
from pathlib import Path

from bhd_cli.assistant.core.entities import Observation, ObservationCategory, FindingDraft
from bhd_cli.assistant.adapters.storage.json_store import JSONStorageAdapter


def test_save_and_load_observation(tmp_path):
    """Test that observations can be saved and loaded correctly."""
    storage = JSONStorageAdapter(tmp_path)

    # Create test observation
    obs = Observation(
        id="obs-123",
        source_artifact="nmap-scan-001",
        category=ObservationCategory.PORT,
        tags=["open", "http"],
        confidence=0.95,
        data={
            "port": 80,
            "service": "http",
            "state": "open"
        },
        created_at=datetime(2026, 2, 17, 10, 30, 0)
    )

    # Save observation
    obs_id = storage.save_observation(obs)

    # Load observations
    loaded = storage.load_observations(session_id="test-session")

    # Verify
    assert len(loaded) == 1
    loaded_obs = loaded[0]
    assert loaded_obs.id == "obs-123"
    assert loaded_obs.source_artifact == "nmap-scan-001"
    assert loaded_obs.category == ObservationCategory.PORT
    assert loaded_obs.tags == ["open", "http"]
    assert loaded_obs.confidence == 0.95
    assert loaded_obs.data["port"] == 80
    assert loaded_obs.data["service"] == "http"
    assert loaded_obs.created_at == datetime(2026, 2, 17, 10, 30, 0)


def test_load_multiple_observations(tmp_path):
    """Test loading multiple observations."""
    storage = JSONStorageAdapter(tmp_path)

    # Save multiple observations
    obs1 = Observation(
        id="obs-1",
        source_artifact="scan-1",
        category=ObservationCategory.SERVICE,
        tags=["ssh"],
        confidence=0.9,
        data={"service": "ssh"}
    )

    obs2 = Observation(
        id="obs-2",
        source_artifact="scan-1",
        category=ObservationCategory.EXPOSURE,
        tags=["public"],
        confidence=0.85,
        data={"exposure": "internet-facing"}
    )

    storage.save_observation(obs1)
    storage.save_observation(obs2)

    # Load all observations
    loaded = storage.load_observations(session_id="test-session")

    assert len(loaded) == 2
    assert loaded[0].id == "obs-1"
    assert loaded[1].id == "obs-2"


def test_load_observations_empty_file(tmp_path):
    """Test loading observations when file doesn't exist."""
    storage = JSONStorageAdapter(tmp_path)

    loaded = storage.load_observations(session_id="test-session")

    assert loaded == []


def test_observation_category_roundtrip(tmp_path):
    """Test that all ObservationCategory enum values roundtrip correctly."""
    storage = JSONStorageAdapter(tmp_path)

    categories = [
        ObservationCategory.SERVICE,
        ObservationCategory.PORT,
        ObservationCategory.TECHNOLOGY,
        ObservationCategory.AUTHENTICATION,
        ObservationCategory.AUTHORIZATION,
        ObservationCategory.EXPOSURE,
        ObservationCategory.CONFIGURATION,
        ObservationCategory.PROTOCOL,
        ObservationCategory.OTHER
    ]

    for idx, category in enumerate(categories):
        obs = Observation(
            id=f"obs-{idx}",
            source_artifact="test-artifact",
            category=category,
            tags=["test"],
            confidence=0.9,
            data={"test": "data"}
        )
        storage.save_observation(obs)

    # Load and verify
    loaded = storage.load_observations(session_id="test-session")

    assert len(loaded) == len(categories)
    for idx, obs in enumerate(loaded):
        assert obs.category == categories[idx]


def test_save_finding_draft(tmp_path):
    """Test that finding drafts can be saved."""
    storage = JSONStorageAdapter(tmp_path)

    draft = FindingDraft(
        id="finding-1",
        title="Test Finding",
        affected_asset="test-asset",
        description="Test description",
        impact="high",
        likelihood="medium",
        evidence_refs=["evidence-1", "evidence-2"],
        remediation="Test remediation",
        business_impact="Test business impact"
    )

    # Save finding draft
    draft_id = storage.save_finding_draft(draft)

    # Verify file was created and contains data
    assert storage.findings_file.exists()

    import json
    with open(storage.findings_file) as f:
        saved_data = json.loads(f.read())

    assert saved_data["title"] == "Test Finding"
    assert saved_data["impact"] == "high"
    assert saved_data["likelihood"] == "medium"
