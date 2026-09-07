# Auditing the register's links: does each row open its own certificate?

`repair_register_pdf_links.py` pointed every row at a file by matching its certificate code
against the Drive filename. This is the check in the other direction: take the file id a cell
**actually links to**, look up what document that is, and ask whether it is the document the
row claims.

That direction is the one that matters, and the repair script's own docstring said why:

> A dead link fails visibly, and someone eventually notices. A live link to the wrong
> laboratory's certificate does not: it opens a real document with real numbers on it, and
> nothing about it says it belongs to a different row.

The audit is also worth more now than it would have been a day ago. 275 of these files have
since been opened and read, so the link is no longer being checked against a folder listing —
it is being checked against documents whose contents are on record in
`review/*_page_reads_*.json`.

## Result

| | Before | After |
|---|---|---|
| Rows with a certificate code | 267 | 267 |
| **Link opens this row's document** | 225 | **246** |
| **Link opens a different document** | **0** | **0** |
| Link points at a file not in the map | 25 | 4 |
| No link at all | 17 | 17 |

**Not one row opened the wrong certificate, before or after.** The serious defect the repair
script existed to fix is gone and stayed gone. What remained was 21 rows linking to a file id
that is in no map — and every one of those ids is **dead**: `get_file_metadata` returns
*Requested entity was not found* for all 17 distinct ids among them.

---

## The 20 in-house CoAs were never missing, they were named differently

| Register | Drive filename |
|---|---|
| `PP CoA #016` | `P050202_QCCoA 001v02, 04.12.2025_PP.pdf` |
| `PP CoA #028` | `P050212_QCCoA 001v02, 21.01.2026_PP.pdf` |

`repair_register_pdf_links.py` left these alone because it matches on the certificate code, and
here **the code cannot match by design**. The register numbers each in-house CoA individually;
Drive names them all for the *form*. `QCCoA 001v02` is not a document identifier — 26 files
share it. The distinguishing key is the P-number, carried as the filename's prefix and in the
register's column C.

So the repair script's *fallback* key is the only key that works here, and its primary key
never had a chance. All 26 files had been sitting in the committed map the whole time.

### The documents prove the match themselves

Matching on a P-number is an inference, so four of the documents were opened. Each prints its
own **Certificate number** in the head:

| File | Page prints | Register row |
|---|---|---|
| `P050202_QCCoA 001v02` | `Certificate number: 016`, Grape Pie, `Batch No: P050202` | r89 `PP CoA #016` |
| `P050212_QCCoA 001v02` | `Certificate number: 028`, Cap Junkie, `P050212` | r98 `PP CoA #028` |
| `P060052_QCCoA 001v02` | `Certificate number: 037`, Apple and Banana, `P060052` | r163/164 `PP CoA #037` |
| `P060092_QCCoA 001v02` | `Certificate number: 033`, Grape Pie, `P060092` | r182/183 `PP CoA #033` |

The document's own content names the register's code. That is stronger evidence than the
filename match used everywhere else in this repository — and it is available only because the
files were opened rather than listed.

## And one certificate that was ambiguous for want of a P-number

Row 109, the State Phytosanitary pesticide report `10802_2845/2`, kept a dead link through the
whole repair. Its code resolves cleanly to exactly two files — the Macedonian original and its
English translation — and the MK-preference rule would have picked the right one. But that rule
only runs after the P-number narrows the pair, and **row 109 has no P-number**: it is a
continuation row, and the register writes each batch's identity once and leaves columns A–C
blank beneath it.

Its block header, row 107, carries `P050192` — which is the file's own prefix, and matches
`Blue Sunset Sherbet BSS 052501` the document names as its sample.

That is a general gap, not one row's bad luck: any code issued for more than one batch was
being abandoned on every continuation row rather than resolved. `repair_register_pdf_links.py`
now walks up to the block header for its disambiguation key, and reports **zero ambiguous rows**
where it previously gave up.

## An audit that flags its own repair is worse than no audit

The first run after relinking reported all 20 in-house rows as **MISDIRECTED**, because the
audit knew only the code rule. The links were right and the audit was wrong.

That is not a cosmetic problem. A permanent block of 20 known-false alarms in a 267-row report
is exactly where a real misdirection goes unnoticed — a reader learns to skim past the block,
and the twenty-first entry is never read. The audit now applies the P-number rule for
form-numbered in-house CoAs, and the misdirected count is a true zero rather than a number
somebody has to remember to discount.

---

## One date corrected, two that a document cannot settle

Fifteen of the nineteen P-numbered in-house rows carry a date identical to their file's. Four
do not.

**Row 182 held `20.02.2020 [see source]`.** February 2020 is impossible for this document: the
certificate prints `Manufacturing date: December 2025` and `Retest date: July 2026`. 20.02.2026
is corroborated three ways — the filename, all seven sibling `P0600xx` rows, and the
manufacturing and retest months on the page — and the bracketed note is the same scaffolding
`apply_date_corrections.py` stripped from row 185. Corrected.

**Rows 89 and 98 are left, and this is the interesting part.** Row 89 holds `04.10.2025`
against a filename saying `04.12.2025`; row 98 holds `24.01.2026` against `21.01.2026`. Both
look like exactly the kind of single-digit slip this campaign has corrected a dozen times.

**The QCCoA form prints no date of issue at all.** Certificate number, strain, batch,
manufacturing month, retest month — and nothing else. The pages were rendered and checked;
there is nothing there to read.

So the filename is the only outside evidence, and a filename is not a document. It was good
enough to *corroborate* 215 dates in the 31.08 date pass and good enough to *flag* these two,
but correcting a release register from a file listing while the document itself is silent
would be precisely the substitution — a value taken from the nearest available source rather
than the right one — that these four passes have spent their time catching. Both rows carry a
comment saying so.

## A correction to yesterday's account of the two-document rows

`review/RESIDUAL_PAGE_VERIFICATION_2026-08-31.md` said the six `PP CoA #nnn / ППКnnnnn` rows
each sit above a bare `ППКnnnnn` row and that "the pattern holds on all six pairs". **It holds
on five.** Block 37 has three rows:

| Row | Code | Date | Values |
|---|---|---|---|
| 163 | `PP CoA #037 / ППК26005` | 21.01.2026 | 4 |
| 164 | `PP CoA #037` | 20.02.2026 | 0 |
| 165 | `ППК26005` | 21.01.2026 | 0 |

Both documents already have a row of their own, so the combined cell on row 163 is redundant,
and its date is `ППК26005`'s while `PP CoA #037`'s own row correctly holds the 20.02.2026 its
file confirms. No value is wrong; which row should carry the batch's results is a structural
question for QC.

---

## What still has no link

| Rows | | Why |
|---|---|---|
| 17 | code `(not numbered)` | in-house documents the register never gave a code |
| 2 | `In-house HPLC / GC cross-check` (r90, r108) | dead ids, and no such document in the certificate folder |
| 2 | `n/a — Purely Plant in-house CoA` (r285, r288) | the cell links to a Drive **folder**, not a file |

The last four are the same four rows that hold the only 40 result cells still unverified. They
are consistent: a row with no external document has no external link either.
