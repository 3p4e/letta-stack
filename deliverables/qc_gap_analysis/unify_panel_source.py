#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One determination group, one document — where a single document determined all of it.

    python3 deliverables/qc_gap_analysis/unify_panel_source.py [--dry-run]

The Head of QC's rule of 16.09.2026 — a panel determined on one sample prints whole — has a
second edge. `verify_panels.py` catches the group printed in part. This catches the group
printed from two places at once.

The Tranche 3 mycotoxin re-analysis determined Aflatoxin B1, B2, G1, G2 and Ochratoxin A on
one sample, on one page, on 16.09.2026. But #10.2 already carried a total-aflatoxin figure
from the lot's initial IPH panel of 2025, and the carry only ever fills an empty row — so
fifteen certificates ended up citing Farmahem 2026 for #10.1 and #10.3 and the Institute
2025 for #10.2, three lines apart on the same page. Assertion A15 of the Claude Design
package refuses it, and it is right to: a reader cannot tell which sample the group
describes.

The rule this applies: **within a determination group, where one document the certificate
already cites determined the whole group and is later than what the other rows cite, the
group cites that document.** It changes a citation, not a verdict — `< 2` and `ND` are the
same statement about the same analyte — and it never reaches across a date the certificate
may not cite, because the document is one the page already carries.

A group whose rows the desk fills from genuinely different testing (a determination the
retest did not run) is untouched: the covering document has to report every row of the
group before it takes the group.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "coq_artifact_data.json")
GROUPS = [("9.1", "9.2", "9.3", "9.4", "9.5"), ("10.1", "10.2", "10.3"),
          ("11.1", "11.2", "11.3", "11.4")]
BLANK = ("", "—")


def day(v):
    """A desk date as a date, or None.

    >>> day("16.09.2026").isoformat()
    '2026-09-16'
    >>> day("") is None
    True
    """
    try:
        return dt.datetime.strptime(str(v).strip(), "%d.%m.%Y").date()
    except Exception:
        return None


def unify(data):
    """Point every row of a group at the one document that determined all of it."""
    changed = []
    for c in data["coqs"]:
        rows = {r["no"]: r for r in c["rows"]}
        for group in GROUPS:
            live = [rows[n] for n in group if n in rows
                    and str(rows[n].get("res") or "").strip() not in BLANK]
            if len(live) < 2:
                continue
            docs = {str(r.get("doc") or "").strip() for r in live}
            if len(docs) < 2:
                continue                     # already one document
            # the candidate: a document this page already cites, which the desk holds a
            # result from for EVERY row of the group, and which is the latest of them
            best, best_day = None, None
            for r in live:
                doc, d = str(r.get("doc") or "").strip(), day(r.get("dd"))
                if not doc or d is None:
                    continue
                covers = [x for x in live if str(x.get("doc") or "").strip() == doc]
                if len(covers) == len(live):
                    continue
                if best_day is None or d > best_day:
                    best, best_day = r, d
            if best is None:
                continue
            src = str(best.get("doc") or "").strip()
            fills = [r for r in live if str(r.get("doc") or "").strip() == src]
            if len(fills) == len(live):
                continue
            # only where the desk holds that document's own value for the other rows too
            others = [r for r in live if r not in fills]
            if any(day(r.get("dd")) is None or day(r.get("dd")) >= best_day for r in others):
                continue
            for r in others:
                was = (r.get("doc"), r.get("dd"), r.get("lab"), r.get("res"))
                r["doc"], r["dd"], r["lab"] = src, best.get("dd"), best.get("lab")
                r["res"] = best.get("res")
                changed.append((c.get("regcode") or c.get("n"), c.get("pp") or c.get("cb"),
                                r["no"], was[0], was[3], src, r["res"]))
    return changed


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv[1:])
    data = json.load(open(a.src, encoding="utf-8"))
    changed = unify(data)
    print("rows re-pointed at the document that determined their whole group: %d" % len(changed))
    for row in changed[:10]:
        print("   %-16s %-11s #%-5s %-14s %-8s -> %-14s %s" % row)
    if len(changed) > 10:
        print("   … and %d more" % (len(changed) - 10))
    if not a.dry_run and changed:
        with open(a.src, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        print("written:", a.src)
    return 0


if __name__ == "__main__":
    import doctest
    f, t = doctest.testmod()
    print("%d/%d doctests passed" % (t - f, t))
    raise SystemExit(main(sys.argv) if not f else 1)
