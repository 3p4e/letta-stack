#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The package, built from what the toolchain has already written.

    python3 design_handoff/toolchain/package_v40.py [--date 2026-09-17]

Eight whole archives, each well under GitHub's 100 MB limit, no splitting (the Head of QC,
17.09.2026: no split archive — "do what is logical"). One archive is one thing a reader
asks for, and nothing is cut in half:

  * `PP_CoQ_Tranche_N_<date>.zip` (N = 1, 2, 3): the certificates of quality of one tranche
    — the merged tranche document (release round then retest) and the retest round alone,
    then every certificate as HTML, vector PDF and Word, by round; and the README;
  * `PP_iCoA_Tranche_N_<date>.zip` (N = 1, 2, 3): the internal certificates of analysis
    behind those certificates of quality, the same three ways, plus the merged retest set;
  * `PP_CoQ_Package_<date>.zip`: everything shared — the merged documents of all three
    tranches and the by-round documents (01_Merged_PDF), the certificates outside the
    tranches with their internal certificates (02_Certificates/Not_in_a_tranche), the two
    certificate lists (03_Lists), the merged internal certificates (04_Internal_CoA), the
    master workbook (05_Master_Workbook), the product specification (06_Specifications)
    and the desk's records (07_Records);
  * `PP_Specification_<date>.zip`: the whole intermediate bulk product specification,
    QCSP 001 v.04 — the bound document and all 57 sheets. It is one document for both the
    signed and the unsigned set, so it travels once and is not copied into either.

An archive over LIMIT is a refusal, not a warning: GitHub rejects a file over 100 MB on
push, and an archive that cannot be pushed is not a deliverable.

