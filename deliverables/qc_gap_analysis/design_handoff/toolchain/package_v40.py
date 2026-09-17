#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The package, built from what the toolchain has already written.

    python3 design_handoff/toolchain/package_v40.py [--date 2026-09-17]            # four archives (per tranche, by round)
    python3 design_handoff/toolchain/package_v40.py --single [--date 2026-09-17]   # ONE archive, the whole folder tree

The Head of QC, 17.09.2026: "package it all under one zip file, and inside the zip place the
entire folder structure." `--single` writes `dist/PP_CoQ_Package_<date>/` — the merged tranche
documents first, then every certificate as HTML, vector PDF and Word by tranche and round, the
two certificate lists, the internal certificates of analysis, the master workbook, the potency
specification and the desk's records — and zips it. GitHub refuses any file over 100 MB, and
the tree is about three times that, so the zip is written as one archive in parts of at most
95 MB (`PP_CoQ_Package_<date>.zip` with `.z01`, `.z02` …): 7-Zip, WinRAR, The Unarchiver or
`zip -s 0 PP_CoQ_Package_<date>.zip --out joined.zip` open it as one file. The four per-tranche
archives are removed when the single one is written, so dist/ holds one set.

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


GAP = os.path.dirname(HANDOFF)


def single(date):
    """One folder tree, then one split zip of it."""
    import shutil, subprocess
    rows = M.collect()
    if len(rows) != 172:
        raise SystemExit("expected 172 documents in out/, found %d" % len(rows))
    root = os.path.join(DIST, "PP_CoQ_Package_%s" % date)
    if os.path.isdir(root):
        shutil.rmtree(root)
    def put(src, rel):
        dst = os.path.join(root, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
    # 01 · the merged documents, tranche by tranche, then by testing round
    for t in ("1", "2", "3"):
        for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
            put(os.path.join(PDF, fn), "01_Merged_PDF/" + fn)
    for fn in FOLDER_DOCS:
        put(os.path.join(PDF, fn), "01_Merged_PDF/By_testing_round/" + fn)
    # 02 · every certificate, three formats, by tranche and round
    for tr, series, stem, html in sorted(rows, key=lambda r: r[2]):
        folder = ("Tranche_%s" % tr) if str(tr) else "Not_in_a_tranche"
        sub = "Retest" if series == "reissue" else "Release"
        h, p, d = triple(html)
        put(h, "02_Certificates/%s/%s/HTML/%s.html" % (folder, sub, stem))
        put(p, "02_Certificates/%s/%s/PDF/%s.pdf" % (folder, sub, stem))
        put(d, "02_Certificates/%s/%s/DOCX/%s.docx" % (folder, sub, stem))
    # 03 · the lists; 04 · the internal certificates; 05 · the master; 06 · the specification; 07 · records
    for f in glob.glob(os.path.join(GAP, "tracker", "CoQ_Retest_List_%s.*" % date)) + glob.glob(os.path.join(GAP, "tracker", "CoQ_Initial_List_%s.*" % date)):
        put(f, "03_Lists/" + os.path.basename(f))
    for f in glob.glob(os.path.join(GAP, "icoa_handoff", "out", "*", "*.html")):
        put(f, "04_Internal_CoA/%s/%s" % (os.path.basename(os.path.dirname(f)), os.path.basename(f)))
    if os.path.exists(os.path.join(GAP, "icoa_handoff", "README.md")):
        put(os.path.join(GAP, "icoa_handoff", "README.md"), "04_Internal_CoA/README.md")
    masters = sorted(glob.glob(os.path.join(GAP, "tracker", "CoQ_Analysis_Master_v*.xlsx")), key=lambda f: int(re.search(r"_v(\d+)", f).group(1)) if re.search(r"_v(\d+)\.xlsx$", f) else -1)
    if masters:
        put(masters[-1], "05_Master_Workbook/" + os.path.basename(masters[-1]))
    for f in glob.glob(os.path.join(GAP, "specs", "*")):
        put(f, "06_Specifications/" + os.path.basename(f))
    for rel in ("tracker/OPEN_ITEMS.md", "design_handoff/docs/REBUILD_v40.md", "design_handoff/dist/BUILD.md",
                "tracker/ENGAGEMENT_REPORT_%s.md" % date, "tracker/ENGAGEMENT_REPORT_%s.html" % date):
        f = os.path.join(GAP, rel)
        if os.path.exists(f):
            put(f, "07_Records/" + os.path.basename(f))
    put(README, "README.md")
    n = sum(len(fs) for _, _, fs in os.walk(root)); size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(root) for f in fs)
    print("%s: %d files, %.0f MiB" % (os.path.relpath(root, HANDOFF), n, size / 1048576.0))
    for old in glob.glob(os.path.join(DIST, "PP_CoQ_*.z*")):
        os.remove(old)
    subprocess.check_call(["zip", "-q", "-r", "-s", "95m", "PP_CoQ_Package_%s.zip" % date, "PP_CoQ_Package_%s" % date], cwd=DIST)
    shutil.rmtree(root)
    parts = sorted(glob.glob(os.path.join(DIST, "PP_CoQ_Package_%s.z*" % date)))
    for p in parts:
        print("   %-34s %6.1f MiB" % (os.path.basename(p), os.path.getsize(p) / 1048576.0))
    return parts


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--single", action="store_true", help="one archive of the whole folder tree, in parts under 95 MB")
    a = ap.parse_args(argv[1:])
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date):
        raise SystemExit("--date YYYY-MM-DD")
    single(a.date) if a.single else build(a.date); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
