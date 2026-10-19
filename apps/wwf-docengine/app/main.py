# docengine.app.main — GrowFlow DocEngine: dedicated FastAPI service.
#
# Internal-only container (no published ports); the WWF backend's /qms proxy
# is the sole caller (X-API-Key). Endpoints:
#   GET  /health                          liveness (+ letta/db readiness)
#   GET  /questionnaires                  index of Mode-A question banks
#   GET  /questionnaires/{key}            full question bank
#   POST /workflows                       start questionnaire->SOP pipeline
#   GET  /workflows/{id}                  poll job state (any worker)
#   POST /build                           direct Markdown -> verified .docx
#   GET  /documents                       registry list
#   GET  /documents/{id}                  registry row (verify report incl.)
#   GET  /documents/{id}/download         the .docx (only ever PASS docs)
#   GET  /documents/{id}/pdf              Gotenberg-rendered PDF
#   GET  /engine/environment              engine sync, renderer fonts, last verify results, fleet drift
#   GET  /register                        controlled documents (register/*.yaml, from QALI 001)
#   GET  /register/next                   next free code of a family, or next annex of a parent
#   PUT  /reference                       store an approved or work-in-progress document's text (approved: indexed in DB3)
#   GET  /reference, /reference/{id}      those documents (list; one with its text)
#   GET  /library                         every code on its shelf: approved, revision, drafts, numbers, retired
#   POST /briefs, GET /briefs[/{id}]      the Document Brief the single workflow edits (also from a reference document)
#   PATCH /briefs/{id}                    change it: fields (chosen / suggested / locked), meta, package, annexes; rev-checked
#   GET  /briefs/{id}/events              its full change history
#   POST /briefs/{id}/sources, DELETE …   upload a .docx/.pdf/.json/.md source (text kept), or remove one
#   POST /briefs/{id}/suggest             the advisor's options (why + source) for open questions; its pick as suggested
#   GET  /briefs/{id}/package             the latest build and its annexes: status, review, assumed, files
#   GET  /briefs/{id}/package.pdf         SOP + annexes as one PDF (409 until every member is built)
#   POST /briefs/{id}/build               build from wherever the brief stands; undecided fields listed as assumed
import asyncio
import contextlib
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import builder, db, engine_env, fleet, glossary, house_codes, library
from .config import settings
from .letta import LettaClient, LettaError
from .pipeline import run_workflow
from .questionnaires import QUESTIONNAIRES, questionnaire_index
from .ragflow import ECOA_NOTE, EXAMPLES_NOTE, RagflowClient, RagflowError, corpus_datasets
from .security import require_api_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("docengine")


# How often a running worker sweeps for jobs a killed worker left behind. The sweep used to run at startup
# only: with two workers it must spare jobs younger than STALE_JOB_MINUTES (the other worker may be running
# them), so a job killed by a redeploy minutes after its last update was never swept and sat at 'running'
# forever (review 14.10.2026). Each worker sweeps on this interval; the UPDATE is idempotent.
REAP_INTERVAL_S = 600


