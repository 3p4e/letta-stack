#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the standing rules of this repository.

These are not style preferences. Each check corresponds to a decision that was
made deliberately and that a future edit could silently undo:

  1. Classical OCR is never used. The certificates are Macedonian Cyrillic mixed
     with Latin chemical symbols — the case Tesseract handles worst. Reading is
     done by the vision chain in AGENT_MODEL_POLICY.md.
  2. Letta is not a RAG engine. No code in this repository may create a Letta
     source; retrieval belongs to RAGFlow.
  3. No credential is ever committed. Keys come from the environment.
  4. Every Python file parses.
  5. The batch gap analysis stays internally consistent — the CSV must not drift
     from the counts the README states, and no batch is counted twice under two
     spellings of the same code.

Run locally exactly as CI runs it:

    python3 scripts/policy_check.py
"""
import ast, csv, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The batch-identity rule has exactly one definition. A second copy here would
# drift from it, and the drift would be invisible: both would pass their own
# tests while keying the same certificate to two different batches.
sys.path.insert(0, os.path.join(ROOT, "ingestion", "common"))
from batch_id import batch_key                                    # noqa: E402

FAIL = []
WARN = []


def rel(p):
    return os.path.relpath(p, ROOT)


def _tracked():
    """Paths git actually tracks. A credential in a gitignored file is a local
    convenience; a credential in a tracked file is an incident. Only the latter
    is this checker's business."""
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"],
                             capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            return {os.path.join(ROOT, p) for p in out.stdout.split("\0") if p}
    except (OSError, subprocess.SubprocessError):
        pass
    return None                                   # not a checkout — scan everything


TRACKED = _tracked()


def walk(exts=None, skip_dirs=(".git", "__pycache__", "node_modules", ".venv")):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if exts and not fn.endswith(exts):
                continue
            full = os.path.join(dirpath, fn)
            if TRACKED is not None and full not in TRACKED:
                continue
            yield full


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, UnicodeError):
        return ""


# ── 1. classical OCR must never be invoked ───────────────────────────────
# Prose that explains *why* Tesseract is not used is fine and expected; an
# actual call is not. Match invocation, not mention.
OCR_CALL = re.compile(
    r"import\s+pytesseract|from\s+pytesseract\b|pytesseract\s*\.|"
    r"['\"]tesseract['\"]|['\"]ocrmypdf['\"]|"
    r"import\s+ocrmypdf|from\s+ocrmypdf\b|"
    r"(?:subprocess|os\.system|check_output|run)\s*\([^)]*\b(?:tesseract|ocrmypdf)\b",
    re.I)


SELF = os.path.abspath(__file__)


def check_no_classical_ocr():
    for p in walk((".py", ".sh", ".yml", ".yaml", ".toml")):
        if os.path.abspath(p) == SELF:
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if OCR_CALL.search(line):
                FAIL.append(f"{rel(p)}:{i}: classical OCR invoked — the policy "
                            f"chain is kimi-k2.6 -> moonshot-v1-128k-vision-preview "
                            f"-> gpt-4o\n      {line.strip()[:100]}")


# ── 2. no code may create a Letta source ─────────────────────────────────
SOURCE_CREATE = re.compile(
    r"letta_source_manager[\s\S]{0,200}?['\"]operation['\"]\s*:\s*['\"]create['\"]|"
    r"['\"]operation['\"]\s*:\s*['\"]create['\"][\s\S]{0,200}?letta_source_manager|"
    r"\.sources\.create\(|/v1/sources/?['\"]\s*,\s*(?:data|json)|"
    r"POST\s+/v1/sources|-X\s*['\"]?POST['\"]?[^\n]*/v1/sources")


def check_no_letta_sources():
    # Shell as well as Python: the two deploy.sh bundles retired on 29.08.2026
    # created their sources with `curl -X POST .../v1/sources/`, so scanning
    # only .py left the way this repository actually did it uncovered.
    for p in walk((".py", ".sh")):
        if os.path.abspath(p) == SELF:
            continue                      # the pattern's own definition, as in check 1
        txt = read(p)
        hit = SOURCE_CREATE.search(txt)
        if hit:
            line = txt.count("\n", 0, hit.start()) + 1
            FAIL.append(f"{rel(p)}:{line}: creates a Letta source — Letta is "
                        f"excluded as a RAG engine; retrieval belongs to RAGFlow")


