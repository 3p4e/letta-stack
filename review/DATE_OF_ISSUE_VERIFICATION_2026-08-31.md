# The dates of issue — 266 register dates, checked

Until now nothing had touched this column. All 266 dates were unverified, and reading
266 documents to check them was the reason.

## The shortcut that made it affordable

The certificate folder names every file `<batch>_<code>, <DD.MM.YYYY>_<lab>.pdf`. That
date is **not** the document — but it is an independent transcription of it. Nobody
copied it from the register.

Comparing all 266 register dates against it:

| | |
|---|---|
| Checkable against a filename | **231** |
| Agree | **215** |
| Disagree | **16** |
| No file to check against | 35 |

So 215 dates agree with a source the register did not produce, and only 16 needed a page
opened. Every one of those 16 was then read off its certificate — no correction here
rests on a filename.

## Three kinds of defect

### 1. The wrong date field — 2 rows

These IPH certificates print **two** dates: `Дата на прием` in the head, and
`Дата: ... година` above the signatures. The column is labelled *Date of issue* and holds
the receipt date.

| Row | Certificate | Page: receipt | Page: issue | Register held |
|---|---|---|---|---|
| 43 | `588/1067/25` | 13.06.2025 | **18.06.2025** | `13.06.2025` |
| 126 | `1219/2170/25` | 26.11.2025 | **01.12.2025** | `26.11.2025` |

Right document, wrong field. That is the third time this week the same shape has turned
up — the Farmahem U-column, the register's heavy-metal limits, and now this. **None of
these is a misread character, and none is visible to a range check.** They are all
"correct value, wrong column", and only reading the label next to the number catches
them.

### 2. Prose where a date belongs — 8 rows

`Completed Nov-Dec 2025`, `Issued ~Dec 2025`, `Issued Dec 2025` — placeholders that were
never resolved, sitting in a released register. All eight documents were read:

| Rows | Certificates | Page prints |
|---|---|---|
| 128, 132, 136, 140 | `ППК25378`–`ППК25381` | `Скопје, 12.12.2025 год.` |
| 130, 134, 138, 142 | `1226`–`1229/2192–2195/25` | `Дата: 05.12.2025 година` |

### 3. Scaffolding left in — 1 row

Row 185 held `20.01.2026 [see source]`. The date was right; the note was not meant to
ship.

All eleven applied by `deliverables/qc_gap_analysis/apply_date_corrections.py`. Eleven
cells changed, nothing else: 268 hyperlinks, all merged ranges and all amber flags
identical before and after.

## Not corrected, deliberately — 5 rows

Rows 123, 127, 131, 135 and 139 hold `21.01.2026` against a code cell naming **two**
documents: `PP CoA #027 / ППК25370`. The CNP certificate is dated 28.11.2025 or
12.12.2025; `21.01.2026` is plausibly the in-house CoA's own date, and the row is
plausibly about the in-house CoA.

The cell cannot be corrected without first deciding which document the row is for. That
is a QC decision, not a transcription fix, and it is the same underlying problem as the
`QCCoA 001` replacement already on the list.

## The 35 that cannot be checked this way

Rows whose certificate has no file in the folder map — the in-house `PP CoA #nnn`
releases, the cross-checks, and the rows carrying no certificate code at all. They are
the same 59 rows whose PDF links cannot be repaired, for the same reason.

## What this does and does not establish

It establishes that **226 of 266 dates are now supported by a source outside the
register** — 215 by an independent filename transcription, 11 by a page read.

It does not establish that the 215 are right. A filename and a register cell can be wrong
together if both were typed from the same mistaken note. What the check does is bound the
problem: any date that disagrees with the folder has been found and read, and the class of
error that produced rows 43 and 126 — reading the receipt date instead of the issue date —
would show up as a disagreement wherever it recurred, because the folder is named from the
issue date. It did not recur.
