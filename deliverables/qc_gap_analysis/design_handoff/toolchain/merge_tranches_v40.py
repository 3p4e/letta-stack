#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One document per tranche — every certificate of quality that tranche carries.

    python3 design_handoff/toolchain/merge_tranches_v40.py
    python3 design_handoff/toolchain/merge_tranches_v40.py --dpi 400
    python3 design_handoff/toolchain/merge_tranches_v40.py --no-flatten

`print_v40.py` prints the set the way it is **built** — the release certificates in
one folder, the 12-month reissues split by tranche. The Head of QC asked on
16.09.2026 for the set the way a tranche is **read**: "two PDF files, tranche one and
tranche two, that will contain all of the certificates of quality for the respective
tranche into one file as merged certificates document."

So a tranche document holds both rounds for its own lots — the release certificates
first, in register order, then the reissues, in register order. That is the order the
rounds happened in, which is how a batch file reads.

## Which certificate belongs to which tranche

The tranche of a lot is the desk's own scope, not a property of the certificate:
`tracker/coq_reissue_scope_2026-09-15.csv` first, then the older
`coq_draft_scope_2026-09-10.csv`, keyed by **P lot** — the same bridge `build_v40.js`
uses to file a reissue. A certificate whose lot appears in neither scope belongs to no
tranche and is **named in the run's output** rather than dropped quietly.

## The pages are not re-rendered

A page here is the page `print_v40.py` produced, so a certificate in the merged
document is the same certificate a person prints singly — no second rendering, no
chance of the two disagreeing. Each page carries a bookmark naming its certificate,
read off the page's own text, so a bookmark can never name a page it is not on.

## Flattening

`--flatten` (the default) renders each page once, here, at 300 dpi into a single RGB
raster and makes that raster the page. Gradients, blends and soft masks are resolved to
pixels before the file leaves the desk, so every printer puts the same thing on paper
instead of interpreting the artwork itself. The raster is Flate, not JPEG — lossless,
and on this artwork smaller than JPEG q95 as well. What is lost is the text layer: a
flattened page cannot be selected or searched. Both forms are written, and the vector
one stays the searchable record.
"""
import argparse, csv, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
HANDOFF = os.path.dirname(HERE)
GAP = os.path.dirname(HANDOFF)
ROOT = os.path.dirname(os.path.dirname(GAP))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(GAP, "live_instrument"))
sys.path.insert(0, os.path.join(ROOT, "ingestion", "coa_track", "letta-imb-coas"))
from print_v40 import merge, order_key, FOLDERS          # noqa: E402
from print_coq_pdfs import FAMILIES, SUBSETS, page_text, render   # noqa: E402
import house_fonts                                                # noqa: E402

OUT = os.path.join(HANDOFF, "out")
PDF = os.path.join(HANDOFF, "pdf")
SCOPES = ("coq_reissue_scope_2026-09-15.csv", "coq_draft_scope_2026-09-10.csv")
STEM = re.compile(r"^(?:CoQ-PP_26-\d+|CoQ-UNASSIGNED)_([^_]+)_")


def tranches():
    """Tranche by P lot, the reissue scope first — the same bridge build_v40.js uses."""
    out = {}
    for f in SCOPES:
        p = os.path.join(GAP, "tracker", f)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                lot = (r.get("p_lot") or "").strip()
                if lot and lot != "—":
                    out.setdefault(lot, (r.get("tranche") or "").strip())
    return out


def lot_of(stem):
    """The batch a document is for, from its file name.

    >>> lot_of("CoQ-PP_26-013_P050072_GP_Grape_Pie_Grade_II")
    'P050072'
    >>> lot_of("CoQ-UNASSIGNED_P160012_P_GrapePie_Grade_I")
    'P160012'
    """
    m = STEM.match(stem)
    return m.group(1) if m else ""


def collect():
    """[(tranche, series, stem, html)] for every built document, series release/reissue."""
    tr, rows = tranches(), []
    for folder in FOLDERS:
        d = os.path.join(OUT, folder)
        if not os.path.isdir(d):
            continue
        series = "reissue" if folder.startswith("REISSUE") else "release"
        for fn in os.listdir(d):
            if not fn.endswith(".html"):
                continue
            stem = fn[:-5]
            rows.append((tr.get(lot_of(stem), ""), series, stem, os.path.join(d, fn)))
    return rows


def print_pages(htmls, pages_dir, chromium=None):
    """Print the documents that have no page yet, with the package's export settings.

    The faces are subset to what THESE documents print and inlined, and Google is
    blocked for the run — same mechanism as print_v40.py, so a page printed here and a
    page printed there are the same page.
    """
    chromium = chromium or (glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome")
                            or [None])[0]
    css, raw, small = house_fonts.font_face_css(page_text(htmls), FAMILIES, SUBSETS)
    print("  fonts: %d faces, %.0f KB upstream -> %.0f KB subset"
          % (css.count("@font-face"), raw / 1024.0, small / 1024.0))
    os.makedirs(pages_dir, exist_ok=True)
    return render(htmls, pages_dir, chromium, css)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--no-flatten", action="store_true")
    ap.add_argument("--tranche", action="append", default=None,
                    help="restrict to these tranches (default: 1 and 2)")
    ap.add_argument("--no-print", action="store_true",
                    help="fail instead of printing a document that has no page yet")
    ap.add_argument("--chromium", default=None)
    a = ap.parse_args(argv[1:])
    wanted = a.tranche or ["1", "2"]
    rows = collect()
    pages_dir = os.path.join(PDF, "pages")
    missing, outside = [], sorted(s for t, _, s, _h in rows if not t)
    todo = [h for t, _s, stem, h in rows if t in wanted
            and not os.path.exists(os.path.join(pages_dir, stem + ".pdf"))]
    if todo and not a.no_print:
        print("printing %d document(s) of tranche %s" % (len(todo), ", ".join(wanted)))
        print_pages(sorted(todo, key=order_key), pages_dir, a.chromium)
    for t in wanted:
        group = [r for r in rows if r[0] == t]
        if not group:
            print("tranche %s: no document carries this tranche" % t)
            continue
        order = {"release": 0, "reissue": 1}
        group.sort(key=lambda r: (order[r[1]], order_key(r[2])))
        parts = []
        for _t, _s, stem, _h in group:
            p = os.path.join(pages_dir, stem + ".pdf")
            (parts if os.path.exists(p) else missing).append(p)
        stem_out = os.path.join(PDF, "CoQ_Tranche_%s" % t)
        n = merge(parts, stem_out + ".pdf", False, a.dpi)
        line = "  Tranche %s  %3d page(s)  %s (%.1f MiB)" % (
            t, n, os.path.basename(stem_out + ".pdf"),
            os.path.getsize(stem_out + ".pdf") / 1048576.0)
        if not a.no_flatten:
            merge(parts, stem_out + "_flat.pdf", True, a.dpi)
            line += "  flat %.1f MiB" % (os.path.getsize(stem_out + "_flat.pdf") / 1048576.0)
        print(line)
        print("      %d release + %d reissue" % (
            sum(1 for r in group if r[1] == "release"),
            sum(1 for r in group if r[1] == "reissue")))
    if missing:
        print("  not printed yet — run print_v40.py first:")
        for p in missing:
            print("      " + os.path.basename(p))
    if outside:
        print("  %d document(s) belong to no tranche in either scope file, so they are "
              "in neither document:" % len(outside))
        for s in outside:
            print("      " + s)
    return 1 if missing else 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
