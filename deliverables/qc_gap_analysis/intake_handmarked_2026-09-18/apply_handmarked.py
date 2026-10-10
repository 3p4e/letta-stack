#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enter the values the Head of QC marked by hand on five certificates, 18.09.2026.

    python3 intake_handmarked_2026-09-18/apply_handmarked.py [--dry-run]

Five certificates of quality came back photographed with figures written in blue ink
against cells the page prints as `[NT]` — not tested. The desk does not print a figure
because someone wrote it on a page: it prints a figure because a laboratory's certificate
carries it, and it prints the code, the date and the laboratory beside it. So each
handwritten figure was put through the two-read gate:

* **first read** — the photographs, cropped to the result column and enlarged;
* **second read** — `cell_resolution_2026-09-09.tsv`, the Head of QC's own reading pass
  over the scans, which for each determination names the document, its issue date and the
  laboratory.

For three lots the two reads agree figure for figure and the pass names a citable
document. Those are entered here, and the defect they close is the desk's, not the
laboratory's: **the values were read on 09.09.2026 and never reached the certificate**,
which has been printing `[NT]` over results that were on file the whole time.

| lot | determination | document | what the certificate printed |
| --- | --- | --- | --- |
| P060182 | 9 microbiological purity | 136/0233/26 · 06.03.2026 | [NT] on all five |
| P060182 | 11 heavy metals | 1060/2026 · 09.03.2026 | [NT] on all four |
| P060412 | 9 microbiological purity | 405/0788/26 · 24.06.2026 | [NT] on all five |
| P060412 | 11 heavy metals | 3660/2026 · 22.06.2026 | [NT] on all four |
| P060422 | 9 microbiological purity | 406/0789/26 · 24.06.2026 | [NT] on all five |
| P060422 | 11 heavy metals | 3662/2026 · 22.06.2026 | [NT] on all four |

One figure the photograph could not settle — the lead value on P060412, whose middle
digit is illegible — is taken from the resolution pass, which reads `0,085`. That is the
gate working as intended rather than a guess.

**Two lots are held.** P060372 and P060362 carry handwritten loss on drying, heavy metals
and pesticide residues for which the resolution pass says `NOTHING ON FILE — no document
anywhere`, and whose Drive lot folders hold only the Farmahem potency pair and the
microbiology certificate. The figures are recorded in `reads_handmarked.json` and are not
printed. A value with no document behind it is exactly what assertion A15 refuses, and
the desk will not put one on a release document on the strength of a photograph.

Every certificate cites only documents issued on or before its own day; the script checks
that for each row it writes and refuses the write otherwise.
"""
import argparse
import copy
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
DATA = os.path.join(GAP, "coq_artifact_data.json")
READS = os.path.join(HERE, "reads_handmarked.json")


def day(d):
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", str(d or ""))
    return (m.group(3), m.group(2), m.group(1)) if m else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    data = json.load(io.open(DATA, encoding="utf-8"))
    reads = json.load(io.open(READS, encoding="utf-8"))
    before = copy.deepcopy(data)

    by_lot = {}
    for c in data["coqs"]:
        if c.get("pp"):
            by_lot.setdefault(c["pp"], []).append(c)

    written, touched, refused = 0, [], []
    for lot in reads["apply"]:
        pn = lot["pn"]
        certs = by_lot.get(pn) or []
        if not certs:
            refused.append("%s — no certificate on the desk" % pn)
            continue
        for c in certs:
            rows = {r["no"]: r for r in c["rows"]}
            for g in lot["groups"]:
                iss, dd = day(c.get("issue")), day(g["date"])
                if iss and dd and dd > iss:
                    refused.append("%s %s #%s — %s of %s postdates the certificate (%s)"
                                   % (pn, c["regcode"], g["det"], g["code"], g["date"],
                                      c.get("issue")))
                    continue
                for no, val in sorted(g["vals"].items()):
                    r = rows.get(no)
                    if r is None:
                        refused.append("%s %s — no row %s" % (pn, c["regcode"], no))
                        continue
                    r["res"] = val
                    r["doc"] = g["code"]
                    r["dd"] = g["date"]
                    r["lab"] = g["lab"]
                    r["st"] = "covered"
                    written += 1
            touched.append("%s  %s  %s" % (c["regcode"], pn, c["t"]))

        # the register block keeps the same documents, so Section 03 and the register
        # cannot drift apart; a block that does not exist is not invented.
        for e in data.get("reg", []):
            if (e.get("pn") or "") != pn:
                continue
            have = {x.get("code") for x in e.get("certs", [])}
            for g in lot["groups"]:
                if g["code"] in have:
                    continue
                e.setdefault("certs", []).append({
                    "code": g["code"], "date": g["date"], "lab": g["lab"],
                    "vals": {}, "flags": []})

    print("rows written      : %d" % written)
    print("certificates      : %d" % len(touched))
    for t in sorted(set(touched)):
        print("   %s" % t)
    print("held, not printed : %s"
          % ", ".join("%s (%s)" % (h["pn"], h["cb"]) for h in reads["held"]))
    if refused:
        print("REFUSED:")
        for r in refused:
            print("   %s" % r)

    if a.dry_run:
        print("\n--dry-run: nothing written")
        return 1 if refused else 0
    if before == data:
        print("\nnothing changed")
        return 0
    with io.open(DATA, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print("\n%s rewritten" % os.path.relpath(DATA, GAP))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
