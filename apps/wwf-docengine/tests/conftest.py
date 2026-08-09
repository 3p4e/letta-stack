"""Real-Postgres fixture for the DocEngine persistence layer.

Until now every DocEngine test ran against fakes: `db.init()` returns early
when DOCENGINE_DATABASE_URL is empty ("tests / degraded mode"), so app/db.py —
job_create, job_update, document_create, reap_stale_jobs — had NO executed
coverage at all. That is how `reap_stale_jobs` shipped never having run once:
its only caller wraps it in `except Exception: log.warning(...)`, so a wrong
column name would have surfaced as a startup warning nobody reads while stale
jobs piled up forever — exactly the condition the function exists to prevent.

`db` is a module with a global pool, so the fixture is function-scoped and
opens/closes per test: cheap against a local Postgres and it keeps one test's
failure from poisoning the next. Tests SKIP rather than fail when no DSN is
configured, so `pytest` in a bare checkout still works; CI sets the variable,
which is what makes the coverage real.
"""
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db  # noqa: E402
from app.config import settings  # noqa: E402


@pytest_asyncio.fixture
async def dbpool():
    """An initialised, empty docengine schema. Skips when no DSN is set."""
    if not settings.database_url:
        pytest.skip("DOCENGINE_DATABASE_URL not set — DB-backed tests skipped")
    await db.init()
    assert db.ready(), "db.init() did not open a pool despite a DSN being set"
    # documents references jobs, so truncate together. No RESTART IDENTITY:
    # both tables key on uuids, so there is no sequence to restart.
    await db.pool().execute("TRUNCATE docengine.documents, docengine.jobs CASCADE")
    try:
        yield db.pool()
    finally:
        await db.close()
