#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register GP0824_02's first testing round, and split GP0824_01's two microbiology reports.

Two defects, both found by checking the owner's control sheets back against the ingested
certificates rather than against the register.

--------------------------------------------------------------------------------------
1. GP0824_02 was missing an entire round of testing.

The register held only the July round — ППК25174, IPH 3176/2025, IPH 627/1128/25 — whose
Total Δ9-THC is 23.19 %. The control sheets release GP0824_02 at 23.79 %, and that figure
was being reported as a sheet-vs-knowledgebase disagreement.

It is not. The 23.79 % is on a certificate the register never held. GP0824_02 was tested
twice, and the May round is in the knowledgebase in full (file "GP0824_02 - (samo rezultat
bez sertifikat) 2.txt"):

    ППК25139     UKIM Faculty of Pharmacy, Skopje 22.05.2025, completed 20.05.2025,
                 received 15.05.2025.  Вкупно Δ9-THC 23.79 — matching the sheets exactly.
    2471/2025    IPH health-safety report, 30.05.2025 — pesticides, heavy metals,
                 total aflatoxins.
    471/0862/25  IPH microbiology, received 16.05.2025, issued 22.05.2025.

So the sheets were right and the register was short a round. Nothing on the sheets is
changed; the missing certificates are added and the disagreement resolves itself.

One thing about ППК25139 is worth knowing when it is cited on a CoQ: the document is headed
"РЕЗУЛТАТ ОД ИСПИТУВАЊЕ" (result of testing) over "Број на приемна контролна книга", not
the "СЕРТИФИКАТ"/"главна контролна книга" heading the other ППК documents carry. It is a
numbered UKIM result sheet rather than a certificate. The number is recorded as printed
and the distinction is left to the owner.

Also worth knowing: ППК25139 prints the strain as "Super Pie", while the two IPH reports
on the same sample print "GRAPE PIE". The Strain column keeps the batch's established
name; the divergence is a certificate fact, reported, not silently reconciled.

--------------------------------------------------------------------------------------
2. GP0824_01's microbiology rows cited one report and carried the other's numbers.

The GP0824_01 file holds two distinct IPH microbiology reports, both received 08.04.2025
and both issued 14.04.2025, on two separately submitted samples:

    318/0585/25   "Grape Pie - сув цвет ..., 33,5 g"      Барање бр. 026/2025
                  TAMC 4,2 x 10³ CFU/g    TYMC 6 x 10² CFU/g
    319/0586/25   "Grape Pie (1) - сув цвет ..., 38 g"    Барање бр. 031/2025
                  TAMC 5,2 x 10³ CFU/g    TYMC 8,8 x 10² CFU/g

The register held five rows: numbered 319/0586/25, but carrying 4.2×10³ and 6×10² — which
are 318/0585/25's results. The number and the numbers came from different reports. That is
the precise failure a CoQ reference is meant to prevent, so the existing rows are relabelled
to the report their results actually came from, and 319/0586/25 is added as its own report
with its own results.

Nothing here is inferred. Every value is transcribed from the ingested certificate text.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

UKIM = "UKIM Faculty of Pharmacy — Center for Natural Products"
IPH = "IPH — Institute of Public Health"

# both GP0824_02 May-round reports are pages of one PDF, filed in P050022 (GP0824_02)
GP02_LINK = "https://drive.google.com/file/d/1ZyghF4WvmezDzjbWQXcbvTkfc6dmHTJl/view"

# ППК25139 — UKIM, 22.05.2025
UKIM_ROWS = [
    ("Loss on Drying", "≤ 10.00%", "7.21%"),
    ("Cannabidiolic acid (CBDA) content", "/", "ND"),
    ("Cannabidiol (CBD) content", "/", "0.02%"),
    ("Cannabinol (CBN) content", "≤ 1.00%", "0.53%"),
    ("Delta-9-THC content", "/", "26.52%"),
    ("Delta-9-THCA content", "/", "0.10%"),
    ("Total CBD (CBD + CBDA x 0.877)", "/", "0.10%"),
    ("Total Delta-9-THC (THC + THCA x 0.877)", "/", "23.79%"),
]

