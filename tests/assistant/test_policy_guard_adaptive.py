"""Tests for PolicyGuard ADAPTIVE mode."""
import pytest

from bhd_cli.assistant.policy.guard import PolicyGuard
from bhd_cli.assistant.core.entities import AssistanceLevel


def test_always_blocked_patterns():
    """Test that always-blocked patterns are blocked regardless of level."""
    # Use VALIDATION_ONLY since LAB_TRAINING requires profile file
    guard = PolicyGuard(assistance_level=AssistanceLevel.VALIDATION_ONLY)

    # These should always be blocked
    blocked_content = [
        "Here is exploit code for the vulnerability",
        "Use this payload generation script",
        "Bypass authentication with this method",
        "Install this backdoor for persistence",
        "Here's a reverse shell command"
    ]

    for content in blocked_content:
        assert not guard.check_content(content, {"test": "always_blocked"})


def test_validation_only_blocks_weaponized():
    """Test that VALIDATION_ONLY blocks weaponized instructions."""
    guard = PolicyGuard(assistance_level=AssistanceLevel.VALIDATION_ONLY)

    blocked = [
        "how to exploit step-by-step instructions",
        "execution step with exploit code provided",
        "attack vector implement payload technique",
        "injection payload example for testing"
    ]

    for content in blocked:
        assert not guard.check_content(content, {"test": "validation_blocked"})


def test_adaptive_mode_allows_normal_language():
    """Test that ADAPTIVE mode allows normal security testing language."""
    guard = PolicyGuard(assistance_level=AssistanceLevel.VALIDATION_ONLY)

    # These should be allowed (reduced false positives)
    allowed_content = [
        "Test for SQL injection vulnerabilities",
        "Validate authentication controls",
        "Check for exposed services",
        "Assess the attack surface",
        "Examine the execution flow",
        "Document the observed behavior",
        "This injection point may be vulnerable"
    ]

    for content in allowed_content:
        assert guard.check_content(content, {"test": "allowed"}), f"Should allow: {content}"


def test_lab_training_allows_more():
    """Test that LAB_TRAINING level allows broader guidance."""
    # Note: LAB_TRAINING requires profile file, so skip for now
    # or test with mock profile
    pass


def test_case_insensitive_blocking():
    """Test that pattern matching is case-insensitive."""
    guard = PolicyGuard(assistance_level=AssistanceLevel.VALIDATION_ONLY)

    variations = [
        "EXPLOIT CODE example",
        "Exploit Code Example",
        "exploit code example"
    ]

    for content in variations:
        assert not guard.check_content(content, {"test": "case_check"})
