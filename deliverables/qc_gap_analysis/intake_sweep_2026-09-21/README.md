# The sweep intake of 21.09.2026

Owner, 21.09.2026: *"There will be no empty space in the certificate of quality nor the
certificate of analysis — all parameter results must be filled in."*

After the closed token set was restored, 485 cells on the face of the 172 certificates
carried a marker rather than a result. **176 of those are the owner's declared exception**
— #10.1 aflatoxin B1 and #10.3 ochratoxin A on the *initial* certificates, which the
release round never ran and the re-analysis campaign carries. That leaves **309 to hunt**.

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

    documents read twice      10
    values agreed             73
    settled by a third read    4
    held                       0
    read ONCE, not applied     5

Five carry one read only: Google's free tier retired a key mid-run and answered 403 for
`403/0786/26`, `408/0791/26`, `434/0848/26`, `475/0927/26` and `76/0119/26`. One read is
not a reading, so they wait for the second.

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

`../apply_sweep_2026-09-21.py` — **27 cells on 6 certificates**, 48 already-printed values
independently confirmed, **0 disagreements**.

Three things it declined to do:

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
    reads_B.json           read B, Google — ten of fifteen
    reads_C.json           the desk's third reads, each with the region it was cut from
    reconcile.py           the gate
    two_read_result.json   its record
    ../apply_sweep_2026-09-21.py   the application, idempotent, --dry-run
