# The sweep intake of 21.09.2026

Owner, 21.09.2026: *"There will be no empty space in the certificate of quality nor the
certificate of analysis — all parameter results must be filled in."*

After the closed token set was restored, 485 cells on the face of the 172 certificates
carried a marker rather than a result. **176 of those are the owner's declared exception**
— #10.1 aflatoxin B1 and #10.3 ochratoxin A on the *initial* certificates, which the
release round never ran and the re-analysis campaign carries. That leaves **309 to hunt**.

Of those 309, this intake and the gap intake beside it have closed **37**. The residue is
**272 cells over 40 certificates**, set out certificate by certificate in
`../tracker/SWEEP_AND_SIGNED_PRINT_2026-09-21.md`; two of those rows are questions already
put to the laboratory (OI-63, OI-64) and the rest are lots for which no external
certificate exists in any record the desk holds.

## What this intake is

The audit of 20.09.2026 enumerated the owner's `eCoA_DATABASE` and held it against every
desk record. **Twenty-four laboratory scans are in no record at all** — not the ingested
corpus, not the release register, not the 09.09 resolution pass. Fifteen of them stand
behind a cell that prints a marker today:

| document | lot | fills |
|---|---|---|
| `75/0118/26` IJZ-MB | P060102 WED102501 | #9.1–9.5 |
| `76/0119/26` IJZ-MB | P060182 GRC102501 | #9.1–9.5 |
| `131/0228/26` IJZ-MB | P060202 J31112501 | #9.1–9.5 |
| `132/0229/26` IJZ-MB | P060162 SJ102501 | #9.1–9.5 |
| `137/0234/26` IJZ-MB | P060222 OPM112501 | #9.1–9.5 |
| `362/0692/26` IJZ-MB | P060342 SCR012601＊ | #9.1–9.5 |
| `403/0786/26` IJZ-MB | P060442 SCR022601 | #9.1–9.5 |
| `407/0790/26` IJZ-MB | P060392 FB012603V | #9.1–9.5 |
| `408/0791/26` IJZ-MB | P060432 FB012603 | #9.1–9.5 |
| `434/0848/26` IJZ-MB | P060452 FB032601 | #9.1–9.5 (second panel) |
| `475/0927/26` IJZ-MB | P050022 GP0824-02 | #9.1–9.5 |
| `031-1-К/26` Farmahem | P060182 GRC102501 | #3, #4, #5, #6 |
| `031-1-ГС/26` Farmahem | P060182 GRC102501 | #8 |
| `328/2026` IJZ | P060182 GRC102501 | #10.2, #11.1–11.4, #12 |
| `227-18-М/26` Farmahem | P050202 GP062501 | #10.1, #10.3 |

The four GRC102501 documents together close a lot that prints 22 markers today — the
cannabinoids, loss on drying, microbiology and the whole contaminant panel, all on file
and none of it read.

## The gate

The same one, unchanged in doctrine: two vendors' models read each rendered page without
seeing the other's answer, a value is taken only where both wrote it, and anything they
differ on is held until a third read of the page settles it and records the region it was
cut from.

    documents read twice      15
    values agreed             98
    settled by a third read    6
    held                       0
    read ONCE, not applied     0

Ten were read by two vendors. For the other five — `403/0786/26`, `408/0791/26`,
`434/0848/26`, `475/0927/26` and `76/0119/26` — Google's free tier retired a key mid-run,
one of them answered *"reported as leaked"*, and no second VENDOR read was available. The
desk read those five itself at 300 dpi, as it did on 16.09 and 18.09, before looking at
read A's answer for them.

**That desk pass was then found wanting, by the desk.** Its crops covered the parameter
table and the letter line but NOT the lab-number line or the signature block, and it had
filled `cert_code`, `batch_canonical` and `date_of_issue` from the **file name**. A file
name is not a page. The header and footer were re-cut and read, and every one of those
fields is now a reading — each recorded in `reads_B.json` under `header_read`, with its
crop region and what it was before:

| document | certificate | Серија | issued | Дата на прием |
|---|---|---|---|---|
| `403/0786/26` | 403/0786/26 | SCR022601 | 24.06.2026 | 18.06.2026 |
| `408/0791/26` | 408/0791/26 | FB012603 | 24.06.2026 | 18.06.2026 |
| `434/0848/26` | 434/0848/26 | FB032601 | 10.07.2026 | 02.07.2026 |
| `475/0927/26` | 475/0927/26 | **P050022** | 04.08.2026 | 28.07.2026 |
| `76/0119/26` | 76/0119/26 | GRC102501 | 09.02.2026 | **02.02.2025** |