# ── 3. no committed credentials ──────────────────────────────────────────
SECRET = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|ragflow-[A-Za-z0-9_-]{20,}|pa-[A-Za-z0-9_-]{30,}|"
    r"ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xi-api-key\s*[:=]\s*['\"][^'\"]{16,}")
SECRET_OK = re.compile(r"sk-\.\.\.|sk-xxx|<set|example|placeholder|YOUR_|\bsk-kimi-\.\.\.", re.I)


def check_no_secrets():
    for p in walk():
        if rel(p).startswith(("deliverables/video/film", "deliverables/qc_gap_analysis/PP_")):
            continue                                  # binary deliverables
        for i, line in enumerate(read(p).splitlines(), 1):
            m = SECRET.search(line)
            if m and not SECRET_OK.search(line):
                FAIL.append(f"{rel(p)}:{i}: looks like a committed credential "
                            f"({m.group(0)[:12]}…) — read it from the environment")


# ── 4. every Python file parses ──────────────────────────────────────────
def check_python_parses():
    for p in walk((".py",)):
        src = read(p)
        if not src.strip():
            continue
        try:
            ast.parse(src, filename=rel(p))
        except SyntaxError as e:
            FAIL.append(f"{rel(p)}:{e.lineno}: does not parse — {e.msg}")


# ── 5. the gap analysis must stay self-consistent ────────────────────────
def check_gap_analysis():
    csv_p = os.path.join(ROOT, "deliverables/qc_gap_analysis/batch_gap_analysis.csv")
    md_p = os.path.join(ROOT, "deliverables/qc_gap_analysis/README.md")
    if not (os.path.exists(csv_p) and os.path.exists(md_p)):
        return
    rows = list(csv.DictReader(open(csv_p, encoding="utf-8")))
    md = read(md_p)

    def stated(label):
        m = re.search(re.escape(label) + r"[^|]*\|\s*\*\*(\d+)\*\*", md)
        return int(m.group(1)) if m else None

    checks = [
        ("Production batches on file", len(rows)),
        ("Certificates of Quality to issue (one per batch)",
         sum(1 for r in rows if r["needs_CoQ"] == "Y")),
        ("CoQ **reissues**", sum(1 for r in rows if r["needs_CoQ_reissue"] == "Y")),
        ("Batches needing the **full** internal CoA panel",
         sum(1 for r in rows if r["iCoA_scope"].startswith("full"))),
        ("Batches needing **Identification C only**",
         sum(1 for r in rows if r["iCoA_scope"] == "IdentC only")),
    ]
    for label, actual in checks:
        want = stated(label)
        if want is None:
            WARN.append(f"README: no stated figure found for “{label}”")
        elif want != actual:
            FAIL.append(f"gap analysis drift: README says {want} for “{label}”, "
                        f"CSV holds {actual}")
    # Batch identity is separator-blind: the owner's rule is that GG1024/01 and
    # GG1024_01 name the same batch. The register writes both forms, so a canonical
    # key is carried in the CSV and two rows must never collapse onto one — that
    # would be the same batch counted twice in every downstream figure.
    seen = {}
    for r in rows:
        want = batch_key(r["batch"])
        if r.get("batch_key") != want:
            FAIL.append(f"gap analysis: {r['batch']} keys to {want}, "
                        f"CSV says {r.get('batch_key')!r}")
        if want in seen:
            FAIL.append(f"gap analysis: {r['batch']} and {seen[want]} are the same "
                        f"batch ({want}) written two ways — counted twice")
        seen[want] = r["batch"]

    # every batch needs exactly one CoQ, and the two iCoA scopes must partition
    if any(r["needs_CoQ"] != "Y" for r in rows):
        FAIL.append("gap analysis: a batch is not flagged needs_CoQ=Y")
    scopes = {r["iCoA_scope"] for r in rows}
    unknown = scopes - {"IdentC only"} - {s for s in scopes if s.startswith("full")}
    if unknown:
        FAIL.append(f"gap analysis: unrecognised iCoA_scope {sorted(unknown)}")


