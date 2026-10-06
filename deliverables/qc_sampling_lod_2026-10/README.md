# PP-QC-SP-002/26 — in-house loss on drying before shipment, Tranches 1 and 2

Three separate document packages, bilingual Macedonian / English, built from committed records only.
Head of QC, 06.10.2026: the sampling of the bags and the loss-on-drying analysis are separate
documentation packages, on the company's own SOP forms. The forms reproduce the July 2026 layouts
field for field (QCT 024 v01, QCSOP 011_A03 v7.0, QCT 021 v01, QASOP_031_A05_v1, QASOP_031_A07);
only the values are prefilled. Each sampling form carries every batch of its day (Head of QC,
05.10.2026), except A03, whose layout is one batch per form.

| Package (`out/`) | Contents |
|---|---|
| `1_PLAN/`, `PP-QC-SP-002_26_PACKAGE-1_PLAN.zip` | Sampling Plan and Execution Protocol (10 pages) |
| `2_SAMPLING_EXECUTION/`, `PP-QC-SP-002_26_PACKAGE-2_SAMPLING_EXECUTION.zip` | Package index, then per sampling day the seven documents below |
| `3_LOD_ANALYSIS_EXECUTION/`, `PP-QC-SP-002_26_PACKAGE-3_LOD_ANALYSIS_EXECUTION.zip` | LOD-01 (Day-1 samples) and LOD-02 (Day-2 samples), one execution record each for all batches analysed together |

Package 2, per sampling day, in order of use:

| Step | Document | Form | Record No. |
|---|---|---|---|
| 1 | Transfer, secure warehouse to sampling room: selected bags K#B#, net 400.0 g, gross at receipt | QCT 024 v01 | `PP-QC-SP-002/26-D1-RCPT` (D2) |
| 2 | Visual inspection on opening, one form per batch, bags prefilled | QCSOP 011_A03 v7.0 | from the A03 register |
| 3 | Before, sampled and after per bag; composite sample code and net per batch; waste, loss, gain | QCT 021 v01 | MLR number from its register |
| 4 | SAMPLED bag labels, 52.5 x 33 mm, one per sampled bag (493 and 492) | QASOP_031_A05_v1 | none |
| 5 | Composite sample labels, A4 4 x 2, one per batch (23 and 23) | QASOP_031_A07 | none |
| 6 | Transfer, sampling room to secure warehouse: the same bags, new net and gross from QCT 021 | QCT 024 v01 | `PP-QC-SP-002/26-D1-RET` (D2) |
| 7 | Transfer, sampling room to QC laboratory: one composite per batch | QCT 024 v01 | `PP-QC-SP-002/26-D1-SMP` (D2) |

Package 3, the LoD execution record: A receipt of the samples (from step 7), B equipment and
conditions, C homogenisation and test portions, D weighings to constant mass per test portion (44
prefilled rows each), E results per batch, F deviations and OOS, G sign-offs.

Each package folder holds every DOCX and PDF and a merged packet PDF with a bookmark per document.
The label sheets are in the folder and the zip but not in the packet: they print on perforated
stock. Data behind every number: `SAMPLING_PLAN_T1_T2_2026-10.tsv` (one row per lot),
`bag_selection.tsv` (one row per selected bag), `DATA_NOTES.md`, `BUILD_LOG.md` (pp_verify result,
page count and SHA-256 of every file).

## What the campaign does

- 46 production batches (Tranche 1: 20, Tranche 2: 26) in 400 g triple-foil bags, 10 per carton, in
  the secure warehouse (sampling point SP-12 of QCSOP 011 v03).
- Per batch: N = kg / 0.400 rounded up (the warehouse's documented bag count governs if it differs),
  n = 1.5 x sqrt(N) rounded up bags opened (WHO TRS 929 Annex 4 r-plan, as in PP-QC-SP-001/26),
  systematic selection with a seeded random start (seed 20261005), one flower — the largest — per
  bag, all n flowers of a batch into ONE composite, k = 1 / 2 / 3 determinations by bag count
  (N up to 100 / 101 to 400 / above 400), about 1.000 g each.
- Method a02.2 (Ph. Eur. 2.2.32, monograph 3028): vacuum oven VO29 at 40 degC, 20 +/- 2 mbar, 24 h, over
  about 100 g molecular sieve R; 1.000 g cut, unsieved, in a pre-dried tared bottle; cool at least 30 min in
  the desiccator, weigh on the Shimadzu AUW220D, back into the oven and weigh again until constant mass
  (two weighings within 0.5 mg); LoD % = (m0 - m1) / m0 x 100; criterion 12.0 % w/w maximum (QCSP 001).
- Two sampling days balanced by bags to open (Day 1: 23 lots, 493 bags, 44 portions; Day 2: 23 lots,
  492 bags, 44 portions); Day-1 results read on Day 2, Day-2 results on Day 3.

## Decisions taken (Head of QC, 05.10.2026) and defaults he can overrule

1. kg basis = master v57, sheet `Reference`, block DELIVERY T1-T3, column E. One evident defect is
   corrected, not propagated: GG1024_01 (P050092) reads 0.87 kg in cell E216 against 223.734 kg on the
   owner's stock table and 560 bags in the July plan — the plan uses 223.73 kg and lists the cell for
   correction. KC102501 keeps the master's 21.67 kg (stock table 16.000 kg).
2. k = 1 / 2 / 3 by bag count; QCSOP 011 v03 writes a duplicate for LoD at SP-06 — noted in the plan.
3. Scope T1 + T2 only; T3 (31 lots) follows as PP-QC-SP-003/26 with the same builder.
4. Built locally with the repository engine (the master of the engine deployed on KVM4); no Letta or
   KVM4 call was needed — the content is authored here and the engine formats it.
5. Documents carry IN REVIEW — NOT FOR USE; on approval they are rebuilt as v1.0 with the effective
   date the Head of QC gives (`STATUS` in `build_campaign_docs.py`). No approval date is invented.
6. Signatories as on the owner's own documents: prepared / approved B. Nikolov, M.Pharm. (QC Head /
   QC Department Manager), checked J. Romevska (QA), analyst Hristina Cekic (QC Analyst).

## Open for the Head of QC (also section 11 of the plan)

- Master v57 Reference E216 (GG1024_01); KC102501 kg; documented bag counts at retrieval.
- k rule vs the SOP duplicate; oven capacity (44 bottles per night).
- The additional drying period for the second weighing (a02.2 or his instruction).
- Record numbers: D1/D2-RCPT, -RET, -SMP for the QCT 024 transfers and LOD-01/-02 for the analysis
  (or QCT 025); A03 and QCT 021 numbers from their registers; RQS registration before sampling.
- HMA pairing on the composites for the method-verification work (5 to 12 % range) — entered before
  approval if the verification agent asks for it.

## Rebuild

```
python3 campaign_data.py --test && python3 campaign_data.py      # data -> TSVs
python3 build_campaign_docs.py                                    # package 1, pp_verify PASS required
python3 build_execution_packages.py                               # packages 2 and 3 (forms, LoD records)
python3 build_labels.py                                           # QASOP_031 label sheets
for f in out/1_PLAN out/2_SAMPLING_EXECUTION out/3_LOD_ANALYSIS_EXECUTION; do
  (cd $f && soffice --headless --convert-to pdf --outdir . *.docx); done
python3 package.py                                                # packets, zips, BUILD_LOG.md
```

Fonts: copy `pp-document-suite/assets/fonts/*.ttf` to `~/.local/share/fonts` and run `fc-cache -f`
before converting, so Calibri resolves to Carlito.