async def _reap_forever() -> None:
    while True:
        await asyncio.sleep(REAP_INTERVAL_S)
        try:
            reaped = await db.reap_stale_jobs()
            if reaped:
                log.warning("reaped %d stale job(s) with no progress for %d minutes", reaped, db.STALE_JOB_MINUTES)
        except Exception:  # noqa: BLE001 — a failed sweep is retried on the next interval
            log.warning("stale-job sweep failed", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    # Sweep jobs abandoned by a previously-killed worker. Startup is exactly
    # when those rows appear (a redeploy kills the worker mid-run), and without
    # this they sit at 'running' forever with a poller waiting on them.
    try:
        reaped = await db.reap_stale_jobs()
        if reaped:
            log.warning("reaped %d stale job(s) left mid-flight by a killed worker", reaped)
    except Exception:
        # Never block startup on the sweep — the service must come up.
        log.warning("stale-job sweep failed at startup", exc_info=True)
    reaper = asyncio.create_task(_reap_forever()) if db.ready() else None
    yield
    if reaper:
        reaper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reaper
    await db.close()


app = FastAPI(title="GrowFlow DocEngine", version="1.0.0", lifespan=lifespan)

# asyncio.create_task() only holds a WEAK reference to the task it returns —
# without also keeping a strong reference somewhere, the task can be silently
# garbage-collected mid-run before it completes (a documented asyncio footgun,
# not hypothetical: see "Important" note under
# https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task).
# A job that vanished mid-generation would sit "running" forever with no
# error recorded — worse than any exception run_workflow itself might raise.
_background_tasks: set[asyncio.Task] = set()


def _fire_and_forget(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def _valid_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


# ---------- health (unauthenticated: compose healthcheck) ----------
@app.get("/health")
async def health():
    return {
        "ok": True,
        "db": db.ready(),
        "letta": LettaClient().configured,
        # configured only: the compose healthcheck must not depend on another stack
        "ragflow": RagflowClient().configured,
        "engine": f"pp-document-suite (synced copy, canon revision {engine_env.CANON})",
    }


# ---------- knowledge (RAGFlow) ----------
class KnowledgeIn(BaseModel):
    corpus: str = "regulatory"          # regulatory | ecoa | examples
    question: str = Field(min_length=2, max_length=2000)
    top_n: int = Field(default=6, ge=1, le=30)
    keyword: bool = False               # full-text: clause numbers, batch codes


@app.post("/knowledge/search", dependencies=[Depends(require_api_key)])
async def knowledge_search(body: KnowledgeIn):
    """Search a RAGFlow knowledge base the way the pipeline does, so a user or agent can
    check a requirement or find a certificate while writing."""
    ids = corpus_datasets(body.corpus)
    if body.corpus not in ("regulatory", "ecoa", "examples"):
        raise HTTPException(404, "unknown corpus")
    if not ids:
        raise HTTPException(409, f"no RAGFlow dataset configured for '{body.corpus}'")
    try:
        passages = await RagflowClient().retrieve(body.question, ids, top_n=body.top_n, keyword=body.keyword)
    except RagflowError as e:
        raise HTTPException(503, str(e))
    note = {"ecoa": ECOA_NOTE, "examples": EXAMPLES_NOTE}.get(body.corpus, "")
    return {"corpus": body.corpus, "passages": passages, "note": note}


@app.get("/knowledge/health", dependencies=[Depends(require_api_key)])
async def knowledge_health():
    rag = RagflowClient()
    return {"configured": rag.configured, "reachable": await rag.reachable(),
            "datasets": {c: list(corpus_datasets(c)) for c in ("regulatory", "ecoa", "examples")}}


# ---------- questionnaires ----------
@app.get("/questionnaires", dependencies=[Depends(require_api_key)])
async def list_questionnaires():
    return {"questionnaires": questionnaire_index()}


@app.get("/questionnaires/{key}", dependencies=[Depends(require_api_key)])
async def get_questionnaire(key: str):
    q = QUESTIONNAIRES.get(key)
    if not q:
        raise HTTPException(404, "unknown questionnaire")
    return q


# ---------- workflows ----------
class WorkflowIn(BaseModel):
    questionnaire: str
    answers: dict = Field(default_factory=dict)
    meta: dict  # {title_mk, title_en, code, version?, orient?}
    requested_by: str = ""
    # The requester's own brief and the sources they name, alongside the questionnaire answers.
    # Free text by design: the questionnaire's options are pre-verified, these are the requester's
    # responsibility, and the §6A audit still checks every reference against them and the findings.
    instructions: str = Field("", max_length=12000)
    sources: list[str] = Field(default_factory=list, max_length=40)
    # For an annex job: the code of the SOP it serves. The pipeline reads that SOP's sections 6 and 7 so the
    # form holds a field for every item the SOP writes into it (13.10.2026 review: four DEMO annexes were
    # generic shipment forms because the generator never saw WHSOP_003).
    parent_sop: str = Field("", max_length=80)


_META_FIELDS = ("title_mk", "title_en", "code", "version", "doctype", "orient")


def _check_meta(meta: dict, required: tuple = ()) -> None:
    """Reject at the door what the HEADERDATA block cannot hold. These values used to be checked only when the
    document was assembled, after every section had been generated: a non-string code crashed the build and a
    line break wrote a HEADERDATA field of its own ("bilingual: no" switched the bilingual gate off)."""
    for k in required:
        if not meta.get(k):
            raise HTTPException(400, f"meta.{k} required")
    for k in _META_FIELDS:
        v = meta.get(k)
        if v is None:
            continue
        if not isinstance(v, str):
            raise HTTPException(400, f"meta.{k} must be text")
        if len(v) > 300 or "\n" in v or "\r" in v or "-->" in v:
            raise HTTPException(400, f"meta.{k} must be one line of at most 300 characters without '-->'")


@app.post("/workflows", dependencies=[Depends(require_api_key)])
async def start_workflow(body: WorkflowIn):
    if body.questionnaire not in QUESTIONNAIRES:
        raise HTTPException(400, "unknown questionnaire")
    _check_meta(body.meta, ("title_mk", "title_en", "code"))
    body.meta["code"] = _house_code(body.meta["code"])
    if body.parent_sop.strip():
        body.parent_sop = _house_code(body.parent_sop, "parent_sop")
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    if not LettaClient().configured:
        raise HTTPException(503, "Letta unavailable")
    jid = await db.job_create("workflow", body.model_dump(), body.requested_by)
    _fire_and_forget(run_workflow(jid))
    return {"job_id": jid, "status": "queued"}


@app.get("/workflows/{jid}", dependencies=[Depends(require_api_key)])
async def get_workflow(jid: str):
    if not _valid_uuid(jid):
        raise HTTPException(404, "no such job")
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    job = await db.job_get(jid)
    if not job:
        raise HTTPException(404, "no such job")
    return job


class ReviewIn(BaseModel):
    decision: str            # approve | return
    note: str = ""
    reviewer: str = ""


@app.post("/workflows/{jid}/review", dependencies=[Depends(require_api_key)])
async def review_workflow(jid: str, body: ReviewIn):
    """A person's decision on a job parked as awaiting_review (a §6A FIX that survived the repair rounds).

    approve → the built, verified .docx is registered in docengine.documents and the job is done;
    return  → the job fails as 'returned for revision: <note>' (a note is required).
    Either way the decision, the note, who and when are kept in result.review."""
    if body.decision not in ("approve", "return"):
        raise HTTPException(422, "decision must be 'approve' or 'return'")
    if body.decision == "return" and not body.note.strip():
        raise HTTPException(422, "a note is required to return a document for revision")
    if not _valid_uuid(jid):
        raise HTTPException(404, "no such job")
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    job = await db.job_get(jid)
    if not job:
        raise HTTPException(404, "no such job")
    res = job.get("result") or {}
    art = res.get("artifact") or {}
    if job["status"] == "awaiting_review" and body.decision == "approve" and not (art.get("path") and Path(art["path"]).is_file()):
        raise HTTPException(410, "the built document is missing; return it for revision and re-run")
    from datetime import datetime, timezone
    review = {"decision": body.decision, "note": body.note.strip(), "by": body.reviewer or job.get("created_by") or "reviewer",
              "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "qa_verdict": res.get("qa_verdict", "")}
    # Atomic claim: of two simultaneous decisions only one moves the row out of awaiting_review.
    if not await db.job_claim(jid, "awaiting_review", "running" if body.decision == "approve" else "failed"):
        raise HTTPException(409, "job is not awaiting review")
    if body.decision == "return":
        await db.job_update(jid, status="failed", stage="format", error=f"returned for revision: {review['note']}"[:500])
        await db.job_merge_result(jid, {"review": review})
    else:
        meta = job["payload"]["meta"]
        try:
            did = await db.document_create(jid, {
                "code": meta["code"], "doctype": meta.get("doctype") or QUESTIONNAIRES[job["payload"]["questionnaire"]]["doctype"],
                "title_mk": meta["title_mk"], "title_en": meta["title_en"], "version": meta.get("version", "1.0"),
                "path": art["path"], "bytes": art.get("bytes") or res.get("bytes") or 0, "verify": res.get("verify", ""),
            })
        except Exception:
            # The claim moved the job to 'running'. Left there, the approval is lost and the job reads as
            # in progress until the reaper fails it an hour later; put it back so the reviewer can retry.
            await db.job_update(jid, status="awaiting_review")
            raise
        # Merged, not rewritten: the SOP's package annexes may record themselves on this row meanwhile.
        await db.job_merge_result(jid, {"document_id": did, "review": review})
        await db.job_update(jid, status="done", stage="done")
    return await db.job_get(jid)


# ---------- direct build (Mode B/C: caller supplies the Markdown) ----------
class BuildIn(BaseModel):
    markdown: str = Field(min_length=20, max_length=400_000)
    # Bounded: this becomes part of a filename via builder.safe_name(). That
    # helper truncates to 120 chars, but only AFTER the value has been accepted
    # — and every other field on this model already carries a bound, so the
    # omission was the odd one out rather than a decision.
    out_name: str = Field(default="document", min_length=1, max_length=80)
    meta: dict = Field(default_factory=dict)


def _house_code(raw: str, field: str = "code") -> str:
    """A document code in the house form of QALI 001 (Head of QC, 18.10.2026): QCSOP011, QCT017, QCSOP011A01.
    The forms in circulation are normalised ("QCSOP 011", "WHSOP_003_A01"); a file name or an unassigned
    placeholder ("QASOP_0XX") is refused. The Formatter once registered upload file names as codes and the Library
    showed them as effective versions (review 14.10.2026). Same rule as web/src/lib/registry.ts."""
    code = house_codes.normalize(raw)
    if not code:
        raise HTTPException(400, f"{field} must be a document code in the house form, e.g. QCSOP011, QCT017 or "
                                 f"QCSOP011A01 (got {str(raw)[:40]!r}); GET /register/next gives the next free one")
    return code


@app.post("/build", dependencies=[Depends(require_api_key)])
async def direct_build(body: BuildIn):
    _check_meta(body.meta)
    code = _house_code((body.meta.get("code") or body.out_name).strip(), "meta.code")
    try:
        result = await asyncio.to_thread(
            builder.build, body.markdown, settings.out_dir, body.out_name
        )
    except builder.VerifyFailed as e:
        # the gate: FAILed docs are deleted and never returned
        raise HTTPException(422, detail={"verify": e.report, "error": "verify FAILED"})
    doc_id = None
    if db.ready():
        doc_id = await db.document_create(
            None,
            {
                "code": code,
                "doctype": result.doctype,
                "title_mk": body.meta.get("title_mk", ""),
                "title_en": body.meta.get("title_en", ""),
                "version": body.meta.get("version", "1.0"),
                "path": str(result.path), "bytes": result.bytes,
                "verify": result.verify_report,
            },
        )
    return {
        "ok": True, "document_id": doc_id, "bytes": result.bytes,
        "verify": result.verify_report,
    }


# ---------- documents ----------
@app.get("/documents", dependencies=[Depends(require_api_key)])
async def list_documents():
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    return {"documents": await db.documents_list()}


async def _doc_or_404(did: str) -> dict:
    if not _valid_uuid(did):
        raise HTTPException(404, "no such document")
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    d = await db.document_get(did)
    if not d:
        raise HTTPException(404, "no such document")
    if not Path(d["path"]).exists():
        raise HTTPException(410, "document artifact missing")
    return d


@app.get("/documents/{did}", dependencies=[Depends(require_api_key)])
async def get_document(did: str):
    if not _valid_uuid(did):
        raise HTTPException(404, "no such document")
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    d = await db.document_get(did)
    if not d:
        raise HTTPException(404, "no such document")
    return d


@app.get("/documents/{did}/download", dependencies=[Depends(require_api_key)])
async def download_document(did: str):
    d = await _doc_or_404(did)
    return FileResponse(
        d["path"],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(d["path"]).name,
    )


@app.get("/documents/{did}/pdf", dependencies=[Depends(require_api_key)])
async def document_pdf(did: str):
    d = await _doc_or_404(did)
    if not settings.gotenberg_url:
        raise HTTPException(503, "PDF renderer unavailable")
    pdf = await _render_pdf(d["path"], did)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition":
                 f'attachment; filename="{Path(d["path"]).stem}.pdf"'},
    )


async def _render_pdf(path: str, label: str) -> bytes:
    """A .docx as PDF through the house renderer, refused if it printed substitute fonts (Head of QC, 10.10.2026)."""
    # Read off the event loop. Passing the open file handle to httpx made it
    # do blocking disk reads while streaming the upload, stalling every other
    # request this worker was serving for the duration of a multi-megabyte
    # .docx — the same defect H14 fixed for builder.build, on a path that is
    # hit far more often.
    try:
        blob = await asyncio.to_thread(Path(path).read_bytes)
    except OSError as e:
        log.warning("PDF conversion: cannot read %s: %s", label, e)
        raise HTTPException(404, "Document file missing") from e
    try:
        auth = (settings.gotenberg_user, settings.gotenberg_password) if settings.gotenberg_user else None
        async with httpx.AsyncClient(timeout=120, auth=auth) as c:
            r = await c.post(
                settings.gotenberg_url + "/forms/libreoffice/convert",
                # refresh the TOC and other indexes before export (same as pp_render)
                data={"updateIndexes": "true"},
                files={"files": (Path(path).name, blob,
                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
    except httpx.HTTPError as e:
        log.warning("Gotenberg PDF conversion failed for %s: %s", label, e)
        raise HTTPException(502, "PDF conversion failed") from e
    if r.status_code != 200:
        raise HTTPException(502, "PDF conversion failed")
    import pp_assets  # vendored engine (on sys.path via builder)
    subs = await asyncio.to_thread(pp_assets.font_substitutions, path, r.content)
    if subs:
        log.warning("PDF for %s refused: %s", label, "; ".join(subs))
        raise HTTPException(502, "the renderer printed substitute fonts: " + "; ".join(subs)[:400])
    return r.content


# ---------- engine environment (Fleet & health → Engine environment) ----------
async def _gotenberg(blob: bytes, name: str = "probe.docx") -> bytes:
    if not settings.gotenberg_url:
        raise RuntimeError("PDF renderer not configured (GOTENBERG_URL unset)")
    auth = (settings.gotenberg_user, settings.gotenberg_password) if settings.gotenberg_user else None
    async with httpx.AsyncClient(timeout=60, auth=auth) as c:
        r = await c.post(settings.gotenberg_url + "/forms/libreoffice/convert",
                         files={"files": (name, blob,
                                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    if r.status_code != 200:
        raise RuntimeError(f"renderer answered {r.status_code}")
    return r.content


@app.get("/engine/environment", dependencies=[Depends(require_api_key)])
async def engine_environment():
    """Measured state of the engine this container runs: nothing here is sample data. A part that
    cannot be measured says so in its own row instead of failing the whole report."""
    h = await asyncio.to_thread(engine_env.engine_hash)
    expected = engine_env.manifest_hash()
    fonts = await engine_env.font_rows(_gotenberg)
    try:
        audit = engine_env.audit_rows(await db.documents_verify_recent(6))
    except Exception as e:  # noqa: BLE001
        audit = [{"run": "registry", "ok": False, "note": f"cannot read the document registry: {e}"[:200]}]
    try:
        drift = engine_env.drift_rows(fleet.load_fleet(), glossary.memory_text(), await LettaClient().list_agents())
    except Exception as e:  # noqa: BLE001
        drift = [{"key": "Letta", "manifest": "fleet.yaml", "live": f"unreachable: {e}"[:120]}]
    return {"canon": engine_env.CANON, "version": f"synced copy · {h}", "synced": h == expected,
            "hash": h, "hashExpected": expected, "fonts": fonts, "glyphAudit": audit, "manifestDrift": drift}


# ---------- register (codes in use, next free code) ----------
@app.get("/register", dependencies=[Depends(require_api_key)])
async def register(status: str = "", family: str = ""):
    rows = house_codes.load_register()
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if family:
        rows = [r for r in rows if house_codes.parts(r["code"])[0].upper() == family.upper()]
    return {"documents": rows}


@app.get("/register/next", dependencies=[Depends(require_api_key)])
async def register_next(family: str = "", parent: str = ""):
    """The code a new document takes: one above the highest the register, the registry or an open job holds."""
    if not family and not parent:
        raise HTTPException(400, "give family (e.g. QCSOP) or parent (e.g. QCSOP011)")
    taken = await db.codes_in_use() if db.ready() else set()
    try:
        return {"code": house_codes.next_code(family=family, parent=parent, taken=taken), "engine_codes_checked": db.ready()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# ---------- reference documents and the Library (Head of QC, 18.10.2026) ----------
class ReferenceIn(BaseModel):
    kind: str = Field(pattern="^(approved|wip)$")
    code: str
    parent: str = ""
    version: str = Field("", max_length=20)
    title_mk: str = Field("", max_length=400)
    title_en: str = Field("", max_length=400)
    effective_date: str = Field("", max_length=20)
    department: str = Field("", max_length=20)
    package: str = ""
    source: dict = {}
    markdown: str = Field(min_length=20, max_length=2_000_000)
    index: bool = True


@app.put("/reference", dependencies=[Depends(require_api_key)])
async def put_reference(body: ReferenceIn):
    """One approved or work-in-progress document the engine did not write. An approved document's text is indexed in
    the examples dataset (DB3_PP_CURRENT), one entry per code + version; a re-sent identical text changes nothing."""
    import hashlib

    from .ragflow import RagflowClient, RagflowError
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    doc = body.model_dump()
    doc["code"] = _house_code(body.code)
    doc["parent"] = _house_code(body.parent, "parent") if body.parent else ""
    doc["package"] = _house_code(body.package, "package") if body.package else ""
    sha = hashlib.sha256(body.markdown.encode("utf-8")).hexdigest()
    rid, changed = await db.reference_upsert(doc, sha)
    row = await db.reference_get(rid)
    indexed, index_error = row["ragflow_doc_id"], ""
    if body.kind == "approved" and body.index and settings.ragflow_example_datasets and (changed or not indexed):
        title = f"{doc['code']} v{doc['version'] or '—'} — {doc['title_en'] or doc['title_mk']}"
        text = f"# {title}\n\n{body.markdown}"
        try:
            indexed = await RagflowClient().index_text(settings.ragflow_example_datasets[0],
                                                       f"{doc['code']}_v{doc['version'] or 'x'}.md", text,
                                                       replace_id=row["ragflow_doc_id"])
            await db.reference_set_ragflow(rid, indexed)
        except RagflowError as e:
            index_error = str(e)[:300]
    return {"id": rid, "code": doc["code"], "changed": changed, "ragflow_doc_id": indexed, "index_error": index_error}


@app.get("/reference", dependencies=[Depends(require_api_key)])
async def list_reference(kind: str = ""):
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    return {"documents": await db.reference_list(kind)}


@app.get("/reference/{rid}", dependencies=[Depends(require_api_key)])
async def get_reference(rid: str):
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    row = await db.reference_get(rid) if _valid_uuid(rid) else None
    if not row:
        raise HTTPException(404, "no such reference document")
    return row


@app.get("/library", dependencies=[Depends(require_api_key)])
async def get_library():
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")
    return library.shelve(house_codes.load_register(), await db.reference_list(), await db.documents_list(500),
                          await db.jobs_open_by_code())


# ---------- the Document Brief: one workflow (Head of QC, 18.10.2026) ----------
from . import brief as briefs  # noqa: E402
from . import sources as srcs  # noqa: E402
from . import advisor  # noqa: E402
from .question_rules import guide as _guide  # noqa: E402


def _option_value(o) -> str:
    return str(o["v"]) if isinstance(o, dict) else str(o)


def _questions(qname: str) -> dict[str, dict]:
    """{key: {label, multi, options}} of a question bank, options as their plain values."""
    return {q["key"]: {"label": (q.get("label") or {}).get("en", q["key"]), "multi": bool(q.get("multi")),
                       "options": [_option_value(o) for o in q.get("options") or []]}
            for r in QUESTIONNAIRES[qname]["rounds"] for q in r["questions"]}


def _guided(b: dict) -> dict:
    """The brief as the workflow shows it: with what the answers so far recommend for each question."""
    b.setdefault("proposals", {})
    b["guide"] = _guide(b, {k: q["options"] for k, q in _questions(b["questionnaire"]).items()})
    return b


class BriefIn(BaseModel):
    package: str
    meta: dict = Field(default_factory=dict)
    questionnaire: str = ""
    parent_sop: str = ""
    from_reference: str = ""          # an approved or work-in-progress document to start from (Revise / Continue)
    requested_by: str = ""


class BriefPatch(BaseModel):
    rev: int
    actor: str = ""
    set: dict = Field(default_factory=dict)
    suggest: dict = Field(default_factory=dict)
    lock: list[str] = Field(default_factory=list)
    unlock: list[str] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    package: str | None = None
    questionnaire: str | None = None
    parent_sop: str | None = None
    annexes: list[dict] | None = None
    status: str | None = None


class SourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    content_b64: str = Field(min_length=1, max_length=21_000_000)
    actor: str = ""


class SuggestIn(BaseModel):
    rev: int
    keys: list[str] = Field(default_factory=list, max_length=20)   # empty: every question not yet decided
    actor: str = ""


class BuildBriefIn(BaseModel):
    rev: int | None = None
    actor: str = ""


def _need_db() -> None:
    if not db.ready():
        raise HTTPException(503, "DocEngine storage unavailable")


async def _brief_or_404(bid: str) -> dict:
    _need_db()
    b = await db.brief_get(bid) if _valid_uuid(bid) else None
    if not b:
        raise HTTPException(404, "no such brief")
    return b


def _brief_meta(meta: dict) -> dict:
    _check_meta(meta)
    if meta.get("code"):
        meta = {**meta, "code": _house_code(meta["code"])}
    return meta


@app.post("/briefs", dependencies=[Depends(require_api_key)])
async def create_brief(body: BriefIn):
    _need_db()
    meta, seed = dict(body.meta), None
    if body.from_reference:
        seed = await db.reference_get(body.from_reference) if _valid_uuid(body.from_reference) else None
        if not seed:
            raise HTTPException(404, "no such reference document")
        for k in ("title_mk", "title_en", "code", "version"):
            meta.setdefault(k, seed.get(k) or "")
    try:
        b = briefs.new_brief(body.package, _brief_meta(meta), body.questionnaire,
                             _house_code(body.parent_sop, "parent_sop") if body.parent_sop else (seed or {}).get("parent", ""))
    except briefs.BriefError as e:
        raise HTTPException(e.status, str(e)) from e
    bid = await db.brief_create(b, body.requested_by)
    if seed:
        text = seed["markdown"]
        label = "approved text" if seed["kind"] == "approved" else "work in progress"
        await db.brief_source_add(bid, 0, body.requested_by, {
            "name": f"{seed['code']} v{seed['version'] or '—'} ({label})", "kind": "md", "bytes": len(text.encode()),
            "sha256": seed["sha256"], "text": text})
    return _guided(await db.brief_get(bid))


@app.get("/briefs", dependencies=[Depends(require_api_key)])
async def list_briefs():
    _need_db()
    return {"briefs": await db.brief_list()}


@app.get("/briefs/{bid}", dependencies=[Depends(require_api_key)])
async def get_brief(bid: str):
    return _guided(await _brief_or_404(bid))


@app.patch("/briefs/{bid}", dependencies=[Depends(require_api_key)])
async def patch_brief(bid: str, body: BriefPatch):
    b = await _brief_or_404(bid)
    patch = body.model_dump(exclude_none=True)
    if body.meta:
        patch["meta"] = _brief_meta({**b["meta"], **body.meta})
        patch["meta"] = {k: v for k, v in patch["meta"].items() if k in body.meta}
    if body.parent_sop:
        patch["parent_sop"] = _house_code(body.parent_sop, "parent_sop")
    try:
        new, events = briefs.apply_patch(b, patch, body.actor)
    except briefs.BriefError as e:
        raise HTTPException(e.status, str(e)) from e
    if events and not await db.brief_save(new, b["rev"], events):
        raise HTTPException(409, "the brief changed meanwhile; reload it")
    return _guided(await db.brief_get(bid))


@app.get("/briefs/{bid}/events", dependencies=[Depends(require_api_key)])
async def brief_history(bid: str):
    await _brief_or_404(bid)
    return {"events": await db.brief_events(bid)}


@app.post("/briefs/{bid}/sources", dependencies=[Depends(require_api_key)])
async def add_brief_source(bid: str, body: SourceIn):
    import base64
    import binascii
    import hashlib
    b = await _brief_or_404(bid)
    try:
        blob = base64.b64decode(body.content_b64, validate=True)
        kind = srcs.kind_of(body.name)
        text = await asyncio.to_thread(srcs.extract, body.name, blob)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(400, str(e) if isinstance(e, srcs.SourceError) else "content_b64 is not base64") from e
    sid = await db.brief_source_add(bid, b["rev"], body.actor, {"name": body.name, "kind": kind, "bytes": len(blob),
                                                                "sha256": hashlib.sha256(blob).hexdigest(), "text": text})
    if sid is None:
        raise HTTPException(409, f"the brief is not open, or already holds {db.MAX_SOURCES} sources")
    note = "" if text.strip() else "no text layer (a scan?): the authors cannot read it"
    return {"id": sid, "chars": len(text), "note": note, "brief": _guided(await db.brief_get(bid))}


@app.delete("/briefs/{bid}/sources/{sid}", dependencies=[Depends(require_api_key)])
async def remove_brief_source(bid: str, sid: str, actor: str = ""):
    await _brief_or_404(bid)
    if not _valid_uuid(sid) or not await db.brief_source_remove(bid, sid, actor):
        raise HTTPException(404, "no such source")
    return _guided(await db.brief_get(bid))


@app.post("/briefs/{bid}/suggest", dependencies=[Depends(require_api_key)])
async def suggest_brief(bid: str, body: SuggestIn):
    """Ask the advisor for options with reasons and sources for questions of the brief. The options are kept as
    `proposals`; the advisor's pick goes in as `suggested` only where nothing is decided. A decided or locked answer is
    never touched."""
    b = await _brief_or_404(bid)
    if body.rev != b["rev"]:
        raise HTTPException(409, f"the brief is at rev {b['rev']}, not {body.rev}; reload it")
    if b["status"] != "open":
        raise HTTPException(409, f"the brief is {b['status']}; reopen it to change it")
    if not LettaClient().configured:
        raise HTTPException(503, "Letta unavailable")
    bank = _questions(b["questionnaire"])
    bank.update({k: {"label": briefs.TEXT_LABEL[k], "multi": False, "options": []} for k in briefs.TEXT_FIELDS})
    unknown = [k for k in body.keys if k not in bank]
    if unknown:
        raise HTTPException(400, f"not a question of this brief: {', '.join(unknown)}")
    open_ = {k for k in bank if b["fields"].get(k, {}).get("state", "suggested") == "suggested"}
    keys = [k for k in (body.keys or bank) if k in open_]
    if not keys:
        return {"proposals": {}, "notes": ["every question asked about is already decided"], "brief": _guided(b)}
    try:
        res = await advisor.propose(b, {k: bank[k] for k in keys}, await db.brief_sources(bid))
    except LettaError as e:
        raise HTTPException(502, f"the advisor failed: {e}") from e
    props = {k: {**v, "at": briefs.now()} for k, v in res["proposals"].items()}
    picks = {k: v["pick"] for k, v in props.items() if v["pick"] not in ("", [])}
    # The advisor takes a while; the requester may have edited meanwhile. Its proposals go onto the brief as it is now
    # (apply_patch never lets a suggestion overwrite a decided or locked answer), retried once if a change lands between.
    for _ in range(3):
        cur = await _brief_or_404(bid)
        try:
            new, events = briefs.apply_patch(cur, {"rev": cur["rev"], "proposals": props, "suggest": picks},
                                             body.actor or "advisor")
        except briefs.BriefError as e:
            raise HTTPException(e.status, str(e)) from e
        if not events or await db.brief_save(new, cur["rev"], events):
            break
    else:
        raise HTTPException(409, "the brief kept changing while the advisor answered; ask again")
    return {"proposals": props, "notes": res["notes"], "brief": _guided(await db.brief_get(bid))}


async def _package_members(b: dict) -> list[dict]:
    from . import package as pkg
    if not b.get("job_ids"):
        return []
    sop_id = b["job_ids"][-1]
    sop = await db.job_get(sop_id)
    out = [pkg.member(sop, await _job_doc(sop), sop_id)]
    started = ((sop or {}).get("result") or {}).get("package_jobs") or []
    for a in started:
        j = await db.job_get(a["job_id"])
        out.append(pkg.member(j, await _job_doc(j), a["job_id"], a.get("code", ""), a.get("title_en", "")))
    # Annexes the build asked for that have not started yet (they start once the SOP is saved, or did not start).
    for a in (((sop or {}).get("payload") or {}).get("package_annexes") or [])[len(started):]:
        err = ((sop or {}).get("result") or {}).get("package_error", "") or \
            ("the SOP did not finish, so its annexes were not started" if (sop or {}).get("status") in ("failed", None) else "")
        out.append(pkg.pending(a, err))
    return out


async def _job_doc(job: dict | None) -> dict | None:
    did = ((job or {}).get("result") or {}).get("document_id")
    return await db.document_get(did) if did and _valid_uuid(did) else None


@app.get("/briefs/{bid}/package", dependencies=[Depends(require_api_key)])
async def brief_package(bid: str):
    """The latest build of the brief as one package: the SOP (or the one document) and every annex it started."""
    from . import package as pkg
    b = await _brief_or_404(bid)
    members = await _package_members(b)
    return {"brief_id": bid, "package": b["package"], "members": [{k: v for k, v in m.items() if k != "file"} | {"has_file": bool(m["file"])}
                                                                  for m in members], **pkg.summary(members)}


@app.get("/briefs/{bid}/package.pdf", dependencies=[Depends(require_api_key)])
async def brief_package_pdf(bid: str):
    """The SOP and its annexes, in that order, as one PDF from the house renderer."""
    from . import package as pkg
    b = await _brief_or_404(bid)
    members = await _package_members(b)
    if not members:
        raise HTTPException(404, "nothing has been built from this brief yet")
    waiting = [m["code"] or m["title_en"] or m["job_id"] for m in members if not m["file"]]
    if waiting:
        raise HTTPException(409, "not built yet: " + ", ".join(waiting))
    if not settings.gotenberg_url:
        raise HTTPException(503, "PDF renderer unavailable")
    sem = asyncio.Semaphore(3)

    async def one(m):
        async with sem:
            return await _render_pdf(m["file"], m["code"])
    head, annexes = members[0], sorted(members[1:], key=lambda m: m["code"])
    pdfs = await asyncio.gather(*(one(m) for m in [head, *annexes]))
    blob = await asyncio.to_thread(pkg.merge, list(pdfs))
    name = f"{head['code'] or 'package'}_package.pdf"
    return Response(content=blob, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


_FAMILY_OF = {"sop": "QCSOP", "sop_annexes": "QCSOP", "form": "QCT", "report": "QCT"}


@app.post("/briefs/{bid}/build", dependencies=[Depends(require_api_key)])
async def build_brief(bid: str, body: BuildBriefIn):
    """Build from wherever the brief stands. A missing code is the register's next free one; everything the requester
    has not decided goes to the authors and is listed as `assumed` in the job."""
    b = await _brief_or_404(bid)
    if body.rev is not None and body.rev != b["rev"]:
        raise HTTPException(409, f"the brief is at rev {b['rev']}, not {body.rev}; reload it")
    if not LettaClient().configured:
        raise HTTPException(503, "Letta unavailable")
    if b["status"] != "open":
        raise HTTPException(409, f"the brief is {b['status']}; reopen it to build")
    taken = await db.codes_in_use() - await db.codes_of_brief(bid)     # a rebuild keeps its own number
    if not b["meta"].get("code"):
        try:
            if b["package"] == "annex":
                if not b.get("parent_sop"):
                    raise HTTPException(400, "an annex needs its SOP (parent_sop) before it can be numbered")
                code = house_codes.next_code(parent=b["parent_sop"], taken=taken)
            else:
                dept = (b["meta"].get("department") or "QC").upper()
                fam = _FAMILY_OF[b["package"]].replace("QC", dept, 1)
                code = house_codes.next_code(family=fam, taken=taken)
        except ValueError as e:
            raise HTTPException(400, f"cannot number this document: {e}") from e
        b["meta"]["code"] = code
    try:
        payload = briefs.to_workflow(b, await db.brief_sources(bid))
        new, events = briefs.apply_patch(b, {"rev": b["rev"], "meta": {"code": b["meta"]["code"]}}, body.actor)
    except briefs.BriefError as e:
        raise HTTPException(e.status, str(e)) from e
    _check_meta(payload["meta"], ("title_mk", "title_en", "code"))
    payload["requested_by"] = body.actor
    # The job and the brief's record of it are one step: if the brief moved on meanwhile (an edit sent just before
    # Build), the job is failed at once and the requester reloads — never a job the brief does not know about.
    jid = await db.job_create("workflow", payload, body.actor)
    new["job_ids"] = [*b.get("job_ids", []), jid]
    events.append({"op": "build", "key": jid, "before": None, "after": {"job_id": jid, "assumed": payload["assumed"]},
                   "actor": body.actor})
    if not new["rev"] > b["rev"]:
        new["rev"] = b["rev"] + 1
    if not await db.brief_save(new, b["rev"], events):
        await db.job_update(jid, status="failed", error="the brief changed while the build started; not run")
        raise HTTPException(409, "the brief changed meanwhile; reload it and build again")
    _fire_and_forget(run_workflow(jid))
    return {"job_id": jid, "status": "queued", "code": b["meta"]["code"], "assumed": payload["assumed"]}
