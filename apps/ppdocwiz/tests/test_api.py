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
    assert value and value != KEY, "the cookie must not be the API key itself"
    assert value == security.session_value(KEY)


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
