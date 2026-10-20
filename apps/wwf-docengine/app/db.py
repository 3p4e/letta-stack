# docengine.app.db — workflow state in Postgres (own schema `docengine`).
# This fixes the qms-creator per-worker in-memory bug class: any uvicorn
# worker can serve any poll because state lives in the database.
from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg

from .config import settings

_pool: asyncpg.Pool | None = None

_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS docengine;
CREATE TABLE IF NOT EXISTS docengine.jobs (
  id          uuid PRIMARY KEY,
  kind        text NOT NULL,                 -- 'workflow' | 'build'
  status      text NOT NULL DEFAULT 'queued',-- queued|running|awaiting_review|done|failed
  stage       text NOT NULL DEFAULT '',
  payload     jsonb NOT NULL DEFAULT '{}'::jsonb,
  result      jsonb NOT NULL DEFAULT '{}'::jsonb,
  error       text,
  created_by  text NOT NULL DEFAULT '',
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS docengine.documents (
  id          uuid PRIMARY KEY,
  job_id      uuid REFERENCES docengine.jobs(id),
  code        text NOT NULL,
  doctype     text NOT NULL,
  title_mk    text NOT NULL DEFAULT '',
  title_en    text NOT NULL DEFAULT '',
  version     text NOT NULL DEFAULT '1.0',
  path        text NOT NULL,
  bytes       int  NOT NULL,
  verify      text NOT NULL,                 -- full pp_verify PASS report
  created_at  timestamptz NOT NULL DEFAULT now()
);
-- Documents the engine did not write (Head of QC, 18.10.2026): the approved, in-use documents (kind 'approved',
-- text of the Word file; the signed scan is referenced, never indexed) and the work in progress from the ACME_SOP
-- drafts folder (kind 'wip'). One row per kind + code + version.
CREATE TABLE IF NOT EXISTS docengine.reference_docs (
  id             uuid PRIMARY KEY,
  kind           text NOT NULL,                 -- 'approved' | 'wip'
  code           text NOT NULL,
  parent         text NOT NULL DEFAULT '',
  version        text NOT NULL DEFAULT '',
  title_mk       text NOT NULL DEFAULT '',
  title_en       text NOT NULL DEFAULT '',
  effective_date text NOT NULL DEFAULT '',
  department     text NOT NULL DEFAULT '',
  package        text NOT NULL DEFAULT '',
  source         jsonb NOT NULL DEFAULT '{}'::jsonb, -- {name, drive_id, drive_scan_ids, folder}
  markdown       text NOT NULL,
  sha256         text NOT NULL,
  ragflow_doc_id text NOT NULL DEFAULT '',
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kind, code, version)
);
-- The Document Brief the single workflow edits (18.10.2026), its full change history and its uploaded sources.
CREATE TABLE IF NOT EXISTS docengine.briefs (
  id          uuid PRIMARY KEY,
  rev         int  NOT NULL DEFAULT 0,
  body        jsonb NOT NULL,                -- package, questionnaire, parent_sop, meta, fields, annexes, job_ids, status
  created_by  text NOT NULL DEFAULT '',
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS docengine.brief_events (
  id        bigserial PRIMARY KEY,
  brief_id  uuid NOT NULL REFERENCES docengine.briefs(id) ON DELETE CASCADE,
  rev       int  NOT NULL,
  at        timestamptz NOT NULL DEFAULT now(),
  actor     text NOT NULL DEFAULT '',
  op        text NOT NULL,
  key       text NOT NULL DEFAULT '',
  before    jsonb,
  after     jsonb
);
CREATE TABLE IF NOT EXISTS docengine.brief_sources (
  id         uuid PRIMARY KEY,
  brief_id   uuid NOT NULL REFERENCES docengine.briefs(id) ON DELETE CASCADE,
  name       text NOT NULL,
  kind       text NOT NULL,
  bytes      int  NOT NULL,
  sha256     text NOT NULL,
  text       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
-- What a source is for (Head of QC, 19.10.2026): reference contents, a formatting example, or an executed example.
ALTER TABLE docengine.brief_sources ADD COLUMN IF NOT EXISTS role text NOT NULL DEFAULT 'content';
CREATE INDEX IF NOT EXISTS de_brief_events ON docengine.brief_events(brief_id, rev);
CREATE INDEX IF NOT EXISTS de_jobs_status ON docengine.jobs(status);
CREATE INDEX IF NOT EXISTS de_docs_code ON docengine.documents(code);
"""


# One fixed key for the schema bootstrap's advisory lock (any constant; only this service takes it).
_SCHEMA_LOCK = 72640301


async def create_schema(c: asyncpg.Connection) -> None:
    """The DDL under one transaction-scoped advisory lock. Several uvicorn workers run init() at the same moment, and
    two CREATE … IF NOT EXISTS racing on an empty database lose to each other with a unique violation on pg_type /
    pg_class — a worker died at startup (review 19.10.2026). The lock serialises them; the second finds the schema."""
    async with c.transaction():
        await c.execute("SELECT pg_advisory_xact_lock($1)", _SCHEMA_LOCK)
        await c.execute(_SCHEMA)


async def init() -> None:
    global _pool
    if not settings.database_url:
        return  # tests / degraded mode: endpoints depending on DB 503
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    async with _pool.acquire() as c:
        await create_schema(c)


async def close() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("docengine db not configured")
    return _pool


def ready() -> bool:
    return _pool is not None


# ---- job helpers ----
async def job_create(kind: str, payload: dict, created_by: str = "") -> str:
    jid = str(uuid.uuid4())
    await pool().execute(
        "INSERT INTO docengine.jobs (id, kind, payload, created_by) VALUES ($1,$2,$3,$4)",
        jid, kind, json.dumps(payload), created_by,
    )
    return jid


async def job_update(jid: str, **fields: Any) -> None:
    sets, vals = ["updated_at = now()"], []
    for k, v in fields.items():
        if k in ("payload", "result"):
            v = json.dumps(v)
        vals.append(v)
        sets.append(f"{k} = ${len(vals)}")
    vals.append(jid)
    # B608 suppressed below: `sets` interpolates only CODE-controlled column
    # names (the **fields kwargs at this module's own call sites: status/
    # stage/error/result/payload). Every VALUE is a real asyncpg bind
    # parameter in *vals, never interpolated. Same parametrized-with-
    # code-controlled-columns pattern the backend documents in app/demo_org.py.
    await pool().execute(
        f"UPDATE docengine.jobs SET {', '.join(sets)} WHERE id = ${len(vals)}", *vals  # nosec B608
    )


async def job_finish(jid: str, **fields: Any) -> bool:
    """A terminal write of the pipeline (done / awaiting_review / failed), refused on a row the reaper has already
    failed: a slow job that outlived STALE_JOB_MINUTES used to come back and overwrite 'abandoned' with 'done', and
    its annexes started on a job the Jobs screen had shown as failed (review 19.10.2026). True when written."""
    sets, vals = ["updated_at = now()"], []
    for k, v in fields.items():
        if k in ("payload", "result"):
            v = json.dumps(v)
        vals.append(v)
        sets.append(f"{k} = ${len(vals)}")
    vals.append(jid)
    r = await pool().fetchval(
        f"UPDATE docengine.jobs SET {', '.join(sets)} WHERE id = ${len(vals)} AND status <> 'failed' RETURNING id",  # nosec B608
        *vals)
    return r is not None


async def job_stop(jid: str, by: str) -> bool:
    """Stop a queued or running job (Head of QC, 20.10.2026: "an option to pause or stop a job that is currently running,
    even if it's by mistake"). The row is failed at once; the worker sees it at its next exchange (job_touch) and stops,
    and job_finish never writes over it. True when the job was stopped."""
    r = await pool().fetchval(
        "UPDATE docengine.jobs SET status='failed', updated_at=now(), error=$2 "
        "WHERE id=$1 AND status IN ('queued','running') RETURNING id", jid, f"stopped by {by or 'a user'}")
    return r is not None


async def job_touch(jid: str) -> str | None:
    """Bump updated_at (the reaper's only signal) and return the job's status; None when the row is gone. Called before
    every exchange with an agent, so a job still working is never reaped and one the reaper failed stops working."""
    return await pool().fetchval("UPDATE docengine.jobs SET updated_at = now() WHERE id = $1 RETURNING status", jid)


# A job is only ever advanced by the worker that owns it, so a worker killed
# mid-run (OOM, redeploy) leaves its row at 'running'/'queued' forever: the
# poller waits on it indefinitely and nothing ever cleans it up. There is no
# lease to renew, so age is the only signal available — and a real build is
# bounded by the /build timeout, so anything far past that is dead.
STALE_JOB_MINUTES = 60


async def reap_stale_jobs(older_than_minutes: int = STALE_JOB_MINUTES) -> int:
    """Fail jobs left mid-flight by a killed worker. Returns how many.

    Runs at startup: a redeploy is exactly when the previous worker was killed,
    so it is both the moment stale rows appear and the moment something is
    running to notice. Uses updated_at, which every job_update() touches, so a
    job still making progress is never reaped."""
    if _pool is None:
        return 0
    rows = await pool().fetch(
        "UPDATE docengine.jobs SET status='failed', updated_at=now(),"
        "   error = COALESCE(NULLIF(error,''), 'abandoned: no progress for '"
        "                    || $1::text || ' minutes (worker killed mid-run)')"
        " WHERE status IN ('queued','running')"
        "   AND updated_at < now() - ($1::text || ' minutes')::interval"
        " RETURNING id", str(older_than_minutes))
    return len(rows)


async def job_get(jid: str) -> dict | None:
    r = await pool().fetchrow("SELECT * FROM docengine.jobs WHERE id = $1", jid)
    if not r:
        return None
    d = dict(r)
    for k in ("payload", "result"):
        if isinstance(d.get(k), str):
            d[k] = json.loads(d[k])
    d["id"] = str(d["id"])
    for k in ("created_at", "updated_at"):
        d[k] = d[k].isoformat()
    return d


async def job_claim(jid: str, from_status: str, to_status: str) -> bool:
    """Move a job from one status to another only if it is still in `from_status`.

    One atomic UPDATE, so two reviewers pressing Approve at once cannot both
    register the document: the second finds the row already moved and gets False."""
    r = await pool().fetchval(
        "UPDATE docengine.jobs SET status = $3, updated_at = now() "
        "WHERE id = $1 AND status = $2 RETURNING id", jid, from_status, to_status)
    return r is not None


async def document_create(job_id: str | None, meta: dict) -> str:
    did = str(uuid.uuid4())
    await pool().execute(
        """INSERT INTO docengine.documents
           (id, job_id, code, doctype, title_mk, title_en, version, path, bytes, verify)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
        did, job_id, meta["code"], meta["doctype"], meta.get("title_mk", ""),
        meta.get("title_en", ""), meta.get("version", "1.0"), meta["path"],
        meta["bytes"], meta["verify"],
    )
    return did


async def documents_list(limit: int = 100) -> list[dict]:
    rows = await pool().fetch(
        "SELECT id, job_id, code, doctype, title_mk, title_en, version, bytes, created_at"
        " FROM docengine.documents ORDER BY created_at DESC LIMIT $1", limit,
    )
    out = []
    for r in rows:
        d = dict(r)
        d["id"] = str(d["id"])
        # The Library tells a controlled version (from a workflow job) from a format-only copy (POST /build).
        d["job_id"] = str(d["job_id"]) if d["job_id"] else None
        d["created_at"] = d["created_at"].isoformat()
        out.append(d)
    return out


async def documents_verify_recent(limit: int = 6) -> list[dict]:
    """The newest registry rows with their pp_verify report (GET /engine/environment)."""
    rows = await pool().fetch(
        "SELECT code, verify, created_at FROM docengine.documents ORDER BY created_at DESC LIMIT $1", limit)
    return [{"code": r["code"], "verify": r["verify"], "created_at": r["created_at"].isoformat()} for r in rows]


async def document_get(did: str) -> dict | None:
    r = await pool().fetchrow("SELECT * FROM docengine.documents WHERE id = $1", did)
    if not r:
        return None
    d = dict(r)
    d["id"] = str(d["id"])
    d["job_id"] = str(d["job_id"]) if d["job_id"] else None
    d["created_at"] = d["created_at"].isoformat()
    return d


async def job_latest_markdown_by_code(code: str) -> dict | None:
    """The parent SOP an annex job reads (Head of QC, 13.10.2026: an annex form must capture what the SOP's
    §6 writes into it): {markdown, job_id, status} of the best job whose document code is `code`.

    A registered document (done) first, then one awaiting a person's review, then anything else that holds
    assembled Markdown; newest first within each. A draft a reviewer returned for revision is never used.
    It used to be simply the newest job of any status, so a failed or returned draft written after the
    approved SOP became the source of every annex built from then on (review 14.10.2026)."""
    from .house_codes import normalize
    # Jobs written before the house code form (18.10.2026) hold "WHSOP_003" or "QCSOP 11": the candidates are
    # normalised in Python, as the register and the Library are — SQL that only removed separators left "QCSOP11"
    # unequal to "QCSOP011" (review 19.10.2026).
    house = normalize(code) or code
    rows = await pool().fetch(
        "SELECT id, status, payload->'meta'->>'code' AS code FROM docengine.jobs"
        " WHERE result->>'markdown' IS NOT NULL"
        "   AND NOT (status = 'failed' AND COALESCE(error, '') LIKE 'returned for revision%')"
        " ORDER BY CASE status WHEN 'done' THEN 0 WHEN 'awaiting_review' THEN 1 ELSE 2 END, created_at DESC")
    for r in rows:
        if r["code"] == code or (r["code"] and normalize(r["code"]) == house):
            md = await pool().fetchval("SELECT result->>'markdown' FROM docengine.jobs WHERE id = $1", r["id"])
            return {"markdown": md, "job_id": str(r["id"]), "status": r["status"]}
    return None


async def codes_in_use() -> set[str]:
    """Document codes the engine itself holds: registered documents and every job not failed. A number an open
    draft carries is taken, so two drafts are never given the same next free code."""
    from .house_codes import normalize
    rows = await pool().fetch(
        "SELECT code FROM docengine.documents"
        " UNION SELECT payload->'meta'->>'code' FROM docengine.jobs"
        "  WHERE status <> 'failed' AND payload->'meta'->>'code' IS NOT NULL")
    return {normalize(r["code"]) or r["code"] for r in rows if r["code"]}       # house form (review 19.10.2026)


async def codes_of_brief(brief_id: str) -> set[str]:
    """Codes held by the jobs a brief started (its earlier builds and their annexes): a rebuild reuses them."""
    if not brief_id:
        return set()
    from .house_codes import normalize
    rows = await pool().fetch("SELECT payload->'meta'->>'code' AS code FROM docengine.jobs WHERE payload->>'brief_id' = $1",
                              brief_id)
    return {normalize(r["code"]) or r["code"] for r in rows if r["code"]}       # as codes_in_use, so they subtract


async def job_merge_result(jid: str, extra: dict) -> None:
    """Add keys to a job's result in one statement, so a concurrent update of other keys is never lost."""
    await pool().execute("UPDATE docengine.jobs SET result = COALESCE(result, '{}'::jsonb) || $2::jsonb, updated_at = now()"
                         " WHERE id = $1", jid, json.dumps(extra))


# ---- reference documents (approved and work in progress, not written by the engine) ----
_REF_COLS = ("kind", "code", "parent", "version", "title_mk", "title_en", "effective_date", "department", "package")


def _ref_row(r, with_text: bool = False) -> dict:
    d = {k: r[k] for k in _REF_COLS}
    d.update(id=str(r["id"]), sha256=r["sha256"], ragflow_doc_id=r["ragflow_doc_id"],
             source=json.loads(r["source"]) if isinstance(r["source"], str) else r["source"],
             updated_at=r["updated_at"].isoformat(), chars=r["chars"] if "chars" in r.keys() else None)
    if with_text:
        d["markdown"] = r["markdown"]
    return d


async def reference_get_key(kind: str, code: str, version: str) -> dict | None:
    r = await pool().fetchrow("SELECT *, length(markdown) AS chars FROM docengine.reference_docs"
                              " WHERE kind=$1 AND code=$2 AND version=$3", kind, code, version)
    return _ref_row(r) if r else None


async def reference_upsert(doc: dict, sha: str) -> tuple[str, bool]:
    """Insert or replace one reference document. Returns (id, changed): an identical text is not rewritten."""
    old = await reference_get_key(doc["kind"], doc["code"], doc.get("version", ""))
    if old and old["sha256"] == sha:
        return old["id"], False
    rid = old["id"] if old else str(uuid.uuid4())
    vals = [doc.get(k, "") for k in _REF_COLS]
    await pool().execute(
        """INSERT INTO docengine.reference_docs (id, kind, code, parent, version, title_mk, title_en, effective_date,
               department, package, source, markdown, sha256)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
           ON CONFLICT (kind, code, version) DO UPDATE SET parent=$4, title_mk=$6, title_en=$7, effective_date=$8,
               department=$9, package=$10, source=$11, markdown=$12, sha256=$13, updated_at=now()""",
        rid, *vals, json.dumps(doc.get("source") or {}), doc["markdown"], sha)
    return rid, True


async def reference_set_ragflow(rid: str, ragflow_doc_id: str) -> None:
    await pool().execute("UPDATE docengine.reference_docs SET ragflow_doc_id=$2, updated_at=now() WHERE id=$1",
                         rid, ragflow_doc_id)


async def reference_list(kind: str = "") -> list[dict]:
    rows = await pool().fetch(
        "SELECT id, kind, code, parent, version, title_mk, title_en, effective_date, department, package, source,"
        "       sha256, ragflow_doc_id, updated_at, length(markdown) AS chars, '' AS markdown"
        " FROM docengine.reference_docs WHERE ($1 = '' OR kind = $1) ORDER BY code, version", kind)
    return [_ref_row(r) for r in rows]


async def reference_get(rid: str) -> dict | None:
    r = await pool().fetchrow("SELECT *, length(markdown) AS chars FROM docengine.reference_docs WHERE id=$1", rid)
    return _ref_row(r, with_text=True) if r else None


async def jobs_open_by_code() -> dict[str, list[dict]]:
    """Workflow jobs not failed, by house-normalised document code (the Library's draft shelf)."""
    from .house_codes import normalize
    rows = await pool().fetch(
        "SELECT id, status, stage, payload->'meta'->>'code' AS code, payload->'meta'->>'title_en' AS title_en,"
        "       updated_at FROM docengine.jobs"
        " WHERE kind='workflow' AND status <> 'failed' AND payload->'meta'->>'code' IS NOT NULL"
        " ORDER BY updated_at DESC")
    out: dict[str, list[dict]] = {}
    for r in rows:
        code = normalize(r["code"]) or r["code"]
        out.setdefault(code, []).append({"id": str(r["id"]), "status": r["status"], "stage": r["stage"],
                                         "title_en": r["title_en"] or "", "updated_at": r["updated_at"].isoformat()})
    return out


# ---- Document Briefs ----
def _brief_row(r) -> dict:
    body = json.loads(r["body"]) if isinstance(r["body"], str) else r["body"]
    return {**body, "id": str(r["id"]), "rev": r["rev"], "created_by": r["created_by"],
            "created_at": r["created_at"].isoformat(), "updated_at": r["updated_at"].isoformat()}


def _brief_body(b: dict) -> str:
    return json.dumps({k: v for k, v in b.items() if k not in ("id", "rev", "created_by", "created_at", "updated_at",
                                                                "sources")})


async def brief_create(b: dict, created_by: str = "") -> str:
    bid = str(uuid.uuid4())
    await pool().execute("INSERT INTO docengine.briefs (id, rev, body, created_by) VALUES ($1,$2,$3,$4)",
                         bid, b["rev"], _brief_body(b), created_by)
    await pool().execute("INSERT INTO docengine.brief_events (brief_id, rev, actor, op, after) VALUES ($1,0,$2,'create',$3)",
                         bid, created_by, json.dumps({"package": b["package"], "meta": b["meta"]}))
    return bid


async def brief_get(bid: str) -> dict | None:
    r = await pool().fetchrow("SELECT * FROM docengine.briefs WHERE id=$1", bid)
    if not r:
        return None
    b = _brief_row(r)
    b["sources"] = await brief_sources(bid, with_text=False)
    return b


async def brief_save(b: dict, old_rev: int, events: list[dict]) -> bool:
    """Write the brief and its events only if it is still at `old_rev`; False when another change won."""
    async with pool().acquire() as c, c.transaction():
        ok = await c.fetchval("UPDATE docengine.briefs SET rev=$2, body=$3, updated_at=now() WHERE id=$1 AND rev=$4"
                              " RETURNING id", b["id"], b["rev"], _brief_body(b), old_rev)
        if not ok:
            return False
        await c.executemany(
            "INSERT INTO docengine.brief_events (brief_id, rev, actor, op, key, before, after) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            [(b["id"], b["rev"], e.get("actor", ""), e["op"], e.get("key", ""), json.dumps(e.get("before")),
              json.dumps(e.get("after"))) for e in events])
    return True


async def brief_list(limit: int = 100) -> list[dict]:
    rows = await pool().fetch("SELECT * FROM docengine.briefs ORDER BY updated_at DESC LIMIT $1", limit)
    out = []
    for r in rows:
        b = _brief_row(r)
        out.append({k: b.get(k) for k in ("id", "rev", "status", "package", "meta", "updated_at", "job_ids")})
    return out


async def brief_events(bid: str) -> list[dict]:
    rows = await pool().fetch("SELECT rev, at, actor, op, key, before, after FROM docengine.brief_events"
                              " WHERE brief_id=$1 ORDER BY id", bid)
    return [{"rev": r["rev"], "at": r["at"].isoformat(), "actor": r["actor"], "op": r["op"], "key": r["key"],
             "before": json.loads(r["before"]) if r["before"] else None,
             "after": json.loads(r["after"]) if r["after"] else None} for r in rows]


MAX_SOURCES = 20


async def brief_source_add(bid: str, rev: int, actor: str, src: dict) -> str | None:
    """Add a source to an open brief; None when the brief is not open or already holds MAX_SOURCES."""
    sid = str(uuid.uuid4())
    async with pool().acquire() as c, c.transaction():
        # The brief row is locked first, so the count below is read after every earlier add committed: 40 uploads
        # sent at once each counted 0 and all 40 went in (review 19.10.2026).
        status = await c.fetchval("SELECT body->>'status' FROM docengine.briefs WHERE id=$1 FOR UPDATE", bid)
        if status != "open":
            return None
        if await c.fetchval("SELECT count(*) FROM docengine.brief_sources WHERE brief_id=$1", bid) >= MAX_SOURCES:
            return None
        new_rev = await c.fetchval("UPDATE docengine.briefs SET rev=rev+1, updated_at=now() WHERE id=$1 RETURNING rev", bid)
        await c.execute("INSERT INTO docengine.brief_sources (id, brief_id, name, kind, bytes, sha256, text, role)"
                        " VALUES ($1,$2,$3,$4,$5,$6,$7,$8)", sid, bid, src["name"], src["kind"], src["bytes"],
                        src["sha256"], src["text"], src.get("role") or "content")
        await c.execute("INSERT INTO docengine.brief_events (brief_id, rev, actor, op, key, after)"
                        " VALUES ($1,$2,$3,'source_add',$4,$5)", bid, new_rev, actor, src["name"],
                        json.dumps({"id": sid, "kind": src["kind"], "bytes": src["bytes"], "chars": len(src["text"]),
                                    "role": src.get("role") or "content"}))
    return sid


async def brief_source_role(bid: str, sid: str, role: str, actor: str) -> bool:
    """Change what a source is for; False when the brief is not open or the source is not its."""
    async with pool().acquire() as c, c.transaction():
        new_rev = await c.fetchval(
            "UPDATE docengine.briefs SET rev=rev+1, updated_at=now() WHERE id=$1 AND body->>'status' = 'open'"
            " AND EXISTS (SELECT 1 FROM docengine.brief_sources WHERE id=$2 AND brief_id=$1) RETURNING rev", bid, sid)
        if new_rev is None:
            return False
        before = await c.fetchrow("SELECT name, role FROM docengine.brief_sources WHERE id=$1", sid)
        await c.execute("UPDATE docengine.brief_sources SET role=$2 WHERE id=$1", sid, role)
        await c.execute("INSERT INTO docengine.brief_events (brief_id, rev, actor, op, key, before, after)"
                        " VALUES ($1,$2,$3,'source_role',$4,$5,$6)", bid, new_rev, actor, before["name"],
                        json.dumps(before["role"]), json.dumps(role))
    return True


async def brief_source_remove(bid: str, sid: str, actor: str) -> bool:
    async with pool().acquire() as c, c.transaction():
        name = await c.fetchval("DELETE FROM docengine.brief_sources s USING docengine.briefs b WHERE s.id=$1"
                                " AND s.brief_id=$2 AND b.id=s.brief_id AND b.body->>'status' = 'open' RETURNING s.name",
                                sid, bid)
        if not name:
            return False
        rev = await c.fetchval("UPDATE docengine.briefs SET rev=rev+1, updated_at=now() WHERE id=$1 RETURNING rev", bid)
        await c.execute("INSERT INTO docengine.brief_events (brief_id, rev, actor, op, key) VALUES ($1,$2,$3,'source_remove',$4)",
                        bid, rev, actor, name)
    return True


async def brief_sources(bid: str, with_text: bool = True) -> list[dict]:
    text = "text" if with_text else "'' AS text"
    rows = await pool().fetch(f"SELECT id, name, kind, bytes, sha256, {text}, length(text) AS chars, created_at, role"
                              " FROM docengine.brief_sources WHERE brief_id=$1 ORDER BY created_at", bid)
    return [{"id": str(r["id"]), "name": r["name"], "kind": r["kind"], "bytes": r["bytes"], "sha256": r["sha256"],
             "chars": r["chars"], "created_at": r["created_at"].isoformat(), "role": r["role"],
             **({"text": r["text"]} if with_text else {})} for r in rows]
