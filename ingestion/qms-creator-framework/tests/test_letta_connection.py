"""
Test Letta server connection and basic operations.

Requires a running Letta server at localhost:8283.
"""

import pytest
from CONTENT_CREATOR_FRAMEWORK.letta_service import LettaService


@pytest.fixture(scope="module")
def letta():
    """Create a LettaService instance."""
    return LettaService(base_url="http://localhost:8283")


def test_server_health(letta):
    """Verify Letta server is reachable."""
    # The client constructor connects; if it fails, fixture creation fails
    assert letta.client is not None


def test_model_resolution(letta):
    """Verify a model is resolved from the priority list."""
    assert letta._model is not None
    assert "/" in letta._model  # e.g., "deepseek/deepseek-reasoner"


def test_list_models(letta):
    """Verify we can list available models."""
    models = letta.client.models.list()
    assert len(models) > 0
    handles = {m.handle for m in models}
    # At least one of our priority models should be available
    expected = {"deepseek/deepseek-reasoner", "openai/gpt-4o", "google_ai/gemini-2.5-pro"}
    assert len(handles & expected) > 0


def test_ensure_archives(letta):
    """Verify archives can be created/retrieved."""
    archives = letta.ensure_archives()
    assert "db1_regulatory" in archives
    assert "db2_entity_qms" in archives
    assert archives["db1_regulatory"].id is not None
    assert archives["db2_entity_qms"].id is not None
