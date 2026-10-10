#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read back every batch documentation bundle on the shelf and check it page by page.

    python3 deliverables/qc_gap_analysis/bundles/audit_dossiers.py

Nothing here trusts the builder. Each bundle is opened as a reader would open it, and the
four things the Head of QC asked for are checked against the pages themselves:

  * page 1 is the certificate of quality named in the table of contents, page 2 the
    internal certificate of analysis behind it;
  * every page of every external laboratory certificate carries the true-copy stamp -
    full-size page, stamp laid over it;
  * no page WE issue carries one: not the certificate of quality, not the internal
    certificate, not the product specification. The stamp says a laboratory's document was
    checked against its original, and for our own documents there is no original elsewhere;
  * the specification sheet is the last page, and the index says which bundles have none.

The stamp is found by its geometry, which is fixed in points and never scaled: about
117 x 51 pt, and on a page carrying /Rotate the width and height are read swapped. That
swap is why an earlier sweep reported two hundred unstamped pages that were stamped.
"""
import collections
import json
import os
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
INDEX = os.path.join(HERE, "dossiers", "INDEX.json")
STAMP_MIN = (40, 56)
STAMP_MAX = (110, 122)


def stamps(page):
    n = 0
    for im in page.get_image_info():
        x0, y0, x1, y1 = im["bbox"]
        d = sorted((abs(x1 - x0), abs(y1 - y0)))
        if STAMP_MIN[0] <= d[0] <= STAMP_MIN[1] and STAMP_MAX[0] <= d[1] <= STAMP_MAX[1]:
            n += 1
    return n


def main():
    shelf = json.load(open(INDEX, encoding="utf-8"))
    findings = []
    ext_pages = unstamped = ours_stamped = with_spec = 0
    for r in shelf:
        path = os.path.join(GAP, r["file"])
        name = os.path.basename(path)
        if not os.path.exists(path):
            findings.append((name, "the index names a file that is not on the shelf")); continue
        doc = pymupdf.open(path)
        toc = doc.get_toc()
        if doc.page_count != r["pages"]:
            findings.append((name, "%d pages on the shelf, %d in the index"
                             % (doc.page_count, r["pages"])))
        if not toc or r["coq"] not in toc[0][1]:
            findings.append((name, "the table of contents does not open on %s" % r["coq"]))
        if len(toc) < 2 or "internal certificate" not in toc[1][1]:
            findings.append((name, "no internal certificate of analysis behind page 1"))
        spec = [t for t in toc if "product specification" in t[1]]
        if r.get("specification") and not spec:
            findings.append((name, "the index claims a specification sheet the bundle has not"))
        if spec:
            with_spec += 1
            if spec[0][2] <= 2:
                findings.append((name, "the specification sheet is not behind the certificates"))
        # ours: the certificate of quality, the internal certificate, the specification
        first_ext = toc[2][2] if len(toc) > 2 else doc.page_count + 1
        last_ext = (spec[0][2] - 1) if spec else doc.page_count
        for i in range(doc.page_count):
            n = stamps(doc[i])
            ours = (i + 1) < first_ext or (i + 1) > last_ext
            if ours:
                if n:
                    ours_stamped += 1
                    findings.append((name, "page %d is ours and carries a stamp" % (i + 1)))
            else:
                ext_pages += 1
                if n == 0:
                    unstamped += 1
                    findings.append((name, "page %d is a laboratory page and is not stamped"
                                     % (i + 1)))
                elif n > 1:
                    findings.append((name, "page %d carries %d stamps" % (i + 1, n)))
        doc.close()
    print("bundles %d   external pages %d   unstamped %d   our pages stamped %d"
          % (len(shelf), ext_pages, unstamped, ours_stamped))
    print("with a specification sheet: %d" % with_spec)
    byt = collections.Counter("T%s %s" % (r["tranche"] or "x", r["round"]) for r in shelf)
    for k in sorted(byt):
        print("   %-12s %d" % (k, byt[k]))
    print("structural findings: %d" % len(findings))
    for n, f in findings[:60]:
        print("   %-58s %s" % (n[:58], f))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
