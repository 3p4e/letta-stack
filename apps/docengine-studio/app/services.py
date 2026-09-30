# docengine_studio.app.services - shared business logic for the REST gateway and
# the MCP surface. Keeping it here guarantees both transports enforce the same
# capability, lane and lifecycle rules (no second implementation to drift).
from __future__ import annotations

import json
import time
from typing import Any

import httpx

from . import db, router
from .clients import DocEngineClient, LettaClient, UpstreamError
from .config import settings


class LaneUnavailable(RuntimeError):
    """Raised when a lane cannot serve the request. Official lanes never fall back."""


# ------------------------------------------------------------------ pass-through

def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and payload.get("__status__"):
        raise UpstreamError("upstream returned %s: %s" % (payload["__status__"], payload.get("detail")))
    return payload


async def upstream_health() -> dict:
    return await DocEngineClient().health()


async def list_questionnaires() -> list[dict]:
    data = _unwrap(await DocEngineClient().list_questionnaires())
    return data.get("questionnaires", data if isinstance(data, list) else [])


async def get_questionnaire(key: str) -> dict:
    return _unwrap(await DocEngineClient().get_questionnaire(key))


async def start_workflow(body: dict, actor: str) -> dict:
    payload = {
        "questionnaire": body.get("questionnaire"),
        "answers": body.get("answers", {}),
        "meta": body.get("meta", {}),
        "requested_by": actor,
    }
    result = _unwrap(await DocEngineClient().start_workflow(payload))
    jid = result.get("job_id")
    doc_id = body.get("document_id")
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO jobs(id,upstream_id,document_id,kind,stage,status,payload,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (db.new_id("job"), jid, doc_id, "workflow", "queued", "running",
             json.dumps(payload, default=str), time.time(), time.time()),
        )
    db.audit("workflow.started", actor=actor, subject=jid, payload={"questionnaire": payload["questionnaire"], "document_id": doc_id})
    return result


async def get_workflow(jid: str) -> dict:
    upstream = _unwrap(await DocEngineClient().get_workflow(jid))
    with db.tx() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE upstream_id=?", (jid,)).fetchone()
        if row and upstream.get("status"):
            conn.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", (upstream["status"], time.time(), row["id"]))
    return upstream


async def build_document(body: dict, actor: str) -> dict:
    doc_id = body.pop("document_id", None)
    result = await DocEngineClient().build(body)
    if isinstance(result, dict) and result.get("__status__") == 422:
        # The gate: the engine refused a FAILed document. Preserve the report.
        db.audit("build.rejected", actor=actor, subject=doc_id, payload={"verify": result.get("detail")})
        return {"ok": False, "status": 422, "verify": result.get("detail")}
    _unwrap(result)
    upstream_doc = result.get("document_id")
    if doc_id:
        with db.tx() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
            if row:
                nxt = conn.execute("SELECT COALESCE(MAX(version),0)+1 AS v FROM document_versions WHERE document_id=?", (doc_id,)).fetchone()["v"]
                conn.execute(
                    "INSERT INTO document_versions(id,document_id,version,job_id,sha256,verdict,created_at) VALUES (?,?,?,?,?,?,?)",
                    (db.new_id("ver"), doc_id, nxt, upstream_doc, None, "PASS", time.time()),
                )
                conn.execute("UPDATE documents SET upstream_id=?,updated_at=? WHERE id=?", (upstream_doc, time.time(), doc_id))
    db.audit("document.built", actor=actor, subject=upstream_doc or doc_id, payload={"bytes": result.get("bytes"), "verdict": "PASS"})
    return result


async def list_certificates() -> list[dict]:
    data = _unwrap(await DocEngineClient().list_documents())
    return data.get("documents", data if isinstance(data, list) else [])


async def get_certificate(did: str) -> dict:
    return _unwrap(await DocEngineClient().get_document(did))


async def fetch_artifact(did: str, kind: str) -> tuple[int, str, bytes]:
    client = DocEngineClient()
    return await (client.pdf(did) if kind == "pdf" else client.download(did))


# -------------------------------------------------------------------- registry