It refuses a stale build: every page must be newer than its HTML and every Word file newer
than its page. Dated archives of another day, and any split parts, are removed from dist/.
"""
import argparse, datetime as dt, glob, json, os, re, sys, zipfile
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
LIMIT = 95 * 1048576
ICOA = os.path.join(GAP, "icoa_handoff", "v3")
ICOA_STEM = re.compile(r"^iCoA-PP_26-\d+_([^_]+)_")


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


def internal_rows(coq_rows):
    """[(tranche, round, stem, html, pdf, docx)] for all 172 internal certificates.

    From v3/, which is the fleet the certificates of quality cite. icoa_handoff/out/ holds
    the superseded v2 set and is not shipped - an earlier version of this script took it,
    which would have put 154 withdrawn certificates in the package.

    An internal certificate takes the tranche of the CERTIFICATE OF QUALITY THAT CITES IT,
    not the tranche its own file name would suggest. A lot without a P number is named by
    its cultivation batch, and the scope files are keyed on P numbers, so reading the
    tranche off the stem put 26 internal certificates outside the tranche their own
    certificate of quality is in.
    """
    data = json.load(open(os.path.join(GAP, "coq_artifact_data.json"), encoding="utf-8"))
    by_code = {}
    for c in data["coqs"]:
        icoa = str(c.get("icoa_code") or "").strip()
        if icoa.startswith("iCoA-PP_"):
            by_code[icoa] = str(c.get("regcode") or "").strip()
    code_tranche = {}
    for icoa, regcode in by_code.items():
        for t, _series, stem, _html in coq_rows:
            if regcode and stem.startswith(regcode + "_"):
                code_tranche[icoa] = t
                break
    tr = M.tranches()
    rows = []
    for rnd in ("INITIAL", "RETEST"):
        for html in sorted(glob.glob(os.path.join(ICOA, "ISSUE_iCOA", rnd, "*.html"))):
            stem = os.path.splitext(os.path.basename(html))[0]
            pdf = os.path.join(ICOA, "pdf", "pages", stem + ".pdf")
            docx = os.path.join(ICOA, "docx", rnd, stem + ".docx")
            for f, what in ((pdf, "page"), (docx, "Word file")):
                if not os.path.exists(f):
                    raise SystemExit("no %s for %s — print_icoa_v3.py / export_docx_icoa.py first"
                                     % (what, stem))
            code = "_".join(stem.split("_")[:2])          # iCoA-PP_26-127
            m = ICOA_STEM.match(stem)
            t = code_tranche.get(code, tr.get(m.group(1), "") if m else "")
            rows.append((t, rnd, stem, html, pdf, docx))
    if len(rows) != 172:
        raise SystemExit("expected 172 internal certificates, found %d" % len(rows))
    return rows


def add_internal(z, root, rows):
    for _t, rnd, stem, html, pdf, docx in sorted(rows, key=lambda r: r[2]):
        sub = "Retest" if rnd == "RETEST" else "Release"
        z.write(html, "%s/HTML/%s/%s.html" % (root, sub, stem))
        z.write(pdf, "%s/PDF/%s/%s.pdf" % (root, sub, stem))
        z.write(docx, "%s/DOCX/%s/%s.docx" % (root, sub, stem))


def seal(path, root, docs, written):
    """Close the archive out, and refuse one GitHub would reject."""
    size = os.path.getsize(path)
    if size > LIMIT:
        raise SystemExit("%s is %.1f MiB — over the %.0f MiB an archive may be"
                         % (os.path.basename(path), size / 1048576.0, LIMIT / 1048576.0))
    written.append((root, docs, size))


def build(date):
    rows = M.collect()
    if len(rows) != 172:
        raise SystemExit("expected 172 documents in out/, found %d" % len(rows))
    irows = internal_rows(rows)
    os.makedirs(DIST, exist_ok=True)
    for old in (glob.glob(os.path.join(DIST, "PP_CoQ_*.z*"))
                + glob.glob(os.path.join(DIST, "PP_iCoA_*.z*"))
                + glob.glob(os.path.join(DIST, "PP_Specification_*.z*"))):
        if not old.endswith("_%s.zip" % date) or re.search(r"\.z\d\d$", old):
            os.remove(old); print("removed", os.path.relpath(old, HANDOFF))
    written = []
    for t in ("1", "2", "3"):
        root = "PP_CoQ_Tranche_%s%s_%s" % (t, SET, date); mine = [r for r in rows if str(r[0]) == t]
        path = os.path.join(DIST, root + ".zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            add_docs(z, root, mine)
            for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
                z.write(os.path.join(PDF, fn), root + "/" + fn)
            z.write(README, root + "/README.md")
        seal(path, root, len(mine), written)

        root = "PP_iCoA_Tranche_%s%s_%s" % (t, SET, date); theirs = [r for r in irows if r[0] == t]
        path = os.path.join(DIST, root + ".zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            add_internal(z, root, theirs)
            for fn in ("iCoA_Retest_Tranche_%s.pdf" % t, "iCoA_Retest_Tranche_%s.docx" % t):
                f = os.path.join(ICOA, "pdf", fn)
                if os.path.exists(f):
                    z.write(f, root + "/" + fn)
            for f in (os.path.join(GAP, "icoa_handoff", "README.md"),
                      os.path.join(ICOA, "README.md")):
                if os.path.exists(f):
                    z.write(f, root + "/" + ("README_v3.md" if ICOA in f else "README.md"))
        seal(path, root, len(theirs), written)

    root = "PP_CoQ_Package%s_%s" % (SET, date)
    loose = [r for r in rows if not str(r[0])]
    iloose = [r for r in irows if not r[0]]
    path = os.path.join(DIST, root + ".zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for t in ("1", "2", "3"):
            for fn in ("CoQ_Tranche_%s.pdf" % t, "CoQ_Tranche_%s_Retest.pdf" % t):
                z.write(os.path.join(PDF, fn), root + "/01_Merged_PDF/" + fn)
        for fn in FOLDER_DOCS:
            z.write(os.path.join(PDF, fn), root + "/01_Merged_PDF/By_testing_round/" + fn)
        add_docs(z, root + "/02_Certificates/Not_in_a_tranche", loose)
        add_internal(z, root + "/02_Certificates/Not_in_a_tranche/Internal_CoA", iloose)
        for f in glob.glob(os.path.join(GAP, "tracker", "CoQ_Retest_List_%s.*" % date)) + glob.glob(os.path.join(GAP, "tracker", "CoQ_Initial_List_%s.*" % date)):
            z.write(f, root + "/03_Lists/" + os.path.basename(f))
        for fn in ("iCoA_INITIAL.pdf", "iCoA_RETEST.pdf"):
            f = os.path.join(ICOA, "pdf", fn)
            if os.path.exists(f):
                z.write(f, root + "/04_Internal_CoA/" + fn)
        for f in (os.path.join(GAP, "icoa_handoff", "README.md"), os.path.join(ICOA, "README.md")):
            if os.path.exists(f):
                z.write(f, root + "/04_Internal_CoA/" + ("README_v3.md" if ICOA in f else "README.md"))
        masters = sorted(glob.glob(os.path.join(GAP, "tracker", "CoQ_Analysis_Master_v*.xlsx")), key=lambda f: int(re.search(r"_v(\d+)\.xlsx$", f).group(1)) if re.search(r"_v(\d+)\.xlsx$", f) else -1)
        if masters:
            z.write(masters[-1], root + "/05_Master_Workbook/" + os.path.basename(masters[-1]))
        z.writestr(root + "/06_Specifications/WHERE_IT_IS.txt",
                   "The product specification is its own archive: PP_Specification_%s.zip.\n"
                   "It is one document for both sets, signed and unsigned, so it is not\n"
                   "copied into either of them (Head of QC, 18.09.2026 — a separate folder\n"
                   "with the entire specification).\n" % date)
        for rel in ("tracker/OPEN_ITEMS.md", "design_handoff/docs/REBUILD_v40.md", "design_handoff/dist/BUILD.md",
                    "tracker/ENGAGEMENT_REPORT_%s.md" % date, "tracker/ENGAGEMENT_REPORT_%s.html" % date):
            f = os.path.join(GAP, rel)
            if os.path.exists(f):
                z.write(f, root + "/07_Records/" + os.path.basename(f))
        z.write(README, root + "/README.md")
    seal(path, root, len(loose) + len(iloose), written)

    # The specification is the same document for the signed and the unsigned set, so it
    # travels once, on its own, rather than twice inside archives it would push over the
    # limit (Head of QC, 18.09.2026: "a separate folder with the entire specification").
    root = "PP_Specification_%s" % date
    path = os.path.join(DIST, root + ".zip")
    spec = [os.path.join(GAP, "specs", "QCSP_001_v04", "pdf", "QCSP_001_v04.pdf"),
            os.path.join(GAP, "specs", "Potency_specifications_25_2026-09-17.pdf"),
            os.path.join(GAP, "specs", "potency_specifications_25_2026-09-17.json")]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in spec:
            if os.path.exists(f):
                z.write(f, root + "/" + os.path.basename(f))
        for f in sorted(glob.glob(os.path.join(GAP, "specs", "QCSP_001_v04", "pdf", "pages", "*.pdf"))):
            z.write(f, root + "/Sheets/" + os.path.basename(f))
        z.write(README, root + "/README.md")
    seal(path, root, len([f for f in spec if os.path.exists(f)]), written)

    for root, docs, size in written:
        with zipfile.ZipFile(os.path.join(DIST, root + ".zip")) as z:
            n = len(z.namelist())
        print("%-44s %3d documents  %3d files  %6.1f MiB"
              % (root + ".zip", docs, n, size / 1048576.0))


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args(argv[1:])
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date):
        raise SystemExit("--date YYYY-MM-DD")
    build(a.date); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
