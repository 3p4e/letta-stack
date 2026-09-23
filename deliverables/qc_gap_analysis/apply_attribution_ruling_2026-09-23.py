#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Head of QC's ruling of 23.09.2026 — the three parts of it that need no new figure.

    python3 deliverables/qc_gap_analysis/apply_attribution_ruling_2026-09-23.py --check
    python3 deliverables/qc_gap_analysis/apply_attribution_ruling_2026-09-23.py

Three changes, all of them relabelling. **No result value is touched anywhere in this
script**, and nothing is invented: what a laboratory measured stays exactly as it was
measured, and where a panel is empty it stays empty, to be reported rather than filled.

## 1 · The iCoA number is the CoQ number

> "the iCoA doc code and the CoQ doc code should go side by side"

Ten of the 172 pairs did. The two registers were numbered independently, so
`CoQ-PP_26-010` carried `iCoA-PP_26-080` and the two ran up to 88 apart. Because there is
exactly one iCoA per CoQ, and the join between them is the lot `Key` and not the number,
the numbers can simply be exchanged: each iCoA takes its own certificate's number. That is
a **permutation**, so it is applied in a single pass — renaming one at a time would walk a
code into a number another certificate still holds.

Every citation moves with it. 511 result rows cite an iCoA as their source document, and
each of those strings is mapped through the same table, so a row that pointed at a
physical document before points at the same physical document after.

## 2 · Identification A, Identification B and foreign matter are ours

> "On all certificates of quality, initial and retest, identification A, identification B
> will be assigned our in-house purely plant laboratory. And on the same certificate for
> the retest batches, it will be included foreign matter."

457 of the 516 rows already read that way and cite the certificate's own iCoA. The
remaining **59 rows on 20 certificates** credited the Center for Natural Products and cited
one of twelve ППК261xx documents — the finding the build gate reports as OI-27. They move
to the in-house laboratory, citing the certificate's own iCoA on its own issue date, which
is the convention the other 457 already follow.

The result is not touched: `Conforms` stays `Conforms`. What changes is who the register
says determined it, and the ruling is that we did.

## 3 · One canonical name per institution

Three laboratories appear under two names each — `IJZ` beside `IPH — Institute of Public
Health`, `CNP` beside `UKIM Faculty of Pharmacy — Center for Natural Products`, `FHM`
beside `Farmahem` — on 85 rows. A certificate that names the same institution two ways in
one fleet is a finding against "the correct institution", so the short forms are expanded.

## What this script deliberately does not do

The ruling also fixes which laboratory performs each panel, and requires a value on every
certificate for microbiology, heavy metals and pesticides. Those are **not** applied here,
because closing them means transcribing figures from certificates — a QC act on the
physical page, not a relabelling. `verify_attribution_2026-09-23.py` reports exactly which
cells are affected and which of them have a document on file.

