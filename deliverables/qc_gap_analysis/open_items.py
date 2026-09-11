#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What the desk cannot decide: the standing register of items awaiting the owner.

    python3 deliverables/qc_gap_analysis/open_items.py            # self-test + census
    python3 deliverables/qc_gap_analysis/open_items.py --md       # write the note

A quality desk can normalise a spelling, derive a column and read a verdict off a
page. It cannot decide whether a grade IV lot may cite a grade III specification,
which analyte a mycotoxin figure belongs to, or whether a controlled document may
be dated on a Saturday. Those are the owner's, and until 11.09.2026 they lived in
chat messages and commit bodies, which is to say they were being rediscovered
every session.

This is the register. Each item says what was found, what the desk did with it,
and precisely what is being asked — because "there is a problem with the
specifications" is not a question anyone can answer, and "may a grade IV lot cite
the grade III specification of the same strain, given that no printed attribute
has ever differed between grades in 257 issued documents" is.

Every item carries its evidence: the file and the figure behind it, so the owner
is ruling on the record rather than on a summary of it.

`STATE` is one of:

    open        the desk is waiting; nothing is being printed on a certificate
    marked      the certificate prints the field bracketed in red, unticked
    ruled       the owner has ruled; kept here for the record with the ruling
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (ref, area, state, headline, found, desk, asked, evidence)
ITEMS = [
    ("OI-01", "Specification", "marked",
     "A lot graded IV or V whose strain has no specification at that grade",
     "The QCSP 001 specification is issued per strain AND per grade. Cap Junky is on file "
     "at grades I, II and III; CJ082501/2 is grade IV. Grape Pie and Orange Punch Mimosa "
     "stop at IV and each has a grade V lot. Exactly one grade V specification exists in "
     "the whole issued set (Clemosa).",
     "The phenotype, chemotype, processing and packaging pills are left unticked and the "
     "band is marked, on 3 lots.",
     "May a lot cite the specification of its own strain at the nearest grade on file? "
     "The evidence says the attributes do not depend on grade: across 71 strains and 257 "
     "issued specifications, phenotype, dominance, chemotype, processing and packaging "
     "differ between grades of one strain in ZERO cases.",
     "spec_attributes_2026-09-10.csv; CJ082501/2, GP082501/2, OPM122501"),

    ("OI-02", "Specification", "marked",
     "Two certificates name a specification by potency band instead of grade",
     "GP052501 names QCSP_001_GP-THC18_v.01 and GRC102501/2 names QCSP_001_GRC-THC12_v.01. "
     "Neither exists in the issued set under any name — but QCSP_001_GP-IV_v.01 does, and "
     "IV is the grade GP052501 carries.",
     "Both pills are marked. No substitution was made without a ruling.",
     "Is the potency-band name an older convention for the same document? If so the desk "
     "joins on the grade and both resolve immediately.",
     "export_coq_artifact_data.py specification join; 2 lots"),

    ("OI-03", "Specification", "open",
     "Thirty-two lots have no grade, so no specification can be named at all",
     "The grade comes from product_specifications_QCSP001.json, built from the specification "
     "copies handed out with the tranches, which covers 48 of the 80 lots. For the other 32 "
     "the desk cannot compose a specification code, and the certificate names none.",
     "Nothing is printed and nothing is guessed.",
     "Where is the grade for the remaining 32 lots recorded? Once the desk has it, the "
     "specification code follows from the strain and the pills fill themselves.",
     "48 of 80 lots indexed; 68 of 164 certificate records carry no grade"),

    ("OI-04", "Result reading", "marked",
     "Four lots where which analyte the figure belongs to decides pass or fail",
     "The release certificates print the mycotoxin sub-parameters as one block and the desk "
     "maps the value to an analyte by its position in the block, not by a printed name. "
     "CLE072501, OPM092501, OPM1024_03 and OPM122501 report 2.1–2.2 µg/kg: as total "
     "aflatoxins (limit 4) they pass, as Aflatoxin B1 (limit 2) they fail.",
     "The figure is printed as the desk reads it and the lot is named here. None of the four "
     "may be signed until a person has read the page.",
     "Read the four certificates and confirm which analyte the figure belongs to.",
     "COQ_DRAFTING_2026-09-10.md; 4 lots"),

    ("OI-05", "Result reading", "open",
     "Nineteen lots print a Total Δ⁹-THC outside the range printed beside it",
     "The acceptance test was one-sided — it asked only whether a value exceeded its limit — "
     "so an assay BELOW its band was never flagged anywhere. Corpus-wide, 19 lots carry a "
     "potency outside the range on their own certificate, every one recorded as covered.",
     "The comparison now happens in the gap report, never on the certificate, and the report "
     "declines any criterion it cannot read as two numbers.",
     "Each of the 19 needs a disposition: re-read, re-test, or a regrade.",
     "status_of / the two-sided criterion; 19 lots"),

    ("OI-06", "Reconciliation", "open",
     "Forty-six disagreements between the desk and the owner's 09.09 pass",
     "Put side by side on the Reconciliation 09.09 sheet: 218 determinations agree, 46 do "
     "not. One is a loss on drying of 76.07 % read on GG1024 against a 12.0 % limit.",
     "None is resolved by the desk. Both readings are shown with their sources.",
     "A person reads the page for each of the 46 and says which reading stands.",
     "Reconciliation 09.09 sheet; 46 rows"),

    ("OI-07", "Issuance", "open",
     "Fifty-seven certificates of quality are dated on a Saturday",
     "06.06.2026, the blanket date for everything that would otherwise issue before the "
     "specification SOP, is a Saturday. The builder's own convention is that a controlled "
     "document issues on a working day.",
     "The owner's date outranks the desk's convention, so it is kept as given and the "
     "workbook carries a flag saying it was chosen deliberately.",
     "Confirm 06.06.2026, or name the working day it moves to (08.06.2026 is the Monday).",
     "issuance_schedule.COQ_BLANKET; 57 certificates"),

    ("OI-08", "Reference", "open",
     "Five result cells cite an SOP form number instead of a certificate",
     "NGP-QCG-SOP-024 F3, (28.11.2025) [NGP] carries Identification C, Total Δ⁹-THC, Total "
     "CBD, Total CBN and loss on drying for BSS052501 and GP062501 — including the banner "
     "assays 20.39 % and 24.89 %. A form number is not a document code and cannot be cited "
     "on a certificate of quality.",
     "The reference is printed as it stands and the lots are named here.",
     "Does the NGP laboratory issue a numbered report for this work? If not, these results "
     "need a different basis.",
     "2 lots, 10 result cells"),

    ("OI-09", "Reference", "open",
     "One laboratory report is on file twice, once per language",
     "10802_2845-2 EN and 10802_2845-2 MK are the same DFL report for BSS052501, cited as "
     "two documents, which is why that lot's certificate count reads one higher than the "
     "sheet's.",
     "Both are cited as the desk found them.",
     "Confirm the two files are one report, and which language version is the controlled copy.",
     "BSS052501; Batch Coverage Certificates (n)"),

    ("OI-10", "Batch identity", "open",
     "Three delivered lots have no cultivation batch recorded anywhere",
     "P160012, P160022 and P160032 carry full CNP results (ППК26117/18/19, 06.07.2026) and a "
     "P number in a series of their own, but no cultivation batch, and no row at all in the "
     "Head of QC's Batch Dates list — so no manufacturing date and no internal CoA basis.",
     "Each row now names its P number inside the label so the three are distinguishable and "
     "no join collapses them; the cultivation batch is left unrecorded rather than invented.",
     "What are the cultivation batches, manufacturing and packaging dates for the P1600xx "
     "series?",
     "3 lots; also absent from Batch Dates: JD112501＊"),

    ("OI-11", "Batch identity", "open",
     "One lot carries two P batches in a single cell",
     "GRC102501 is recorded against P060142 / P060182 in one cell, so its coverage row "
     "aggregates what are arguably two lots and its certificate count cannot reconcile.",
     "Left as the owner's tracker records it.",
     "Are these one lot packed into two P batches, or two lots sharing a cultivation batch? "
     "If two, they need two rows.",
     "GRC102501"),

    ("OI-12", "Batch identity", "open",
     "A lot and its ＊ sub-lot are credited from the same three documents",
     "JD112501 and JD112501＊ both cite ППК26065, 2365-2026 and 306-0550-26. On the parent "
     "those readings are marked on file, not credited; on the sub-lot they are credited. The "
     "sub-lot's microbiology block also carries the parent's round-1 values while its "
     "cannabinoids and metals come from round 2.",
     "Both rows are left as recorded and the pair is named here.",
     "Is JD112501＊ a distinct lot? If so, which round's microbiology belongs to it?",
     "JD112501 / JD112501＊"),

    ("OI-13", "Panel scope", "open",
     "Two optional test panels have never been exercised",
     "The pesticide panel offers a Ph. Eur. 2.8.13 option and a CUMCS-equivalency option, and "
     "none of the lots was tested to equivalency. The expanded microbiology option "
     "(P. aeruginosa, S. aureus) has never been run.",
     "Neither is claimed on any certificate.",
     "Should the certificates record that the option exists and was not exercised, or stay "
     "silent on it?",
     "Ph. Eur. 2.8.13; Ph. Eur. 2.6.13 expanded panel"),

    ("OI-14", "Document content", "open",
     "Three fields still print a specimen or a placeholder",
     "The two approvers' names are the master template's specimen. The potency acceptance "
     "range is a bracketed placeholder in both places it prints. Identification C is not yet "
     "cited from the cannabinoid-determination document the owner's ruling names.",
     "All three print bracketed in red and unticked, so no draft can be mistaken for issued.",
     "The approvers' names and titles; the potency range per grade; confirmation of the "
     "Identification C sourcing rule for the initial series.",
     "_CoQ_MASTER_Template.html; 22 drafts"),

    ("OI-15", "Method status", "open",
     "The pesticide acceptance criterion is stated as ≤ LOQ, which is not the Ph. Eur. test",
     "Ph. Eur. 2.8.13 sets a maximum per compound, not a limit of quantitation. OPM1024_02 "
     "shows why it matters: delta-HCH is reported at < 0.01 mg/kg against a maximum of 0.3, "
     "which conforms to the monograph and is not ≤ LOQ, and the column has no way to say so. "
     "The owner confirmed on 11.09.2026 that the reading itself is correct.",
     "The result is printed as the laboratory reports it.",
     "Restate the criterion as the Ph. Eur. maximum table, and say how a conforming "
     "detection should print beside 28 not-detected residues.",
     "IJZ 2994/2025, 19.06.2025, OPM 1024_02 (P050062); verdict on the page: ОДГОВАРА"),

    ("OI-16", "Result", "open",
     "One lot's foreign matter is reported by the laboratory as not conforming",
     "FB032601 prints 0.08 % (Не одговара) on ППК26127 of 21.07.2026. The figure passes the "
     "gravimetric ≤ 2.0 % limb, so CNP is failing it on another limb of Ph. Eur. 2.8.2 "
     "(leaf and stem size). The desk used to fold Не одговара to absent — a pass — because "
     "the phrase contains одговара; that is fixed and the lot now reads as out of "
     "specification.",
     "Flagged OOS. An out-of-specification result needs an investigation record.",
     "Confirm the non-conformity with CNP and open the deviation, or obtain a corrected "
     "certificate.",
     "FB032601; ППК26127, 21.07.2026 [CNP]"),

    ("OI-17", "Result", "open",
     "Five microbiological counts exceed the Ph. Eur. 5.1.4 band and four sit inside it",
     "Judged as the desk judges a counted limit — ≤ 10ⁿ against 2 × 10ⁿ — GG1024_01, "
     "OPM052501, GP052501, HPA052501 and CJ062501/2 are out of specification on TYMC; "
     "GG1024_02, HPA1024_01, GP0824_03 and CJ052501/01 are in the undetermined band.",
     "Printed red bold and amber bold respectively, and named in each lot's STATUS.",
     "Each out-of-specification count needs an investigation record; the four undetermined "
     "need a disposition.",
     "Ph. Eur. 5.1.4; 9 lots"),

    ("OI-18", "Document content", "open",
     "The same assertion prints bilingually on some certificates and in English on others",
     "Identification A and foreign matter print Conforms on 51 determinations and "
     "Conforms | Соодветствува on 12 — the certificate's own English | Macedonian pattern, "
     "applied to some cells and not others.",
     "Left as it stands: which form a bilingual certificate uses is a document-design "
     "decision, not a transcription one, so the desk did not impose a choice.",
     "Should every result print bilingually, or every result in English with the "
     "Macedonian only in the column headings?",
     "63 determinations across the 22 drafts"),

    ("OI-19", "Result", "open",
     "One ochratoxin result prints as a working note rather than a value",
     "2.06 — DETECTED, >LOQ on Ochratoxin A. The limit is 20 µg/kg so it conforms, but the "
     "cell carries the reader's note instead of the figure and its qualifier.",
     "Printed as the desk holds it.",
     "How should a conforming detection print — the figure alone, or the figure with a "
     "detected qualifier? The same question as OI-15 for pesticides.",
     "#10.3 Ochratoxin A, 1 determination"),

    ("OI-20", "Desk status", "open",
     "Nine result cells hold a desk status instead of a value",
     "not ingested (the document exists but has not been extracted into the eCoA database) "
     "on 5 cells, held for review (the two independent reads disagreed) on 3, and one "
     "Identification C awaiting a decision.",
     "Each is carried on the Work Order sheet with what it needs; none reaches a certificate.",
     "Nothing — these are desk work, listed so the count is visible.",
     "Work Order sheet"),
]

