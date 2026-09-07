# The three delivery tranches against the desk — 07.09.2026

**Question.** 78 cultivation batches — 6,934.26 kg — left the site in the deliveries of
31.07, 14.08 and 28.08.2026 (the owner's *Tranches Overview*). Has each of them what a
certificate of quality needs, and is the desk's record of it true?

**Answer.** 44 are ready to issue. 30 are short of coverage. 4 have nothing on file at all.
And on 5 the batch was delivered in a potency bracket its own certificate contradicts —
which is not a desk defect but the most consequential thing in this report.

Everything below is reproducible: `tranches_raw_2026-09-07.csv` holds the delivery list
verbatim (its per-tranche totals reconcile against the sheet's own ВКУПНО lines), and the
**Delivery T1–T3** sheet of `CoQ_Analysis_Master_v12.xlsx` is built by reading Batch
Coverage, so the two cannot drift.

| | T1 (31.07) | T2 (14.08) | T3 (28.08) | all |
|---|---|---|---|---|
| batches delivered | 21 | 29 | 28 | 78 |
| kg | 1,480.66 | 2,747.87 | 2,705.73 | 6,934.26 |
| ready to issue | 14 | 17 | 13 | **44** |
| short of coverage | 7 | 8 | 15 | **30** |
| nothing on file | 0 | 4 | 0 | **4** |
| potency contradicted | 2 | 1 | 2 | **5** |

---

## 1. The five potency contradictions — for the QP, not for the desk

Each of these was delivered under a bracket that its own release certificate puts it
outside of. The certificate is the desk's typed record of the laboratory's page; the
declaration is the customer-facing sheet. They cannot both be right.

| Batch | T | kg | delivered as | its certificate says | belongs in |
|---|---|---|---|---|---|
| **JD012603/02** | 2 | 46.00 | 13.30 %, bracket 13–16 % | **20.54 %** (ППК26113, 30.06.2026, CNP) | 19–22 % |
| **FB012603** | 3 | 75.00 | 14.65 %, bracket 13–16 % | **20.83 %** (ППК26112, 30.06.2026, CNP) | 19–22 % |
| **FB012603V** | 3 | 16.00 | 15.60 %, bracket 13–16 % | **18.29 %** (ППК26110, 30.06.2026, CNP) | 16–19 % |
| **GG012603** | 1 | 40.00 | 15.59 %, bracket 13–16 % | **17.59 %** (ППК26114, 30.06.2026, CNP) | 16–19 % |
| **OPM122501** | 1 | 104.26 | 11.00 %, bracket 10–13 % | **8.09 %** (100-4-К/26, 09.04.2026, Farmahem) | 7–10 % |

Four are under-declared — the customer received more potent product than the bracket it was
sold in. One, OPM122501, is over-declared: 104 kg was sold as 10–13 % against a certificate
reading 8.09 %.

The CNP certificates are dated 30.06.2026 against packaging on 23–24.05 and 15.06.2026, so
they are the **initial release testing**, not the July retest campaign — the delivery
declaration and the release certificate disagree about the same testing, not about two
different samples. A cross-check on all 78 found no other batch off by more than 0.5 points
except GP062501 (22.89 % declared, 24.89 % on file), which stays inside its 22–25 % bracket.

Every declared potency does sit inside its own printed bracket, so the sheet is internally
consistent; it is the certificates it disagrees with.

## 2. Four delivered batches with no record anywhere — 193.32 kg

| Batch | T | P lot | kg | state |
|---|---|---|---|---|
| ACC102501 | 2 | P060122 | 38.88 | on the Head of QC's list (packed 18–19.02.2026); no certificate in eCOA_DB, no tracker lot |
| PUM102501 | 2 | P060112 | 49.91 | on the list (packed 17.02.2026); no certificate, no tracker lot |
| CF102501 | 2 | P060132 | 48.35 | on the list (packed 19–20.02.2026); no certificate, no tracker lot |
| CC012603 | 2 | P060372 | 56.18 | on the list (packed 24.05.2026); no certificate, no tracker lot |

All four are tranche 2. They are not identity failures — the batch list knows them, the
corpus holds nothing under any spelling, and no certificate anywhere prints their P number.
Either the documents exist on paper and have never been ingested, or the testing was never
done. Both are answerable only at the site.

## 3. The identity defects — eleven delivered batches that looked undocumented and were not

Fifteen of the 78 failed to resolve to a desk row on the first pass. Only the four above
were real. The other eleven were spelling, in three distinct mechanisms:

**3a. The asterisk, and which asterisk.** The company marks certain lots with a trailing
asterisk — `GG012601*` — and the Head of QC's batch list writes it that way. The delivery
sheet drops the mark, and the document filenames carry the **fullwidth** `＊` (U+FF0A) where
the paper prints ASCII `*`: nine documents in the corpus do this, the same homoglyph reflex
that returns `ТНС` for `THC` on a Cyrillic page. So the tracker held `GG012601＊` while the
batch list held `GG012601*`, and the two never met. The visible damage: **P060342 stood in
the tracker with no cultivation batch at all**, while the batch list said `SCR012601*` — 90 kg
of Scrambler delivered in tranche 3, apparently a nameless lot.

*Fixed:* `batch_id.py::batch_key` now folds every star glyph onto ASCII and keeps the mark,
with doctests. Whether a starred lot and its unstarred namesake are one batch is a fact about
the floor, not something a key may decide — the five open cases are in
`ingestion/ecoa_runner/identity_questions_2026-09-07.tsv` for a ruling.

**3b. A certificate that names only the packaging lot.** IJZ-MB prints `Серија: P060102` and
no cultivation batch, so the lot was created nameless — while the Head of QC's list says
`WED102501`, delivered in tranche 3. Three lots were in this state.

*Fixed:* the builder now back-fills a nameless lot's name from the batch list by P number,
and says so on build: `P050142 → BSS1024_01/2; P060102 → WED102501; P060342 → SCR012601*`.
The extraction prompt now requires the P number to be captured wherever it appears
(rule 8), because for these certificates it is the lot's only link to its name.

**3c. `SJ0925021`.** The batch list writes `SJ0925021` against P060082. All three
certificates the desk credits to that lot print `серија SJ092501`; the delivery sheet
delivers `SJ092501`; no `SJ092502` exists in any list. It is a mistyped digit.

*Fixed, as evidence rather than as a guess:* when a delivered batch resolves to no desk row,
the Delivery sheet now looks for the lot that credits **the certificates which print that
batch**, and names what it found — for SJ092501, "through the certificates that print this
batch (85/2026, 9/0012/26, ППК26006); the desk names the lot SJ0925021". The typo itself is
in the ruling file: correcting the Head of QC's own list is the Head of QC's to do.

## 4. Roll-ups: five delivered sub-lots that share one row

The delivery list sells sub-lots; the desk holds one row for the parent:

| delivered | its P lot | the desk's row |
|---|---|---|
| GRC102501/1 | P060142 | `GRC102501` (P060142 / P060182) |
| GRC102501/2 | P060182 | same row |
| JD012603/01 | P060362 | `JD012603` (P060362 / P060412 / P060422) |
| JD012603/02 | P060412 | same row |
| JD012603/02V | P060422 | same row |

A certificate of quality is issued per packaging lot, so a roll-up row cannot state coverage
for any one of them. It is not academic: reading potency through the roll-up hands
`JD012603/01` and `JD012603/02` the value from `ППК26111`, which is **JD012603/02V's**
certificate — a CoQ built that way would print another sub-lot's assay. The Delivery sheet
now says "the desk row is the roll-up X" in the Desk lot column wherever this applies, and
the potency column is keyed to the batch itself, never through the roll-up. Splitting the
rows needs the owner's word on which certificate belongs to which sub-lot.

## 5. Strain names invented by the reader

The corpus holds `Cup Junky`, `Sleepy Joy`, `Permanent Market`, `Appel and Banana`,
`Wedding Crasher`, `GorillaGlue` and `Clemosa a bud` — none of which is what the page
prints. Each splits one strain in two wherever anything groups by strain. Worse, the desk
files **GG4** (GG012601, GG012603, GG112501) and **Gorilla Glue** (GG1024, GG1024_01,
GG1024_02) under one strain name, while the delivery list keeps them apart as two strains.

*Fixed in the prompt* (rule 9, plus a closed strain list in `identity_normalisation`): the
strain is printed in Latin inside Macedonian text and must be copied exactly — a read that
lands outside the list is a reading error to raise, never a new strain and never a quiet
mapping. The corpus keeps what it holds until re-read; the rule stops it recurring.

## 6. RAGflow

- **`eCOA_SS` had never been parsed.** Ten stability certificates for the Grape Pie lots
  P050022, P050072 and P050202 (25 °C/60 %RH and 40 °C/75 %RH at 3, 6 and 9 months) sat in
  `UNSTART` with zero chunks — invisible to every retrieval since ingestion. Parsing is now
  running, with GraphRAG and RAPTOR turned off first: on ten templated certificates they
  would have cost a great deal and bought nothing.
- **Two of the four datasets had no description at all**, and a description is the prompt an
  agent reads when it chooses where to look. All four now describe themselves, and
  `eCOA_DB`'s says how to query it: the asterisk is part of the batch code and must be ASCII;
  a sub-lot separator carries no meaning; a batch that returns nothing may be on file under
  its P number; and **no measured value may be read out of the chunk text** — the chunk text
  drops superscripts and truncates counted ranges, and a mould count of 4,2 × 10⁴ read as
  10³ turns a failing batch into a passing one.
- **The extraction agent is at 1.1.0** with rules 7, 8 and 9 (the asterisk, the packaging lot,
  the strain), each recorded against the delivered batch it cost.
- Connectivity: the MCP server answers, but the host is slow — a cold `list` takes ~17 s and
  a broad semantic query ~88 s, past the MCP client's 60 s timeout. Narrow queries with
  `dataset_ids` and a small `top_k` succeed; broad sweeps need the REST endpoint.

## 7. What is short, and of what

Of the 30 delivered batches that are not ready, the missing determinations cluster tightly:

| missing | batches |
|---|---|
| #10 Mycotoxins, #11 Heavy metals, #12 Pesticide residues | 7 |
| #9 Microbiology and those three | 6 |
| #8 Loss on drying, #9, #11, #12 | 5 |
| #6 Total CBN alone | 4 |
| #9 Microbiology, #11, #12 | 2 |
| #6 with #10, #11, #12 | 1 |
| #6 and #8 | 1 |
| #8 Loss on drying alone | 1 |
| more than half the panel | 3 — GG1024 (9 of 12), SCR012601 (8), WED102501 (8) |

Nine of the thirty are short of nothing but the contaminant panel (#10–#12) and, in six
cases, microbiology with it; four want only Total CBN. That is one testing campaign away
from thirteen more certificates.

`GG1024` is the sharpest case: delivered in tranche 2 at 44.84 kg with **nine of twelve
determinations missing** — no cannabinoid assay of any kind exists for it, in any laboratory,
under any spelling. It is the R&D lot; it was still delivered.

## 8. What a person has to decide

1. The five potency contradictions in §1 — which figure governs, and what follows for
   product already with the customer.
2. The four batches in §2 — do the documents exist?
3. The six identity rulings in `identity_questions_2026-09-07.tsv`.
4. Whether to split the roll-up rows in §4, and on what evidence.
