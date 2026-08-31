# The Farmahem certificates, read off their own pages

**Scope:** 63 Farmahem reports behind 63 register rows and 189 values, none previously
checked against a document. **All 31 cannabinoid reports are read and corrected; the 22
mycotoxin and 10 loss-on-drying reports remain.** All 63 are downloaded and rendered.

| Suffix | Reports | Register columns | State |
|---|---|---|---|
| `К` / `K` | 31 | THC %, CBD %, CBN % | **read, corrected** |
| `М` | 22 | Aflatoxins Σ, Aflatoxin B1, Ochratoxin A | rendered, not read |
| `GS` / `ГС` | 10 | Loss on drying % | rendered, not read |

## Result — the cannabinoid reports

| | |
|---|---|
| Reports read | **31 of 31** |
| Register values compared | 93 |
| Agreement | **89 — 95.7%** |
| Defects | **4, across 3 rows** |

## Every defect is the same mistake wearing a different hat

Each report prints one table: `Име на компонента | Кратенка | Резултат [%w/w] |
U [%w/w]`, three rows — CBD, CBN, Δ9-THC. So beside every result sits its own
uncertainty, and directly above or below sits another component's result. **Three of the
four ways to pick the wrong cell have actually happened.**

| Row | Certificate | Register held | Page prints | What went wrong |
|---|---|---|---|---|
| 9 | `197-1-К/26` BG1024 | CBN `0.02` | CBN **`0.28`**, U `0.02` | took the **U column** |
| 276 | `197-7-К/26` P060352 | CBD `<LOQ`, CBN `0.22` | CBD **`0.22`**, CBN **`< LOQ`** | the **two rows swapped** |
| 286 | `197-13-К/26` HPA1024 | CBN `N.D.` | CBN **`0.36`** | a result recorded as **not detected** |

Each was confirmed at 2.6× magnification before being called.

**Δ9-THC is correct on all 31 reports.** That is the striking part. The
release-critical parameter — the one everybody checks — is perfect. All four defects sit
in the CBD/CBN pair: the two minor cannabinoids, adjacent to each other and to the
uncertainty column, in a place where any number looks plausible whatever cell it came
from.

No range check can see any of this. Every wrong value is inside the plausible range for
the parameter it was entered against. Only reading the column header catches it, which
is the argument for a typed extraction record — value, unit, limit and *source column*
in one object — rather than a chunk of prose.

**Row 286 is the one a reviewer should care about.** `N.D.` is not a small number; it is
a statement that the laboratory looked and found nothing. It reported 0.36 %. That is a
difference in kind, not degree.

Applied by `deliverables/qc_gap_analysis/apply_farmahem_corrections.py` — four cells,
nothing else touched: 268 hyperlinks, all merged ranges and all amber flags identical
before and after.

## Two things that are not defects

**`<LOQ` versus `< LOQ (<0.20)`.** The 051 and 100 series print `<LOQ**` with their own
footnote `<LOQ** - под лимит на квантификација (<0.20%)`. The register expands that
footnote inline. It is *more* informative than the page, not less, and treating it as a
difference would have buried the four that matter — which is why
`compare_farmahem_reads.py` normalises it explicitly rather than silently.

**A batch serial that disagrees with itself, resolved.** The IPH pass found `1628/2026`
printing `J311122501` where its sibling `1625/2026` printed `J31122501`. Farmahem's
`100-2-К/26` and `100-3-К/26` — the same batch, the hand-trimmed and trimmed samples —
both print **`J31122501`**, and so does the register. The extra digit is an outlier on
that one IJZ document.

## Method

The Drive download lands on disk and never enters context. Pages render at 200 DPI;
page 1 is the cover, page 2 carries both the sample table — client name, batch, and the
laboratory's own internal number `CF-nnn/26` — and the result table, so the page read
names its own certificate.

**These are scans.** `pdftotext` returns zero characters on every one of the 63, so the
render is the only admissible source. Worth stating plainly, because this series was
extracted "verbatim" in an earlier task — from the RAG corpus, not from the paper.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.

## Still to read

22 mycotoxin reports (`197-n-М/26`, `276-31-М/25`) and 10 loss-on-drying reports
(`051-n-GS/26`, `100-n-ГС/26`) — 96 register values. All rendered; continuing costs only
the reads.
