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
CREATE INDEX IF NOT EXISTS de_jobs_status ON docengine.jobs(status);
CREATE INDEX IF NOT EXISTS de_docs_code ON docengine.documents(code);
"""


async def init() -> None:
    global _pool
    if not settings.database_url:
        return  # tests / degraded mode: endpoints depending on DB 503
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    async with _pool.acquire() as c:
        await c.execute(_SCHEMA)


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
        "SELECT id, code, doctype, title_mk, title_en, version, bytes, created_at"
        " FROM docengine.documents ORDER BY created_at DESC LIMIT $1", limit,
    )
    out = []
    for r in rows:
        d = dict(r)
        d["id"] = str(d["id"])
        d["created_at"] = d["created_at"].isoformat()
        out.append(d)
    return out


async def document_get(did: str) -> dict | None:
    r = await pool().fetchrow("SELECT * FROM docengine.documents WHERE id = $1", did)
    if not r:
        return None
    d = dict(r)
    d["id"] = str(d["id"])
    d["job_id"] = str(d["job_id"]) if d["job_id"] else None
    d["created_at"] = d["created_at"].isoformat()
    return d
