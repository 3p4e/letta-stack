"""
Test Letta agent creation and messaging.

Requires a running Letta server at localhost:8283.
"""

import pytest
from CONTENT_CREATOR_FRAMEWORK.letta_service import LettaService
from CONTENT_CREATOR_FRAMEWORK.agent_definitions import AGENT_CONFIGS
from CONTENT_CREATOR_FRAMEWORK.letta_tools import register_all_tools


@pytest.fixture(scope="module")
def letta():
    svc = LettaService(base_url="http://localhost:8283")
    register_all_tools(svc)
    svc.ensure_archives()
    svc.ensure_agents(AGENT_CONFIGS)
    return svc


def test_agents_created(letta):
    """Verify all expected agents exist."""
    expected_roles = [
        "cover", "purpose", "scope", "definitions", "raci",
        "regulatory", "procedure", "documentation", "training",
        "annex", "assembler",
    ]
    for role in expected_roles:
        agent = letta.get_agent(role)
        assert agent is not None, f"Agent '{role}' not found"
        assert agent.id is not None


def test_send_message(letta):
    """Verify we can send a message and get a response."""
    response = letta.send_message(
        "purpose",
        "Generate a short purpose statement for a Document Control SOP in EU GMP cannabis."
    )
    assert response is not None
    assert len(response) > 50  # Should be a substantial response


def test_send_message_unknown_role(letta):
    """Verify sending to unknown role raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        letta.send_message("nonexistent_role", "Hello")


def test_update_agent_context(letta):
    """Verify context update doesn't raise."""
    letta.update_agent_context("purpose", "Test context: QA_00.02 Document Control SOP")


def test_reset_agent_messages(letta):
    """Verify message reset doesn't raise."""
    letta.reset_agent_messages("purpose")
