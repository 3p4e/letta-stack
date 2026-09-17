#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The four archives of the package, built from what the toolchain has already written.

    python3 design_handoff/toolchain/package_v40.py [--date 2026-09-17]

One archive per tranche, each carrying every certificate of the tranche as HTML, vector
PDF and Word, plus the two merged tranche documents; and one archive by testing round,
carrying the four folder documents and — so that no document is delivered only inside a
merged file — the HTML, PDF and Word of the documents that belong to no tranche.

It refuses a stale build. Every document must have a page newer than its HTML and a Word
file newer than its page: an archive that ships a page printed before the HTML it was
printed from says something the desk no longer says.

Dated archives of another day are removed from dist/ and named in the output, so the
folder holds one set.
"""
import argparse, datetime as dt, glob, os, re, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); HANDOFF = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import merge_tranches_v40 as M                                          # noqa: E402
OUT = os.path.join(HANDOFF, "out"); PDF = os.path.join(HANDOFF, "pdf")
PAGES = os.path.join(PDF, "pages"); DOCX = os.path.join(HANDOFF, "docx")
DIST = os.path.join(HANDOFF, "dist"); README = os.path.join(DIST, "README.md")
FOLDER_DOCS = ["CoQ_ISSUE_COQ.pdf", "CoQ_REISSUE_T1.pdf", "CoQ_REISSUE_T2.pdf", "CoQ_REISSUE_T3.pdf"]


def triple(html):
    """(html, page pdf, docx) for one document, or a named refusal."""
    stem = os.path.splitext(os.path.basename(html))[0]
    folder = os.path.relpath(os.path.dirname(html), OUT)
    pdf = os.path.join(PAGES, stem + ".pdf"); docx = os.path.join(DOCX, folder, stem + ".docx")
    for p, what in ((pdf, "page"), (docx, "Word file")):
        if not os.path.exists(p):
            raise SystemExit("no %s for %s — print_v40.py / export_docx_v40.py first" % (what, stem))
    if os.path.getmtime(pdf) < os.path.getmtime(html):
        raise SystemExit("stale page: %s was printed before its HTML was built" % stem)
    if os.path.getmtime(docx) < os.path.getmtime(pdf):
        raise SystemExit("stale Word file: %s was exported before its page was printed" % stem)
    return html, pdf, docx


def add_docs(z, root, rows):
    for _, series, stem, html in sorted(rows, key=lambda r: r[2]):
        sub = "Retest" if series == "reissue" else "Release"
        h, p, d = triple(html)
        z.write(h, "%s/HTML/%s/%s.html" % (root, sub, stem))
        z.write(p, "%s/PDF/%s/%s.pdf" % (root, sub, stem))
        z.write(d, "%s/DOCX/%s/%s.docx" % (root, sub, stem))


def build(date):
    rows = M.collect()
    if len(rows) != 172:
        raise SystemExit("expected 172 documents in out/, found %d" % len(rows))
    os.makedirs(DIST, exist_ok=True)
    for old in glob.glob(os.path.join(DIST, "PP_CoQ_*.zip")):
        if not old.endswith("_%s.zip" % date):
            os.remove(old); print("removed", os.path.relpath(old, HANDOFF))
    written = []
    for t in ("1", "2", "3"):
        root = "PP_CoQ_Tranche_%s_%s" % (t, date); mine = [r for r in rows if str(r[0]) == t]
        with zipfile.ZipFile(os.path.join(DIST, root + ".zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            add_docs(z, root, mine)
            for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
                z.write(os.path.join(PDF, fn), root + "/" + fn)
            z.write(README, root + "/README.md")
            n = len(z.namelist())
        written.append((root, len(mine), n))
    root = "PP_CoQ_By_testing_round_%s" % date; loose = [r for r in rows if not str(r[0])]
    with zipfile.ZipFile(os.path.join(DIST, root + ".zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for fn in FOLDER_DOCS:
            z.write(os.path.join(PDF, fn), root + "/" + fn)
        add_docs(z, root + "/Not_in_a_tranche", loose)
        z.write(README, root + "/README.md")
        n = len(z.namelist())
    written.append((root, len(loose), n))
    for root, docs, n in written:
        size = os.path.getsize(os.path.join(DIST, root + ".zip")) / 1048576.0
        print("%-40s %3d documents  %3d files  %6.1f MiB" % (root + ".zip", docs, n, size))


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args(argv[1:])
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date):
        raise SystemExit("--date YYYY-MM-DD")
    build(a.date); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
