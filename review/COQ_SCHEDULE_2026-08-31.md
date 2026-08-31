# Every CoQ filled in: 61 certificates, 23 determinations each, and the document behind every value

31.08.2026 · the CoQ issuance schedule, rebuilt on the owner's own issue plan and filled
from the release register.

---

## The CoQ universe is the owner's, and it is 61, not 102

The `ISSUE_COQ` folder in Drive (`Final_Docs/xCOAs/CoX_DES/ISSUE_COQ`) holds the approved
CoQ master template, **48 rendered initial-release CoQs** and an issue plan generated from
`PP_Potency_MASTER_Spec.xlsx`. Its conventions — now committed as
`deliverables/qc_gap_analysis/ISSUE_COQ_CONVENTIONS.md`, with the plan verbatim as
`coq_issue_plan.json`:

* **One CoQ per packaged lot**, numbered `CoQ-PP-{year}-{NNNN}` sequentially by packaging
  date — `CoQ-PP-2025-0001…0022`, `CoQ-PP-2026-0001…0026`.
* **13 additional-testing CoQs**, `CoQ-PP-2026-0027…0039`, for the lots whose 12-month
  retest fell due. Ordinary sequential numbers; *a CoQ is never labelled "retest"*.
* Every CoQ prints an **`iCoA-PP-{year}-{NNNN}`** reference and the lot's grade acceptance
  range; the banner potency is the actual assay, not the nominal.
* Results the master spec does not hold are **controlled blanks**: *a CoQ must never carry
  a result or a conformity assertion that has not been certified.*

This closes the packaged-lot question three registers carried as open: register batches
with no packaged lot get **no CoQ** — there are 41 of them, and among them sit
**OPM052501 and CJ062501-2, both carrying a TYMC over its acceptance criterion** with no
CoQ to hold the finding.

## What was built

**`PP_CoQ_Parameter_Schedule_2026-08-31.xlsx`** (`build_coq_schedule.py`) — five sheets:

1. **CoQ Parameter Schedule** — 61 × 23 = 1 403 rows: parameter, method and acceptance
   criterion verbatim from QCSP 001 v.03, result, source document code, date, institution,
   status, and the routing for what remains. This is the transcription source for the
   controlled blanks on every CoQ.
2. **CoQ Coverage** — one row per CoQ: number, iCoA reference, banner THC, acceptance
   range, coverage counts, every document the certificate must cite.
3. **iCoA Plan** — the 103 in-house certificates the routing requires.
4. **Sourcing routes** — who *can* perform identity and foreign matter, and who *will*.
5. **QCSP 001 v.03** — the 23 determinations, verbatim.

The registers workbook's **CoQ Issuance** sheet now carries the same 61, from the same
computation, so the two cannot drift.

## The routing (owner's decision, 31.08.2026)

| Determination | At initial release, where no outsourced lab covered it | At retest |
|---|---|---|
| Ident A + B | **Purely Plant laboratory — one iCoA** | Farmahem, with the assay |
| Ident C | outside laboratory (CNP Ident C only, or Farmahem) | Farmahem, with the assay |
| Foreign matter | **Purely Plant laboratory — a second, separate iCoA** | Purely Plant laboratory — one iCoA |

Constraints that shape it: CNP does not sell foreign matter separately — it comes only
inside the full identity-plus-assay package — and the in-house laboratory cannot perform
Ident C. Twelve batches already have Ident A, B and foreign matter **covered by their CNP
Ph. Eur. 11.5 certificate** (the iCoA register's own `covered by CNP` fields, which an
earlier draft of the builder ignored); only Ident C is outstanding there.

Under the routing: **69 × {Ident A+B} + 90 × {foreign matter} in-house certificates over
the old 102-CoQ basis; 45 + 58 = 103 over the plan's 61 CoQs.**

## The counts, over the 61 CoQs of the plan

| | rows |
|---|---|
| covered by a certificate on file | 500 |
| still to be performed — routed | 232 |
| not tested by anyone | 347 |
| additional testing owed — no post-release certificate yet | 173 |
| upon request (P. aeruginosa, S. aureus) | 122 |
| **in-house CoA only — underlying eCoA NOT on file** | **18** |
| laboratory finding recorded, conforming | 5 |
| OUT OF SPECIFICATION | 3 |
| UNDETERMINED — pending the QCSP 001 reading | 3 |
| BLOCKED — declared out of specification | 1 |

## GG1024, and nine lots like it

`GG1024` (CoQ-PP-2025-0003 and 0029) is in the schedule **with every value it has** —
taken from the in-house CoA transcription, whose own footnote attributes the testing to
accredited laboratories — and every one flagged red: **not one underlying eCoA is on
file. Locate the physical certificates, scan, upload.** Nine further lots' cultivation
batches are in the same state (OMP1024_01¹, PUM102501, ACC102501, CF102501, FB012601/1,
JD012603/01, FB012602, CC012603, SCR012603 — the last five also absent from the register
entirely).

¹ OMP1024_01 resolves: the register's own P-number column shows its `OPM1024_01` block IS
lot P050042 — one transposition, on the master spec. Aliased with that evidence.

## Recorded, not resolved

1. **26 lots' banner THC matches no register assay** — the master spec carries analyses
   (the T2 re-analysis round among them) whose certificates the eCoA register has never
   received. Same class as GG1024: certificates to locate and file.
2. **35 lots' grade range disagrees with the signed QCSP 001 PDF** beyond the endpoint
   convention — two owner documents, two grade designs. The plan drives the CoQs; the
   disagreement is flagged per lot.
3. **192 rows cite a document dated after the CoQ's issue date** — the plan dates initial
   CoQs at packaging, and testing routinely finished later. The printed issue date must
   be no earlier than the newest cited document; QC sets it at issue.
4. **Identification C has still never been performed by anyone**, on any lot: 60 of 61
   CoQs owe it (the 61st is blocked).
5. Aflatoxin B1 and Ochratoxin A are certified separately only by Farmahem's `197-*-М`
   and `276-31-М/25`; the IPH `nnnn/yyyy` series reports the aflatoxin sum alone.

6. **`CoQ-PP-2026-0005` is assigned twice**: to GP0824_01 / P050102 in the older
   `deliverables/qc_register/` deliverable, and to P060062 (Permanent Marker) in the
   owner's plan — whose rendered document exists. The plan governs; the older
   deliverable's CoQ numbers are superseded and must not be issued.
7. **The rendered CoQ merges QCSP 001 items 1 and 2** into one appearance row — its
   analytical table has ten §01 rows against the specification's twelve. The schedule
   keys on the specification; transcription onto the form carries 1 and 2 together.

Ochratoxin A's acceptance criterion, incidentally, is settled by QCSP 001: **≤ 20 µg/kg**
— so the register's amber `2.06 — DETECTED, >LOQ` conforms with room to spare, and the
"per PP spec" column finally has its number.

An adversarial verification workflow ran over the whole build (5 agents, glyph-level
reads of all 48 specification PDFs with `pdftotext -bbox`): section 02 is one document
in 48 files with zero content differences; the `10⁵`/`10⁴` superscripts, the aflatoxin
subscripts and the µ/∑/– codepoints are confirmed from glyph baselines; and every source
rule this build implements was independently restated from the repository. Its two
genuinely new findings are items 6 and 7 above.
