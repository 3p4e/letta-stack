"""
Test Letta archive operations: create, ingest, search.

Requires a running Letta server at localhost:8283.
"""

import pytest
from pathlib import Path
from CONTENT_CREATOR_FRAMEWORK.letta_service import LettaService


@pytest.fixture(scope="module")
def letta():
    svc = LettaService(base_url="http://localhost:8283")
    svc.ensure_archives()
    return svc


def test_archives_exist(letta):
    """Verify both archives are accessible."""
    db1 = letta.get_archive("db1_regulatory")
    db2 = letta.get_archive("db2_entity_qms")
    assert db1 is not None
    assert db2 is not None


def test_ingest_passage(letta):
    """Verify we can create a passage in an archive."""
    archive = letta.get_archive("db1_regulatory")
    letta.client.archives.passages.create(
        archive_id=archive.id,
        text="EU GMP Annex 7 requires cannabis facilities to maintain document control procedures.",
        tags=["test", "eu-gmp"],
    )


def test_search_archive(letta):
    """Verify archive search returns results."""
    results = letta.search_archive("db1_regulatory", "document control EU GMP cannabis", top_k=3)
    assert isinstance(results, list)
    # We ingested at least one passage above
    if results:
        assert "text" in results[0]
        assert "score" in results[0]


def test_dual_db_search(letta):
    """Verify dual-DB search returns structured results."""
    results = letta.dual_db_search("quality management system", top_k=3)
    assert "db1_results" in results
    assert "db2_results" in results
    assert isinstance(results["db1_results"], list)
    assert isinstance(results["db2_results"], list)


def test_chunk_text():
    """Test the text chunking helper."""
    text = "A" * 2500
    chunks = LettaService._chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_short_text():
    """Short text should return a single chunk."""
    chunks = LettaService._chunk_text("Short text", chunk_size=1000, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == "Short text"
