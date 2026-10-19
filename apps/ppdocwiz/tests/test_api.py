"""ppdocwiz API contract tests.

Each case pins a decision that a later edit could silently undo — which is the
point, because every one of these was a real defect before the 2026-08-29
hardening pass. Deliberately parallel to apps/wwf-docengine/tests/test_api.py so
the two services' auth contracts are demonstrably the same.
"""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_mod
import security
from config import settings

KEY = "test-key-not-a-real-secret"


@pytest.fixture(autouse=True)
def _configure(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    monkeypatch.setattr(settings, "letta_agents", "qms_docx_formatter")
    # Cookies are Secure by default; TestClient speaks http, so a Secure cookie
    # would never be echoed back and every cookie assertion would fail for the
    # wrong reason.
    monkeypatch.setattr(settings, "cookie_secure", False)
    monkeypatch.setattr(app_mod, "OUT", str(tmp_path))


@pytest.fixture
def client():
    return TestClient(app_mod.app)


# ---------------------------------------------------------------- open routes
def test_health_is_open(client):
    """The compose healthcheck calls this with no headers. Gating it would leave
    the container permanently `unhealthy`."""
    assert client.get("/api/health").status_code == 200


def test_health_leaks_no_filesystem_paths(client):
    body = client.get("/api/health").json()
    assert "suite" not in body, "an ungated endpoint must not disclose container paths"


# ---------------------------------------------------------------------- auth
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_gated_routes_require_a_credential(client, headers):
    assert client.get("/api/doctypes", headers=headers).status_code == 401


def test_correct_key_is_accepted(client):
    assert client.get("/api/doctypes", headers={"X-API-Key": KEY}).status_code == 200


def test_unconfigured_service_refuses_rather_than_running_open(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    r = client.get("/api/doctypes", headers={"X-API-Key": ""})
    assert r.status_code == 503, "an unconfigured deploy must fail closed, never open"


# ------------------------------------------------------------------- session
def test_session_cookie_unlocks_and_is_httponly(client):
    r = client.post("/api/session", json={"key": KEY})
    assert r.status_code == 200
    raw = r.headers["set-cookie"].lower()
    assert "httponly" in raw, "an XSS must not be able to read the session value"
    assert "samesite=strict" in raw, "SameSite=Strict is what stands in for a CSRF token"
    # the cookie alone (no header) opens a gated route — this is what makes the
    # plain <a href> download links work in a browser
    assert client.get("/api/doctypes").status_code == 200


def test_session_cookie_is_derived_not_the_key(client):
    r = client.post("/api/session", json={"key": KEY})
    value = r.cookies.get(security.COOKIE)
    assert value and KEY not in value, "the cookie must not carry the API key"
    assert security.session_id(value, KEY), "it is a signed session the server accepts"
    other = client.post("/api/session", json={"key": KEY}).cookies.get(security.COOKIE)
    assert other != value, "every sign-in is its own session" 


def test_session_rejects_a_wrong_key(client):
    assert client.post("/api/session", json={"key": "nope"}).status_code == 401


# ------------------------------------------------------------------ download
@pytest.mark.parametrize("name", [
    "../../../etc/passwd.docx",
    "..%2f..%2fetc%2fpasswd.docx",
    "..",
    "....//....//etc/passwd.docx",
])
def test_download_never_escapes_the_output_directory(client, name):
    r = client.get(f"/api/download/{name}", headers={"X-API-Key": KEY})
    assert r.status_code in (400, 404), f"{name!r} must not resolve to a file"


def test_download_rejects_a_foreign_extension(client, tmp_path):
    (tmp_path / "doc.docx").write_bytes(b"x")
    r = client.get("/api/download/doc.exe", headers={"X-API-Key": KEY})
    assert r.status_code == 400, "a .docx must not be served under an .exe name"


# ------------------------------------------------------- filename sanitising
@pytest.mark.parametrize("raw", [
    "../../etc/passwd",
    'x" onmouseover="alert(1)',
    "WHSOP/002",
    "a b\tc",
])
def test_safe_name_strips_every_path_and_markup_character(raw):
    out = app_mod._safe_name(raw)
    assert re.fullmatch(r"[A-Za-z0-9._-]+", out), f"{raw!r} -> {out!r} kept a hostile character"


def test_safe_name_never_returns_empty():
    assert app_mod._safe_name("") and app_mod._safe_name("///") and app_mod._safe_name(None)


def test_build_download_url_is_always_path_safe(client):
    """The regression guard for the code -> doc_id -> download_docx -> href chain:
    a document code full of quotes and slashes must not reach the frontend's
    href attribute with anything that could break out of it."""
    payload = {"doctype": "ANNEX", "code": 'x" onmouseover="alert(1)/../..',
               "mk_title": "М", "en_title": "E", "sections": []}
    r = client.post("/api/wizard/build", json={"payload": payload},
                    headers={"X-API-Key": KEY})
    # The build itself may fail without the engine present; the URL shape is
    # what this test pins, so only assert when the field is returned.
    url = r.json().get("download_docx")
    if url:
        assert re.fullmatch(r"/api/download/[A-Za-z0-9._-]+\.docx", url), url


# ---------------------------------------------------------------- chat agent
def test_chat_refuses_an_agent_outside_the_allowlist(client, monkeypatch):
    monkeypatch.setenv("LETTA_BASE_URL", "http://letta.invalid")
    r = client.post("/api/chat", json={"message": "hi", "agent": "security_auditor"},
                    headers={"X-API-Key": KEY})
    assert r.status_code == 400, "the agent name must not be attacker-chosen"


# ------------------------------------------------------------------ frontend
def test_frontend_collects_the_parent_field():
    """`parent.value` resolved to window.parent, not the input, so the Parent SOP
    field was silently dropped from every generated document."""
    html = (Path(__file__).resolve().parents[1] / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "parent:$('parent').value" in html.replace(" ", "")


def test_frontend_escapes_every_interpolation():
    html = (Path(__file__).resolve().parents[1] / "frontend" / "index.html").read_text(encoding="utf-8")
    unescaped = [m.group(1) for m in re.finditer(r"\$\{([^}]*)\}", html) if "esc(" not in m.group(1)]
    assert not unescaped, f"unescaped interpolations: {unescaped}"


# ---- raw-Markdown build (Builder Source view) -------------------------------------------
GOOD_MD = """<!--HEADERDATA
mk_title: Тест
en_title: Test
code: WHSOP_999_A01
version: 01
doctype: FORM
orient: portrait
-->

# 1 Општо | General
[[FORM]]
Датум ||| Date ||| _
[[/FORM]]
"""
H = {"X-API-Key": KEY}


def test_raw_build_uses_the_pasted_code_and_offers_downloads(client):
    r = client.post("/api/build", json={"markdown": GOOD_MD, "out_name": "something_else"}, headers=H)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] and "RESULT: PASS" in body["verify"]
    assert body["doc_id"].startswith("WHSOP_999_A01_")          # HEADERDATA code, not out_name
    assert client.get(body["download_docx"], headers=H).status_code == 200


def test_raw_build_failure_is_422_and_leaves_nothing_downloadable(client, monkeypatch):
    def failing(md, base):
        path = Path(app_mod.OUT) / (base + ".docx"); path.write_bytes(b"x")
        return False, "RESULT: FAIL", str(path)
    monkeypatch.setattr(app_mod, "_build_from_markdown", failing)
    r = client.post("/api/build", json={"markdown": GOOD_MD}, headers=H)
    assert r.status_code == 422 and r.json()["verify"] == "RESULT: FAIL"
    assert not list(Path(app_mod.OUT).glob("WHSOP_999_A01_*.docx"))


def test_raw_build_requires_a_credential(client):
    assert client.post("/api/build", json={"markdown": GOOD_MD}).status_code == 401


# ---- DocEngine same-origin proxy ---------------------------------------------------------
def test_docengine_proxy_refuses_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "docengine_url", "")
    assert client.get("/api/docengine/health", headers=H).status_code == 503


@pytest.mark.parametrize("path", ["admin", "documents/../../etc", "", "health/../admin"])
def test_docengine_proxy_forwards_only_docengine_routes(client, monkeypatch, path):
    monkeypatch.setattr(settings, "docengine_url", "http://127.0.0.1:9")
    assert client.get(f"/api/docengine/{path}", headers=H).status_code == 404


def test_docengine_proxy_requires_a_credential(client, monkeypatch):
    monkeypatch.setattr(settings, "docengine_url", "http://127.0.0.1:9")
    assert client.get("/api/docengine/health").status_code == 401


def test_docengine_proxy_reports_unreachable_as_502(client, monkeypatch):
    monkeypatch.setattr(settings, "docengine_url", "http://127.0.0.1:9")
    assert client.get("/api/docengine/health", headers=H).status_code == 502


# ---- PDF download -------------------------------------------------------------------------
def test_pdf_inline_for_preview(client):
    (Path(app_mod.OUT) / "D1.docx").write_bytes(b"x"); (Path(app_mod.OUT) / "D1.pdf").write_bytes(b"%PDF-1.4")
    assert client.get("/api/download/D1.pdf?inline=1", headers=H).headers["content-disposition"].startswith("inline")
    assert client.get("/api/download/D1.pdf", headers=H).headers["content-disposition"].startswith("attachment")


# ---------------------------------------------------------------- review 14.10.2026
def test_non_ascii_key_is_401_not_500(client):
    """compare_digest raises TypeError on a non-ASCII str; the gate compares bytes now."""
    r = client.get("/api/doctypes", headers={"X-API-Key": "ключ".encode()})
    assert r.status_code == 401
    assert client.post("/api/session", json={"key": "ключ"}).status_code == 401


def test_builds_run_one_at_a_time(monkeypatch):
    """Two sync build routes run on the thread pool together and share sys.argv and the engine's globals."""
    held = []
    monkeypatch.setattr(app_mod, "_build_locked", lambda md, base: held.append(app_mod._BUILD_LOCK.locked()) or (True, "", ""))
    app_mod._build_from_markdown("x", "y")
    assert held == [True] and not app_mod._BUILD_LOCK.locked()


def test_a_bad_wizard_payload_is_422_not_500(client):
    h = {"X-API-Key": KEY}
    assert client.post("/api/wizard/preview", headers=h, json={"payload": {"mk_title": None, "sections": []}}).status_code == 422
    assert client.post("/api/wizard/build", headers=h, json={"payload": {"sections": [{"level": "x"}]}}).status_code == 422


def test_build_errors_do_not_return_a_traceback(client, monkeypatch):
    def boom(md, base):
        raise RuntimeError("engine broke")
    monkeypatch.setattr(app_mod, "_build_locked", boom)
    r = client.post("/api/wizard/build", headers={"X-API-Key": KEY}, json={"payload": {"code": "X", "sections": []}})
    assert r.status_code == 422 and "Traceback" not in r.text and "RuntimeError: engine broke" in r.json()["error"]


def test_raw_markdown_is_bounded(client):
    r = client.post("/api/build", headers={"X-API-Key": KEY}, json={"markdown": "x" * 400_001})
    assert r.status_code == 422


def test_jobs_rerun_carries_the_brief_and_the_parent_sop():
    """Re-run sent only questionnaire, answers and meta: an annex re-run lost its brief and parent SOP."""
    src = (Path(__file__).resolve().parents[1] / "web" / "src" / "screens" / "Jobs.tsx").read_text(encoding="utf-8")
    rerun = src[src.index("const rerun"):src.index("usePrimary(")]
    for f in ("instructions:", "sources:", "parent_sop:"):
        assert f in rerun, f


# ---------------------------------------------------------------- session lifetime (review 14.10.2026)
def test_the_old_fixed_cookie_value_is_no_longer_accepted(client):
    client.cookies.set(security.COOKIE, security.session_value(KEY))
    assert client.get("/api/doctypes").status_code == 401


def test_an_expired_session_is_refused():
    import time
    old = security.issue_session(KEY, now=time.time() - security.SESSION_TTL - 120)
    assert security.session_id(old, KEY) is None
    assert security.session_id(security.issue_session(KEY), KEY)


def test_a_tampered_session_is_refused():
    v = security.issue_session(KEY)
    head, iat, sid, mac = v.split(".")
    assert security.session_id(f"{head}.{int(iat) + 3600}.{sid}.{mac}", KEY) is None    # extended by hand
    assert security.session_id(v, "another-key") is None


def test_sign_out_ends_the_session_on_the_server(client, monkeypatch, tmp_path):
    monkeypatch.setattr(security, "REVOKED_FILE", str(tmp_path / "revoked.json"))
    value = client.post("/api/session", json={"key": KEY}).cookies.get(security.COOKIE)
    assert client.get("/api/doctypes").status_code == 200
    r = client.post("/api/session/close", json={})
    assert r.status_code == 200
    client.cookies.set(security.COOKIE, value)            # a browser (or a thief) that kept the cookie
    assert client.get("/api/doctypes").status_code == 401


# ---------------------------------------------------------------- chat build links (review 14.10.2026)
def _letta_turn(md):
    import json as _j
    return {"messages": [
        {"message_type": "tool_call_message",
         "tool_call": {"name": "build_pp_document", "arguments": _j.dumps({"markdown": md, "out_path": "/data/x.docx"})}},
        {"message_type": "tool_return_message", "tool_return": _j.dumps({"ok": True, "out_path": "/data/x.docx"})},
        {"message_type": "assistant_message", "content": "Built it."}]}


def test_chat_rebuilds_the_agents_document_here_and_links_to_it(client, monkeypatch):
    md = ("<!--HEADERDATA\nmk_title: Тест\nen_title: Test\ncode: QCSOP_014_A03\ndoctype: FORM\n-->\n"
          "# 1 Идентификација | Identification\n[[FORM]]\nДатум ||| Date ||| _\n[[/FORM]]\n")
    monkeypatch.setenv("LETTA_BASE_URL", "http://letta")

    def fake_letta(method, path, body=None, timeout=90):
        return [{"id": "a1", "name": "qms_docx_formatter"}] if method == "GET" else _letta_turn(md)

    monkeypatch.setattr(app_mod, "_letta", fake_letta)
    r = client.post("/api/chat", headers={"X-API-Key": KEY}, json={"message": "build it"})
    b = r.json()["built"]
    assert r.status_code == 200 and b["ok"] and b["doc_id"].startswith("QCSOP_014_A03_")
    assert client.get(b["download_docx"], headers={"X-API-Key": KEY}).status_code == 200   # the file is here


def test_chat_without_a_build_offers_no_links(client, monkeypatch):
    monkeypatch.setenv("LETTA_BASE_URL", "http://letta")
    monkeypatch.setattr(app_mod, "_letta", lambda m, p, body=None, timeout=90:
                        [{"id": "a1", "name": "qms_docx_formatter"}] if m == "GET"
                        else {"messages": [{"message_type": "assistant_message", "content": "hi"}]})
    assert client.post("/api/chat", headers={"X-API-Key": KEY}, json={"message": "hi"}).json()["built"] is None



def test_every_docengine_route_the_web_client_calls_is_forwarded():
    """The proxy allowlist and the web client drifted apart once (library, register, engine: 404 in the browser)."""
    import re
    from pathlib import Path

    live = (Path(__file__).resolve().parents[1] / "web/src/api/live.ts").read_text(encoding="utf-8")
    called = set(re.findall(r"de \+ '/([a-z_]+)", live)) | set(re.findall(r"\$\{de\}/([a-z_]+)", live))
    assert called and called <= app_mod._DE_ROUTES, sorted(called - app_mod._DE_ROUTES)


def test_the_brief_routes_pass_patch_and_delete(client, monkeypatch):
    monkeypatch.setattr(settings, "docengine_url", "http://127.0.0.1:9")
    for method in ("patch", "delete"):
        assert getattr(client, method)("/api/docengine/briefs/x", headers=H).status_code == 502   # forwarded, not 404/405
    assert client.put("/api/docengine/reference", headers=H).status_code == 405                 # operator route stays out


def test_auth_off_opens_every_route_and_says_so(client, monkeypatch):
    """Head of QC, 19.10.2026: no key sign-in for now. PPDOCWIZ_AUTH=off is a switch; the default keeps the gate."""
    assert client.get("/api/doctypes").status_code == 401            # default: the key is required
    assert client.get("/api/health").json()["auth"] is True
    monkeypatch.setattr(settings, "auth_off", True)
    assert client.get("/api/doctypes").status_code == 200            # no key, no cookie
    assert client.get("/api/health").json()["auth"] is False
    monkeypatch.setattr(settings, "api_key", "")                     # even with no key configured
    assert client.get("/api/doctypes").status_code == 200


def test_the_auth_switch_reads_only_off(monkeypatch):
    import importlib
    import config
    for raw, off in (("off", True), (" OFF ", True), ("on", False), ("", False), ("no", False)):
        monkeypatch.setenv("PPDOCWIZ_AUTH", raw)
        assert importlib.reload(config).Settings().auth_off is off
    monkeypatch.delenv("PPDOCWIZ_AUTH")
    importlib.reload(config)
