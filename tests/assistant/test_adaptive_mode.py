"""Tests for ADAPTIVE mode context evaluation."""
import pytest

from bhd_cli.assistant.core.adaptive_mode import (
    AssistContext,
    Environment,
    TargetOwner,
    EffectiveAssistLevel,
    evaluate_assist_level
)


def test_standard_mode_default():
    """Test that standard mode is granted by default."""
    context = AssistContext(
        environment=Environment.PROD_CLIENT,
        authorization=True,
        target_owner=TargetOwner.CLIENT,
        requested_level=EffectiveAssistLevel.STANDARD
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.STANDARD
    assert "requested_level=standard" in result.reasons


def test_deep_lab_granted_when_conditions_met():
    """Test that deep_lab is granted when all conditions are met."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.DEEP_LAB
    assert "deep_lab_enabled" in result.reasons[0]


def test_deep_lab_clamped_prod_environment():
    """Test that deep_lab is clamped to standard in prod environment."""
    context = AssistContext(
        environment=Environment.PROD_CLIENT,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.STANDARD
    assert any("clamped: environment=prod_client" in r for r in result.reasons)


def test_deep_lab_clamped_no_authorization():
    """Test that deep_lab is clamped without authorization."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=False,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.STANDARD
    assert any("clamped: authorization=false" in r for r in result.reasons)


def test_deep_lab_clamped_client_target():
    """Test that deep_lab is clamped for client-owned targets."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.CLIENT,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.STANDARD
    assert any("clamped: target_owner=client" in r for r in result.reasons)


def test_deep_lab_works_in_ctf():
    """Test that deep_lab works in CTF environment."""
    context = AssistContext(
        environment=Environment.CTF,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    result = evaluate_assist_level(context)

    assert result.effective_level == EffectiveAssistLevel.DEEP_LAB


def test_context_serialization():
    """Test that context can be serialized to dict."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.DEEP_LAB
    )

    context_dict = context.to_dict()

    assert context_dict["environment"] == "lab"
    assert context_dict["authorization"] is True
    assert context_dict["target_owner"] == "self"
    assert context_dict["requested_level"] == "deep_lab"


def test_evaluation_serialization():
    """Test that evaluation can be serialized to dict."""
    context = AssistContext(
        environment=Environment.LAB,
        authorization=True,
        target_owner=TargetOwner.SELF,
        requested_level=EffectiveAssistLevel.STANDARD
    )

    result = evaluate_assist_level(context)
    result_dict = result.to_dict()

    assert "effective_level" in result_dict
    assert "reasons" in result_dict
    assert "context" in result_dict
    assert isinstance(result_dict["reasons"], list)
