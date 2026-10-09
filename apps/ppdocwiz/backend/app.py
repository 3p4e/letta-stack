#!/usr/bin/env python3
"""
PP Doc Wiz — backend gateway (FastAPI).

One container that:
  • embeds the pp-document-suite engine → the WIZARD path builds house-style .docx in-process
    (deterministic, no LLM), verifies with pp_verify, and offers .docx / .pdf download;
  • proxies the CHAT path to a Letta agent (freeform → the agent composes + builds);
  • serves the PP Suite frontend (../frontend/suite, built from ../web) at "/", with the
    original single-file SPA kept at /legacy (../frontend/index.html).

Config (env):
  PPDOCWIZ_API_KEY  REQUIRED. Shared secret for every /api route except /api/health.
                    Unset => the service refuses every call with 503 (never open).
  PP_SUITE_DIR   path to pp-document-suite (default: sibling of this repo checkout, or /opt/pp-document-suite)
  PP_OUT_DIR     where built docs are written (default: /data or tempdir)
  LETTA_BASE_URL Letta REST base (enables the chat tab); LETTA_TOKEN optional
  LETTA_AGENT    ALLOWLIST of agents the chat proxy may reach (comma-separated,
                 default qms_docx_formatter) — not merely a default
  PPDOCWIZ_COOKIE_SECURE  "0" only for plain-HTTP loopback dev (default secure)
  PPDOCWIZ_UI    "legacy" serves the old single-file SPA at "/" (default: the suite, when built)
  DOCENGINE_URL / DOCENGINE_API_KEY  internal DocEngine base and its key; /api/docengine/* forwards
                 there (Questionnaire, Jobs, Library screens). Unset => those routes 503.
Run: uvicorn app:app --host 0.0.0.0 --port 8770
Publish on loopback only and route via Traefik; see docker-compose.yml.
"""
import asyncio, threading, os, sys, io, re, json, uuid, hmac, tempfile, subprocess, contextlib, shutil, urllib.request, urllib.error, urllib.parse
from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import wizard
import security
from config import settings

# Every caller-supplied string that becomes a path component goes through this.
# Same collapse as apps/wwf-docengine/app/builder.py:56-59 and the same allowlist
# guarantee as pp-document-suite/integrations/service.py:33-35. (Three near-copies
# now exist in the repo; integrations/ is not importable from this container, so
# duplicating the rule beats reshaping the image's import graph.)
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_name(name: str) -> str:
    return (_SAFE_NAME.sub("_", (name or "document").strip()) or "document")[:120]

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
# The suite is a Vite build (apps/ppdocwiz/web → frontend/suite). It is optional: a
# checkout without `npm run build` still serves the legacy SPA at "/".
SUITE_UI = os.path.join(HERE, "..", "frontend", "suite")

app = FastAPI(title="PP Doc Wiz", version="1.0")

# Static bundle only: hashed JS/CSS, fonts and the logo — no data, no credential.
# Same exposure as "/" itself, which is ungated because it is the sign-in page.
if os.path.isdir(os.path.join(SUITE_UI, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(SUITE_UI, "assets")), name="suite-assets")


class BuildReq(BaseModel):
    payload: dict


class ChatReq(BaseModel):
    message: str
    agent: str | None = None


class SessionReq(BaseModel):
    key: str


class RawBuildReq(BaseModel):
    markdown: str
    out_name: str | None = None


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
    # DELIBERATELY UNGATED — the compose healthcheck calls this with no headers
    # (docker-compose.yml), so gating it makes the container permanently
    # "unhealthy". Do not add a dependency here without changing that too.
    # The container filesystem path ("suite") used to be returned and is not:
    # this endpoint is reachable without a credential, and the frontend only
    # ever reads .letta and .pdf.
    return {"ok": True, "letta": bool(os.environ.get("LETTA_BASE_URL")),
            "pdf": bool(shutil.which("soffice") or os.environ.get("GOTENBERG_URL"))}


