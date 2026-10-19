# docengine.app.package — one view and one PDF for what a Document Brief built (Head of QC, 18.10.2026: "create SOP +
# Annexes etc from the same workflow").
#
# A build of a brief is one job; an SOP + annexes build starts one annex job per annex once the SOP is saved
# (pipeline._package, result.package_jobs). members() lists the latest build and its annexes, each with its status
# and the file a PDF is made from: the registered document (done) or the verified artifact awaiting a person's review.
# The merged PDF is the SOP followed by its annexes in code order, each rendered by the house renderer. Not a QMS
# record (CLAUDE.md §10).
from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter

READY = ("done", "awaiting_review")


def member(job: dict | None, doc: dict | None, job_id: str, code: str = "", title: str = "") -> dict:
    """One row of the package: what the job is, where it stands and which file a PDF is made from."""
    if not job:
        return {"job_id": job_id, "code": code, "title_en": title, "status": "missing", "stage": "", "file": "",
                "document_id": None, "review_reason": "", "assumed": [], "error": "the job is not on record"}
    p, r = job.get("payload") or {}, job.get("result") or {}
    path = (doc or {}).get("path") or (r.get("artifact") or {}).get("path") or ""
    return {"job_id": job_id, "code": (p.get("meta") or {}).get("code") or code,
            "title_en": (p.get("meta") or {}).get("title_en") or title, "status": job["status"],
            "stage": job.get("stage") or "", "document_id": r.get("document_id"),
            "file": path if job["status"] in READY and path and Path(path).is_file() else "",
            "review_reason": r.get("review_reason", ""), "assumed": p.get("assumed") or [],
            "error": (job.get("error") or r.get("package_error") or "")[:300]}


def pending(annex: dict, error: str = "") -> dict:
    """An annex of the package whose job has not started: it starts when the SOP is saved."""
    return {"job_id": "", "code": "", "title_en": annex.get("title_en") or annex.get("title_mk") or "",
            "status": "failed" if error else "pending", "stage": "", "document_id": None, "file": "",
            "review_reason": "", "assumed": [], "error": error or "starts when the SOP is saved"}


def summary(members: list[dict]) -> dict:
    """Where the package stands as a whole."""
    st = [m["status"] for m in members]
    return {"complete": bool(members) and all(s in READY for s in st),
            "failed": [m["code"] or m["title_en"] or m["job_id"] for m in members if m["status"] in ("failed", "missing")],
            "running": [m["code"] or m["title_en"] for m in members if m["status"] in ("queued", "running", "pending")],
            "awaiting_review": [m["code"] for m in members if m["status"] == "awaiting_review"],
            "pdf_ready": bool(members) and all(m["file"] for m in members)}


def merge(pdfs: list[bytes]) -> bytes:
    w = PdfWriter()
    for blob in pdfs:
        for page in PdfReader(io.BytesIO(blob)).pages:
            w.add_page(page)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()
