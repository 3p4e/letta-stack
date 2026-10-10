#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A panel determined on one sample prints whole, or it does not print at all.

    python3 deliverables/qc_gap_analysis/verify_panels.py        # 0 findings = clean

The Head of QC, 16.09.2026:

    "It's not possible that the same batch has only one parameter for microbiological
    purity stated as absent and the others missing. If there are values for one parameter
    of the microbiological purity, there are results and values for all of them from that
    batch."

He is right, and it is a property of the document rather than a preference. A
microbiological purity report determines all five parameters on one sample and prints them
in one table; a certificate that cites it for two and leaves three blank is not a
defensible page — it says the desk holds part of a result that does not come in parts.

The same holds for the heavy metals: one report, four analytes, one table.

This is the standing check. It runs over the desk's export rather than the rendered HTML,
so it catches a partial panel before a certificate is built from it. A panel that is
entirely absent is not a finding — that is an honest gap, and the certificate says so in
every one of its five cells.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "coq_artifact_data.json")
PANELS = {
    "microbiological purity": ("9.1", "9.2", "9.3", "9.4", "9.5"),
    "heavy metals": ("11.1", "11.2", "11.3", "11.4"),
}
BLANK = ("", "—")


def findings(data):
    """Every certificate printing some but not all of a panel.

    >>> findings({"coqs": [{"n": "X", "rows": [
    ...     {"no": "9.1", "res": "1 \\u00d7 10\\u00b3"}, {"no": "9.2", "res": ""},
    ...     {"no": "9.3", "res": ""}, {"no": "9.4", "res": ""}, {"no": "9.5", "res": ""}]}]})
    [('X', '', 'microbiological purity', 1, 5, '9.2, 9.3, 9.4, 9.5')]
    >>> findings({"coqs": [{"n": "Y", "rows": [{"no": n, "res": ""} for n in
    ...     ("9.1", "9.2", "9.3", "9.4", "9.5")]}]})
    []
    """
    out = []
    for c in data["coqs"]:
        res = {r["no"]: str(r.get("res") or "").strip() for r in c["rows"]}
        for name, dets in PANELS.items():
            have = [d for d in dets if res.get(d, "") not in BLANK]
            if 0 < len(have) < len(dets):
                out.append((c.get("regcode") or c.get("n"), c.get("pp") or c.get("cb") or "",
                            name, len(have), len(dets),
                            ", ".join(d for d in dets if res.get(d, "") in BLANK)))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    f = findings(json.load(open(a.src, encoding="utf-8")))
    print("certificates printing a partial panel: %d" % len(f))
    for row in f:
        print("   %-16s %-11s %-24s %d of %d — missing %s" % row)
    return 1 if f else 0


if __name__ == "__main__":
    import doctest
    fail, total = doctest.testmod()
    print("%d/%d doctests passed" % (total - fail, total))
    raise SystemExit(main(sys.argv) if not fail else 1)
