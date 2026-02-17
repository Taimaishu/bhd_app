"""Tests for policy guard."""
import pytest
from pathlib import Path
from datetime import datetime

from bhd_cli.assistant.core.entities import AssistanceLevel, DecisionLogEntry
from bhd_cli.assistant.policy.guard import PolicyGuard


def test_policy_guard_blocks_exploit_code():
    """Test that policy guard blocks exploit code patterns."""
    guard = PolicyGuard(AssistanceLevel.VALIDATION_ONLY)

    # Test blocked patterns
    blocked_texts = [
        "Here is the exploit code for this vulnerability",
        "Let me show you payload generation for this",
        "How to bypass authentication using SQL injection",
        "Create a reverse shell script",
        "This backdoor will persist on the system",
        "DDoS attack using this method",
    ]

    for text in blocked_texts:
        assert not guard.check_content(text, {}), f"Should block: {text}"


def test_policy_guard_allows_safe_content():
    """Test that policy guard allows safe validation content."""
    guard = PolicyGuard(AssistanceLevel.VALIDATION_ONLY)

    # Test allowed patterns
    allowed_texts = [
        "Validate the authentication mechanism",
        "Document the evidence of misconfiguration",
        "Verify authorization checks are in place",
        "Test with read-only operations",
        "Capture the response for documentation",
    ]

    for text in allowed_texts:
        assert guard.check_content(text, {}), f"Should allow: {text}"


def test_policy_guard_level_0_blocks_exploitation_guidance():
    """Test that Level 0 blocks exploitation guidance."""
    guard = PolicyGuard(AssistanceLevel.VALIDATION_ONLY)

    blocked = [
        "How to exploit this vulnerability",
        "Attack vector implementation steps",
        "SQL injection payload examples",
    ]

    for text in blocked:
        assert not guard.check_content(text, {}), f"Level 0 should block: {text}"


def test_policy_guard_level_1_requires_profile(tmp_path):
    """Test that Level 1 requires a profile file."""
    # Should raise without profile
    with pytest.raises(ValueError, match="requires explicit profile file"):
        PolicyGuard(AssistanceLevel.LAB_TRAINING)

    # Should raise with invalid profile
    invalid_profile = tmp_path / "profile.json"
    invalid_profile.write_text('{"assistance_level": 0}')

    with pytest.raises(ValueError, match="explicitly set assistance_level: 1"):
        PolicyGuard(AssistanceLevel.LAB_TRAINING, profile_path=invalid_profile)

    # Should work with valid profile
    valid_profile = tmp_path / "profile.json"
    valid_profile.write_text('{"assistance_level": 1}')

    guard = PolicyGuard(AssistanceLevel.LAB_TRAINING, profile_path=valid_profile)
    assert guard.get_assistance_level() == AssistanceLevel.LAB_TRAINING


def test_policy_guard_decision_logging(tmp_path):
    """Test that decisions are logged to JSONL."""
    log_file = tmp_path / "decision_log.jsonl"
    guard = PolicyGuard(
        AssistanceLevel.VALIDATION_ONLY,
        decision_log_path=log_file
    )

    # Trigger a block
    guard.check_content("Here's the exploit code", {"test": "context"})

    # Check log was created
    assert log_file.exists()

    # Check log content
    with open(log_file) as f:
        lines = f.readlines()
        assert len(lines) == 1
        import json
        entry = json.loads(lines[0])
        assert entry["event_type"] == "policy_blocked"
        assert entry["assistance_level"] == "VALIDATION_ONLY"


def test_policy_guard_redaction(tmp_path):
    """Test that sensitive information is redacted in logs."""
    log_file = tmp_path / "decision_log.jsonl"
    guard = PolicyGuard(
        AssistanceLevel.VALIDATION_ONLY,
        decision_log_path=log_file
    )

    entry = DecisionLogEntry(
        timestamp=datetime.utcnow(),
        event_type="policy_blocked",
        assistance_level=AssistanceLevel.VALIDATION_ONLY,
        details={"pattern": "sensitive_pattern", "context": "secret_data"},
        redacted=True
    )

    guard.log_decision(entry)

    # Check redaction
    with open(log_file) as f:
        import json
        logged = json.loads(f.read())
        assert "[REDACTED]" in str(logged["details"])


def test_policy_guard_case_insensitive():
    """Test that pattern matching is case-insensitive."""
    guard = PolicyGuard(AssistanceLevel.VALIDATION_ONLY)

    # Test various cases
    blocked = [
        "EXPLOIT CODE",
        "Exploit Code",
        "exploit code",
        "eXpLoIt CoDe",
    ]

    for text in blocked:
        assert not guard.check_content(text, {}), f"Should block regardless of case: {text}"
