#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register the GG1024 in-house CoA, which the extraction pass had missed entirely.

GG1024 is the sixth R&D batch. The other five — CJ1024, BG1024, BSS1024, HPA1024,
OPM1024 — each carry their in-house Report of Analysis in the register. GG1024 carried
nothing: zero rows, on a batch the List of COAs marks coa_on_file = YES and the Tranches
Overview releases at 13.34 %. The certificate was ingested all along (GG1024.txt,
2 468 chars, processing_status completed); it simply never made it into the table.

Every cell below is transcribed off that file. The transcription convention is HPA1024's,
because HPA1024 is the same document type from the same issuer:

  * Parameter carries the method the CoA prints for it, as "<name> — <method>". Where the
    CoA prints a method once and leaves the rows beneath it blank (the pesticide block
    under Ph. Eur. 2.8.13, the heavy-metal block under Ph. Eur. 2.4.27), the method
    applies to the whole block and is repeated per row. E. coli and Salmonella print no
    method and get none.
  * Superscripts are written ^N — the CoA sets them typographically and the register is
    plain text.
  * The document footnote marks with ** the parameters sent to accredited laboratories.
    Appearance and Foreign matter carry no **; they are the producer's own determinations
    and the Issuing Institution cell says so rather than crediting a lab that did not
    perform them.
  * Certificate Code records that the document prints no number, rather than inventing one.

Three things are recorded exactly as printed even though they read oddly, because they are
what the paper says and the register does not correct laboratories:

  * The microbial acceptance criteria: "<10^5, max 500 000 CFU/g" (TAMC) and
    "<10^4, max 50 000 CFU/g" (TYMC). **Those maxima are wrong on the form.** Ph. Eur.
    5.1.4, in identical harmonised wording USP <1111>, reads an enumeration criterion of
    10^n CFU as a maximum acceptable count of 2 x 10^n — so 10^5 is 200 000 and 10^4 is
    20 000, not 500 000 and 50 000. No pharmacopoeial text uses a x5 multiplier for
    microbial limits. The figures stay here because this column transcribes the document;
    they were separately copied into `build_qc_register.py` and `build_master_workbook.py`
    as if they were the criterion, and into the batch release register's specification row,
    where on 31.08.2026 they caused four conforming TYMC results to be flagged as
    exceedances. Those three are corrected. **Correcting the in-house CoA form itself is a
    QA action and is not in this script's gift.** Record:
    `review/OOS_RECTIFICATION_2026-08-31.md`.

  * Bile-tolerant gram-negative bacteria: result "<10^2 >10 CFU/g" — the CoA prints both
    bounds, i.e. a count above 10 and below 100.
  * Total Δ9-THC acceptance criterion "12.6 – 15.4% of the labelled amount" — that is the
    document's own wording, kept verbatim in the source layer.

The Drive link is the one thing that cannot be given. There is no GG1024 folder under the
CoA parent at all: of the six R&D batches, five have one and GG1024 does not, and no file
named for it exists anywhere in the drive. The cell says that plainly instead of pointing
at a folder that would not contain the document either.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "exports", "master_coa_table.tsv")

FIELDS = ["Seq", "Cultivation Batch", "P-Number", "Strain", "Parameter",
          "Acceptance Criterion", "Result", "Certificate Code", "Issue Date",
          "Issuing Institution", "Drive File Link"]

BATCH = "GG1024"
STRAIN = "Gorilla Glue"
CODE = ("n/a — Purely Plant in-house CoA (Batch GG1024, no certificate/report number "
        "printed)")
DATE = "23.04.2025"
LINK = ("Not in Drive — in-house CoA held in the knowledgebase as GG1024.txt; no GG1024 "
        "folder exists under the CoA parent")

ACC = ("IPH / UKIM Faculty of Pharmacy [accredited labs per PP in-house CoA footnote**; "
       "lab not attributed per-row]")
OWN = "Not stated on PP in-house CoA (row unmarked, not attributed to an accredited lab)"

PEST = "Ph. Eur. 2.8.13 / MKC EN 15662:2020"
METAL = "Ph. Eur. 2.4.27 / MKC EN 17853:2023"
MICRO = "Ph. Eur. 5.1.8, category C"

