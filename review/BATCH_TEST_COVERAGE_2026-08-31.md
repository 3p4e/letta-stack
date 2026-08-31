# What testing does each batch actually have? The register is organised so you cannot see.

The register holds one row per certificate, grouped into a block per batch. That answers
*what does this certificate say* very well. It answers *is this batch fully tested* not at all,
because the answer is the **shape** of a block — how many rows it has and from which
laboratories — and a shape is not something a column can hold.

`deliverables/qc_gap_analysis/batch_test_coverage.py` reads the shape. For each of the 80
batches it reports which of five test families appears, identified from the certificate code
and the issuing institution.

| Family | Recognised by | Covers |
|---|---|---|
| potency | `ППКnnnnn`, CNP | Δ9-THC, CBD, CBN, loss on drying |
| cannabinoids | Farmahem `-К/26`, `-ГС/26`, `-LoD-26` | cannabinoids, loss on drying |
| mycotoxins | Farmahem `-М/26` | aflatoxins Σ, aflatoxin B1, ochratoxin A |
| microbiology | IJZ-MB `nnn/nnnn/yy` | TAMC, TYMC, GNB, *E. coli*, *Salmonella* |
| physico-chemical | IPH `nnnn/yyyy`, plus the phytosanitary screen | Pb, Cd, As, Hg, aflatoxins, pesticides |

## Result

| | |
|---|---|
| Batches in the register | **80** |
| With microbiology **and** physico-chemical | **42** |
| With no microbiology recorded | **38** |
| With no physico-chemical recorded | 37 |

**This reports what the register records, not what a laboratory did.** A batch with no
microbiology row may have been tested and not entered, may be mid-testing, or may not have been
sent. The register has no disposition column and no release date, so it cannot distinguish
those three, and neither can this script. Printing the gap is the honest output; a verdict
would not be.

### And the dates say most of it is work in progress

Of the 38 batches with no microbiology recorded, **37 are 2026 batches**, the earliest with a
latest certificate of 02.03.2026 and the newest 10.08.2026. Set against batches that *do* have
microbiology, which run from 27.02.2025 to 10.08.2026, the pattern is unambiguous: the
incomplete blocks are the recent end of the register, exactly where testing still in flight
would be.

What the 38 do have:

| Batches | Testing recorded |
|---|---|
| 22 | potency only |
| 9 | cannabinoids + mycotoxins |
| 6 | cannabinoids only |
| 1 | potency + physico-chemical |

## The one that is not recent · `OPM1024_01`, row 30

Exactly one of the 38 is a 2025 batch, and its latest certificate is **07.05.2025** — fifteen
months old. It is also the only one of the 38 that has physico-chemical testing.

Its block is:

| Row | Code | Date |
|---|---|---|
| 30 | `ППК25117` | 06.05.2025 |
| 31 | `2156/2025` | 07.05.2025 |
| 32 | `2156/2025 (microbiology sub-report lab-ref not distinctly captured in OCR text)` | 07.05.2025 |

**Row 32 holds a complete set of microbiological results — TAMC, TYMC, GNB, *E. coli*,
*Salmonella*.** The script does not count them, and is right not to: the row's code names the
*physico-chemical* report, with an annotation saying the microbiology sub-report's own
laboratory reference could not be read. So this batch has microbiology data whose **source
document has never been identified**, and that is why it does not appear as a microbiology row.

The IPH physico-chemical pass reached the same conclusion from the other direction — it found
row 32 while checking whether an annotation should be stripped from row 31, and recorded that
the row was not among the 40 IJZ-MB certificates read because it carries no IJZ-MB number. Two
independent routes to the same gap. It is the one entry on this list that is not explained by
recency, and the one worth a QC question now rather than in three months.

## Two strings for the same absence

| Marker | Rows |
|---|---|
| `(not numbered)` | 17 |
| `n/a` | 18 |

Both mark the same state — a batch block holding only potency results — and they sit in
adjacent rows of the same register: `FB012603` at row 241 writes `(not numbered)` while
`FB012603V` at row 242 writes `n/a`, two rows apart, for the same absence on two samples of the
same batch.

This matters beyond tidiness. The link audit counts rows by their code cell, and `n/a` rows are
excluded from it as "not a certificate" while `(not numbered)` rows are counted as certificates
with no link. So the register's own two spellings put the same fact in two different buckets of
every report anybody writes over it. The rows themselves are otherwise completely empty — no
date, no institution, no values, no link.

**Normalising the two to one string is a one-line change with no risk, and it is not made
here** — which of the two is correct is a QC decision about what the row means, and neither
spelling is wrong until that is settled.

---

## Method

Derived entirely from the register, with no document reads: the five families are identified
from certificate codes whose format was established during the four verification passes, so
the classification rests on 226 documents already opened.

One bug is worth recording because it produced a false finding before it was caught. A first
version read `231/0394/26 (Racno trimiran cvet)` as a code and failed to match it, reporting
`J31122501` and `OPM122501` as having no microbiology when both have it — the brackets are a
note about the sample, not part of the certificate number. The fix is the same trailing-bracket
strip that `fold()` has always done, and it is the third time in this campaign that an
annotation attached to a code has broken something that reads codes.

Full per-batch table: `deliverables/qc_gap_analysis/batch_test_coverage_2026-08-31.csv`.