@app.post("/api/session")
def open_session(r: SessionReq):
    """Exchange the API key for an HttpOnly cookie.

    This is what lets the browser frontend authenticate at all: its download
    links are plain <a href> anchors, and a browser cannot put a header on an
    anchor navigation. The cookie is derived from the key, never the key itself,
    so an XSS in the frontend has no credential to steal."""
    if not settings.api_key:
        return JSONResponse({"ok": False, "error": "not configured"}, status_code=503)
    if not hmac.compare_digest(r.key, settings.api_key):
        return JSONResponse({"ok": False, "error": "bad key"}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie(security.COOKIE, security.session_value(settings.api_key),
                    httponly=True, samesite="strict",
                    secure=settings.cookie_secure, max_age=8 * 3600, path="/")
    return resp


@app.get("/api/doctypes", dependencies=[Depends(security.require_api_key)])
def doctypes():
    return {"doctypes": wizard.DOCTYPES}


@app.get("/api/example", dependencies=[Depends(security.require_api_key)])
def example():
    return {"payload": wizard.EXAMPLE, "markdown": wizard.compose_markdown(wizard.EXAMPLE)}


@app.post("/api/wizard/preview", dependencies=[Depends(security.require_api_key)])
def preview(r: BuildReq):
    return {"markdown": wizard.compose_markdown(r.payload)}


@app.post("/api/wizard/build", dependencies=[Depends(security.require_api_key)])
def build(r: BuildReq):
    md = wizard.compose_markdown(r.payload)
    # _safe_name, not the old two .replace() calls: those stripped "/" and " "
    # but left quotes and angle brackets intact, and this value is returned as
    # download_docx and interpolated into an href="..." by the frontend. A code
    # of  x" onmouseover="y  broke out of the attribute. Sanitising at the write
    # side kills that chain at its source.
    doc_id = _safe_name(r.payload.get("code") or "document") + "_" + uuid.uuid4().hex[:8]
    try:
        ok, verify, path = _build_from_markdown(md, doc_id)
    except Exception as e:
        import traceback
        return JSONResponse({"ok": False, "error": traceback.format_exc()[-900:], "markdown": md}, status_code=422)
    if not ok:
        _discard(path)
    return {"ok": ok, "verify": verify, "doc_id": doc_id, "markdown": md,
            "download_docx": f"/api/download/{doc_id}.docx",
            "download_pdf": f"/api/download/{doc_id}.pdf"}


def _discard(docx_path: str):
    """A FAIL build is never served: remove the .docx (and any PDF rendered from it)."""
    for p in (docx_path, docx_path[:-len(".docx")] + ".pdf"):
        with contextlib.suppress(FileNotFoundError):
            os.unlink(p)


@app.post("/api/build", dependencies=[Depends(security.require_api_key)])
def raw_build(r: RawBuildReq):
    """Bilingual Markdown as typed in the Builder's Source view → the SAME engine the
    wizard path uses. (It used to go to DocEngine POST /build, whose vendored engine
    is the canon-2026-07 copy and printed [[BOX]] markers verbatim, among others.)"""
    code = ((re.search(r"^code:\s*(.+)$", r.markdown, re.M) or [None, r.out_name])[1] or "").strip()
    doc_id = _safe_name(code or "document") + "_" + uuid.uuid4().hex[:8]
    try:
        ok, verify, path = _build_from_markdown(r.markdown, doc_id)
    except Exception as e:
        return JSONResponse({"ok": False, "verify": "", "error": str(e)[:300]}, status_code=422)
    if not ok:
        _discard(path)
        return JSONResponse({"ok": False, "verify": verify, "error": "verify FAILED"}, status_code=422)
    return {"ok": True, "verify": verify, "doc_id": doc_id,
            "download_docx": f"/api/download/{doc_id}.docx",
            "download_pdf": f"/api/download/{doc_id}.pdf"}


# PDFs come from pp-document-suite/scripts/pp_render.py: the shared Gotenberg service when
# GOTENBERG_URL is set, else local LibreOffice with the field-updating macro profile, so an
# SOP's table of contents is filled either way. Concurrent local soffice instances hang (seen
# in the 09.10 test): one render at a time; a request that waited reuses the finished PDF.
_RENDER_LOCK = threading.Lock()


def _render_pdf(docx: str, pdf: str):
    import pp_render
    pp_render.render_pdf(docx, pdf)


@app.get("/api/download/{name}", dependencies=[Depends(security.require_api_key)])
def download(name: str, inline: int = 0):
    base, ext = os.path.splitext(name)
    # Extension allowlist. Previously anything that was not ".pdf" fell through
    # to the else branch and served the .docx under the requested name, so
    # GET /api/download/foo.exe returned a document called foo.exe.
    if ext not in (".docx", ".pdf"):
        return JSONResponse({"error": "unsupported format"}, status_code=400)
    # `name` arrives from the URL path and used to be joined straight onto OUT.
    # Starlette compiles {name} to [^/]+ and uvicorn decodes before routing, so a
    # multi-segment traversal 404s at the router today — but that is a property
    # of the pinned framework versions, not a guarantee, and switching this to
    # {name:path} would make it live. Sanitise, then prove containment.
    root = os.path.realpath(OUT)
    docx = os.path.realpath(os.path.join(root, _safe_name(base) + ".docx"))
    if os.path.commonpath([root, docx]) != root:
        return JSONResponse({"error": "not found"}, status_code=404)
    if not os.path.exists(docx):
        return JSONResponse({"error": "not found"}, status_code=404)
    stem = os.path.basename(docx)[:-len(".docx")]
    if ext == ".pdf":
        pdf = os.path.join(root, stem + ".pdf")
        if not os.path.exists(pdf):
            if not (shutil.which("soffice") or os.environ.get("GOTENBERG_URL")):
                return JSONResponse({"error": "no PDF renderer (set GOTENBERG_URL or install LibreOffice)"}, status_code=501)
            import pp_render
            try:
                with _RENDER_LOCK:
                    if not os.path.exists(pdf):
                        _render_pdf(docx, pdf)
            except subprocess.TimeoutExpired:
                return JSONResponse({"error": "PDF rendering timed out"}, status_code=504)
            except pp_render.RenderError as e:
                return JSONResponse({"error": str(e)[:300]}, status_code=502)
        # ?inline=1 lets the suite's Preview show the PDF in a frame instead of downloading it.
        return FileResponse(pdf, filename=stem + ".pdf", media_type="application/pdf",
                            content_disposition_type="inline" if inline else "attachment")
    return FileResponse(docx, filename=stem + ".docx",
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


@app.post("/api/chat", dependencies=[Depends(security.require_api_key)])
def chat(r: ChatReq):
    if not os.environ.get("LETTA_BASE_URL"):
        return JSONResponse({"ok": False, "error": "chat disabled: set LETTA_BASE_URL"}, status_code=503)
    # LETTA_AGENT is an ALLOWLIST, not a fallback. The agent name used to be
    # taken from the request body with the env value as a mere default, so a
    # caller could name ANY agent on the server (the lookup below scans up to
    # 200) and converse with it — reaching agents with tools and memory this app
    # has no business exposing. An unlisted name is now refused outright.
    allowed = settings.agent_allowlist
    name = r.agent or (allowed[0] if allowed else "")
    if name not in allowed:
        return JSONResponse(
            {"ok": False, "error": f"agent {name!r} is not permitted by this deployment"},
            status_code=400)
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


# ---------------- DocEngine proxy (same-origin, for the suite) ----------------
# The browser holds only the ppdocwiz session cookie; the DocEngine key never leaves
# this process. Only the DocEngine's own public routes are forwarded.
_DE_ROUTES = {"health", "questionnaires", "workflows", "build", "documents", "knowledge"}
_DE_PASS_HEADERS = ("content-type", "content-disposition", "content-length")


@app.api_route("/api/docengine/{path:path}", methods=["GET", "POST", "HEAD"],
               dependencies=[Depends(security.require_api_key)])
async def docengine_proxy(path: str, request: Request):
    if not settings.docengine_url:
        return JSONResponse({"error": "DocEngine not configured: set DOCENGINE_URL"}, status_code=503)
    parts = [p for p in path.split("/") if p]
    if not parts or parts[0] not in _DE_ROUTES or any(p in (".", "..") for p in parts):
        return JSONResponse({"error": "not found"}, status_code=404)
    url = settings.docengine_url + "/" + "/".join(urllib.parse.quote(p, safe="") for p in parts)
    if request.url.query:
        url += "?" + request.url.query
    body = await request.body() if request.method == "POST" else None
    # DocEngine routes are GET-only; a HEAD (the Library's availability probe) is
    # sent upstream as GET and answered without the body.
    hdrs = {"Content-Type": request.headers.get("content-type", "application/json"),
            "X-API-Key": settings.docengine_api_key, "User-Agent": "ppdocwiz/1.0"}
    if request.method == "HEAD":
        hdrs["Range"] = "bytes=0-0"          # availability probe: one byte, not the whole file
    req = urllib.request.Request(url, data=body, method="GET" if request.method == "HEAD" else request.method, headers=hdrs)

    def fetch():
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    try:
        # urllib blocks; off the event loop so one slow DocEngine call cannot stall every other request
        status, headers, data = await asyncio.to_thread(fetch)
    except Exception as e:
        return JSONResponse({"error": "DocEngine unreachable: " + str(e)[:200]}, status_code=502)
    if request.method == "HEAD" and status == 206:
        status = 200
    out = {k: headers[k] for k in _DE_PASS_HEADERS if headers.get(k) and k != "content-length"}
    return Response(content=b"" if request.method == "HEAD" else data, status_code=status,
                    media_type=headers.get("content-type"), headers=out)


def _legacy():
    if os.path.exists(FRONTEND):
        return HTMLResponse(open(FRONTEND, encoding="utf-8").read())
    return HTMLResponse("<h1>PP Doc Wiz</h1><p>frontend/index.html missing</p>")


@app.get("/")
def index():
    suite = os.path.join(SUITE_UI, "index.html")
    if os.environ.get("PPDOCWIZ_UI", "").lower() != "legacy" and os.path.exists(suite):
        return HTMLResponse(open(suite, encoding="utf-8").read())
    return _legacy()


@app.get("/legacy")
def legacy():
    return _legacy()
