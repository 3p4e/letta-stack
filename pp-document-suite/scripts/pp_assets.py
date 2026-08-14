# -*- coding: utf-8 -*-
"""
Purely Plant — ASSET REGISTRY and GLYPH GUARD (part of pp-document-suite).

Two jobs:

1. **Registry.** One place that knows where the house assets live — the wordmark
   images, the verified font files, the palette (from pp_theme) — so a builder
   never hard-codes a path or hunts for a logo again. `logo()`, `font_file()`,
   `chart_style()`.

2. **Glyph guard.** The engine's documents are Macedonian-first. A font that
   lacks Cyrillic renders MK text as tofu boxes or, worse, silently falls back
   per-character and scrambles the line. This module can *prove* a font covers
   the text before the document ships:

       pp_assets.missing_glyphs("Calibri", "Спецификација")  -> "" if clean

   `pp_verify.py` calls `audit_docx()` on every build, so a font/script mismatch
   fails the pre-delivery gate instead of reaching the reader.

**Why this exists.** A build once shipped with Cyrillic scrambled in the PDF.
The cause was not the document: `~/.fonts` held *subset* Carlito webfonts (106
glyphs, no Cyrillic) that outranked the full system Carlito (2 117 glyphs) in
fontconfig, so every Calibri run resolved to a font missing the alphabet it
needed. `check_environment()` detects exactly that condition.
"""
import os
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
FONT_DIR = os.path.join(ASSETS, "fonts")
BRAND_DIR = os.path.join(ASSETS, "brand")
TEMPLATE = os.path.join(ASSETS, "PP_BASE_TEMPLATE.docx")

# Macedonian alphabet — the coverage a body font MUST have to be usable here.
MK_ALPHABET = ("АБВГДЃЕЖЗЅИЈКЛЉМНЊОПРСТЌУФХЦЧЏШ"
               "абвгдѓежзѕијклљмнњопрстќуфхцчџш")

# Registered faces. `file` is the bundled copy; `aliases` are the names that
# appear in .docx runs and resolve to this face at render time.
FACES = {
    "Carlito":     {"file": "Carlito-Regular.ttf",    "aliases": ("Calibri",), "scripts": ("latin", "cyrillic")},
    "Montserrat":  {"file": "Montserrat-Regular.otf", "aliases": (),           "scripts": ("latin", "cyrillic")},
}

# Faces that are display-only and known NOT to carry Cyrillic. Never assign
# these to Macedonian text — the ImB specification family uses them for Latin
# cultivar names only.
LATIN_ONLY_DISPLAY = ("Orbitron", "Roboto Mono")


def logo(variant="header"):
    """Path to the Purely Plant wordmark. variant='header' (compact, jpg) or 'full' (png)."""
    name = {"header": "pp_logo_header.jpg", "full": "pp_logo_full.png"}[variant]
    p = os.path.join(BRAND_DIR, name)
    if not os.path.exists(p):
        raise FileNotFoundError("brand asset missing: %s" % p)
    return p


def font_file(face):
    """Path to a bundled font file for a registered face, or None."""
    f = FACES.get(face)
    if not f:
        return None
    p = os.path.join(FONT_DIR, f["file"])
    return p if os.path.exists(p) else None


def chart_style():
    """matplotlib rcParams that match the document house style (pairs with pp_charts)."""
    import pp_theme as th
    return {
        "font.family": "sans-serif",
        "font.sans-serif": ["Carlito", "Montserrat", "DejaVu Sans"],
        "axes.edgecolor": th.MPL_GREY,
        "axes.labelcolor": th.MPL_NAVY,
        "text.color": "#16232B",
        "xtick.color": th.MPL_GREY,
        "ytick.color": th.MPL_GREY,
        "axes.grid": True,
        "grid.color": "#E3E9F0",
        "grid.linewidth": 0.6,
        "figure.facecolor": "white",
        "savefig.dpi": 200,
    }


