# docengine.app.engine_env — what GET /engine/environment reports: the state of the engine this
# container really runs, measured, never sampled.
#
#   sync    the engine files in this image hashed against engine/MANIFEST, which
#           engine/sync_from_suite.sh writes from pp-document-suite at commit time;
#   fonts   one probe document per house face rendered by the live renderer, its embedded
#           fonts read back: a face the PDF does not carry, or a fallback face beside it,
#           is a substitution (Head of QC, 10.10.2026: never a substitute font);
#   audit   the pp_verify result of the last documents the registry holds;
#   drift   the persistent fleet agents' memory blocks against agents/fleet.yaml. The
#           pipeline's per-exchange clones are built from fleet.yaml; the chat talks to the
#           persistent agents, so a difference here is a difference in what the chat is told.
#
# Run as a script to write engine/MANIFEST:  python3 app/engine_env.py --write-manifest
import hashlib
import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
MANIFEST = ENGINE / "MANIFEST"
CANON = "2026-10-09"

MK_ALPHABET = ("АБВГДЃЕЖЗЅИЈКЛЉМНЊОПРСТЌУФХЦЧЏШ"
               "абвгдѓежзѕијклљмнњопрстќуфхцчџш")
# The faces the engine sets text in (pp_format / pp_report / pp_theme), each with text it must carry.
PROBE_FACES = (
    ("Calibri", MK_ALPHABET + " 0123456789 № %"),
    ("Arial Narrow", MK_ALPHABET + " 0123456789 №"),
)
# Faces a renderer falls back to; one of them in a probe PDF means a letter was not in the face asked for.
FALLBACK = ("dejavu", "liberation", "freesans", "freeserif", "notosans", "notoserif", "carlito", "opensans")
FONT_TTL = 900.0
_font_cache: dict = {}


def _engine_files() -> list[Path]:
    out = []
    for sub, keep in (("scripts", (".py", ".sh", ".ps1")), ("assets", None), ("references", None)):
        base = ENGINE / sub
        if base.is_dir():
            out += [p for p in base.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts and (keep is None or p.suffix in keep)]
    return sorted(out, key=lambda p: p.relative_to(ENGINE).as_posix())


def engine_hash() -> str:
    """sha256 over every engine file's path and bytes, first 12 hex digits."""
    h = hashlib.sha256()
    for p in _engine_files():
        h.update(p.relative_to(ENGINE).as_posix().encode() + b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def manifest_hash() -> str:
    try:
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if line.startswith("sha256 "):
                return line.split()[1]
    except OSError:
        pass
    return "none"


def _norm(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def probe_docx(face: str, text: str) -> bytes:
    """A one-paragraph .docx whose every run asks for `face`."""
    from docx import Document
    from docx.oxml.ns import qn
    d = Document()
    for bold in (False, True):
        r = d.add_paragraph().add_run(text)
        r.bold = bold
        r.font.name = face
        rf = r._element.get_or_add_rPr().get_or_add_rFonts()
        for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(k), face)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def classify(face: str, embedded: set[str]) -> dict:
    """One row of the font table from the fonts a probe PDF embeds."""
    want = _norm(face)
    own = sorted(e for e in embedded if _norm(e).startswith(want))
    others = sorted(e for e in embedded if not _norm(e).startswith(want))
    fallback = [e for e in others if _norm(e).startswith(FALLBACK)]
    if not own:
        return {"face": face, "file": "not embedded", "ok": False,
                "missing": "substituted by " + (", ".join(others) or "nothing")}
    if fallback:
        return {"face": face, "file": ", ".join(own), "ok": False,
                "missing": "some letters fell back to " + ", ".join(fallback)}
    return {"face": face, "file": ", ".join(own), "ok": True, "missing": ""}


async def font_rows(render, now: float | None = None) -> list[dict]:
    """Render one probe per house face through `render(docx_bytes) -> pdf_bytes` (cached FONT_TTL s)."""
    import asyncio

    import pp_assets  # vendored engine (on sys.path via builder)
    now = time.monotonic() if now is None else now
    if _font_cache.get("at") and now - _font_cache["at"] < FONT_TTL:
        return _font_cache["rows"]
    rows = []
    for face, text in PROBE_FACES:
        try:
            pdf = await render(await asyncio.to_thread(probe_docx, face, text))
            rows.append(classify(face, set(pp_assets.pdf_fonts(pdf))))
        except Exception as e:  # noqa: BLE001 — a failed probe is reported, never hidden
            rows.append({"face": face, "file": "probe failed", "ok": False, "missing": str(e)[:200]})
    if all(r["file"] != "probe failed" for r in rows):
        _font_cache.update(at=now, rows=rows)
    return rows


def audit_rows(docs: list[dict]) -> list[dict]:
    """The registry's newest documents with the first line of their pp_verify report."""
    out = []
    for d in docs:
        report = (d.get("verify") or "").strip()
        verdict = next((ln for ln in report.splitlines() if ln.startswith("RESULT:")), "")
        ok = verdict.strip() == "RESULT: PASS"
        stamp = str(d.get("created_at", ""))[:16].replace("T", " ")
        out.append({"run": f"{stamp} {d.get('code', '')}".strip(), "ok": ok,
                    "note": verdict or "no pp_verify result recorded"})
    return out


def drift_rows(spec: dict, glossary_text: str, live_agents: list[dict]) -> list[dict]:
    """fleet.yaml against the persistent agents: one row per agent and memory block that differs."""
    def blocks(a: dict) -> dict:
        mem = a.get("memory") or {}
        return {b.get("label"): (b.get("value") or "") for b in (mem.get("blocks") or a.get("blocks") or [])}

    def size(v) -> str:
        return "absent" if v is None else f"{len(v.strip())} chars"

    live = {a.get("name"): a for a in live_agents}
    rows, same, checked = [], 0, 0
    for ag in spec.get("agents", []):
        name = ag["name"]
        if name not in live:
            rows.append({"key": name, "manifest": "declared", "live": "missing"})
            continue
        have = blocks(live[name])
        want = {"gf_house_rules": spec.get("house_rules", ""), "persona": ag.get("persona", ""),
                "gf_glossary_mk": glossary_text}
        for label, v in want.items():
            checked += 1
            got = have.get(label)
            if got is not None and got.strip() == v.strip():
                same += 1
                continue
            rows.append({"key": f"{name} · {label}", "manifest": size(v), "live": size(got)})
    rows.append({"key": "memory blocks identical to fleet.yaml", "manifest": str(checked), "live": str(same)})
    return rows


if __name__ == "__main__":
    if sys.argv[1:] == ["--write-manifest"]:
        MANIFEST.write_text(
            "# Written by engine/sync_from_suite.sh: hash of scripts/, assets/ and references/.\n"
            "# GET /engine/environment compares the image's engine with this line.\n"
            f"sha256 {engine_hash()}\n", encoding="utf-8")
        print("engine manifest", manifest_hash())
    else:
        print(engine_hash())
