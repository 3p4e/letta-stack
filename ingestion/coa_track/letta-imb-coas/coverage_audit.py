#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which release parameters each batch actually has a result for, tranche by tranche.

"Is the register complete" has been answered so far by counting batches and certificates.
That is the wrong measure. A batch can hold twenty rows and still be missing the mycotoxin
panel, and a tranche can look fully covered because its loudest batches are.

This asks the only question that matters for release: for every batch, is there a
transcribed result for every parameter the Ph. Eur. Cannabis flos monograph and the Purely
Plant release specification require? Nothing is judged pass or fail — presence only.

The panel below is what a complete batch record needs:

  identity        appearance, identification, foreign matter, loss on drying
  assay           total Δ9-THC, total CBD, total CBN
  mycotoxins      aflatoxin B1, total aflatoxins, ochratoxin A   (all three, per the
                  owner's instruction that a batch assayed only for total aflatoxins is
                  recorded as not tested on the other two rather than left blank)
  heavy metals    lead, cadmium, arsenic, mercury                (four, not one)
  pesticides      the screen, however the certificate reports it
  microbiology    TAMC, TYMC, bile-tolerant gram-negative, E. coli, Salmonella

Stability pulls are excluded: they are a different study, not part of the release record,
and counting them would make a batch look covered on the strength of a six-month timepoint.
"""
import csv
import os
import sys
from collections import OrderedDict, defaultdict

import coa_pivot as cp
import crosscheck_sources as cc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "PP_Coverage_By_Batch.tsv")

# Appearance, Identification and Foreign matter are determined by Purely Plant on its own
# in-house CoA and never appear on an outsourced-laboratory certificate. The owner has
# ruled the in-house CoAs out of the knowledgebase entirely — they are not ingested and not
# filed — so those three are out of scope here. Measuring against them made 62, 49 and 50
# batches look deficient for holding exactly what they were supposed to hold.
OUT_OF_SCOPE = OrderedDict([
    ("appearance", "Appearance"),
    ("identification", "Identification"),
    ("foreign_matter", "Foreign matter"),
])

PANEL = OrderedDict([
    ("loss_on_drying", ("identity", "Loss on drying")),
    ("thc", ("assay", "Total Δ9-THC")),
    ("cbd", ("assay", "Total CBD")),
    ("cbn", ("assay", "Total CBN")),
    ("afla_b1", ("mycotoxins", "Aflatoxin B1")),
    ("aflatoxins", ("mycotoxins", "Aflatoxins Σ")),
    ("ochratoxin", ("mycotoxins", "Ochratoxin A")),
    ("pb", ("metals", "Lead")),
    ("cd", ("metals", "Cadmium")),
    ("as_", ("metals", "Arsenic")),
    ("hg", ("metals", "Mercury")),
    ("pesticides", ("pesticides", "Pesticide screen")),
    ("tamc", ("micro", "TAMC")),
    ("tymc", ("micro", "TYMC")),
    ("bile", ("micro", "Bile-tolerant")),
    ("ecoli", ("micro", "E. coli")),
    ("salmonella", ("micro", "Salmonella")),
])

GROUPS = ("identity", "assay", "mycotoxins", "metals", "pesticides", "micro")


def main():
    rows, batches = cp.build()
    by_seq = cp.group_by_seq(rows)

    tr = {cc.norm_batch(r["batch"]): r for r in cc.read_tsv("tranches_overview.tsv")}

    records = []
    for b in batches:
        key = cc.norm_batch(b["batch"])
        have = set()
        for rec in by_seq[b["seq"]]:
            param = rec["Parameter"] or ""
            if cp.STABILITY_RE.search(param):
                continue                      # a stability pull is not a release result
            kind = cp.classify(param)
            if kind in PANEL:
                have.add(kind)
        sheet = tr.get(key) or {}
        records.append({
            "seq": int(b["seq"]),
            "batch": b["batch"],
            "p": (b["p_number"] or "").strip(),
            "strain": b["strain"],
            "tranche": (sheet.get("tranche") or "").strip() or "-",
            "have": have,
            "missing": [k for k in PANEL if k not in have],
        })

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["Tranche", "Seq", "Batch", "P-Number", "Strain", "Covered", "Of",
                    "Missing parameters"])
        for r in sorted(records, key=lambda x: (x["tranche"], x["seq"])):
            w.writerow([r["tranche"], r["seq"], r["batch"], r["p"], r["strain"],
                        len(r["have"]), len(PANEL),
                        ", ".join(PANEL[k][1] for k in r["missing"]) or "—"])

    print("Wrote %s" % OUT)
    print("\nPanel: %d parameters per batch (stability pulls excluded)\n" % len(PANEL))

    by_tranche = defaultdict(list)
    for r in records:
        by_tranche[r["tranche"]].append(r)

    for t in sorted(by_tranche):
        group = by_tranche[t]
        full = [r for r in group if not r["missing"]]
        print("=" * 78)
        print("TRANCHE %s — %d batches, %d complete, %d with gaps"
              % (t, len(group), len(full), len(group) - len(full)))
        print("=" * 78)
        gap_count = defaultdict(int)
        for r in group:
            for k in r["missing"]:
                gap_count[k] += 1
        for k, n in sorted(gap_count.items(), key=lambda kv: -kv[1]):
            print("   %-18s missing on %2d of %2d batches" % (PANEL[k][1], n, len(group)))
        if not gap_count:
            print("   (no gaps)")
        print()
        for r in sorted(group, key=lambda x: x["seq"]):
            mark = "OK " if not r["missing"] else "GAP"
            print("   %s seq %-3d %-14s %-22s %2d/%2d  %s"
                  % (mark, r["seq"], r["batch"], r["strain"][:22],
                     len(r["have"]), len(PANEL),
                     ", ".join(PANEL[k][1] for k in r["missing"])[:72]))
        print()

    total_full = sum(1 for r in records if not r["missing"])
    print("=" * 78)
    print("OVERALL: %d of %d batches carry the full panel" % (total_full, len(records)))
    worst = defaultdict(int)
    for r in records:
        for k in r["missing"]:
            worst[k] += 1
    print("\nMost frequently missing across all batches:")
    for k, n in sorted(worst.items(), key=lambda kv: -kv[1])[:12]:
        print("   %-18s %2d batches" % (PANEL[k][1], n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
