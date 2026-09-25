#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the Tranche 1 and Tranche 2 retest internal certificates into two PDFs.

    python3 icoa_handoff/v3/merge_tranche_retests.py

The delivery tranche is a Drive-folder grouping, not a laboratory campaign: it comes from
`intake_tranches_2026-09-18/drive_folders_2026-09-18.tsv`, the grouping the Head of QC set on
18.09.2026. A folder is named `<cultivation batch>_<P lot>`, so the lot key is the trailing
field when it reads P0xxxxx; the four folders with no P batch assigned (OPM1024, HPA1024,
BSS1024, BG1024, GG1024, CJ1024) key on their own name, which is how the register writes them.

Every retest ROUND on a tranche lot is included — a lot with two retests contributes two
certificates, because the register issues one per round.

Pages come from `pdf/pages/`, already rendered by print_icoa_v3.py; nothing is re-rendered.
"""
import collections
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(GAP, "intake_tranches_2026-09-18", "drive_folders_2026-09-18.tsv")
PAGES = os.path.join(HERE, "pdf", "pages")
PDF = os.path.join(HERE, "pdf")
PLOT = re.compile(r"^P\d{6}$")


def tranche_lots(path=SRC):
    lots = collections.defaultdict(set)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            tail = r["folder"].rsplit("_", 1)[-1]
            lots[r["tranche"]].add(tail if PLOT.match(tail) else r["folder"])
    return lots


def lot_of(name):
    m = re.search(r"iCoA-PP_26-\d{3}_([A-Za-z0-9]+)_", name)
    return m.group(1) if m else ""


def seq(name):
    m = re.search(r"iCoA-PP_26-(\d{3})", name)
    return int(m.group(1)) if m else 10 ** 6


def label(name):
    code = re.search(r"iCoA-PP_26-\d{3}", name)
    round_ = re.search(r"Retest_(\d+)", name)
    bits = [code.group(0) if code else "—", lot_of(name)]
    if round_:
        bits.append("retest " + round_.group(1))
    return " · ".join(b for b in bits if b)


def merge(pages, dest, title):
    import pymupdf
    out, toc = pymupdf.open(), []
    for p in pages:
        d = pymupdf.open(p)
        out.insert_pdf(d)
        toc.append([1, label(os.path.basename(p)), out.page_count])
        d.close()
    out.set_toc(toc)
    out.set_metadata({"title": title, "producer": "Purely Plant Quality Desk"})
    out.save(dest, garbage=4, deflate=True)
    out.close()
    return len(toc)


def main():
    lots = tranche_lots()
    have = {os.path.basename(p): p for p in glob.glob(os.path.join(PAGES, "*.pdf"))}
    retests = sorted((n for n in have if "_Retest_" in n), key=seq)
    for t, name in (("T1", "Tranche_1"), ("T2", "Tranche_2")):
        sel = [have[n] for n in retests if lot_of(n) in lots[t]]
        covered = {lot_of(os.path.basename(p)) for p in sel}
        missing = sorted(lots[t] - covered)
        dest = os.path.join(PDF, "iCoA_Retest_%s.pdf" % name)
        n = merge(sel, dest, "Purely Plant — Internal Certificates of Analysis — %s retests"
                  % name.replace("_", " "))
        print("  %-10s %3d certificate(s) over %d/%d lots  %s (%.1f MiB)%s"
              % (name, n, len(covered), len(lots[t]), os.path.basename(dest),
                 os.path.getsize(dest) / 1048576.0,
                 "  NO RETEST ON FILE: " + ", ".join(missing) if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