Idempotent: a second run reports every change as already applied and writes nothing.
Refuses to run if the register is not the shape it was verified against.
"""
import argparse
import collections
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "coq_artifact_data.json")
MAPMD = os.path.join(HERE, "tracker", "ICOA_RENUMBER_2026-09-23.md")

IPH = "IPH — Institute of Public Health"
CNP = "UKIM Faculty of Pharmacy — Center for Natural Products"
FHM = "Farmahem"
PP = "Purely Plant GmbH (in-house)"
ALIAS = {"IJZ": IPH, "CNP": CNP, "FHM": FHM}

INHOUSE_DETS = ("1", "2", "7")            # Ident A, Ident B, foreign matter
ICOA = re.compile(r"iCoA-PP_26-(\d{3})")
EXPECT_COQS = 172


def renumber_map(coqs):
    """old iCoA code -> new iCoA code, where the new one is the CoQ's own number."""
    m = {}
    for c in coqs:
        old, reg = c.get("icoa_code"), str(c.get("regcode") or "")
        n = reg.replace("CoQ-PP_26-", "")
        if not old or not re.fullmatch(r"\d{3}", n):
            raise SystemExit("cannot renumber: %r carries %r" % (reg, old))
        m[old] = "iCoA-PP_26-" + n
    if len(set(m)) != len(m) or len(set(m.values())) != len(m):
        raise SystemExit("the renumbering is not one-to-one — refusing to write")
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report and write nothing")
    ap.add_argument("--data", default=DATA)
    a = ap.parse_args(argv)

    d = json.load(open(a.data, encoding="utf-8"))
    coqs = d.get("coqs") or []
    if len(coqs) != EXPECT_COQS:
        raise SystemExit("expected %d certificates, found %d — refusing to write"
                         % (EXPECT_COQS, len(coqs)))

    # ---- 1 · the renumbering, in one pass
    m = renumber_map(coqs)
    moved = sum(1 for k, v in m.items() if k != v)
    cites = 0
    for c in coqs:
        c["icoa_code"] = m[c["icoa_code"]]
        for r in c.get("rows") or []:
            doc = str(r.get("doc") or "")
            if ICOA.search(doc):
                new = ICOA.sub(lambda x: m.get(x.group(0), x.group(0)), doc)
                if new != doc:
                    cites += 1
                r["doc"] = new

    # ---- 2 · Ident A, Ident B and foreign matter in house, on the certificate's own iCoA
    rehomed = collections.Counter()
    for c in coqs:
        mine, when = c["icoa_code"], c.get("icoa_issue")
        for r in c.get("rows") or []:
            if str(r.get("no")) not in INHOUSE_DETS:
                continue
            if str(r.get("lab") or "") == PP and str(r.get("doc") or "") == mine:
                continue
            rehomed[(str(c.get("regcode")), str(r.get("lab") or "")[:40])] += 1
            r["lab"], r["doc"] = PP, mine
            if when:
                r["dd"] = when

    # ---- 3 · one canonical name per institution
    renamed = collections.Counter()
    for c in coqs:
        for r in c.get("rows") or []:
            lab = str(r.get("lab") or "")
            if lab in ALIAS:
                renamed[lab] += 1
                r["lab"] = ALIAS[lab]

    print("1 · the iCoA number is the CoQ number")
    print("    %d of %d numbers move; %d citing rows follow them" % (moved, len(m), cites))
    print("2 · Identification A, Identification B and foreign matter in house")
    print("    %d row(s) on %d certificate(s) move to %s"
          % (sum(rehomed.values()), len({k[0] for k in rehomed}), PP))
    for (code, was), n in sorted(rehomed.items())[:8]:
        print("        %s  %d row(s), was %s" % (code, n, was))
    if len(rehomed) > 8:
        print("        ... and %d more certificate(s)" % (len(rehomed) - 8))
    print("3 · one canonical name per institution")
    for k, v in renamed.most_common():
        print("    %4d row(s): %s -> %s" % (v, k, ALIAS[k]))
    if not renamed:
        print("    already clean")

    if a.check:
        print("\n--check: nothing written")
        return 0
    if not (moved or rehomed or renamed):
        print("\nalready applied — nothing written")
        return 0

    if not os.path.exists(a.data + ".bak"):
        shutil.copy2(a.data, a.data + ".bak")
    with open(a.data, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
    print("\nwrote %s" % a.data)

    with open(MAPMD, "w", encoding="utf-8") as fh:
        fh.write("# The iCoA renumbering of 23.09.2026\n\n")
        fh.write('Head of QC: *"the iCoA doc code and the CoQ doc code should go side by '
                 'side"*. Ten of the 172 pairs already did. Each iCoA now takes its own '
                 "certificate's number; the join between the registers is the lot key, not "
                 "the number, so nothing else moves. %d citation(s) followed.\n\n" % cites)
        fh.write("| CoQ | iCoA was | iCoA now |\n| --- | --- | --- |\n")
        for c in coqs:
            was = [k for k, v in m.items() if v == c["icoa_code"]][0]
            if was != c["icoa_code"]:
                fh.write("| %s | %s | %s |\n" % (c.get("regcode"), was, c["icoa_code"]))
    print("wrote %s" % MAPMD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