One field changed on the reading: `475/0927/26` prints **`Серија: P050022`**, not the
cultivation batch `GP0824-02` the file name carries. The rest confirmed what the first
pass had assumed — which is not the same as having read it, and is why it was re-read.

**What the gate learned.** Sixty-one of the first pass's holds were about nothing: the two
vendors file the Institute's 29 residues under different normalised keys while transcribing
the same printed names and the same results. The gate now indexes a row by the name the
PAGE prints, drops rows with no result in either read, folds a bilingual label to its first
half, and — for identity only, never for a value — folds Cyrillic homoglyphs and
transliteration. Four real disagreements remained and each was settled on a crop:

* `131/0228/26` and `132/0229/26`, bile-tolerant — read A gave `< 10^1`, the page says
  `< 10² и >10 CFU/g`. **The fuller read was right again**, the sixth and seventh instance
  of the OI-36 class.
* `328/2026`, two residue labels — the page prints `vkupno DDT` and `endosulfan sulfat`,
  so read A had silently rendered a transliteration back into Cyrillic and corrected the
  laboratory's spelling. That is what the desk's own rule forbids.
* `227-18-М/26`, the lot — the page prints `P05022`, six digits where a production lot has
  seven. Settled to **P050202** on five independent lines, set out in `reads_C.json`. This
  is the one certificate of its thirty that **neither reader could extract on 16.09.2026**;
  both read it today.

## Applied

`../apply_sweep_2026-09-21.py` — **37 cells on 8 certificates**, 27 already-printed values
independently confirmed, **0 disagreements**, and 83 cells left alone because ANOTHER
document already covers them.

The last ten came out of the header re-read. `CoQ-PP_26-079` (FB012603, Fat Bastard) and
`CoQ-PP_26-080` (SCR022601, Scrambler) printed *"not tested — no certificate covers it"*
for the whole microbiology panel while `408/0791/26` and `403/0786/26` sat on Drive. Both
panels are complete now.

Four things it declined to do:

* **`434/0848/26` is not applied to either lot** — OI-64. The page prints *Примерок за
  тестирање: Сув цвет од медицински канабис **Gorilla Glue**, 33,34 g* and, two lines
  below, *Серија: **FB032601***. FB is this record's Fat Bastard prefix and GG its Gorilla
  Glue one; both lots exist. `433/0847/26` — the preceding number, same day, same
  manufacturer — names Fat Bastard, carries FB032601 and already fills that panel on
  CoQ-PP_26-081 with **different counts**, so the two reports are two samples rather than
  one report twice. CoQ-PP_26-082, the Gorilla Glue lot, is the one of the pair with an
  empty panel. Which lot the page certifies is the laboratory's to say.

* **`CoQ-PP_26-026` does not cite `227-18-М/26`.** A re-analysis document is a retest
  document whatever its code says, and that release certificate issued on 06.06.2026 —
  three months before the page exists. The reissue takes it, and with it the owner's
  account of the mycotoxin exception becomes literally true: aflatoxin B1 and ochratoxin A
  are on the retest, not the release.
* **Two TYMC values are not "covered".** `1.1 × 10⁴` and `1.6 × 10⁴ CFU/g` sit between the
  literal power of ten and twice it, which Ph. Eur. 5.1.4 makes UNDETERMINED rather than
  conforming. The apply now judges every value against its own criterion through the same
  validator the schedule uses, rather than passing it as covered.
* **`75/0118/26` is not applied at all** — OI-63. Both vendors read its bile-tolerant line
  faithfully and the PAGE is malformed: `< 10³ и 10² CFU/g`, with no `>`. A panel is one
  determination on one sample and prints whole or not at all, so the four sound values are
  held with the fifth rather than printing four fifths of a panel.

One repair came out of it. `CoQ-PP_26-149` raised "param credited twice: 10" the moment
Farmahem carried its aflatoxin B1 and ochratoxin A while the Institute still carried the
total aflatoxins. The design system states the rule (`rules-coq-compile.html`, rule 5) and
the builder did not implement it: a determination family that splits across two
laboratories **stays dotted on both rows**. It now does — IPH takes `10.2`, Farmahem takes
`10.1, 10.3`, and nothing is credited twice.

## Files

    drive_ids.json         the fifteen documents, their Drive ids, lot and laboratory
    two_reads.py           the two vendor reads
    reads_A.json           read A, OpenAI
    reads_B.json           read B — Google for ten, the desk at 300 dpi for five,
                           each of the five carrying header_read: what the lab-number
                           line and the signature block print, and the crop it came from
    reads_C.json           the desk's third reads, each with the region it was cut from
    reconcile.py           the gate
    two_read_result.json   its record
    ../apply_sweep_2026-09-21.py   the application, idempotent, --dry-run
