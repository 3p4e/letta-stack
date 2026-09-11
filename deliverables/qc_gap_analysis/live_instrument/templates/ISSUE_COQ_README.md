# ISSUE_COQ — CoQ issue register

*Supplied by the owner on 10.09.2026, Drive folder `CoXTemp`
(`1JtunFDx-2sgOr1bEFv-Ktis9rB5hNrGw`), alongside `_CoQ_MASTER_Template.html` and
`cox.css`. The template in that folder is **byte-identical** to the one already
vendored here — verified by md5 — so nothing about the master changed; this
README is the specification for what may be written into it.*

Generated from **PP_Potency_MASTER_Spec.xlsx** (Master – All Batches, 48 rows).
Last revised 31.08.2026.

- **`_CoQ_MASTER_Template.html`** — master copy of the approved CoQ (blank controlled fields).
- **48 CoQs for the initial batch release** — `CoQ-PP-{year}-{NNNN}`, numbered sequentially by packaging date.
- **13 further CoQs** — issued for the batches whose 12-month retest fell due; each is an **ordinary sequential CoQ** (`CoQ-PP-2026-0027 … 0039`) carrying the results of the additional QC testing. **A CoQ is never labelled "retest"** — it is a certificate of quality for the batch at its date of issue.

## Banner potency
The gold figure beside the strain name is the **actual Total Δ⁹-THC assay result for that batch** — not the grade nominal. The ± tolerance is not shown on any CoQ. The grade nominal ± tolerance and the acceptance range stay on the SPC; the range still appears in the CoQ Section 01 "Potency" field and as the row-4 acceptance criterion.

## Filled from the master spec
Batch № · cultivation batch № · strain · grade · class · potency range · product code · specification doc code · manufacture date · packaging date · **Total Δ⁹-THC assay result** · issue date · iCoA reference code.

## Left as controlled blanks (`—`)
Quantitative results not present in the source data (Total CBD, CBN, foreign matter, LoD, microbiology, mycotoxins, heavy metals, pesticides), the outsourced-laboratory eCoA codes, and **both conformity tick-boxes**. A CoQ must never carry a result or a conformity assertion that has not been certified — QC transcribes these from the actual iCoA/eCoA and ticks one box at issue. The 13 additional-testing CoQs carry every result cell blank, including the identity rows and the assay, pending their own certificates.

## Self-contained
Every CoQ has the brand mark embedded as a data-URI and the full stylesheet inlined, so the logo, layout, fonts and A4 fidelity survive download and PDF export.

---

## Owner's ruling of 10.09.2026 — where the two potency figures come from

Two instructions arrived with this README and they override the register table
above on one point each. Recorded here because they are what the compiler
implements:

1. **The banner figure and the row-4 assay are the same number, and it is the
   certificate's.** Not the master spec's `Total THC` column. Before this ruling
   the banner carried the spec figure and row 4 the certificate's, and they
   disagreed on all 22 Tranche 1 and 2 drafts — by as much as 3.76 points.
2. **The acceptance range is a placeholder.** It is supplied separately, so both
   places that print it — the Section 01 "Potency" field and the row-4
   acceptance criterion — carry it **in brackets** until it is settled.

3. **The phenotype and processing pills are selected according to the
   specification for the product strain.** With the chemotype pill beside them
   they are product attributes, not laboratory results, and the document that
   states them is the issued QCSP 001 specification the certificate already
   names in Spec. Ref. `spec_attributes.py` reads all three bands — and the
   primary-packaging line — off that document. Where the specification is not on
   file, every pill in the band is unticked and marked; the desk does not tick a
   box it cannot cite.

Everything else in the master is the master's. The compiler writes the fields
listed under *Filled from the master spec*, the three selection bands, the result
cells, and the Section 03 laboratory cross-reference — and nothing else. A build-time check holds it to
that: master 24 rows against draft 24 rows, **zero** differences in the parameter
and method columns, and exactly one in the acceptance-criteria column, which is
the bracketed row-4 range.

## Register

See `PP_Potency_MASTER_Spec.xlsx` and the owner's copy of this file in `CoXTemp`
for the full 48-row register (CoQ № · PP batch · cultivation batch · strain ·
grade · class · range · Total THC · manufacture · packaging · iCoA ref · further
CoQ). It is not duplicated here: the desk reads the same figures from
`coq_issue_plan.json`, and one register copied into two places is one register
too many.
