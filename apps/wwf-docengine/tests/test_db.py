"""app/db.py against a real Postgres — the layer that had no executed coverage.

The stale-job reaper gets the most attention here because it is the piece with
the worst failure mode: it runs once at startup inside a broad `except
Exception: log.warning(...)`, so every way it can be wrong is silent. A job
wrongly reaped destroys a running build's record; a job wrongly SPARED sits at
'running' forever with a poller waiting on it. Both directions are pinned.
"""
import uuid

import pytest

from app import db

pytestmark = pytest.mark.asyncio


async def seed_job(pool, *, status: str, age_minutes: int = 0,
                   error: str | None = None, kind: str = "workflow") -> str:
    """Insert a job with a backdated updated_at — the only thing the reaper
    keys on. Bypasses job_create deliberately: the point is to control
    updated_at, which job_create never lets a caller set."""
    jid = str(uuid.uuid4())
    await pool.execute(
        "INSERT INTO docengine.jobs (id, kind, status, error, updated_at)"
        " VALUES ($1, $2, $3, $4, now() - make_interval(mins => $5))",
        jid, kind, status, error, age_minutes)
    return jid


async def status_of(pool, jid: str) -> str:
    return await pool.fetchval("SELECT status FROM docengine.jobs WHERE id = $1", jid)


async def test_reaper_fails_jobs_abandoned_by_a_killed_worker(dbpool):
    stale_running = await seed_job(dbpool, status="running", age_minutes=120)
    stale_queued = await seed_job(dbpool, status="queued", age_minutes=999)

    assert await db.reap_stale_jobs() == 2

    assert await status_of(dbpool, stale_running) == "failed"
    assert await status_of(dbpool, stale_queued) == "failed"
    err = await dbpool.fetchval(
        "SELECT error FROM docengine.jobs WHERE id = $1", stale_running)
    assert "abandoned" in err and "worker killed mid-run" in err


async def test_reaper_spares_everything_it_must(dbpool):
    """The dangerous direction. Three distinct reasons a job must survive:

    - `fresh`: still making progress. job_update() touches updated_at on every
      stage change, so an active build is continuously young.
    - `awaiting_review`: blocked on a HUMAN. Legitimately days old — reaping it
      would destroy the review gate, so it must never appear in the predicate.
    - `done`: terminal. Reaping it would rewrite finished history.
    """
    fresh = await seed_job(dbpool, status="running", age_minutes=5)
    review = await seed_job(dbpool, status="awaiting_review", age_minutes=5000)
    done = await seed_job(dbpool, status="done", age_minutes=5000)
    failed = await seed_job(dbpool, status="failed", age_minutes=5000)

    assert await db.reap_stale_jobs() == 0

    assert await status_of(dbpool, fresh) == "running"
    assert await status_of(dbpool, review) == "awaiting_review"
    assert await status_of(dbpool, done) == "done"
    assert await status_of(dbpool, failed) == "failed"


async def test_reaper_keeps_an_error_the_job_already_recorded(dbpool):
    """A job that recorded WHY it failed and then died before its status caught
    up must keep that message — it is the only diagnosis anyone has. The
    COALESCE(NULLIF(error,'')) only fills in a blank one."""
    jid = await seed_job(dbpool, status="running", age_minutes=300,
                         error="letta: connection reset")
    assert await db.reap_stale_jobs() == 1
    row = await dbpool.fetchrow(
        "SELECT status, error FROM docengine.jobs WHERE id = $1", jid)
    assert row["status"] == "failed"
    assert row["error"] == "letta: connection reset"


async def test_reaper_threshold_is_honoured(dbpool):
    """Just inside the window survives; just outside does not. Pins that the
    cutoff is really applied rather than the predicate matching everything."""
    inside = await seed_job(dbpool, status="running", age_minutes=59)
    outside = await seed_job(dbpool, status="running", age_minutes=61)
    assert await db.reap_stale_jobs(60) == 1
    assert await status_of(dbpool, inside) == "running"
    assert await status_of(dbpool, outside) == "failed"


async def test_reaper_is_a_no_op_without_a_pool():
    """Called before init() (or in degraded mode) it must return 0, not raise —
    main.py's lifespan calls it before the service is known to have a DB."""
    await db.close()
    assert not db.ready()
    assert await db.reap_stale_jobs() == 0


async def test_job_round_trip(dbpool):
    """job_create -> job_get -> job_update, incl. the jsonb columns that
    job_update special-cases and the updated_at bump the reaper depends on."""
    jid = await db.job_create("workflow", {"questionnaire": "sop_qc"}, created_by="tester")
    job = await db.job_get(jid)
    assert job["status"] == "queued" and job["kind"] == "workflow"
    assert job["payload"]["questionnaire"] == "sop_qc"

    before = await dbpool.fetchval(
        "SELECT updated_at FROM docengine.jobs WHERE id = $1", jid)
    await db.job_update(jid, status="done", stage="done", result={"document_id": "x"})
    after = await db.job_get(jid)
    assert after["status"] == "done"
    assert after["result"]["document_id"] == "x"
    bumped = await dbpool.fetchval(
        "SELECT updated_at FROM docengine.jobs WHERE id = $1", jid)
    assert bumped >= before, "job_update must move updated_at — the reaper keys on it"

    assert await db.job_get("00000000-0000-0000-0000-000000000000") is None


async def test_document_create_and_read_back(dbpool):
    jid = await db.job_create("build", {})
    did = await db.document_create(jid, {
        "code": "QCSOP-999", "doctype": "SOP", "title_mk": "МК", "title_en": "EN",
        "version": "1.0", "path": "/data/out/QCSOP-999.docx", "bytes": 4242,
        "verify": "RESULT: PASS",
    })
    doc = await db.document_get(did)
    assert doc["code"] == "QCSOP-999" and doc["bytes"] == 4242
    assert doc["verify"] == "RESULT: PASS"
    assert any(d["id"] == did for d in await db.documents_list())
