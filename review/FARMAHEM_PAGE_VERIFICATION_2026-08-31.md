# The Farmahem certificates, read off their own pages — in progress

**Scope:** 63 Farmahem reports behind 63 register rows and 189 values, none previously
checked against a document. **9 read, 54 to go.** All 63 are downloaded and rendered.

The family splits three ways by the suffix on the report number:

| Suffix | Reports | Register columns |
|---|---|---|
| `К` / `K` | 31 | THC %, CBD %, CBN % |
| `М` | 22 | Aflatoxins Σ, Aflatoxin B1, Ochratoxin A |
| `GS` / `ГС` | 10 | Loss on drying % |

## The finding that makes this family worth reading carefully

Every Farmahem cannabinoid report puts the result and its measurement uncertainty in
**adjacent numeric columns**:

| Име на компонента | Кратенка | Резултат [%w/w] | U [%w/w] |
|---|---|---|---|
| Вкупен Cannabinol | Total CBN | **0.28** | 0.02 |

Row 9 of the register (`197-1-К/26`, BG1024) holds **`0.02`** for CBN. That is not a
misread digit and not a transposition — **it is the uncertainty column**. Confirmed at
2.6× magnification.

The number is small and the parameter is not release-critical, so nothing about
BG1024's disposition changes. What matters is the shape of the mistake: it is
available on all 31 cannabinoid reports, silent, and produces a value that looks
entirely plausible. A range check would not catch it; only reading the column headers
does.

Of the nine read so far, one row took the U column and eight are correct — including
two, `197-9-К/26` and `197-11-К/26`, that carry a real CBN result (0.20 and 0.23) and
transcribe it correctly. So this is not a systematic rule being applied wrongly; it is
a single slip in a place where slips are easy and invisible.

## Result so far

| | |
|---|---|
| Certificates read | **9 of 63** |
| Register values compared | 27 |
| Agreement | **26** |
| Differences | 1 — row 9 CBN |

No correction has been applied yet. The whole family will be corrected in one pass
once all 31 cannabinoid reports are read, so that a single script carries every row
the U-column check turns up rather than the workbook gaining a revision per finding.

## Method

Same as the IPH pass: the Drive download lands on disk and never enters context; pages
render at 200 DPI; page 1 is the cover carrying the report number and date of issue,
page 2 the sample table and the result table. Page 2 is read because that is where
both the sample identity (client name plus batch, and the laboratory's own internal
number `CF-nnn/26`) and the results sit, so the crop names its own certificate.

These are scans: `pdftotext` returns **zero characters** on every one of them, so the
render is the only admissible source. That is worth recording because the Farmahem
series was extracted "verbatim" in an earlier task — from the RAG corpus, not from the
paper.

Classical OCR is not used and is forbidden by `scripts/policy_check.py` rule 1.