# 2471/2025 — IPH health safety, 30.05.2025. Every pesticide and metal reads "Н.д." on the
# report; the acceptance criteria are the report's own MaxDK column, which matches the PP
# release spec already recorded against the July round.
IPH_ROWS = [
    ("Deltamethrin", "<0.5 mg/kg", "N.D."),
    ("Chlorpyriphos-methyl", "<0.1 mg/kg", "N.D."),
    ("Chlorpyriphos-ethyl", "<0.2 mg/kg", "N.D."),
    ("Endosulfan (sum of isomers and endosulfan sulfate)", "<3 mg/kg", "N.D."),
    ("Lindan", "<0.6 mg/kg", "N.D."),
    ("Aldrin and dieldrin (sum of)", "<0.05 mg/kg", "N.D."),
    ("HCH (sum of alpha-, beta-, delta- and epsilon-)", "<0.3 mg/kg", "N.D."),
    ("HCB (Hexachlorbenzene)", "<0.1 mg/kg", "N.D."),
    ("DDT (total)", "<1 mg/kg", "N.D."),
    ("Heptachlor (sum of heptachlor and heptachlorepoxide)", "<0.05 mg/kg", "N.D."),
    ("Endrin", "<0.05 mg/kg", "N.D."),
    ("Chlordane (sum of cis- and trans-)", "<0.05 mg/kg", "N.D."),
    ("Metoxychlor", "<0.05 mg/kg", "N.D."),
    ("Cadmium", "<0.3 mg/kg (≤ 1)", "N.D."),
    ("Lead", "<0.5 mg/kg (≤ 5)", "N.D."),
    ("Mercury", "<0.1 mg/kg", "N.D."),
    ("Arsenic", "<0.2 mg/kg (≤ 2)", "N.D."),
    ("Total aflatoxins", "<4 µg/kg", "<2 µg/kg"),
]

# 471/0862/25 — IPH microbiology, issued 22.05.2025. The bile-tolerant result prints both
# bounds ("< 10^1 и > 10 CFU/g") and is kept that way.
MICRO_ROWS = [
    ("Total aerobic microbial count (TAMC)", "≤ 10⁵ CFU/g", "700 CFU/g"),
    ("Total combined yeasts/moulds count (TYMC)", "≤ 10⁴ CFU/g", "<10 CFU/g"),
    ("Bile-tolerant gram-negative bacteria", "≤ 10⁴ CFU/g", "<10¹ and >10 CFU/g"),
    ("Escherichia coli", "absent/g", "Одговара (absent)"),
    ("Salmonella", "absent/25g", "Одговара (absent)"),
]

# 319/0586/25 — the GP0824_01 report whose results the register did not hold
GP01_319 = [
    ("Total aerobic microbial count (TAMC)", "≤ 10⁵ CFU/g", "5.2×10³ CFU/g"),
    ("Total combined yeasts/moulds count (TYMC)", "≤ 10⁴ CFU/g", "8.8×10² CFU/g"),
    ("Bile-tolerant gram-negative bacteria", "≤ 10⁴ CFU/g", "<10 CFU/g"),
    ("Escherichia coli", "absent/g", "Одговара (absent)"),
    ("Salmonella", "absent/25g", "Одговара (absent)"),
]


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    def first_row_of(batch):
        for r in rows:
            if (r["Cultivation Batch"] or "").strip() == batch:
                return r
        raise SystemExit("batch %s not in register" % batch)

    added, relabelled = [], 0

    # --- 1. GP0824_02's May round -------------------------------------------
    g2 = first_row_of("GP0824_02")
    if not any((r["Certificate Code"] or "").strip() == "ППК25139" for r in rows):
        for code, date, inst, block in (
                ("ППК25139", "22.05.2025 (completed 20.05.2025)", UKIM, UKIM_ROWS),
                ("2471/2025", "30.05.2025", IPH, IPH_ROWS),
                ("471/0862/25", "22.05.2025", IPH, MICRO_ROWS)):
            for param, ac, result in block:
                added.append({
                    "Seq": g2["Seq"], "Cultivation Batch": "GP0824_02",
                    "P-Number": g2["P-Number"], "Strain": g2["Strain"],
                    "Parameter": param, "Acceptance Criterion": ac, "Result": result,
                    "Certificate Code": code, "Issue Date": date,
                    "Issuing Institution": inst, "Drive File Link": GP02_LINK,
                })

    # --- 2. GP0824_01's two microbiology reports ----------------------------
    g1 = first_row_of("GP0824_01")
    for r in rows:
        if ((r["Cultivation Batch"] or "").strip() == "GP0824_01"
                and (r["Certificate Code"] or "").strip() == "319/0586/25"):
            r["Certificate Code"] = "318/0585/25"
            relabelled += 1
    if relabelled and not any(
            (r["Certificate Code"] or "").strip() == "319/0586/25" for r in rows):
        link = g1["Drive File Link"]
        for param, ac, result in GP01_319:
            added.append({
                "Seq": g1["Seq"], "Cultivation Batch": "GP0824_01",
                "P-Number": g1["P-Number"], "Strain": g1["Strain"],
                "Parameter": param, "Acceptance Criterion": ac, "Result": result,
                "Certificate Code": "319/0586/25", "Issue Date": "14.04.2025",
                "Issuing Institution": IPH, "Drive File Link": link,
            })

    if not added and not relabelled:
        print("nothing to do — both rounds already registered")
        return 0

    rows.extend(added)
    # keep each batch's rows contiguous and in their original order
    order = {}
    for i, r in enumerate(rows):
        order.setdefault(r["Seq"], i)
    rows.sort(key=lambda r: (int(r["Seq"]), order[r["Seq"]]))

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("rows added: %d    GP0824_01 rows relabelled 319/0586/25 -> 318/0585/25: %d"
          % (len(added), relabelled))
    print("total rows now: %d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
