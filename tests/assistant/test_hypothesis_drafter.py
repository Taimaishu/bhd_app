"""Tests for hypothesis drafter with schema validation."""
import pytest
from pathlib import Path

from bhd_cli.assistant.core.adaptive_mode import (
    AssistContext,
    Environment,
    TargetOwner,
    EffectiveAssistLevel
)
from bhd_cli.assistant.core.entities import Observation, ObservationCategory
from bhd_cli.assistant.core.hypothesis_drafter import HypothesisDrafter
from bhd_cli.assistant.adapters.llm.mock_provider import MockLLMProvider
from bhd_cli.assistant.policy.guard import PolicyGuard


@pytest.fixture
def mock_llm():
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def policy_guard():
    """Create policy guard."""
    return PolicyGuard()


@pytest.fixture
def drafter(mock_llm, policy_guard):
    """Create hypothesis drafter with mock provider."""
    return HypothesisDrafter(
        llm_provider=mock_llm,
        policy_guard=policy_guard
    )


@pytest.fixture
def sample_observations():
    """Create sample observations."""
    return [
        Observation(
            id="obs-1",
            source_artifact="nmap-scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service", "rdp"],
            confidence=1.0,
            data={
                "host": "10.0.0.100",
                "port": 3389,
                "service": "rdp",
                "product": "Microsoft Terminal Services",
                "version": "10.0",
                "state": "open"
            }
        ),
        Observation(
            id="obs-2",
            source_artifact="nmap-scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service", "ssh"],
            confidence=1.0,
            data={
                "host": "10.0.0.100",
                "port": 22,
                "service": "ssh",
                "product": "OpenSSH",
                "version": "8.9p1",
                "state": "open"
            }
        )
    ]


def test_drafter_standard_mode(drafter, sample_observations):
    """Test hypothesis drafting in standard mode."""
    context = AssistContext(
        environment=Environment.PROD_CLIENT,
        authorization=True,
        target_owner=TargetOwner.CLIENT,
        requested_level=EffectiveAssistLevel.STANDARD
    )

    result = drafter.draft_hypotheses(sample_observations, context, max_hypotheses=1)

    assert result["status"] == "success"
    assert result["effective_assist_level"] == "standard"
    assert len(result["hypotheses"]) > 0

    # Check hypothesis structure
    hyp = result["hypotheses"][0]
    assert "id" in hyp
    assert "title" in hyp
    assert "description" in hyp
    assert "risk_tags" in hyp
    assert "confidence" in hyp
    assert "rationale" in hyp


def test_drafter_deep_lab_mode(drafter, sample_observations):
    """Test hypothesis drafting in deep_lab mode."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = drafter.draft_hypotheses(sample_observations, context, max_hypotheses=1)

    assert result["status"] == "success"
    assert result["effective_assist_level"] == "deep_lab"
    assert "deep_lab_enabled" in result["reasons"][0]


def test_drafter_clamping_to_standard(drafter, sample_observations):
    """Test that deep_lab request is clamped to standard when conditions not met."""
    context = AssistContext(
        environment=Environment.PROD_CLIENT,  # Not lab/ctf
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = drafter.draft_hypotheses(sample_observations, context)

    assert result["status"] == "success"
    assert result["effective_assist_level"] == "standard"
    assert any("clamped" in r for r in result["reasons"])


def test_drafter_observation_clustering(drafter):
    """Test that observations are clustered properly."""
    observations = [
        Observation(
            id="obs-1",
            source_artifact="scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service"],
            confidence=1.0,
            data={"host": "10.0.0.100", "port": 22}
        ),
        Observation(
            id="obs-2",
            source_artifact="scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service"],
            confidence=1.0,
            data={"host": "10.0.0.100", "port": 80}
        ),
        Observation(
            id="obs-3",
            source_artifact="scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service"],
            confidence=1.0,
            data={"host": "10.0.0.200", "port": 22}
        )
    ]

    clusters = drafter._cluster_observations(observations)

    # Should have 2 clusters: (service, 10.0.0.100) and (service, 10.0.0.200)
    assert len(clusters) == 2


def test_drafter_with_failing_provider():
    """Test drafter behavior when LLM provider fails."""
    failing_provider = MockLLMProvider(should_fail=True)
    policy_guard = PolicyGuard()
    drafter = HypothesisDrafter(failing_provider, policy_guard)

    observations = [
        Observation(
            id="obs-1",
            source_artifact="scan-1",
            category=ObservationCategory.SERVICE,
            tags=["service"],
            confidence=1.0,
            data={"host": "10.0.0.100", "port": 22}
        )
    ]

    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.STANDARD
    )

    # Should handle failure gracefully
    result = drafter.draft_hypotheses(observations, context)

    assert result["status"] == "success"
    # No hypotheses generated due to failure
    assert len(result["hypotheses"]) == 0


def test_drafter_schema_validation(drafter, sample_observations):
    """Test that generated hypotheses are validated against schema."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.STANDARD
    )

    result = drafter.draft_hypotheses(sample_observations, context)

    # All hypotheses should be valid
    for hyp in result["hypotheses"]:
        # Required fields
        assert "id" in hyp
        assert "related_observations" in hyp
        assert "title" in hyp
        assert "description" in hyp
        assert "risk_tags" in hyp
        assert "confidence" in hyp
        assert "rationale" in hyp

        # Type checks
        assert isinstance(hyp["related_observations"], list)
        assert isinstance(hyp["risk_tags"], list)
        assert isinstance(hyp["confidence"], (int, float))
        assert 0 <= hyp["confidence"] <= 1
