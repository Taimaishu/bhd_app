"""End-to-end integration tests for ingest -> suggest -> render flow."""
import tempfile
from pathlib import Path

from bhd_cli.assistant.core.entities import Observation, ObservationCategory
from bhd_cli.assistant.adapters.storage.json_store import JSONStorageAdapter
from bhd_cli.assistant.playbooks.selector import PlaybookSelector


def get_rules_path():
    """Get path to selector rules."""
    return Path(__file__).parent.parent.parent / "src" / "bhd_cli" / "assistant" / "playbooks" / "selectors" / "selector_rules.yaml"


def test_e2e_ingest_suggest_network():
    """Test end-to-end flow: ingest observations, suggest playbook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        storage = JSONStorageAdapter(storage_dir)

        # Simulate ingested observations from Nmap (SERVICE category with version)
        obs1 = Observation(
            id="obs-1",
            source_artifact="nmap-scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service", "ssh"],
            confidence=1.0,
            data={
                "host": "10.0.0.1",
                "port": 22,
                "service": "ssh",
                "product": "OpenSSH",
                "version": "8.9p1",
                "state": "open"
            }
        )

        # Save observation
        storage.save_observation(obs1)

        # Load observations back
        observations = storage.load_observations(session_id="test")

        assert len(observations) == 1

        # Run selector
        selector = PlaybookSelector(get_rules_path())
        selected = selector.select_playbook(observations, "network")

        # Should match exposed_admin_interfaces
        assert selected == "exposed_admin_interfaces"


def test_e2e_ingest_suggest_ics():
    """Test end-to-end flow for ICS Modbus detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        storage = JSONStorageAdapter(storage_dir)

        # Simulate Modbus detection
        obs1 = Observation(
            id="obs-1",
            source_artifact="nmap-ics-scan",
            category=ObservationCategory.PORT,
            tags=["open", "modbus"],
            confidence=0.98,
            data={
                "host": "10.0.0.10",
                "port": 502,
                "service": "modbus",
                "state": "open"
            }
        )

        storage.save_observation(obs1)
        observations = storage.load_observations(session_id="test")

        selector = PlaybookSelector(get_rules_path())
        selected = selector.select_playbook(observations, "ics")

        # Should match modbus_exposure
        assert selected == "modbus_exposure"


def test_e2e_no_match():
    """Test end-to-end flow when no playbook matches."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        storage = JSONStorageAdapter(storage_dir)

        # Observation that doesn't match any rules
        obs1 = Observation(
            id="obs-1",
            source_artifact="test",
            category=ObservationCategory.OTHER,
            tags=["unknown"],
            confidence=0.5,
            data={"test": "data"}
        )

        storage.save_observation(obs1)
        observations = storage.load_observations(session_id="test")

        selector = PlaybookSelector(get_rules_path())
        selected = selector.select_playbook(observations, "network")

        # Should return None
        assert selected is None
