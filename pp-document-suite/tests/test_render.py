"""pp_render: the Gotenberg request (updateIndexes, basic auth), the fallback to local
LibreOffice, and a clear error when neither renderer is available."""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import pp_render  # noqa: E402


class _Stub(BaseHTTPRequestHandler):
    seen = {}
    reply = b"%PDF-1.7 stub"

    def do_POST(self):
        n = int(self.headers["Content-Length"])
        _Stub.seen = {"path": self.path, "auth": self.headers.get("Authorization"),
                      "ctype": self.headers["Content-Type"], "body": self.rfile.read(n)}
        self.send_response(200); self.send_header("Content-Type", "application/pdf"); self.end_headers()
        self.wfile.write(_Stub.reply)

    def log_message(self, *a):
        pass


@pytest.fixture
def gotenberg(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), _Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("GOTENBERG_URL", f"http://127.0.0.1:{srv.server_port}")
    yield _Stub
    srv.shutdown()


@pytest.fixture
def docx(tmp_path):
    p = tmp_path / "in.docx"; p.write_bytes(b"PK\x03\x04 fake docx"); return str(p)


def test_gotenberg_request(gotenberg, docx, tmp_path, monkeypatch):
    monkeypatch.setenv("GOTENBERG_USERNAME", "pp"); monkeypatch.setenv("GOTENBERG_PASSWORD", "s")
    out = tmp_path / "out.pdf"
    assert pp_render.render_pdf(docx, str(out)) == "gotenberg"
    s = gotenberg.seen
    assert s["path"] == "/forms/libreoffice/convert" and s["ctype"].startswith("multipart/form-data")
    assert b'name="updateIndexes"\r\n\r\ntrue' in s["body"] and b'filename="in.docx"' in s["body"]
    assert s["auth"] == "Basic cHA6cw=="          # pp:s
    assert out.read_bytes() == b"%PDF-1.7 stub"


def test_non_pdf_reply_is_an_error(gotenberg, docx, tmp_path, monkeypatch):
    monkeypatch.setattr(_Stub, "reply", b"<html>error</html>")
    with pytest.raises(pp_render.RenderError):
        pp_render.render_gotenberg(docx, str(tmp_path / "o.pdf"))


def test_auto_falls_back_to_local_when_gotenberg_unreachable(docx, tmp_path, monkeypatch):
    monkeypatch.setenv("GOTENBERG_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(pp_render, "render_local", lambda d, p: "local")
    assert pp_render.render_pdf(docx, str(tmp_path / "o.pdf")) == "local"


def test_no_renderer_names_both_reasons(docx, tmp_path, monkeypatch):
    monkeypatch.delenv("GOTENBERG_URL", raising=False)
    monkeypatch.setattr(pp_render.shutil, "which", lambda name: None)
    with pytest.raises(pp_render.RenderError, match="no local LibreOffice"):
        pp_render.render_pdf(docx, str(tmp_path / "o.pdf"))