STATES = {"open", "marked", "ruled"}
HEAD = ("Ref", "Area", "State", "Item", "What was found", "What the desk did",
        "What is needed", "Evidence")


def items(state=None, area=None):
    """The register, optionally narrowed.

    >>> len(items())
    20
    >>> [i[0] for i in items(area="Specification")]
    ['OI-01', 'OI-02', 'OI-03']
    >>> sorted({i[2] for i in items()})
    ['marked', 'open']
    >>> all(len(i) == len(HEAD) for i in items())
    True
    >>> sorted({i[0] for i in items()}) == sorted([i[0] for i in items()])
    True
    """
    out = ITEMS
    if state:
        out = [i for i in out if i[2] == state]
    if area:
        out = [i for i in out if i[1] == area]
    return out


def markdown():
    """The register as the note that travels with the package."""
    lines = ["# Open items — awaiting the owner", "",
             "Every finding the desk has raised and cannot itself settle, with the evidence",
             "behind it and the decision being asked for. Built by `open_items.py`; the same",
             "register is the **Open Items** sheet of the workbook.", "",
             f"**{len(items('open'))} open · {len(items('marked'))} marked on the certificate**",
             ""]
    area = None
    for ref, ar, state, head, found, desk, asked, ev in ITEMS:
        if ar != area:
            area = ar
            lines += [f"## {ar}", ""]
        lines += [f"### {ref} · {head}", "",
                  f"*State:* **{state}** · *Evidence:* {ev}", "",
                  f"**Found.** {found}", "",
                  f"**The desk.** {desk}", "",
                  f"**Needed.** {asked}", ""]
    return "\n".join(lines)


