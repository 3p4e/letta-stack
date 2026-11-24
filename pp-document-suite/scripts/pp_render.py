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
    RUNNER_URL/RUNNER_TOKEN       the kvm4-runner (POST /shell, /file/write, /file/read): reaches the same
                                  Gotenberg container from inside KVM4 when the public route is closed to this
                                  device (no basic-auth password, proxy). PP_RENDER_CONTAINER, default gotenberg.
    PP_RENDER                     auto (default) | gotenberg | runner | local
Auto order: Gotenberg (GOTENBERG_URL) -> runner -> local LibreOffice. The local route is last because a machine
without the licensed house fonts renders with substitutes, which _check_fonts refuses.
No third-party packages: standard library only.
"""
import base64
import contextlib
import os
import signal
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


class RenderTimeout(RenderError):
    """The renderer did not finish in time. A RenderError, so auto mode and callers handle it like any other."""


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


def _runner_call(path, body, timeout):
    import json
    url, tok = os.environ.get("RUNNER_URL", "").rstrip("/"), os.environ.get("RUNNER_TOKEN", "")
    req = urllib.request.Request(url + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RenderError(f"runner HTTP {e.code}: {e.read()[:200]!r}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise RenderError(f"runner unreachable: {e}") from e


def render_runner(docx, pdf, timeout=240):
    """Render on KVM4's Gotenberg container through the kvm4-runner (Open Brain, 09.10.2026: RUNNER_URL/RUNNER_TOKEN;
    KVM4_RUNNER_TOKEN is stale). The DOCX is copied into the container and converted by its own curl on localhost:3000,
    so no Gotenberg password is needed and the licensed fonts are the container's."""
    if not (os.environ.get("RUNNER_URL") and os.environ.get("RUNNER_TOKEN")):
        raise RenderError("RUNNER_URL/RUNNER_TOKEN are not set")
    box = os.environ.get("PP_RENDER_CONTAINER", "gotenberg")
    k = uuid.uuid4().hex[:12]
    host = f"/tmp/pprender_{k}"
    with open(docx, "rb") as f:
        data = f.read()
    try:
        _runner_call("/shell", {"cmd": f"mkdir -p {host}"}, 60)
        _runner_call("/file/write", {"path": f"{host}/in.docx", "content_b64": base64.b64encode(data).decode(),
                                     "mode": 0o644}, 120)
        cmd = (f"docker cp {host}/in.docx {box}:/tmp/{k}.docx && "
               f"docker exec {box} curl -sf --max-time {timeout - 20} -F updateIndexes=true "
               f"-F files=@/tmp/{k}.docx http://localhost:3000/forms/libreoffice/convert -o /tmp/{k}.pdf && "
               f"docker cp {box}:/tmp/{k}.pdf {host}/out.pdf")
        r = _runner_call("/shell", {"cmd": cmd, "timeout": timeout}, timeout + 30)
        if r.get("exit_code") not in (0, None):
            raise RenderError("runner render failed: " + str(r.get("output", ""))[-300:])
        out = base64.b64decode(_runner_call("/file/read", {"path": f"{host}/out.pdf", "max_bytes": 60_000_000},
                                            120)["content_b64"])
    finally:
        with contextlib.suppress(RenderError):
            _runner_call("/shell", {"cmd": f"docker exec -u root {box} rm -f /tmp/{k}.docx /tmp/{k}.pdf; "
                                           f"rm -rf {host}"}, 60)
    if not out.startswith(b"%PDF"):
        raise RenderError("runner returned something that is not a PDF")
    _write_atomic(pdf, out)
    return "runner"


def render_local(docx, pdf, timeout=300):
    """LibreOffice with a throw-away copy of the bundled macro profile (fields and indexes refreshed)."""
    if not shutil.which("soffice"):
        raise RenderError("no local LibreOffice (soffice) on this machine")
    docx = os.path.abspath(docx)
    with tempfile.TemporaryDirectory(prefix="pp-render-") as tmp:
        part = os.path.join(tmp, "out.pdf")
        if '"' in docx:
            # The paths are spliced into a Basic macro call as "..." literals; a quote in the name ended the
            # literal early and the macro failed or wrote elsewhere (review 19.10.2026). Work from a safe copy.
            safe = os.path.join(tmp, "in.docx"); shutil.copyfile(docx, safe); docx = safe
        if '"' in tmp:
            raise RenderError(f"temporary directory {tmp!r} contains a double quote; set TMPDIR to a plain path")
        if os.path.isdir(LO_PROFILE):
            prof = os.path.join(tmp, "profile")
            shutil.copytree(LO_PROFILE, prof)
            # Own process group: /usr/bin/soffice is a wrapper, and a timeout used to kill only the wrapper,
            # leaving soffice.bin running on a profile this function had already deleted. And the timeout
            # escaped as subprocess.TimeoutExpired, outside the RenderError contract (review 14.10.2026).
            proc = subprocess.Popen(["soffice", "-env:UserInstallation=file://" + prof, "--headless",
                                     f'macro:///Standard.Module1.ToPdf("{docx}","{part}")'],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise RenderTimeout(f"local LibreOffice did not finish within {timeout} s") from None
        if not os.path.exists(part):
            raise RenderError("local LibreOffice did not produce a PDF")
        with open(part, "rb") as f:
            _write_atomic(pdf, f.read())
    return "local"


def _check_fonts(docx, pdf):
    """Refuse a PDF printed with substitute fonts (Head of QC, 10.10.2026: never accept a substitute)."""
    try:
        sys.path.insert(0, HERE)
        import pp_assets
    except ImportError:          # the suite's own module; absent only in a broken checkout
        raise RenderError("font check unavailable: pp_assets not importable")
    if not os.path.exists(pdf):
        raise RenderError("the renderer produced no PDF")
    subs = pp_assets.font_substitutions(docx, pdf)
    if subs:
        with contextlib.suppress(OSError):
            os.unlink(pdf)
        raise RenderError("rendered with substitute fonts — install them on the renderer, never accept a "
                          "substitute: " + "; ".join(subs))


def render_pdf(docx, pdf, mode=None):
    """Render and return the route used ('gotenberg', 'runner' or 'local'). auto: Gotenberg if
    configured, then the kvm4-runner, then local LibreOffice."""
    route = _render(docx, pdf, mode)
    _check_fonts(docx, pdf)      # every route: a PDF with substitute fonts is never handed out
    return route


def _render(docx, pdf, mode=None):
    mode = (mode or os.environ.get("PP_RENDER", "auto")).lower()
    if mode == "gotenberg":
        return render_gotenberg(docx, pdf)
    if mode == "runner":
        return render_runner(docx, pdf)
    if mode == "local":
        return render_local(docx, pdf)
    errors = []
    if os.environ.get("GOTENBERG_URL"):
        try:
            return render_gotenberg(docx, pdf)
        except RenderError as e:
            errors.append(str(e))
    if os.environ.get("RUNNER_URL") and os.environ.get("RUNNER_TOKEN"):
        try:
            return render_runner(docx, pdf)
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
