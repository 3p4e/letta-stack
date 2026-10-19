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


async def test_job_claim_moves_a_job_only_once(dbpool):
    """Two reviewers approving at once: only one claim moves the row out of awaiting_review."""
    jid = await seed_job(dbpool, status="awaiting_review")
    assert await db.job_claim(jid, "awaiting_review", "running") is True
    assert await db.job_claim(jid, "awaiting_review", "running") is False
    assert await status_of(dbpool, jid) == "running"


async def seed_doc_job(pool, *, code: str, status: str, age_minutes: int, error: str | None = None) -> str:
    import json
    jid = str(uuid.uuid4())
    await pool.execute(
        "INSERT INTO docengine.jobs (id, kind, status, error, payload, result, created_at)"
        " VALUES ($1, 'workflow', $2, $3, $4::jsonb, $5::jsonb, now() - make_interval(mins => $6))",
        jid, status, error, json.dumps({"meta": {"code": code}}),
        json.dumps({"markdown": f"# 6.0 {status} {age_minutes}"}), age_minutes)
    return jid


async def test_parent_sop_prefers_the_registered_document_over_newer_drafts(dbpool):
    """Review 14.10.2026: the newest job of ANY status used to be the parent an annex read, so a failed or
    returned draft written after the approved SOP replaced it."""
    done = await seed_doc_job(dbpool, code="WHSOP_003", status="done", age_minutes=600)
    await seed_doc_job(dbpool, code="WHSOP_003", status="failed", age_minutes=10)
    await seed_doc_job(dbpool, code="WHSOP_003", status="failed", age_minutes=5, error="returned for revision: §3")
    await seed_doc_job(dbpool, code="OTHER", status="done", age_minutes=1)
    got = await db.job_latest_markdown_by_code("WHSOP_003")
    assert got["job_id"] == done and got["status"] == "done" and got["markdown"].startswith("# 6.0 done")


async def test_parent_sop_never_reads_a_returned_draft(dbpool):
    await seed_doc_job(dbpool, code="X", status="failed", age_minutes=5, error="returned for revision: no")
    assert await db.job_latest_markdown_by_code("X") is None
    review = await seed_doc_job(dbpool, code="X", status="awaiting_review", age_minutes=50)
    await seed_doc_job(dbpool, code="X", status="failed", age_minutes=1, error="sections are not bilingual: 3.0")
    assert (await db.job_latest_markdown_by_code("X"))["job_id"] == review


async def test_the_document_list_tells_controlled_versions_from_copies(dbpool):
    jid = await db.job_create("workflow", {"meta": {"code": "WHSOP_003"}})
    base = {"code": "WHSOP_003", "doctype": "SOP", "path": "/x", "bytes": 1, "verify": "RESULT: PASS"}
    await db.document_create(jid, base)
    await db.document_create(None, base)
    rows = await db.documents_list()
    assert sorted(r["job_id"] is None for r in rows) == [False, True]
    assert next(r for r in rows if r["job_id"])["job_id"] == jid


async def test_a_reference_document_is_stored_once_per_kind_code_and_version(dbpool):
    doc = {"kind": "approved", "code": "QCSOP022", "version": "01", "title_en": "Chemicals", "markdown": "text " * 10,
           "source": {"name": "QCSOP 022.docx", "drive_id": "abc"}}
    rid, changed = await db.reference_upsert(doc, "sha-1")
    assert changed
    assert await db.reference_upsert(doc, "sha-1") == (rid, False)        # the same text is not rewritten
    rid2, changed = await db.reference_upsert({**doc, "markdown": "new " * 10}, "sha-2")
    assert rid2 == rid and changed
    await db.reference_set_ragflow(rid, "rf-1")
    row = await db.reference_get(rid)
    assert row["markdown"].startswith("new") and row["source"]["drive_id"] == "abc" and row["ragflow_doc_id"] == "rf-1"
    wip, _ = await db.reference_upsert({**doc, "kind": "wip"}, "sha-1")
    assert wip != rid
    listed = await db.reference_list("approved")
    assert [r["id"] for r in listed] == [rid] and "markdown" not in listed[0] and listed[0]["chars"] == 40


async def test_a_brief_keeps_every_change_and_refuses_a_stale_write(dbpool):
    from app import brief as B
    b = B.new_brief("sop", {"title_en": "Sampling"})
    bid = await db.brief_create(b, "bn")
    got = await db.brief_get(bid)
    new, events = B.apply_patch(got, {"rev": 0, "set": {"doc.purpose": "Sample FP"}}, "bn")
    assert await db.brief_save(new, 0, events)
    assert not await db.brief_save(new, 0, events)                       # the second writer of rev 0 loses
    sid = await db.brief_source_add(bid, 1, "bn", {"name": "old.docx", "kind": "docx", "bytes": 10, "sha256": "s",
                                                   "text": "Old SOP"})
    got = await db.brief_get(bid)
    assert got["rev"] == 2 and got["fields"]["doc.purpose"]["value"] == "Sample FP"
    assert got["sources"][0]["name"] == "old.docx" and "text" not in got["sources"][0]
    assert (await db.brief_sources(bid))[0]["text"] == "Old SOP"
    assert await db.brief_source_remove(bid, sid, "bn")
    ops = [e["op"] for e in await db.brief_events(bid)]
    assert ops == ["create", "set", "source_add", "source_remove"]
    assert [x["id"] for x in await db.brief_list()] == [bid]
