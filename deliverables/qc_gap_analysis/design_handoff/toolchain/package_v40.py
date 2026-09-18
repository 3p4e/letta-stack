#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The package, built from what the toolchain has already written.

    python3 design_handoff/toolchain/package_v40.py [--date 2026-09-17]

Four whole archives, each under GitHub's 100 MB limit, no splitting (the Head of QC,
17.09.2026: no split archive — "do what is logical"):

  * `PP_CoQ_Tranche_N_<date>.zip` (N = 1, 2, 3): everything of one tranche — the merged tranche
    document (release round then retest) and the retest round alone, then every certificate of
    the tranche as HTML, vector PDF and Word, by round; and the README;
  * `PP_CoQ_Package_<date>.zip`: everything shared — the merged documents of all three tranches
    and the by-round documents (01_Merged_PDF), the six certificates outside the tranches
    (02_Certificates/Not_in_a_tranche), the two certificate lists (03_Lists), the internal
    certificates of analysis (04_Internal_CoA), the master workbook (05_Master_Workbook), the
    potency specification (06_Specifications) and the desk's records (07_Records).

It refuses a stale build: every page must be newer than its HTML and every Word file newer
than its page. Dated archives of another day, and any split parts, are removed from dist/.
"""
import argparse, datetime as dt, glob, os, re, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); HANDOFF = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import merge_tranches_v40 as M                                          # noqa: E402
OUT = os.path.join(HANDOFF, "out"); PDF = os.path.join(HANDOFF, "pdf")
PAGES = os.path.join(PDF, "pages"); DOCX = os.path.join(HANDOFF, "docx")
DIST = os.path.join(HANDOFF, "dist"); README = os.path.join(DIST, "README.md"); GAP = os.path.dirname(HANDOFF)
FOLDER_DOCS = ["CoQ_ISSUE_COQ.pdf", "CoQ_REISSUE_T1.pdf", "CoQ_REISSUE_T2.pdf", "CoQ_REISSUE_T3.pdf"]

# The desk issues the same fleet twice (Head of QC, 18.09.2026): "one complete set with the
# signatures applied and one complete set without the signatures applied". One switch drives
# the whole pipeline - PP_SIGNATURES=1 builds the signed fleet - and the same switch names its
# archives, so the two sets sit side by side in dist/ and neither can be mistaken for the other.
SET = "_Signed" if os.environ.get("PP_SIGNATURES") == "1" else ""


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
    for old in glob.glob(os.path.join(DIST, "PP_CoQ_*.z*")):
        if not old.endswith("_%s.zip" % date) or re.search(r"\.z\d\d$", old):
            os.remove(old); print("removed", os.path.relpath(old, HANDOFF))
    written = []
    for t in ("1", "2", "3"):
        root = "PP_CoQ_Tranche_%s%s_%s" % (t, SET, date); mine = [r for r in rows if str(r[0]) == t]
        with zipfile.ZipFile(os.path.join(DIST, root + ".zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            add_docs(z, root, mine)
            for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
                z.write(os.path.join(PDF, fn), root + "/" + fn)
            z.write(README, root + "/README.md")
            n = len(z.namelist())
        written.append((root, len(mine), n))
    root = "PP_CoQ_Package%s_%s" % (SET, date); loose = [r for r in rows if not str(r[0])]
    with zipfile.ZipFile(os.path.join(DIST, root + ".zip"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for t in ("1", "2", "3"):
            for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
                z.write(os.path.join(PDF, fn), root + "/01_Merged_PDF/" + fn)
        for fn in FOLDER_DOCS:
            z.write(os.path.join(PDF, fn), root + "/01_Merged_PDF/By_testing_round/" + fn)
        add_docs(z, root + "/02_Certificates/Not_in_a_tranche", loose)
        for f in glob.glob(os.path.join(GAP, "tracker", "CoQ_Retest_List_%s.*" % date)) + glob.glob(os.path.join(GAP, "tracker", "CoQ_Initial_List_%s.*" % date)):
            z.write(f, root + "/03_Lists/" + os.path.basename(f))
        for f in glob.glob(os.path.join(GAP, "icoa_handoff", "out", "*", "*.html")):
            z.write(f, root + "/04_Internal_CoA/%s/%s" % (os.path.basename(os.path.dirname(f)), os.path.basename(f)))
        if os.path.exists(os.path.join(GAP, "icoa_handoff", "README.md")):
            z.write(os.path.join(GAP, "icoa_handoff", "README.md"), root + "/04_Internal_CoA/README.md")
        masters = sorted(glob.glob(os.path.join(GAP, "tracker", "CoQ_Analysis_Master_v*.xlsx")), key=lambda f: int(re.search(r"_v(\d+)\.xlsx$", f).group(1)) if re.search(r"_v(\d+)\.xlsx$", f) else -1)
        if masters:
            z.write(masters[-1], root + "/05_Master_Workbook/" + os.path.basename(masters[-1]))
        for f in glob.glob(os.path.join(GAP, "specs", "*")):
            z.write(f, root + "/06_Specifications/" + os.path.basename(f))
        for rel in ("tracker/OPEN_ITEMS.md", "design_handoff/docs/REBUILD_v40.md", "design_handoff/dist/BUILD.md",
                    "tracker/ENGAGEMENT_REPORT_%s.md" % date, "tracker/ENGAGEMENT_REPORT_%s.html" % date):
            f = os.path.join(GAP, rel)
            if os.path.exists(f):
                z.write(f, root + "/07_Records/" + os.path.basename(f))
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