# ---------------------------------------------------------------- glyph guard

def _resolve(face):
    """Resolve a run's font name to an actual file the renderer will use.
       Prefers the bundled copy; else asks fontconfig; else scans the font dirs."""
    for name, f in FACES.items():
        if face == name or face in f["aliases"]:
            p = font_file(name)
            if p:
                return p
    try:
        import subprocess
        out = subprocess.run(["fc-match", "-f", "%{file}", face],
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    for pat in ("/usr/share/fonts/**/*.ttf", "/usr/share/fonts/**/*.otf"):
        hits = [p for p in glob.glob(pat, recursive=True)
                if face.replace(" ", "").lower() in os.path.basename(p).replace(" ", "").lower()]
        if hits:
            return hits[0]
    return None


def _cmap(path, _cache={}):
    if path not in _cache:
        try:
            from fontTools.ttLib import TTFont
            _cache[path] = set(TTFont(path, lazy=True, fontNumber=0).getBestCmap())
        except Exception:
            _cache[path] = None
    return _cache[path]


def missing_glyphs(face, text):
    """Characters of `text` the resolved `face` cannot render. '' means clean.
       Whitespace and control characters are ignored (never glyph-mapped)."""
    path = _resolve(face)
    if not path:
        return ""            # cannot resolve — report nothing rather than false-alarm
    cm = _cmap(path)
    if cm is None:
        return ""
    miss = []
    for ch in text:
        if ch.isspace() or ord(ch) < 0x20:
            continue
        if ord(ch) not in cm and ch not in miss:
            miss.append(ch)
    return "".join(miss)


def check_environment():
    """Detect the subset-webfont trap: a font directory shadowing a full system
       face with a cut-down copy. Returns a list of human-readable problems."""
    problems = []
    for face in ("Calibri", "Carlito"):
        p = _resolve(face)
        if not p:
            problems.append("%s: no font file resolves" % face)
            continue
        miss = missing_glyphs(face, MK_ALPHABET)
        if miss:
            problems.append("%s resolves to %s, which is missing Macedonian letters: %s"
                            % (face, os.path.basename(p), miss))
    for d in (os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts")):
        for p in glob.glob(os.path.join(d, "*.ttf")) + glob.glob(os.path.join(d, "*.otf")):
            cm = _cmap(p)
            if cm is not None and len(cm) < 300:
                problems.append("subset font in user font dir may shadow a full face: %s (%d glyphs)"
                                % (p, len(cm)))
    return problems


def audit_docx(path):
    """Every run in a .docx checked against the font it declares.
       Returns a list of (font, offending characters, sample text)."""
    import re
    import zipfile
    bad = {}
    with zipfile.ZipFile(path) as z:
        parts = [n for n in z.namelist()
                 if n.startswith("word/") and n.endswith(".xml")
                 and ("document" in n or "header" in n or "footer" in n)]
        for n in parts:
            xml = z.read(n).decode("utf-8", "replace")
            for run in re.findall(r"<w:r[ >].*?</w:r>", xml, re.S):
                m = re.search(r'w:ascii="([^"]+)"', run)
                face = m.group(1) if m else "Calibri"
                text = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", run, re.S))
                if not text.strip():
                    continue
                miss = missing_glyphs(face, text)
                if miss:
                    key = (face, miss)
                    bad.setdefault(key, text[:60])
    return [(f, m, s) for (f, m), s in bad.items()]


if __name__ == "__main__":
    import sys
    probs = check_environment()
    print("ENVIRONMENT:", "OK" if not probs else "PROBLEMS")
    for p in probs:
        print("  !", p)
    for path in sys.argv[1:]:
        bad = audit_docx(path)
        print("%s: %s" % (os.path.basename(path), "glyph coverage OK" if not bad else "MISSING GLYPHS"))
        for face, miss, sample in bad:
            print("  ! %s cannot render %r  e.g. %r" % (face, miss, sample))
    sys.exit(1 if probs else 0)
