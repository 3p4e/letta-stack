# -*- coding: utf-8 -*-
"""pp_render.py — DOCX → PDF the same way on every machine (Head of QC, 09.10.2026).

Rendering used to depend on what the device had: Word on the laptop, LibreOffice in a
container, nothing on the phone. One function now renders through the shared Gotenberg
service on KVM4 when it is configured, and falls back to a local LibreOffice only when it is
not reachable. Both routes update fields and indexes first, so an SOP's table of contents
is filled (a plain `soffice --convert-to pdf` leaves it empty).

    python3 pp_render.py in.docx out.pdf          # prints the route used
    import pp_render; pp_render.render_pdf("in.docx", "out.pdf")

Environment:
    GOTENBERG_URL                 e.g. http://gotenberg:3000 (in-stack) or
                                  https://render.srv1231216.hstgr.cloud (any device)
    GOTENBERG_USERNAME/_PASSWORD  basic auth, when the service is exposed publicly
    PP_RENDER                     auto (default) | gotenberg | local
No third-party packages: standard library only.
"""
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LO_PROFILE = os.path.join(HERE, "..", "assets", "lo_profile")
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class RenderError(RuntimeError):
    pass


def _multipart(fields, files):
    boundary = "pp" + uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out += [f"--{boundary}", f'Content-Disposition: form-data; name="{k}"', "", str(v)]
    body = "\r\n".join(out).encode() + (b"\r\n" if out else b"")
    for name, (fname, data, mime) in files.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{fname}\"\r\n"
                 f"Content-Type: {mime}\r\n\r\n").encode() + data + b"\r\n"
    return body + f"--{boundary}--\r\n".encode(), f"multipart/form-data; boundary={boundary}"


def render_gotenberg(docx, pdf, url=None, timeout=180):
    url = (url or os.environ.get("GOTENBERG_URL", "")).rstrip("/")
    if not url:
        raise RenderError("GOTENBERG_URL is not set")
    with open(docx, "rb") as f:
        data = f.read()
    # updateIndexes: refresh the TOC and other indexes before export (Gotenberg 8, LibreOffice route)
    body, ctype = _multipart({"updateIndexes": "true"}, {"files": (os.path.basename(docx), data, DOCX_MIME)})
    req = urllib.request.Request(url + "/forms/libreoffice/convert", data=body, method="POST",
                                 headers={"Content-Type": ctype, "User-Agent": "pp-render/1.0"})
    user, pw = os.environ.get("GOTENBERG_USERNAME", ""), os.environ.get("GOTENBERG_PASSWORD", "")
    if user:
        req.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = r.read()
    except urllib.error.HTTPError as e:
        raise RenderError(f"Gotenberg HTTP {e.code}: {e.read()[:200]!r}") from e
    except (urllib.error.URLError, OSError) as e:
        raise RenderError(f"Gotenberg unreachable: {e}") from e
    if not out.startswith(b"%PDF"):
        raise RenderError("Gotenberg returned something that is not a PDF")
    _write_atomic(pdf, out)
    return "gotenberg"


def render_local(docx, pdf, timeout=300):
    """LibreOffice with a throw-away copy of the bundled macro profile (fields and indexes refreshed)."""
    if not shutil.which("soffice"):
        raise RenderError("no local LibreOffice (soffice) on this machine")
    docx = os.path.abspath(docx)
    with tempfile.TemporaryDirectory(prefix="pp-render-") as tmp:
        part = os.path.join(tmp, "out.pdf")
        if os.path.isdir(LO_PROFILE):
            prof = os.path.join(tmp, "profile")
            shutil.copytree(LO_PROFILE, prof)
            subprocess.run(["soffice", "-env:UserInstallation=file://" + prof, "--headless",
                            f'macro:///Standard.Module1.ToPdf("{docx}","{part}")'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        if not os.path.exists(part):
            raise RenderError("local LibreOffice did not produce a PDF")
        with open(part, "rb") as f:
            _write_atomic(pdf, f.read())
    return "local"


def render_pdf(docx, pdf, mode=None):
    """Render and return the route used ('gotenberg' or 'local'). auto: Gotenberg if
    configured, local LibreOffice if Gotenberg is unset or unreachable."""
    mode = (mode or os.environ.get("PP_RENDER", "auto")).lower()
    if mode == "gotenberg":
        return render_gotenberg(docx, pdf)
    if mode == "local":
        return render_local(docx, pdf)
    errors = []
    if os.environ.get("GOTENBERG_URL"):
        try:
            return render_gotenberg(docx, pdf)
        except RenderError as e:
            errors.append(str(e))
    try:
        return render_local(docx, pdf)
    except RenderError as e:
        errors.append(str(e))
    raise RenderError("no renderer: " + "; ".join(errors))


def _write_atomic(path, data):
    staged = f"{path}.{uuid.uuid4().hex[:8]}.part"
    with open(staged, "wb") as f:
        f.write(data)
    os.replace(staged, path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: pp_render.py in.docx out.pdf")
    print("rendered via", render_pdf(sys.argv[1], sys.argv[2]))
