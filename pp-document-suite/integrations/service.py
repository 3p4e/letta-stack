#!/usr/bin/env python3
"""
service.py — the Purely Plant Document Suite as a small REST build service. Owns the engine, the
template, the fonts and (optionally) a DOCX->PDF renderer, so many thin clients / agents on other
hosts can build house-style .docx without any Python of their own.

  POST /build    {markdown, name}      -> {ok, path, verify}   (and writes <name>.docx)
  POST /build.docx {markdown, name}    -> streams the .docx file back
  POST /build.pdf  {markdown, name}    -> streams a PDF (needs LibreOffice `soffice` on PATH)
  GET  /health                         -> {ok, engine}

Run:  pip install fastapi uvicorn python-docx lxml
      uvicorn service:app --host 0.0.0.0 --port 8600
This is the same contract the site QMS API (:8500) already follows (see LETTA_INTEGRATION.md).
"""
import os, sys, tempfile, subprocess, shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

SUITE = os.environ.get("PP_SUITE_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SUITE, "scripts")
OUTDIR = os.environ.get("PP_OUT_DIR", tempfile.gettempdir())

app = FastAPI(title="Purely Plant Document Suite", version="1.6.2")


class BuildReq(BaseModel):
    markdown: str
    name: str = "document"


def _safe_name(name: str) -> str:
    keep = "".join(c for c in name if c.isalnum() or c in "-_.")
    return keep or "document"


def _build(markdown: str, name: str):
    name = _safe_name(name)
    out = os.path.join(OUTDIR, name + ".docx")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(markdown)
        src = f.name
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_from_md.py"), src, out], check=True)
        v = subprocess.run([sys.executable, os.path.join(SCRIPTS, "pp_verify.py"), out],
                           capture_output=True, text=True)
    finally:
        os.unlink(src)
    return out, ("RESULT: PASS" in v.stdout), v.stdout.strip()


def _to_pdf(docx_path: str):
    if not shutil.which("soffice"):
        return None
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir",
                    os.path.dirname(docx_path), docx_path], check=True)
    pdf = os.path.splitext(docx_path)[0] + ".pdf"
    return pdf if os.path.exists(pdf) else None


@app.get("/health")
def health():
    return {"ok": os.path.exists(os.path.join(SCRIPTS, "build_from_md.py")), "engine": SUITE}


@app.post("/build")
def build(r: BuildReq):
    out, ok, verify = _build(r.markdown, r.name)
    return JSONResponse({"ok": ok, "path": out, "verify": verify})


@app.post("/build.docx")
def build_docx(r: BuildReq):
    out, ok, verify = _build(r.markdown, r.name)
    if not ok:
        return JSONResponse({"ok": False, "verify": verify}, status_code=422)
    return FileResponse(out, filename=os.path.basename(out),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.post("/build.pdf")
def build_pdf(r: BuildReq):
    out, ok, verify = _build(r.markdown, r.name)
    if not ok:
        return JSONResponse({"ok": False, "verify": verify}, status_code=422)
    pdf = _to_pdf(out)
    if not pdf:
        return JSONResponse({"ok": False, "error": "no PDF renderer (install LibreOffice/soffice)",
                             "docx": out}, status_code=501)
    return FileResponse(pdf, filename=os.path.basename(pdf), media_type="application/pdf")
