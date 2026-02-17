"""Tests for playbook selector."""
import pytest
from pathlib import Path

from bhd_cli.assistant.core.entities import Observation, ObservationCategory
from bhd_cli.assistant.playbooks.selector import PlaybookSelector


@pytest.fixture
def selector():
    """Create selector with rules."""
    rules_path = Path(__file__).parent.parent.parent.parent / "src" / "bhd_cli" / "assistant" / "playbooks" / "selectors" / "selector_rules.yaml"
    return PlaybookSelector(rules_path)


def test_selector_web_idor(selector):
    """Test that selector picks IDOR playbook for web resources."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="burp-scan-1",
            category=ObservationCategory.SERVICE,
            tags=["http", "idor"],
            confidence=0.9,
            data={
                "status_code": 200,
                "url_pattern": "/user/123",
                "method": "GET"
            }
        )
    ]

    result = selector.select_playbook(observations, "web")
    assert result == "idor_validation"


def test_selector_web_authz(selector):
    """Test that selector picks authz playbook for authorization issues."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="test-1",
            category=ObservationCategory.AUTHORIZATION,
            tags=["authz", "bypass"],
            confidence=0.95,
            data={
                "status_code": 200,
                "authz_bypass_indicator": True,
                "endpoint": "/admin"
            }
        )
    ]

    result = selector.select_playbook(observations, "web")
    assert result == "authz_broken_access"


def test_selector_network_exposed_admin(selector):
    """Test that selector picks exposed admin playbook for open admin services."""
    # Test with PORT category
    observations_port = [
        Observation(
            id="obs-1",
            source_artifact="nmap-scan-1",
            category=ObservationCategory.PORT,
            tags=["open", "ssh"],
            confidence=0.99,
            data={
                "port": 22,
                "service": "ssh",
                "state": "open"
            }
        )
    ]

    result = selector.select_playbook(observations_port, "network")
    assert result == "exposed_admin_interfaces"

    # Test with SERVICE category (version info available)
    observations_service = [
        Observation(
            id="obs-2",
            source_artifact="nmap-scan-2",
            category=ObservationCategory.SERVICE,
            tags=["service", "ssh"],
            confidence=1.0,
            data={
                "port": 22,
                "service": "ssh",
                "product": "OpenSSH",
                "version": "8.9p1",
                "state": "open"
            }
        )
    ]

    result = selector.select_playbook(observations_service, "network")
    assert result == "exposed_admin_interfaces"


def test_selector_ics_modbus(selector):
    """Test that selector picks Modbus playbook for exposed Modbus."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="ics-scan-1",
            category=ObservationCategory.PORT,
            tags=["modbus", "ics"],
            confidence=0.98,
            data={
                "port": 502,
                "service": "modbus",
                "state": "open"
            }
        )
    ]

    result = selector.select_playbook(observations, "ics")
    assert result == "modbus_exposure"


def test_selector_ics_opcua(selector):
    """Test that selector picks OPC UA playbook for exposed OPC UA."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="ics-scan-1",
            category=ObservationCategory.PORT,
            tags=["opcua", "ics"],
            confidence=0.98,
            data={
                "port": 4840,
                "service": "opcua",
                "state": "open"
            }
        )
    ]

    result = selector.select_playbook(observations, "ot")
    assert result == "opcua_exposure"


def test_selector_no_match(selector):
    """Test that selector returns None when no rules match."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="test-1",
            category=ObservationCategory.OTHER,
            tags=["unknown"],
            confidence=0.5,
            data={"test": "data"}
        )
    ]

    result = selector.select_playbook(observations, "web")
    assert result is None


def test_selector_wrong_test_type(selector):
    """Test that selector doesn't match rules with wrong test type."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="nmap-scan-1",
            category=ObservationCategory.PORT,
            tags=["open", "ssh"],
            confidence=0.99,
            data={
                "port": 22,
                "service": "ssh",
                "exposure": "public",
                "state": "open"
            }
        )
    ]

    # Network observation but asking for web test type
    result = selector.select_playbook(observations, "web")
    assert result is None


def test_selector_priority(selector):
    """Test that selector picks highest priority match."""
    # Create observations that could match multiple rules
    observations = [
        Observation(
            id="obs-1",
            source_artifact="test-1",
            category=ObservationCategory.SERVICE,
            tags=["http"],
            confidence=0.9,
            data={
                "status_code": 200,
                "url_pattern": "/user/123"
            }
        ),
        Observation(
            id="obs-2",
            source_artifact="test-1",
            category=ObservationCategory.AUTHORIZATION,
            tags=["authz"],
            confidence=0.95,
            data={
                "status_code": 200,
                "authz_bypass_indicator": True
            }
        )
    ]

    # IDOR has priority 100, authz has priority 95
    result = selector.select_playbook(observations, "web")
    assert result == "idor_validation"


def test_selector_explain_mode_match(selector):
    """Test explain mode when rule matches."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="nmap-scan",
            category=ObservationCategory.SERVICE,
            tags=["service", "ssh"],
            confidence=1.0,
            data={
                "port": 22,
                "service": "ssh",
                "product": "OpenSSH",
                "version": "8.9p1"
            }
        )
    ]

    result = selector.select_playbook(observations, "network", explain=True)

    # Should be a dict
    assert isinstance(result, dict)
    assert "evaluated_rules" in result
    assert "selected_playbook" in result

    # Should select exposed_admin_interfaces
    assert result["selected_playbook"] == "exposed_admin_interfaces"

    # Should have evaluation details
    evaluated = result["evaluated_rules"]
    assert isinstance(evaluated, list)
    assert len(evaluated) > 0

    # Find the matching rule
    matched_rules = [r for r in evaluated if r.get("matched")]
    assert len(matched_rules) > 0
    assert matched_rules[0]["rule_id"] == "network_exposed_admin_service"
    assert matched_rules[0]["playbook_id"] == "exposed_admin_interfaces"


def test_selector_explain_mode_no_match(selector):
    """Test explain mode when no rule matches."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="test",
            category=ObservationCategory.OTHER,
            tags=["unknown"],
            confidence=0.5,
            data={"test": "data"}
        )
    ]

    result = selector.select_playbook(observations, "network", explain=True)

    # Should be a dict
    assert isinstance(result, dict)
    assert result["selected_playbook"] is None

    # All rules should have failure_reasons
    evaluated = result["evaluated_rules"]
    for rule in evaluated:
        if not rule.get("matched"):
            assert "failure_reasons" in rule
            assert len(rule["failure_reasons"]) > 0