def sheet(wb, index=None):
    """Write the Open Items sheet into an open workbook."""
    from openpyxl.styles import Alignment, Font, PatternFill
    name = "Open Items"
    if name in wb.sheetnames:
        wb.remove(wb[name])
    sh = wb.create_sheet(name, index if index is not None else len(wb.sheetnames))
    fill = {"open": "FFF2CC", "marked": "FCE4D6", "ruled": "E2EFDA"}
    for c, t in enumerate(HEAD, 1):
        cell = sh.cell(1, c, t)
        cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for r, row in enumerate(ITEMS, 2):
        for c, v in enumerate(row, 1):
            cell = sh.cell(r, c, v)
            cell.font = Font(name="Calibri", size=8, bold=(c <= 3))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if c == 3:
                cell.fill = PatternFill("solid", fgColor=fill.get(v, "FFFFFF"))
        sh.row_dimensions[r].height = 66
    for col, w in zip("ABCDEFGH", (7, 15, 9, 34, 52, 40, 44, 30)):
        sh.column_dimensions[col].width = w
    # the workbook's standing claim: every sheet prints landscape, fitted to width
    sh.page_setup.orientation = "landscape"
    sh.page_setup.fitToWidth = 1
    sh.page_setup.fitToHeight = 0
    sh.sheet_properties.pageSetUpPr.fitToPage = True
    sh.freeze_panes = "D2"
    sh.auto_filter.ref = f"A1:H{len(ITEMS) + 1}"
    return sh


if __name__ == "__main__":
    import doctest
    fail, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fail))
    if fail:
        sys.exit(1)
    if "--md" in sys.argv:
        p = os.path.join(HERE, "tracker", "OPEN_ITEMS.md")
        open(p, "w", encoding="utf-8").write(markdown() + "\n")
        print("wrote", p)
    import collections
    print("open items: %d (%d open, %d marked on the certificate)"
          % (len(ITEMS), len(items("open")), len(items("marked"))))
    for a, n in collections.Counter(i[1] for i in ITEMS).most_common():
        print("   %-16s %d" % (a, n))
    sys.exit(0)
