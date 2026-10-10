# Loss on drying — one rule for the source, on every certificate — 17.09.2026

> **The Head of QC, 17.09.2026**
>
> "For all certificates of quality documents for all production batches you have to cite the
> parameter value for drying and also cite the corresponding certificate, and in this case for
> this parameter it is either Center for Natural Products or Farmahem laboratory, and in cases
> where you have both you will choose the value from Farmahem."

Three instructions, and the desk had none of them written down anywhere.

1. **#8 is never left blank while a document exists.** A certificate printing "not tested" with
   a loss-on-drying report for its own lot on file is a desk failure, not a testing gap.
2. **Two laboratories determine it and no others** — the Center for Natural Products (the `ППК`
   series, where the figure sits on the potency page) and Farmahem (the `ГС` series, its own
   one-parameter report). The census of all 172 certificates confirms it: no third laboratory
   appears anywhere in the set.
3. **Farmahem outranks the Center where a lot has both.** That is a ranking of *sources*, not of
   dates, which is why `apply_lod_source.py` is a source rule and not a carry rule.

---

## 1 · What the sweep found

Twenty-eight certificates — fourteen lots, each with a release and a reissue — printed nothing
for #8. The desk swept, for every one of them:

* the release register;
* the Head of QC's own 09.09 resolution pass;
* the eCoA spec listing `PP_Spec_Parameter_Listing.xlsx`;
* the whole of the owner's Drive, by lot folder and by document title.

**One document turned up.** `031-3-ГС/26` of **12.02.2026** — Farmahem, Wedding Cake
`WED102501` / **P060102**, loss on drying **6,8 %** ± 0,2 against the printed criterion < 12,
sample CF-43/26, received 30.01.2026, analysed 09–10.02.2026, Ph. Eur. 11.5 (2.2.32:2024). It is
one of the 44 scans `OI-42` enumerated on 16.09.2026 as being in no record of the desk. Its four
siblings of the same delivery — `031-1`, `031-2`, `031-4`, `031-5` — are all cited on
certificates already; only this one had been left behind, and the two Wedding Cake certificates
were among the twenty-eight.

It came in through the two-read gate (`intake_LoD031_2026-09-17`) and **`CoQ-PP_26-046` and
`CoQ-PP_26-165` now print 6,8 % citing 031-3-ГС/26 of 12.02.2026, Farmahem.**

---

## 2 · What could not be filled, and why

**Thirteen lots have no loss-on-drying report anywhere**, from either laboratory:

| P lot | Batch | Strain | Certificates |
| --- | --- | --- | --- |
| HPA1024 | HPA1024 | High Pro Amnesia | CoQ-PP_26-005, CoQ-PP_26-097 |
| OPM1024 | OPM1024 | Orange Punch Mimosa | CoQ-PP_26-006, CoQ-PP_26-101 |
| P050142 | BSS1024_01/2 | Blue Sunset Sherbet | CoQ-PP_26-021, CoQ-PP_26-138 |
| P060142 | GRC102501/1 | Graps & Creme | CoQ-PP_26-050, CoQ-PP_26-152 |
| — | CC012601-1 (P060332) | Cash Cow | CoQ-PP_26-068, CoQ-PP_26-087 |
| P060342 | SCR012601 | Scrambler | CoQ-PP_26-073, CoQ-PP_26-160 |
| P060352 | FB012602 | Fat Bastard | CoQ-PP_26-070, CoQ-PP_26-091 |
| P060362 | JD012603/01 | Jelly Donuts | CoQ-PP_26-071, CoQ-PP_26-122 |
| P060372 | CC012603 | Cash Cow | CoQ-PP_26-072, CoQ-PP_26-108 |
| P060382 | SCR012603 | Scrambler | CoQ-PP_26-074, CoQ-PP_26-105 |
| P060492 | JD042601 | Jelly Donutz | CoQ-PP_26-084, CoQ-PP_26-125 |
| — | FB042601 | Fat Bastard | both still at issue |
| — | CC042601 | Cash Cow | both still at issue |

The Head of QC's own 09.09 pass had already reached the same verdict for five of them —
"NOTHING ON FILE — no document anywhere" — and marked HPA1024 and OPM1024 as having only an
in-house scan, which is neither of the two laboratories the ruling names.

**This is a testing gap, not a desk one, and the certificate prints "not tested" because that is
the truth of it.** `OI-53` puts it to the Head of QC: these thirteen lots need loss on drying
determined, or a ruling that they are released without it. Farmahem's ГС report is one parameter
on one page, and one submission would close all thirteen.

---

## 3 · The ranking, and what it decides today

`apply_lod_source.py` holds the rule as an ordered list — **Farmahem, then the Center, then the
in-house sheet** — and for every certificate takes the highest-ranked laboratory the lot has,
then that laboratory's latest page.

**Today the ranking decides nothing.** No lot has both: Farmahem's ГС-series covers twelve lots,
the Center's ППК-series covers the rest, and the two never overlap. The rule is written down for
the next lot that goes to both — which, on the evidence of the thirteen above, is likely to be
soon.

| laboratory | certificates | documents |
| --- | ---: | ---: |
| CNP (UKIM Faculty of Pharmacy) ППК-series | 118 | 62 |
| Farmahem ГС-series | 24 | 12 |
| Purely Plant internal certificate of analysis | 4 | 2 |

The four in-house citations are P050192 and P050202, whose loss on drying exists only as the
company's own cross-check on the internal certificate. Neither laboratory has a page for either
lot, so the ruling's two-laboratory rule has nothing to promote them to; the in-house figure
stays, and it is the only record there is.

---

## 4 · What the rule deliberately does not do

It does **not** move a citation from one document of the same laboratory to a later one. That is
the question `OI-52` puts to the Head of QC — does the microbiological ruling of the same day,
that a newer external certificate means a retest, reach loss on drying too? Two certificates turn
on it: `CoQ-PP_26-095` (P050022) prints ППК25139 of 22.05.2025 where ППК25174 of 10.07.2025 is on
file, and `CoQ-PP_26-153` (J31112501) prints 051-5-ГС/26 of 02.03.2026 where 100-1-ГС/26 of
09.04.2026 is. Both newer documents predate their certificate, so under that rule the citation
would move and the date of issue would not.

The two standing guards hold here as everywhere: a release certificate refuses a retest document
(10.09.2026), and no certificate cites a document issued after its own day (v35).

---

## Reproducing

    python3 deliverables/qc_gap_analysis/intake_LoD031_2026-09-17/apply_LoD031.py
    python3 deliverables/qc_gap_analysis/apply_lod_source.py
    python3 deliverables/qc_gap_analysis/lod_check.py --md --date=17.09.2026

All three are idempotent.
