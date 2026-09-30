# docengine_studio.app.db - studio-local state: registry overlay, lifecycle, approvals,
# audit hash chain, api clients, model routing and lane routing.
# Additive only: upstream DocEngine remains the system of record for generated artefacts.
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  upstream_id TEXT,
  title TEXT NOT NULL,
  doc_type TEXT,
  questionnaire_key TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  language TEXT DEFAULT 'MK',
  revision TEXT,
  owner TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS document_versions (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id),
  version INTEGER NOT NULL,
  job_id TEXT,
  sha256 TEXT,
  verdict TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  upstream_id TEXT,
  document_id TEXT,
  kind TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  payload TEXT,
  error TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  version INTEGER,
  role TEXT NOT NULL,
  actor TEXT NOT NULL,
  decision TEXT NOT NULL,
  comment TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS signatures (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  version INTEGER,
  actor TEXT NOT NULL,
  meaning TEXT NOT NULL,
  sha256 TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS provenance (
  id TEXT PRIMARY KEY,
  document_id TEXT,
  job_id TEXT,
  lane TEXT NOT NULL,
  source TEXT NOT NULL,
  citation TEXT,
  detail TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event TEXT NOT NULL,
  actor TEXT,
  subject TEXT,
  payload TEXT,
  prev_hash TEXT,
  hash TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS api_clients (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  client_id TEXT NOT NULL UNIQUE,
  secret_hash TEXT NOT NULL,
  scopes TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS model_routing (
  fn TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  temperature REAL NOT NULL DEFAULT 0.0,
  rationale TEXT
);
CREATE TABLE IF NOT EXISTS lane_router (
  intent TEXT PRIMARY KEY,
  lane TEXT NOT NULL,
  fail_closed INTEGER NOT NULL DEFAULT 1,
  rationale TEXT
);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE INDEX IF NOT EXISTS idx_audit_subject ON audit(subject);
CREATE INDEX IF NOT EXISTS idx_jobs_doc ON jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);
"""

GENESIS = "0" * 64

DEFAULT_MODEL_ROUTING = [
    ("sop_section_authoring", "moonshot", "alegretto", 0.2, "Producer role: descriptive authoring."),
    ("annex_generation", "moonshot", "alegretto", 0.2, "Producer role: annex text from source data."),
    ("bilingual_translation", "moonshot", "alegretto", 0.2, "Producer role: MK/EN rendering."),
    ("app_assistant", "moonshot", "alegretto", 0.3, "Conversational assistance; may propose."),
    ("voice_capture", "moonshot", "alegretto", 0.1, "Transcribe/structurise user dictation."),
    ("snapshot_summary", "moonshot", "alegretto", 0.3, "Advisory narrative summaries."),
    ("orchestration", "deepseek", "deepseek-chat", 0.0, "Machine routing between providers."),
    ("regulatory_check", "deepseek", "deepseek-chat", 0.0, "Checker role: deterministic verdicts."),
    ("qa_audit", "deepseek", "deepseek-reasoner", 0.0, "Checker role: producer/checker separation."),
    ("raci_assignment", "deepseek", "deepseek-chat", 0.0, "Checker role: rule mapping."),
    ("record_extraction", "deepseek", "deepseek-chat", 0.0, "Checker role: structured extraction."),
    ("verification", "deepseek", "deepseek-chat", 0.0, "Checker role: pass/fail gate."),
    ("intent_classification", "deepseek", "deepseek-chat", 0.0, "Verifier role: lane routing."),
]

DEFAULT_LANE_ROUTER = [
    ("official_evidence", "ragflow", 1, "Official certificate/spec retrieval; no silent fallback."),
    ("coa_lookup", "ragflow", 1, "Certificate retrieval by identity; refusal on miss."),
    ("qa_query", "letta", 0, "QA knowledge questions (advisory)."),
    ("assistant_chat", "letta", 0, "General assistant conversation (advisory)."),
    ("summarisation", "letta", 0, "Narrative summarisation (advisory)."),
]


def _connect() -> sqlite3.Connection:
    settings.ensure_dirs()
    conn = sqlite3.connect(str(settings.db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with tx() as conn:
        conn.executescript(SCHEMA)
        for row in DEFAULT_MODEL_ROUTING:
            conn.execute(
                "INSERT OR IGNORE INTO model_routing(fn,provider,model,temperature,rationale) VALUES (?,?,?,?,?)",
                row,
            )
        for row in DEFAULT_LANE_ROUTER:
            conn.execute(
                "INSERT OR IGNORE INTO lane_router(intent,lane,fail_closed,rationale) VALUES (?,?,?,?)",
                row,
            )
        cur = conn.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1")
        last = cur.fetchone()
        conn.execute("INSERT OR IGNORE INTO meta(k,v) VALUES ('audit_head', ?)", (last["hash"] if last else GENESIS,))


# --------------------------------------------------------------------------- id

def new_id(prefix: str) -> str:
    return "%s_%s" % (prefix, uuid.uuid4().hex[:16])


# -------------------------------------------------------------------------- audit

def _audit_hash(prev: str, event: str, actor: str | None, subject: str | None, payload: Any, ts: float) -> str:
    body = json.dumps({"e": event, "a": actor, "s": subject, "p": payload, "t": round(ts, 6)}, sort_keys=True, default=str)
    return hashlib.sha256((prev + "|" + body).encode("utf-8")).hexdigest()


def audit(event: str, actor: str | None = None, subject: str | None = None, payload: Any = None) -> dict:
    ts = time.time()
    with tx() as conn:
        cur = conn.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1")
        row = cur.fetchone()
        prev = row["hash"] if row else GENESIS
        h = _audit_hash(prev, event, actor, subject, payload, ts)
        conn.execute(
            "INSERT INTO audit(event,actor,subject,payload,prev_hash,hash,created_at) VALUES (?,?,?,?,?,?,?)",
            (event, actor, subject, json.dumps(payload, default=str) if payload is not None else None, prev, h, ts),
        )
        conn.execute("INSERT INTO meta(k,v) VALUES ('audit_head', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (h,))
        return {"seq": conn.execute("SELECT last_insert_rowid() AS s").fetchone()["s"], "hash": h, "prev_hash": prev}


def audit_verify() -> dict:
    with tx() as conn:
        rows = conn.execute("SELECT * FROM audit ORDER BY seq").fetchall()
    prev = GENESIS
    for r in rows:
        payload = json.loads(r["payload"]) if r["payload"] else None
        expect = _audit_hash(prev, r["event"], r["actor"], r["subject"], payload, r["created_at"])
        if expect != r["hash"] or r["prev_hash"] != prev:
            return {"ok": False, "broken_at": r["seq"], "expected": expect, "found": r["hash"]}
        prev = r["hash"]
    return {"ok": True, "events": len(rows), "head": prev}

