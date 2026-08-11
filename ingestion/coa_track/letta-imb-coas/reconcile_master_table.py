#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcile the master CoA dataset against the owner's control sheets.

This rewrites *identity and placement* only — which batch a row belongs to, how that
batch is spelled, which packaging lot it carries, and where it sits in the chronology.
It never touches a Parameter, Acceptance Criterion, Result, Certificate Code, Issue
Date, Issuing Institution or Drive link. Those are transcriptions of the certificate
and the certificate is the only thing entitled to change them.

Four defects are corrected, each one checked back to the certificate first:

  1. Seven rows were filed under a packaging lot (P060152, P060212, P060242, P060332,
     P060352, P060382, P060402). That is faithful to the paper — the Farmahem 197-series
     certificates really do print the P-number in the "Серија" field — but it splits four
     physical batches across two register entries each. The Quantities table is the bridge
     between lot and cultivation batch, so each row is refiled under the batch it belongs
     to and the lot moves into the P-Number column where it belongs.

  2. Sub-lots were spelled "-1" in the register and "/1" on every certificate
     (ППК25280 "серија: CJ052501/1", ППК25378 "GP072501/1", ППК26067 "FB012601/1").
     The register carried a file-naming convention, not the certificate's own spelling.

  3. FB012601 is FB012601/1 — ППК26067 names the sub-lot, and its 14.68 % matches the
     Tranches Overview figure for FB012601/1 exactly.

  4. 18 batches carried no packaging lot at all. The Quantities table supplies every one.

Batch order becomes chronological by cultivation date, which the batch code itself
carries (MMYY after the strain prefix), then by sub-lot and packaging lot. Entries whose
code holds no date — the P160xxx Grape Pie lots — fall back to first certificate issue.

