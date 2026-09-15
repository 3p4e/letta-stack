# Truth check of 15.09.2026 — results and cited documents

**Asked by the owner:** *"perform a truth check of the parameter results and doc eCoA code etc."*

**What was checked.** `tracker/truth_check_2026-09-15.py`, an independent code path (it imports
none of the desk's builders or verifiers), read the primary records — the release register with
the three intakes applied, the intake transcriptions and their second reads, the two-read corpus
of the eCoA database, the owner's 09.09 pass, the tracker instances — and compared, with its own
key and value normalisation, what every derived layer states: the export (the certificates'
rows), the tracker sheet of the recalculated workbook, the compiled drafts, the references table
and the CoQ Register. Where the records disagreed, the page was read a third time from the eCoA
database on 15.09.2026 (752/2025, 5/0008/26, 9/0012/26, 471/0862/25, 304/0548/26).

**What it found.**

1. **The tracker asserted ND for an analyte the laboratory never printed — 99 cells.** The
   owner's v8 tracker marks Aflatoxin B1 and Ochratoxin A `n.r.` on the IJZ release certificates
   and the desk folded that into ND under the ND ruling of 10.09.2026. The page of 752/2025 prints
   one mycotoxin line only (total aflatoxins < 2 µg/kg); the register says *not tested*; the
   corpus reads hold only the total. The mark is the owner's, not a laboratory's result. **Corrected
   in v32**: the cells read *not reported*, as the boundary ruled on 11.09.2026 requires; the
   certificates already omitted the line. The desk's document index no longer lists a column
   marked *not tested* as reported.
2. **Four microbiology cells where the owner's v8 value contradicts the page** — 5/0008/26 TAMC
   is 1 × 10² (not < 1 × 10²), 9/0012/26 bile-tolerant < 10 (not 10), 471/0862/25 TYMC < 10
   (not 10), 304/0548/26 bile-tolerant < 10² and > 10 (not < 10²). In all four the release register
   and the certificates were right. **Corrected in v32** from the page reads
   (`tracker/value_corrections_2026-09-15.json`).
3. **The tracker does not carry the 17 documents of the 09.09 pass that eleven certificates print
   from**, each resting on one page read — GG1024's loss on drying of 76.07 % above all. Recorded
   as **OI-35**; not changed.
4. **Four two-read corpus records passed the gate with their reads disagreeing on a comparator**,
   and the 09.09 pass table holds three Total THC values (197-13/7/6-К/26) that neither the
   register nor the two reads carry; nothing prints them. Recorded as **OI-36**; not changed.

**What it did not find.** No certificate row, tracker cell, draft, references-table cell or
register row prints a result, code, date or laboratory that a primary record contradicts, beyond
the four items above. The 94 intake certificates (220-М, 227-К, 220-К) match their register rows
and tracker instances on every result, date, laboratory and lot; the 89 with a second read agree
with it. Every one of the 73 compiled drafts prints the register's code, the export's date, the
superseded certificate, every result and every cited document as the export holds them.

**Residual findings on v32 (21):** the two open items above (T3, T5) and the two starred lots
whose register block carries no P lot (T1; OI-28). The generated report follows.

---

# Truth check of 15.09.2026 — results and cited documents

Built by `tracker/truth_check_2026-09-15.py` over the register with the intakes applied, the intake
transcriptions and their second reads, the two-read corpus, the tracker instances, the export,
the recalculated workbook (tracker and CoQ Register), the references table and every compiled draft.

## Comparisons

| check | count |
| --- | ---: |
| T0 second read's lot field holds no lot (label checked instead) | 12 |
| T0 two-read pairs | 89 |
| T0 two-read results | 64 |
| T1 intake certificates | 94 |
| T1 results | 282 |
| T2 instances | 94 |
| T2 results | 282 |
| T3 cited rows | 1866 |
| T3 column map entries | 17 |
| T3 results compared | 1557 |
| T4 results compared | 1414 |
| T4 tracker citations | 1964 |
| T5 certificates with no tracker lot | 15 |
| T5 rows | 1497 |
| T6 cited documents | 359 |
| T6 drafts | 73 |
| T6 results compared | 1497 |
| T7 cells | 1549 |
| T7 certificates | 161 |
| T8 numbered rows | 161 |

## Findings — 21

### T1 · register block is not the lot the certificate prints — 2

* 227-15-K/26: block JD012601 / , certificate JD012601 / P060312
* 227-21-K/26: block GG012601 / , certificate GG012601 / P060302

### T3 · the primary records disagree among themselves (#4) — 3

* HPA1024: 197-13-К/26 prints '17.31'; agrees with ['register row 358', 'corpus']; not with ["09.09 pass (one read) '19.68 %w/w'"]
* P060352: 197-7-К/26 prints '18.86'; agrees with ['register row 348', 'corpus']; not with ["09.09 pass (one read) '24.09 %w/w'"]
* P060332: 197-6-К/26 prints '17.67'; agrees with ['register row 345', 'corpus']; not with ["09.09 pass (one read) '23.29 %w/w'"]

### T3 · the primary records disagree among themselves (#5) — 1

* P060352: 197-7-К/26 prints '0.22'; agrees with ['register row 348', 'corpus']; not with ["09.09 pass (one read) '< LOQ %w/w'"]

### T3 · the primary records disagree among themselves (#6) — 1

* HPA1024: 197-13-К/26 prints '0.36'; agrees with ['register row 358', 'corpus']; not with ["09.09 pass (one read) '< LOQ %w/w'"]

### T3 · the primary records disagree among themselves (#9.1) — 2

* P060092: 5/0008/26 prints '1 × 10²'; agrees with ['register row 228']; not with ["corpus '< 1 x 10² CFU/g'"]
* P060092: 5/0008/26 prints '1 × 10²'; agrees with ['register row 228']; not with ["corpus '< 1 x 10² CFU/g'"]

### T5 · certificate cites a document the tracker does not cite for the lot (#5) — 1

* P060112: 031-2-K/26; tracker cites ['220/25/K/26']

### T5 · certificate cites a document the tracker does not cite for the lot (#6) — 1

* P060112: 031-2-K/26; tracker cites ['220/25/K/26']

### T5 · certificate cites a document the tracker does not cite for the lot (#8) — 10

* GG1024: ППК25008; tracker cites []
* P060112: 031-2-LoD/26; tracker cites []
* P060122: 031-5-LoD/26; tracker cites []
* P060132: 031-4-LoD/26; tracker cites []
* J31122501: 100-2-ГС/26; tracker cites ['100/2/K/26', '100/3/K/26']
* GG1024: ППК25008; tracker cites []
* P060112: 031-2-LoD/26; tracker cites []
* P060122: 031-5-LoD/26; tracker cites []
* P060132: 031-4-LoD/26; tracker cites []
* J31122501: 100-2-ГС/26; tracker cites ['100/2/K/26', '100/3/K/26']