# (parameter, acceptance criterion, result, issuing institution)
ROWS = [
    ("Appearance — Visual",
     "Dark green to pale yellow or light brown to reddish-brown female inflorescence, "
     "with characteristic aromatic odour", "Confirms", OWN),
    ("Identification — DAB",
     "The retention time of each cannabinoid of the test solution corresponds to its of "
     "the standard solution", "Confirms", ACC),
    ("Foreign matter — Ph. Eur. 2.8.2", "< 2.0%", "Confirms", OWN),

    ("Total Δ9-tetrahydrocannabinol — DAB",
     "12.6 – 15.4% of the labelled amount", "13.34%", ACC),
    ("Total Cannabidiol — DAB", "< 1.0%", "0.03%", ACC),
    ("Cannabinol — DAB", "< 1.0%", "N.D.", ACC),

    ("Total aflatoxines — Ph. Eur. 2.8.18 / Afla test Fluorometric method",
     "< 4 µg/kg", "< 2 µg/kg", ACC),

    ("Deltamethrin — " + PEST, "< 0.5 mg/kg", "N.D.", ACC),
    ("Chlorpyriphos-methyl — " + PEST, "< 0.1 mg/kg", "N.D.", ACC),
    ("Chlorpyriphos-ethyl — " + PEST, "< 0.2 mg/kg", "N.D.", ACC),
    ("Endosulfan (sum of isomers and endosulfan sulfate) — " + PEST,
     "< 3 mg/kg", "N.D.", ACC),
    ("Lindan — " + PEST, "< 0.6 mg/kg", "N.D.", ACC),
    ("Aldrin and dieldrin (sum of) — " + PEST, "< 0.05 mg/kg", "N.D.", ACC),
    ("HCH (sum of α-, β-, δ- and ε) — " + PEST, "< 0.3 mg/kg", "N.D.", ACC),
    ("HCB (Hexachlorobenzene) — " + PEST, "< 0.1 mg/kg", "N.D.", ACC),
    ("DDT (total) — " + PEST, "< 1 mg/kg", "N.D.", ACC),
    ("Heptachlor (sum of heptachlor and heptachloroepoxide) — " + PEST,
     "< 0.05 mg/kg", "N.D.", ACC),
    ("Endrin — " + PEST, "< 0.05 mg/kg", "N.D.", ACC),
    ("Chlordane (sum of cis- and trans-) — " + PEST, "< 0.05 mg/kg", "N.D.", ACC),
    ("Metoxychlor — " + PEST, "< 0.05 mg/kg", "N.D.", ACC),

    ("Cadmium — " + METAL, "< 0.3 mg/kg", "0.016 mg/kg", ACC),
    ("Lead — " + METAL, "< 0.5 mg/kg", "0.052 mg/kg", ACC),
    ("Mercury — " + METAL, "< 0.1 mg/kg", "0.004 mg/kg", ACC),
    ("Arsenic — " + METAL, "< 0.2 mg/kg", "0.04 mg/kg", ACC),

    ("Total aerobic microbial count (TAMC) — " + MICRO,
     "<10^5, max 500 000 CFU/g", "1.1·10^4 CFU/g", ACC),
    ("Total combined yeasts/moulds count (TYMC) — " + MICRO,
     "<10^4, max 50 000 CFU/g", "<10 CFU/g", ACC),
    ("Bile-tolerant gram-negative bacteria — Ph. Eur. 2.6.12",
     "<10^2 CFU/g", "<10^2 >10 CFU/g", ACC),
    ("Escherichia coli/g", "To be absent", "Absent", ACC),
    ("Salmonella/25g", "To be absent", "Absent", ACC),
]


def main():
    with open(TSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    already = [r for r in rows if (r["Cultivation Batch"] or "").strip() == BATCH]
    if already:
        print("GG1024 already carries %d rows — nothing appended." % len(already))
        return 0

    # Seq is provisional; reconcile_master_table.py renumbers every batch chronologically
    # straight after this, and GG1024's code puts it with the other 10/24 R&D batches.
    seq = str(max(int(r["Seq"]) for r in rows) + 1)
    for param, ac, result, inst in ROWS:
        rows.append({
            "Seq": seq, "Cultivation Batch": BATCH, "P-Number": "", "Strain": STRAIN,
            "Parameter": param, "Acceptance Criterion": ac, "Result": result,
            "Certificate Code": CODE, "Issue Date": DATE,
            "Issuing Institution": inst, "Drive File Link": LINK,
        })

    with open(TSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print("GG1024: %d rows appended at provisional seq %s (total rows now %d)"
          % (len(ROWS), seq, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
