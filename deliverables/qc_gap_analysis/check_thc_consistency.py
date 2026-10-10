#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Total THC on every certificate: the header banner, the results row, the cited document, the page.

    python3 deliverables/qc_gap_analysis/check_thc_consistency.py

The Head of QC, 17.09.2026: "run a final check on the actual analysis results regarding total
THC — what is referenced, what is stated in the results table, what is in the header."

For each of the 172 certificates: the Section 01 banner figure against the #4 row; the #4 row
against the register's value for the document it cites (an in-house internal certificate is not
a register document and is skipped; a CNP certificate the register holds under the in-house
CoA's combined name is found under that name); the cited date against the register's; the
printed form of both figures (two decimals); and the built page against the data — the banner
as printed and the #4 row as printed. Prints one line per finding, or 'no findings'.
"""
import collections, glob, html, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "coq_artifact_data.json"); OUT = os.path.join(HERE, "design_handoff", "out")


def nk(s):
    return re.sub(r"[\s\-/_.]+", "", str(s or "")).upper()


def num(s):
    m = re.search(r"\d+(?:[.,]\d+)?", str(s or "")); return float(m.group(0).replace(",", ".")) if m else None


def main(argv):
    d = json.load(io.open(SRC, encoding="utf-8"))
    reg = {}
    for b in d["reg"]:
        for c in b.get("certs") or []:
            v = (c.get("vals") or {}).get("E")
            if v is None:
                continue
            code = str(c.get("code") or "")
            reg.setdefault(nk(code), (str(v), c.get("date"), False))
            if "/" in code and "CoA" in code:                       # 'PP CoA #027 / ППК25370' -> also under ППК25370;
                reg.setdefault(nk(code.split("/", 1)[1]), (str(v), c.get("date"), True))   # its date is the in-house CoA's
    flags = collections.defaultdict(list); notes = []
    for c in d["coqs"]:
        r4 = next((r for r in c["rows"] if r["no"] == "4"), {})
        res = (r4.get("res") or "").strip(); doc = (r4.get("doc") or "").strip(); banner = (c.get("thc") or "").strip()
        nres, nban = num(res), num(banner)
        if (nres is None) != (nban is None) or (nres is not None and abs(nres - nban) > 0.001):
            flags["banner differs from the results row"].append((c["regcode"], banner, res))
        if nres is not None and doc and doc != "—" and not doc.startswith("iCoA"):
            hit = reg.get(nk(doc))
            if not hit:
                flags["cited document not in the register"].append((c["regcode"], doc, res))
            elif abs(num(hit[0]) - nres) > 0.001:
                flags["results row differs from the register"].append((c["regcode"], doc, res, hit[0]))
            elif hit[1] != r4.get("dd"):
                if hit[2]:
                    notes.append((c["regcode"], doc, r4.get("dd"), "register files it under the in-house CoA's number and date", hit[1]))
                else:
                    flags["cited date differs from the register"].append((c["regcode"], doc, r4.get("dd"), hit[1]))
        if res and res != "—" and not re.match(r"^\d+\.\d{2}$", res):
            flags["results row not printed with two decimals"].append((c["regcode"], res))
        if banner and not re.match(r"^\d+\.\d{2}$", banner):
            flags["banner not printed with two decimals"].append((c["regcode"], banner))
        f = glob.glob(os.path.join(OUT, "**", c["regcode"] + "_*.html"), recursive=True)
        if f:
            s = io.open(f[0], encoding="utf-8").read()
            m = re.search(r'class="pbp-val">(.*?)</span></span>', s, re.S)
            pb = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else None; pbn = num(pb)
            if (pbn is None) != (nban is None) or (pbn is not None and abs(pbn - nban) > 0.001):
                flags["page banner differs from the data"].append((c["regcode"], pb, banner))
            body = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", s[s.index("<body"):], flags=re.S)
            t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
            i = t.find("Assay — Total Δ"); seg = t[i:i + 200]
            if nres is not None and ("%s %%" % res) not in seg:
                flags["page results row differs from the data"].append((c["regcode"], res, seg[-60:]))
    print("certificates checked:", len(d["coqs"]))
    for k, v in flags.items():
        print("%s: %d" % (k, len(v)))
        for x in v[:10]:
            print("   ", x)
    if not flags:
        print("no findings")
    for x in notes:
        print("note:", x)
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