def list_registry(status: str | None = None, limit: int = 200) -> list[dict]:
    with db.tx() as conn:
        if status:
            rows = conn.execute("SELECT * FROM documents WHERE status=? ORDER BY updated_at DESC LIMIT ?", (status, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_registry_entry(doc_id: str) -> dict | None:
    with db.tx() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    return dict(row) if row else None


STATUS_FLOW = {"draft": {"in_review"}, "in_review": {"draft", "approved"}, "approved": {"effective", "superseded"}, "effective": {"superseded"}, "superseded": set()}


def create_registry_entry(body: dict, actor: str) -> dict:
    title = (body.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    doc_id = db.new_id("doc")
    now = time.time()
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO documents(id,title,doc_type,questionnaire_key,status,language,revision,owner,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (doc_id, title, body.get("doc_type"), body.get("questionnaire_key"),
             body.get("status", "draft"), body.get("language", "MK"), body.get("revision"), actor, now, now),
        )
    db.audit("document.created", actor=actor, subject=doc_id, payload={"title": title, "doc_type": body.get("doc_type")})
    return get_registry_entry(doc_id)


def update_registry_status(doc_id: str, new_status: str, actor: str, comment: str | None = None) -> dict:
    entry = get_registry_entry(doc_id)
    if not entry:
        raise KeyError(doc_id)
    cur = entry["status"]
    if new_status == cur:
        return entry
    allowed = STATUS_FLOW.get(cur, set())
    if new_status not in allowed:
        raise ValueError("illegal transition %s -> %s" % (cur, new_status))
    with db.tx() as conn:
        conn.execute("UPDATE documents SET status=?,updated_at=? WHERE id=?", (new_status, time.time(), doc_id))
    db.audit("document.status_changed", actor=actor, subject=doc_id, payload={"from": cur, "to": new_status, "comment": comment})
    return get_registry_entry(doc_id)


def add_approval(doc_id: str, decision: str, actor: str, role: str, comment: str | None, version: int | None) -> dict:
    if decision not in ("approved", "rejected", "changes_requested"):
        raise ValueError("invalid decision")
    entry = get_registry_entry(doc_id)
    if not entry:
        raise KeyError(doc_id)
    aid = db.new_id("apr")
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO approvals(id,document_id,version,role,actor,decision,comment,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (aid, doc_id, version, role, actor, decision, comment, time.time()),
        )
    db.audit("document.approval", actor=actor, subject=doc_id, payload={"decision": decision, "role": role, "comment": comment})
    return {"id": aid, "document_id": doc_id, "decision": decision}


def add_signature(doc_id: str, meaning: str, actor: str, sha256: str | None, version: int | None) -> dict:
    if not meaning.strip():
        raise ValueError("signature meaning is required")
    sid = db.new_id("sig")
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO signatures(id,document_id,version,actor,meaning,sha256,created_at) VALUES (?,?,?,?,?,?,?)",
            (sid, doc_id, version, actor, meaning, sha256, time.time()),
        )
    db.audit("document.signed", actor=actor, subject=doc_id, payload={"meaning": meaning})
    return {"id": sid, "document_id": doc_id, "meaning": meaning}


def list_approvals(doc_id: str) -> list[dict]:
    with db.tx() as conn:
        rows = conn.execute("SELECT * FROM approvals WHERE document_id=? ORDER BY created_at DESC", (doc_id,)).fetchall()
        sigs = conn.execute("SELECT * FROM signatures WHERE document_id=? ORDER BY created_at DESC", (doc_id,)).fetchall()
    return {"approvals": [dict(r) for r in rows], "signatures": [dict(r) for r in sigs]}


# ------------------------------------------------------------------- audit read

def audit_tail(limit: int = 100) -> list[dict]:
    with db.tx() as conn:
        rows = conn.execute("SELECT * FROM audit ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ lane routing

def _ragflow_retrieve(question: str, dataset_ids: list[str] | None) -> list[dict]:
    if not settings.ragflow_endpoint:
        raise LaneUnavailable("official lane (RAGFlow) is not configured")
    if not settings.ragflow_key:
        raise LaneUnavailable("official lane (RAGFlow) has no API key configured")
    body = {"question": question, "page_size": 8, "similarity_threshold": 0.2}
    if dataset_ids:
        body["dataset_ids"] = dataset_ids
    try:
        with httpx.Client(timeout=60.0) as c:
            r = c.post(
                settings.ragflow_endpoint + "/api/v1/retrieval",
                headers={"Authorization": "Bearer " + settings.ragflow_key},
                json=body,
            )
    except Exception as e:  # noqa: BLE001
        raise LaneUnavailable("official lane unreachable: %s" % str(e)[:160]) from e
    if r.status_code >= 400:
        raise LaneUnavailable("official lane error %s: %s" % (r.status_code, r.text[:160]))
    data = r.json()
    chunks = (data.get("data") or {}).get("chunks") if isinstance(data, dict) else None
    return chunks or []


async def ask(question: str, intent: str, actor: str, agent: str | None = None) -> dict:
    """Lane-routed question answering. Official intents fail closed by construction."""
    route = router.resolve_lane(intent)
    lane = route["lane"]
    started = time.time()
    citations: list[dict] = []
    if lane == "ragflow":
        try:
            chunks = _ragflow_retrieve(question, None)
        except LaneUnavailable as e:
            # Fail closed: official intents never fall back to the advisory lane,
            # and every refusal is recorded for audit.
            db.audit("lane.refused", actor=actor, subject=intent, payload={"lane": lane, "reason": str(e)})
            raise
        if not chunks:
            db.audit("lane.refused", actor=actor, subject=intent, payload={"lane": lane, "reason": "no verified evidence"})
            raise LaneUnavailable("no verified evidence found in the official lane; refusing to answer")
        answer = "\n\n".join(c.get("content", "") for c in chunks[:4]).strip()
        citations = [{"source": c.get("document_keyword") or c.get("docnm_kwd"), "dataset": c.get("dataset_id"), "similarity": c.get("similarity")} for c in chunks[:8]]
        lane_label = "official"
    else:
        client = LettaClient()
        if not client.configured:
            raise LaneUnavailable("advisory lane (Letta) is not configured")
        answer = await client.send_message(question, agent)
        lane_label = "advisory"
    elapsed = round(time.time() - started, 3)
    with db.tx() as conn:
        for c in citations or [{}]:
            conn.execute(
                "INSERT INTO provenance(id,document_id,job_id,lane,source,citation,detail,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (db.new_id("prv"), None, None, lane, c.get("source") or "n/a", json.dumps(c, default=str), question[:400], time.time()),
            )
    db.audit("assistant.ask", actor=actor, subject=intent, payload={"lane": lane, "citation_count": len(citations), "elapsed": elapsed})
    return {"answer": answer, "lane": lane, "lane_label": lane_label, "intent": intent,
            "citations": citations, "fail_closed": route["fail_closed"], "elapsed": elapsed,
            "advisory": lane == "letta"}