# ── 6. no compose we author publishes on 0.0.0.0 ─────────────────────────
# Traefik is the sole public ingress on KVM4; a raw published port is either
# absent or pinned to loopback (server/RAGFLOW_MCP_ENABLE.md: "The fix is one
# line: bind the published port to loopback"). ppdocwiz shipped "8770:8770",
# i.e. every interface, in front of an app with no authentication.
#
# Scoped to the composes this repository OWNS. ingestion/coa_track/network-shared/
# and server/compose/*.sanitized.yml are captured snapshots of the live host —
# rewriting them to satisfy a lint would destroy the record they exist to be.
OWNED_COMPOSE = ("apps/", "pp-document-suite/")
PUBLISH = re.compile(r'^\s*-\s*"?(?!127\.0\.0\.1:|::1:|localhost:)(\d+):(\d+)"?\s*$')


def check_no_public_ports():
    for p in walk((".yml", ".yaml")):
        if not rel(p).startswith(OWNED_COMPOSE):
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if PUBLISH.match(line):
                FAIL.append(f"{rel(p)}:{i}: publishes a port on all interfaces — "
                            f"bind to 127.0.0.1 and route via Traefik\n      {line.strip()}")


# ── 7. no unpinned pip install in a tracked Dockerfile ───────────────────
# An unpinned image is not reproducible, and it silently changes the framework
# behaviour the app's own path handling rests on.
PIP_INSTALL = re.compile(r"pip\s+install\b")


def check_pinned_pip():
    for p in walk():
        if os.path.basename(p) != "Dockerfile" and not os.path.basename(p).startswith("Dockerfile."):
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if not PIP_INSTALL.search(line) or line.lstrip().startswith("#"):
                continue
            # -r <file> defers the pins to a manifest; == pins inline. Either is fine.
            if " -r " not in line and "==" not in line:
                FAIL.append(f"{rel(p)}:{i}: unpinned pip install — use -r requirements.txt "
                            f"or ==versions\n      {line.strip()}")


# ── 8. no unescaped interpolation into innerHTML ─────────────────────────
# The ppdocwiz frontend interpolated build output, agent replies and tool
# returns straight into innerHTML. Escaping every sink once is a cleanup the
# next feature can silently undo; this keeps it undone-able.
INNER_HTML = re.compile(r"\.innerHTML\s*(=|\+=)")
INTERP = re.compile(r"\$\{([^}]*)\}")


def check_escaped_innerhtml():
    for p in walk((".html", ".js")):
        if not rel(p).startswith("apps/"):
            continue
        src = read(p)
        # Assignment and template body can span lines, so judge the whole file:
        # any interpolation at all must be esc()-wrapped where innerHTML is used.
        if not INNER_HTML.search(src):
            continue
        for m in INTERP.finditer(src):
            if "esc(" in m.group(1):
                continue
            line = src[:m.start()].count("\n") + 1
            FAIL.append(f"{rel(p)}:{line}: interpolation not esc()-wrapped in a file that "
                        f"writes innerHTML — escape it, or assign via textContent\n"
                        f"      ${{{m.group(1).strip()[:60]}}}")


CHECKS = [
    ("classical OCR never invoked", check_no_classical_ocr),
    ("no Letta source creation", check_no_letta_sources),
    ("no committed credentials", check_no_secrets),
    ("all Python parses", check_python_parses),
    ("gap analysis self-consistent", check_gap_analysis),
    ("no all-interfaces published ports", check_no_public_ports),
    ("pip installs are pinned", check_pinned_pip),
    ("innerHTML interpolations are escaped", check_escaped_innerhtml),
]

if __name__ == "__main__":
    print("policy check\n" + "=" * 60)
    for name, fn in CHECKS:
        before = len(FAIL)
        fn()
        added = len(FAIL) - before
        print(f"  {'FAIL' if added else 'ok  '}  {name}"
              + (f"  ({added})" if added else ""))
    for w in WARN:
        print(f"\nWARN  {w}")
    if FAIL:
        print("\n" + "-" * 60)
        for f in FAIL:
            print(f"FAIL  {f}")
        print(f"\n{len(FAIL)} problem(s).")
        sys.exit(1)
    print("\nAll policy checks passed.")
