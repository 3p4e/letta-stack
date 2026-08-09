# docengine.app.builder — the formatting core, adopted COMPLETELY from
# pp-document-suite per docs/DOCENGINE-CANON-2026-07.md.
#
# In-process wrapper around the vendored canonical engine:
#   bilingual Markdown --build_from_md--> .docx --pp_verify--> PASS | FAIL
#
# HARD GATE: a document that does not print `RESULT: PASS` never leaves this
# module — build() raises instead of returning a path. This mirrors the live
# Letta tool's contract ({ok, verify, path, bytes}) but enforces PASS.
import contextlib
import io
import os
import re
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import ENGINE_SCRIPTS

# The engine scripts import each other as top-level modules (pp_format,
# pp_report, ...), exactly like inside the packaged skill — put the vendored
# scripts dir on sys.path once.
if str(ENGINE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ENGINE_SCRIPTS))

import build_from_md  # noqa: E402  (vendored engine)
import pp_verify      # noqa: E402  (vendored engine)

# python-docx documents are not thread-safe and the engine uses module state
# (template lookup, sys.argv shim in verify) — serialize builds. Throughput is
# not the concern here; correctness of controlled documents is.
_BUILD_LOCK = threading.Lock()

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class VerifyFailed(Exception):
    """The produced .docx failed the pp_verify gate — it must not be shipped."""

    def __init__(self, report: str):
        super().__init__("pp_verify FAILED")
        self.report = report


@dataclass
class BuildResult:
    path: Path
    bytes: int
    verify_report: str
    doctype: str


def safe_name(name: str) -> str:
    """Collapse anything path-hostile out of a user-supplied output name."""
    name = _SAFE_NAME.sub("_", (name or "document").strip()) or "document"
    return name[:120]


def run_verify(docx_path: Path, min_pt: float = 6.0, require_bilingual: bool = True) -> tuple[bool, str]:
    """Run the vendored pp_verify in-process; return (passed, report_text)."""
    buf = io.StringIO()
    argv = sys.argv
    sys.argv = ["pp_verify", str(docx_path), "--min-pt", str(min_pt),
                "--require-bilingual", "true" if require_bilingual else "false"]
    code = 0
    try:
        with contextlib.redirect_stdout(buf):
            try:
                pp_verify.main()
            except SystemExit as e:  # pp_verify exits 0=PASS 1=FAIL
                code = int(e.code or 0)
    finally:
        sys.argv = argv
    report = buf.getvalue().strip()
    # pp_verify opens its report with `== VERIFY: <absolute path>`, and this
    # report is handed straight back to API callers (both in the success
    # response and in VerifyFailed's 422 detail) and stored in the documents
    # table. That published the service's container filesystem layout to every
    # client for no diagnostic benefit — the basename identifies the artifact
    # just as well, and the caller already knows which document it asked for.
    report = report.replace(str(docx_path), Path(docx_path).name)
    return code == 0 and "RESULT: PASS" in report, report


def _strip_headerdata(markdown: str) -> str:
    """Line-anchored HEADERDATA strip (mirrors build_from_md.py's parser
    fix) — a naive non-greedy regex would stop at the first literal '-->'
    inside a field value, undercounting the real source content."""
    lines = markdown.splitlines()
    start = end = None
    for idx, ln in enumerate(lines):
        if ln.strip() == "<!--HEADERDATA":
            start = idx
            break
    if start is not None:
        for idx in range(start + 1, len(lines)):
            if lines[idx].strip() == "-->":
                end = idx
                break
    if start is not None and end is not None:
        return "\n".join(lines[:start] + lines[end + 1 :])
    return markdown


def _source_word_char_counts(markdown: str) -> tuple[int, int]:
    """§5A fidelity source-side count: the ASSEMBLED markdown minus its own
    grammar tokens (HEADERDATA block, [[FORM/TABLE]] markers, heading
    markup, column separators). This pipeline never has a second reference
    .docx to compare against (build() only ever has the source markdown and
    the produced .docx) — the source markdown itself is the ground truth
    for a no-impoverishment check."""
    body = _strip_headerdata(markdown)
    body = re.sub(r"^\[\[/?(?:FORM|TABLE)[^\]]*\]\]\s*$", "", body, flags=re.M)
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.M)
    body = body.replace("|||", " ").replace("~~", " ").replace("|", " ")
    words = len(re.findall(r"\S+", body))
    chars = len(re.sub(r"\s+", "", body))
    return words, chars


def build(markdown: str, out_dir: Path, out_name: str = "document") -> BuildResult:
    """Bilingual Markdown -> controlled .docx, verified. Raises VerifyFailed
    (doc deleted) on a FAIL — a failed document never exists on disk after."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # H13 — the output path used to be safe_name(out_name) + ".docx", derived
    # from the document CODE alone. Two concurrent builds of the same code
    # therefore wrote the same file: they interleaved, and the FAIL path below
    # (out.unlink) could delete the OTHER worker's *passing* document. The
    # in-process _BUILD_LOCK cannot help — the service runs multiple uvicorn
    # workers, i.e. separate processes.
    # Each build now owns a unique path. It is written under a dot-prefixed
    # `.partial` name and only os.replace()d into place once it has PASSED, so
    # a reader can never observe a half-written or unverified document, and the
    # FAIL cleanup can only ever remove this build's own temp file.
    stamp = uuid.uuid4().hex[:12]
    final = out_dir / f"{safe_name(out_name)}-{stamp}.docx"
    out = out_dir / f".{safe_name(out_name)}-{stamp}.partial.docx"
    doctype = "SOP"
    m = re.search(r"^doctype:\s*(\S+)", markdown, re.M)
    if m:
        doctype = m.group(1).upper()
    require_bilingual = True
    mbil = re.search(r"^bilingual:\s*(\S+)", markdown, re.M)
    if mbil and mbil.group(1).strip().lower() in ("no", "false"):
        require_bilingual = False
    with _BUILD_LOCK:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(markdown)
            src = f.name
        try:
            build_from_md.main(src, str(out))
        finally:
            Path(src).unlink(missing_ok=True)
        passed, report = run_verify(out, require_bilingual=require_bilingual)
        # §5A no-impoverishment check: the produced .docx must not contain
        # LESS content than the source markdown it was built from. Always
        # run and always reported, even when already failing on font/
        # bilingual, so a FAIL report names every reason at once.
        src_words, src_chars = _source_word_char_counts(markdown)
        r = pp_verify.analyse(str(out))
        fid_ok = r["words"] >= src_words and r["chars"] >= src_chars
        report += (f"\n   FIDELITY (§5A, markdown-source) output>=source:"
                   f" words {r['words']}>={src_words}, chars {r['chars']}>={src_chars}"
                   f"  [{'OK' if fid_ok else 'FAIL'}]")
        passed = passed and fid_ok
    if not passed:
        out.unlink(missing_ok=True)
        raise VerifyFailed(report)
    # Atomic publish: same filesystem, so os.replace is a rename, and the
    # document appears at its final path complete and already verified.
    os.replace(out, final)
    return BuildResult(
        path=final, bytes=final.stat().st_size, verify_report=report, doctype=doctype
    )