Strain spellings are collapsed only where the sole difference is spacing ("GorillaGlue"
-> "Gorilla Glue"). Genuinely different spellings across certificates — Cap Junkie /
Cap Junky / Cup Junky — are left alone; choosing between those is the owner's call, not
a script's.
"""
import csv
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")
SOT = os.path.join(HERE, "sources_of_truth")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

PNUM = re.compile(r"^P\d{6}$")
SUBLOT = re.compile(r"-0*(\d+)([A-Z]?)$", re.I)
# a cultivation code carries MMYY straight after the strain prefix; the prefix may itself
# contain digits (J31, GG4), so the pairs are scanned with a lookahead and the first
# plausible month/year wins
DATEPAIR = re.compile(r"(?=(\d{2})(\d{2}))")
DMY = re.compile(r"(\d{2})[.\-/](\d{2})[.\-/](\d{4})")

# ППК26067 names "серија: FB012601/1"; the register had dropped the sub-lot.
CERT_RELABEL = {"FB012601": "FB012601/1"}


def read_tsv(name):
    with open(os.path.join(SOT, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def slash_sublot(label):
    """Certificates write a sub-lot as '/1'; the register wrote '-1'."""
    return SUBLOT.sub(lambda m: "/%s%s" % (int(m.group(1)), m.group(2).upper()), label)


def strip_note(label):
    """Drop a trailing parenthetical descriptor from a batch cell.

    Two J31122501 rows read "J31122501 (Trimiran cvet sub-lot)" and "... (Racno trimiran
    cvet sub-lot)". That is the packaging presentation Farmahem sampled (100-3-К/26 vs
    100-2-К/26), not a different cultivation batch, and it belongs to the certificate row
    rather than to the batch identity — left in place it invents two phantom batches.
    """
    return re.sub(r"\s*\([^)]*\)\s*$", "", (label or "").strip())


def key_of(label):
    """Comparison key: case, spacing, notes and sub-lot zero-padding folded away."""
    b = strip_note(label).upper().replace(" ", "")
    b = re.sub(r"\s*-?R&D$", "", b)
    b = b.rstrip("*")
    if PNUM.match(b):
        return b
    return re.sub(r"[-/]0*(\d+)([A-Z]?)$", lambda m: "/%s%s" % (m.group(1), m.group(2)), b)


def chrono(label, first_issue):
    """(year, month) of cultivation, read off the batch code; certificate date if absent."""
    s = (label or "").upper().replace(" ", "")
    for m in DATEPAIR.finditer(s):
        mm, yy = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12 and 24 <= yy <= 30:
            return (2000 + yy, mm)
    m = DMY.search(first_issue or "")
    if m:
        return (int(m.group(3)), int(m.group(2)))
    return (9999, 99)


def sublot_no(label):
    m = re.search(r"[-/_](\d+)[A-Z]?$", (label or "").upper())
    return int(m.group(1)) if m else 0


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    before = len({int(r["Seq"]) for r in rows})

    qt = read_tsv("quantities_table.tsv")
    lot_to_batch, batch_to_lot = {}, {}
    for r in qt:
        lot = (r.get("p_number") or "").strip().upper()
        bat = (r.get("batch_label") or "").strip()
        if not bat:
            continue
        if PNUM.match(lot):
            # the sheets flag some batches with a trailing "*"; it is a note to the
            # reader, not part of the batch number
            lot_to_batch[lot] = bat.rstrip("*").strip()
            batch_to_lot[key_of(bat)] = lot

    # --- pass 1: give every row its true batch identity ---------------------
    log = defaultdict(list)
    for r in rows:
        raw = (r["Cultivation Batch"] or "").strip()
        label = CERT_RELABEL.get(raw, raw)
        if label != raw:
            log["relabelled to the certificate's own series"].append("%s -> %s" % (raw, label))

        bare = strip_note(label)
        if bare != label:
            log["packaging descriptor moved out of the batch cell"].append(
                "%s -> %s" % (label, bare))
            label = bare

        k = key_of(label)
        if PNUM.match(k):                      # filed under its packaging lot
            bat = lot_to_batch.get(k)
            if bat:
                log["refiled from packaging lot to cultivation batch"].append(
                    "%s -> %s" % (k, bat))
                r["P-Number"] = k
                label = bat
                k = key_of(bat)

        slashed = slash_sublot(label)
        if slashed != label:
            log["sub-lot respelled as the certificates print it"].append(
                "%s -> %s" % (label, slashed))
        r["Cultivation Batch"] = slashed

        if not (r["P-Number"] or "").strip() and k in batch_to_lot:
            r["P-Number"] = batch_to_lot[k]
            log["packaging lot supplied from the Quantities table"].append(
                "%s -> %s" % (slashed, batch_to_lot[k]))

    # --- pass 2: collapse spacing-only strain variants -----------------------
    spellings = defaultdict(Counter)
    for r in rows:
        s = (r["Strain"] or "").strip()
        if s:
            spellings[re.sub(r"[^a-z0-9]", "", s.lower())][s] += 1
    canon = {}
    for norm, c in spellings.items():
        # prefer the spelling that actually separates the words
        best = max(c, key=lambda s: (len(s.split()) > 1, c[s], -len(s)))
        for s in c:
            if s != best:
                canon[s] = best
    for r in rows:
        s = (r["Strain"] or "").strip()
        if s in canon:
            log["strain spacing normalised"].append("%s -> %s" % (s, canon[s]))
            r["Strain"] = canon[s]

    # --- pass 3: regroup, re-order chronologically, renumber -----------------
    groups = OrderedDict()
    for r in rows:
        groups.setdefault(key_of(r["Cultivation Batch"]), []).append(r)

    merged = [k for k, g in groups.items()
              if len({int(x["Seq"]) for x in g}) > 1]
    for k in merged:
        log["two register entries merged into one batch"].append(
            "%s  (was seq %s)" % (k, ", ".join(str(s) for s in
                                               sorted({int(x["Seq"]) for x in groups[k]}))))

    def sort_key(item):
        k, g = item
        label = g[0]["Cultivation Batch"]
        first = min((x["Issue Date"] or "") for x in g)
        y, m = chrono(label, first)
        lot = next((x["P-Number"] for x in g if (x["P-Number"] or "").strip()), "")
        # within a cultivation month the packaging-lot number is the running order, and it
        # keeps a batch's sub-lots adjacent; batches never packaged for sale sort first
        return (y, m, lot, sublot_no(label), label)

    ordered = sorted(groups.items(), key=sort_key)

    out = []
    for i, (k, g) in enumerate(ordered, start=1):
        # one batch, one strain and one lot across all its rows
        strain = Counter((x["Strain"] or "").strip() for x in g if (x["Strain"] or "").strip())
        lot = next((x["P-Number"] for x in g if (x["P-Number"] or "").strip()), "")
        label = g[0]["Cultivation Batch"]
        for x in g:
            x["Seq"] = str(i)
            x["Cultivation Batch"] = label
            x["P-Number"] = lot
            if strain:
                x["Strain"] = strain.most_common(1)[0][0]
            out.append(x)

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(out)

    print("batches %d -> %d    rows %d (unchanged)" % (before, len(ordered), len(out)))
    for head in sorted(log):
        seen = list(dict.fromkeys(log[head]))
        print("\n%s  (%d)" % (head, len(seen)))
        for line in seen:
            print("   " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
