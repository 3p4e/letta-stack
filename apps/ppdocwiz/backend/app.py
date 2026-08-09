#!/usr/bin/env python3
"""
PP Doc Wiz — backend gateway (FastAPI).

One container that:
  • embeds the pp-document-suite engine → the WIZARD path builds house-style .docx in-process
    (deterministic, no LLM), verifies with pp_verify, and offers .docx / .pdf download;
  • proxies the CHAT path to a Letta agent (freeform → the agent composes + builds);
  • serves the single-file frontend (../frontend/index.html).

Config (env):
  PP_SUITE_DIR   path to pp-document-suite (default: sibling of this repo checkout, or /opt/pp-document-suite)
  PP_OUT_DIR     where built docs are written (default: /data or tempdir)
  LETTA_BASE_URL Letta REST base (enables the chat tab); LETTA_TOKEN optional; LETTA_AGENT default qms_docx_formatter
Run: uvicorn app:app --host 0.0.0.0 --port 8770
"""
import os, sys, io, json, uuid, tempfile, subprocess, contextlib, shutil, urllib.request, urllib.error
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
import wizard

HERE = os.path.dirname(os.path.abspath(__file__))
def _find_suite():
    for c in (os.environ.get("PP_SUITE_DIR"),
              os.path.join(HERE, "..", "..", "pp-document-suite"),
              "/opt/pp-document-suite", "/root/.letta/pp-document-suite"):
        if c and os.path.exists(os.path.join(c, "scripts", "build_from_md.py")):
            return os.path.abspath(c)
    return os.path.abspath(os.path.join(HERE, "..", "..", "pp-document-suite"))
SUITE = _find_suite()
sys.path.insert(0, os.path.join(SUITE, "scripts"))
for extra in ("/root/.letta/pp-libs",):          # persistent deps location on the Letta host
    if os.path.isdir(extra): sys.path.insert(0, extra)

OUT = os.environ.get("PP_OUT_DIR") or ("/data" if os.path.isdir("/data") else tempfile.gettempdir())
os.makedirs(OUT, exist_ok=True)
FRONTEND = os.path.join(HERE, "..", "frontend", "index.html")

app = FastAPI(title="PP Doc Wiz", version="1.0")


class BuildReq(BaseModel):
    payload: dict


class ChatReq(BaseModel):
    message: str
    agent: str | None = None


def _build_from_markdown(md: str, base: str):
    """Run the engine in-process: markdown -> .docx + verify. Returns (ok, verify, docx_path)."""
    out = os.path.join(OUT, base + ".docx")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md); src = f.name
    try:
        import importlib, build_from_md; importlib.reload(build_from_md); build_from_md.main(src, out)
    finally:
        os.unlink(src)
    verify = ""
    try:
        import pp_verify, importlib; importlib.reload(pp_verify)
        buf = io.StringIO(); oa = sys.argv; sys.argv = ["pp_verify", out]
        try:
            with contextlib.redirect_stdout(buf): pp_verify.main()
        except SystemExit: pass
        finally: sys.argv = oa
        verify = buf.getvalue().strip()
    except Exception as e:
        verify = "verify-error: " + str(e)[:150]
    ok = os.path.exists(out) and "RESULT: PASS" in verify
    return ok, verify, out


@app.get("/api/health")
def health():
    return {"ok": True, "suite": SUITE, "letta": bool(os.environ.get("LETTA_BASE_URL")),
            "pdf": bool(shutil.which("soffice"))}


@app.get("/api/doctypes")
def doctypes():
    return {"doctypes": wizard.DOCTYPES}


@app.get("/api/example")
def example():
    return {"payload": wizard.EXAMPLE, "markdown": wizard.compose_markdown(wizard.EXAMPLE)}


@app.post("/api/wizard/preview")
def preview(r: BuildReq):
    return {"markdown": wizard.compose_markdown(r.payload)}


@app.post("/api/wizard/build")
def build(r: BuildReq):
    md = wizard.compose_markdown(r.payload)
    doc_id = (r.payload.get("code") or "document").replace("/", "_").replace(" ", "_") + "_" + uuid.uuid4().hex[:8]
    try:
        ok, verify, path = _build_from_markdown(md, doc_id)
    except Exception as e:
        import traceback
        return JSONResponse({"ok": False, "error": traceback.format_exc()[-900:], "markdown": md}, status_code=422)
    return {"ok": ok, "verify": verify, "doc_id": doc_id, "markdown": md,
            "download_docx": f"/api/download/{doc_id}.docx",
            "download_pdf": f"/api/download/{doc_id}.pdf"}


@app.get("/api/download/{name}")
def download(name: str):
    base, ext = os.path.splitext(name)
    docx = os.path.join(OUT, base + ".docx")
    if not os.path.exists(docx):
        return JSONResponse({"error": "not found"}, status_code=404)
    if ext == ".pdf":
        pdf = os.path.join(OUT, base + ".pdf")
        if not os.path.exists(pdf):
            if not shutil.which("soffice"):
                return JSONResponse({"error": "no PDF renderer (LibreOffice not installed)"}, status_code=501)
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, docx], check=True)
        return FileResponse(pdf, filename=base + ".pdf", media_type="application/pdf")
    return FileResponse(docx, filename=base + ".docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ---------------- chat path (Letta proxy) ----------------
def _letta(method, path, body=None, timeout=90):
    base = os.environ["LETTA_BASE_URL"].rstrip("/")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "User-Agent": "ppdocwiz/1.0"})
    tok = os.environ.get("LETTA_TOKEN") or os.environ.get("LETTA_API_KEY")
    if tok: req.add_header("Authorization", "Bearer " + tok)
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode()
    return json.JSONDecoder().raw_decode(raw)[0] if raw.strip() else {}


@app.post("/api/chat")
def chat(r: ChatReq):
    if not os.environ.get("LETTA_BASE_URL"):
        return JSONResponse({"ok": False, "error": "chat disabled: set LETTA_BASE_URL"}, status_code=503)
    name = r.agent or os.environ.get("LETTA_AGENT", "qms_docx_formatter")
    try:
        agents = _letta("GET", "/v1/agents/?limit=200")
        aid = next((a["id"] for a in agents if a.get("name") == name), None)
        if not aid:
            return JSONResponse({"ok": False, "error": f"agent '{name}' not found"}, status_code=404)
        run = _letta("POST", f"/v1/agents/{aid}/messages", {"messages": [{"role": "user", "content": r.message}]}, timeout=180)
        msgs = run.get("messages", run if isinstance(run, list) else [])
        reply, built = "", None
        for m in msgs:
            mt = m.get("message_type")
            if mt == "assistant_message":
                reply = m.get("content") if isinstance(m.get("content"), str) else reply
            elif mt == "tool_return_message":
                try:
                    tr = json.loads(m.get("tool_return", "{}"))
                    if tr.get("ok") and tr.get("path"): built = tr
                except Exception: pass
        return {"ok": True, "agent": name, "reply": reply or "(no assistant text)", "built": built}
    except urllib.error.HTTPError as e:
        return JSONResponse({"ok": False, "error": f"letta {e.code}: {e.read().decode()[:200]}"}, status_code=502)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:300]}, status_code=502)


@app.get("/")
def index():
    if os.path.exists(FRONTEND):
        return HTMLResponse(open(FRONTEND, encoding="utf-8").read())
    return HTMLResponse("<h1>PP Doc Wiz</h1><p>frontend/index.html missing</p>")
